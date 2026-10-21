<script>
/* 필기: 형광펜(뜻 있는 4색) · 내 답 · 만년필/볼펜 손글씨 · 모아 보기
   저장: 계정 db(data/users/<id>/…)가 되면 기기 간 동기화, 안 되면 이 기기 브라우저에만 */
(function(){
  var COLORS={y:'기억할 문장',p:'나를 찌르는 말씀',b:'붙잡을 약속',g:'모임에 가져갈 질문'};
  var BLOCKS='.text p, .guide p, .qa .q, blockquote, .notes li, .kr, .verse, .cmp td, .steps li';
  var arts=[].slice.call(document.querySelectorAll('article.chap'));
  var byId={}; arts.forEach(function(a){byId[a.id]=a;});

  /* ── 저장소 ───────────────────────────── */
  var mode='local', db=null, uid=null, queue={};
  function lget(k){try{var v=localStorage.getItem('ppnote:'+k);return v?JSON.parse(v):null;}catch(e){return null;}}
  function lset(k,v){try{localStorage.setItem('ppnote:'+k,JSON.stringify(v));}catch(e){}}
  function ref(k){return db.collection('data/users/'+uid).doc(k);}
  function load(k){
    if(mode!=='db') return Promise.resolve(lget(k));
    var timer=new Promise(function(res){setTimeout(function(){res('__timeout');},4000);});
    return Promise.race([ref(k).get(),timer]).then(function(s){if(s==='__timeout'||!s||!s.exists)return null;return s.data();},function(){return null;});
  }
  function save(k,v){
    lset(k,v);
    if(mode!=='db') return;
    var prev=queue[k]||Promise.resolve();
    queue[k]=prev.then(function(){return ref(k).set(v);}).catch(function(e){
      if(e&&e.code==='invalid_argument'){mode='local';showStore();}
    });
  }
  function initStore(){
    if(!window.claude||!window.claude.use) return;
    Promise.all([window.claude.use('db'),window.claude.use('user')]).then(function(r){
      if(!r[0]||!r[1]) return;
      return r[1].id().then(function(id){
        if(!id) return; db=r[0]; uid=id; mode='db'; showStore();
        Object.keys(loaded).forEach(function(c){delete loaded[c];}); // 계정 저장분으로 다시 읽기
        if(current) loadChapter(current);
      });
    }).catch(function(){});
  }

  /* ── 장 데이터 ───────────────────────── */
  var loaded={}, chData={}, current=null;
  function blocksOf(a){return [].slice.call(a.querySelectorAll(BLOCKS)).filter(function(b){return !b.closest('.myans,.mini,.print-cover,.dock');});}
  function key(c){return 'ch-'+c;}
  var SENT=/[.?!…](?:["'”’」』)\]]*)\s+/g;
  function prepSentences(c){ // 문장마다 span.sn으로 감싸 둠(누르면 그 문장을 칠함)
    blocksOf(byId[c]).forEach(function(b){
      if(b.dataset.sn) return; b.dataset.sn='1'; var si=0;
      textNodes(b).forEach(function(t){
        if(t.parentNode.closest&&t.parentNode.closest('.sn')) return;
        var v=t.nodeValue; if(!v.trim()) return;
        var parts=[],last=0,m; SENT.lastIndex=0;
        while((m=SENT.exec(v))){parts.push([v.slice(last,m.index+m[0].length),si]);si++;last=m.index+m[0].length;}
        if(last<v.length) parts.push([v.slice(last),si]);
        var frag=document.createDocumentFragment();
        parts.forEach(function(pp){var sp=document.createElement('span');sp.className='sn';sp.dataset.s=pp[1];sp.textContent=pp[0];frag.appendChild(sp);});
        t.parentNode.replaceChild(frag,t);
      });
    });
  }
  function norm(d){d=d||{};d.hl=d.hl||[];d.ans=d.ans||{};return d;}
  function loadChapter(c){
    if(loaded[c]) return loaded[c];
    if(!chData[c]){prepSentences(c); chData[c]=norm(lget(key(c))); renderHL(c); renderAns(c); loadInk(c);}
    loaded[c]=Promise.resolve(chData[c]);
    if(mode==='db') load(key(c)).then(function(r){
      if(!r) return; r=norm(r); var d=chData[c], have={};
      d.hl.forEach(function(h){have[h.id]=1;});
      r.hl.forEach(function(h){if(!have[h.id]&&!(d.del&&d.del[h.id]))d.hl.push(h);});
      Object.keys(r.ans).forEach(function(q){if(!d.ans[q])d.ans[q]=r.ans[q];});
      renderHL(c); renderAns(c); lset(key(c),d);
    });
    return loaded[c];
  }
  function persist(c){save(key(c),chData[c]);}

  /* ── 형광펜 ───────────────────────────── */
  function textNodes(el){var w=document.createTreeWalker(el,NodeFilter.SHOW_TEXT,null),n,out=[];while((n=w.nextNode()))out.push(n);return out;}
  function wrap(block,s,e,c,hid){
    var pos=0;
    textNodes(block).forEach(function(t){
      var L=t.nodeValue.length,a=Math.max(s,pos),b=Math.min(e,pos+L);
      if(b>a){
        var mid=t; if(a>pos) mid=t.splitText(a-pos); if(b<pos+L) mid.splitText(b-a);
        var m=document.createElement('mark'); m.className='hl hl-'+c; m.dataset.hid=hid;
        mid.parentNode.insertBefore(m,mid); m.appendChild(mid);
      }
      pos+=L;
    });
  }
  function unwrapAll(block){[].slice.call(block.querySelectorAll('mark.hl')).forEach(function(m){var p=m.parentNode;while(m.firstChild)p.insertBefore(m.firstChild,m);p.removeChild(m);p.normalize();});}
  function renderHL(c){
    var a=byId[c], bl=blocksOf(a), d=chData[c];
    bl.forEach(function(b){if(b.querySelector('mark.hl'))unwrapAll(b);});
    d.hl.forEach(function(h){var b=bl[h.k];if(b)wrap(b,h.s,h.e,h.c,h.id);});
  }
  function offsetIn(block,node,off){var r=document.createRange();r.setStart(block,0);r.setEnd(node,off);return r.toString().length;}
  var lastRange=null,lastAt=0,touching=false,autoT=null,hlDrag=null;
  function inArticle(n){n=n&&(n.nodeType===1?n:n.parentNode);return n&&n.closest&&n.closest('article.chap');}
  document.addEventListener('selectionchange',function(){
    var sel=window.getSelection(); if(!sel||sel.isCollapsed||!sel.rangeCount) return;
    var r=sel.getRangeAt(0); if(!inArticle(r.commonAncestorContainer)) return;
    lastRange=r.cloneRange(); lastAt=Date.now();
    if(tool==='hl'&&!hlDrag){clearTimeout(autoT);autoT=setTimeout(function(){applyColor(hlColor);},1100);}
  });
  document.addEventListener('touchstart',function(){touching=true;},{passive:true,capture:true});
  document.addEventListener('touchend',function(){touching=false;},{passive:true,capture:true});
  document.addEventListener('touchcancel',function(){touching=false;},{passive:true,capture:true});
  function applyColor(c){
    var sel=window.getSelection(), rg=null;
    if(sel&&!sel.isCollapsed&&sel.rangeCount&&inArticle(sel.getRangeAt(0).commonAncestorContainer)) rg=sel.getRangeAt(0).cloneRange();
    else if(lastRange&&Date.now()-lastAt<20000) rg=lastRange;
    if(!rg||rg.collapsed) return false;
    lastRange=null; clearTimeout(autoT);
    var a=(rg.commonAncestorContainer.nodeType===1?rg.commonAncestorContainer:rg.commonAncestorContainer.parentNode).closest('article.chap');
    if(!a) return false;
    var ch=a.id; loadChapter(ch).then(function(){
      var bl=blocksOf(a), d=chData[ch], added=[];
      bl.forEach(function(b,k){
        if(!rg.intersectsNode(b)) return;
        var s=b.contains(rg.startContainer)?offsetIn(b,rg.startContainer,rg.startOffset):0;
        var e=b.contains(rg.endContainer)?offsetIn(b,rg.endContainer,rg.endOffset):b.textContent.length;
        if(e-s<1) return;
        var h={id:'h'+Date.now().toString(36)+k,k:k,s:s,e:e,c:c,t:b.textContent.slice(s,e).trim().slice(0,240)};
        d.hl.push(h); added.push(h.id);
      });
      if(!added.length) return;
      undo.push({type:'hl',ch:ch,ids:added});
      try{window.getSelection().removeAllRanges();}catch(e){} renderHL(ch); persist(ch);
    });
    return true;
  }
  /* 형광펜으로 톡: 문장 모드 → 그 문장 전체, 용어 모드 → 그 장의 같은 용어 전부. 이미 칠한 곳을 톡 → 지움 */
  var hlMode='s'; try{hlMode=localStorage.getItem('ppnote-hm')==='w'?'w':'s';}catch(e){}
  var WORD=/[가-힣A-Za-z0-9·%]+/g, JOSA=/(에서는|으로는|에서|으로|부터|까지|에게|처럼|보다|이나|이란|이다|이며|이고|하는|하고|하면|해야|에는|과는|와는|은|는|이|가|을|를|의|에|로|과|와|도|만|란)$/;
  function inRect(x,y,el,pad){var rs=el.getClientRects();for(var q=0;q<rs.length;q++){var r=rs[q];if(x>=r.left-pad&&x<=r.right+pad&&y>=r.top-pad&&y<=r.bottom+pad)return true;}return false;}
  function snAt(root,x,y){var ss=root.querySelectorAll('.sn');for(var i=0;i<ss.length;i++){if(inRect(x,y,ss[i],2))return ss[i];}return null;}
  function wordAt(sp,x,y){ // 좌표 아래 낱말(Range 사각형으로 찾음, caret API 안 씀)
    var ts=textNodes(sp),best=null,bd=1e9;
    ts.forEach(function(t){var v=t.nodeValue,m;WORD.lastIndex=0;
      while((m=WORD.exec(v))){var r=document.createRange();r.setStart(t,m.index);r.setEnd(t,m.index+m[0].length);
        var rs=r.getClientRects();for(var q=0;q<rs.length;q++){var b=rs[q];
          var dx=x<b.left?b.left-x:(x>b.right?x-b.right:0),dy=y<b.top?b.top-y:(y>b.bottom?y-b.bottom:0),dd=dx+dy*2;
          if(dd<bd){bd=dd;best=m[0];}}}});
    return bd<14?best:null;
  }
  function stem(w,all){ // 조사를 떼되, 뗀 말이 장 안에서 더 자주 나올 때만("공제한도"→"공제한" 방지)
    function cnt(x){return all.split(x).length-1;}
    var t=w;for(var n=0;n<2;n++){var u=t.replace(JOSA,'');if(u.length>=2&&u!==t&&cnt(u)>cnt(t))t=u;else break;}return t;}
  function blockIdx(bl,n){for(var i=0;i<bl.length;i++){if(bl[i].contains(n))return i;}return -1;}
  function tapHL(a,x,y,sp){
    var ch=a.id; loadChapter(ch); var d=chData[ch], bl=blocksOf(a);
    var ms=a.querySelectorAll('mark.hl'); for(var m=0;m<ms.length;m++){if(inRect(x,y,ms[m],1)){removeHL(ch,ms[m].dataset.hid);return true;}}
    sp=sp||snAt(a,x,y); if(!sp) return false;
    var k=blockIdx(bl,sp); if(k<0) return false;
    var added=[], gid='g'+Date.now().toString(36);
    function free(kk,s,e){return !d.hl.some(function(h){return h.k===kk&&h.s<e&&h.e>s;});}
    if(hlMode==='w'){
      var w=wordAt(sp,x,y); if(!w) return false; var term=stem(w,bl.map(function(b){return b.textContent;}).join('\n'));
      bl.forEach(function(b,kk){
        if(bl.some(function(o){return o!==b&&o.contains(b);})) return; // 겹친 블록(li 안의 p 등)은 바깥 것만
        var t=b.textContent,i=0;
        while((i=t.indexOf(term,i))>=0){if(free(kk,i,i+term.length)){var h={id:gid+'_'+added.length,k:kk,s:i,e:i+term.length,c:hlColor,t:term,g:gid};d.hl.push(h);added.push(h.id);}i+=term.length;}
      });
    } else {
      var b=bl[k], same=[].filter.call(b.querySelectorAll('.sn'),function(x){return x.dataset.s===sp.dataset.s;});
      var r=document.createRange(); r.setStartBefore(same[0]); r.setEndAfter(same[same.length-1]);
      var pre=document.createRange(); pre.setStart(b,0); pre.setEnd(r.startContainer,r.startOffset);
      var st=pre.toString().length, en=st+r.toString().length, txt=b.textContent;
      var hit=d.hl.filter(function(h){return h.k===k&&h.s<en&&h.e>st;})[0];
      if(hit){removeHL(ch,hit.id);return true;}
      while(en>st&&/\s/.test(txt[en-1]))en--;
      var h={id:'h'+Date.now().toString(36)+k,k:k,s:st,e:en,c:hlColor,t:txt.slice(st,en).trim().slice(0,240)};
      d.hl.push(h); added.push(h.id);
    }
    if(!added.length) return false;
    undo.push({type:'hl',ch:ch,ids:added}); renderHL(ch); persist(ch); return true;
  }
  document.addEventListener('click',function(e){ // 손글씨 층이 없는 곳(마우스·손가락 클릭)
    if(tool!=='hl') return;
    var sp=e.target.closest&&e.target.closest('.sn'); if(!sp) return;
    var a=sp.closest('article.chap'); if(!a) return;
    e.preventDefault(); e.stopPropagation(); tapHL(a,e.clientX,e.clientY,sp);
  },true);
  function removeHL(ch,hid){ // 용어 묶음(g)은 한꺼번에 지움
    var d=chData[ch];d.del=d.del||{};var h=d.hl.filter(function(x){return x.id===hid;})[0];if(!h)return;
    var gone=d.hl.filter(function(x){return x.id===hid||(h.g&&x.g===h.g);});
    gone.forEach(function(x){d.del[x.id]=1;});
    d.hl=d.hl.filter(function(x){return gone.indexOf(x)<0;});undo.push({type:'unhl',ch:ch,hs:gone});renderHL(ch);persist(ch);
  }
  document.addEventListener('click',function(e){
    if(!document.body.classList.contains('tool-eraser')) return;
    var m=e.target.closest&&e.target.closest('mark.hl'); if(!m) return;
    e.preventDefault(); removeHL(m.closest('article.chap').id,m.dataset.hid);
  });

  /* ── 내 답 ───────────────────────────── */
  function renderAns(c){
    var a=byId[c], d=chData[c];
    [].slice.call(a.querySelectorAll('.qa > div')).forEach(function(q,i){
      var qid='q'+i, box=q.querySelector(':scope > .myans');
      if(!box){
        box=document.createElement('div'); box.className='myans';
        var b=document.createElement('button'); b.type='button'; b.textContent='✎ 내 답 쓰기';
        var ta=document.createElement('textarea'); ta.hidden=true; ta.id='ans-'+c+'-'+qid; ta.setAttribute('aria-label','내 답');
        ta.placeholder='먼저 스스로 답해 보세요. 그다음 아래 해설을 읽습니다.';
        var st=document.createElement('span'); st.className='saved';
        b.addEventListener('click',function(){ta.hidden=!ta.hidden; if(!ta.hidden) ta.focus();});
        var t; ta.addEventListener('input',function(){
          clearTimeout(t); st.textContent='…';
          t=setTimeout(function(){var v=ta.value.trim(); if(v) d.ans[qid]={t:v,q:(q.querySelector('.q')||{}).textContent||''}; else delete d.ans[qid];
            box.classList.toggle('has',!!v); persist(c); st.textContent='저장됨';},700);
        });
        b.appendChild(st); box.appendChild(b); box.appendChild(ta);
        var qq=q.querySelector('.q'); if(qq) qq.insertAdjacentElement('afterend',box); else q.appendChild(box);
      }
      var ta2=box.querySelector('textarea'), v=d.ans[qid];
      if(v){ta2.value=v.t; ta2.hidden=false; box.classList.add('has');}
    });
  }

  /* ── 손글씨 (만년필 · 볼펜) ─────────────── */
  var NS='http://www.w3.org/2000/svg', inkData={}, inkLoaded={}, inkTimers={};
  function inkKey(c,sid){return 'ink-'+c+'-'+sid;}
  function sections(c){return [].slice.call(byId[c].querySelectorAll('section.page'));}
  function sid(sec){return sec.id.split('-').slice(1).join('-')||'x';}
  function overlay(sec){
    var svg=sec.querySelector(':scope > svg.ink');
    if(!svg){svg=document.createElementNS(NS,'svg');svg.setAttribute('class','ink');svg.setAttribute('aria-hidden','true');sec.appendChild(svg);bindPen(svg,sec);}
    var w=sec.clientWidth||1,h=sec.clientHeight||1; svg.setAttribute('viewBox','0 0 1000 '+(1000*h/w).toFixed(1));
    return svg;
  }
  function loadInk(c){
    if(inkLoaded[c]) return; inkLoaded[c]=true;
    sections(c).forEach(function(sec){
      var k=inkKey(c,sid(sec));
      load(k).then(function(d){inkData[k]=(d&&d.s)||[]; if(inkData[k].length) drawAll(sec,c);});
    });
  }
  function drawAll(sec,c){
    var svg=overlay(sec),k=inkKey(c,sid(sec));
    while(svg.firstChild) svg.removeChild(svg.firstChild);
    (inkData[k]||[]).forEach(function(st,i){svg.appendChild(pathFor(st,i));});
  }
  function mid(a,b){return [(a[0]+b[0])/2,(a[1]+b[1])/2];}
  function smoothD(pts){
    if(pts.length<2) return 'M'+pts[0][0]+' '+pts[0][1]+'l.1 0';
    var d='M'+pts[0][0].toFixed(1)+' '+pts[0][1].toFixed(1);
    for(var i=1;i<pts.length-1;i++){var m=mid(pts[i],pts[i+1]);d+='Q'+pts[i][0].toFixed(1)+' '+pts[i][1].toFixed(1)+' '+m[0].toFixed(1)+' '+m[1].toFixed(1);}
    var l=pts[pts.length-1]; return d+'L'+l[0].toFixed(1)+' '+l[1].toFixed(1);
  }
  function outlineD(pts){ // 만년필: 점마다 굵기가 다른 윤곽을 채워 그림
    if(pts.length<2){var p=pts[0],r=Math.max(p[2]/2,.6);return 'M'+(p[0]-r)+' '+p[1]+'a'+r+' '+r+' 0 1 0 '+(2*r)+' 0a'+r+' '+r+' 0 1 0 '+(-2*r)+' 0';}
    var L=[],R=[];
    for(var i=0;i<pts.length;i++){
      var a=pts[Math.max(0,i-1)],b=pts[Math.min(pts.length-1,i+1)],dx=b[0]-a[0],dy=b[1]-a[1],len=Math.hypot(dx,dy)||1,nx=-dy/len,ny=dx/len,h=pts[i][2]/2;
      L.push([pts[i][0]+nx*h,pts[i][1]+ny*h]); R.push([pts[i][0]-nx*h,pts[i][1]-ny*h]);
    }
    var d=smoothD(L).replace(/^M/,'M'); var rr=R.reverse();
    d+='L'+rr[0][0].toFixed(1)+' '+rr[0][1].toFixed(1)+smoothD(rr).replace(/^M[^QL]*/,'');
    return d+'Z';
  }
  function pathFor(st,i){
    var p=document.createElementNS(NS,'path');
    p.setAttribute('class',st.t==='m'?'mk m'+st.c:(st.t==='f'?'foun ':'ball ')+'i'+st.c);
    p.setAttribute('d',st.t==='f'?outlineD(st.p):smoothD(st.p));
    if(st.t!=='f') p.setAttribute('stroke-width',st.w);
    p.dataset.i=i; return p;
  }
  var tool=null, ink='1', size=1, nib=-0.7, msize=1, MSIZE=[16,24,32]; // 펜촉 각도(라디안), 형광펜 굵기
  function bindPen(svg,sec){
    var cur=null,live=null,last=null,lastT=0,wPrev=0;
    function pt(e){var r=svg.getBoundingClientRect();var s=1000/r.width;return [(e.clientX-r.left)*s,(e.clientY-r.top)*s];}
    svg.addEventListener('touchstart',function(e){ // 펜슬로만: 펜슬 터치일 때만 스크롤을 막음
      if(!document.body.classList.contains('pencil-only')) return;
      for(var i=0;i<e.touches.length;i++) if(e.touches[i].touchType==='stylus'){e.preventDefault();return;}
    },{passive:false});
    function eraseAt(e){ // 지우개: 누른 자리 근처의 손글씨 획과 그 아래 형광펜을 지움
      var c=sec.closest('article.chap').id,k=inkKey(c,sid(sec)),p=pt(e),arr=inkData[k]||[],hit=false;
      function segD(q,a1,b1){var dx=b1[0]-a1[0],dy=b1[1]-a1[1],L=dx*dx+dy*dy,t=L?Math.max(0,Math.min(1,((q[0]-a1[0])*dx+(q[1]-a1[1])*dy)/L)):0;return Math.hypot(q[0]-a1[0]-t*dx,q[1]-a1[1]-t*dy);}
      for(var i=arr.length-1;i>=0;i--){var st=arr[i],R=20+(st.t==='f'?4:(st.w||4)/2),pts=st.p,near=false;
        if(pts.length===1) near=Math.hypot(pts[0][0]-p[0],pts[0][1]-p[1])<R;
        for(var j=1;j<pts.length&&!near;j++){if(segD(p,pts[j-1],pts[j])<R)near=true;}
        if(near){arr.splice(i,1);undo.push({type:'unink',k:k,sec:sec,c:c,st:st,i:i});hit=true;}}
      if(hit){drawAll(sec,c);saveInk(k);return;}
      var ms=sec.querySelectorAll('mark.hl');
      for(var m=0;m<ms.length;m++){var rs=ms[m].getClientRects();for(var q=0;q<rs.length;q++){var rr=rs[q];
        if(e.clientX>=rr.left-4&&e.clientX<=rr.right+4&&e.clientY>=rr.top-4&&e.clientY<=rr.bottom+4){removeHL(c,ms[m].dataset.hid);return;}}}
    }
    var erasing=false, holdT=null, holdP=null, lastRaw=null;
    function lineTo(endP){ // 시작점에서 지금 위치까지 반듯한 직선으로 바꿈
      var a=cur.p[0], b=[endP[0],endP[1]];
      if(cur.t==='m'&&Math.abs(b[1]-a[1])<18) b[1]=a[1]; // 형광펜은 줄과 수평이면 수평으로
      if(cur.t==='f'){
        var ws=cur.straightW, n=14, out=[];
        for(var i=0;i<=n;i++){var t=i/n, tw=Math.min(1,Math.min(i,n-i)/3+0.45);out.push([+(a[0]+(b[0]-a[0])*t).toFixed(1),+(a[1]+(b[1]-a[1])*t).toFixed(1),+(ws*tw).toFixed(2)]);}
        cur.p=out;
      } else cur.p=[[a[0],a[1]],[+b[0].toFixed(1),+b[1].toFixed(1)]];
      live.setAttribute('d',cur.t==='f'?outlineD(cur.p):smoothD(cur.p));
    }
    function snapStraight(){
      if(!cur||cur.straight||!lastRaw) return;
      var a=cur.p[0]; if(Math.hypot(lastRaw[0]-a[0],lastRaw[1]-a[1])<20) return;
      if(cur.t==='f'){var sum=0,c2=0;cur.p.forEach(function(q){if(q[2]>0.8){sum+=q[2];c2++;}});cur.straightW=c2?sum/c2:2.5;}
      cur.straight=true; lineTo(lastRaw);
    }
    function caretAt(x,y){
      svg.style.pointerEvents='none';
      var r=null;
      try{
        if(document.caretRangeFromPoint) r=document.caretRangeFromPoint(x,y);
        else if(document.caretPositionFromPoint){var cp=document.caretPositionFromPoint(x,y);if(cp){r=document.createRange();r.setStart(cp.offsetNode,cp.offset);}}
      }catch(err){}
      svg.style.pointerEvents='';
      return r&&inArticle(r.startContainer)?r:null;
    }
    function dragRange(){
      var a=hlDrag.a,b=hlDrag.b||hlDrag.a,r=document.createRange();
      if(a.compareBoundaryPoints(Range.START_TO_START,b)<=0){r.setStart(a.startContainer,a.startOffset);r.setEnd(b.startContainer,b.startOffset);}
      else{r.setStart(b.startContainer,b.startOffset);r.setEnd(a.startContainer,a.startOffset);}
      return r;
    }
    svg.addEventListener('pointerdown',function(e){
      erasing=false; clearTimeout(holdT);
      if(tool==='eraser'){if(document.body.classList.contains('pencil-only')&&e.pointerType==='touch')return;e.preventDefault();try{svg.setPointerCapture(e.pointerId);}catch(err){}erasing=true;eraseAt(e);return;}
      if(tool!=='pen'&&tool!=='ball'&&tool!=='hl') return;
      if(document.body.classList.contains('pencil-only')&&e.pointerType==='touch') return;
      e.preventDefault(); try{svg.setPointerCapture(e.pointerId);}catch(err){} overlay(sec);
      var p=pt(e), pr=e.pressure||0.5;
      cur=tool==='hl'?{t:'m',c:hlColor,w:MSIZE[msize],p:[]}:{t:tool==='pen'?'f':'b',c:ink,w:tool==='pen'?0:(1.6+size*1.2),p:[]}; last=p; lastT=e.timeStamp; wPrev=0;
      if(cur.t==='f') cur.p.push([+p[0].toFixed(1),+p[1].toFixed(1),0.6]); else cur.p.push([+p[0].toFixed(1),+p[1].toFixed(1)]);
      live=pathFor(cur,-1); svg.appendChild(live); lastRaw=p; holdP=p;
    });
    svg.addEventListener('pointermove',function(e){
      if(erasing){if(tool!=='eraser'||e.buttons===0){erasing=false;}else{eraseAt(e);return;}}
      if(hlDrag){
        if(e.pointerType!=='touch'&&e.buttons===0){finishHL();return;}
        hlDrag.pts.push([e.clientX,e.clientY]); flashAt(e.clientX,e.clientY);
        return;
      }
      if(!cur) return; if(document.body.classList.contains('pencil-only')&&e.pointerType==='touch') return;
      if(e.pointerType!=='touch'&&e.buttons===0){end();return;}
      lastRaw=pt(e);
      if(cur.straight){lineTo(lastRaw);return;}
      if(!holdP||Math.hypot(lastRaw[0]-holdP[0],lastRaw[1]-holdP[1])>4){holdP=lastRaw;clearTimeout(holdT);holdT=setTimeout(snapStraight,500);}
      var evs=e.getCoalescedEvents?e.getCoalescedEvents():[e]; if(!evs.length) evs=[e];
      evs.forEach(function(ev){
        if(ev.pointerType==='pen'&&ev.pressure===0) return;
        var raw=pt(ev), k=0.42; // 손떨림 보정: 이전 점 쪽으로 끌어당김
        var p=[last[0]+(raw[0]-last[0])*k,last[1]+(raw[1]-last[1])*(cur.t==='m'?0.12:k)]; // 형광펜은 줄을 따라 반듯하게
        var dx=p[0]-last[0],dy=p[1]-last[1],dist=Math.hypot(dx,dy); if(dist<0.6) return;
        if(cur.t==='f'){
          var dt=Math.max(1,ev.timeStamp-lastT),v=dist/dt,pr=ev.pressure||0.5;
          var dir=0.28+0.72*Math.abs(Math.sin(Math.atan2(dy,dx)-nib));   // 펜촉 방향에 따라 굵고 가늘게
          var target=(2.6+size*1.6)*dir*(0.6+0.8*pr)*Math.max(0.55,Math.min(1.15,1.2-v*0.35));
          var w=wPrev?wPrev+(target-wPrev)*0.3:target*0.5; wPrev=w;
          var n=cur.p.length; if(n<4) w*=0.55+0.15*n; // 시작은 가늘게
          cur.p.push([+p[0].toFixed(1),+p[1].toFixed(1),+w.toFixed(2)]);
        } else cur.p.push([+p[0].toFixed(1),+p[1].toFixed(1)]);
        last=p; lastT=ev.timeStamp;
      });
      live.setAttribute('d',cur.t==='f'?outlineD(cur.p):smoothD(cur.p));
    });
    function spansAt(x,y){ // 좌표로 그 자리의 문장 조각 찾기(클릭·선택·caret API 없이)
      var out=[],ss=sec.querySelectorAll('.sn');
      for(var i=0;i<ss.length;i++){var rs=ss[i].getClientRects();
        for(var j=0;j<rs.length;j++){var r=rs[j];if(x>=r.left-2&&x<=r.right+2&&y>=r.top-3&&y<=r.bottom+3){out.push(ss[i]);break;}}}
      return out;
    }
    function flashAt(x,y){spansAt(x,y).forEach(function(sp){sp.classList.add('flash');});}
    function finishHL(){
      if(!hlDrag) return; var pts=hlDrag.pts; hlDrag=null;
      [].forEach.call(sec.querySelectorAll('.sn.flash'),function(x){x.classList.remove('flash');});
      var a=sec.closest('article.chap'), ch=a.id, bl=blocksOf(a); loadChapter(ch); var d=chData[ch];
      var groups={}, order=[];
      pts.forEach(function(p){spansAt(p[0],p[1]).forEach(function(sp){
        for(var k=0;k<bl.length;k++){if(bl[k].contains(sp)){var g=k+':'+sp.dataset.s;if(!groups[g]){groups[g]={k:k,s:sp.dataset.s};order.push(g);}break;}}
      });});
      if(!order.length) return;
      var tap=pts.length<4, added=[];
      order.forEach(function(g){
        var k=groups[g].k,b=bl[k],same=[].filter.call(b.querySelectorAll('.sn'),function(x){return x.dataset.s===groups[g].s;});
        var r=document.createRange();r.setStartBefore(same[0]);r.setEndAfter(same[same.length-1]);
        var pre=document.createRange();pre.setStart(b,0);pre.setEnd(r.startContainer,r.startOffset);
        var st=pre.toString().length,en=st+r.toString().length,txt=b.textContent;
        var hit=d.hl.filter(function(h){return h.k===k&&h.s<en&&h.e>st;})[0];
        if(hit){if(tap) removeHL(ch,hit.id); return;}
        while(en>st&&/\s/.test(txt[en-1]))en--;
        var h={id:'h'+Date.now().toString(36)+k+'_'+added.length,k:k,s:st,e:en,c:hlColor,t:txt.slice(st,en).trim().slice(0,240)};
        d.hl.push(h); added.push(h.id);
      });
      if(added.length){undo.push({type:'hl',ch:ch,ids:added}); renderHL(ch); persist(ch);}
    }
    function end(){
      clearTimeout(holdT);
      if(hlDrag){finishHL();return;}
      erasing=false;
      if(!cur) return;
      delete cur.straightW; var wasStraight=cur.straight; delete cur.straight;
      if(cur.t==='f'&&cur.p.length>3&&!wasStraight){ // 끝은 가늘게 빠지도록
        var n=cur.p.length; for(var j=1;j<=3;j++){cur.p[n-j][2]=+(cur.p[n-j][2]*(0.45+0.15*(j-1))).toFixed(2);}
      }
      if(cur.t==='m'&&!wasStraight){ // 거의 안 움직인 형광펜 = 톡 → 문장/용어 칠하기
        var p0=cur.p[0],ext=0;cur.p.forEach(function(q){ext=Math.max(ext,Math.hypot(q[0]-p0[0],q[1]-p0[1]));});
        if(ext<14){var rr=svg.getBoundingClientRect(),sc=rr.width/1000,X=rr.left+p0[0]*sc,Y=rr.top+p0[1]*sc;
          if(live&&live.parentNode)live.parentNode.removeChild(live);cur=null;live=null;tapHL(sec.closest('article.chap'),X,Y);return;}
      }
      var c=sec.closest('article.chap').id,k=inkKey(c,sid(sec));
      if(cur.t==='m'){var seen={},tx=[];cur.p.forEach(function(q){var r=svg.getBoundingClientRect(),sc=r.width/1000;spansAt(r.left+q[0]*sc,r.top+q[1]*sc).forEach(function(sp){var key2=sp.dataset.s+'|'+sp.parentNode.textContent.length;if(!seen[key2]){seen[key2]=1;tx.push(sp.textContent.trim());}});});cur.tx=tx.join(' ').slice(0,240);cur.id='m'+Date.now().toString(36);}
      (inkData[k]=inkData[k]||[]).push(cur); undo.push({type:'ink',k:k,sec:sec,c:c});
      cur=null; live=null; drawAll(sec,c); saveInk(k);
    }
    svg.addEventListener('pointerup',end); svg.addEventListener('pointercancel',end);
  }
  function saveInk(k){clearTimeout(inkTimers[k]);inkTimers[k]=setTimeout(function(){save(k,{s:inkData[k]});},900);}
  window.addEventListener('resize',function(){document.querySelectorAll('svg.ink').forEach(function(s){var sec=s.parentNode;var w=sec.clientWidth||1,h=sec.clientHeight||1;s.setAttribute('viewBox','0 0 1000 '+(1000*h/w).toFixed(1));});});

  /* ── 되돌리기 ─────────────────────────── */
  var undo=[];
  function doUndo(){
    var u=undo.pop(); if(!u) return;
    if(u.type==='hl'){var d=chData[u.ch];d.hl=d.hl.filter(function(h){return u.ids.indexOf(h.id)<0;});renderHL(u.ch);persist(u.ch);}
    if(u.type==='unhl'){var dd=chData[u.ch];(u.hs||[u.h]).forEach(function(h){dd.hl.push(h);if(dd.del)delete dd.del[h.id];});renderHL(u.ch);persist(u.ch);}
    if(u.type==='ink'){inkData[u.k].pop();drawAll(u.sec,u.c);saveInk(u.k);}
    if(u.type==='unink'){inkData[u.k].splice(u.i,0,u.st);drawAll(u.sec,u.c);saveInk(u.k);}
  }

  /* ── 도구 창 ──────────────────────────── */
  var I={
    hl:'<svg viewBox="0 0 24 24"><path d="M4 20h7"/><path d="M14.5 4.5l5 5L10 19H5v-5z"/><path d="M12 7l5 5"/></svg>',
    pen:'<svg viewBox="0 0 24 24"><path d="M12 3c3 3 5 6 5 9l-5 9-5-9c0-3 2-6 5-9z"/><path d="M12 12v4"/><circle cx="12" cy="11" r="1"/></svg>',
    ball:'<svg viewBox="0 0 24 24"><path d="M16 3l5 5L9 20l-6 1 1-6z"/><path d="M14 5l5 5"/></svg>',
    er:'<svg viewBox="0 0 24 24"><path d="M8 20h12"/><path d="M4 15l9-9 6 6-7 7H8z"/><path d="M9 10l6 6"/></svg>',
    undo:'<svg viewBox="0 0 24 24"><path d="M9 14L4 9l5-5"/><path d="M4 9h11a5 5 0 010 10h-3"/></svg>',
    list:'<svg viewBox="0 0 24 24"><path d="M9 6h11M9 12h11M9 18h11"/><circle cx="4.5" cy="6" r="1"/><circle cx="4.5" cy="12" r="1"/><circle cx="4.5" cy="18" r="1"/></svg>',
    min:'<svg viewBox="0 0 24 24"><path d="M6 9l6 6 6-6"/></svg>'
  };
  var dock=document.createElement('div'); dock.className='dock'; dock.hidden=true; dock.setAttribute('role','toolbar'); dock.setAttribute('aria-label','필기 도구');
  dock.innerHTML='<div class="row">'+
    '<button type="button" class="grip" data-a="grip" title="끌어서 옮기기" aria-label="도구 창 옮기기"><svg viewBox="0 0 24 24"><circle cx="9" cy="6" r="1.3"/><circle cx="15" cy="6" r="1.3"/><circle cx="9" cy="12" r="1.3"/><circle cx="15" cy="12" r="1.3"/><circle cx="9" cy="18" r="1.3"/><circle cx="15" cy="18" r="1.3"/></svg></button>'+
    '<button type="button" data-t="hl" aria-pressed="false" title="형광펜">'+I.hl+'</button>'+
    '<button type="button" data-t="pen" aria-pressed="false" title="만년필">'+I.pen+'</button>'+
    '<button type="button" data-t="ball" aria-pressed="false" title="볼펜">'+I.ball+'</button>'+
    '<button type="button" data-t="eraser" aria-pressed="false" title="지우개">'+I.er+'</button><span class="sep"></span>'+
    '<button type="button" data-a="undo" title="되돌리기">'+I.undo+'</button>'+
    
    '<button type="button" class="zt" data-a="zo" title="글자 작게" aria-label="글자 작게">가−</button><button type="button" class="zt" data-a="zi" title="글자 크게" aria-label="글자 크게">가+</button>'+
    '<button type="button" data-a="min" title="접기" aria-expanded="true">'+I.min+'</button></div>'+
    '<div class="sub" data-for="hl">'+Object.keys(COLORS).map(function(c){return '<span class="swl"><button type="button" class="sw" data-c="'+c+'" aria-pressed="'+(c==='y')+'" style="background:var(--hl-'+c+')" aria-label="'+COLORS[c]+'"></button>'+COLORS[c].split(' ').slice(-1)[0]+'</span>';}).join('')+'<span class="sep"></span>'+
      '<button type="button" class="wbtn" data-msize="0" aria-pressed="false" title="가늘게"><span style="width:16px;height:5px;opacity:.5"></span></button>'+
      '<button type="button" class="wbtn" data-msize="1" aria-pressed="true" title="보통"><span style="width:16px;height:9px;opacity:.5"></span></button>'+
      '<button type="button" class="wbtn" data-msize="2" aria-pressed="false" title="굵게"><span style="width:16px;height:13px;opacity:.5"></span></button><span class="sep"></span>'+
      '<span class="hm" role="group" aria-label="톡 눌렀을 때"><button type="button" data-hm="s" aria-pressed="'+(hlMode==='s')+'" title="톡 누르면 문장 전체">문장</button><button type="button" data-hm="w" aria-pressed="'+(hlMode==='w')+'" title="톡 누르면 이 장의 같은 용어 전부">용어</button></span></div>'+
    '<div class="sub" data-for="pen" hidden>'+
      '<span class="swl"><button type="button" class="sw" data-ink="1" aria-pressed="true" style="background:var(--ink-1)" aria-label="먹색"></button>먹색</span>'+
      '<span class="swl"><button type="button" class="sw" data-ink="2" aria-pressed="false" style="background:var(--ink-2)" aria-label="남색 잉크"></button>남색</span>'+
      '<span class="swl"><button type="button" class="sw" data-ink="3" aria-pressed="false" style="background:var(--ink-3)" aria-label="적갈색"></button>적갈색</span>'+
      '<span class="sep"></span>'+
      '<button type="button" class="wbtn" data-size="0" aria-pressed="false" title="가늘게"><span style="width:16px;height:2px"></span></button>'+
      '<button type="button" class="wbtn" data-size="1" aria-pressed="true" title="보통"><span style="width:16px;height:4px"></span></button>'+
      '<button type="button" class="wbtn" data-size="2" aria-pressed="false" title="굵게"><span style="width:16px;height:6px"></span></button>'+
      '<label class="tg"><input type="checkbox" id="pencil-only"> 펜슬로만 쓰기</label></div>'+
    '';
  document.body.appendChild(dock);
  var hint={set textContent(v){}}, hlColor='y';
  var HINT={hl:'글자를 길게 눌러 고르고 손을 떼면 지금 색으로 칠해집니다. 색을 바꾸려면 아래 색을 누르세요.',pen:'만년필: 펜촉 방향에 따라 획이 굵고 가늘어지고, 손떨림을 잡아 줍니다.',ball:'볼펜: 고른 굵기로 씁니다.',eraser:'지울 손글씨 획 위를 문지르거나, 지울 형광펜을 누르세요.'};
  function setTool(t){
    tool=(tool===t)?null:t;
    ['hl','pen','ball','eraser'].forEach(function(x){document.body.classList.toggle('tool-'+x,tool===x);});
    [].forEach.call(dock.querySelectorAll('[data-t]'),function(b){b.setAttribute('aria-pressed',b.dataset.t===tool?'true':'false');});
    dock.querySelector('[data-for="hl"]').hidden=!(tool==='hl'||tool===null);
    dock.querySelector('[data-for="pen"]').hidden=!(tool==='pen'||tool==='ball');
    hint.textContent=tool?HINT[tool]:'도구를 고르세요. 형광펜 색: 노랑 기억 · 분홍 찔림 · 하늘 약속 · 연두 질문';
    if(tool) arts.filter(function(a){return !a.hasAttribute('data-off');}).forEach(function(a){loadChapter(a.id);sections(a.id).forEach(overlay);});
    try{localStorage.setItem('ppnote-tool',tool||'');}catch(e){}
  }
  function pickColor(b){
    hlColor=b.dataset.c;[].forEach.call(dock.querySelectorAll('[data-c]'),function(x){x.setAttribute('aria-pressed',x===b?'true':'false');});
    if(tool!=='hl') setTool('hl');
    if(!applyColor(hlColor)) hint.textContent='이제 글자를 길게 눌러 고르면 '+COLORS[hlColor]+' 색으로 칠해집니다.';
  }
  function keepSel(e){if(e.target.closest('button,label')) e.preventDefault();}
  dock.addEventListener('mousedown',keepSel); dock.addEventListener('pointerdown',function(e){var b=e.target.closest('.sw[data-c]');if(!b)return;e.preventDefault();pickColor(b);});
  dock.addEventListener('click',function(e){
    var b=e.target.closest('button'); if(!b) return;
    if(b.dataset.t) setTool(b.dataset.t);
    if(b.dataset.c&&e.detail===0) pickColor(b); // 키보드로 누른 경우
    if(b.dataset.ink){ink=b.dataset.ink;[].forEach.call(dock.querySelectorAll('[data-ink]'),function(x){x.setAttribute('aria-pressed',x===b?'true':'false');});}
    if(b.dataset.msize){msize=+b.dataset.msize;[].forEach.call(dock.querySelectorAll('[data-msize]'),function(x){x.setAttribute('aria-pressed',x===b?'true':'false');});}
    if(b.dataset.size){size=+b.dataset.size;[].forEach.call(dock.querySelectorAll('[data-size]'),function(x){x.setAttribute('aria-pressed',x===b?'true':'false');});}
    if(b.dataset.hm){hlMode=b.dataset.hm;[].forEach.call(dock.querySelectorAll('[data-hm]'),function(x){x.setAttribute('aria-pressed',x===b?'true':'false');});try{localStorage.setItem('ppnote-hm',hlMode);}catch(err){}if(tool!=='hl')setTool('hl');}
    if(b.dataset.a==='undo') doUndo();
    if(b.dataset.a==='gather') openGather();
    if(b.dataset.a==='min'){var m=dock.classList.toggle('min');b.setAttribute('aria-expanded',m?'false':'true');placeDock();}
    if(b.dataset.a==='zi'||b.dataset.a==='zo') setZoom(rz+(b.dataset.a==='zi'?0.1:-0.1));
  });
  var po=dock.querySelector('#pencil-only');
  var touchDev=('ontouchstart' in window)||navigator.maxTouchPoints>0;
  function setPO(v){po.checked=v;document.body.classList.toggle('pencil-only',v);try{localStorage.setItem('ppnote-po',v?'1':'0');}catch(e){}}
  po.addEventListener('change',function(){setPO(po.checked);});
  var poS=null;try{poS=localStorage.getItem('ppnote-po');}catch(e){}
  setPO(poS===null?touchDev:poS==='1');
  function showStore(){var el=document.getElementById('nstore');if(el)el.textContent=mode==='db'?'계정에 저장됩니다 (다른 기기에서도 보임)':'이 기기의 브라우저에만 저장됩니다';}
  showStore();

  /* 도구 창 위치: 화면(보이는 영역) 기준으로 고정, 확대해도 같은 크기 */
  /* 붙는 쪽에 따라 모양이 바뀜: 왼쪽·오른쪽 끝 → 세로, 위·아래 끝 → 가로 */
  var vv=window.visualViewport, pos={side:'b',at:-1}, drag=null, M=12;
  try{var ps=JSON.parse(localStorage.getItem('ppnote-dock2')||'null');if(ps&&ps.side)pos=ps;}catch(e){}
  function view(){ // 손가락 확대(scale>1)일 때만 보이는 영역 오프셋을 씀. 키보드가 올라와 화면이 밀린 것(scale=1)은 무시 → 도구 창이 화면 밖으로 안 나감
    var sc=vv?vv.scale:1; if(!vv||sc<1.02) return {sc:1,ox:0,oy:0,W:window.innerWidth,H:window.innerHeight};
    return {sc:sc,ox:vv.offsetLeft,oy:vv.offsetTop,W:vv.width*sc,H:vv.height*sc};}
  function topGap(){var b=document.querySelector('.bar');var r=b?b.getBoundingClientRect():null;return r&&r.bottom>0?r.bottom+M:M;}
  function setShape(){dock.classList.toggle('vert',pos.side==='l'||pos.side==='r');}
  function placeDock(fx,fy){
    if(dock.hidden) return; var v=view(), w=dock.offsetWidth, h=dock.offsetHeight, sx, sy;
    if(fx!=null){sx=fx;sy=fy;}
    else if(pos.side==='l'||pos.side==='r'){sx=pos.side==='l'?M:v.W-w-M; sy=pos.at<0?(v.H-h)/2:pos.at;}
    else {sy=pos.side==='t'?topGap():v.H-h-M; sx=pos.at<0?v.W-w-M:pos.at;}
    sx=Math.max(M,Math.min(v.W-w-M,sx)); sy=Math.max(M,Math.min(v.H-h-M,sy));
    dock.style.transform='translate('+(v.ox+sx/v.sc)+'px,'+(v.oy+sy/v.sc)+'px)'+(v.sc!==1?' scale('+(1/v.sc)+')':'');
    dock._sx=sx; dock._sy=sy;
  }
  setShape();
  if(vv){vv.addEventListener('resize',function(){placeDock();});vv.addEventListener('scroll',function(){placeDock();});}
  window.addEventListener('resize',function(){placeDock();}); window.addEventListener('orientationchange',function(){setTimeout(placeDock,300);});
  /* 검색창 등에 글자를 칠 때(키보드)는 도구 창을 잠시 숨기고, 끝나면 제자리에 다시 놓음 */
  function isField(t){return t&&t.matches&&t.matches('input:not([type=checkbox]):not([type=radio]),textarea,select,[contenteditable]')&&!t.closest('.myans');}
  document.addEventListener('focusin',function(e){if(isField(e.target))dock.classList.add('typing');});
  document.addEventListener('focusout',function(e){if(!isField(e.target))return;dock.classList.remove('typing');[0,250,600,1200].forEach(function(t){setTimeout(function(){placeDock();},t);});});
  var sT=null; window.addEventListener('scroll',function(){clearTimeout(sT);sT=setTimeout(function(){placeDock();},120);},{passive:true});
  document.addEventListener('chapshow',function(){setTimeout(function(){placeDock();},50);});
  var grip=dock.querySelector('.grip');
  grip.addEventListener('pointerdown',function(e){e.preventDefault();try{grip.setPointerCapture(e.pointerId);}catch(err){}drag={x:e.clientX,y:e.clientY,sx:dock._sx||0,sy:dock._sy||0};dock.classList.add('dragging');});
  grip.addEventListener('pointermove',function(e){if(!drag)return;var sc=view().sc;placeDock(drag.sx+(e.clientX-drag.x)*sc,drag.sy+(e.clientY-drag.y)*sc);});
  function dropDock(){if(!drag)return;drag=null;dock.classList.remove('dragging');var v=view(),w=dock.offsetWidth,h=dock.offsetHeight;
    var cx=dock._sx+w/2, cy=dock._sy+h/2, d={l:cx, r:v.W-cx, t:cy, b:v.H-cy};
    var side=Object.keys(d).sort(function(a,b){return d[a]-d[b];})[0];
    var before=dock.classList.contains('vert');
    pos={side:side,at:(side==='l'||side==='r')?Math.max(0,cy-h/2):Math.max(0,cx-w/2)};
    setShape();
    if(dock.classList.contains('vert')!==before){ // 모양이 바뀌면 크기가 달라지므로 손을 놓은 자리 중심에 다시 맞춤
      var w2=dock.offsetWidth,h2=dock.offsetHeight; pos.at=(side==='l'||side==='r')?Math.max(0,cy-h2/2):Math.max(0,cx-w2/2);}
    try{localStorage.setItem('ppnote-dock2',JSON.stringify(pos));}catch(err){} placeDock();}
  grip.addEventListener('pointerup',dropDock); grip.addEventListener('pointercancel',dropDock);
  /* 글자 크기(화면 확대 대신) */
  var rz=1; try{rz=parseFloat(localStorage.getItem('ppnote-rz'))||1;}catch(e){}
  function setZoom(z){rz=Math.max(0.8,Math.min(1.8,Math.round(z*10)/10));
    /* 읽던 자리 유지: 화면 위쪽 단락과 그 안의 비율을 기억했다가 되돌림 */
    var anc=null,fr=0,top=(document.querySelector('.bar')||{}).offsetHeight||0;
    var ps=document.querySelectorAll('article.chap:not([data-off]) section.page');
    for(var i=0;i<ps.length;i++){var r=ps[i].getBoundingClientRect(); if(r.bottom>top+4&&r.height){anc=ps[i];fr=(top+4-r.top)/r.height;break;}}
    document.documentElement.style.setProperty('--rz',rz);try{localStorage.setItem('ppnote-rz',rz);}catch(e){}
    document.querySelectorAll('svg.ink').forEach(function(sv){var sec=sv.parentNode,w=sec.clientWidth||1,h=sec.clientHeight||1;sv.setAttribute('viewBox','0 0 1000 '+(1000*h/w).toFixed(1));});
    if(anc){var r2=anc.getBoundingClientRect(); window.scrollBy(0,r2.top+Math.max(0,fr)*r2.height-(top+4));}
    var zv=document.getElementById('zval'); if(zv) zv.textContent=Math.round(rz*100)+'%';}

  /* 바에 필기 버튼 */
  var bar=document.querySelector('.bar'), nb=document.createElement('button');
  nb.type='button'; nb.id='notesbtn'; nb.textContent='필기'; nb.setAttribute('aria-pressed','false');
  /* 바에 글자 크기 (필기를 켜지 않아도 늘 보임) */
  var zs=document.createElement('span'); zs.className='seg zseg'; zs.setAttribute('role','group'); zs.setAttribute('aria-label','글자 크기');
  zs.innerHTML='<button type="button" data-z="-1" title="글자 작게" aria-label="글자 작게">가−</button><button type="button" id="zval" data-z="0" title="기본 크기로" aria-label="글자 크기 기본으로">100%</button><button type="button" data-z="1" title="글자 크게" aria-label="글자 크게">가+</button>';
  zs.addEventListener('click',function(e){var b=e.target.closest('button'); if(!b) return; var d=+b.dataset.z; setZoom(d?rz+d*0.1:1);});
  bar.appendChild(zs);
  bar.appendChild(nb);
  setZoom(rz);
  function setNotes(on){
    document.body.classList.toggle('notes-on',on); dock.hidden=!on; nb.setAttribute('aria-pressed',on?'true':'false'); if(on) requestAnimationFrame(function(){placeDock();});
    if(!on){tool=null;['hl','pen','ball','eraser'].forEach(function(x){document.body.classList.remove('tool-'+x);});}
    else setTool(null);
    try{localStorage.setItem('ppnote-on',on?'1':'0');}catch(e){}
  }
  nb.addEventListener('click',function(){setNotes(!document.body.classList.contains('notes-on'));});

  /* ── 모아 보기 ───────────────────────── */
  var g=document.createElement('div'); g.className='gather'; g.hidden=true;
  g.innerHTML='<div class="sheet" role="dialog" aria-label="모아 보기"><div class="top"><h2>모아 보기</h2><button type="button" data-x>닫기</button></div><p class="store" id="nstore"></p>'+
    '<select id="gch" aria-label="장 선택"><option value="all">전체 장</option>'+arts.map(function(a){return '<option value="'+a.id+'">'+a.getAttribute('data-title')+'</option>';}).join('')+'</select>'+
    '<div class="filt" id="gf"><button type="button" data-f="all" aria-pressed="true">전부</button>'+Object.keys(COLORS).map(function(c){return '<button type="button" data-f="'+c+'" aria-pressed="false">'+COLORS[c]+'</button>';}).join('')+'<button type="button" data-f="a" aria-pressed="false">내 답</button></div><div id="glist"></div></div>';
  document.body.appendChild(g); showStore();
  var gf='all';
  function openGather(){g.hidden=false; var s=g.querySelector('#gch'); if(current) s.value=current; renderGather();}
  g.addEventListener('click',function(e){
    if(e.target===g||e.target.hasAttribute('data-x')){g.hidden=true;return;}
    var f=e.target.closest('[data-f]'); if(f){gf=f.dataset.f;[].forEach.call(g.querySelectorAll('[data-f]'),function(x){x.setAttribute('aria-pressed',x===f?'true':'false');});renderGather();return;}
    var it=e.target.closest('.it'); if(it){g.hidden=true; if(it.dataset.sec){var o=document.getElementById('chap');if(o){o.value=it.dataset.ch;o.dispatchEvent(new Event('change'));}setTimeout(function(){var t=document.getElementById(it.dataset.sec);if(t)t.scrollIntoView({block:'start'});},160);} else jumpTo(it.dataset.ch,+it.dataset.k,it.dataset.q);}
  });
  g.querySelector('#gch').addEventListener('change',renderGather);
  function renderGather(){
    var sel=g.querySelector('#gch').value, list=g.querySelector('#glist'), ids=sel==='all'?arts.map(function(a){return a.id;}):[sel];
    list.textContent='불러오는 중…';
    Promise.all(ids.map(loadChapter)).then(function(){
      list.innerHTML=''; var n=0;
      ids.forEach(function(c){
        var d=chData[c]; if(!d) return;
        var items=[];
        if(gf==='all'||gf!=='a') d.hl.filter(function(h){return gf==='all'||h.c===gf;}).sort(function(a,b){return a.k-b.k||a.s-b.s;}).forEach(function(h){items.push({cls:h.c,small:COLORS[h.c],text:h.t,k:h.k});});
        if(gf!=='a') sections(c).forEach(function(sec){(inkData[inkKey(c,sid(sec))]||[]).forEach(function(st){if(st.t==='m'&&st.tx&&(gf==='all'||gf===st.c))items.push({cls:st.c,small:COLORS[st.c],text:st.tx,sec:sec.id});});});
        if(gf==='all'||gf==='a') Object.keys(d.ans).forEach(function(q){items.push({cls:'a',small:'내 답 · '+d.ans[q].q,text:d.ans[q].t,q:q});});
        if(!items.length) return;
        var hd=document.createElement('div'); hd.className='grp'; hd.textContent=byId[c].getAttribute('data-title'); list.appendChild(hd);
        items.forEach(function(x){var b=document.createElement('button');b.type='button';b.className='it '+x.cls;b.dataset.ch=c;if(x.k!=null)b.dataset.k=x.k;if(x.q)b.dataset.q=x.q;if(x.sec)b.dataset.sec=x.sec;
          var s=document.createElement('small');s.textContent=x.small;b.appendChild(s);b.appendChild(document.createTextNode(x.text));list.appendChild(b);n++;});
      });
      if(!n){list.innerHTML='<p class="empty">아직 모은 것이 없습니다. 위쪽 <b>필기</b>를 켜고 글자를 길게 눌러 고른 다음 색을 누르면 여기에 모입니다. 튜터 가이드 질문 아래 <b>✎ 내 답 쓰기</b>에 적은 답도 함께 모입니다.</p>';}
    });
  }
  function jumpTo(c,k,q){
    var o=document.getElementById('chap'); if(o){o.value=c;o.dispatchEvent(new Event('change'));}
    setTimeout(function(){
      var t=null;
      if(q){t=document.getElementById('ans-'+c+'-'+q);} else if(!isNaN(k)){t=blocksOf(byId[c])[k];}
      if(t) t.scrollIntoView({block:'center'});
    },160);
  }

  /* ── 장 표시와 연결 ───────────────────── */
  document.addEventListener('chapshow',function(e){current=e.detail; if(current){loadChapter(current); if(tool) sections(current).forEach(overlay);}});
  var vis=arts.filter(function(a){return !a.hasAttribute('data-off');});
  if(vis.length===1||document.body.classList.contains('single')) current=(vis[0]||{}).id||null;
  if(current) loadChapter(current);
  if('IntersectionObserver' in window){
    var io=new IntersectionObserver(function(es){es.forEach(function(x){if(x.isIntersecting) loadChapter(x.target.id);});},{rootMargin:'200px 0px'});
    arts.forEach(function(a){io.observe(a);});
  }
  var on=null;try{on=localStorage.getItem('ppnote-on');}catch(e){}
  if(on==='1') setNotes(true);
  setTimeout(initStore,0);
})();
</script>
