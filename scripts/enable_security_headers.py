#!/usr/bin/env python3
"""HTTPS-stable gate + nginx HSTS/security-header enablement (Wave P10b / H2398).

Hard gate (handoff fail condition):
  HSTS must NEVER be enabled on a broken or HTTP-only host. Browsers cache
  the policy and lock users out if TLS later fails.

Typical flow on the LXC (root@193.232.229.92)::

  # 1) Gate + dry plan (no mutations):
  python3 /opt/samudra/repo/scripts/enable_security_headers.py

  # 2) When GATE GO (HTTPS 200 + HTTP→HTTPS redirect):
  python3 /opt/samudra/repo/scripts/enable_security_headers.py --apply

  # 3) Prove (handoff acceptance):
  curl -sI https://samudra.193.232.229.92.sslip.io/ | grep -i strict

Exit codes:
  0  GO (HTTPS stable; apply succeeded if --apply)
  2  HTTPS not stable / HTTP-only  (NOT done — refuse HSTS)
  3  apply/runtime failure after the gate was GO
  1  usage / local errors
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

DEFAULT_HOST = "samudra.193.232.229.92.sslip.io"
DEFAULT_NGINX = "/etc/nginx/sites-available/samudra"
DEFAULT_SNIPPET_DST = "/etc/nginx/snippets/samudra-security-headers.conf"
DEFAULT_HEALTH_PATH = "/api/health"
INCLUDE_BASENAME = "samudra-security-headers.conf"
HSTS_TOKEN = "strict-transport-security"

# Repo-relative source of the include (committed; box copy is installed).
def default_snippet_src() -> Path:
    return Path(__file__).resolve().parent.parent / "deploy" / INCLUDE_BASENAME


class NoRedirect(urllib.request.HTTPErrorProcessor):
    """Return 3xx as a normal response so the gate can see the redirect."""

    def http_response(self, request, response):  # noqa: ANN001
        return response

    https_response = http_response


def _opener() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(NoRedirect)


def fetch(
    url: str,
    *,
    method: str = "GET",
    timeout: float = 20.0,
) -> tuple[int, dict[str, str], bytes]:
    """Return (status, lowercased headers, body). Does not follow redirects."""
    req = urllib.request.Request(url, method=method)
    try:
        with _opener().open(req, timeout=timeout) as resp:
            headers = {k.lower(): v for k, v in resp.headers.items()}
            body = resp.read() if method.upper() != "HEAD" else b""
            return int(resp.status), headers, body
    except urllib.error.HTTPError as exc:
        headers = {k.lower(): v for k, v in (exc.headers or {}).items()}
        body = b""
        try:
            body = exc.read() if method.upper() != "HEAD" else b""
        except Exception:  # noqa: BLE001 — probe surface
            body = b""
        return int(exc.code), headers, body


def fetch_hairpin(
    url: str,
    host: str,
    *,
    dest_ip: str = "127.0.0.1",
    method: str = "GET",
    timeout: float = 20.0,
) -> tuple[int, dict[str, str], bytes]:
    """Probe a public URL against dest_ip (on-box hairpin bypass).

    From the LXC, `https://samudra.…sslip.io` often times out (no hairpin
    NAT). curl --resolve still exercises the real nginx 443 listener + cert.
    """
    from urllib.parse import urlparse

    parsed = urlparse(url)
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    curl = shutil.which("curl")
    if not curl:
        raise RuntimeError("curl not on PATH for hairpin fallback")
    cmd = [
        curl,
        "-sS",
        "-D",
        "-",
        "-o",
        "/dev/null",
        "--max-time",
        str(int(timeout)),
        "--resolve",
        f"{host}:{port}:{dest_ip}",
    ]
    if method.upper() == "HEAD":
        cmd.append("-I")
    cmd.append(url)
    proc = subprocess.run(
        cmd,
        check=False,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"curl --resolve failed rc={proc.returncode} err={(proc.stderr or '').strip()!r}"
        )
    raw = proc.stdout or ""
    # Last header block (in case of redirects we did not follow — curl -D
    # still prints the response we got).
    status = 0
    headers: dict[str, str] = {}
    for line in raw.splitlines():
        if line.startswith("HTTP/"):
            parts = line.split()
            if len(parts) >= 2 and parts[1].isdigit():
                status = int(parts[1])
                headers = {}
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip().lower()] = v.strip()
    return status, headers, b""


def https_stable_gate(
    host: str,
    *,
    health_path: str = DEFAULT_HEALTH_PATH,
    timeout: float = 20.0,
) -> tuple[bool, str, dict[str, object]]:
    """Return (ok, reason, probe). ok False ⇒ must not enable HSTS."""
    https_health = f"https://{host}{health_path}"
    http_root = f"http://{host}/"
    probe: dict[str, object] = {
        "https_health_url": https_health,
        "http_root_url": http_root,
    }

    try:
        https_status, https_headers, _ = fetch(
            https_health, method="GET", timeout=timeout
        )
    except Exception as exc:  # noqa: BLE001 — try on-box hairpin before refuse
        probe["https_public_error"] = f"{type(exc).__name__}: {exc}"
        try:
            https_status, https_headers, _ = fetch_hairpin(
                https_health, host, method="GET", timeout=timeout
            )
            probe["https_probe"] = "hairpin-127.0.0.1"
        except Exception as hairpin_exc:  # noqa: BLE001
            probe["https_error"] = (
                f"{type(exc).__name__}: {exc}; "
                f"hairpin: {type(hairpin_exc).__name__}: {hairpin_exc}"
            )
            return (
                False,
                f"HTTPS GET {https_health} failed ({type(exc).__name__}: {exc}) "
                "— refuse HSTS (would pin clients to a broken host)",
                probe,
            )

    probe["https_health_status"] = https_status
    if https_status != 200:
        return (
            False,
            f"HTTPS GET {https_health} → {https_status}, want 200 "
            "— refuse HSTS until the cert/vhost is serving cleanly",
            probe,
        )

    try:
        http_status, http_headers, _ = fetch(http_root, method="GET", timeout=timeout)
    except Exception as exc:  # noqa: BLE001
        probe["http_public_error"] = f"{type(exc).__name__}: {exc}"
        try:
            http_status, http_headers, _ = fetch_hairpin(
                http_root, host, method="GET", timeout=timeout
            )
            probe["http_probe"] = "hairpin-127.0.0.1"
        except Exception as hairpin_exc:  # noqa: BLE001
            probe["http_error"] = (
                f"{type(exc).__name__}: {exc}; "
                f"hairpin: {type(hairpin_exc).__name__}: {hairpin_exc}"
            )
            return (
                False,
                f"HTTP GET {http_root} failed ({type(exc).__name__}: {exc}) "
                "— need a live HTTP→HTTPS redirect before HSTS",
                probe,
            )

    probe["http_status"] = http_status
    location = (http_headers.get("location") or "").strip()
    probe["http_location"] = location
    if http_status not in (301, 302, 307, 308):
        return (
            False,
            f"HTTP {http_root} → {http_status} (not a redirect). "
            "HSTS on a host that still serves the app over HTTP is the "
            "H2398 fail condition.",
            probe,
        )
    if not location.lower().startswith("https://"):
        return (
            False,
            f"HTTP redirect Location={location!r} is not HTTPS "
            "— refuse HSTS",
            probe,
        )

    return (
        True,
        f"HTTPS {https_health} → 200; HTTP {http_root} → {http_status} {location}",
        probe,
    )


def iter_braced_blocks(text: str, keyword: str) -> list[tuple[int, int, str]]:
    """Return (start, end, block) for each `keyword { ... }` with brace match."""
    blocks: list[tuple[int, int, str]] = []
    i = 0
    pat = re.compile(rf"\b{re.escape(keyword)}\b[^{{]*\{{")
    while True:
        m = pat.search(text, i)
        if not m:
            return blocks
        start = m.start()
        brace = m.end() - 1
        depth = 0
        j = brace
        while j < len(text):
            ch = text[j]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = j + 1
                    blocks.append((start, end, text[start:end]))
                    i = end
                    break
            j += 1
        else:
            raise RuntimeError(f"unbalanced braces starting at {start} for {keyword!r}")
    return blocks


def is_https_server(block: str) -> bool:
    return bool(
        re.search(r"(?m)^\s*listen\s+[^;]*\b443\b", block)
        or re.search(r"(?m)^\s*listen\s+[^;]*\bssl\b", block)
        or re.search(r"(?m)^\s*ssl_certificate\b", block)
    )


def is_http_only_server(block: str) -> bool:
    has_80 = bool(re.search(r"(?m)^\s*listen\s+[^;]*\b80\b", block))
    return has_80 and not is_https_server(block)


def include_line(snippet_dst: str, indent: str = "    ") -> str:
    return f"{indent}include {snippet_dst};"


def _inject_after_server_name(block: str, line: str) -> str:
    if line.strip() in block:
        return block
    # After the first server_name statement; else after the opening brace.
    m = re.search(r"(?m)^(\s*server_name\s+[^;]+;)\s*$", block)
    if m:
        insert_at = m.end()
        return block[:insert_at] + "\n" + line + block[insert_at:]
    m = re.search(r"\{", block)
    if not m:
        raise RuntimeError("server block has no opening brace")
    insert_at = m.end()
    return block[:insert_at] + "\n" + line + block[insert_at:]


def _inject_into_locations_with_add_header(block: str, line: str) -> str:
    """Repeat the include inside locations that already set add_header."""
    out = block
    # Walk locations from the end so offsets stay valid if we only replace
    # whole location strings via a collected list.
    locations = iter_braced_blocks(block, "location")
    if not locations:
        return out
    pieces: list[str] = []
    last = 0
    for start, end, loc in locations:
        pieces.append(block[last:start])
        new_loc = loc
        if "add_header" in loc and line.strip() not in loc:
            # After the location's opening brace.
            brace = loc.find("{")
            new_loc = loc[: brace + 1] + "\n" + line + loc[brace + 1 :]
        pieces.append(new_loc)
        last = end
    pieces.append(block[last:])
    return "".join(pieces)


def inject_security_headers(
    text: str,
    *,
    snippet_dst: str = DEFAULT_SNIPPET_DST,
) -> tuple[str, dict[str, int]]:
    """Insert the snippet include into every HTTPS server; never into HTTP-only.

    Returns (new_text, stats).
    """
    stats = {
        "https_servers": 0,
        "http_only_servers": 0,
        "https_touched": 0,
        "locations_touched": 0,
    }
    servers = iter_braced_blocks(text, "server")
    if not servers:
        raise RuntimeError("no server { } blocks found")

    line = include_line(snippet_dst)
    pieces: list[str] = []
    last = 0
    for start, end, block in servers:
        pieces.append(text[last:start])
        if is_http_only_server(block):
            stats["http_only_servers"] += 1
            if snippet_dst in block:
                raise RuntimeError(
                    "HSTS include already present in a listen-80 server — "
                    "refuse to keep that (H2398 fail condition). Remove it first."
                )
            pieces.append(block)
        elif is_https_server(block):
            stats["https_servers"] += 1
            new_block = block
            before_loc = new_block
            if snippet_dst not in new_block.split("location", 1)[0]:
                new_block = _inject_after_server_name(new_block, line)
            new_block = _inject_into_locations_with_add_header(new_block, line)
            if new_block != block:
                stats["https_touched"] += 1
            if new_block != before_loc:
                # count location includes roughly
                stats["locations_touched"] += new_block.count(snippet_dst) - before_loc.count(
                    snippet_dst
                )
            pieces.append(new_block)
        else:
            pieces.append(block)
        last = end
    pieces.append(text[last:])
    return "".join(pieces), stats


def https_include_leaked_into_http(text: str, snippet_dst: str) -> bool:
    for _s, _e, block in iter_braced_blocks(text, "server"):
        if is_http_only_server(block) and snippet_dst in block:
            return True
    return False


def install_snippet(src: Path, dst: Path) -> None:
    if not src.is_file():
        raise RuntimeError(f"snippet source missing: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"snippet: installed {src} → {dst}", flush=True)


def _run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(cmd), flush=True)
    return subprocess.run(
        cmd,
        check=check,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=False,
    )


def prove_hsts(host: str, timeout: float = 20.0) -> tuple[bool, str, dict[str, str]]:
    """Handoff prove-with: HEAD / must carry Strict-Transport-Security.

    `curl -sI` is HEAD. The app returns 405 on HEAD /, so the nginx
    `always` flag is load-bearing — without it the prove-with command fails.
    """
    url = f"https://{host}/"
    try:
        status, headers, _ = fetch(url, method="HEAD", timeout=timeout)
    except Exception as exc:  # noqa: BLE001
        try:
            status, headers, _ = fetch_hairpin(
                url, host, method="HEAD", timeout=timeout
            )
        except Exception as hairpin_exc:  # noqa: BLE001
            return (
                False,
                f"HEAD {url} failed: {type(exc).__name__}: {exc}; "
                f"hairpin: {type(hairpin_exc).__name__}: {hairpin_exc}",
                {},
            )
    hsts = headers.get(HSTS_TOKEN, "")
    extra = {
        "status": str(status),
        "strict-transport-security": hsts,
        "x-content-type-options": headers.get("x-content-type-options", ""),
        "x-frame-options": headers.get("x-frame-options", ""),
        "referrer-policy": headers.get("referrer-policy", ""),
        "permissions-policy": headers.get("permissions-policy", ""),
    }
    if not hsts:
        return False, f"HEAD {url} → {status} but no Strict-Transport-Security", extra
    if "max-age=" not in hsts.lower():
        return False, f"HSTS present but no max-age: {hsts!r}", extra
    return True, f"HEAD {url} → {status} {HSTS_TOKEN}: {hsts}", extra


def print_plan(host: str, nginx: Path, snippet_src: Path, snippet_dst: Path) -> None:
    print(
        f"""
## Plan (after HTTPS-stable GATE GO)

1. Confirm HTTPS {host}/api/health → 200 and HTTP→HTTPS redirect
2. Install {snippet_src} → {snippet_dst}
3. Include that snippet in every listen-443 server in {nginx}
   (and in every location that already has add_header)
4. Do NOT include it in any listen-80 server
5. nginx -t && systemctl reload nginx
6. Prove: curl -sI https://{host}/ | grep -i strict
7. Re-check: GET https://{host}/api/health still 200

Fail = enabling HSTS when step 1 is not green.
""".strip(),
        flush=True,
    )


def apply(
    *,
    host: str,
    nginx: Path,
    snippet_src: Path,
    snippet_dst: Path,
    skip_reload: bool,
) -> dict[str, object]:
    if not nginx.is_file():
        raise RuntimeError(f"nginx site missing: {nginx}")

    backup = Path(tempfile.gettempdir()) / "samudra.nginx.bak-h2398"
    original = nginx.read_text(encoding="utf-8")
    backup.write_text(original, encoding="utf-8")
    print(f"backup: {backup}", flush=True)

    if https_include_leaked_into_http(original, str(snippet_dst)):
        raise RuntimeError(
            "existing site already includes the HSTS snippet in a listen-80 "
            "server — refuse to apply on top of that"
        )

    install_snippet(snippet_src, snippet_dst)
    new_text, stats = inject_security_headers(original, snippet_dst=str(snippet_dst))
    print(f"inject: {stats}", flush=True)
    if stats["https_servers"] < 1:
        raise RuntimeError(
            "no listen-443 server in the site file — refuse HSTS "
            "(HTTP-only vhost is the fail condition)"
        )

    if new_text != original:
        nginx.write_text(new_text, encoding="utf-8")
        print(f"nginx: wrote includes into {nginx}", flush=True)
    else:
        print("nginx: includes already present (idempotent)", flush=True)

    if https_include_leaked_into_http(new_text, str(snippet_dst)):
        nginx.write_text(original, encoding="utf-8")
        raise RuntimeError("inject leaked into listen-80 — restored backup")

    try:
        _run(["nginx", "-t"])
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        nginx.write_text(original, encoding="utf-8")
        raise RuntimeError(f"nginx -t failed, restored backup: {exc}") from exc

    if not skip_reload:
        _run(["systemctl", "reload", "nginx"])
    else:
        print("skip-reload: left nginx running the previous config", flush=True)

    ok, reason, extra = prove_hsts(host)
    print(f"prove: {reason}", flush=True)
    for k, v in extra.items():
        if v:
            print(f"  {k}: {v}", flush=True)
    if not ok and not skip_reload:
        raise RuntimeError(f"HSTS prove-with failed after reload: {reason}")

    health_url = f"https://{host}{DEFAULT_HEALTH_PATH}"
    try:
        health_status, _, _ = fetch(health_url, method="GET")
    except Exception:
        health_status, _, _ = fetch_hairpin(health_url, host, method="GET")
    print(f"smoke: {health_url} → {health_status}", flush=True)
    if health_status != 200 and not skip_reload:
        raise RuntimeError(f"health smoke failed after reload: {health_status}")

    return {"stats": stats, "prove": extra, "health": health_status}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--host", default=DEFAULT_HOST, help="Public HTTPS Host to gate + prove")
    p.add_argument("--nginx-site", type=Path, default=Path(DEFAULT_NGINX))
    p.add_argument("--snippet-src", type=Path, default=default_snippet_src())
    p.add_argument("--snippet-dst", type=Path, default=Path(DEFAULT_SNIPPET_DST))
    p.add_argument("--health-path", default=DEFAULT_HEALTH_PATH)
    p.add_argument(
        "--apply",
        action="store_true",
        help="Install snippet + patch HTTPS servers + reload nginx (default: gate only)",
    )
    p.add_argument(
        "--skip-reload",
        action="store_true",
        help="With --apply: write files and nginx -t but do not reload (tests)",
    )
    p.add_argument(
        "--skip-live-gate",
        action="store_true",
        help="Skip the live HTTPS probe (hermetic tests / offline rewrite only)",
    )
    args = p.parse_args(argv)

    host = args.host.strip().lower().rstrip(".")
    if not host or " " in host or host.startswith("<"):
        print("error: refuse placeholder/empty host", file=sys.stderr)
        return 1

    if not args.skip_live_gate:
        ok, reason, probe = https_stable_gate(host, health_path=args.health_path)
        print(f"gate: {reason}", flush=True)
        for k, v in probe.items():
            print(f"  {k}: {v}", flush=True)
        if not ok:
            print(
                "REFUSE: HTTPS is not stable — Wave P10b / H2398 is NOT done. "
                "Do not enable HSTS.",
                flush=True,
            )
            print_plan(host, args.nginx_site, args.snippet_src, args.snippet_dst)
            return 2
        print("GATE GO: HTTPS is stable and HTTP redirects to HTTPS", flush=True)
    else:
        print("gate: skipped (--skip-live-gate)", flush=True)

    print_plan(host, args.nginx_site, args.snippet_src, args.snippet_dst)

    if not args.apply:
        print("dry: pass --apply to install the snippet and patch nginx", flush=True)
        return 0

    try:
        apply(
            host=host,
            nginx=args.nginx_site,
            snippet_src=args.snippet_src,
            snippet_dst=args.snippet_dst,
            skip_reload=args.skip_reload,
        )
    except Exception as exc:  # noqa: BLE001 — operator surface; always exit 3
        print(f"APPLY FAIL: {exc}", file=sys.stderr)
        return 3

    print(
        "DONE: HSTS present on HTTPS HEAD / — close H2398 with nginx snippet + curl -sI evidence",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
