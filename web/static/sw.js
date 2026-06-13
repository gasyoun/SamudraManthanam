/**
 * Service Worker — Пахтанье океана
 *
 * Strategy:
 *   - App-shell assets (CSS, JS, fonts, icons): cache-first (precached on install)
 *   - HTML navigations: network-first with cache fallback
 *   - API routes (/api/*): network-only (search stays online)
 *
 * Cache version: bump SW_VERSION to force cache refresh on deploy.
 * The activate handler prunes any caches whose name does not start with
 * CACHE_NAME, so old versions are cleaned automatically.
 */

const SW_VERSION = '1';
const CACHE_NAME = `samudra-v${SW_VERSION}`;

// Assets to precache on install (app shell).
// Keep this list small: large corpus reader pages are cached on-demand.
const PRECACHE_URLS = [
  '/',
  '/sources',
  '/static/style.css',
  '/static/site.css',
  '/static/manifest.webmanifest',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  // Fonts — woff2 subsets (small, always needed for first paint)
  '/static/fonts/charis-sil.woff2',
  '/static/fonts/charis-sil-bold.woff2',
  '/static/fonts/Sahitya-Regular.woff2',
  // Core scripts
  '/static/search.js',
  '/static/scripts/reader.js',
  '/static/scripts/selection.js',
];

// ── Install: precache app shell ──────────────────────────────────────────────

self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(PRECACHE_URLS)),
  );
});

// ── Activate: prune old caches ───────────────────────────────────────────────

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((k) => !k.startsWith('samudra-'))
          .map((k) => caches.delete(k)),
      ),
    ).then(() => self.clients.claim()),
  );
});

// ── Fetch: routing logic ─────────────────────────────────────────────────────

self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Only handle same-origin requests.
  if (url.origin !== location.origin) return;

  // API: always network-only. Search must stay live; corrections likewise.
  if (url.pathname.startsWith('/api/')) {
    return;
  }

  // Static assets: cache-first (fonts, CSS, JS, images).
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(cacheFirst(request));
    return;
  }

  // Reader pages manually marked "offline" by the user: cache-first.
  // (These are populated by the offline module in offline.js.)
  if (_isMarkedOffline(url.pathname)) {
    event.respondWith(cacheFirst(request));
    return;
  }

  // Everything else (HTML navigations): network-first, cached fallback.
  event.respondWith(networkFirst(request));
});

// ── Strategy implementations ─────────────────────────────────────────────────

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;

  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch (_) {
    return new Response('オフライン — ресурс недоступен', {
      status: 503,
      headers: { 'Content-Type': 'text/plain; charset=utf-8' },
    });
  }
}

async function networkFirst(request) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch (_) {
    const cached = await caches.match(request);
    if (cached) return cached;

    // Fallback: serve the root page shell from cache so navigation
    // still works even if the exact URL isn't cached.
    const shell = await caches.match('/');
    if (shell) return shell;

    return new Response(
      `<!DOCTYPE html><html lang="ru"><body>
       <p style="font-family:sans-serif;padding:2rem">
         Нет подключения к сети. Страница недоступна в офлайн-режиме.
         <br><a href="/">На главную</a></p></body></html>`,
      { status: 503, headers: { 'Content-Type': 'text/html; charset=utf-8' } },
    );
  }
}

// ── Offline registry helper ──────────────────────────────────────────────────
// offline.js writes slugs to the 'samudra-offline-registry' cache; the SW
// checks it here so routing decisions are synchronous-ish (cache.match is async
// but the check below wraps it to avoid blocking non-offline navigations).

const _offlineRegistry = new Set();

async function _loadOfflineRegistry() {
  try {
    const cache = await caches.open('samudra-offline-registry');
    const keys  = await cache.keys();
    keys.forEach((req) => _offlineRegistry.add(new URL(req.url).pathname));
  } catch (_) {}
}
_loadOfflineRegistry();

function _isMarkedOffline(pathname) {
  return _offlineRegistry.has(pathname);
}

// ── Message: update notification ─────────────────────────────────────────────

self.addEventListener('message', (event) => {
  if (event.data === 'skipWaiting') {
    self.skipWaiting();
  }
});
