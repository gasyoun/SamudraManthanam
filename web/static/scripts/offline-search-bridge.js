/**
 * offline-search-bridge.js — bridges the jQuery search page (search.js, a
 * non-module classic script) to the ES-module offline search engine
 * (search-offline.js). Exposes a small synchronous-ish facade on
 * window.SamudraOffline so search.js can route a query to local search when the
 * network is down and a pack is installed.
 *
 * Design:
 *  - LAZY: the worker + wasm are NOT loaded on page load. They spin up only when
 *    the user goes offline (pre-warm on the 'offline' event) or on the first
 *    offline search. Online users pay nothing.
 *  - DEGRADED + HONEST: offline packs store plain line_text (no HTML), so
 *    results are a clearly-marked plain-text list with highlighting and reader
 *    links — not a pretense of the rich server fragment.
 *  - opfs-sahpool needs no cross-origin isolation, so this works on index.html
 *    (which has no COEP). Packs installed on /offline-settings are visible here.
 */
import * as off from '/static/scripts/search-offline.js?v=3e-2';

let _initPromise = null;     // memoised worker init + pack detection
let _ready = false;
let _installedPacks = [];    // ['base'] | ['dict'] | ['base','dict'] | []
let _sourceMap = {};         // source_id -> { title, slug, role }

// ── Lazy init ─────────────────────────────────────────────────────────────────

async function _doInit() {
    await off.init();                          // load worker + sahpool VFS
    const packs = [];
    for (const t of ['base', 'dict']) {
        try { if (await off.hasPack(t)) packs.push(t); } catch (_) { /* ignore */ }
    }
    _installedPacks = packs;

    // Build source_id -> {title, slug} from each installed pack (titles live in
    // pack_sources, not in the query rows). Keying by bare source_id is safe:
    // the build preserves the GLOBAL corpus.db source_id (base = sources NOT IN
    // dict; dict = the dictionaries), so the id sets are disjoint across packs —
    // no cross-pack collision is possible.
    _sourceMap = {};
    for (const t of packs) {
        try {
            await off.openPack(t);
            const { sources } = await off.listSources(t);
            for (const s of sources) {
                _sourceMap[s.source_id] = { title: s.title, slug: s.source_slug, role: s.role };
            }
        } catch (_) { /* a pack may fail to open; skip it */ }
    }
    _ready = true;
}

function ensureReady() {
    if (!_initPromise) _initPromise = _doInit().catch(err => {
        _initPromise = null;       // allow retry
        throw err;
    });
    return _initPromise;
}

// ── Rendering ─────────────────────────────────────────────────────────────────

function _esc(s) {
    return String(s)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;')
        .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function _reEscape(s) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function _highlight(text, terms) {
    let html = _esc(text);
    // Highlight on the escaped text. Terms are escaped the same way so they
    // match. Longest-first avoids partial overlaps. Caller passes plain terms.
    const sorted = [...terms].filter(Boolean).sort((a, b) => b.length - a.length);
    for (const term of sorted) {
        const needle = _reEscape(_esc(term));
        if (!needle) continue;
        try {
            html = html.replace(new RegExp(`(${needle})(?![^<]*>)`, 'giu'),
                '<span class="highlight">$1</span>');
        } catch (_) { /* skip un-compilable term */ }
    }
    return html;
}

function _queryTerms(query) {
    return query.split('\n').flatMap(l => l.split(/\s+/)).map(t => t.trim()).filter(Boolean);
}

/**
 * Render offline result rows to an HTML string for #results-area. Intentionally
 * a degraded, clearly-marked view: source-grouped plain text with highlighting
 * and a reader link (which works offline only if that source was cached).
 */
function renderHtml(query, rows, meta = {}) {
    const terms = _queryTerms(query);
    if (!rows.length) {
        return '<div class="offline-banner">⚡ Офлайн-поиск · по запросу ничего не найдено в загруженных текстах.</div>' +
               '<p style="color:#666;font-size:0.9rem;">Полный поиск станет доступен, когда вернётся сеть.</p>';
    }

    // Group by source, preserving first-seen order.
    const groups = new Map();
    for (const r of rows) {
        if (!groups.has(r.source_id)) groups.set(r.source_id, []);
        groups.get(r.source_id).push(r);
    }

    const sourcesHit = groups.size;
    let html = `<div class="offline-banner">⚡ Офлайн-поиск (без сети) · найдено ${rows.length} в ${sourcesHit} ` +
               `источник${sourcesHit === 1 ? 'е' : (sourcesHit < 5 ? 'ах' : 'ах')}` +
               (meta.timeout ? ' · показаны не все совпадения (превышен лимит сканирования)' : '') +
               '</div>';

    html += '<div class="chapters">';
    let idx = 0;
    for (const [sourceId, hits] of groups) {
        idx++;
        const src = _sourceMap[sourceId] || {};
        const title = _esc(src.title || `Источник ${sourceId}`);
        html += `<div class="chapter"><div class="chapter_title" id="offchap_${idx}">${idx}. ${title}</div>`;
        for (const h of hits) {
            const ref = _esc(h.link_id || String(h.line_num));
            const slug = src.slug;
            const linkOpen = slug
                ? `<a href="/sources/${encodeURIComponent(slug)}?highlight=${encodeURIComponent(h.line_num)}" target="_blank" rel="noopener" style="color:#e67e22;text-decoration:none;font-weight:600;">${ref} ↗</a>`
                : `<span style="color:#999;">${ref}</span>`;
            html += '<div class="citation_block" style="padding:0.5rem 0;">' +
                    `<div class="citation-meta" style="font-size:0.75rem;color:#999;margin-bottom:4px;">${linkOpen}</div>` +
                    `<div class="full-content">${_highlight(h.line_text || '', terms)}</div>` +
                    '</div>';
        }
        html += '<hr></div>';
    }
    html += '</div>';
    return html;
}

// ── Search across installed packs ─────────────────────────────────────────────

async function search({ query, mode = 'plain', caseSensitive = false, wholeWord = false, sourceIds = null, limit = 2000 } = {}) {
    await ensureReady();
    if (!_installedPacks.length) {
        // A pack may have been installed since the bridge first initialised
        // (e.g. on /offline-settings, then back here). Re-detect once before
        // giving up, so the user isn't told "no index" right after installing.
        await refresh().catch(() => {});
    }
    if (!_installedPacks.length) {
        const e = new Error('NO_PACK');
        e.code = 'NO_PACK';
        throw e;
    }
    const merged = [];
    let timeout = false;
    for (const t of _installedPacks) {
        try {
            const res = await off.searchOffline({
                packType: t, mode, query, caseSensitive, wholeWord, sourceIds, limit,
            });
            if (res.results) merged.push(...res.results);
            if (res.timeout) timeout = true;
        } catch (err) {
            // One pack failing to open/query (e.g. post-install OPFS corruption)
            // must not sink results from the other packs — skip it.
            console.warn('[offline] search on pack "' + t + '" failed; skipping:', err && err.message || err);
        }
        if (merged.length >= limit) break;
    }
    return { rows: merged.slice(0, limit), timeout };
}

// ── Public facade ─────────────────────────────────────────────────────────────

window.SamudraOffline = {
    /** Pre-warm the worker + pack detection (call on the 'offline' event). */
    prewarm() { ensureReady().catch(() => {}); },
    /** Resolves once (lazy) init has completed; rejects if init failed. Lets
     *  callers (e.g. the status pill) react when offline search becomes ready. */
    whenReady() { return ensureReady(); },
    /** True once init has completed AND at least one pack is installed. */
    isAvailable() { return _ready && _installedPacks.length > 0; },
    /** Has the bridge finished its (lazy) init at least once? */
    isReady() { return _ready; },
    /** Which packs are usable offline. */
    installedPacks() { return _installedPacks.slice(); },
    /** Run an offline search across installed packs. Resolves {rows, timeout}. */
    search,
    /** Render rows to an HTML string for #results-area. */
    renderHtml,
    /** Force re-detection of installed packs (worker init is idempotent/fast).
     *  Called internally by search() on the no-pack path so a pack installed
     *  since first init is picked up without a page reload. */
    refresh() { _initPromise = null; _ready = false; return ensureReady(); },
};

// Pre-warm when the browser reports going offline, so the first offline search
// is fast. Harmless if it fails (e.g. no pack installed).
window.addEventListener('offline', () => window.SamudraOffline.prewarm());
