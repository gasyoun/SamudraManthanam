# Frontier Design-Session Plan — H2 2026

**Status:** Active · 2026-06-12
**Premise:** Frontier-model (Fable-tier) time is spent only on five design/review
sessions, each producing a durable written artifact. Implementation then runs on
cheaper model tiers (Sonnet/Opus) against those artifacts. Bulk corpus processing,
if any, runs on Haiku via the Batches API.

Rights constraint applies to every session: corpus texts are not cleared for open
redistribution — no public dumps, no DOI'd datasets, no public TEI downloads.
Everything ships inside the app and its search service only.

---

## Session 1 — Line-ID scheme ✅ DONE (2026-06-12)

- **Deliverable:** [docs/LINE_ID_SCHEME.md](LINE_ID_SCHEME.md)
- **Output:** `{work}:{passage}` scheme, three source classes (verse / dictionary /
  prose), duplicate disambiguation, minting + immutability rules, acceptance criteria.
- **Remaining human decisions:** §8.1 (Mahābhārata book-number duplication — recommend
  keep), §8.2 (dictionaries in v1 — recommend mint `e{n}` now).
- **Unblocks:** Sessions 2 and 3; Phase 4 citations.

## Session 2 — HTML→JSONL converter spec ✅ DONE (2026-06-12)

- **Deliverable:** [docs/CONVERTER_SPEC.md](CONVERTER_SPEC.md)
- **Key output:** the structural insight that one source "line" = one `citation_block`
  bundling Sanskrit + Russian + commentary as sibling divs, which the converter explodes
  into grouped canonical records. Four parse paths characterized against live data
  (A-clean / A-range / B-dict / C-prose), JSONL schema with `#sa`/`#ru`/`#comm{n}`
  segment suffixes, commentary `annotates` linkage, SLP1 + Vedic-accent handling, 7 CI
  validation gates, conversion run-report.
- **Findings that fed forward:** Sanskrit↔Russian alignment is already encoded as sibling
  divs (free group key for S3); dictionaries already carry 4 scripts per line
  (deva/iast/slp1/cyrillic) — the cross-script layer arrives partly for free.
- **Remaining for S3/M.G.:** n:m alignment edge semantics (range-merge, interpolations)
  → S3; non-tab dictionary `forms` backfill; authoritative `structure` assignment.

## Session 3 — Sanskrit↔Russian alignment spec ✅ DONE (2026-06-12)

- **Deliverable:** [docs/ALIGNMENT_SPEC.md](ALIGNMENT_SPEC.md)
- **Decisive finding:** alignment is **extraction, not inference** — Sanskrit and Russian
  are already interleaved as sibling divs in one `citation_block` (78,219 clean 1:1
  blocks measured). No statistical aligner needed for v1.
- **n:m worry resolved:** ranges are pre-merged by the source to translation granularity
  (`65.1-2` = 2 Sanskrit verses : 1 Russian block, atomic 1:1 at group level). The
  CONVERTER_SPEC §9.1 n:m concern is pre-solved by the markup.
- **Real edge cases (bounded):** 2 whole translation-only texts (buddhacharita-balmont,
  mify-drind, 100% `0:1` monolingual), 10,145 monolingual-Russian blocks, vedanga_jyotisha
  59% partial, refrains (dhruva), secondary numbering, interleaved nav headings.
- **Spec includes:** group data model, per-block cardinality (1:1/0:1/1:0), gold-standard
  regression oracle (~25 hand-verified groups), 5 CI gates, reader-toggle semantics.
- **Open for M.G.:** compare-route monolingual rows (§9.1); vedanga_jyotisha gap = defect
  or genuine (§9.2).

## Session 4 — Offline search design (sqlite-wasm + OPFS)

- **Goal:** Architecture for Phase 3 PWA offline search.
- **Inputs:** current FTS5 schema + query layer ([web/app/services/search_service.py](../web/app/services/search_service.py)),
  corpus.db size figures, Phase 2 PWA shell (must exist first — Sonnet work).
- **Deliverable:** `docs/OFFLINE_SEARCH_DESIGN.md` — wasm bundle strategy, OPFS DB
  shipping/update path (versioned with `corpus_meta`), query parity matrix (which of
  plain/regex/morph modes work offline), storage quotas, and the fallback story.
- **Rights note:** an OPFS-resident corpus.db on the user's device is the same posture
  as today's Windows zips (corpus ships inside the installed app) — acceptable; no
  separate public download endpoint may be added for it.
- **Order note:** last of the build sessions; depends on Phase 2 being done and is
  independent of Sessions 2–3.
- **Gate status (2026-06-12):** Phase 2 — S4's prerequisite — is now **planned** in
  [PHASE2_PLAN.md](PHASE2_PLAN.md), which defines an explicit "S4 contract surface" (§3):
  installable PWA shell, `navigator.storage.persist()` durability layer, per-text offline
  selection module, and offline/online state UX. S4 may be designed as soon as Phase 2 is
  *implemented* (not just planned). S4's `OFFLINE_SEARCH_DESIGN.md` should consume that
  contract rather than re-specify the shell.

## Session 5 — Pre-release review

- **Goal:** One deep review pass over the load-bearing changes before the H2 release.
- **Scope:** converter + alignment implementation diff, ID-resolver route, offline
  bundle, plus a rights/licensing sweep (no endpoint or export accidentally widens
  corpus distribution).
- **Deliverable:** review findings doc + sign-off checklist; blockers filed as issues.
- **Timing:** after implementation of Sessions 2–4 outputs; before version bump and
  release zip.

---

## Sequence and dependencies

```
S1 line-ID ✅ ──→ S2 converter spec ──→ S3 alignment spec ──→ implement (Sonnet)
                                                                  │
Phase 2 PWA shell (Sonnet, parallel) ──→ S4 offline design ──→ implement (Sonnet)
                                                                  │
                                                    S5 pre-release review ──→ release
```

## Working rules for each session

1. **One session, one artifact.** Full task spec and all inputs gathered up front in a
   single opening prompt; cheap scripted censuses prepared beforehand.
2. **Specs end with acceptance criteria** that the implementing model can be tested
   against mechanically.
3. **Human decisions are extracted, not deferred:** each spec ends with a short
   numbered "open questions" list with a recommendation per item (pattern proven in
   Session 1 — two of three questions resolved in-session).
4. **End the session when the artifact is committed.** Implementation starts in a fresh
   cheaper-tier session that reads the spec.
