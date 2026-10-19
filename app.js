/* ================= 기본 설정 ================= */
const DEFAULT_START = '2026-11-02';      // Day 1 기본 날짜 (설정에서 변경 가능)
const EXAM = '2027-12-05';               // 목표 시험: 2027년 12월 JLPT (12월 첫째 일요일)
const MID_EXAM = '2027-07-04';           // 선택: 2027년 7월 JLPT (중간 점검 응시)
const TOTAL = 365;
const DAYS = window.N1_DAYS || {};
const AUDIO = window.N1_AUDIO || null;
const RANKS = [[0,'見習い · 수습'],[30,'初段'],[60,'二段'],[100,'三段'],[150,'四段'],[220,'五段 · 합격권'],[365,'免許皆伝 · N1']];
const PHASES = [
  [1,90,'1단계','N1 문법 기초 · 文法形式 / 組み立て / 文脈規定','N2 → N1'],
  [91,180,'2단계','N1 문법 심화 · 言い換え / 用法 / 文章の文法','N1 문법'],
  [181,270,'3단계','독해 실전 · 内容 / 統合 / 主張理解 + 경어','読解'],
  [271,360,'4단계','청해 집중 · 혼동 문법 · 실전 모의','聴解'],
  [361,365,'마무리','시험 전략 + 졸업 모의고사','合格']
];
// [월, 제목, 집중 파트]
const UNITS = [
  [1,'시간·계기 문법 + 사회·경제 한자어','文法形式の判断 · 漢字読み'],
  [2,'역접·조건 문법 + 빈출 부사','文の組み立て'],
  [3,'정도·강조·한정 + 형용사','文脈規定'],
  [4,'상태·경향·기준 + 복합동사','言い換え類義'],
  [5,'문어체 강조·평가 + 의태어','用法'],
  [6,'문장 흐름 문법 + 관용구','文章の文法'],
  [7,'접속사로 읽는 논리 + 사자성어','内容理解'],
  [8,'주장 문말 표현 + 가타카나어','統合理解 · 情報検索'],
  [9,'비즈니스 경어 + 시사 한자어','主張理解'],
  [10,'청해 회화체 + 言い換え 짝','課題 · ポイント理解'],
  [11,'혼동 문법 비교 + 用法 빈출어','概要 · 即時応答 · 統合'],
  [12,'빈출 문법 최종 정리','실전 모의'],
  [13,'시험 전략 + 졸업 모의고사','合格']
];
const isTest = d => d % 30 === 0 && d < TOTAL;
const isRev = d => d % 7 === 0 && d < TOTAL && !isTest(d);
const monthOf = d => Math.min(13, Math.ceil(d / 30));

/* ================= 저장소 (실패해도 동작) ================= */
const store = {
  get(k, def){ try{ const v = localStorage.getItem('n1note-'+k); return v == null ? def : JSON.parse(v); }catch(e){ return def; } },
  set(k, v){ try{ localStorage.setItem('n1note-'+k, JSON.stringify(v)); }catch(e){} }
};
const opts = Object.assign({kana:true, ko:true, rate:1}, store.get('opts', {}));
const saveOpts = () => store.set('opts', opts);
const START = () => store.get('start', DEFAULT_START);

/* ================= 날짜 ================= */
const pad = n => String(n).padStart(2,'0');
const ymd = d => d.getFullYear()+'-'+pad(d.getMonth()+1)+'-'+pad(d.getDate());
const midnight = s => new Date(s+'T00:00:00');
function today0(){ const t = new Date(); t.setHours(0,0,0,0); return t; }
function calendarDay(){ return Math.max(1, Math.min(TOTAL, Math.floor((today0() - midnight(START()))/86400000) + 1)); }
function dayOfDate(s){ return Math.floor((midnight(s) - midnight(START()))/86400000) + 1; }
function dateOf(day){ const s = midnight(START()); s.setDate(s.getDate()+day-1); return (s.getMonth()+1)+'/'+s.getDate(); }
function dDay(s){ return Math.ceil((midnight(s) - today0())/86400000); }

/* ================= 진도 ================= */
const done = () => store.get('done', {});
const isDone = d => !!done()[d];
function hasContent(d){
  if (d === TOTAL) return !!window.N1_FINAL;
  return !!DAYS[d] || isRev(d) || isTest(d);
}
function nextDay(){ for (let d=1; d<=TOTAL; d++){ if (!isDone(d)) return d; } return TOTAL; }
function doneCount(){ return Object.keys(done()).length; }
function rankOf(n){ let r = RANKS[0][1]; RANKS.forEach(([k,name]) => { if (n >= k) r = name; }); return r; }
function nextRank(n){ for (const [k,name] of RANKS){ if (n < k) return [k,name]; } return null; }
function streak(){
  const dd = Object.values(done()); if (!dd.length) return 0;
  const set = new Set(dd); let s = 0; const t = today0();
  if (!set.has(ymd(t))) t.setDate(t.getDate()-1);
  while (set.has(ymd(t))) { s++; t.setDate(t.getDate()-1); }
  return s;
}
function markDone(d){
  const m = done(); const before = rankOf(Object.keys(m).length);
  if (!m[d]) m[d] = ymd(new Date());
  store.set('done', m);
  const after = rankOf(Object.keys(m).length);
  if (after !== before) toast('🎉 승급! ' + after);
}
function dayTitle(d){
  if (d === TOTAL) return '졸업 모의고사 30제';
  if (isTest(d)) return monthOf(d)+'개월차 월말 모의';
  if (isRev(d)) return '주간 복습';
  return DAYS[d] ? DAYS[d].title : '';
}

/* ================= 간격 반복(SRS) ================= */
const GAPS = [1,2,4,8,16,32,64,128];
function allWords(){
  const out = {}; Object.values(DAYS).forEach(D => (D.words||[]).forEach(w => { out[w.w] = Object.assign({day:D.day}, w); }));
  return out;
}
function srs(){ return store.get('srs', {}); }
function addWords(day){
  const s = srs(); const t = new Date(); t.setDate(t.getDate()+1); const tomorrow = ymd(t);
  (DAYS[day] && DAYS[day].words || []).forEach(w => { if (!s[w.w]) s[w.w] = {box:0, due:tomorrow}; });
  store.set('srs', s);
}
function dueWords(){
  const s = srs(); const t = ymd(new Date()); const W = allWords();
  return Object.keys(s).filter(k => s[k].due <= t && W[k]).map(k => W[k]);
}
function grade(w, ok){
  const s = srs(); const c = s[w] || {box:0};
  c.box = ok ? Math.min(c.box+1, GAPS.length-1) : 0;
  const d = new Date(); d.setDate(d.getDate() + (ok ? GAPS[c.box] : 1));
  c.due = ymd(d); s[w] = c; store.set('srs', s);
}

/* ================= 음성 ================= */
// 1순위: 미리 만든 음성 파일(audio/dNNN.mp3) — 아이폰·아이패드 무음 모드에서도 재생됨
// 2순위: 기기의 일본어 TTS
let jaVoice = null;
function pickVoice(){
  try{
    const vs = speechSynthesis.getVoices().filter(v => /^ja/i.test(v.lang));
    jaVoice = vs.find(v => /google/i.test(v.name)) || vs.find(v => /nanami|keita|kyoko|otoya|online|natural/i.test(v.name)) || vs[0] || null;
  }catch(e){}
}
try{ pickVoice(); speechSynthesis.onvoiceschanged = pickVoice; }catch(e){}

const player = new Audio(); player.preload = 'auto';
let curUrl = '', token = 0, watch = 0, playingBtn = null;
const blobUrl = {}, loading = {};
const fileUrl = name => 'audio/'+name+'.mp3';
function prefetch(name){
  if (!AUDIO || !AUDIO[name] || blobUrl[name] || loading[name]) return;
  loading[name] = fetch(fileUrl(name)).then(r => r.ok ? r.blob() : Promise.reject(r.status))
    .then(b => { blobUrl[name] = URL.createObjectURL(b); }).catch(() => {}).finally(() => { delete loading[name]; });
}
let curName = '';
function findClip(text){
  if (!AUDIO) return null;
  if (curName && AUDIO[curName] && AUDIO[curName][text]) return {name:curName, s:AUDIO[curName][text][0], d:AUDIO[curName][text][1]};
  for (const name in AUDIO){ const h = AUDIO[name][text]; if (h) return {name, s:h[0], d:h[1]}; }
  return null;
}
function setPlaying(btn){ if (playingBtn) playingBtn.classList.remove('playing'); playingBtn = btn; if (btn) btn.classList.add('playing'); }
function speakTTS(text, onend){
  try{
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = 'ja-JP'; if (jaVoice) u.voice = jaVoice; u.rate = opts.rate;
    u.onend = u.onerror = () => onend && onend();
    speechSynthesis.speak(u);
    if (!jaVoice) setTimeout(() => { pickVoice(); if (!jaVoice) toast('일본어 음성이 없어요. 기기 설정에서 일본어 음성을 설치하세요.'); }, 600);
  }catch(e){ toast('이 화면에서는 음성이 나오지 않아요.'); onend && onend(); }
}
function stopAudio(){
  token++; cancelAnimationFrame(watch);
  try{ player.pause(); }catch(e){}
  try{ speechSynthesis.cancel(); }catch(e){}
  setPlaying(null);
  document.querySelectorAll('.line.now').forEach(x => x.classList.remove('now'));
}
function speak(text, btn, onend){
  const my = ++token; cancelAnimationFrame(watch);
  try{ speechSynthesis.cancel(); }catch(e){}
  setPlaying(btn);
  const end = () => { if (my !== token) return; setPlaying(null); onend && onend(); };
  const c = findClip(text);
  if (!c){ speakTTS(text, end); return; }
  const url = blobUrl[c.name] || fileUrl(c.name);
  if (curUrl !== url) player.src = curUrl = url;
  prefetch(c.name);
  player.defaultPlaybackRate = player.playbackRate = opts.rate;
  const stopAt = c.s + c.d;
  const tick = () => {
    if (my !== token) return;
    if (player.currentTime >= stopAt || player.ended){ player.pause(); end(); }
    else watch = requestAnimationFrame(tick);
  };
  if (player.readyState >= 1) player.currentTime = c.s;
  else { player.muted = true; player.addEventListener('loadedmetadata', () => { player.currentTime = c.s; player.muted = false; }, {once:true}); }
  const p = player.play();
  if (p) p.then(() => { if (my !== token) return; player.playbackRate = opts.rate; cancelAnimationFrame(watch); watch = requestAnimationFrame(tick); })
          .catch(() => { if (my !== token) return; player.muted = false; speakTTS(text, end); });
}
function playSeq(texts, btn, onIdx){
  let i = 0;
  const step = () => {
    if (i >= texts.length){ onIdx && onIdx(-1); setPlaying(null); return; }
    onIdx && onIdx(i);
    speak(texts[i++], btn, () => setTimeout(step, 350));
  };
  step();
}

/* ================= 녹음 (IndexedDB) ================= */
function idb(){ return new Promise((res, rej) => { try{ const r = indexedDB.open('n1note', 1); r.onupgradeneeded = () => r.result.createObjectStore('rec'); r.onsuccess = () => res(r.result); r.onerror = () => rej(r.error); }catch(e){ rej(e); } }); }
async function recPut(k, blob){ try{ const db = await idb(); db.transaction('rec','readwrite').objectStore('rec').put(blob, k); }catch(e){} }
async function recGet(k){ try{ const db = await idb(); return await new Promise(r => { const q = db.transaction('rec').objectStore('rec').get(k); q.onsuccess = () => r(q.result || null); q.onerror = () => r(null); }); }catch(e){ return null; } }
let mediaRec = null;
async function toggleRec(key, btn){
  if (mediaRec && mediaRec.state === 'recording'){ mediaRec.stop(); return; }
  try{
    const stream = await navigator.mediaDevices.getUserMedia({audio:true});
    const chunks = []; mediaRec = new MediaRecorder(stream);
    mediaRec.ondataavailable = e => chunks.push(e.data);
    mediaRec.onstop = async () => {
      stream.getTracks().forEach(t => t.stop());
      await recPut(key, new Blob(chunks, {type: mediaRec.mimeType || 'audio/webm'}));
      btn.classList.remove('recording'); btn.textContent = '🎙 다시 녹음'; toast('녹음 저장됨');
    };
    mediaRec.start(); btn.classList.add('recording'); btn.textContent = '⏹ 녹음 끝내기';
  }catch(e){ toast('마이크를 쓸 수 없어요 (권한 허용 필요)'); }
}
async function playRec(key){
  const b = await recGet(key); if (!b){ toast('아직 녹음이 없어요'); return; }
  const a = new Audio(URL.createObjectURL(b)); a.play();
}

/* ================= 공통 ================= */
const $app = document.getElementById('app');
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function toast(msg){ const t = document.createElement('div'); t.className = 'toast'; t.textContent = msg; document.body.appendChild(t); setTimeout(() => t.remove(), 2600); }
const AV_COLORS = {'男':'#4a6cff','女':'#ff6b8a','部長':'#c9a227','課長':'#b5651d','店員':'#2fa36b','客':'#7a8a9a','司会':'#8b6cff','先生':'#3d6fb6','医者':'#1aa58a','社長':'#d6283f','係員':'#5e9c8f','アナウンサー':'#a64ca6'};
function avatar(who){
  const c = AV_COLORS[who] || Object.entries(AV_COLORS).find(([k]) => String(who).includes(k))?.[1] || '#8b6cff';
  return '<span class="av" style="background:'+c+'">'+esc(String(who||'?').replace(/の学生/,'').charAt(0))+'</span>';
}
function sayBtn(text){ return '<button class="say" data-say="'+esc(text)+'" aria-label="듣기">🔊</button>'; }
function shuffle(a){ a = a.slice(); for (let i=a.length-1;i>0;i--){ const j = Math.floor(Math.random()*(i+1)); [a[i],a[j]] = [a[j],a[i]]; } return a; }
const NUM = '①②③④';
document.addEventListener('click', e => {
  const s = e.target.closest('[data-say]'); if (s){ speak(s.dataset.say, s.classList.contains('say') ? s : null); return; }
  const w = e.target.closest('.word'); if (w){ w.classList.toggle('flip'); if (w.classList.contains('flip')) speak(w.dataset.w); return; }
  const k = e.target.closest('.ko.hid'); if (k){ k.classList.remove('hid'); }
});

/* ================= 화면: 홈 ================= */
function viewHome(){
  curName = '';
  const n = doneCount(), nd = nextDay(), cal = calendarDay(), nr = nextRank(n), due = dueWords().length;
  const pct = Math.round(n / TOTAL * 100), dd = dDay(EXAM), mid = dDay(MID_EXAM);
  let h = '<header class="top"><h1>N1 합격노트<small>日本語能力試験 N1 · 365일 완성 · 2027년 12월 시험 대비</small></h1></header>';
  h += '<section class="hero"><span class="rank">⚡ '+rankOf(n)+'</span>'
     + '<div class="big">Day '+nd+'</div><div class="sub">'+esc(dayTitle(nd))+'</div>'
     + '<div class="bar"><i style="width:'+pct+'%"></i></div>'
     + '<div class="small muted">'+n+' / 365일 완료 ('+pct+'%)'+(nr ? ' · 다음 승급 「'+nr[1]+'」까지 '+(nr[0]-n)+'일' : '')+'</div>'
     + '<div class="stats"><div class="stat"><b>'+streak()+'</b><span>연속 공부일</span></div><div class="stat"><b>'+Object.keys(srs()).length+'</b><span>배운 어휘</span></div><div class="stat"><b>'+(dd > 0 ? 'D-'+dd : dd === 0 ? 'D-DAY' : '종료')+'</b><span>12/5 N1 시험</span></div></div>';
  h += hasContent(nd) ? '<a class="cta" href="#day/'+nd+'">▶ Day '+nd+' 공부 시작</a>'
                      : '<div class="cta ghost">Day '+nd+' 자료 준비 중</div>';
  h += '</section>';
  if (nd < cal - 2) h += '<div class="notice">달력상으로는 Day '+cal+'이에요. 밀린 '+(cal-nd)+'일은 주간 복습일에 2개씩 따라잡아 보세요.</div>';
  if (mid > 0 && mid <= 120) h += '<div class="notice">7월 JLPT(7/4)까지 D-'+mid+'. 중간 점검으로 응시해 보는 것을 추천해요 — 접수는 보통 3~4월이에요.</div>';
  if (dd > 0 && dd <= 150 && dd > 90) h += '<div class="notice">12월 JLPT 접수 기간(보통 8~9월)을 놓치지 마세요. JLPT 한국 공식 사이트에서 확인하세요.</div>';
  if (nd === TOTAL && isDone(TOTAL) && dd > 0) h += '<div class="notice">365일 완주! 시험까지 남은 '+dd+'일은 월말 모의(Day 30·60·…·360)와 졸업 모의고사를 다시 풀고, 단어 복습을 매일 하세요.</div>';
  h += '<div class="row2"><a class="cta '+(due ? 'alt' : 'ghost')+'" href="#review" style="margin:0">🔁 어휘 복습 '+(due ? due+'개' : '없음')+'</a>'
     + '<a class="cta ghost" href="#words" style="margin:0">📖 어휘장</a></div>';

  // 365 진도판
  const midDay = dayOfDate(MID_EXAM);
  h += '<section class="card" style="margin-top:14px"><h2>📅 365일 진도판</h2>';
  PHASES.forEach(([a,b,name,desc,lv]) => {
    h += '<div class="phase"><span><b>'+name+'</b> · '+desc+'</span><span>'+lv+'</span></div><div class="grid">';
    for (let d=a; d<=b; d++){
      let cls = 'cell'; if (hasContent(d)) cls += ' open'; if (hasContent(d) && (isRev(d) || isTest(d) || d === TOTAL)) cls += ' rev';
      if (isDone(d)) cls += ' done'; if (d === nd) cls += ' next'; if (d === cal) cls += ' today'; if (d === midDay) cls += ' exam';
      const tip = 'Day '+d+' ('+dateOf(d)+')'+(d === midDay ? ' · 7월 JLPT' : '');
      h += hasContent(d) ? '<a class="'+cls+'" href="#day/'+d+'" title="'+tip+'">'+d+'</a>' : '<span class="'+cls+'" title="'+tip+'">'+d+'</span>';
    }
    h += '</div>';
  });
  h += '<div class="legend"><span><i style="background:linear-gradient(135deg,#8b6cff,#5aa9ff)"></i>완료</span><span><i style="background:#2a2456"></i>공부 가능</span><span><i style="background:#1f3a44"></i>복습·모의</span><span><i style="outline:2px solid #ffd166"></i>다음</span><span><i style="outline:2px solid #ff4d6d"></i>7월 시험</span></div></section>';

  // 월별 유닛
  h += '<section class="card"><h2>🗂 월별 유닛</h2><div class="eplist">';
  UNITS.forEach(([m,t,part]) => {
    const a = (m-1)*30+1, b = Math.min(m*30, TOTAL);
    const ds = []; for (let d=a; d<=b; d++) if (hasContent(d)) ds.push(d);
    const c = ds.filter(isDone).length;
    h += ds.length ? '<a class="eprow" href="#day/'+(ds.find(d => !isDone(d)) || ds[0])+'"><span>'+m+'개월차 · '+esc(t)+' <span class="muted small t">'+esc(part)+'</span></span><span class="small muted">'+c+'/'+ds.length+'</span></a>'
                   : '<div class="eprow lock"><span>'+m+'개월차 · '+esc(t)+'</span><span class="small">🔒</span></div>';
  });
  h += '</div></section>';

  h += '<section class="card"><h2>📝 N1 시험 구성</h2><div class="small" style="line-height:1.8">'
     + '<b>言語知識(文字・語彙・文法)・読解</b> 110분 · <b>聴解</b> 약 55분<br>'
     + '득점 구분: 언어지식 0~60 · 독해 0~60 · 청해 0~60 → <b>합격 100/180</b>, 각 구분 <b>19점 미만이면 불합격</b><br>'
     + '<span class="muted">시간·배점은 JLPT 공식 기준. 시험일·접수일은 매년 공식 사이트에서 다시 확인하세요.</span></div></section>';

  h += '<section class="card"><h2>⚙️ 설정</h2>'
     + '<div class="toggles"><label class="tg" style="display:inline-flex;gap:6px;align-items:center">시작일 <input type="date" id="startIn" value="'+START()+'" style="background:transparent;color:inherit;border:0;font:inherit"></label>'
     + '<button class="tg" id="rateBtn">말하기 속도: '+(opts.rate >= 1.15 ? '빠르게(실전)' : opts.rate >= 1 ? '보통' : '느리게')+'</button><button class="tg" data-say="本日はよろしくお願いいたします。">🔊 음성 테스트</button></div>'
     + '<div class="toggles">'+Array.from({length:13},(_,i)=>'<a class="tg" href="#print/'+(i+1)+'" style="text-decoration:none">🖨 '+(i+1)+'월차</a>').join('')+'</div>'
     + '<div class="small muted">음성은 앱에 들어 있는 녹음 파일로 재생돼요. 소리가 안 나면 기기 볼륨을 확인하세요. 진도 기록은 이 기기의 브라우저에만 저장돼요.</div></section>';
  h += '<div class="foot">모든 지문·대화·문제는 학습용으로 새로 쓴 것이며 실제 기출문제가 아닙니다.<br>음성은 음성합성(Open JTalk)이라 실제 시험 음성보다 억양이 단조로워요. 4단계부터는 공식 문제집 음원도 함께 들으세요.</div>';
  $app.innerHTML = h;
  document.getElementById('rateBtn').onclick = () => { opts.rate = opts.rate >= 1.15 ? 0.85 : opts.rate >= 1 ? 1.2 : 1; saveOpts(); viewHome(); };
  document.getElementById('startIn').onchange = e => { if (e.target.value){ store.set('start', e.target.value); toast('시작일: '+e.target.value); viewHome(); } };
}

/* ================= 화면: 하루 공부 ================= */
function quizHTML(Q, i, D){
  const listen = Q.type === '聴解';
  return '<div class="q" data-q="'+i+'"><div class="qq"><span class="chip gr" style="margin-right:6px">'+esc(Q.type)+'</span>Q'+(i+1)+'.</div>'
    + (listen ? '<div style="margin:6px 0 8px"><button class="iconbtn" data-playlines="1">🔊 대화 듣기</button> <span class="small muted">스크립트를 보지 말고 들으세요</span></div>' : '')
    + '<div class="qtext ja">'+esc(Q.q)+'</div>'
    + '<div class="opts">'+Q.choices.map((c,j) => '<button class="opt ja" data-j="'+j+'">'+NUM[j]+' '+esc(c)+'</button>').join('')+'</div><div class="why" hidden>💡 '+esc(Q.why)+'</div></div>';
}
function lineHTML(L, i, kc, sh, d){
  return '<div class="line" data-li="'+i+'"><div class="who">'+avatar(L.who)+esc(L.who)+'</div><div class="body"><div class="jp ja">'+esc(L.ja)+'</div><div class="kana ja">'+esc(L.kana)+'</div><div class="'+kc+'">'+esc(L.ko)+'</div>'
    + (sh ? '<div class="shadow">'+[0,1,2].map(j => '<button data-sh="'+i+'-'+j+'" class="'+(sh[i+'-'+j]?'on':'')+'">'+(j+1)+'회</button>').join('')+'</div>' : '')+'</div>'+sayBtn(L.ja)+'</div>';
}
function viewDay(d){
  if (d === TOTAL) return viewFinal();
  if (isTest(d)) return viewTest(d);
  if (isRev(d)) return viewRevDay(d);
  const D = DAYS[d]; if (!D){ location.hash = ''; return; }
  curName = 'd'+String(d).padStart(3,'0'); prefetch(curName);
  const sh = store.get('shadow-'+d, {});
  const listenDay = D.quiz.some(q => q.type === '聴解');
  let h = '<header class="top"><a class="back" href="#" aria-label="홈">‹</a><div class="spacer"></div>'
        + (d > 1 && hasContent(d-1) ? '<a class="iconbtn" href="#day/'+(d-1)+'" style="text-decoration:none;line-height:40px">‹ 이전</a>' : '')
        + (hasContent(d+1) ? '<a class="iconbtn" href="#day/'+(d+1)+'" style="text-decoration:none;line-height:40px">다음 ›</a>' : '') + '</header>';
  h += '<div class="daytag"><span class="chip">Day '+d+' · '+dateOf(d)+'</span><span class="chip ep">'+monthOf(d)+'개월차 · '+esc(D.part)+'</span><span class="chip gr">'+esc(D.grammar.point)+'</span>'+(isDone(d) ? '<span class="chip" style="color:#4fe3b5">✓ 완료</span>' : '')+'</div>';
  h += '<div class="dtitle">'+esc(D.title)+'</div>';

  h += '<div class="toggles"><button class="tg '+(opts.kana?'on':'')+'" id="tKana">요미가나 '+(opts.kana?'ON':'OFF')+'</button><button class="tg '+(opts.ko?'on':'')+'" id="tKo">해석 '+(opts.ko?'ON':'OFF (눌러서 보기)')+'</button></div>';
  const kc = opts.ko ? 'ko' : 'ko hid';

  h += '<section class="card"><h2><span class="n">1</span> 오늘의 지문 · 読解 <span class="small muted" style="font-weight:400">'+esc(D.topic)+'</span></h2>'
     + '<div class="passage ja">'+esc(D.passage.ja)+'</div>'
     + '<div class="toggles" style="margin:10px 0 0">'+'<button class="tg" data-say="'+esc(D.passage.ja)+'">🔊 지문 듣기</button><span class="small muted" style="align-self:center">'+D.passage.ja.length+'자 · 목표 '+Math.max(1, Math.round(D.passage.ja.length/250))+'분</span></div>'
     + '<details class="reveal"><summary>해석 보기</summary><div class="ko" style="font-size:15px;margin-top:6px">'+esc(D.passage.ko)+'</div></details></section>';

  h += '<section class="card '+(opts.kana?'':'hideKana')+'"><h2><span class="n">2</span> 청해 · 섀도잉 '+(listenDay ? '<span class="small muted" style="font-weight:400">(오늘 퀴즈 ③은 이 대화를 듣고 풀어요)</span>' : '')+'</h2>'
     + '<div class="toggles" style="margin-bottom:4px"><button class="tg on" data-playlines="1">▶ 대화 전체 듣기</button><button class="tg" id="stopBtn">■ 멈춤</button></div>';
  const linesHtml = D.lines.map((L,i) => lineHTML(L, i, kc, sh, d)).join('');
  h += listenDay ? '<details class="reveal"><summary>스크립트 보기 (퀴즈 ③을 푼 다음에!)</summary><div id="lines">'+linesHtml+'</div></details>' : '<div id="lines">'+linesHtml+'</div>';
  h += '<div class="small muted" style="margin-top:8px">듣고 → 한 줄씩 따라 말하고 → 회차 버튼. 익숙해지면 홈 설정에서 속도를 「빠르게(실전)」로.</div></section>';

  h += '<section class="card"><h2><span class="n">3</span> N1 어휘 8 · 눌러서 뒤집기</h2><div class="words">';
  D.words.forEach(w => { h += '<button class="word" data-w="'+esc(w.w)+'"><div class="in"><div class="f"><b>'+esc(w.w)+'</b>'+(opts.kana && w.r !== w.w ? '<span>'+esc(w.r)+'</span>' : '')+'</div><div class="b">'+esc(w.ko)+'<span class="ja">'+esc(w.r)+'</span></div></div></button>'; });
  h += '</div></section>';

  h += '<section class="card '+(opts.kana?'':'hideKana')+'"><h2><span class="n">4</span> 문법 한 컷</h2><div class="gpoint">'+esc(D.grammar.point)+'</div><div class="gform">접속 · '+esc(D.grammar.form)+'</div><div class="gdesc">'+esc(D.grammar.desc)+'</div>';
  D.grammar.ex.forEach(x => { h += '<div class="ex"><div class="body"><div class="jp ja">'+esc(x.ja)+'</div><div class="kana ja">'+esc(x.kana)+'</div><div class="'+kc+'">'+esc(x.ko)+'</div></div>'+sayBtn(x.ja)+'</div>'; });
  h += '</section>';

  const C = D.compare;
  h += '<section class="card"><h2><span class="n">5</span> 헷갈리는 표현 구별</h2><div class="conv">'
     + '<div class="box anime" style="display:flex;gap:10px;align-items:center"><div class="body"><div class="lab">A · '+esc(C.a)+'</div><div class="jp ja" style="font-size:17px">'+esc(C.exA)+'</div></div>'+sayBtn(C.exA)+'</div><div class="arrow">vs</div>'
     + '<div class="box real" style="display:flex;gap:10px;align-items:center"><div class="body"><div class="lab">B · '+esc(C.b)+'</div><div class="jp ja" style="font-size:17px">'+esc(C.exB)+'</div></div>'+sayBtn(C.exB)+'</div>'
     + '<div class="small" style="color:var(--ink2)">'+esc(C.note)+'</div></div></section>';

  h += '<section class="card"><h2><span class="n">6</span> 쓰기·말하기 미션 ✍️</h2><div class="mission">'+esc(D.mission)+'</div>'
     + '<textarea class="note ja" id="note" placeholder="여기에 써 보세요 (이 기기에 자동 저장)">'+esc(store.get('note-'+d, ''))+'</textarea>'
     + '<div class="rec"><button id="recBtn">🎙 소리 내어 녹음</button><button id="playBtn">▶ 내 목소리</button></div>'
     + '<details class="reveal"><summary>모범 답안 보기</summary><div class="ex"><div class="body"><div class="jp ja">'+esc(D.missionEx.ja)+'</div><div class="kana ja">'+esc(D.missionEx.kana)+'</div><div class="ko">'+esc(D.missionEx.ko)+'</div></div>'+sayBtn(D.missionEx.ja)+'</div></details></section>';

  h += '<section class="card"><h2><span class="n">7</span> JLPT형 문제 3</h2><div id="quiz">'+D.quiz.map((Q,i) => quizHTML(Q, i, D)).join('')+'</div></section>';
  h += '<div class="finish"><button class="cta" id="fin" '+(isDone(d)?'':'disabled')+'>'+(isDone(d) ? '✓ 완료한 날 · 홈으로' : '문제 3개를 모두 맞히면 완료할 수 있어요')+'</button></div>';
  $app.innerHTML = h; scrollTo(0,0);

  document.getElementById('tKana').onclick = () => { opts.kana = !opts.kana; saveOpts(); viewDay(d); };
  document.getElementById('tKo').onclick = () => { opts.ko = !opts.ko; saveOpts(); viewDay(d); };
  document.getElementById('stopBtn').onclick = stopAudio;
  $app.querySelectorAll('[data-playlines]').forEach(b => b.onclick = () => {
    const rows = [...$app.querySelectorAll('#lines .line')];
    playSeq(D.lines.map(L => L.ja), b, i => rows.forEach((r,j) => r.classList.toggle('now', j === i)));
  });
  $app.querySelectorAll('[data-sh]').forEach(b => b.onclick = () => { const s = store.get('shadow-'+d, {}); s[b.dataset.sh] = !s[b.dataset.sh]; store.set('shadow-'+d, s); b.classList.toggle('on'); });
  document.getElementById('note').oninput = e => store.set('note-'+d, e.target.value);
  const rb = document.getElementById('recBtn'); rb.onclick = () => toggleRec('day'+d, rb);
  document.getElementById('playBtn').onclick = () => playRec('day'+d);

  const answered = {}; const fin = document.getElementById('fin');
  $app.querySelectorAll('#quiz .q').forEach(qe => {
    const Q = D.quiz[+qe.dataset.q];
    qe.querySelectorAll('.opt').forEach(o => o.onclick = () => {
      if (answered[qe.dataset.q] === true) return;
      const j = +o.dataset.j;
      if (j === Q.a){ o.classList.add('ok'); answered[qe.dataset.q] = true; qe.querySelector('.why').hidden = false; }
      else { o.classList.add('ng'); answered[qe.dataset.q] = answered[qe.dataset.q] || false; }
      const wrong = store.get('wrong', {}); if (j !== Q.a){ wrong[d+'-'+qe.dataset.q] = 1; store.set('wrong', wrong); }
      if (Object.values(answered).filter(v => v).length === D.quiz.length && !isDone(d)){ fin.disabled = false; fin.textContent = '🔥 Day '+d+' 완료하기'; }
    });
  });
  fin.onclick = () => {
    if (!isDone(d)){ markDone(d); addWords(d); toast('Day '+d+' 완료! 어휘 8개가 복습함에 들어갔어요'); }
    location.hash = '';
  };
}

/* ================= 복습·모의 문제 만들기 ================= */
function rangeDays(a, b){ const r = []; for (let i=a; i<=b; i++) if (DAYS[i]) r.push(DAYS[i]); return r; }
function buildQuiz(ds, nWords, nJlpt){
  const words = []; ds.forEach(D => D.words.forEach(w => words.push(w)));
  const qs = [];
  shuffle(words).slice(0, nWords).forEach((w, i) => {
    const asRead = i % 2 === 1 && w.r !== w.w;  // 절반은 읽기, 절반은 뜻
    const pool = words.filter(x => asRead ? x.r !== w.r : x.ko !== w.ko);
    const right = asRead ? w.r : w.ko;
    const ch = shuffle([right].concat(shuffle(pool).slice(0,3).map(x => asRead ? x.r : x.ko)));
    qs.push({type: asRead ? '漢字読み' : '어휘 뜻', q: w.w, say: w.w, choices: ch, a: ch.indexOf(right), word: w.w});
  });
  const jl = []; ds.forEach(D => D.quiz.forEach(Q => { if (Q.type !== '聴解' && Q.type !== '内容理解') jl.push(Object.assign({day: D.day}, Q)); }));
  shuffle(jl).slice(0, nJlpt).forEach(Q => qs.push(Q));
  return shuffle(qs);
}
function quizBlock(qs){
  return qs.map((Q,i) => '<div class="q" data-q="'+i+'"><div class="qq" style="display:flex;gap:10px;align-items:center"><span style="flex:1"><span class="chip gr" style="margin-right:6px">'+esc(Q.type)+'</span>Q'+(i+1)+'.'+(Q.day ? ' <span class="small muted">Day '+Q.day+'</span>' : '')+'</span>'+(Q.say ? sayBtn(Q.say) : '')+'</div>'
    + '<div class="qtext ja" style="'+(Q.word ? 'font-size:24px;font-weight:700' : '')+'">'+esc(Q.q)+'</div>'
    + '<div class="opts">'+Q.choices.map((c,j) => '<button class="opt ja" data-j="'+j+'">'+NUM[j]+' '+esc(c)+'</button>').join('')+'</div>'
    + (Q.why ? '<div class="why" hidden>💡 '+esc(Q.why)+'</div>' : '')+'</div>').join('');
}
function wireQuiz(qs, onAll, onEach){
  let score = 0; const st = {};
  $app.querySelectorAll('.q').forEach(qe => {
    const i = +qe.dataset.q, Q = qs[i]; if (!Q) return;
    qe.querySelectorAll('.opt').forEach(o => o.onclick = () => {
      if (st[i] !== undefined) return;
      const ok = +o.dataset.j === Q.a; st[i] = ok; if (ok) score++;
      o.classList.add(ok ? 'ok' : 'ng'); if (!ok) qe.querySelectorAll('.opt')[Q.a].classList.add('ok');
      const w = qe.querySelector('.why'); if (w) w.hidden = false;
      if (Q.word) grade(Q.word, ok);
      onEach && onEach(Q, ok);
      if (Object.keys(st).length === qs.length) onAll(score, st);
    });
  });
}

/* ================= 화면: 주간 복습일 ================= */
function viewRevDay(d){
  curName = '';
  const ds = rangeDays(d-6, d-1); const qs = buildQuiz(ds, 6, 4);
  let h = '<header class="top"><a class="back" href="#">‹</a><div class="spacer"></div>'+(hasContent(d+1) ? '<a class="iconbtn" href="#day/'+(d+1)+'" style="text-decoration:none;line-height:40px">다음 ›</a>' : '')+'</header>';
  h += '<div class="daytag"><span class="chip">Day '+d+' · '+dateOf(d)+'</span><span class="chip ep">주간 복습</span></div><div class="dtitle">이번 주 정리 · 10문제</div>';
  h += '<section class="card"><h2>📌 이번 주 문법</h2>'+ds.map(D => '<div class="ex"><div class="body"><div class="small muted">Day '+D.day+' · '+esc(D.grammar.form)+'</div><div class="jp ja" style="font-size:17px;color:var(--gold)">'+esc(D.grammar.point)+'</div><div class="ja">'+esc(D.grammar.ex[0].ja)+'</div><div class="ko">'+esc(D.grammar.ex[0].ko)+'</div></div>'+sayBtn(D.grammar.ex[0].ja)+'</div>').join('')+'</section>';
  h += '<section class="card"><h2>📝 복습 퀴즈</h2>'+quizBlock(qs)+'</section>';
  h += '<section class="card"><h2>🎧 이번 주 대화 몰아서 듣기</h2><div class="small muted" style="margin-bottom:6px">대본 없이 먼저 들어 보고, 안 들리는 문장만 눌러서 다시 들으세요.</div>'+ds.map(D => D.lines.map(L => '<div class="ex"><div class="body"><div class="jp ja" style="font-size:16px">'+esc(L.ja)+'</div><div class="ko">'+esc(L.ko)+'</div></div>'+sayBtn(L.ja)+'</div>').join('')).join('')+'</section>';
  h += '<div class="finish"><button class="cta" id="fin" '+(isDone(d)?'':'disabled')+'>'+(isDone(d)?'✓ 완료한 날 · 홈으로':'퀴즈를 다 풀면 완료할 수 있어요')+'</button></div>';
  $app.innerHTML = h; scrollTo(0,0);
  const fin = document.getElementById('fin');
  wireQuiz(qs, s => { fin.disabled = false; fin.textContent = '🔥 '+s+'/'+qs.length+'점 · Day '+d+' 완료하기'; });
  fin.onclick = () => { if (!isDone(d)) markDone(d); location.hash = ''; };
}

/* ================= 화면: 월말 모의 ================= */
function viewTest(d){
  curName = '';
  const ds = rangeDays(d-29, d-1); const qs = buildQuiz(ds, 10, 10);
  const reads = shuffle(ds.filter(D => D.quiz[2] && D.quiz[2].type !== '聴解')).slice(0, 2);
  const listens = shuffle(ds.filter(D => D.quiz[2] && D.quiz[2].type === '聴解')).slice(0, 3);
  let h = '<header class="top"><a class="back" href="#">‹</a></header>';
  h += '<div class="daytag"><span class="chip">Day '+d+' · '+dateOf(d)+'</span><span class="chip gr">월말 모의</span></div><div class="dtitle">'+monthOf(d)+'개월차 승급 시험</div>';
  h += '<section class="card"><h2>① 문자·어휘·문법 20문제</h2>'+quizBlock(qs)+'</section>';
  const extra = [];
  if (reads.length){
    h += '<section class="card"><h2>② 독해 다시 풀기 — 시간 재고 읽기</h2>';
    reads.forEach(D => { const i = qs.length + extra.length; extra.push(D.quiz[2]); h += '<div class="passage ja" style="margin:10px 0">'+esc(D.passage.ja)+'</div>'+quizBlock([D.quiz[2]]).replace('data-q="0"', 'data-q="'+i+'"').replace('Q1.', 'Q'+(i+1)+'.'); });
    h += '</section>';
  }
  if (listens.length){
    h += '<section class="card"><h2>③ 청해 다시 풀기 — 대본 없이</h2>';
    listens.forEach(D => { const i = qs.length + extra.length; extra.push(D.quiz[2]); h += '<div style="margin:10px 0"><button class="iconbtn" data-listen="'+D.day+'">🔊 Day '+D.day+' 대화 듣기</button></div>'+quizBlock([D.quiz[2]]).replace('data-q="0"', 'data-q="'+i+'"').replace('Q1.', 'Q'+(i+1)+'.'); });
    h += '</section>';
  }
  const all = qs.concat(extra);
  h += '<section class="card"><h2>④ 이번 달 틀렸던 문제</h2><div class="small muted">'+wrongList(d-29, d-1)+'</div></section>';
  h += '<div class="finish"><button class="cta" id="fin" '+(isDone(d)?'':'disabled')+'>'+(isDone(d)?'✓ 통과 · 홈으로':'모든 문제를 풀면 완료')+'</button></div>';
  $app.innerHTML = h; scrollTo(0,0);
  $app.querySelectorAll('[data-listen]').forEach(b => b.onclick = () => { const D = DAYS[b.dataset.listen]; curName = 'd'+String(D.day).padStart(3,'0'); playSeq(D.lines.map(L => L.ja), b); });
  const fin = document.getElementById('fin');
  wireQuiz(all, s => { const p = Math.round(s/all.length*100); fin.disabled = false; fin.textContent = (p >= 70 ? '🏆 ' : '💪 ')+s+'/'+all.length+' ('+p+'%) · 완료하기'+(p < 70 ? ' — 70% 미만이면 틀린 날 다시 보기' : ''); });
  fin.onclick = () => { if (!isDone(d)) markDone(d); location.hash = ''; };
}
function wrongList(a, b){
  const w = store.get('wrong', {}); const ds = [...new Set(Object.keys(w).map(k => +k.split('-')[0]).filter(x => x >= a && x <= b))].sort((x,y) => x-y);
  return ds.length ? '처음에 틀렸던 날: '+ds.map(x => '<a href="#day/'+x+'" style="color:var(--blue)">Day '+x+'</a>').join(' · ') : '처음부터 다 맞혔어요. 훌륭해요!';
}

/* ================= 화면: Day 365 졸업 모의고사 ================= */
function viewFinal(){
  curName = 'final'; prefetch('final');
  const F = window.N1_FINAL; const d = TOTAL;
  const SECS = [['言語知識','文字・語彙','文法'],['読解','読解'],['聴解','聴解']];
  let h = '<header class="top"><a class="back" href="#">‹</a></header>';
  h += '<div class="daytag"><span class="chip">Day 365 · '+dateOf(d)+'</span><span class="chip gr">졸업 시험</span></div><div class="dtitle">'+esc(F.title)+'</div>';
  h += '<section class="card"><div class="mission">'+esc(F.intro)+'</div></section>';
  let lastPassage = '';
  h += '<section class="card"><h2>문제</h2>';
  F.qs.forEach((Q,i) => {
    if (i === 0 || F.qs[i-1].sec !== Q.sec) h += '<div class="phase" style="margin-top:18px"><b>'+esc(Q.sec)+'</b></div>';
    if (Q.passage && Q.passage !== lastPassage){ h += '<div class="passage ja" style="margin:10px 0">'+esc(Q.passage)+'</div>'; lastPassage = Q.passage; }
    if (Q.script) h += '<div style="margin:10px 0 0"><button class="iconbtn" data-fs="'+i+'">🔊 '+(i+1)+'번 듣기</button></div>';
    h += quizBlock([Q]).replace('data-q="0"', 'data-q="'+i+'"').replace('Q1.', 'Q'+(i+1)+'.');
  });
  h += '</section><div id="cert"></div>';
  h += '<div class="finish"><button class="cta" id="fin" disabled>'+(isDone(d) ? '30문제를 다시 풀면 성적표가 나와요' : '30문제를 모두 풀면 채점돼요')+'</button></div>';
  $app.innerHTML = h; scrollTo(0,0);
  $app.querySelectorAll('[data-fs]').forEach(b => b.onclick = () => playSeq(F.qs[+b.dataset.fs].script.map(l => l.ja), b));
  const fin = document.getElementById('fin');
  wireQuiz(F.qs, (s, st) => {
    const part = sec => { const idx = F.qs.map((q,i) => [q,i]).filter(([q]) => sec.slice(1).includes(q.sec)); return Math.round(idx.filter(([,i]) => st[i]).length / Math.max(1, idx.length) * 60); };
    const sc = SECS.map(part), tot = sc.reduce((a,b) => a+b, 0), pass = tot >= 100 && sc.every(x => x >= 19);
    fin.disabled = false; fin.textContent = pass ? '🏅 합격권! 성적표 보기' : '💪 성적표 보기';
    fin.onclick = () => {
      if (!isDone(d)) markDone(d);
      document.getElementById('cert').innerHTML = '<section class="hero" style="text-align:center"><span class="rank">⚡ '+(pass ? '免許皆伝' : '再挑戦')+'</span><div class="big">'+tot+' / 180</div><div class="sub">'+(pass ? '합격 기준(100점·각 19점) 통과' : '합격 기준: 총점 100 이상 + 각 구분 19 이상')+'</div>'
        + '<div class="stats">'+SECS.map((s,i) => '<div class="stat"><b>'+sc[i]+'</b><span>'+s[0]+' /60</span></div>').join('')+'</div>'
        + '<p class="sub" style="margin-top:14px">'+(dDay(EXAM) > 0 ? '시험까지 D-'+dDay(EXAM)+'. ' : '')+'점수가 낮은 구분의 월(月)을 다시 돌고, 어휘 복습은 매일 계속하세요.<br>お疲れさまでした。合格を祈っています。</p></section>';
      document.getElementById('cert').scrollIntoView({behavior:'smooth'});
    };
  });
}

/* ================= 화면: 어휘 복습 (SRS) ================= */
function viewReview(){
  curName = '';
  const list = shuffle(dueWords()); let i = 0, ok = 0, back = false;
  function draw(){
    if (i >= list.length){
      $app.innerHTML = '<header class="top"><a class="back" href="#">‹</a><h1>어휘 복습</h1></header><section class="card" style="text-align:center"><div class="dtitle">'+(list.length ? '오늘 복습 끝! '+ok+'/'+list.length : '오늘 복습할 어휘가 없어요')+'</div><p class="muted">맞힌 어휘는 점점 더 긴 간격(1→2→4→8…일)으로, 틀린 어휘는 내일 다시 나와요.</p><a class="cta" href="#">홈으로</a></section>';
      return;
    }
    const w = list[i];
    $app.innerHTML = '<header class="top"><a class="back" href="#">‹</a><h1>어휘 복습<small>'+(i+1)+' / '+list.length+'</small></h1></header>'
      + '<div class="flash" id="fl"><div class="w">'+esc(w.w)+'</div>'+(back ? '<div class="r">'+esc(w.r)+'</div><div class="m">'+esc(w.ko)+'</div><div class="hint">Day '+w.day+'</div>' : '<div class="hint">읽기와 뜻을 떠올린 뒤 눌러서 확인</div>')+'</div>'
      + (back ? '<div class="row2" style="margin-top:14px"><button class="cta alt" id="ng" style="margin:0">✗ 몰랐다</button><button class="cta" id="ok" style="margin:0">○ 알았다</button></div>' : '');
    document.getElementById('fl').onclick = () => { if (!back){ back = true; speak(w.w); draw(); } else speak(w.w); };
    if (back){
      document.getElementById('ok').onclick = () => { grade(w.w, true); ok++; i++; back = false; draw(); };
      document.getElementById('ng').onclick = () => { grade(w.w, false); i++; back = false; draw(); };
    }
  }
  draw();
}

/* ================= 화면: 어휘장 ================= */
function viewWords(){
  curName = '';
  const s = srs(); const W = Object.values(allWords()).filter(w => s[w.w]);
  let h = '<header class="top"><a class="back" href="#">‹</a><h1>내 어휘장<small>배운 어휘 '+W.length+'개 · 전체 '+Object.keys(allWords()).length+'개</small></h1></header>';
  if (!W.length) h += '<section class="card muted">Day를 완료하면 어휘가 여기에 쌓여요.</section>';
  else h += '<section class="card">'+W.map(w => '<div class="ex" data-say="'+esc(w.w)+'" style="cursor:pointer"><div class="body"><span class="jp ja" style="font-size:18px">'+esc(w.w)+'</span> <span class="kana ja">'+esc(w.r)+'</span><div class="ko">'+esc(w.ko)+'</div></div><span class="chip">'+(s[w.w].box >= 4 ? '🟢 암기' : s[w.w].box >= 2 ? '🟡 익숙' : '🔴 학습중')+'</span></div>').join('')+'</section>';
  $app.innerHTML = h;
}

/* ================= 인쇄용 (월별 워크북) ================= */
function viewPrint(m){
  const a = (m-1)*30+1, b = Math.min(m*30, TOTAL), U = UNITS[m-1];
  let h = '<div class="pcover"><div class="kan">合</div><h1>N1 합격노트</h1><p style="font-size:14pt;margin:6mm 0 2mm">'+m+'개월차 워크북 · Day '+a+' ~ '+b+'</p><p style="color:#555">'+dateOf(a)+' ~ '+dateOf(b)+' · '+esc(U[1])+' · '+esc(U[2])+'</p>'
        + '<p style="margin-top:20mm;font-size:10pt;color:#666">모든 지문과 문제는 학습용으로 새로 쓴 것입니다. 앱에서 음성을 들으며 함께 공부하세요.</p></div>';
  for (let d=a; d<=b; d++){
    const D = DAYS[d];
    if (d === TOTAL && window.N1_FINAL){
      const F = window.N1_FINAL;
      h += '<div class="pday pb"><div class="ph"><b>Day 365 · '+esc(F.title)+'</b><span>'+dateOf(d)+'</span></div>'
         + F.qs.map((Q,i) => (Q.passage && (!i || F.qs[i-1].passage !== Q.passage) ? '<div class="pg ja">'+esc(Q.passage)+'</div>' : '')+'<div class="pq"><b>'+(i+1)+'.</b> ['+esc(Q.type)+'] <span class="ja">'+esc(Q.script ? '(청해 — 앱에서 듣기) '+Q.q : Q.q)+'</span><br>'+Q.choices.map((c,j) => NUM[j]+' <span class="ja">'+esc(c)+'</span>').join(' &nbsp; ')+'</div>').join('')
         + '<div class="pans">'+F.qs.map((Q,i) => (i+1)+': '+NUM[Q.a]).join(' &nbsp; ')+'</div></div>';
      continue;
    }
    if (isRev(d) || isTest(d)){
      const test = isTest(d), ds = rangeDays(test ? d-29 : d-6, d-1);
      const ws = []; ds.forEach(X => X.words.forEach(w => ws.push(w)));
      const pick = (arr, n) => arr.filter((_, i) => i % Math.max(1, Math.floor(arr.length / n)) === 0).slice(0, n);
      h += '<div class="pday'+(test ? ' pb' : '')+'"><div class="ph"><b>Day '+d+' · '+(test ? m+'개월차 월말 모의' : '주간 복습')+'</b><span>'+dateOf(d)+'</span></div>';
      h += '<div class="pg">'+ds.map(X => '<div><span class="pt">'+esc(X.grammar.point)+'</span> — <span class="ja">'+esc(X.grammar.ex[0].ja)+'</span></div>').join('')+'</div>';
      h += '<div class="pq"><b>읽기와 뜻 쓰기</b></div><div class="pwords">'+pick(ws, test ? 24 : 12).map(w => '<div><b>'+esc(w.w)+'</b><br>읽기 ______ 뜻 ______</div>').join('')+'</div>';
      h += '<div class="pchk">☐ 앱 '+(test ? '월말 모의 (문자·어휘·문법 + 독해·청해 다시 풀기)' : '복습 퀴즈 10문제 + 대화 몰아서 듣기')+' &nbsp; 점수: ____</div></div>';
      continue;
    }
    if (!D) continue;
    h += '<div class="pday"><div class="ph"><b>Day '+d+' · '+esc(D.title)+'</b><span>'+dateOf(d)+' · '+esc(D.part)+'</span></div>';
    h += '<div class="pg ja" style="background:#fff;border:1px solid #ccc">'+esc(D.passage.ja)+'</div>';
    h += '<div class="pwords">'+D.words.map(w => '<div><b>'+esc(w.w)+'</b> '+esc(w.r)+'<br>'+esc(w.ko)+'</div>').join('')+'</div>';
    h += '<div class="pg"><span class="pt">'+esc(D.grammar.point)+'</span> ('+esc(D.grammar.form)+') — '+esc(D.grammar.desc)+'<br>'+D.grammar.ex.map(x => '<span class="ja">'+esc(x.ja)+'</span>').join(' / ')+'</div>';
    h += '<div class="pq"><b>구별</b> '+esc(D.compare.a)+' vs '+esc(D.compare.b)+' — '+esc(D.compare.note)+'</div>';
    h += '<div class="pq"><b>미션</b> '+esc(D.mission)+'</div><div class="pwrite"></div><div class="pwrite"></div>';
    h += D.quiz.map((Q,i) => '<div class="pq">Q'+(i+1)+'. ['+esc(Q.type)+'] <span class="ja">'+esc(Q.type === '聴解' ? '(앱에서 대화 듣기) '+Q.q : Q.q)+'</span><br>'+Q.choices.map((c,j) => NUM[j]+' <span class="ja">'+esc(c)+'</span>').join(' &nbsp; ')+'</div>').join('');
    h += '<div class="pchk">☐ 지문 정독 &nbsp; ☐ 청해 섀도잉 3회 &nbsp; ☐ 어휘 8 &nbsp; ☐ 미션 &nbsp; ☐ 문제</div></div>';
  }
  h += '<div class="pday pb"><div class="ph"><b>정답</b><span>'+m+'개월차</span></div><div class="pans">'+rangeDays(a,b).map(D => '<div>Day '+D.day+': '+D.quiz.map(Q => NUM[Q.a]).join(' ')+'</div>').join('')+'</div></div>';
  document.getElementById('print').innerHTML = h;
}

/* ================= 라우터 ================= */
function route(){
  stopAudio();
  const h = location.hash.replace(/^#\/?/, '');
  const [v, a] = h.split('/');
  if (v === 'day' && a && hasContent(+a)) viewDay(+a);
  else if (v === 'review') viewReview();
  else if (v === 'words') viewWords();
  else if (v === 'print'){ viewPrint(+a || 1); viewHome(); setTimeout(() => { try{ if (!/headless/i.test(navigator.userAgent)) window.print(); }catch(e){} }, 800); }
  else viewHome();
}
addEventListener('hashchange', route);
route();
if ('serviceWorker' in navigator && location.protocol === 'https:') navigator.serviceWorker.register('sw.js').catch(() => {});
