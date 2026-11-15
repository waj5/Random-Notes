const scope = self.registration.scope
const index = new URL('index.html', scope).href
const assets = new Set(offlineAssets.map(path => new URL(path, scope).href))
const novelsPath = new URL('novels', scope).pathname
const cachePrefix = `random-notes-shell:${scope}:`
const cacheName = cachePrefix + offlineVersion

self.addEventListener('install', event => {
  event.waitUntil(caches.open(cacheName).then(cache => cache.addAll([index, ...assets])))
})

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    for (const name of await caches.keys()) {
      if (name.startsWith(cachePrefix) && name !== cacheName) await caches.delete(name)
    }
    await self.clients.claim()
  })())
})

self.addEventListener('fetch', event => {
  const { request } = event
  if (request.method !== 'GET') return
  const url = new URL(request.url)
  if (url.origin !== self.location.origin) return

  const isNovelPage = url.pathname === novelsPath ||
    (url.pathname.startsWith(novelsPath + '/') && /^\/(?:\d+\/?)?$/.test(url.pathname.slice(novelsPath.length)))
  if (request.mode === 'navigate' && isNovelPage) {
    event.respondWith(fetch(request).catch(async () => {
      const cache = await caches.open(cacheName)
      return await cache.match(index) ?? Response.error()
    }))
  } else if (assets.has(url.href)) {
    event.respondWith((async () => {
      const cache = await caches.open(cacheName)
      return await cache.match(request) ?? fetch(request)
    })())
  }
})
