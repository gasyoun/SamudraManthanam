#!/usr/bin/env python3
"""Deterministic eval runner for SamudraManthanam (H6846).

Suite ``alignment-locus-gold`` grades the committed alignment gold against the
canonical-id and cardinality contract the parallel corpus relies on. No model,
no network, no new gold.

Usage::

    python evals/run_eval.py             # gold replay
    python evals/run_eval.py --canary    # gold passes AND a mutated id fails
    python evals/run_eval.py --json
"""

import argparse
import copy
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GOLD = REPO / "web" / "tests" / "fixtures" / "alignment_gold.jsonl"
CARDINALITY = re.compile(r"^\d+:\d+$")


def load_gold(path=GOLD):
    rows = []
    with open(path, "r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if line:
                row = json.loads(line)
                row["_lineno"] = lineno
                rows.append(row)
    return rows


def grade(rows):
    errors = []
    seen = set()
    for row in rows:
        lineno = row.get("_lineno", "?")
        group = row.get("group") or ""
        if not group:
            errors.append("line %s: empty group" % lineno)
            continue
        if group in seen:
            errors.append("line %s: duplicate group %r" % (lineno, group))
        seen.add(group)
        cardinality = row.get("cardinality") or ""
        match = CARDINALITY.match(cardinality)
        if not match:
            errors.append("line %s: cardinality %r is not n:m" % (lineno, cardinality))
            n_sa, n_ru = 1, 1
        else:
            n_sa, n_ru = (int(x) for x in cardinality.split(":"))
        want_sa = group + "#sa" if n_sa else None
        want_ru = group + "#ru" if n_ru else None
        if row.get("sa_id") != want_sa:
            errors.append("line %s: sa_id %r != %r for %s" % (lineno, row.get("sa_id"), want_sa, cardinality))
        if row.get("ru_id") != want_ru:
            errors.append("line %s: ru_id %r != %r for %s" % (lineno, row.get("ru_id"), want_ru, cardinality))
        if not (row.get("sa_text_fragment") or "").strip() and not (row.get("ru_text_fragment") or "").strip():
            errors.append("line %s: both text fragments are empty" % lineno)
        if not (row.get("alignment") or "").strip():
            errors.append("line %s: empty alignment" % lineno)
        for comm_id in row.get("comm_ids") or []:
            if not comm_id.startswith(group + ".comm"):
                errors.append("line %s: comm id %r outside group %r" % (lineno, comm_id, group))
    return errors


def mutate(rows):
    mutated = copy.deepcopy(rows)
    if mutated:
        bad = dict(mutated[0])
        bad["ru_id"] = bad["group"] + "#sa"
        mutated[0] = bad
    return mutated


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canary", action="store_true", help="also require a mutated id to fail")
    parser.add_argument("--json", action="store_true", help="print a JSON result object")
    args = parser.parse_args()

    rows = load_gold()
    gold_errors = grade(rows)
    result = {
        "suite": "alignment-locus-gold",
        "cases": len(rows),
        "gold": "PASS" if not gold_errors else "FAIL",
        "gold_errors": gold_errors,
    }

    ok = not gold_errors
    if args.canary:
        mutated_errors = grade(mutate(rows))
        result["canary"] = {
            "mutation": "first Russian id re-pointed at #sa",
            "mutation_result": "FAIL" if mutated_errors else "PASS",
            "mutation_errors": mutated_errors,
        }
        ok = ok and bool(mutated_errors)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=1))
    else:
        print("== alignment-locus-gold: gold %s (%d cases) ==" % (result["gold"], result["cases"]))
        for err in gold_errors:
            print("  - " + err)
        if args.canary:
            canary = result["canary"]
            print("== canary: mutated answer %s (expected FAIL) ==" % canary["mutation_result"])
            for err in canary["mutation_errors"]:
                print("  - " + err)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
