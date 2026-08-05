"""One deployment contract, checked identically against every profile (H1927 D4).

Both production paths are first-class: a Docker container and a bare
systemd/nginx host. Before this script they were verified by different means —
the container by a HEALTHCHECK that only looked at `/api/health`, the bare host
by whatever the operator remembered to curl. A profile that is only checked
informally is the one that breaks.

So this asserts a *transport-neutral* contract. It takes a base URL and knows
nothing about how the thing behind it was started: same checks, same pass/fail,
whether that URL is a container port, an nginx vhost, or a locally-run uvicorn.

VERIFICATION D5: "Docker and bare-host profiles pass the same
health/search/regex/PWA/version contract. — Shared smoke report."

Usage
-----
    python web/scripts/deployment_contract_smoke.py --base-url http://127.0.0.1:8000
    python web/scripts/deployment_contract_smoke.py --base-url https://samudra.example \
        --profile bare --json-report smoke-report.json

Exit codes: 0 all required checks passed · 1 a required check failed ·
2 the target never became ready.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field, asdict

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

DEFAULT_TIMEOUT = 15.0
# VERIFICATION "Performance budgets": application readiness with existing local
# DBs, no more than 10 s. The wait allowance is deliberately larger than the
# budget so a slow-but-passing boot is reported as a *number*, not as a
# timeout with no measurement.
READINESS_BUDGET_S = 10.0
READINESS_WAIT_S = 90.0
# Hard regex deadline 2 s + teardown within 500 ms.
REGEX_DEADLINE_S = 2.0
REGEX_TEARDOWN_ALLOWANCE_S = 0.5


@dataclass
class CheckResult:
    name: str
    ok: bool
    required: bool
    detail: str
    duration_ms: int = 0
    skipped: bool = False

    @property
    def status(self) -> str:
        if self.skipped:
            return "SKIP"
        return "PASS" if self.ok else ("FAIL" if self.required else "WARN")


@dataclass
class Report:
    base_url: str
    profile: str
    checks: list[CheckResult] = field(default_factory=list)

    def add(self, result: CheckResult) -> CheckResult:
        self.checks.append(result)
        return result

    @property
    def failed(self) -> list[CheckResult]:
        return [c for c in self.checks if c.required and not c.ok and not c.skipped]


class Response:
    def __init__(self, status: int, headers: dict[str, str], body: bytes, elapsed: float):
        self.status = status
        self.headers = {k.lower(): v for k, v in headers.items()}
        self.body = body
        self.elapsed = elapsed

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")

    def json(self):
        return json.loads(self.text)


def request(
    url: str,
    *,
    method: str = "GET",
    payload: dict | None = None,
    headers: dict | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> Response:
    data = None
    extra_headers = headers or {}
    headers = {"User-Agent": "samudra-deployment-contract-smoke/1"}
    headers.update(extra_headers)
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    started = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            return Response(resp.status, dict(resp.headers), body, time.monotonic() - started)
    except urllib.error.HTTPError as exc:
        body = exc.read()
        return Response(exc.code, dict(exc.headers or {}), body, time.monotonic() - started)


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def wait_for_readiness(base: str, report: Report) -> bool:
    """Poll /api/health until the corpus reports OK, or give up.

    Readiness, not liveness: a process that accepts connections while its
    corpus probe is still failing is not a deployment anyone should call good.
    """
    deadline = time.monotonic() + READINESS_WAIT_S
    started = time.monotonic()
    last = "never responded"
    while time.monotonic() < deadline:
        try:
            resp = request(f"{base}/api/health", timeout=5.0)
            if resp.status == 200:
                data = resp.json()
                if data.get("corpus_db", {}).get("ok") is True:
                    elapsed = time.monotonic() - started
                    within = elapsed <= READINESS_BUDGET_S
                    report.add(
                        CheckResult(
                            "readiness",
                            True,
                            True,
                            f"ready in {elapsed:.1f}s "
                            f"({'within' if within else 'OVER'} the {READINESS_BUDGET_S:.0f}s budget)",
                            int(elapsed * 1000),
                        )
                    )
                    report.add(
                        CheckResult(
                            "readiness_budget",
                            within,
                            False,  # advisory: a slow host is not a broken contract
                            f"{elapsed:.1f}s vs {READINESS_BUDGET_S:.0f}s budget",
                            int(elapsed * 1000),
                        )
                    )
                    return True
                last = f"health 200 but corpus_db.ok={data.get('corpus_db', {}).get('ok')}"
            else:
                last = f"health returned {resp.status}"
        except Exception as exc:  # noqa: BLE001 — the target may not be up yet
            last = f"{type(exc).__name__}: {exc}"
        time.sleep(1.0)

    report.add(CheckResult("readiness", False, True, f"never became ready: {last}"))
    return False


def check_health_shape(base: str, report: Report) -> None:
    resp = request(f"{base}/api/health")
    data = resp.json() if resp.status == 200 else {}
    corpus = data.get("corpus_db", {})
    report.add(
        CheckResult(
            "health_reports_sources",
            bool(corpus.get("source_count", 0) > 0),
            True,
            f"source_count={corpus.get('source_count')}",
            int(resp.elapsed * 1000),
        )
    )
    # state_db degrading is legitimate (STATE_DB_PATH may be unset on a
    # read-only profile), so this is reported, not enforced.
    state = data.get("state_db", {})
    report.add(
        CheckResult(
            "health_state_db",
            bool(state.get("ok")),
            False,
            f"state_db.ok={state.get('ok')} error={state.get('error')}",
        )
    )


def check_corpus_version_exposed(base: str, report: Report) -> None:
    """The deployment must be able to say *which* corpus it is serving.

    Without this a bad bundle is indistinguishable from a good one at runtime.
    """
    resp = request(f"{base}/api/health")
    meta = resp.json().get("corpus_db", {}).get("metadata", {}) if resp.status == 200 else {}
    version = meta.get("corpus_version")
    report.add(
        CheckResult(
            "corpus_version_exposed",
            bool(version),
            True,
            f"corpus_version={version!r} generated_at={meta.get('generated_at')!r}",
        )
    )


def check_plain_search(base: str, report: Report, query: str) -> None:
    resp = request(
        f"{base}/api/search",
        method="POST",
        payload={"mode": "plain", "query": query, "limit": 10},
    )
    ok = resp.status == 200
    count = None
    if ok:
        try:
            body = resp.json()
            results = body.get("results", body if isinstance(body, list) else [])
            count = len(results)
        except Exception:  # noqa: BLE001
            ok = False
    report.add(
        CheckResult(
            "plain_search",
            ok,
            True,
            f"status={resp.status} results={count} query={query!r}",
            int(resp.elapsed * 1000),
        )
    )


def check_bounded_regex(base: str, report: Report) -> None:
    """A catastrophic pattern must not hold a worker past the hard deadline.

    The contract is about *bounded time and a clean response*, not about which
    status code the app chooses — a timeout may legitimately surface as 4xx or
    5xx. What must never happen is the request hanging.
    """
    # NOT the textbook `(a+)+$`: measured 05-08-2026, the `regex` engine this
    # app uses optimises that one away (~1 ms on 40 chars), so a smoke built on
    # it would report PASS without ever exercising the deadline. `(a|a)*$` is an
    # alternation the optimiser cannot collapse.
    evil = "(a|a)*$"
    started = time.monotonic()
    try:
        resp = request(
            f"{base}/api/search",
            method="POST",
            payload={"mode": "regex", "query": evil, "limit": 10},
            timeout=REGEX_DEADLINE_S + REGEX_TEARDOWN_ALLOWANCE_S + 5.0,
        )
        elapsed = time.monotonic() - started
        status = resp.status
        leaked = _looks_like_internal_leak(resp.text)
    except Exception as exc:  # noqa: BLE001
        elapsed = time.monotonic() - started
        report.add(
            CheckResult(
                "bounded_regex",
                False,
                True,
                f"request did not complete within the deadline: {type(exc).__name__}: {exc}",
                int(elapsed * 1000),
            )
        )
        return

    allowance = REGEX_DEADLINE_S + REGEX_TEARDOWN_ALLOWANCE_S
    report.add(
        CheckResult(
            "bounded_regex",
            elapsed <= allowance,
            True,
            f"returned {status} in {elapsed:.2f}s (allowance {allowance:.1f}s)",
            int(elapsed * 1000),
        )
    )
    report.add(
        CheckResult(
            "regex_error_is_opaque",
            not leaked,
            True,
            "no internal detail in the timeout/error payload"
            if not leaked
            else f"payload leaks internals: {resp.text[:200]!r}",
        )
    )


_LEAK_MARKERS = (
    "Traceback (most recent call last)",
    "/app/",
    "site-packages",
    ".py\", line ",
)


def _looks_like_internal_leak(text: str) -> bool:
    return any(marker in text for marker in _LEAK_MARKERS)


def check_static_and_pwa(base: str, report: Report) -> None:
    sw = request(f"{base}/sw.js")
    report.add(
        CheckResult(
            "pwa_service_worker",
            sw.status == 200 and sw.headers.get("service-worker-allowed") == "/",
            True,
            f"status={sw.status} Service-Worker-Allowed={sw.headers.get('service-worker-allowed')!r}",
            int(sw.elapsed * 1000),
        )
    )

    root = request(f"{base}/")
    report.add(
        CheckResult(
            "root_page",
            root.status == 200,
            True,
            f"status={root.status}",
            int(root.elapsed * 1000),
        )
    )
    report.add(
        CheckResult(
            "html_coop_header",
            root.headers.get("cross-origin-opener-policy") == "same-origin",
            True,
            f"COOP={root.headers.get('cross-origin-opener-policy')!r}",
        )
    )

    # A static asset, discovered from the page rather than hardcoded, so this
    # keeps working when asset names change.
    match = re.search(r'(?:href|src)="(/static/[^"?]+)', root.text)
    if not match:
        report.add(
            CheckResult("static_asset", True, False, "no /static asset referenced by /", skipped=True)
        )
    else:
        asset = request(f"{base}{match.group(1)}")
        report.add(
            CheckResult(
                "static_asset",
                asset.status == 200
                and asset.headers.get("cross-origin-resource-policy") == "same-origin",
                True,
                f"{match.group(1)} status={asset.status} "
                f"CORP={asset.headers.get('cross-origin-resource-policy')!r} "
                f"Cache-Control={asset.headers.get('cache-control')!r}",
                int(asset.elapsed * 1000),
            )
        )


def check_reader_route(base: str, report: Report) -> None:
    """Reader pages are the deep-link surface; a broken slug route is invisible
    to a health check but breaks every citation."""
    listing = request(f"{base}/api/sources")
    if listing.status != 200:
        report.add(
            CheckResult("reader_route", False, True, f"/api/sources returned {listing.status}")
        )
        return
    try:
        sources = listing.json()
        rows = sources if isinstance(sources, list) else sources.get("sources", [])
        slug = next((r.get("slug") for r in rows if r.get("slug")), None)
    except Exception as exc:  # noqa: BLE001
        report.add(CheckResult("reader_route", False, True, f"unparseable /api/sources: {exc}"))
        return

    if not slug:
        report.add(
            CheckResult("reader_route", True, False, "no slugged source to probe", skipped=True)
        )
        return

    page = request(f"{base}/sources/{urllib.parse.quote(str(slug), safe='-_')}")
    report.add(
        CheckResult(
            "reader_route",
            page.status == 200,
            True,
            f"/sources/{slug} status={page.status}",
            int(page.elapsed * 1000),
        )
    )


def check_sitemaps(base: str, report: Report) -> None:
    index = request(f"{base}/sitemap.xml")
    report.add(
        CheckResult(
            "sitemap_index",
            index.status == 200 and "<sitemapindex" in index.text,
            True,
            f"status={index.status}",
            int(index.elapsed * 1000),
        )
    )
    robots = request(f"{base}/robots.txt")
    report.add(
        CheckResult(
            "robots",
            robots.status == 200 and "Sitemap:" in robots.text,
            True,
            f"status={robots.status}",
        )
    )


ADMIN_PROBE_PATH = "/api/admin/vacuum"


def check_admin_credentials(base: str, report: Report) -> None:
    """Two different questions about the admin surface, kept apart on purpose.

    1. **Does a wrong key get in?** A deployment that honours a bogus admin key
       is broken now, on this profile, and must fail the contract.
    2. **Are credentials accepted from the URL at all?** `?key=…` puts the
       secret in nginx access logs, browser history and Referer headers.

    Both are now **required**. Question 2 was a standing WARN while it was
    Lane C3's to fix; H1926 landed the header-only transport, so a deployment
    that still honours a query-string credential is running pre-H1926 code and
    the contract should say so rather than keep tolerating it.

    The probes hit the real endpoint. A check pointed at a path that does not
    exist would 404 and "pass" forever.
    """
    resp = request(
        f"{base}{ADMIN_PROBE_PATH}",
        method="POST",
        headers={"X-Admin-Key": "smoke-test-not-a-real-key"},
    )
    if resp.status == 404:
        report.add(
            CheckResult(
                "admin_rejects_wrong_key",
                False,
                True,
                f"{ADMIN_PROBE_PATH} returned 404 — the probe path is wrong, so this "
                f"check proves nothing. Fix the path rather than trusting the pass.",
            )
        )
        return

    refused = resp.status in (401, 403)
    report.add(
        CheckResult(
            "admin_rejects_wrong_key",
            refused,
            True,
            f"{ADMIN_PROBE_PATH} with a bogus header key returned {resp.status} "
            f"({'refused' if refused else 'NOT REFUSED'})",
            int(resp.elapsed * 1000),
        )
    )

    query_resp = request(
        f"{base}{ADMIN_PROBE_PATH}?key=smoke-test-not-a-real-key", method="POST"
    )
    # 400 is the H1926 refusal-without-comparison. 401/403 would mean the
    # credential was still *read* from the query string, just not honoured —
    # the leak has already happened by then, so that is not a pass.
    query_refused = query_resp.status == 400
    report.add(
        CheckResult(
            "no_query_string_credentials",
            query_refused,
            True,
            f"{ADMIN_PROBE_PATH}?key=… returned {query_resp.status} "
            f"({'refused outright' if query_refused else 'NOT refused as a transport — pre-H1926 code?'})",
            int(query_resp.elapsed * 1000),
        )
    )


# ---------------------------------------------------------------------------

def run(base_url: str, profile: str, query: str) -> Report:
    base = base_url.rstrip("/")
    report = Report(base_url=base, profile=profile)

    if not wait_for_readiness(base, report):
        return report

    check_health_shape(base, report)
    check_corpus_version_exposed(base, report)
    check_plain_search(base, report, query)
    check_bounded_regex(base, report)
    check_static_and_pwa(base, report)
    check_reader_route(base, report)
    check_sitemaps(base, report)
    check_admin_credentials(base, report)
    return report


def print_report(report: Report) -> None:
    width = max((len(c.name) for c in report.checks), default=10)
    print(f"\nDeployment contract — profile={report.profile} target={report.base_url}")
    print("-" * (width + 60))
    for check in report.checks:
        timing = f"{check.duration_ms:>6}ms" if check.duration_ms else " " * 8
        print(f"{check.status:<5} {check.name:<{width}} {timing}  {check.detail}")
    print("-" * (width + 60))
    passed = sum(1 for c in report.checks if c.ok and not c.skipped)
    print(f"{passed}/{len(report.checks)} checks passed; {len(report.failed)} required failure(s)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base-url", required=True, help="Root URL of the running deployment")
    parser.add_argument(
        "--profile",
        default="docker",
        choices=["docker", "bare", "local"],
        help="Label recorded in the report; the checks themselves are identical",
    )
    parser.add_argument(
        "--query",
        default="a",
        help="Plain-search probe term (default: 'a', which matches any real corpus)",
    )
    parser.add_argument("--json-report", help="Write the machine-readable report here")
    args = parser.parse_args()

    report = run(args.base_url, args.profile, args.query)
    print_report(report)

    if args.json_report:
        with open(args.json_report, "w", encoding="utf-8") as fh:
            json.dump(
                {
                    "base_url": report.base_url,
                    "profile": report.profile,
                    "checks": [asdict(c) | {"status": c.status} for c in report.checks],
                },
                fh,
                ensure_ascii=False,
                indent=2,
            )
        print(f"report written to {args.json_report}")

    if not report.checks or report.checks[0].name == "readiness" and not report.checks[0].ok:
        return 2
    return 1 if report.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
