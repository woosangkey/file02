// N1 합격노트 — 오프라인 저장 (온라인이면 최신본, 오프라인이면 저장본)
// 데이터를 고치면 VERSION 숫자를 올릴 것. 음성(audio/)은 한 번 들은 날부터 저장된다.
const VERSION = 'n1note-v1';
const FILES = ["./", "index.html", "app.js", "data/m01.js", "data/m02.js", "data/m03.js", "data/m04.js", "data/m05.js", "data/m06.js", "data/m07.js", "data/m08.js", "data/m09.js", "data/m10.js", "data/m11.js", "data/m12.js", "data/m13.js", "data/final.js", "data/audio-index.js", "manifest.webmanifest", "icon-192.png", "icon-512.png"];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(VERSION).then(c => c.addAll(FILES)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k !== VERSION && k !== 'n1note-audio').map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);

  // 글꼴·음성: 한 번 받으면 저장본 사용
  const audio = url.origin === location.origin && url.pathname.includes('/audio/');
  if (audio || url.hostname.includes('fonts.googleapis.com') || url.hostname.includes('fonts.gstatic.com')) {
    if (req.headers.has('range')) return;  // 구간 요청은 브라우저에 맡김
    const box = audio ? 'n1note-audio' : VERSION;
    e.respondWith(caches.open(box).then(c => c.match(req).then(hit => hit ||
      fetch(req).then(res => { if (res.ok && res.status === 200) c.put(req, res.clone()); return res; }))));
    return;
  }

  // 앱 파일: 최신본 먼저, 실패하면 저장본
  if (url.origin === location.origin) {
    e.respondWith(fetch(req).then(res => {
      if (res.ok) { const copy = res.clone(); caches.open(VERSION).then(c => c.put(req, copy)); }
      return res;
    }).catch(() => caches.match(req, { ignoreSearch: true }).then(hit => hit || caches.match('index.html'))));
  }
});
