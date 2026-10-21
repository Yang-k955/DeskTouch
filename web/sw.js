'use strict';
var CACHE = 'desktouch-static-v1';
var STATIC = ['index.html', 'style.css', 'app.js', 'manifest.json', 'icon.svg', 'icon192.png', 'icon512.png'];
var BASE = new URL('./', self.location.href);
var ALLOWED = STATIC.map(function (file) { return new URL(file, BASE).pathname; });
self.addEventListener('install', function (event) {
  event.waitUntil(caches.open(CACHE).then(function (cache) { return cache.addAll(STATIC.map(function (file) { return new URL(file, BASE).href; })); }).then(function () { return self.skipWaiting(); }));
});
self.addEventListener('activate', function (event) {
  event.waitUntil(caches.keys().then(function (keys) { return Promise.all(keys.filter(function (key) { return key.indexOf('desktouch-static-') === 0 && key !== CACHE; }).map(function (key) { return caches.delete(key); })); }).then(function () { return self.clients.claim(); }));
});
self.addEventListener('fetch', function (event) {
  var request = event.request;
  var url = new URL(request.url);
  if (request.method !== 'GET' || url.origin !== self.location.origin || url.search || request.headers.has('Authorization') || /^\/(api|ws)(\/|$)/.test(url.pathname)) return;
  var isHome = request.mode === 'navigate' && url.pathname === BASE.pathname;
  if (!isHome && ALLOWED.indexOf(url.pathname) < 0) return;
  var key = isHome ? new URL('index.html', BASE).href : request.url;
  event.respondWith(fetch(request, { cache: 'no-cache' }).then(function (response) {
    if (response.ok && response.type === 'basic') {
      var copy = response.clone(); event.waitUntil(caches.open(CACHE).then(function (cache) { return cache.put(key, copy); }));
    }
    return response;
  }).catch(function () { return caches.match(key).then(function (cached) { return cached || Response.error(); }); }));
});
