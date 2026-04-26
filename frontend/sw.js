/* DHARMA-NYAYA — Service Worker
 * Provides offline capability and caches the Rights Card for offline use.
 */

const CACHE_VERSION = 'dharma-nyaya-v4';
const OFFLINE_PAGE = '/offline-rights';

const STATIC_ASSETS = [
  '/',
  '/chat',
  '/quiz',
  '/sos',
  '/legal-aid',
  '/legal-docs',
  '/spot-the-trap',
  '/predict',
  '/voice',
  '/offline-rights',
  '/offline-guides',
  '/assets/css/styles.css',
  '/assets/js/app.js',
  '/assets/js/i18n.js',
  '/assets/js/network.js',
  '/assets/js/pwa.js',
  '/assets/favicon.svg',
  '/manifest.json',
];

// ── Install: pre-cache shell + offline rights page ────────────────────────

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_VERSION).then(cache => {
      // Cache what we can, ignore failures for network-only assets
      return Promise.allSettled(
        STATIC_ASSETS.map(url =>
          cache.add(url).catch(() => console.warn('[SW] Could not cache:', url))
        )
      );
    }).then(() => self.skipWaiting())
  );
});

// ── Activate: purge old caches ────────────────────────────────────────────

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(key => key !== CACHE_VERSION)
          .map(key => caches.delete(key))
      )
    ).then(() => self.clients.claim())
  );
});

// ── Fetch: Network-first for API, Cache-first for assets ─────────────────

self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET and cross-origin (CDN fonts, tailwind)
  if (request.method !== 'GET') return;
  if (url.origin !== self.location.origin) return;

  // API routes: network only, no caching
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request).catch(() =>
        new Response(
          JSON.stringify({ error: 'Offline', message: 'No internet connection.' }),
          { status: 503, headers: { 'Content-Type': 'application/json' } }
        )
      )
    );
    return;
  }

  // Static assets: cache-first
  if (
    url.pathname.startsWith('/assets/') ||
    url.pathname === '/manifest.json' ||
    url.pathname.endsWith('.svg') ||
    url.pathname.endsWith('.png') ||
    url.pathname.endsWith('.woff2')
  ) {
    event.respondWith(
      caches.match(request).then(cached => cached || fetch(request).then(resp => {
        const clone = resp.clone();
        caches.open(CACHE_VERSION).then(cache => cache.put(request, clone));
        return resp;
      }))
    );
    return;
  }

  // HTML pages: network-first, fallback to cache, then offline rights page
  event.respondWith(
    fetch(request)
      .then(resp => {
        // Cache successful page loads
        if (resp.ok) {
          const clone = resp.clone();
          caches.open(CACHE_VERSION).then(cache => cache.put(request, clone));
        }
        return resp;
      })
      .catch(() =>
        caches.match(request).then(cached => {
          if (cached) return cached;
          // For navigation requests fall back to offline rights page
          if (request.mode === 'navigate') {
            return caches.match(OFFLINE_PAGE);
          }
          return new Response('Offline', { status: 503 });
        })
      )
  );
});
