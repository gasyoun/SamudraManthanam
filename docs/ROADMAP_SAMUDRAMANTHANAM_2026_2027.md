# ROADMAP — SamudraManthanam, August 2026–July 2027

_Created: 30-07-2026 · Last updated: 30-07-2026_

**Status: LIVING.** This is the sole status roadmap for the programme indexed
by [PLAN_SAMUDRAMANTHANAM_ARCHITECTURE_2026_2027.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/PLAN_SAMUDRAMANTHANAM_ARCHITECTURE_2026_2027.md).

## Goal

Preserve the successful web/desktop corpus product while making its canonical
data, durable references, deployments, migrations, and public contribution
surface reproducible and safe. Architecture integrity leads; corpus growth
continues immediately; collaborative research features follow on the hardened
contracts.

## Done — do not re-plan

- H2 Phases 0–3e: canonical JSONL conversion, PWA/offline reader, sqlite-wasm
  search, metadata, and generated views.
- NKРЯ W0–W4 and H906 morphology.
- Somadeva all 18 books aligned and re-keyed.
- Residual July Wave 1: JSON/CSV export, dead `morph_cache` removal, SSE tests,
  DBhP uniqueness scoping, and Cyrillic-homoglyph regression guard.
- Existing FTS5/search services, publication swap, offline-pack builders, and
  shared `sanskrit-util` adoption.

## Wave 1 — integrity plus bounded corpus delivery

**Span:** August–September 2026.

**Execution routing:** H1919–H1922 are superseded historical Codex packets.
Run Lanes A–D from the Opus 5 1M (`claude-opus-5[1m]`) Claude Code handoffs:
[H1924](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1924-Opus_SamudraManthanam_canonical-manifest-artifact-bundle_30.07.26.md),
[H1925](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1925-Opus_SamudraManthanam_durable-reference-zero-orphan_30.07.26.md),
[H1926](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1926-Opus_SamudraManthanam_bounded-regex-correction-trust_30.07.26.md),
and
[H1927](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1927-Opus_SamudraManthanam_runtime-migrations-dual-deploy_30.07.26.md).
Start H1924 and independent H1926 first; H1925 depends on H1924; H1927 may
start independent substeps but its final smoke consumes H1924–H1926.

- H1924:
  `Read C:\Users\user\Documents\GitHub\Uprava\handoffs\H1924-Opus_SamudraManthanam_canonical-manifest-artifact-bundle_30.07.26.md and execute it.`
- H1926:
  `Read C:\Users\user\Documents\GitHub\Uprava\handoffs\H1926-Opus_SamudraManthanam_bounded-regex-correction-trust_30.07.26.md and execute it.`
- H1925:
  `Read C:\Users\user\Documents\GitHub\Uprava\handoffs\H1925-Opus_SamudraManthanam_durable-reference-zero-orphan_30.07.26.md and execute it.`
- H1927:
  `Read C:\Users\user\Documents\GitHub\Uprava\handoffs\H1927-Opus_SamudraManthanam_runtime-migrations-dual-deploy_30.07.26.md and execute it.`

### A. Canonical corpus and artifact contract

Deliver:

- versioned manifest schema;
- JSONL/source/hash/provenance enumeration;
- checksum-pinned immutable corpus bundle;
- generated-view inventory for web DB, offline packs, desktop HTML/no-tags, and
  release reports;
- validation of the actual JSONL and artifacts being published.

Unblocks: durable identity migration, reliable full-corpus gates, object-store
delivery, and one source of truth for both products.

### B. Durable scholarly references

Deliver:

- `source_slug + canonical_id + corpus_version` through search, exports,
  citations, corrections, AI/cache references, and generated links;
- compatibility reads for legacy `source_id + line_num`;
- reversible state migration and zero-orphan report;
- removal of external ordinal reliance only after the report is green.

Unblocks: dependable annotations/corrections and corpus rebuilds.

### C. Public-boundary safety

Deliver:

- hard-deadline regex execution behind the existing search contract;
- explicit syntax/resource budgets and performance tests;
- admin credentials moved out of URLs;
- anonymous low-trust correction intake plus verified-session elevated actions;
- audit/rate-limit hooks appropriate to each trust tier.

Unblocks: safe public corrections and later collaborative tooling.

### D. Runtime and release reproducibility

Deliver:

- ordered checksum migrations for `state.db`;
- explicit rebuild/schema-version policy for `corpus.db`;
- bounded extraction of lifespan/migrations, headers, static/PWA routes, and
  sitemap generation from `main.py`;
- shared deployment contract tests for container and bare-host profiles;
- full-corpus gate on every corpus-changing PR and release;
- explicit performance budgets and measurements.

Unblocks: predictable releases and future service decomposition without a
framework rewrite.

### E. Corpus lane — Wisdomlib

Stage C is partly scraped and expected to finish within two weeks. Finish the
existing work, produce deterministic structural/anomaly reports and a
stratified review sample, then register accepted outputs in the canonical
manifest. Do not label this lane externally blocked.

### F. Corpus lane — Ignatiev H1438

Recover and audit the existing `h1438-ignatjev-waveb` worktree/branch before
writing new parser or data work. Validate its Nīlamata/Adbhuta outputs,
provenance and raw/derived-file boundary; use H1438 rather than minting a
duplicate programme. Continue independent of other lanes unless manifest
registration is the only remaining merge dependency.

### Wave-1 exit

- manifest/bundle v1 published;
- zero-orphan stable-identity migration green and reversible;
- public regex demonstrably bounded;
- no admin secret in a URL;
- state/corpus migration policies enforced;
- both deployment profiles pass one contract;
- full corpus passes on every corpus-changing PR and the release candidate;
- Wisdomlib Stage C and the recovered H1438 Wave-B slice have deterministic
  reports and reviewed integration status.

## Wave 2 — corpus scale and dual-product generation

**Span:** October–December 2026.

- Finish viable H1438 works through format-specific front ends feeding the same
  canonical record model.
- Promote Wisdomlib ingestion from one-off completion to reproducible incremental
  refresh.
- Generate desktop HTML/no-tags/catalogues from the canonical manifest and add
  golden parity checks against the maintained desktop client.
- Publish immutable corpus-bundle versions through the selected artifact
  channel and exercise rollback in both deployment profiles.
- Replace the stale duplicate-suffix ceiling with an evidence-based invariant
  and categorised exception report.
- Complete the claimed H1485 work only through its existing owner; integrate its
  contracts after review rather than rescoping it here.

Exit: one corpus release is rebuilt from pinned artifacts and consumed by both
web and desktop without manual source-list reconciliation.

## Wave 3 — collaborative research workbench

**Span:** January–March 2027.

- Add verified sessions and contributor roles on top of Wave-1 identity.
- Ship correction/annotation workflows keyed only by durable corpus identity.
- Provide editor queues, audit history, provenance-preserving acceptance, and
  regeneration into canonical sources.
- Improve morphology and cross-script discovery using existing shared assets,
  measured corpus evidence, and explicit fallbacks.
- Add accessible progressive-JavaScript workbench modules; preserve Jinja/PWA
  and offline-reader behavior.

Exit: anonymous proposals and verified scholarly contributions coexist without
weakening corpus identity or rebuild guarantees.

## Wave 4 — consolidation, performance, and dual-product release

**Span:** April–July 2027.

- Enforce production-corpus budgets for plain, morph, regex, reader, startup,
  offline-pack download/build, and desktop generation.
- Run a dual-product release rehearsal and rollback from immutable artifacts.
- Consolidate historical architecture/roadmap documents and preserve only
  explicit supersession links.
- Measure adoption across researcher, reader, and corpus-engineer workflows.
- Re-rank the next programme from measured bottlenecks rather than speculative
  platform expansion.

Exit: a documented, reversible web+desktop release consumes one canonical
bundle and meets the published verification and performance contract.

## Explicit non-goals

- Replacing FTS5 without measured failure.
- Rewriting the application as an SPA.
- Rebuilding transliteration, NKРЯ, Somadeva, Wisdomlib, or Ignatiev pipelines.
- Duplicating H1438 or the actively claimed H1485 work.
- Treating ordinal database IDs as durable external identity.
- Rights research, rights-driven relocation, or rights release gates.
- Mutating production data during implementation.
- Committing raw personal archives or secrets.

## Human checkpoints

No blocking implementation decision remains. Human review is limited to:

- the stratified corpus samples required by the quality contract;
- merging/reconciling existing H1438/H1485 work where ownership overlaps;
- ordinary PR review and deployment authority;
- research-feature prioritization after Wave-2 measurements.

_Dr. Mārcis Gasūns_
