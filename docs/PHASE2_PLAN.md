_Created: 25-08-2026 · Last updated: 05-09-2026_

# Phase 2 Implementation Plan — Mobile-Ready Web + PWA Shell

**For:** an implementation session (Sonnet-tier — no frontier design needed; this plan is
the design). **Status:** ready to start · 2026-06-12
**Why now:** Phase 2 is the **gate** between the finished Phase 1 specs and the two
remaining frontier sessions — **S4 (offline search) cannot be designed until the PWA shell
and offline-reader storage layer it builds on exist.** This plan clears that gate.

**Scheduling:** Phase 2 is **independent of Phase 1** — it touches templates, static assets,
and the service worker, not the converter or `corpus.db` schema. It can run **in parallel**
with Phase 1 implementation. The one soft coupling (offline reader content format) is
resolved in §C to keep them decoupled.

---

## 0. Rights guardrail (unchanged, applies here)

The offline reader caches corpus text **on the user's own device, inside the installed
PWA** — the same distribution posture as today's Windows release zips, and explicitly
allowed by the roadmap. **Do not** add a public "download the corpus" endpoint, a shareable
export of cached content, or any origin other than the app's own serving it. Caching for
the installed user ≠ publication.

---

## 1. Current state (measured 2026-06-12)

| Aspect | State | Implication |
|---|---|---|
| Viewport meta | present in `_base.html` | responsive base exists |
| `@media` rules | present in `_base.html`, `source_view.html`, `index.html`, `compare_*`, `search_page.html`, `site.css`, `style.css` | **audit & fill gaps**, not greenfield |
| PWA (manifest/SW/icons) | **none** | net-new — workstream B |
| Fonts | 5 unsubsetted TTF, ~3.3 MB total: Charis SIL ×3 (~2.4 MB), Sahitya 234 KB, Sanskrit2003 691 KB | subset + woff2; **two Devanagari faces is redundant** |
| Head injection point | `_base.html` has `{% block extra_head %}` + ordered `style.css`→`site.css` | clean place for manifest link / theme-color |
| Static serving | `/static/` (FastAPI) | SW scope + asset caching straightforward |
| Templates | `_base.html` layout; `source_view.html` is the reader; `compare_view.html` the compare route | three responsive targets |

---

## 2. The three workstreams

### A — Responsive audit + font strategy (the foundation)

1. **380 px audit** of the three primary surfaces — search (`index.html` /
   `search_page.html`), reader (`source_view.html`), compare (`compare_view.html`). Fix
   overflow, tap-target size (≥ 44 px), and the reader's two-pane Sanskrit/Russian layout
   collapsing to stacked panes on narrow screens. The reader already has a `lang` toggle
   (ALIGNMENT_SPEC §5) — on mobile, default to stacked-both with the toggle prominent.
2. **Touch-friendly result navigation** — larger hit areas on result rows, chapter nav,
   and the compare pager; momentum-scroll friendly; no hover-only affordances.
3. **Font strategy (measurable win):**
   - Convert all faces to **woff2** and **subset** to the glyphs actually used (Cyrillic +
     Latin-with-IAST-diacritics for Charis; Devanagari block for the Indic face).
   - **Consolidate the two Devanagari faces** (Sahitya 234 KB vs Sanskrit2003 691 KB) to
     one — recommend **Sahitya** (smaller; verify glyph coverage of the corpus's Devanagari
     first). Removes ~700 KB.
   - `font-display: swap`; preload only the Cyrillic+Latin subset (the default reading
     face); lazy-load Devanagari (only the dictionary lines and headwords use it).
   - Target: first-paint font payload well under 200 KB.

**Acceptance:** the three surfaces usable and uncramped at 380 px; Lighthouse mobile
"Best Practices" + "Accessibility" tap-target checks pass; first-paint font payload < 200 KB.

### B — PWA manifest + service worker (the installable shell)

1. **`static/manifest.webmanifest`** — name (RU), short_name, `start_url: /`,
   `display: standalone`, `theme_color`/`background_color`, icon set (maskable + any-purpose
   at 192/512). Generate icons from the existing favicon source. Link from `extra_head` +
   `theme-color` meta.
2. **`static/sw.js` — hand-rolled, no build step.** The app has **no bundler**; do not add
   Workbox or an npm toolchain. A ~150-line cache-first-for-assets / network-first-for-HTML
   service worker is sufficient and keeps the zero-build deployment intact.
   - **App-shell precache:** `_base` chrome, `site.css`/`style.css`, the woff2 subsets, core
     JS (`reader.js`, `search.js`), icons. Versioned cache name keyed to a build stamp.
   - **Runtime strategy:** static assets cache-first; navigations network-first with cache
     fallback; **the search API stays network-only** ("online search unchanged" — roadmap).
   - **Update flow:** new SW activates on next load; show a "обновление готово" refresh
     toast (reuse the existing engaged-banner pattern).
3. **Registration** from a tiny inline script in `_base.html` (guarded by
   `'serviceWorker' in navigator`).

**Acceptance:** installable on Android Chrome **and** iOS Safari (Lighthouse PWA
"installable" green); app shell loads with network throttled to offline after first visit;
**online search behaviour byte-identical to pre-PWA**.

### C — Offline reader (first offline milestone, S4's foundation)

The roadmap's "user picks texts to keep offline; SW caches reader pages + per-text JSON."
To stay **decoupled from Phase 1**, v1 of the offline reader caches the **server-rendered
reader HTML pages + their assets**, not a Phase-1 JSON format. (When Phase 1 lands and S4
builds the offline *pack*, it supersedes this with the JSONL-derived format — see §3.)

1. **"Keep offline" control** on each source page and the source list — toggles a per-source
   entry in a small client-side registry (IndexedDB or `localStorage` + Cache API).
2. **On enable:** fetch and cache the source's reader page(s) and any per-source assets;
   show progress; handle interruption/resume.
3. **Storage durability:** call `navigator.storage.persist()` and surface quota/eviction
   state (iOS Safari evicts non-persisted origins). A "managed offline texts" panel shows
   what's cached, total size, and a remove action.
4. **Offline indication:** when offline, the UI marks which texts are readable and greys the
   rest; search clearly indicates it needs connectivity (until S4).

**Acceptance:** a user toggles a text offline, goes airplane-mode, and reads it fully
(roadmap acceptance: "a cached text fully readable in airplane mode"); persisted storage
survives an iOS Safari background-evict cycle.

---

## 3. The S4 contract surface (what S4 will assume Phase 2 delivered)

S4 (offline search, sqlite-wasm + OPFS) **builds directly on Phase 2**. State these as a
stable interface so S4's design can rely on them:

| Phase 2 deliverable | What S4 reuses it for |
|---|---|
| Installable PWA shell + versioned SW cache | S4's wasm engine + DB ship and update through the same shell/cache-versioning |
| `navigator.storage.persist()` + quota/eviction UX | S4's OPFS-resident DB needs exactly this durability layer |
| "Keep offline" registry + per-text selection UX | S4's per-text-group **pack download** extends this same selection model |
| Offline/online state indication + search-needs-network messaging | S4 flips these texts/queries to "answerable offline" |

**Design rule:** build C's storage + selection layer as a small module with a clean
interface (`registerOffline(textId)`, `listOffline()`, `removeOffline(textId)`,
`persistRequested()`), so S4 swaps the *content* (HTML pages → sqlite pack) without
rewriting the *plumbing*.

---

## 4. Build order

1. **A1 font subset/woff2 + consolidation** (biggest perf win, zero risk, unblocks nothing
   else but speeds everything).
2. **A2 responsive audit fixes** (three surfaces).
3. **B manifest + service worker + registration** (installable shell).
4. **C offline-reader storage module + "keep offline" UX** (the S4 foundation).
5. **Lighthouse + airplane-mode verification** pass; fix to green.

Each step committed `ai-wip:`; A and B can interleave; C depends on B.

## 5. Acceptance (roadmap Phase 2 gate)

- [ ] Lighthouse PWA **installable** on Android Chrome and iOS Safari.
- [ ] A cached text **fully readable in airplane mode**.
- [ ] Three primary surfaces usable at 380 px; tap-targets ≥ 44 px.
- [ ] First-paint font payload < 200 KB; one Devanagari face.
- [ ] Online search behaviour **unchanged** (golden-query parity in `web/tests/`).
- [ ] Offline-storage module exposes the §3 interface for S4.

## 6. Decided vs open

**Decided (build to these):** hand-rolled SW (no Workbox/bundler); consolidate to one
Devanagari face; offline-reader v1 caches rendered HTML (not Phase-1 JSON); search stays
network-only in Phase 2.

**Open — recommended default, surface at review (non-blocking):**
- Devanagari face = Sahitya (smaller) **pending glyph-coverage check** vs Sanskrit2003.
  If Sahitya lacks a needed conjunct, keep Sanskrit2003 and subset it instead.
- Default-offline texts: none auto-cached; user opts in per text (roadmap stance). Revisit
  if a "starter pack" is wanted.
- iOS install affordance: iOS Safari has no install prompt API — add a one-time "Add to
  Home Screen" hint card for iOS users. Confirm desired copy with M.G.

**Out of scope (later phases):** wasm/OPFS search (S4/Phase 3), offline morphology, native
app packaging.

## 7. Hand-off note

This plan is self-contained for a Sonnet-tier implementer the same way
`IMPLEMENTATION_HANDOFF_PHASE1.md` is. It can proceed **in parallel** with Phase 1
implementation — different files, no shared schema. When both Phase 1 and Phase 2 are done,
**S4 is unblocked** and becomes the next frontier session; **S5 (pre-release review)** runs
after S4's implementation, before the release.

_Dr. Mārcis Gasūns_
