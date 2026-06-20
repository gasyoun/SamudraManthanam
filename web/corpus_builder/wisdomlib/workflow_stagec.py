#!/usr/bin/env python3
"""Validated GitHub Actions launcher for `crawl.py stageC`.

GitHub dispatch inputs arrive as environment variables. This script validates
them, builds an argv list, and invokes crawl.py without a shell so user input is
never interpreted as command text on the self-hosted runner.
"""
import os
import re
import subprocess
import sys

from crawl import SECTIONS


ALLOWED_CTYPES = {"article", "book", "compilation", "essay", "scripture"}
ALLOWED_LANGS = {"sanskrit", "sanskrit?", "pali", "prakrit?", "tibetan?"}
ALLOWED_PALI_MODES = {"any", "only", "exclude"}
SLUG_RE = re.compile(r"^[a-z0-9-]+$")


def _env(env, name, default=""):
    return env.get(name, default).strip()


def _csv(value):
    return [x.strip() for x in value.split(",") if x.strip()]


def _validate_tokens(name, value, allowed=None, pattern=None):
    tokens = _csv(value)
    for token in tokens:
        if allowed is not None and token not in allowed:
            raise ValueError(f"invalid {name}: {token!r}")
        if pattern is not None and not pattern.match(token):
            raise ValueError(f"invalid {name}: {token!r}")
    return tokens


def _int_env(env, name, default, min_value, max_value):
    raw = _env(env, name, str(default))
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if value < min_value or value > max_value:
        raise ValueError(f"{name} must be between {min_value} and {max_value}")
    return value


def _float_env(env, name, default, min_value, max_value):
    raw = _env(env, name, str(default))
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number") from exc
    if value < min_value or value > max_value:
        raise ValueError(f"{name} must be between {min_value} and {max_value}")
    return value


def build_argv(env=os.environ):
    argv = ["crawl.py", "stageC"]
    for lang in _validate_tokens("lang", _env(env, "WL_LANG", "sanskrit"), ALLOWED_LANGS):
        argv += ["--lang", lang]
    for section in _validate_tokens("section", _env(env, "WL_SECTION"), set(SECTIONS)):
        argv += ["--section", section]
    for ctype in _validate_tokens("ctype", _env(env, "WL_CTYPE"), ALLOWED_CTYPES):
        argv += ["--ctype", ctype]
    for slug in _validate_tokens("slug", _env(env, "WL_SLUG"), pattern=SLUG_RE):
        argv += ["--slug", slug]

    if _env(env, "WL_ENGLISH", "false").lower() == "true":
        argv.append("--english")

    pali_mode = _env(env, "WL_PALI_MODE", "any")
    if pali_mode not in ALLOWED_PALI_MODES:
        raise ValueError(f"invalid pali_mode: {pali_mode!r}")
    if pali_mode == "only":
        argv.append("--pali")
    elif pali_mode == "exclude":
        argv.append("--no-pali")

    min_words = _int_env(env, "WL_MIN_WORDS", 0, 0, 100_000_000)
    if min_words:
        argv += ["--min-words", str(min_words)]
    limit = _int_env(env, "WL_LIMIT", 0, 0, 100_000)
    if limit:
        argv += ["--limit", str(limit)]

    # Refuse a full-corpus crawl with no selection: clearing `lang` (or leaving
    # every filter blank) would otherwise silently select all ~838 books. Require
    # at least one selecting filter (or an explicit --limit) to broaden on purpose.
    SELECTORS = ("--lang", "--section", "--ctype", "--slug",
                 "--english", "--pali", "--no-pali", "--min-words", "--limit")
    if not any(flag in argv for flag in SELECTORS):
        raise ValueError(
            "no selection filter set — refusing an unfiltered full-corpus crawl; "
            "set at least one of lang/section/ctype/slug/english/pali/min_words/limit")

    argv += ["--workers", str(_int_env(env, "WL_WORKERS", 1, 1, 8))]
    delay = _float_env(env, "WL_DELAY", 5, 0, 3600)
    argv += ["--delay", f"{delay:g}"]
    return argv


def main():
    try:
        argv = build_argv()
    except ValueError as exc:
        print(f"input validation failed: {exc}", file=sys.stderr)
        return 2
    print("running:", " ".join(argv))
    return subprocess.run([sys.executable] + argv, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
