/**
 * VisionAttenda AI - Progressive Web App Service Worker
 */

const CACHE_NAME = 'visionattenda-v1.0.0';
const STATIC_ASSETS = [
  '/',
  '/dashboard',
  '/live',
  '/students',
  '/attendance',
  '/reports',
  '/settings',
  '/static/css/style.css',
  '/static/js/main.js',
  '/static/js/live_recognition.js',
  '/static/js/face_registration.js',
  '/static/js/dashboard.js',
  '/static/js/attendance.js',
  '/static/js/reports.js',
  '/static/manifest.json',
  '/static/images/icons/icon-192.png',
  '/static/images/icons/icon-512.png',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css',
  'https://cdn.jsdelivr.net/npm/chart.js',
  'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800&display=swap'
];

// Install Event: Pre-cache core app shell
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[ServiceWorker] Caching App Shell Assets');
      return cache.addAll(STATIC_ASSETS).catch(err => console.warn('Some assets could not be cached on install:', err));
    })
  );
  self.skipWaiting();
});

// Activate Event: Clean up old cache versions
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keyList) => {
      return Promise.all(
        keyList.map((key) => {
          if (key !== CACHE_NAME) {
            console.log('[ServiceWorker] Removing old cache version:', key);
            return caches.delete(key);
          }
        })
      );
    })
  );
  return self.clients.claim();
});

// Fetch Event: Network-first for dynamic APIs & Camera frames, Cache-first for static CSS/JS/images
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Always use Network-Only for dynamic APIs, webcam frame streams, and POST/PUT requests
  if (url.pathname.startsWith('/api/') || url.pathname === '/video_feed' || event.request.method !== 'GET') {
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        // Return cache but update in background (stale-while-revalidate)
        fetch(event.request).then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, networkResponse));
          }
        }).catch(() => {});
        return cachedResponse;
      }

      return fetch(event.request).then((networkResponse) => {
        if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic') {
          return networkResponse;
        }

        const responseToCache = networkResponse.clone();
        caches.open(CACHE_NAME).then((cache) => {
          cache.put(event.request, responseToCache);
        });

        return networkResponse;
      }).catch(() => {
        // Fallback if offline
        return caches.match('/dashboard');
      });
    })
  );
});
