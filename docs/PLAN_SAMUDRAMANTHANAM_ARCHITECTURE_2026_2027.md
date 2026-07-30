# PLAN — SamudraManthanam architecture and corpus programme, 2026–2027

_Created: 30-07-2026 · Last updated: 30-07-2026_

**Status: LIVING · canonical planning index.**

This plan turns SamudraManthanam's working FastAPI/SQLite/JSONL platform into a
reproducible, reference-stable, dual-product scholarly system while continuing
corpus growth. Architecture integrity comes first; corpus expansion follows
immediately and runs in parallel where its files do not overlap; research
workbench features follow once the data and identity contracts are dependable.
The horizon is twelve months, with Wave 1 divided into bounded unattended
handoffs.

The configured Claude Fable 5 planner failed twice before returning a draft.
The owner explicitly authorized a best-effort Codex takeover; this package was
therefore authored by Codex from the completed five-round `/ask` interview and
the repository audit.

## Layer documents

| Layer | Canonical document |
|---|---|
| Roadmap | [ROADMAP_SAMUDRAMANTHANAM_2026_2027.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ROADMAP_SAMUDRAMANTHANAM_2026_2027.md) |
| Architecture | [ARCHITECTURE_SAMUDRAMANTHANAM_CANONICAL_PLATFORM.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ARCHITECTURE_SAMUDRAMANTHANAM_CANONICAL_PLATFORM.md) |
| Wave-1 implementation | [IMPLEMENTATION_SAMUDRAMANTHANAM_ARCHITECTURE_INTEGRITY.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/IMPLEMENTATION_SAMUDRAMANTHANAM_ARCHITECTURE_INTEGRITY.md) |
| Verification and risks | [VERIFICATION_SAMUDRAMANTHANAM_ARCHITECTURE_INTEGRITY.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/VERIFICATION_SAMUDRAMANTHANAM_ARCHITECTURE_INTEGRITY.md) |
| Plan metadoc | [PLAN_SAMUDRAMANTHANAM_ARCHITECTURE_2026_2027.meta.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/PLAN_SAMUDRAMANTHANAM_ARCHITECTURE_2026_2027.meta.md) |

This plan supersedes the status and queue claims in
[PLAN_SAMUDRAMANTHANAM_RESIDUAL_2026H2.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/PLAN_SAMUDRAMANTHANAM_RESIDUAL_2026H2.md)
and its residual roadmap. Historical design specifications remain valid where
this plan does not replace their contracts.

## Decisions taken

These rulings are locked inputs, not suggestions for the executor to revisit.

| ID | Ruling | Consequence |
|---|---|---|
| R1 | Priority order is architecture integrity, then corpus growth, then research-platform features. | Waves follow that order, with safe corpus work parallel to architecture. |
| R2 | Plan for twelve months. | The roadmap spans August 2026 through July 2027. |
| R3 | Wave 1 is balanced. | It includes architecture work and bounded Wisdomlib/H1438 delivery. |
| R4 | Researchers, general readers, and corpus engineers are equal audiences. | Contracts must serve citation, reading, and reproducible-build workflows. |
| R5 | Success requires both a trustworthy production baseline and a major corpus milestone. | Neither code-only cleanup nor corpus-only growth completes the programme. |
| R6 | Wisdomlib Stage C is partly scraped, not blocked, and expected to finish within two weeks. | Treat it as active Wave-1 input, not an external blocker. |
| R7 | A versioned manifest plus canonical JSONL is authoritative. | HTML, SQLite, offline packs, and desktop files become derived views. |
| R8 | Docker Compose/VPS and bare systemd/uvicorn/nginx remain equally supported. | Both implement and pass one deployment contract. |
| R9 | Desktop and web remain fully supported products. | No desktop freeze; generated desktop views remain release outputs. |
| R10 | Corpus data uses a separate controlled data layer. | Application Git history no longer has to carry every large canonical payload. |
| R11 | Rights are ignored as a planning variable. | Rights cause no move, delay, gate, or workstream in this programme. |
| R12 | Corpus bundles use checksum-pinned versioned release/object-storage artifacts. | Deployments fetch or mount an immutable named bundle. |
| R13 | Corrections support anonymous low-trust proposals and verified elevated contributors. | Identity and authorization are separate from proposal intake. |
| R14 | Public regex remains, with a genuinely bounded engine. | Current synchronous Python `re` scanning is replaced behind the same contract. |
| R15 | Refactor the runtime through bounded extraction. | Split `main.py` responsibilities without a clean-architecture rewrite. |
| R16 | Use ordered checksum-tracked SQL migrations with separate corpus/state policies. | Rebuildable and mutable databases do not share migration semantics. |
| R17 | Keep Jinja, progressive vanilla JavaScript, PWA, and sqlite-wasm. | No SPA or framework migration is scheduled. |
| R18 | Wave 1 includes Wisdomlib Stage C and H1438 Wave-B in parallel. | Integrate existing work; do not mint duplicate corpus programmes. |
| R19 | Stable identity uses a reversible compatibility migration. | Dual-read old ordinals, migrate retained records, then deprecate external ordinals. |
| R20 | Wave-1 merge gates include hermetic, security, migration, fixture-corpus, and deployment smoke checks. | A targeted unit suite alone is insufficient. |
| R21 | The full checksum-pinned corpus is verified on every corpus-changing PR and every release. | Corpus changes explicitly opt into the full-data gate. |
| R22 | One contract suite verifies both deployment paths. | Container CI and scheduled/pre-release bare-host rehearsal share assertions. |
| R23 | Stable identity must satisfy a reversible zero-orphan invariant. | Every retained old reference resolves to the same canonical record after rebuild. |
| R24 | New corpus work requires deterministic output, structural gates, anomaly reports, and stratified human review. | Parser success alone is not publication acceptance. |
| R25 | Performance uses explicit budgets. | Search, regex, startup, and offline-pack budgets are measured and enforced. |
| R26 | On non-destructive ambiguity, apply the marked default, log it, and continue. | Executors do not stall on minor unspecified details. |
| R27 | Stop only for secret exposure, irreversible loss, an unresolvable canonical mismatch, corrupt source/artifact, or missing external authority. | Ordinary test failures receive one bounded repair attempt. |
| R28 | Handoffs authorize commit, PR, and merge when all gates pass. | No force-push; repository protections and reviews still apply. |
| R29 | Fence secrets, raw personal archives, destructive history rewrites, unrelated repositories, production-data mutation, and undocumented public-contract changes. | Rights analysis is explicitly not part of this fence. |
| R30 | Respect H1485's active claim and recover H1438's existing branch rather than duplicating either. | Use fresh worktrees and reconcile before overlap. |
| R31 | A failed parallel lane parks and reports; independent lanes continue. | Wave 1 need not ship as a single atomic PR. |

## Architectural invariants

1. `source_slug + canonical_id + corpus_version` is the durable public identity.
   Numeric database IDs and line ordinals are internal compatibility fields.
2. A checksum-pinned corpus manifest enumerates every canonical JSONL source and
   every generated artifact.
3. Build inputs are immutable; derived outputs are reproducible and replaceable.
4. `corpus.db` is rebuildable/read-mostly; `state.db` is mutable and migrated.
5. Web and desktop consume generated views from the same canonical bundle.
6. Search semantics remain governed by
   [web/SEARCH_CONTRACT.md](https://github.com/gasyoun/SamudraManthanam/blob/main/web/SEARCH_CONTRACT.md).
7. Both production profiles pass the same externally observable contract.
8. Existing shared transliteration and search implementations are reused.

## Wave-1 execution map

The implementation and verification documents define the exact steps and
acceptance checks. New handoff IDs are wired after the autonomy-readiness gate.

| Lane | Deliverable | Owner |
|---|---|---|
| A | Canonical manifest, immutable bundle contract, and publish validation | [H1924](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1924-Opus_SamudraManthanam_canonical-manifest-artifact-bundle_30.07.26.md) |
| B | Durable identity propagation and reversible zero-orphan migration | [H1925](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1925-Opus_SamudraManthanam_durable-reference-zero-orphan_30.07.26.md) |
| C | Hard-bounded regex, secure admin transport, and two-tier correction identity | [H1926](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1926-Opus_SamudraManthanam_bounded-regex-correction-trust_30.07.26.md) |
| D | Checksum migrations, bounded `main.py` extraction, and dual-deployment contract smoke tests | [H1927](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1927-Opus_SamudraManthanam_runtime-migrations-dual-deploy_30.07.26.md) |
| E | Wisdomlib Stage C completion and manifest integration | Existing [issue #17](https://github.com/gasyoun/SamudraManthanam/issues/17); no duplicate handoff |
| F | H1438 Wave-B branch recovery, validation, and merge | Existing [H1438](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1438-Sonnet_SamudraManthanam_ignatjev-tantras-puranas-ingest_22.07.26.md); no duplicate handoff |
| Guarded | Corpus Builder engine/GUI work | Existing H1485 claim; excluded from new Wave-1 ownership |

H1919–H1922 are superseded, archived Codex-routed records and must not be
executed. The replacement executor for Lanes A–D is Opus 5 1M
(`claude-opus-5[1m]`) in Claude Code, folder
`C:\Users\user\Documents\GitHub\SamudraManthanam`:

- H1924:
  `Read C:\Users\user\Documents\GitHub\Uprava\handoffs\H1924-Opus_SamudraManthanam_canonical-manifest-artifact-bundle_30.07.26.md and execute it.`
- H1926, independent:
  `Read C:\Users\user\Documents\GitHub\Uprava\handoffs\H1926-Opus_SamudraManthanam_bounded-regex-correction-trust_30.07.26.md and execute it.`
- H1925, after H1924:
  `Read C:\Users\user\Documents\GitHub\Uprava\handoffs\H1925-Opus_SamudraManthanam_durable-reference-zero-orphan_30.07.26.md and execute it.`
- H1927, independent substeps with final smoke after H1924–H1926:
  `Read C:\Users\user\Documents\GitHub\Uprava\handoffs\H1927-Opus_SamudraManthanam_runtime-migrations-dual-deploy_30.07.26.md and execute it.`

Dependencies:

- Lane A publishes the manifest schema before Lane B removes any external
  ordinal dependency or lanes E/F register new corpus artifacts.
- Lane C is code-path independent and may run in parallel with A.
- Lane D may start its extraction and test harness in parallel, but it consumes
  Lane A's bundle contract before final deployment smoke tests.
- Lanes E/F continue independently, then rebase and register through Lane A's
  manifest contract before merge.

## Autonomy contract

1. **Ambiguity:** use the marked default in this plan, write one concise entry
   under `.ai_state.md` Dev Notes, and continue.
2. **Bounded repair:** when a check fails with a local, deterministic cause,
   attempt one scoped repair and rerun the affected gate. Park the lane if the
   same acceptance failure persists.
3. **Immediate stop:** halt for secret exposure, irreversible data loss,
   canonical-reference mismatch without deterministic recovery, corrupt
   source/artifact, or required authority not granted by the handoff.
4. **Delivery:** worktree from current `origin/main`; targeted staging; commit;
   PR; merge only after all lane gates and required shared gates pass.
5. **Fence:** do not touch secrets, raw personal archives, unrelated
   repositories, production data, Git history, or public contracts outside the
   documented scope. Do not duplicate H1438/H1485 work.
6. **Rights:** do not start rights research, move work because of rights, or
   treat rights as a release gate for this programme.
7. **Parallel failure:** park and report the failed lane; continue independent
   lanes whose acceptance remains valid.

## Prior-art verdict

**PARTIAL — build only the gaps.**

Reuse:

- FastAPI routers/services and FTS5 search;
- `corpus.db`/`state.db` separation;
- JSONL converters, publication swap, offline packs, and desktop generators;
- `sanskrit-util` through the existing vendored adapter;
- existing NKРЯ, Somadeva, Wisdomlib, and Ignatiev pipelines;
- H1438 and H1485 ownership already in flight.

Build:

- the missing manifest and immutable bundle contract;
- durable-reference propagation and migration;
- real regex isolation;
- verified/anonymous identity separation and secret-safe administration;
- migration runner, bounded composition-root split, and common deployment tests;
- truthful planning/status wiring.

## Autonomy-readiness summary

**Verdict: PASS (30-07-2026).** Each new Wave-1 lane has an architecture
section, ordered file-level steps, acceptance criteria, identified risks, and a
collision-safe owner handoff. Existing corpus lanes retain their current owners
and gain explicit integration gates. No blocking `@DECIDE` or handoff
placeholder remains; nothing scheduled rebuilds an existing asset.

_Dr. Mārcis Gasūns_
