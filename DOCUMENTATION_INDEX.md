# Documentation Index

_Created: 19-06-2026 · Last updated: 24-09-2026_

Purpose: tell humans and implementation agents which Markdown files are current, supporting, or historical.

Coverage is **generated** (H5426): the sections below are hand-owned editorial verdicts, and
[`scripts/documentation_index_check.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/scripts/documentation_index_check.py)
lists everything they do not name under *Every other Markdown file*. Run
`python scripts/documentation_index_check.py --check` (exit 1 = stale) or `--fix`.

## Current Primary Docs

- `README.md`: project overview and build/use notes.
- `docs/PLAN_SAMUDRAMANTHANAM_ARCHITECTURE_2026_2027.md`: **canonical
  planning index** — locked decisions, autonomy contract, and links to every
  current architecture/roadmap/implementation/verification layer.
- `docs/ROADMAP_SAMUDRAMANTHANAM_2026_2027.md`: **sole living status roadmap**
  — architecture integrity, corpus growth, and research workbench programme.
- `ROADMAP_2026_H2_DH_MOBILE.md`: historical H2 design and decision record;
  superseded for status.
- `docs/ARCHITECTURE_SAMUDRAMANTHANAM_CANONICAL_PLATFORM.md`: current
  canonical-bundle, stable-identity, dual-deployment, and dual-product
  architecture.
- `TARGET_ARCHITECTURE.md`: previous implementation baseline; consult the
  current architecture above for new work.
- `ARCHITECTURE_CRITIQUE_AND_OPEN_QUESTIONS.md` and
  `ARCHITECTURE_REVIEW_6_MONTH_ROADMAP.md`: historical review inputs.
- `CHANGELOG.md`: notable changes.
- `.ai_state.md`: session journal — queue, WIP, hypotheses.

## Phase 1 Design Specs (frozen — DH data layer)

- `docs/IMPLEMENTATION_HANDOFF_PHASE1.md`: **start here to implement Phase 1** — build order, file targets, gates, definition of done.
- `docs/LINE_ID_SCHEME.md`: frozen `{work}:{passage}` stable-ID contract (S1).
- `docs/CONVERTER_SPEC.md`: HTML→JSONL converter spec (S2).
- `docs/ALIGNMENT_SPEC.md`: Sanskrit↔Russian alignment spec (S3).
- `docs/TAG_CENSUS.md` / `.json`: measured corpus structural inventory (S2 prerequisite).
- `docs/DESIGN_SESSIONS_PLAN.md`: the five-session frontier plan (S1–S3 done, S4–S5 pending).
- `docs/PHASE2_PLAN.md`: Phase 2 plan (responsive + PWA shell + offline reader) — the gate before S4; Sonnet-tier, parallelizable with Phase 1.

## Current Supporting Docs

- `web/SEARCH_CONTRACT.md`: search behavior contract.
- `web/corpus_builder/wisdomlib/README.md`: Wisdomlib crawler operations, rights guardrails, Stage A/B/C commands, Cloudflare/rate-limit reality, and watcher usage.
- `web/corpus_builder/wisdomlib/CATALOG.md`: Wisdomlib bibliographic catalog summary generated from Stage A/B metadata.
- `use_cases.md`: user scenarios.
- `DEPLOYMENT.md`: no-Docker VPS first-time install + corpus publish.
- `OPS.md`: production day-2 operator path (pull/pip/restart/smoke/code rollback) for `/opt/samudra` (H2388).
- `CLAUDE.md`: agent guidance for this repository.
- `Corpus_builder/CLAUDE.md`: Corpus Builder-specific agent guidance.
- `Corpus_builder/docs/DECIDE_BRIEF_p5-gui-lcl-vs-cli_14-08-2026.md`: Phase 5 GUI-fate brief (H2435) — deferred; `cb` unused as translator.
- `docs/KATALOG_KOMBINACIJ_SBORKI_KORPUSA.md`: catalog of build combinations (H2719) — agent + human.
- `docs/DLYA_ANATOLIYA_DOBAVLENIE_IGNATIEVA_VS_STARAYA_SBORKA.md`: for Anatoly — Ignatiev add vs old `cb`.
- `web/corpus_builder/apply_errata.py`: typo → patch JSONL → rebuild HTML without `cb.exe` (H2720). Pilot `errata.yml` under `web/corpus_builder/errata/`.

## Historical Docs (`docs/archive/`)

Context only — do not treat as current instructions:

- `docs/archive/WEB_PLAN.md`: older from-scratch web architecture plan.
- `docs/archive/roadmap.md`: older 1-month roadmap (May–June 2026).
- `docs/archive/gemini-implementation-plan.md`, `docs/archive/gemini-fix-web.md`, `docs/archive/GEMINI_REVIEW.md`: older Gemini-era plans and reviews.
- `docs/archive/GEMINI_FLASH_IMPLEMENTATION_PLAN.md` + `docs/archive/GEMINI_FLASH_PHASE_0[1-5]_*.md`: completed Gemini Flash implementation phases (all [COMPLETE]).
- `docs/archive/CODE_ARCHITECTURE_REVIEW.md`: earlier code/architecture review.
- `docs/archive/PRE_GEMINI_AUDIT.md`: pre-Gemini audit (2026-05-15); all findings fixed.
- `docs/archive/ai_status.md`: previous AI implementation status.

## Reading Order For Implementation Agents

1. `DOCUMENTATION_INDEX.md`
2. `CLAUDE.md`
3. `docs/PLAN_SAMUDRAMANTHANAM_ARCHITECTURE_2026_2027.md`
4. `docs/ROADMAP_SAMUDRAMANTHANAM_2026_2027.md`
5. `docs/ARCHITECTURE_SAMUDRAMANTHANAM_CANONICAL_PLATFORM.md`
6. `web/SEARCH_CONTRACT.md`
7. `.ai_state.md`

## Wisdomlib Status Rule

Current Wisdomlib programme status belongs in
`docs/ROADMAP_SAMUDRAMANTHANAM_2026_2027.md`. Detailed crawler operation belongs
in `web/corpus_builder/wisdomlib/README.md`; the generated bibliographic summary
belongs in `web/corpus_builder/wisdomlib/CATALOG.md`.

## Conflict Rule

When documents conflict:

1. User messages and latest architecture decisions win.
2. `docs/PLAN_SAMUDRAMANTHANAM_ARCHITECTURE_2026_2027.md` and its linked
   living roadmap win over older plans/roadmaps.
3. `docs/ARCHITECTURE_SAMUDRAMANTHANAM_CANONICAL_PLATFORM.md` wins over older
   architecture plans.
4. Historical docs (`docs/archive/`) are context only.

## Maintenance Rule

When adding a new planning document:

- add it to this index,
- mark whether it is current, supporting, or historical,
- update `changelog.md`,
- run `python scripts/documentation_index_check.py --fix` so the generated coverage
  section below stays complete (a doc you do not categorise lands there, never nowhere).

<!-- BEGIN GENERATED: uncategorised-docs (scripts/documentation_index_check.py) -->

## Every other Markdown file (generated)

Generated by [`scripts/documentation_index_check.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/scripts/documentation_index_check.py)
— every `*.md` under the repo root and `docs/` that the hand-written sections above do
not name. Presence here is coverage, **not** a current/supporting/historical verdict:
promote a file into a section above the moment its status matters.

76 file(s):

- [`AGENTS.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/AGENTS.md): AGENTS.md — SamudraManthanam
- [`CODE_OF_CONDUCT.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/CODE_OF_CONDUCT.md): Contributor Covenant Code of Conduct
- [`CONTRIBUTING.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/CONTRIBUTING.md): Contributing to SamudraManthanam
- [`docs/ARCHITECTURE_SAMUDRAMANTHANAM_OXALPHA_CODE_REVIEW.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ARCHITECTURE_SAMUDRAMANTHANAM_OXALPHA_CODE_REVIEW.md): SamudraManthanam OxAlpha code-review architecture
- [`docs/ARCHITECTURE_SAMUDRAMANTHANAM_RESIDUAL.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ARCHITECTURE_SAMUDRAMANTHANAM_RESIDUAL.md): ARCHITECTURE — SamudraManthanam residual lanes
- [`docs/CORPUS_BUNDLE_SPEC.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/CORPUS_BUNDLE_SPEC.md): CORPUS BUNDLE SPEC — canonical manifest and immutable bundle
- [`docs/CORPUS_BUNDLE_SPEC.meta.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/CORPUS_BUNDLE_SPEC.meta.md): CORPUS_BUNDLE_SPEC.md — metadoc
- [`docs/DECISIONS_NEEDED.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/DECISIONS_NEEDED.md): Decisions needed — human input required
- [`docs/DECISIONS_NKRYA_PARALLEL_SUBMISSION_23-09-2026.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/DECISIONS_NKRYA_PARALLEL_SUBMISSION_23-09-2026.md): NKRYa parallel-corpus submission — decisions (23-09-2026)
- [`docs/DUP_SUFFIX_INVARIANT_REPORT.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/DUP_SUFFIX_INVARIANT_REPORT.md): Duplicate-suffix invariant report
- [`docs/DURABLE_REFERENCE_INVENTORY.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/DURABLE_REFERENCE_INVENTORY.md): Durable reference inventory — every place a corpus reference is retained
- [`docs/H2370_DEAD_VCL_STATIC_PROOF.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2370_DEAD_VCL_STATIC_PROOF.md): H2370 — dead VCL cleanup static proof
- [`docs/H2391_BRANDED_HOSTNAME_TLS_STATUS.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2391_BRANDED_HOSTNAME_TLS_STATUS.md): H2391 / Wave P5 — branded hostname + TLS status
- [`docs/H2392_OFFLINE_PACKS_PROD_STATUS.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2392_OFFLINE_PACKS_PROD_STATUS.md): H2392 / Wave P6 — offline packs build + serve on prod: status
- [`docs/H2393_ZERO_ORPHAN_PROD_GATE_STATUS.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2393_ZERO_ORPHAN_PROD_GATE_STATUS.md): H2393 / Wave P7 — zero-orphan durable-ref gate on prod state vs corpus
- [`docs/H2396_ADMIN_ENV_HARDENING_STATUS.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2396_ADMIN_ENV_HARDENING_STATUS.md): H2396 / Wave P10 — admin key / env hardening: status
- [`docs/H2398_NGINX_HSTS_SECURITY_HEADERS_STATUS.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2398_NGINX_HSTS_SECURITY_HEADERS_STATUS.md): H2398 / Wave P10b — HSTS + nginx security headers: status
- [`docs/H2415_IGNATIEV_ARCHIVE_REMAINDER_CENSUS.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2415_IGNATIEV_ARCHIVE_REMAINDER_CENSUS.md): H2415 — Ignatiev archive remainder census
- [`docs/H2417_PHASE3_LAZARUS_PORT.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2417_PHASE3_LAZARUS_PORT.md): H2417 — Corpus_builder Phase 3 Lazarus/FPC LCL port
- [`docs/H2427_GOLDEN_CAPTURE_P3_VERIFY.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2427_GOLDEN_CAPTURE_P3_VERIFY.md): H2427 — Phase 0 golden capture + Phase 3 Lazarus re-verify
- [`docs/H2428_LAZUTF8_ENCODING_LAYER.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2428_LAZUTF8_ENCODING_LAYER.md): H2428 — Corpus_builder Phase 1: unified lazUTF8 encoding layer
- [`docs/H2429_DCU_UNITS_CANONICAL_DIFF.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2429_DCU_UNITS_CANONICAL_DIFF.md): H2429 — dcu vs Units: sizes, API deltas, canonical pick
- [`docs/H2430_OTHERUNITFILES_SHARED_UTILS.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2430_OTHERUNITFILES_SHARED_UTILS.md): H2430 — OtherUnitFiles shared utils + SHARED_CODE
- [`docs/H2431_LINUX_LAZBUILD.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2431_LINUX_LAZBUILD.md): H2431 — Corpus_builder Phase 3 residual: Linux `lazbuild` of `cb.lpi`
- [`docs/H2432_CLI_HEADLESS_BUILD.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2432_CLI_HEADLESS_BUILD.md): H2432 — Corpus_builder Phase 4 headless CLI (`--build` / `--out`)
- [`docs/H2433_WEB_PIPELINE_HOOK.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2433_WEB_PIPELINE_HOOK.md): H2433 — Corpus_builder Phase 4 web-pipeline hook
- [`docs/H2449_IGNATIEV_BACKMATTER_LAYERS_CENSUS.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2449_IGNATIEV_BACKMATTER_LAYERS_CENSUS.md): H2449 — Ignatiev preface + glossary/bibliography layers census
- [`docs/H2450_PROSE_COMMENTARY_APPARATUS.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2450_PROSE_COMMENTARY_APPARATUS.md): H2450 — Prose commentary apparatus (`N. …` / `N. Источник:`)
- [`docs/H2450_REMAINDER_REPARSE.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2450_REMAINDER_REPARSE.md): H2450 residual reparse — free-bracket + auto census
- [`docs/H2738_MBH_WORD_ARTICLES_INDEXES.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2738_MBH_WORD_ARTICLES_INDEXES.md): H2738 — MBH Smirnov articles and indexes from Anatoly Drive
- [`docs/H2866_PAID_AI_SPEND_POLICY_STATUS.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2866_PAID_AI_SPEND_POLICY_STATUS.md): H2866 — paid-AI spend policy: status and evidence
- [`docs/IMPLEMENTATION_SAMUDRAMANTHANAM_ARCHITECTURE_INTEGRITY.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/IMPLEMENTATION_SAMUDRAMANTHANAM_ARCHITECTURE_INTEGRITY.md): IMPLEMENTATION — SamudraManthanam architecture-integrity Wave 1
- [`docs/IMPLEMENTATION_SAMUDRAMANTHANAM_OXALPHA_CODE_REVIEW.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/IMPLEMENTATION_SAMUDRAMANTHANAM_OXALPHA_CODE_REVIEW.md): SamudraManthanam OxAlpha code-review implementation
- [`docs/IMPLEMENTATION_SAMUDRAMANTHANAM_RESIDUAL.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/IMPLEMENTATION_SAMUDRAMANTHANAM_RESIDUAL.md): IMPLEMENTATION — SamudraManthanam residual wave-1
- [`docs/KATALOG_KOMBINACIJ_SBORKI_KORPUSA.meta.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/KATALOG_KOMBINACIJ_SBORKI_KORPUSA.meta.md): Metadoc — KATALOG_KOMBINACIJ_SBORKI_KORPUSA.md
- [`docs/LETTER_DRAFT_NKRYA_SANSKRIT_PARALLEL_AND_API_QUOTA_23-09-2026.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/LETTER_DRAFT_NKRYA_SANSKRIT_PARALLEL_AND_API_QUOTA_23-09-2026.md): Письма в НКРЯ: санскритский параллельный корпус + лимит API (черновики, 23-09-2026)
- [`docs/LOCAL_ONLY_DATA.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/LOCAL_ONLY_DATA.md): Local-only data inventory
- [`docs/MAYA_TANTRA_GLUED_DIGIT_MODE_H2377.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/MAYA_TANTRA_GLUED_DIGIT_MODE_H2377.md): Māyā-tantra glued-digit footnote mode (H2377)
- [`docs/NIRVANA_TANTRA_GLUED_DIGIT_REBASELINE_H2385.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/NIRVANA_TANTRA_GLUED_DIGIT_REBASELINE_H2385.md): Nirvāṇa-tantra glued-digit re-baseline (H2385)
- [`docs/NIRVANA_TANTRA_VERSE_COUNT_DROP_H2273.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/NIRVANA_TANTRA_VERSE_COUNT_DROP_H2273.md): Nirvāṇa-tantra verse-count drop justification (H2273)
- [`docs/OFFLINE_SEARCH_DESIGN.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/OFFLINE_SEARCH_DESIGN.md): S4 — Offline Search Design
- [`docs/OXALPHA_STATUS_GATE_DESIGN_2026.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/OXALPHA_STATUS_GATE_DESIGN_2026.md): Future OxAlpha status-gate design — SamudraManthanam (DESIGN ONLY, NOT ENABLED)
- [`docs/PERFORMANCE_BASELINES.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/PERFORMANCE_BASELINES.md): Performance baselines
- [`docs/PLAN_SAMUDRAMANTHANAM_ARCHITECTURE_2026_2027.meta.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/PLAN_SAMUDRAMANTHANAM_ARCHITECTURE_2026_2027.meta.md): PLAN_SAMUDRAMANTHANAM_ARCHITECTURE_2026_2027.meta.md — document record
- [`docs/PLAN_SAMUDRAMANTHANAM_OXALPHA_CODE_REVIEW_HARDENING_2026Q3.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/PLAN_SAMUDRAMANTHANAM_OXALPHA_CODE_REVIEW_HARDENING_2026Q3.md): SamudraManthanam OxAlpha code-review hardening plan
- [`docs/PLAN_SAMUDRAMANTHANAM_OXALPHA_CODE_REVIEW_HARDENING_2026Q3.meta.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/PLAN_SAMUDRAMANTHANAM_OXALPHA_CODE_REVIEW_HARDENING_2026Q3.meta.md): PLAN_SAMUDRAMANTHANAM_OXALPHA_CODE_REVIEW_HARDENING_2026Q3.meta.md
- [`docs/PLAN_SAMUDRAMANTHANAM_RESIDUAL_2026H2.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/PLAN_SAMUDRAMANTHANAM_RESIDUAL_2026H2.md): PLAN — SamudraManthanam residual replan (2026H2)
- [`docs/PLAN_SAMUDRAMANTHANAM_RESIDUAL_2026H2.meta.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/PLAN_SAMUDRAMANTHANAM_RESIDUAL_2026H2.meta.md): Metadoc — PLAN_SAMUDRAMANTHANAM_RESIDUAL_2026H2
- [`docs/ROADMAP_NKRYA_PARALLEL_RUSCORPORA_2026_2027.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ROADMAP_NKRYA_PARALLEL_RUSCORPORA_2026_2027.md): НКРЯ / ruscorpora.ru export roadmap — nkrya-parallel (2026–2027)
- [`docs/ROADMAP_SAMUDRAMANTHANAM_OXALPHA_CODE_REVIEW_2026Q3.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ROADMAP_SAMUDRAMANTHANAM_OXALPHA_CODE_REVIEW_2026Q3.md): SamudraManthanam OxAlpha code-review roadmap
- [`docs/ROADMAP_SAMUDRAMANTHANAM_RESIDUAL_2026H2.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ROADMAP_SAMUDRAMANTHANAM_RESIDUAL_2026H2.md): ROADMAP — SamudraManthanam residual (post-H2 truth-pass) — Moved
- [`docs/ROADMAP_SOMADEVA_KSS_ALIGNMENT_SCALEUP_2026_2027.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ROADMAP_SOMADEVA_KSS_ALIGNMENT_SCALEUP_2026_2027.md): Roadmap — Somadeva's Kathāsaritsāgara SA↔RU alignment: scale-up to all 18 lambakas
- [`docs/ROADMAP_SOMADEVA_KSS_ALIGNMENT_SCALEUP_2026_2027.meta.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ROADMAP_SOMADEVA_KSS_ALIGNMENT_SCALEUP_2026_2027.meta.md): Metadoc — ROADMAP_SOMADEVA_KSS_ALIGNMENT_SCALEUP_2026_2027.md
- [`docs/RUBANOVA_NKRYA_PIPELINE_MANUAL.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/RUBANOVA_NKRYA_PIPELINE_MANUAL.md): Rubanova НКРЯ pipeline manual — Russian sanskritism indexing + morphology, and the Sanskrit (DCS) side
- [`docs/RUBANOVA_NKRYA_PIPELINE_MANUAL.meta.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/RUBANOVA_NKRYA_PIPELINE_MANUAL.meta.md): Metadoc — RUBANOVA_NKRYA_PIPELINE_MANUAL.md
- [`docs/RUBANOVA_NKRYA_RUBRIC_DECLENSION_STATUS_2024_11.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/RUBANOVA_NKRYA_RUBRIC_DECLENSION_STATUS_2024_11.md): Rubric declension for index search — is it accounted for, does it exist?
- [`docs/SAMSKRTAM_CORPUS_LINGUIST_PAGE_DRAFT_NKRYA_SHOWCASE_23-09-2026.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/SAMSKRTAM_CORPUS_LINGUIST_PAGE_DRAFT_NKRYA_SHOWCASE_23-09-2026.md): Черновик страницы samskrtam.ru «Для корпусных лингвистов» — санскритско-русский параллельный корпус (витрина НКРЯ)
- [`docs/SOMADEVA_KSS_RIGHTS_COPYRIGHT_UNLOCK.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/SOMADEVA_KSS_RIGHTS_COPYRIGHT_UNLOCK.md): Somadeva Kathāsaritsāgara — rights status and what a proven copyright unlocks
- [`docs/SPEC_SAMUDRA_SCHOLAR_TIER_PAID_CAPABILITY_2026.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/SPEC_SAMUDRA_SCHOLAR_TIER_PAID_CAPABILITY_2026.md): Scholar tier — the paid corpus capability, costed against Samudra's real surface
- [`docs/SPEC_SAMUDRA_SCHOLAR_TIER_PAID_CAPABILITY_2026.meta.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/SPEC_SAMUDRA_SCHOLAR_TIER_PAID_CAPABILITY_2026.meta.md): Metadoc — SPEC_SAMUDRA_SCHOLAR_TIER_PAID_CAPABILITY_2026.md
- [`docs/SPEC_WORD_OF_THE_DAY_2026.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/SPEC_WORD_OF_THE_DAY_2026.md): Word of the Day — design spec
- [`docs/VERIFICATION_SAMUDRAMANTHANAM_ARCHITECTURE_INTEGRITY.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/VERIFICATION_SAMUDRAMANTHANAM_ARCHITECTURE_INTEGRITY.md): VERIFICATION — SamudraManthanam architecture-integrity Wave 1
- [`docs/VERIFICATION_SAMUDRAMANTHANAM_OXALPHA_CODE_REVIEW.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/VERIFICATION_SAMUDRAMANTHANAM_OXALPHA_CODE_REVIEW.md): SamudraManthanam OxAlpha code-review verification and risks
- [`docs/VERIFICATION_SAMUDRAMANTHANAM_RESIDUAL.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/VERIFICATION_SAMUDRAMANTHANAM_RESIDUAL.md): VERIFICATION — SamudraManthanam residual wave-1
- [`docs/WAVE_A_PDF_GLUED_DIGIT_REBASELINE_H2412_14.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/WAVE_A_PDF_GLUED_DIGIT_REBASELINE_H2412_14.md): Wave-A PDF glued-digit re-baseline (H2412–H2414)
- [`docs/acceptance/H2394_UX_ACCEPTANCE_BILINGUAL_DEEPLINK_CHECKLIST.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/acceptance/H2394_UX_ACCEPTANCE_BILINGUAL_DEEPLINK_CHECKLIST.md): H2394 — P9 UX acceptance: bilingual Sa+Ru + deep-link on prod
- [`docs/agents/domain.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/agents/domain.md): Domain Docs
- [`docs/agents/issue-tracker.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/agents/issue-tracker.md): Issue Tracker
- [`docs/agents/triage-labels.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/agents/triage-labels.md): Triage Labels
- [`docs/archive/GEMINI_FLASH_PHASE_01_FOUNDATION.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/archive/GEMINI_FLASH_PHASE_01_FOUNDATION.md): Gemini Flash Phase 01: Foundation
- [`docs/archive/GEMINI_FLASH_PHASE_02_SEARCH_READER.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/archive/GEMINI_FLASH_PHASE_02_SEARCH_READER.md): Gemini Flash Phase 02: Search and Reader
- [`docs/archive/GEMINI_FLASH_PHASE_03_IDENTITY_CORRECTIONS.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/archive/GEMINI_FLASH_PHASE_03_IDENTITY_CORRECTIONS.md): Gemini Flash Phase 03: Identity and Corrections
- [`docs/archive/GEMINI_FLASH_PHASE_04_AI.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/archive/GEMINI_FLASH_PHASE_04_AI.md): Gemini Flash Phase 04: AI
- [`docs/archive/GEMINI_FLASH_PHASE_05_DEPLOY_OPERATIONS.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/archive/GEMINI_FLASH_PHASE_05_DEPLOY_OPERATIONS.md): Gemini Flash Phase 05: Deploy and Operations
- [`docs/archive/ROADMAP_SAMUDRAMANTHANAM_RESIDUAL_2026H2.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/archive/ROADMAP_SAMUDRAMANTHANAM_RESIDUAL_2026H2.md): ROADMAP — SamudraManthanam residual (post-H2 truth-pass)
- [`docs/reviews/OXALPHA_RETROSPECTIVE_CODE_REVIEW_26-08-2026.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/reviews/OXALPHA_RETROSPECTIVE_CODE_REVIEW_26-08-2026.md): SamudraManthanam — OxAlpha 30-day retrospective code review (fixed window 26-07..25-08-2026)

<!-- END GENERATED: uncategorised-docs -->

_Dr. Mārcis Gasūns_
