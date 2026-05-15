# Architecture Critique and Open Questions

Date: 2026-05-15

Purpose: red-team review of architecture and implementation solutions proposed across project Markdown files.

This document does not replace `TARGET_ARCHITECTURE.md`. It challenges it. Gemini Flash should read this before treating any architecture decision as final.

## Documents Reviewed

Current planning docs:

- `TARGET_ARCHITECTURE.md`
- `ARCHITECTURE_REVIEW_6_MONTH_ROADMAP.md`
- `GEMINI_FLASH_IMPLEMENTATION_PLAN.md`
- `GEMINI_FLASH_PHASE_01_FOUNDATION.md`
- `GEMINI_FLASH_PHASE_02_SEARCH_READER.md`
- `GEMINI_FLASH_PHASE_03_IDENTITY_CORRECTIONS.md`
- `GEMINI_FLASH_PHASE_04_AI.md`
- `GEMINI_FLASH_PHASE_05_DEPLOY_OPERATIONS.md`

Older or partly superseded docs:

- `WEB_PLAN.md`
- `roadmap.md`
- `gemini-implementation-plan.md`
- `CODE_ARCHITECTURE_REVIEW.md`
- `README.md`
- `ai_status.md`
- `use_cases.md`
- `web/SEARCH_CONTRACT.md`

## Documentation Risk

Several Markdown files now describe overlapping plans from different moments. This can confuse Gemini Flash.

Critique:

- `WEB_PLAN.md` still reads like a from-scratch Docker-era web specification.
- `roadmap.md` is a 1-month roadmap and contains older ordering and numbering issues.
- `gemini-implementation-plan.md` is an older long-form plan.
- `GEMINI_FLASH_IMPLEMENTATION_PLAN.md` is now the current short index.

Better alternative:

- Add a documentation index that marks each plan as current, supporting, or historical.
- Keep old plans for context, but do not let Gemini treat them as current instructions.

Question:

- Should old plans be moved under `docs/archive/` or kept in the repository root?

## 1. VPS Without Docker

Proposed solution:

- Deploy first serious version on a VPS without Docker.

Critique:

- No-Docker reduces one layer, but it can create a snowflake server.
- Python versions, system packages, nginx config, and service state become manual operational knowledge.
- Rollback is less reproducible unless scripts are very disciplined.

Why another solution may be better:

- Docker Compose on VPS gives reproducible runtime while still storing `corpus.db` on a host volume.
- PaaS can be simpler if persistent disk is reliable and cheap enough.

Current recommendation:

- Keep no-Docker as the preference only if VPS maintenance simplicity matters more than reproducibility.
- Reconsider Docker Compose on VPS as a serious alternative.

Question:

- Is the objection to Docker technical, hosting-related, or just a desire to keep things simple?

## 2. `corpus.db` on VPS Filesystem

Proposed solution:

- Store generated `corpus.db` directly on VPS persistent storage.

Critique:

- This is simple, but the VPS becomes the only obvious artifact store.
- Manual uploads can drift from source.
- Disaster recovery depends on backups that do not exist yet.

Why another solution may be better:

- Object storage such as S3-compatible storage or Backblaze B2 is better for versioned DB artifacts and rollback.
- GitHub Release assets may be workable for occasional DB releases, even though normal Git cannot store the DB.
- Rebuilding on the VPS from corpus sources is more reproducible than uploading a DB.

Current recommendation:

- Start with VPS storage, but design publish scripts so object storage can be added later.

Question:

- Do you want the first publish flow to upload a locally built DB, or rebuild the DB on the VPS from corpus source files?

## 3. SQLite FTS5 as Search Engine

Proposed solution:

- Keep SQLite FTS5 for corpus search.

Critique:

- SQLite FTS5 is strong for simple search, but weaker for advanced ranking, fuzzy search, substring search, stemming, and concurrent writes.
- Prefix search is not the same as true substring search.
- Russian morphology and Sanskrit morphology may need richer indexes.

Why another solution may be better:

- PostgreSQL gives relational state, migrations, auth data, and full-text search in one system.
- Meilisearch gives typo tolerance, fast facets, and ranking with less custom code.
- Tantivy-based custom indexing could support specialized Sanskrit/Russian search later.

Current recommendation:

- Keep SQLite now, but add benchmark gates before declaring it the long-term search engine.

Question:

- Is desktop-style substring search more important than FTS-style token/prefix search?

## 4. Split `corpus.db` and `state.db`

Proposed solution:

- Use generated `corpus.db` plus mutable `state.db`.

Critique:

- Two SQLite DBs reduce publish risk but add cross-DB complexity.
- Backups and migrations now have two lifecycles.
- Joining user/correction data to corpus lines becomes application-level work.

Why another solution may be better:

- One PostgreSQL DB could hold corpus search, users, corrections, AI logs, and migrations coherently.
- One SQLite DB with attached generated tables is simpler, but dangerous during rebuilds.

Current recommendation:

- Keep the split for the first 6 months, but treat `state.db` as a possible stepping stone to PostgreSQL.

Question:

- Do you expect many simultaneous logged-in users, or mostly a small scholarly group?

## 5. Keep FastAPI With Jinja and jQuery

Proposed solution:

- Keep current server-rendered/Jinja plus jQuery style.

Critique:

- It is fast to extend, but complex reader/correction/AI UI can become messy.
- jQuery state can become hard to test.
- Accessibility and responsive behavior may lag.

Why another solution may be better:

- HTMX would fit server-rendered FastAPI and reduce custom JavaScript.
- React/Vue/Svelte would help if the reader becomes a rich annotation workspace.

Current recommendation:

- Consider HTMX before a full SPA. It matches this project better than jumping to React.

Question:

- Do you imagine the reader UI as mostly document pages, or as a complex annotation workspace?

## 6. Lead Capture at 50 Percent Scroll

Proposed solution:

- Ask for name/email after about half-page reading depth.

Critique:

- Scroll depth is a crude signal.
- It can annoy serious readers before they trust the site.
- It may capture less qualified users than export/correction/save actions.

Why another solution may be better:

- Ask after a high-intent action: export, correction proposal, saved search, AI explanation, or second visit.
- Ask softly in-page instead of modal-first.

Current recommendation:

- Use 50 percent scroll only as one trigger. Prefer high-intent triggers.

Question:

- Which user action is valuable enough to require email: export, correction proposal, AI, saved search, or all of them?

## 7. Magic-Link Login From Captured Email

Proposed solution:

- Captured email becomes identity key for future magic-link login.

Critique:

- Lead capture and authentication are different trust levels.
- A typo in email capture can create broken identity records.
- Magic-link email deliverability becomes a production dependency.

Why another solution may be better:

- Keep leads separate from accounts until the user explicitly requests login.
- Use magic link only when the user tries to access corrections, saved searches, or admin.

Current recommendation:

- Store leads first, convert to login identity only after email verification.

Question:

- Should submitting the lead form immediately send a verification email, or only later when login is needed?

## 8. Correction Proposals for Email-Identified Users

Proposed solution:

- Email-identified users may propose corpus corrections.

Critique:

- This can create spam, low-quality proposals, and moderation load.
- Email capture alone does not prove scholarly trust.
- Corrections may need source-specific context and editorial rules.

Why another solution may be better:

- Start with invitation-only correction proposals for students/scholars.
- Allow public correction suggestions but queue them behind rate limits and moderation.

Current recommendation:

- Allow email-identified proposals, but require verified email plus rate limits.

Question:

- Should first correction access be public-after-email, invitation-only, or limited to your students?

## 9. Provider-Agnostic AI

Proposed solution:

- Build OpenAI, local, Gemini, and fake providers behind one interface.

Critique:

- A generic provider abstraction can become over-engineered before the first useful AI feature exists.
- Provider differences leak through: tool use, context length, structured output, safety filters, local latency.

Why another solution may be better:

- Build a task-level AI interface first: summarize, explain, compare, suggest queries.
- Hide providers under each task only when a second provider is actually needed.

Current recommendation:

- Keep provider-agnostic direction, but implement task contracts before deep provider abstractions.

Question:

- Which AI feature is first: result summary, passage explanation, passage comparison, or related-query suggestion?

## 10. Ollama as First Local Runner

Proposed solution:

- Test local AI first with Ollama through an OpenAI-compatible endpoint.

Critique:

- Ollama is convenient, but not necessarily best for server throughput or reproducibility.
- Model availability and OpenAI-compatible behavior can vary.

Why another solution may be better:

- llama.cpp server is lighter and more controllable.
- vLLM is better for GPU server throughput.
- LM Studio is easier for desktop experiments.

Current recommendation:

- Use Ollama only for local experimentation. Keep production local-provider choice open.

Question:

- Will local models run on your desktop, on the VPS CPU, or on a GPU server?

## 11. Stem/Root Lookup via Sanskrit Heritage

Proposed solution:

- Keep current Sanskrit Heritage-backed Stem/Root Lookup.

Critique:

- External availability and response format are outside our control.
- It is not full morphology.
- Network dependency makes tests and production behavior less predictable.

Why another solution may be better:

- Build an offline curated morphology cache from known sources.
- Treat morphology as an indexed lexical layer, not an API call at search time.

Current recommendation:

- Keep Sanskrit Heritage as optional enrichment, but build an offline fallback path.

Question:

- Do you have or want a curated morphology/stem dataset that can be imported offline?

## 12. HTML Export First

Proposed solution:

- Keep HTML as the main export format.

Critique:

- HTML is readable, but not ideal for downstream analysis.
- Translators may want Markdown or DOCX.
- Scholars may want CSV/JSON/TEI-like structured data.

Why another solution may be better:

- Add JSON export first for structured reuse.
- Add Markdown for human editing.
- Add CSV for spreadsheet comparison.

Current recommendation:

- Keep HTML, but add JSON export before Markdown if correction/AI workflows need stable result references.

Question:

- Which export format would your students actually use after HTML: Markdown, DOCX, CSV, or JSON?

## 13. Stable Citations Later

Proposed solution:

- Treat stable citations as later, not immediate.

Critique:

- Correction proposals, exports, AI explanations, and reader URLs all become stronger if citations are stable early.
- Retrofitting versioned citations later can be painful.

Why another solution may be better:

- Add lightweight corpus versioning now, even if full scholarly provenance comes later.

Current recommendation:

- Make corpus version and source hash part of exports and correction proposals early.

Question:

- Should citations remain stable across corpus corrections, or is "latest corpus" acceptable for now?

## 14. Desktop Corpus Sync

Proposed solution:

- Keep `/api/corpus-sync` for legacy desktop updates.

Critique:

- Maintaining desktop sync competes with web platform work.
- The desktop updater has security concerns.
- Supporting both paths may slow web-first progress.

Why another solution may be better:

- Freeze desktop sync except for critical fixes.
- Focus on web reader/export workflows first.

Current recommendation:

- Deprioritize desktop sync unless there is a clear active desktop user need.

Question:

- How important is desktop sync in the next 6 months compared with web reader and corpus editing?

## 15. SSE Progress Endpoint

Proposed solution:

- Keep SSE endpoint for compatibility, frontend no longer depends on it.

Critique:

- A dead-but-present endpoint invites future confusion.
- It currently does extra search work if used.

Why another solution may be better:

- Remove it until background search jobs exist.
- Or rebuild it as the single owner of long-running search jobs.

Current recommendation:

- Deprecate it explicitly in docs and tests unless a real streaming job architecture is planned.

Question:

- Do users need live search progress, or is a fast single response enough?

## 16. Documentation Strategy

Proposed solution:

- Add more planning files.

Critique:

- More docs can make Gemini less reliable if old docs contradict new docs.
- Root directory is becoming crowded with planning files.

Why another solution may be better:

- Create `docs/current/` and `docs/archive/`.
- Keep only `README.md`, `changelog.md`, and the current Gemini index at repo root.

Current recommendation:

- Add `DOCUMENTATION_INDEX.md` now.
- Later move historical docs under `docs/archive/`.

Question:

- Should I reorganize documentation folders now, or only add an index for the moment?

## Priority Questions For You

1. Docker Compose on VPS, no-Docker VPS, or PaaS with persistent disk?
2. Upload locally built `corpus.db`, rebuild on VPS, or store DB artifacts in object storage?
3. Desktop-style substring search or current FTS prefix search?
4. First identity trigger: scroll depth, export, correction proposal, AI, saved search, or second visit?
5. Correction proposals: public-after-verified-email, invitation-only, or students-only first?
6. First AI feature: result summary, passage explanation, passage comparison, or related-query suggestion?
7. First non-HTML export format: Markdown, DOCX, CSV, or JSON?
8. Should desktop sync stay on the 6-month roadmap?
9. Should old planning docs be moved to `docs/archive/`?

## Provisional Decision Changes

These are not implemented yet, but should influence the next documentation pass:

1. Treat no-Docker VPS as provisional, not settled. Docker Compose on VPS may be better.
2. Treat `state.db` as a stepping stone. PostgreSQL may be better if logged-in usage grows.
3. Treat 50 percent scroll capture as one possible trigger, not the main identity strategy.
4. Treat provider-agnostic AI as task-first, provider-second.
5. Treat desktop sync as optional unless user priority confirms it.
6. Add corpus versioning earlier than originally planned.
7. Add a documentation index before more planning docs are created.
