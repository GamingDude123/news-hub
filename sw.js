/* EcoTrace service worker.
 *
 * Two different strategies on purpose:
 *   - HTML is network-first, so a push always reaches the phone. Cache-first
 *     here would leave people staring at a stale build with no way to refresh.
 *   - pack.json and the decoder are cache-first, because they are large,
 *     rarely change, and are exactly what you need when the signal dies.
 */

const CACHE = "ecotrace-v10";
const SHELL = ["/", "/ecotrace.html", "/pack.json", "/icon-180.png", "/icon-512.png", "/manifest.json"];

self.addEventListener("install", e => {
  e.waitUntil(
    caches.open(CACHE)
      .then(c => Promise.allSettled(SHELL.map(u => c.add(u))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;

  const url = new URL(req.url);
  const sameOrigin = url.origin === self.location.origin;
  const isDoc = req.mode === "navigate" || (req.headers.get("accept") || "").includes("text/html");

  // Never cache product lookups — a stale price or score is worse than none.
  if (url.pathname.startsWith("/api/")) return;

  if (isDoc) {
    e.respondWith(
      fetch(req)
        .then(res => {
          const copy = res.clone();
          caches.open(CACHE).then(c => c.put(req, copy)).catch(() => {});
          return res;
        })
        .catch(() => caches.match(req).then(r => r || caches.match("/ecotrace.html")))
    );
    return;
  }

  if (sameOrigin || /zxing|jsdelivr/.test(url.href)) {
    e.respondWith(
      caches.match(req).then(hit => hit || fetch(req).then(res => {
        if (res.ok) {
          const copy = res.clone();
          caches.open(CACHE).then(c => c.put(req, copy)).catch(() => {});
        }
        return res;
      }))
    );
  }
});
