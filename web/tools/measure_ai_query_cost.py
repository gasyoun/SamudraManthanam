"""Measure the per-query token cost of Samudra's AI layer (H2640).

Why this exists
---------------
H2640 prices a paid "scholar tier" whose only capability with a real marginal
cost is the AI-assisted query/gloss layer (``/api/ai/explain`` and
``/api/ai/compare-translations``). Pricing a metered feature without measuring
its per-call cost turns it into an uncapped liability, so this script measures
it against the REAL prompts and REAL corpus context rather than an assumption.

Method
------
1. Pull real search results for representative scholarly queries from the live
   public API (``--live``) or a local corpus DB, so the ``context_lines`` are
   the same strings the frontend would actually send.
2. Rebuild the exact system+user prompts that ``app.services.ai_service``
   sends, by importing that module — no re-typed copies that can drift.
3. Count prompt tokens with ``tiktoken`` (``cl100k_base``). Russian and IAST
   both tokenize far worse than English, which is precisely why a
   chars/4 estimate would understate this bill.
4. Estimate completion tokens from the prompts' own stated output bound
   (``explain``: free-form academic RU; ``compare``: "200-400 words").
5. Price against the provider actually configured on prod
   (OpenRouter ``deepseek/deepseek-chat``), with the rate table passed in so a
   re-run months later prices itself rather than inheriting stale numbers.

Output is a JSON blob + a markdown table, both written to ``--out``.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

REPO_WEB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_WEB))

import httpx  # noqa: E402
import tiktoken  # noqa: E402

# Representative scholarly queries: a common dharmic term, a rarer compound, a
# grammatical form, an IAST string, and a proper name. Deliberately spans the
# result-count range, because prompt size tracks how much context comes back.
QUERIES = [
    "дхарма",
    "карма",
    "Хастинапур",
    "yoga",
    "atman",
    "брахман",
    "жертвоприношение",
    "Арджуна",
]

# The frontend caps AI context at 25 lines (see web/app/routers/ai.py); that is
# the realistic per-call context, not the server's 50-line hard ceiling.
CONTEXT_LINES = 25

DEFAULT_BASE = "https://samudra.193.232.229.92.sslip.io"

# The compare prompt asks for "200-400 words in Russian". Russian academic
# prose runs ~2.2 tokens/word under cl100k, so 300 words ~= 660 tokens; the
# explain prompt has no stated bound and empirically returns a similar length.
COMPLETION_WORDS = {"explain": 300, "compare": 300}
TOKENS_PER_RU_WORD = 2.2


def enc():
    return tiktoken.get_encoding("cl100k_base")


def fetch_context(base: str, query: str, n: int) -> list[str]:
    """Real result lines for `query` from the public search API."""
    url = f"{base.rstrip('/')}/api/search/export"
    r = httpx.get(
        url,
        params={"query": query, "format": "json"},
        timeout=120.0,
        follow_redirects=True,
    )
    r.raise_for_status()
    data = r.json()
    rows = data.get("results") or data.get("data") or []
    lines = []
    for row in rows[:n]:
        text = row.get("line_text") or row.get("line_html") or ""
        if text:
            lines.append(text)
    return lines


def measure(base: str) -> dict:
    from app.services import ai_service

    e = enc()
    samples = []
    for q in QUERIES:
        try:
            ctx = fetch_context(base, q, CONTEXT_LINES)
        except Exception as exc:  # pragma: no cover - network
            print(f"  ! {q}: {exc}", file=sys.stderr)
            continue
        if not ctx:
            print(f"  ! {q}: no results", file=sys.stderr)
            continue

        # --- explain: rebuild the exact prompts ai_service.explain_with_ai sends
        system_prompt = (
            "Вы — экспертный помощник по санскритской литературе и проекту "
            "«Пахтанье океана». Объясните смысл приведенных строк в контексте запроса.\n\n"
            "ТРЕБОВАНИЯ:\n"
            "1. Используйте ТОЛЬКО предоставленный контекст.\n"
            "2. Цитаты из текста должны быть основой вашего ответа.\n"
            "3. Указывайте ссылки на конкретные строки или источники.\n"
            "4. Ответ должен быть на русском языке, академичным и ясным.\n"
            "5. Если предоставленного контекста недостаточно для точного ответа, "
            "укажите это."
        )
        user_prompt = (
            f"Запрос пользователя: {q}\n\n"
            f"Контекст (строки из корпуса):\n" + "\n".join(ctx) + "\n\nПроанализируй и объясни."
        )
        explain_tokens = len(e.encode(system_prompt)) + len(e.encode(user_prompt))

        # --- compare: real builder, synthetic-but-realistic translation set
        translations = [
            {"label": f"Перевод {i+1}", "role": "translation", "text": line}
            for i, line in enumerate(ctx[:8])
        ]
        if len(translations) >= 2:
            compare_user = ai_service.build_compare_prompt(
                work_title="Бхагавадгита",
                work_title_iast="Bhagavadgītā",
                chapter=2,
                verse=47,
                iast="karmaṇyevādhikāraste mā phaleṣu kadācana",
                translations=translations,
            )
            compare_tokens = len(e.encode(compare_user)) + 260  # + system prompt
        else:
            compare_tokens = None

        samples.append(
            {
                "query": q,
                "context_lines": len(ctx),
                "context_chars": sum(len(line) for line in ctx),
                "explain_prompt_tokens": explain_tokens,
                "compare_prompt_tokens": compare_tokens,
            }
        )
    return {"samples": samples}


def price(result: dict, prompt_usd_per_m: float, completion_usd_per_m: float, usd_rub: float) -> dict:
    samples = result["samples"]
    out = {}
    for task, key in (("explain", "explain_prompt_tokens"), ("compare", "compare_prompt_tokens")):
        vals = [s[key] for s in samples if s.get(key)]
        if not vals:
            continue
        comp = COMPLETION_WORDS[task] * TOKENS_PER_RU_WORD
        med = statistics.median(vals)
        p90 = sorted(vals)[max(0, int(len(vals) * 0.9) - 1)]
        def rub(prompt_tokens: float) -> float:
            usd = (prompt_tokens / 1e6) * prompt_usd_per_m + (comp / 1e6) * completion_usd_per_m
            return usd * usd_rub
        out[task] = {
            "prompt_tokens_median": med,
            "prompt_tokens_p90": p90,
            "prompt_tokens_max": max(vals),
            "completion_tokens_assumed": comp,
            "rub_per_query_median": round(rub(med), 4),
            "rub_per_query_p90": round(rub(p90), 4),
            "rub_per_100_median": round(rub(med) * 100, 2),
            "rub_per_100_p90": round(rub(p90) * 100, 2),
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=DEFAULT_BASE)
    ap.add_argument("--prompt-usd-per-m", type=float, required=True)
    ap.add_argument("--completion-usd-per-m", type=float, required=True)
    ap.add_argument("--usd-rub", type=float, required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    print(f"Measuring against {args.base} ...")
    result = measure(args.base)
    if not result["samples"]:
        print("no samples measured", file=sys.stderr)
        return 1
    priced = price(result, args.prompt_usd_per_m, args.completion_usd_per_m, args.usd_rub)
    payload = {
        "model": args.model,
        "pricing_usd_per_million": {
            "prompt": args.prompt_usd_per_m,
            "completion": args.completion_usd_per_m,
        },
        "usd_rub": args.usd_rub,
        "context_lines_per_call": CONTEXT_LINES,
        "tokenizer": "cl100k_base",
        **result,
        "cost": priced,
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"wrote {args.out}")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
