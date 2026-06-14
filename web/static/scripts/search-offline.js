/**
 * search-offline.js — Main-thread ES module.
 *
 * Owns the Worker lifecycle and exposes a Promise-based API over postMessage.
 * Import this module in any page that needs offline search capability.
 *
 * Usage:
 *   import * as offlineSearch from '/static/scripts/search-offline.js';
 *   await offlineSearch.init();
 *   await offlineSearch.installPack('base', pct => console.log(pct));
 *   const { results } = await offlineSearch.searchOffline({
 *       packType: 'base', mode: 'plain', query: 'dharma', limit: 50
 *   });
 *
 * Durable storage lives inside the worker (opfs-sahpool VFS). The main thread
 * never touches OPFS directly — it streams the download, verifies the hash,
 * then hands the bytes to the worker via a transferable ArrayBuffer.
 *
 * The module degrades gracefully:
 *   - If WASM fails to load → init() rejects; isSearchAvailable() stays false.
 *   - If the SAH pool can't install → worker reports vfs='memory'; installPack
 *     still works for the session but the pack is lost on tab close.
 *   - If a pack is not open → searchOffline() rejects cleanly.
 */

// Cache-bust token for the worker script. App JS under /static is now served
// `Cache-Control: no-cache` (it revalidates every load), so an edited or
// redeployed worker reaches users automatically — bumping this is NO LONGER
// required for freshness (DECISIONS_NEEDED D4 resolved). Kept frozen as
// belt-and-suspenders: `new Worker(url)` has its own script cache, and this
// guards against an intermediary that strips no-cache.
const WORKER_VERSION = '3d-2';

let _worker = null;
let _workerReady = false;     // true after first successful 'init' reply
let _initPromise = null;
let _pendingCalls = new Map();
let _msgId = 0;

// ── Internal: postMessage with Promise ────────────────────────────────────────

function _send(type, payload = {}, transfer = undefined) {
    return new Promise((resolve, reject) => {
        if (!_worker) {
            reject(new Error('Search worker is not running'));
            return;
        }
        const id = String(++_msgId);
        _pendingCalls.set(id, { resolve, reject });
        if (transfer && transfer.length) {
            _worker.postMessage({ type, id, payload }, transfer);
        } else {
            _worker.postMessage({ type, id, payload });
        }
    });
}

function _startWorker() {
    if (_worker) return;
    _worker = new Worker(`/static/scripts/search.worker.js?v=${WORKER_VERSION}`, { type: 'module' });

    _worker.onmessage = (e) => {
        const { id, ok, result, error } = e.data;
        const cb = _pendingCalls.get(id);
        if (!cb) return;
        _pendingCalls.delete(id);
        ok ? cb.resolve(result) : cb.reject(new Error(error));
    };

    _worker.onerror = (err) => {
        // Module-load failures surface here as a detail-less Event (no .message).
        const msg = err && err.message ? err.message : 'worker failed to load';
        console.error('[search-offline] worker error:', msg);
        for (const [, cb] of _pendingCalls) {
            cb.reject(new Error('Worker error: ' + msg));
        }
        _pendingCalls.clear();
        _workerReady = false;
    };
}

// ── Public API ────────────────────────────────────────────────────────────────

/**
 * Start the worker and load the WASM binary + durable VFS.
 * Safe to call multiple times — only initialises once.
 * Returns { vfs } describing the VFS chosen by the worker
 * ('opfs-sahpool' durable, or 'memory').
 */
export async function init() {
    if (_initPromise) return _initPromise;
    _startWorker();
    _initPromise = _send('init').then(result => {
        _workerReady = true;
        return result;
    }).catch(err => {
        _initPromise = null;   // allow retry
        _workerReady = false;
        throw err;
    });
    return _initPromise;
}

/**
 * Returns true when the worker is initialised and ready to accept queries.
 * Does not attempt to initialise — call init() first.
 */
export function isSearchAvailable() {
    return _workerReady;
}

/**
 * Is a pack present in durable storage?
 * @param {string} packType  'base' | 'dict'
 * @returns {Promise<boolean>}
 */
export async function hasPack(packType = 'base') {
    const { installed } = await _send('hasPack', { packType });
    return installed;
}

/**
 * Open an installed pack (or deserialise a provided buffer).
 *
 * @param {string} packType   'base' | 'dict'
 * @param {ArrayBuffer} [buffer]  If provided, deserialise into memory instead
 *                                of opening from durable storage.
 * @returns {Promise<{ packType, meta }>}
 */
export async function openPack(packType = 'base', buffer = null) {
    return _send('openPack', { packType, buffer });
}

/**
 * Close an open pack and free its memory. Does not remove it from storage.
 * @param {string} packType
 */
export async function closePack(packType = 'base') {
    return _send('closePack', { packType });
}

/**
 * Read pack_meta as a flat object (corpus_version, pack_version, built_at, …).
 * Opens the pack if needed.
 * @param {string} packType
 * @returns {Promise<object>}
 */
export async function packMeta(packType = 'base') {
    const { meta } = await _send('getMeta', { packType });
    return meta;
}

/**
 * List the sources in a pack (id, slug, title, role). Opens the pack if needed.
 * Used to map result rows (which carry only source_id) to display titles/links.
 * @param {string} packType
 * @returns {Promise<{packType, sources: Array<{source_id, source_slug, title, role}>}>}
 */
export async function listSources(packType = 'base') {
    return _send('listSources', { packType });
}

/**
 * Compare the installed pack's corpus_version against the server's current
 * version. Non-blocking — the UI surfaces the result as an "update available"
 * hint; packs are large, so auto-update is never performed.
 *
 * @param {string} packType
 * @returns {Promise<{installed: string|null, latest: string|null, updateAvailable: boolean}>}
 */
export async function checkVersion(packType = 'base') {
    let installed = null;
    let latest = null;
    try {
        const meta = await packMeta(packType);
        installed = meta.corpus_version || null;
    } catch (_) { /* pack not installed/openable */ }
    try {
        const r = await fetch('/api/corpus-version');
        if (r.ok) latest = (await r.json()).corpus_version || null;
    } catch (_) { /* offline — can't check */ }
    return {
        installed,
        latest,
        updateAvailable: !!(installed && latest && installed !== latest),
    };
}

/**
 * Run an offline search query.
 *
 * @param {object} params
 * @param {string}   params.query         Search string (multi-line = OR terms)
 * @param {string}   [params.packType]    'base' | 'dict'   default: 'base'
 * @param {string}   [params.mode]        'plain' | 'regex'  default: 'plain'
 * @param {boolean}  [params.caseSensitive]
 * @param {boolean}  [params.wholeWord]
 * @param {number[]} [params.sourceIds]   Filter by source IDs
 * @param {number}   [params.limit]       Max results (default: 200)
 *
 * @returns {Promise<{ mode, results, scanned?, timeout? }>}
 */
export async function searchOffline(params) {
    return _send('query', params);
}

/**
 * Worker status: which VFS is in use, which packs are open.
 * @returns {Promise<{ initialized, vfs, openPacks }>}
 */
export async function status() {
    if (!_worker) return { initialized: false, vfs: null, openPacks: [] };
    return _send('status');
}

/**
 * Download a pack from the server, verify its SHA-256, write it to durable
 * storage (opfs-sahpool, inside the worker), and open it.
 *
 * The download is decoded transparently if the server used Content-Encoding;
 * crypto.subtle.digest hashes the decoded bytes, which match the pack's
 * on-disk SHA-256 sidecar.
 *
 * @param {string}   packType      'base' | 'dict'
 * @param {Function} [onProgress]  Called with 0–100 during download
 * @returns {Promise<{ packType, byteLength, sha256, persisted }>}
 */
export async function installPack(packType = 'base', onProgress = null) {
    // Ensure the worker + VFS are up so the durable-vs-memory decision below
    // reads a real vfs (status() returns null before init).
    await init();

    // 1. Expected SHA-256 from the version endpoint. Fail CLOSED: if the server
    //    can't supply a hash (sidecar missing/unreadable), refuse to install
    //    rather than persisting bytes we can't verify.
    const verResp = await fetch('/api/corpus-version');
    if (!verResp.ok) throw new Error('Cannot reach /api/corpus-version');
    const verData = await verResp.json();
    const expectedSha = verData.pack_sha256?.[packType];
    if (!expectedSha) {
        throw new Error(`Integrity hash for '${packType}' is unavailable — refusing to install an unverifiable pack`);
    }

    // 2. Stream-download the pack.
    const packResp = await fetch(`/api/offline-packs/${packType}.db`);
    if (!packResp.ok) {
        if (packResp.status === 404) throw new Error(`Pack '${packType}' is not built yet`);
        throw new Error(`Pack download failed: ${packResp.status}`);
    }

    // The reader yields DECODED bytes. Under Content-Encoding: gzip,
    // Content-Length is the COMPRESSED size — wrong as a denominator. Raw
    // decoded size precedence:
    //   1. corpus-version pack_bytes — proxy-safe (a non-standard X-* header can
    //      be stripped by an intermediary), already fetched above (no round-trip)
    //   2. X-Db-Bytes header — travels with the served bytes (consistent even if
    //      corpus-version and the served .gz momentarily disagree)
    //   3. Content-Length — only valid when the body is NOT encoded (raw .db)
    //   4. indeterminate (-1) — report the byte count so the UI shows progress
    //      instead of freezing at 0
    const verBytes = verData.pack_bytes?.[packType] || 0;
    const headerBytes = parseInt(packResp.headers.get('x-db-bytes') || '0', 10);
    const contentLength = parseInt(packResp.headers.get('content-length') || '0', 10);
    const total = verBytes || headerBytes || (packResp.headers.get('content-encoding') ? 0 : contentLength);
    const reader = packResp.body.getReader();
    const chunks = [];
    let received = 0;

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        chunks.push(value);
        received += value.byteLength;
        if (onProgress) {
            onProgress(total ? Math.min(100, Math.round((received / total) * 100)) : -1, received);
        }
    }

    // 3. Concatenate chunks → ArrayBuffer.
    const u8 = new Uint8Array(received);
    let offset = 0;
    for (const chunk of chunks) { u8.set(chunk, offset); offset += chunk.byteLength; }
    const ab = u8.buffer;

    // 4. SHA-256 verification (Web Crypto API). expectedSha is guaranteed
    //    non-empty here (fail-closed check above).
    const hashBuf = await crypto.subtle.digest('SHA-256', ab);
    const hashHex = Array.from(new Uint8Array(hashBuf))
        .map(b => b.toString(16).padStart(2, '0')).join('');

    if (hashHex !== expectedSha) {
        throw new Error(`SHA-256 mismatch: expected ${expectedSha}, got ${hashHex}`);
    }

    // 5. Hand the verified bytes to the worker as a transferable (no multi-100MB
    //    structured-clone copy). Durable when the SAH pool is available;
    //    otherwise deserialise into memory for this session (old browsers with
    //    no FileSystemSyncAccessHandle). Either path consumes `ab`.
    const st = await status();
    let byteLength = ab.byteLength;
    let persisted = false;
    if (st.vfs === 'opfs-sahpool') {
        ({ byteLength } = await _send('importPack', { packType, buffer: ab }, [ab]));
        await openPack(packType);
        persisted = true;
    } else {
        await _send('openPack', { packType, buffer: ab }, [ab]);
    }

    return { packType, byteLength, sha256: hashHex, persisted };
}

/**
 * Remove a pack from durable storage and close it.
 * @param {string} packType
 */
export async function removePack(packType = 'base') {
    return _send('removePack', { packType });
}
