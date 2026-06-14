/**
 * search.worker.js — Dedicated worker for offline SQLite search.
 *
 * Loaded as a module worker:
 *   new Worker('/static/scripts/search.worker.js', { type: 'module' })
 *
 * ── Why dynamic import() and not a static import ──────────────────────────────
 * sqlite3.mjs MUST be brought in via `await import(...)` inside _init(), NOT via
 * a top-level `import sqlite3InitModule from '...'`. A static import makes
 * sqlite3.mjs a load-time dependency of this worker module; in that position it
 * fails worker instantiation with a detail-less `error` event (the browser
 * surfaces `[object Event]` with no message/filename). Deferring the import to
 * runtime lets the worker instantiate first, then pull in sqlite3 cleanly.
 * Verified in Chrome 2026-06-13 against @sqlite.org/sqlite-wasm 3.53.0.
 *
 * ── Storage: opfs-sahpool, not OpfsDb ────────────────────────────────────────
 * The regular OPFS VFS (sqlite3.oo1.OpfsDb) does NOT initialise in this build
 * even on a cross-origin-isolated page (sqlite3.opfs is undefined — the async
 * proxy never comes up). The OPFS SAH Pool VFS (installOpfsSAHPoolVfs) DOES
 * work, is durable, uses synchronous access handles, and crucially needs no
 * cross-origin isolation — so the same pack works on pages without COEP.
 * Packs live in the pool under the virtual filename `/samudra-{packType}.db`.
 *
 * Message protocol: { type, id, payload? }
 * Reply protocol:   { type: 'reply', id, ok: bool, result | error }
 *
 * Supported message types:
 *   init        — load sqlite3 wasm + install SAH pool; reply: { vfs }
 *   importPack  — write downloaded pack bytes into durable storage;
 *                 payload: { packType, buffer (ArrayBuffer, transferable) }
 *                 reply: { packType, byteLength }
 *   removePack  — delete a pack from durable storage; payload: { packType }
 *   hasPack     — is a pack present in durable storage? payload: { packType }
 *                 reply: { packType, installed }
 *   openPack    — open a pack DB; payload: { packType, buffer? }
 *                 reply: { packType, meta }
 *   closePack   — close a pack; payload: { packType }
 *   getMeta     — read pack_meta as an object; payload: { packType }
 *                 reply: { packType, meta }
 *   listSources — pack_sources rows; payload: { packType }
 *                 reply: { packType, sources: [{source_id, source_slug, title, role}] }
 *   query       — search; payload: { packType, mode, query, caseSensitive,
 *                                    wholeWord, sourceIds, limit }
 *   status      — current state; reply: { initialized, vfs, openPacks }
 */

// ── State ─────────────────────────────────────────────────────────────────────

let _sqlite3 = null;
let _pool = null;          // opfs-sahpool poolUtil, or null when unavailable
let _initPromise = null;
const _dbs = {};           // packType → sqlite3 DB instance

function _packFile(packType) {
    return `/samudra-${packType}.db`;
}

// ── Initialisation ────────────────────────────────────────────────────────────

async function _init() {
    if (_sqlite3) return _sqlite3;
    if (_initPromise) return _initPromise;
    _initPromise = (async () => {
        // Dynamic import — see header note. sqlite3.mjs locates sqlite3.wasm
        // itself via its own import.meta.url (same /static/wasm/ directory).
        const mod = await import('/static/wasm/sqlite3.mjs');
        _sqlite3 = await mod.default();
        // Durable VFS. Falls back to memory-only when the pool can't install
        // (e.g. no FileSystemSyncAccessHandle support on very old browsers).
        try {
            _pool = await _sqlite3.installOpfsSAHPoolVfs({
                name: 'samudra-offline',
                initialCapacity: 6,
            });
        } catch (err) {
            _pool = null;
        }
        return _sqlite3;
    })();
    try {
        return await _initPromise;
    } catch (err) {
        _initPromise = null;   // allow retry on transient failure
        throw err;
    }
}

function _detectVfs() {
    return _pool ? 'opfs-sahpool' : 'memory';
}

// ── Durable storage (opfs-sahpool) ─────────────────────────────────────────────

function _hasPack(packType) {
    if (!_pool) return false;
    return _pool.getFileNames().includes(_packFile(packType));
}

async function _importPack(packType, buffer) {
    if (!_pool) {
        throw new Error('Durable storage is unavailable; pack cannot be saved');
    }
    const name = _packFile(packType);
    // importDb accepts the raw SQLite file bytes (the downloaded pack IS a
    // valid SQLite file, so no transform is needed).
    const bytes = new Uint8Array(buffer);
    const n = _pool.importDb(name, bytes);
    return { packType, byteLength: n };
}

function _removePack(packType) {
    if (_dbs[packType]) {
        try { _dbs[packType].close(); } catch (_) { /* ignore */ }
        delete _dbs[packType];
    }
    if (_pool && _hasPack(packType)) {
        _pool.unlink(_packFile(packType));
    }
    return { packType };
}

// ── Pack open / close ─────────────────────────────────────────────────────────

function _openFromPool(packType) {
    // Durable read from the SAH pool. The file must have been placed there by
    // _importPack first.
    return new _pool.OpfsSAHPoolDb(_packFile(packType));
}

function _openFromBuffer(sqlite3, buffer) {
    // Deserialise an ArrayBuffer into an in-memory DB. Used when:
    //   - durable storage is unavailable (memory fallback)
    //   - tests pass a fixture pack directly
    const db = new sqlite3.oo1.DB(':memory:');
    const p = sqlite3.wasm.allocFromTypedArray(new Uint8Array(buffer));
    const rc = sqlite3.capi.sqlite3_deserialize(
        db.pointer, 'main', p, buffer.byteLength, buffer.byteLength,
        sqlite3.capi.SQLITE_DESERIALIZE_FREEONCLOSE |
        sqlite3.capi.SQLITE_DESERIALIZE_RESIZEABLE
    );
    if (rc !== 0) {
        sqlite3.wasm.dealloc(p);
        throw new Error(`sqlite3_deserialize failed (rc=${rc})`);
    }
    return db;
}

function _packMeta(db) {
    return Object.fromEntries(
        db.selectObjects('SELECT key, value FROM pack_meta').map(r => [r.key, r.value])
    );
}

async function _openPack(packType, buffer) {
    if (_dbs[packType]) return _dbs[packType];   // idempotent
    let db;
    if (buffer) {
        db = _openFromBuffer(_sqlite3, buffer);
    } else if (_hasPack(packType)) {
        db = _openFromPool(packType);
    } else {
        throw new Error(`Pack '${packType}' is not installed and no buffer was provided`);
    }
    _dbs[packType] = db;
    return db;
}

// ── Search ────────────────────────────────────────────────────────────────────

function _reEscape(s) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function _buildMatchExpr(token, wholeWord) {
    // Escape FTS5 double-quote: double it
    const escaped = token.replace(/"/g, '""');
    // Whole-word: no trailing wildcard; default: prefix match via trailing *
    return wholeWord ? `"${escaped}"` : `"${escaped}"*`;
}

function _runFts(db, params) {
    const {
        terms,              // string[]  — pre-split multi-line query
        caseSensitive = false,
        wholeWord = false,
        sourceIds = null,
        limit = 200,
    } = params;

    const results = [];
    const seen = new Set();  // deduplicate across OR terms

    for (const term of terms) {
        if (!term.trim()) continue;
        const tokens = term.trim().split(/\s+/).filter(Boolean);
        if (!tokens.length) continue;

        // Build FTS5 MATCH: space-separated tokens are AND inside a term
        const matchExpr = tokens.map(t => _buildMatchExpr(t, wholeWord)).join(' AND ');

        let sql =
            'SELECT cl.id, cl.source_id, cl.link_id, cl.canonical_id, ' +
            '       cl.chapter, cl.line_num, cl.line_text ' +
            'FROM corpus_fts f ' +
            'JOIN corpus_lines cl ON cl.id = f.rowid ' +
            'WHERE corpus_fts MATCH ?';
        const bindVals = [matchExpr];

        if (sourceIds && sourceIds.length) {
            sql += ` AND cl.source_id IN (${sourceIds.map(() => '?').join(',')})`;
            bindVals.push(...sourceIds);
        }
        // Over-fetch to allow for post-filter loss
        sql += ` LIMIT ${Math.min(limit * 10, 5000)}`;

        const rows = db.selectObjects(sql, bindVals);

        for (const row of rows) {
            if (seen.has(row.id)) continue;

            // Case-sensitive post-filter
            if (caseSensitive) {
                const allTokensMatch = tokens.every(t => row.line_text.includes(t));
                if (!allTokensMatch) continue;
            }

            // Whole-word post-filter (FTS5 prefix suppressed above, but
            // boundary check is still needed for multi-char Unicode words)
            if (wholeWord) {
                const allBounded = tokens.every(t => {
                    try {
                        return new RegExp(`(?<![\\p{L}\\p{N}])${_reEscape(t)}(?![\\p{L}\\p{N}])`, 'u')
                            .test(row.line_text);
                    } catch (_) {
                        return row.line_text.includes(t);
                    }
                });
                if (!allBounded) continue;
            }

            seen.add(row.id);
            results.push(row);
            if (results.length >= limit) return results;
        }
    }
    return results;
}

function _runRegex(db, params) {
    const {
        patterns,           // string[]  — one regex per OR term
        caseSensitive = false,
        sourceIds = null,
        limit = 200,
    } = params;

    const regexes = patterns.map(p => {
        try { return new RegExp(p, caseSensitive ? 'u' : 'iu'); }
        catch (_) { return null; }
    }).filter(Boolean);

    if (!regexes.length) return { results: [], scanned: 0, timeout: false };

    let sql = 'SELECT id, source_id, link_id, canonical_id, chapter, line_num, line_text FROM corpus_lines';
    const bindVals = [];
    if (sourceIds && sourceIds.length) {
        sql += ` WHERE source_id IN (${sourceIds.map(() => '?').join(',')})`;
        bindVals.push(...sourceIds);
    }

    const results = [];
    let scanned = 0;
    let timedOut = false;
    const BUDGET_ROWS = 500_000;
    const BUDGET_MS   = 5_000;
    const startMs = Date.now();

    // Stream rows one at a time. selectObjects() would MATERIALISE the whole
    // table into a JS array first (≈16 s for the 320k-row base pack), which
    // blows the time budget before a single regex runs — making regex search
    // always return 0 on large packs. step() lets the watchdog bound real work.
    // Per row we fetch only line_text (column index 6) for the regex test and
    // build the full row object solely on a match, avoiding 320k allocations.
    const stmt = db.prepare(sql);
    try {
        if (bindVals.length) stmt.bind(bindVals);
        while (stmt.step()) {
            scanned++;
            if (scanned > BUDGET_ROWS || Date.now() - startMs > BUDGET_MS) {
                timedOut = true;
                break;
            }
            const lineText = stmt.get(6);  // line_text (0:id 1:source_id 2:link_id 3:canonical_id 4:chapter 5:line_num 6:line_text)
            if (regexes.some(re => re.test(lineText))) {
                results.push(stmt.get({}));
                if (results.length >= limit) break;
            }
        }
    } finally {
        stmt.finalize();
    }
    return { results, scanned, timeout: timedOut };
}

// ── Message dispatch ──────────────────────────────────────────────────────────

async function _handle(type, payload) {
    switch (type) {
        case 'init': {
            await _init();
            return { vfs: _detectVfs() };
        }

        case 'importPack': {
            await _init();
            const { packType = 'base', buffer = null } = payload;
            if (!buffer) throw new Error('importPack requires a buffer');
            return _importPack(packType, buffer);
        }

        case 'removePack': {
            await _init();
            const { packType = 'base' } = payload;
            return _removePack(packType);
        }

        case 'hasPack': {
            await _init();
            const { packType = 'base' } = payload;
            return { packType, installed: _hasPack(packType) };
        }

        case 'openPack': {
            await _init();
            const { packType = 'base', buffer = null } = payload;
            const db = await _openPack(packType, buffer);
            return { packType, meta: _packMeta(db) };
        }

        case 'closePack': {
            const { packType = 'base' } = payload;
            if (_dbs[packType]) {
                try { _dbs[packType].close(); } catch (_) { /* ignore */ }
                delete _dbs[packType];
            }
            return { packType };
        }

        case 'getMeta': {
            await _init();
            const { packType = 'base' } = payload;
            const db = await _openPack(packType, null);
            return { packType, meta: _packMeta(db) };
        }

        case 'listSources': {
            await _init();
            const { packType = 'base' } = payload;
            const db = await _openPack(packType, null);
            const sources = db.selectObjects(
                'SELECT source_id, source_slug, title, role FROM pack_sources ORDER BY source_id'
            );
            return { packType, sources };
        }

        case 'query': {
            const { packType = 'base', mode = 'plain', query = '', ...rest } = payload;
            const db = _dbs[packType];
            if (!db) throw new Error(`Pack '${packType}' is not open`);

            // Multi-line query → OR terms
            const terms = query.split('\n').map(t => t.trim()).filter(Boolean);

            if (mode === 'regex') {
                return { mode, ..._runRegex(db, { patterns: terms, ...rest }) };
            } else {
                const results = _runFts(db, { terms, ...rest });
                return { mode, results };
            }
        }

        case 'status': {
            return {
                initialized: !!_sqlite3,
                vfs: _sqlite3 ? _detectVfs() : null,
                openPacks: Object.keys(_dbs),
            };
        }

        default:
            throw new Error(`Unknown message type: ${type}`);
    }
}

self.onmessage = async function (e) {
    const { type, id, payload = {} } = e.data;
    try {
        const result = await _handle(type, payload);
        self.postMessage({ type: 'reply', id, ok: true, result });
    } catch (err) {
        self.postMessage({ type: 'reply', id, ok: false, error: String(err && err.message || err) });
    }
};
