"""Samudra Manthanam production health monitor.

Run once per cron invocation (every 15 minutes). Checks /api/health and a
search probe, logs every outcome, and writes a CRITICAL alert to the journal
file after ALERT_THRESHOLD consecutive failures (circuit-breaker).

Usage (cron line added by H2390):
  */15 * * * * /opt/samudra/venv/bin/python /opt/samudra/repo/scripts/health_monitor.py

Env overrides:
  SAMUDRA_BASE_URL     default: http://127.0.0.1:8000
  SAMUDRA_LOG_DIR      default: /opt/samudra/logs
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL = os.environ.get("SAMUDRA_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
LOG_DIR = os.environ.get("SAMUDRA_LOG_DIR", "/opt/samudra/logs")
TIMEOUT = 15  # seconds per HTTP call
ALERT_THRESHOLD = 5  # consecutive failures before CRITICAL journal entry
PROBE_QUERY = "Арджун"  # stable Russian query; should always return ≥1 result

LOG_FILE = os.path.join(LOG_DIR, "health_monitor.log")
JOURNAL_FILE = os.path.join(LOG_DIR, "health_monitor_journal.log")
STATE_FILE = os.path.join(LOG_DIR, ".health_monitor_state.json")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_state() -> dict:
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"consecutive_failures": 0, "last_alert_at": None}


def _save_state(state: dict) -> None:
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f)


def _append_log(line: str) -> None:
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def _append_journal(line: str) -> None:
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(JOURNAL_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def _http_get(path: str) -> tuple[int, dict | None]:
    """Return (status_code, parsed_json_or_None)."""
    url = BASE_URL + path
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            try:
                return resp.status, json.loads(body)
            except json.JSONDecodeError:
                return resp.status, None
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception as e:
        return 0, {"error": str(e)}


def _http_post_json(path: str, payload: dict) -> tuple[int, dict | None]:
    url = BASE_URL + path
    data = json.dumps(payload).encode("utf-8")
    try:
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            try:
                return resp.status, json.loads(body)
            except json.JSONDecodeError:
                return resp.status, None
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception as e:
        return 0, {"error": str(e)}


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_health() -> tuple[bool, str]:
    t0 = time.monotonic()
    code, body = _http_get("/api/health")
    elapsed = int((time.monotonic() - t0) * 1000)

    if code != 200:
        return False, f"health HTTP {code} ({elapsed}ms)"

    status = (body or {}).get("status", "?")
    if status != "ok":
        corpus_err = (body or {}).get("corpus_db", {}).get("error")
        state_err = (body or {}).get("state_db", {}).get("error")
        detail = f"corpus={corpus_err} state={state_err}"
        return False, f"health degraded ({elapsed}ms): {detail}"

    source_count = (body or {}).get("corpus_db", {}).get("source_count", "?")
    return True, f"health ok ({elapsed}ms) sources={source_count}"


def check_search() -> tuple[bool, str]:
    t0 = time.monotonic()
    code, body = _http_post_json(
        "/api/search", {"query": PROBE_QUERY, "mode": "plain"}
    )
    elapsed = int((time.monotonic() - t0) * 1000)

    if code != 200:
        return False, f"search HTTP {code} ({elapsed}ms)"

    total = (body or {}).get("total", "?")
    if isinstance(total, int) and total == 0:
        return False, f"search returned 0 results for probe query ({elapsed}ms)"

    return True, f"search ok ({elapsed}ms) total={total}"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    ts = _now_iso()
    state = _load_state()

    health_ok, health_msg = check_health()
    search_ok, search_msg = check_search()

    all_ok = health_ok and search_ok
    overall = "PASS" if all_ok else "FAIL"

    log_line = f"{ts} {overall} | {health_msg} | {search_msg}"
    _append_log(log_line)
    print(log_line)

    if all_ok:
        if state["consecutive_failures"] > 0:
            recovery_msg = (
                f"{ts} RECOVERY after {state['consecutive_failures']} failure(s)"
            )
            _append_log(recovery_msg)
            _append_journal(recovery_msg)
        state["consecutive_failures"] = 0
    else:
        state["consecutive_failures"] += 1
        fail_count = state["consecutive_failures"]

        if fail_count >= ALERT_THRESHOLD:
            alert_msg = (
                f"{ts} CRITICAL: {fail_count} consecutive failures — "
                f"INVESTIGATE {BASE_URL} | {health_msg} | {search_msg}"
            )
            _append_journal(alert_msg)
            print(alert_msg, file=sys.stderr)

    _save_state(state)


if __name__ == "__main__":
    main()
