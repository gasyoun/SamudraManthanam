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

## Session 2 — HTML→JSONL converter spec

- **Goal:** Spec (not code) for the converter that turns the 148 presentational HTML/TXT
  files into the canonical JSONL master, minting canonical IDs per Session 1.
- **Inputs to bring into the session:**
  - [docs/LINE_ID_SCHEME.md](LINE_ID_SCHEME.md) (frozen, with §8 decisions made)
  - [web/ingest/parse_html.py](../web/ingest/parse_html.py) (current extraction logic
    and its known hacks)
  - A structural census of all 148 files: tag inventory per file (`citation_block`,
    `range`, `chapter_content`, `H1`, `endchapter`, footnote spans), produced by a cheap
    scripted pass *before* the session — do not burn frontier tokens on grep work.
- **Deliverable:** `docs/CONVERTER_SPEC.md` — JSONL record schema (line text, html,
  canonical_id, script tags, footnotes, chapter), per-class extraction rules,
  edge-case inventory (the 41 duplicates, `chapter_NC` commentary anchors, `comment_*`,
  Vedic accent stripping), validation gates (round-trip + acceptance criteria from
  Session 1 §9), and the test plan.
- **Order note:** before Session 3, because alignment operates on converter output.

## Session 3 — Sanskrit↔Russian alignment spec

- **Goal:** Spec for explicit alignment groups in the JSONL master (today alignment is
  implicit in HTML line adjacency).
- **Inputs:** converter spec; 3–4 hand-picked parallel sources of different shapes
  (verse-aligned Gītā; range-merged Gītagovinda; prose Vishnu-purāṇa; a
  Sanskrit-only or Russian-only control).
- **Deliverable:** `docs/ALIGNMENT_SPEC.md` — alignment-group data model
  (n:m verse↔translation mapping keyed by canonical IDs), confidence tiers
  (markup-derived vs heuristic vs manual), gold-standard sample definition
  (~20 hand-verified pairs to evaluate any automated aligner), and what the reader's
  `lang=ru|sa` toggle consumes.
- **Frontier-model leverage:** the n:m edge cases (one Russian stanza translating a
  verse range; translator's interpolations with no Sanskrit source) are where cheap
  models produce plausible-but-wrong designs.

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
