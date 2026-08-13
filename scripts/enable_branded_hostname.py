#!/usr/bin/env python3
"""DNS-gated branded hostname enablement for Samudra Manthanam (Wave P5 / H2391).

Hard gate (handoff acceptance):
  - A branded hostname is DONE only when its A-record points at the VPS and
    HTTPS returns 200 on /api/health.
  - Missing or wrong DNS must NEVER be treated as done (exit 2).

sslip.io remains the permanent fallback Host; this script never removes it.

Typical flow on the LXC (root@193.232.229.92)::

  # 1) Human creates A-record (recommended: samudra.samskrte.ru → 193.232.229.92)
  # 2) Gate + dry plan (no mutations):
  python3 /opt/samudra/repo/scripts/enable_branded_hostname.py \\
      --hostname samudra.samskrte.ru

  # 3) When gate is GO, apply nginx server_name + certbot + smoke:
  python3 /opt/samudra/repo/scripts/enable_branded_hostname.py \\
      --hostname samudra.samskrte.ru --apply

Exit codes:
  0  GO (DNS OK; apply succeeded if --apply)
  2  DNS missing / wrong IP / NXDOMAIN  (NOT done)
  3  apply/runtime failure after DNS was OK
  1  usage / local errors
"""

from __future__ import annotations

import argparse
import re
import shutil
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

# Windows / UTF-8 consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

DEFAULT_EXPECTED_IP = "193.232.229.92"
DEFAULT_SSLIP = "samudra.193.232.229.92.sslip.io"
DEFAULT_NGINX = "/etc/nginx/sites-available/samudra"
DEFAULT_HEALTH_PATH = "/api/health"


def resolve_a_records(hostname: str) -> list[str]:
    """Return unique IPv4 A answers for hostname (empty on NXDOMAIN/no A)."""
    answers: list[str] = []
    try:
        infos = socket.getaddrinfo(hostname, None, socket.AF_INET, socket.SOCK_STREAM)
    except socket.gaierror:
        return []
    for info in infos:
        ip = info[4][0]
        if ip not in answers:
            answers.append(ip)
    return answers


def dns_gate(hostname: str, expected_ip: str) -> tuple[bool, str, list[str]]:
    """Return (ok, reason, answers). ok False ⇒ must not treat as done."""
    answers = resolve_a_records(hostname)
    if not answers:
        return (
            False,
            f"DNS NXDOMAIN or no A-record for {hostname!r} "
            f"(human must create A → {expected_ip} first)",
            answers,
        )
    if expected_ip not in answers:
        return (
            False,
            f"DNS A for {hostname!r} is {answers}, expected {expected_ip} "
            f"(refuse certbot until pointed at this VPS)",
            answers,
        )
    return True, f"A {hostname} → {answers} includes {expected_ip}", answers


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


def ensure_server_name(nginx_path: Path, hostname: str, sslip: str) -> bool:
    """Ensure hostname appears in every server_name line that mentions sslip.

    Returns True if the file was modified.
    """
    text = nginx_path.read_text(encoding="utf-8")
    if re.search(rf"(?m)^\s*server_name\s+[^;]*\b{re.escape(hostname)}\b", text):
        print(f"nginx: server_name already includes {hostname}", flush=True)
        return False

    def _inject(match: re.Match[str]) -> str:
        line = match.group(0)
        if hostname in line:
            return line
        # Insert branded name first, keep existing names (sslip fallback).
        return re.sub(
            r"server_name\s+",
            f"server_name {hostname} ",
            line,
            count=1,
        )

    new_text, n = re.subn(
        rf"(?m)^\s*server_name\s+[^;]*\b{re.escape(sslip)}\b[^;]*;",
        _inject,
        text,
    )
    if n == 0:
        # Fallback: any server_name line in the samudra site file.
        new_text, n = re.subn(
            r"(?m)^\s*server_name\s+[^;]+;",
            _inject,
            text,
        )
    if n == 0:
        raise RuntimeError(
            f"no server_name line found in {nginx_path}; "
            "edit manually then re-run with --apply"
        )
    nginx_path.write_text(new_text, encoding="utf-8")
    print(f"nginx: added {hostname} to {n} server_name line(s) in {nginx_path}", flush=True)
    return True


def certbot_issue(hostname: str, email: str | None, dry_run_certbot: bool) -> None:
    certbot = shutil.which("certbot")
    if not certbot:
        raise RuntimeError("certbot not on PATH (apt install certbot python3-certbot-nginx)")
    cmd = [
        certbot,
        "--nginx",
        "-d",
        hostname,
        "--non-interactive",
        "--agree-tos",
        "--redirect",
    ]
    if email:
        cmd.extend(["--email", email])
    else:
        cmd.append("--register-unsafely-without-email")
    if dry_run_certbot:
        cmd.append("--dry-run")
    _run(cmd)


def smoke_https(hostname: str, health_path: str, timeout: float = 20.0) -> int:
    """Return HTTP status via curl -I against https://hostname/health_path."""
    curl = shutil.which("curl")
    if not curl:
        raise RuntimeError("curl not on PATH")
    url = f"https://{hostname}{health_path}"
    proc = subprocess.run(
        [
            curl,
            "-sS",
            "-o",
            "/dev/null",
            "-w",
            "%{http_code}",
            "--max-time",
            str(int(timeout)),
            "-I",
            url,
        ],
        check=False,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
    )
    code_str = (proc.stdout or "").strip()
    try:
        return int(code_str)
    except ValueError:
        print(f"smoke: curl failed rc={proc.returncode} out={code_str!r} err={proc.stderr!r}", flush=True)
        return 0


def print_plan(hostname: str, expected_ip: str, nginx: Path, sslip: str) -> None:
    print(
        f"""
## Plan (after DNS GO)

1. Ensure A-record:  {hostname}  →  {expected_ip}
2. Add {hostname} to server_name in {nginx}
   (keep {sslip} as permanent fallback Host)
3. nginx -t && systemctl reload nginx
4. certbot --nginx -d {hostname} --redirect
5. Smoke: curl -I https://{hostname}/api/health   → expect 200
6. Smoke fallback: curl -I https://{sslip}/api/health → still 200
7. Optional: set PUBLIC_BASE_URL=https://{hostname} in /opt/samudra/.env
   and restart samudra (does not remove sslip CORS if both listed)

Do NOT close H2391 / Wave P5 until step 5 returns 200.
""".strip(),
        flush=True,
    )


def apply(
    hostname: str,
    *,
    expected_ip: str,
    nginx: Path,
    sslip: str,
    email: str | None,
    certbot_dry_run: bool,
    health_path: str,
    skip_certbot: bool,
) -> None:
    if not nginx.is_file():
        raise RuntimeError(f"nginx site missing: {nginx}")

    # Backup once per apply
    backup = Path(tempfile.gettempdir()) / f"samudra.nginx.bak-h2391-{hostname}"
    backup.write_text(nginx.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"backup: {backup}", flush=True)

    ensure_server_name(nginx, hostname, sslip)
    _run(["nginx", "-t"])
    _run(["systemctl", "reload", "nginx"])

    if not skip_certbot:
        certbot_issue(hostname, email=email, dry_run_certbot=certbot_dry_run)
    else:
        print("skip-certbot: left TLS issuance to the operator", flush=True)

    # certbot --nginx rewrites the vhost; re-apply H2398 includes so a new
    # 443 server does not ship without HSTS (sslip already has them).
    try:
        import enable_security_headers as _hsts
    except ImportError:
        _hsts = None
    if _hsts is not None:
        snippet_src = _hsts.default_snippet_src()
        snippet_dst = Path(_hsts.DEFAULT_SNIPPET_DST)
        if snippet_src.is_file():
            current = nginx.read_text(encoding="utf-8")
            _hsts.install_snippet(snippet_src, snippet_dst)
            rewritten, stats = _hsts.inject_security_headers(
                current, snippet_dst=str(snippet_dst)
            )
            if rewritten != current:
                nginx.write_text(rewritten, encoding="utf-8")
                print(f"hsts: re-applied includes after certbot ({stats})", flush=True)
                _run(["nginx", "-t"])
                _run(["systemctl", "reload", "nginx"])
            else:
                print(f"hsts: includes already present ({stats})", flush=True)
        else:
            print(f"hsts: snippet source missing at {snippet_src} — skip", flush=True)
    else:
        print("hsts: enable_security_headers not importable — skip", flush=True)

    if certbot_dry_run or skip_certbot:
        print("apply: certbot dry-run/skip — skip live HTTPS smoke", flush=True)
        return

    code = smoke_https(hostname, health_path)
    print(f"smoke: https://{hostname}{health_path} → {code}", flush=True)
    if code != 200:
        raise RuntimeError(
            f"branded HTTPS smoke failed (got {code}, want 200) — "
            "not done; inspect certbot/nginx logs"
        )

    # Fallback must remain
    fb = smoke_https(sslip, health_path)
    print(f"smoke fallback: https://{sslip}{health_path} → {fb}", flush=True)
    if fb != 200:
        print(
            "WARNING: sslip fallback did not return 200; investigate before claiming done",
            flush=True,
        )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument(
        "--hostname",
        required=True,
        help="Branded FQDN (recommended: samudra.samskrte.ru). Must already resolve.",
    )
    p.add_argument("--expected-ip", default=DEFAULT_EXPECTED_IP)
    p.add_argument("--sslip", default=DEFAULT_SSLIP, help="Fallback Host that must stay in server_name")
    p.add_argument("--nginx-site", type=Path, default=Path(DEFAULT_NGINX))
    p.add_argument("--health-path", default=DEFAULT_HEALTH_PATH)
    p.add_argument(
        "--apply",
        action="store_true",
        help="Mutate nginx + run certbot after DNS gate passes (default: gate+plan only)",
    )
    p.add_argument(
        "--email",
        default=None,
        help="Let's Encrypt account email (else --register-unsafely-without-email)",
    )
    p.add_argument(
        "--certbot-dry-run",
        action="store_true",
        help="With --apply: run certbot --dry-run only (no real cert)",
    )
    p.add_argument(
        "--skip-certbot",
        action="store_true",
        help="With --apply: only inject server_name + reload nginx",
    )
    args = p.parse_args(argv)

    hostname = args.hostname.strip().lower().rstrip(".")
    if not hostname or " " in hostname or hostname.startswith("<"):
        print("error: refuse placeholder/empty hostname", file=sys.stderr)
        return 1

    ok, reason, answers = dns_gate(hostname, args.expected_ip)
    print(f"dns: {reason}", flush=True)
    if answers:
        print(f"dns answers: {answers}", flush=True)

    if not ok:
        print(
            "REFUSE: DNS missing/wrong — Wave P5 / H2391 is NOT done "
            "(human A-record first). sslip fallback stays primary.",
            flush=True,
        )
        print_plan(hostname, args.expected_ip, args.nginx_site, args.sslip)
        return 2

    print("GATE GO: DNS points at this VPS", flush=True)
    print_plan(hostname, args.expected_ip, args.nginx_site, args.sslip)

    if not args.apply:
        print("dry: pass --apply to mutate nginx + certbot on this host", flush=True)
        return 0

    try:
        apply(
            hostname,
            expected_ip=args.expected_ip,
            nginx=args.nginx_site,
            sslip=args.sslip,
            email=args.email,
            certbot_dry_run=args.certbot_dry_run,
            health_path=args.health_path,
            skip_certbot=args.skip_certbot,
        )
    except Exception as exc:  # noqa: BLE001 — operator surface; always exit 3
        print(f"APPLY FAIL: {exc}", file=sys.stderr)
        return 3

    print("DONE: branded HTTPS smoke 200 — close H2391 with cert path + nginx server_name evidence", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
