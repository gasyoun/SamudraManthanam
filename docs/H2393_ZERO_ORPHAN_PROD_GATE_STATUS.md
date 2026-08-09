# H2393 / Wave P7 — zero-orphan durable-ref gate on prod state vs corpus

_Created: 09-08-2026 · Last updated: 09-08-2026_

**Handoff:** [H2393](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2393-Sonnet_SamudraManthanam_prod-zero-orphan-gate-prod-state_07.08.26.md)
**Executor:** Sonnet 5 (`claude-sonnet-4-5`)
**Verdict 09-08-2026: RAN ON REAL PROD DATA — PASS, but vacuously (0 retained references currently in prod `state.db`).**

## Acceptance (locked in the handoff)

| Criterion | Status 09-08-2026 |
|---|---|
| `zero_orphan_report.py` runs against prod state+corpus | **done** — real `/opt/samudra/db/state.db` + `/opt/samudra/db/corpus.db` on `root@193.232.229.92` |
| Report artifact with counts | [`reports/zero_orphan_prod_2026-08-09.json`](https://github.com/gasyoun/SamudraManthanam/blob/main/reports/zero_orphan_prod_2026-08-09.json) |
| Fail = report only on fixture DB | **honoured** — this run used the real prod DBs, not the hermetic fixtures in [`web/tests/test_zero_orphan.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/tests/test_zero_orphan.py) |

## What was run

```
ssh root@193.232.229.92
cd /opt/samudra/repo/web
/opt/samudra/venv/bin/python scripts/zero_orphan_report.py \
  --before /opt/samudra/db/backups/corpus_20260808_095256.db \
  --candidate /opt/samudra/db/corpus.db \
  --state /opt/samudra/db/state.db \
  --json /tmp/zero_orphan_prod_report.json \
  --rollback-rehearsal
```

- **`--before`** = the most recent pre-rebuild backup on prod, `corpus_version=v2026.07.15`, 611,569 lines, 183 sources.
- **`--candidate`** = the live `corpus.db`, `corpus_version=2026.08`, 671,250 lines, 230 sources (a real rebuild — source and line counts both shifted, which is exactly the condition B5 exists to catch).
- **`--state`** = the live prod `state.db`.

## Result

```
before=v2026.07.15 (611569 lines) → candidate=2026.08 (671250 lines)
references checked: 0
rollback rehearsal: SAFE ({})
ZERO-ORPHAN: PASS
EXIT: 0
```

Full JSON: [`reports/zero_orphan_prod_2026-08-09.json`](https://github.com/gasyoun/SamudraManthanam/blob/main/reports/zero_orphan_prod_2026-08-09.json).

## The honest caveat (why "PASS" needs a qualifier)

`references_checked: 0`. Prod `state.db`'s `corrections` table currently holds
**zero rows** — the migrated `canonical_id` / `source_slug` / `ref_status` columns
exist (schema is live, per [`DURABLE_REFERENCE_INVENTORY.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/DURABLE_REFERENCE_INVENTORY.md)),
but no correction has been submitted against production yet, so there is nothing
for the gate to orphan. This run proves:

- the script executes end-to-end against real, non-fixture prod DBs (satisfies
  the handoff's literal fail condition — "report only on fixture DB" did **not**
  happen);
- the rollback rehearsal path is safe on real data;
- the plumbing (SSH access, venv, paths, DB permissions) all works for future runs.

It does **not** prove zero-orphan survival of any *real* retained reference across
a rebuild, because there are no real retained references in prod yet. That
stronger claim — proven in [`test_zero_orphan.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/tests/test_zero_orphan.py)
against a fixture that deliberately shifts every ordinal — still only has fixture
evidence at real-prod-corrections scale. This gate should be re-run once the
first production correction lands and a corpus rebuild happens after it, to get
a non-vacuous `references_checked > 0` result.

## Follow-up

- [ ] Re-run this gate after the first real correction + rebuild cycle to get a
  non-zero `references_checked`. No new handoff needed — routine re-run of this
  same command is sufficient; note the result in this doc or the next Wave P
  status sweep.

_Dr. Mārcis Gasūns_
