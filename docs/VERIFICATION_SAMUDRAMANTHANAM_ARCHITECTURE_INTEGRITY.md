# VERIFICATION — SamudraManthanam architecture-integrity Wave 1

_Created: 30-07-2026 · Last updated: 30-07-2026_

Acceptance, performance, and risk companion to
[PLAN_SAMUDRAMANTHANAM_ARCHITECTURE_2026_2027.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/PLAN_SAMUDRAMANTHANAM_ARCHITECTURE_2026_2027.md).

## Global merge gate

Every new Wave-1 handoff must pass:

1. scoped hermetic tests;
2. security/adversarial tests for changed public boundaries;
3. migration/reversibility tests for schema or reference changes;
4. representative fixture-corpus build;
5. container boot and shared deployment-contract smoke;
6. documentation/status truth check;
7. full checksum-pinned corpus workflow when corpus inputs, converters,
   manifests, schemas, or generated-view contracts change.

Corpus-changing PRs and releases always run the complete corpus gate.

## Lane A — manifest and bundle

| ID | Acceptance criterion | Proof |
|---|---|---|
| A1 | Manifest schema rejects missing identity, hash, count, version, or provenance fields. | Schema/unit fixtures |
| A2 | Two builds from identical inputs are byte-identical. | Determinism test |
| A3 | A one-byte JSONL mutation fails hash validation before ingest. | Adversarial fixture |
| A4 | Publish validates the JSONL actually selected by the manifest, not an old HTML tree. | Ingest/publish integration test |
| A5 | Local and HTTP/object transports enforce the same expected checksum. | Resolver tests |
| A6 | Web DB, offline pack, and desktop reports name the same input-manifest hash. | Fixture build report |
| A7 | Prior bundle remains activatable after a failed candidate publication. | Rollback rehearsal |

## Lane B — durable identity

| ID | Acceptance criterion | Proof |
|---|---|---|
| B1 | Search, reader, exports, corrections, and retained AI/cache references expose or store the canonical tuple. | Contract/inventory tests |
| B2 | New durable records do not depend solely on numeric source/line ordinals. | Schema and code assertion |
| B3 | Every pre-migration retained reference resolves to the same canonical record after rebuild. | Zero-orphan report |
| B4 | Ambiguous or missing mappings fail visibly; none silently bind to another line. | Adversarial migration fixtures |
| B5 | Migration can be rerun safely and rolled back/recovered from its recorded backup. | Migration rehearsal |
| B6 | Legacy URLs/records remain readable during the compatibility span. | Compatibility suite |

## Lane C — regex, admin, and correction trust

| ID | Acceptance criterion | Proof |
|---|---|---|
| C1 | Catastrophic regex input cannot occupy an application worker beyond the hard deadline plus teardown allowance. | Adversarial timing test |
| C2 | Legitimate existing scholarly regex fixtures retain documented semantics. | Compatibility suite |
| C3 | Timeout/error payload is stable and reveals no internal details. | API contract test |
| C4 | Admin endpoints reject query-string credentials. | Security test |
| C5 | Test access logs contain no credential values. | Log assertion |
| C6 | Submitted email text alone cannot grant verified identity or elevated capability. | Identity/authorization tests |
| C7 | Anonymous proposals remain possible under the low-trust/rate-limit path. | End-to-end correction test |

## Lane D — migrations, runtime, and deployments

| ID | Acceptance criterion | Proof |
|---|---|---|
| D1 | Applied state migrations are ordered, checksum-recorded, and reject later edits. | Migration runner tests |
| D2 | Corpus schema changes rebuild rather than mutate a long-lived production corpus DB. | Policy/integration assertion |
| D3 | Existing routes and key response headers survive the bounded `main.py` extraction. | Route snapshot/contract tests |
| D4 | The exact production Python version is covered by CI and boots the application image. | CI matrix + image smoke |
| D5 | Docker and bare-host profiles pass the same health/search/regex/PWA/version contract. | Shared smoke report |
| D6 | Every corpus-changing PR and release runs the full pinned-bundle workflow. | Workflow path tests |
| D7 | Duplicate-suffix validation uses a categorised invariant, not an unexplained stale count ceiling. | Full-corpus report |

## Lanes E/F — corpus quality

For both Wisdomlib Stage C and H1438 Wave B:

| ID | Acceptance criterion | Proof |
|---|---|---|
| Q1 | Source enumeration and conversion are deterministic. | Two-run hashes/counts |
| Q2 | Structural and canonical-ID gates pass. | Corpus test report |
| Q3 | Parser anomalies are categorised, not discarded. | Checked anomaly report |
| Q4 | A stratified sample covers source/work, structure, low-confidence cases, and boundary cases. | Review sheet and verdict summary |
| Q5 | Only derived/approved artifacts cross the raw personal-archive fence. | Changed-file/provenance review |
| Q6 | Accepted output is registered by manifest and passes the full corpus-changing PR gate. | Manifest diff + workflow |

## Performance budgets

Wave 1 first records a reproducible production-corpus baseline. Unless current
measured behavior is already worse, enforce these initial ceilings:

- plain representative search: p95 no more than 500 ms on the reference host;
- reader/source lookup: p95 no more than 500 ms;
- regex: hard wall-clock deadline 2 s, teardown complete within 500 ms;
- application readiness with existing local DBs: no more than 10 s;
- manifest validation: linear in bundle bytes and no duplicate full-file reads
  without evidence;
- offline-pack and desktop generation: no more than 20% regression from the
  recorded baseline for identical inputs.

If the reference host cannot meet a numeric ceiling before the change, preserve
or improve its measured baseline and record the exception; do not silently
delete the budget.

## Risks and required spikes

| Risk | Probability/impact | Default mitigation or spike |
|---|---|---|
| Existing canonical IDs are not stable across all converter rebuilds. | Medium/high | Lane B begins with a two-build identity census; halt only if deterministic mapping is impossible. |
| Object/release storage transport becomes vendor-coupled. | Medium/medium | Keep resolver transport interface and local-file test implementation; manifest uses URL/object plus checksum. |
| Regex engine differs from Python semantics. | High/medium | Compatibility corpus first; fall back to killable process isolation for unsupported legitimate cases. |
| State migration finds orphaned ordinal references. | Medium/high | Emit categorised report; map by pinned corpus/content evidence; never guess. |
| `main.py` extraction causes startup/header drift. | Medium/medium | Route/header snapshots before refactor; small extraction commits. |
| Bare-host CI requires unavailable infrastructure. | Medium/medium | Container CI remains per-PR; bare rehearsal is scheduled/pre-release on an ephemeral authorized host. |
| Full-corpus workflow is too slow for corpus PRs. | Medium/medium | Cache immutable bundle by checksum; never skip correctness gates because of runtime. |
| H1438 branch contains raw or stale artifacts. | Medium/high | Inventory/diff first; preserve valid derived work; exclude raw personal material. |
| Wisdomlib partial scrape has gaps or duplicate shards. | Medium/medium | Deterministic shard ledger and completeness/anomaly report before conversion. |
| Dual desktop/web support creates divergent generated views. | Medium/high | One manifest input, shared identity mapping, golden parity samples, and release report. |
| H1485 overlaps generated-view contracts. | Medium/medium | Respect active owner; integrate only reviewed outputs after reconciliation. |
| Planning documentation drifts again. | High/medium | One living PLAN/ROADMAP, metadoc ledger, documentation-index conflict rule, and roadmap registration. |

## Autonomy-readiness gate

The gate passes only when:

- every new lane has an owner handoff;
- lanes E/F cite their existing owner rather than duplicates;
- all deliverables map to architecture, ordered steps, acceptance, and risks;
- no blocking `@DECIDE` or unresolved placeholder remains;
- prior-art reuse is explicit;
- the autonomy contract is copied into each new handoff;
- documentation and hub status point to this plan.

Gate verdict is written into the PLAN after handoff minting.

_Dr. Mārcis Gasūns_
