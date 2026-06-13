/**
 * offline.js — Offline reader storage module
 *
 * S4 contract surface (PHASE2_PLAN §3):
 *   registerOffline(slug)   — fetch and cache a source's reader page + assets
 *   removeOffline(slug)     — remove from cache and registry
 *   listOffline()           — returns [{slug, url, size, cachedAt}]
 *   persistRequested()      — call navigator.storage.persist(); returns Promise<boolean>
 *   isOffline(slug)         — synchronous check against in-memory registry
 *   getQuota()              — returns Promise<{usage, quota, percent}>
 *
 * Storage layout:
 *   Cache 'samudra-offline-registry'  — key=reader URL, value=metadata response
 *   Cache 'samudra-offline-pages'     — key=URL, value=full HTTP response
 *
 * The SW reads 'samudra-offline-registry' to route cached navigations.
 * Callers must call init() once (awaitable; safe to call multiple times).
 */

const REGISTRY_CACHE = 'samudra-offline-registry';
const PAGES_CACHE    = 'samudra-offline-pages';

let _registry = null; // {slug → {slug, url, size, cachedAt}}

async function _loadRegistry() {
  if (_registry) return _registry;
  _registry = {};
  try {
    const cache = await caches.open(REGISTRY_CACHE);
    const keys  = await cache.keys();
    await Promise.all(keys.map(async (req) => {
      const res  = await cache.match(req);
      const meta = await res.json();
      _registry[meta.slug] = meta;
    }));
  } catch (_) {}
  return _registry;
}

async function _saveRegistryEntry(meta) {
  const cache = await caches.open(REGISTRY_CACHE);
  const body  = JSON.stringify(meta);
  await cache.put(
    meta.url,
    new Response(body, {headers: {'Content-Type': 'application/json'}}),
  );
  _registry[meta.slug] = meta;
}

async function _deleteRegistryEntry(slug) {
  const reg = await _loadRegistry();
  const meta = reg[slug];
  if (!meta) return;
  const cache = await caches.open(REGISTRY_CACHE);
  await cache.delete(meta.url);
  delete _registry[slug];
}

// ── Public API ────────────────────────────────────────────────────────────────

export async function init() {
  await _loadRegistry();
}

export function isOffline(slug) {
  return _registry != null && slug in _registry;
}

export async function listOffline() {
  const reg = await _loadRegistry();
  return Object.values(reg).sort((a, b) => a.cachedAt - b.cachedAt);
}

/**
 * Cache a source's reader page so it's available offline.
 * Fetches the reader URL, stores it in samudra-offline-pages, and
 * records the entry in the registry so the SW can route it.
 *
 * @param {string} slug     — source slug (e.g. "01_rigveda")
 * @param {Function} [onProgress] — called with (fetched, total) byte counts
 * @returns {Promise<void>}
 */
export async function registerOffline(slug, onProgress) {
  await _loadRegistry();
  const url   = `/sources/${encodeURIComponent(slug)}`;
  const cache = await caches.open(PAGES_CACHE);

  const response = await fetch(url);
  if (!response.ok) throw new Error(`HTTP ${response.status} for ${url}`);

  // Stream the body so we can report progress and measure size.
  const reader = response.body.getReader();
  const chunks = [];
  let   loaded = 0;
  const contentLength = parseInt(response.headers.get('Content-Length') || '0', 10);

  while (true) {
    const {done, value} = await reader.read();
    if (done) break;
    chunks.push(value);
    loaded += value.length;
    if (onProgress) onProgress(loaded, contentLength || loaded);
  }

  const body = new Uint8Array(loaded);
  let offset = 0;
  for (const chunk of chunks) {
    body.set(chunk, offset);
    offset += chunk.length;
  }

  // Reconstruct a storable response from the streamed body.
  const storedResponse = new Response(body, {
    status:  response.status,
    headers: response.headers,
  });
  await cache.put(url, storedResponse);

  const meta = {
    slug,
    url,
    size:     loaded,
    cachedAt: Date.now(),
  };
  await _saveRegistryEntry(meta);
}

/**
 * Remove a source from the offline cache and registry.
 */
export async function removeOffline(slug) {
  const reg  = await _loadRegistry();
  const meta = reg[slug];
  if (!meta) return;
  const cache = await caches.open(PAGES_CACHE);
  await cache.delete(meta.url);
  await _deleteRegistryEntry(slug);
}

/**
 * Request persistent storage (prevents iOS/Android eviction).
 * @returns {Promise<boolean>} — true if granted
 */
export async function persistRequested() {
  if (!navigator.storage || !navigator.storage.persist) return false;
  return navigator.storage.persist();
}

/**
 * Storage quota info.
 * @returns {Promise<{usage:number, quota:number, percent:number}>}
 */
export async function getQuota() {
  if (!navigator.storage || !navigator.storage.estimate) {
    return {usage: 0, quota: 0, percent: 0};
  }
  const {usage, quota} = await navigator.storage.estimate();
  return {
    usage:   usage  || 0,
    quota:   quota  || 0,
    percent: quota ? Math.round((usage / quota) * 100) : 0,
  };
}
