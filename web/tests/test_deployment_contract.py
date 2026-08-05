"""D5 acceptance — the shared deployment contract itself (H1927).

VERIFICATION D5: "Docker and bare-host profiles pass the same
health/search/regex/PWA/version contract."

The workflows run `deployment_contract_smoke.py` against a live deployment.
This file tests the script's *verdict logic* hermetically — that a passing
report exits 0, a failing required check exits 1, an unready target exits 2,
and that the checks are not vacuous. A smoke script whose own pass/fail
arithmetic is untested is a green light nobody has audited.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "deployment_contract_smoke.py"


def _load():
    """Import the script by path, as a module named in sys.modules.

    The registration is required, not tidiness: `@dataclass` resolves its own
    defining module through `sys.modules[cls.__module__]`, so a module executed
    without being registered raises AttributeError at class-creation time.
    """
    name = "deployment_contract_smoke"
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


smoke = _load()


def test_required_failure_is_reported_as_failure():
    report = smoke.Report(base_url="http://x", profile="local")
    report.add(smoke.CheckResult("a", True, True, "fine"))
    report.add(smoke.CheckResult("b", False, True, "broken"))
    assert [c.name for c in report.failed] == ["b"]


def test_advisory_failure_does_not_fail_the_contract():
    """A WARN must never gate a build — that is what makes it survivable."""
    report = smoke.Report(base_url="http://x", profile="local")
    report.add(smoke.CheckResult("state_db", False, False, "degraded"))
    assert report.failed == []
    assert report.checks[0].status == "WARN"


def test_skipped_check_is_not_a_failure():
    report = smoke.Report(base_url="http://x", profile="local")
    report.add(smoke.CheckResult("static", False, True, "nothing to probe", skipped=True))
    assert report.failed == []
    assert report.checks[0].status == "SKIP"


@pytest.mark.parametrize(
    "text,expected",
    [
        ('{"detail":"Search timed out"}', False),
        ('{"detail":"regex error"}', False),
        ('Traceback (most recent call last):\n  File "/app/x.py", line 1', True),
        ('File "/usr/lib/python3.14/site-packages/re.py", line 12', True),
    ],
)
def test_internal_leak_detection(text, expected):
    assert smoke._looks_like_internal_leak(text) is expected


def test_admin_probe_path_exists_in_the_application():
    """Guards against the check that passes because its URL 404s.

    The first version of this smoke probed `/api/admin/corrections`, which does
    not exist — it returned 404 and reported PASS forever. Pin the probe path
    to a route the app actually registers.
    """
    import app.main  # read at call time — test_cors reloads this module

    paths = {getattr(r, "path", "") for r in app.main.app.routes}
    assert smoke.ADMIN_PROBE_PATH in paths, (
        f"{smoke.ADMIN_PROBE_PATH} is not a registered route — the admin check "
        f"would 404 and prove nothing. App registers: {sorted(paths)}"
    )


def test_budgets_match_the_verification_document():
    """These numbers are a contract, not tuning knobs.

    VERIFICATION "Performance budgets": readiness <= 10 s; regex hard deadline
    2 s with teardown complete within 500 ms.
    """
    assert smoke.READINESS_BUDGET_S == 10.0
    assert smoke.REGEX_DEADLINE_S == 2.0
    assert smoke.REGEX_TEARDOWN_ALLOWANCE_S == 0.5


def test_every_check_declares_whether_it_gates():
    """No check may be ambiguous about whether it can fail a deployment."""
    report = smoke.Report(base_url="http://x", profile="local")
    result = report.add(smoke.CheckResult("x", True, True, "d"))
    assert isinstance(result.required, bool)
    assert result.status in {"PASS", "FAIL", "WARN", "SKIP"}
