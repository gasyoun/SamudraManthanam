"""Post the day's word-of-the-day record to Telegram (H4955).

Reads `web/app/data/word_of_day_current.json` (written by
`word_of_day_generate.py`) and posts it to the channel named by
TELEGRAM_WOD_BOT_TOKEN / TELEGRAM_WOD_CHAT_ID.

**Known gap (per the H4955 spec's own "not yet decided" list):** no
Telegram/VK bot or channel has been provisioned for samskrtam.ru yet — this
site's social automation is distinct from the samskrte.ru tutoring-business
one referenced in Uprava's canonical customer-links doc, and no credentials
exist in this repo's settings/env today. Until MG provisions one, this
script has nothing to post to: it logs the record and exits 0 (not an
error — the nightly timer chains generate -> post, and a missing channel
must not fail the generate step's own success).

Usage:
    python scripts/word_of_day_post.py [--record PATH]
"""
import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "web"))
from app.settings import settings  # noqa: E402

DEFAULT_RECORD = (
    Path(settings.WORD_OF_DAY_RECORD_PATH)
    if settings.WORD_OF_DAY_RECORD_PATH
    else REPO_ROOT / "web" / "app" / "data" / "word_of_day_current.json"
)


def format_message(record: dict) -> str:
    lines = [
        f"Слово дня: {record['devanagari']} {record['iast']}",
        record["gloss"],
    ]
    if record.get("pos"):
        lines.append(f"({record['pos']})")
    example = record.get("example")
    if example:
        lines.append(f"\n«{example['text']}» — {example['source']}")
    lines.append(f"\n{record['source']}")
    return "\n".join(lines)


def post_to_telegram(token: str, chat_id: str, text: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps({"chat_id": chat_id, "text": text}).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        if resp.status != 200:
            raise RuntimeError(f"Telegram API returned {resp.status}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--record", type=Path, default=DEFAULT_RECORD)
    args = ap.parse_args()

    if not args.record.exists():
        print(f"word_of_day_post: no record at {args.record}, nothing to post", file=sys.stderr)
        sys.exit(1)

    record = json.loads(args.record.read_text(encoding="utf-8"))
    text = format_message(record)

    token = os.environ.get("TELEGRAM_WOD_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_WOD_CHAT_ID")
    if not token or not chat_id:
        print(
            "word_of_day_post: TELEGRAM_WOD_BOT_TOKEN/TELEGRAM_WOD_CHAT_ID not set — "
            "no samskrtam.ru social channel provisioned yet (H4955 documented gap). "
            "Would have posted:\n" + text
        )
        return

    post_to_telegram(token, chat_id, text)
    print(f"word_of_day_post: posted {record['entry_id']} to chat {chat_id}")


if __name__ == "__main__":
    main()
