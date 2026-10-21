#!/usr/bin/env python3
"""『법인 컨설팅 100문 100답』 웹 스터디북 생성기 — content/*.md → web/index.html (Claude 아티팩트용).

인쇄판(build.py)과 같은 원고를 쓰고, 화면용 마크업과 학습 도구(검색·읽음 체크·메모·형광펜·모아 보기)를 붙인다.
"""
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from build import load_chapters, md_to_html  # noqa: E402
from toc import BOOK_SUBTITLE, BOOK_TITLE, PARTS  # noqa: E402


def emph(t):
    t = html.escape(t)
    t = re.sub(r"\*(.+?)\*", r"<em>\1</em>", t)
    return t.replace("|", "<br>")


def tables(h):
    return h.replace("<table", '<div class="tw"><table').replace("</table>", "</table></div>")


def plain(h):
    t = re.sub(r"<[^>]+>", " ", h)
    return re.sub(r"\s+", " ", html.unescape(t)).strip()


SKILL = os.path.join(ROOT, "..", "plugins", "study-annotation", "skills", "study-annotation", "assets")


def notes_assets():
    """study-annotation 스킬의 notes.js / notes.css를 이 책 구조에 맞춰 불러온다."""
    css = open(os.path.join(SKILL, "notes.css"), encoding="utf-8").read()
    js = open(os.path.join(SKILL, "notes.js"), encoding="utf-8").read()
    subs = [
        ("var COLORS={y:'기억할 문장',p:'나를 찌르는 말씀',b:'붙잡을 약속',g:'모임에 가져갈 질문'};",
         "var COLORS={y:'핵심',p:'주의',b:'숫자·요건',g:'고객용'};"),
        ("var BLOCKS='.text p, .guide p, .qa .q, blockquote, .notes li, .kr, .verse, .cmp td, .steps li';",
         "var BLOCKS='.intro p, .intro li, .qhead h3, .qbody p, .qbody li, .qbody td, .qbody h4, .caption';"),
        ("function sid(sec){return sec.id.split('-').slice(1).join('-')||'x';}", "function sid(sec){return sec.id;}"),
        ("section.page", "section.qsec"),
        ("a.querySelectorAll('.qa > div')", "a.querySelectorAll('section.qsec:not(.intro-sec)')"),
        ("q:(q.querySelector('.q')||{}).textContent||''", "q:(q.querySelector('.q, .qhead h3')||{}).textContent||''"),
        ("ta.placeholder='먼저 스스로 답해 보세요. 그다음 아래 해설을 읽습니다.';",
         "ta.placeholder='이 질문에 대한 내 생각, 고객 사례, 다음에 물어볼 것을 적어 두세요.';"),
        ("'도구를 고르세요. 형광펜 색: 노랑 기억 · 분홍 찔림 · 하늘 약속 · 연두 질문'",
         "'도구를 고르세요. 형광펜 색: 노랑 핵심 · 분홍 주의 · 하늘 숫자·요건 · 연두 고객용'"),
        ("튜터 가이드 질문 아래 <b>✎ 내 답 쓰기</b>", "질문 끝의 <b>✎ 내 답 쓰기</b>"),
        # 모아 보기 버튼을 도구 창에 되살림 (스킬 3절)
        ("'<button type=\"button\" data-a=\"undo\" title=\"되돌리기\">'+I.undo+'</button>'+",
         "'<button type=\"button\" data-a=\"undo\" title=\"되돌리기\">'+I.undo+'</button>'+'<button type=\"button\" data-a=\"gather\" title=\"모아 보기\" aria-label=\"모아 보기\">'+I.list+'</button>'+"),
    ]
    for a, b in subs:
        if a not in js:
            raise SystemExit("notes.js 적용 실패: " + a[:60])
        js = js.replace(a, b)
    return css, js


def main():
    chs = load_chapters()
    by_id = {c["id"]: c for c in chs}
    q = 0
    nav, arts, toc_parts, search = [], [], [], []
    for pl, pt, ps, ids in PARTS:
        rows = []
        for cid in ids:
            c = by_id[cid]
            n = int(cid)
            qs_html, opts = [], []
            first_q = q + 1
            for qq in c["qs"]:
                q += 1
                body = tables(md_to_html(qq["body"]))
                qid = f"q{q:03d}"
                subs = " · ".join(qq["subs"][:3])
                qs_html.append(
                    f'<section class="qsec" id="{qid}" data-q="{qid}" data-ch="c{cid}">'
                    f'<div class="qhead"><span class="qno"><small>Q</small>{q:03d}</span><h3>{html.escape(qq["title"])}</h3></div>'
                    f'<div class="qbody">{body}</div>'
                    f'<div class="qfoot"><button type="button" class="readbtn" data-q="{qid}" aria-pressed="false">읽음 표시</button>'
                    f'<span class="saved" aria-live="polite"></span></div>'
                    f'</section>')
                opts.append(f'<option value="{qid}">{q:03d} {html.escape(qq["title"])}</option>')
                search.append({"id": qid, "n": q, "c": n, "t": qq["title"], "x": plain(body)[:6000]})
            last_q = q
            intro = tables(md_to_html(c["intro"]))
            arts.append(
                f'<article class="page view chap" id="c{cid}" hidden data-off data-title="{n}장 {html.escape(c["meta"]["title"])}">'
                f'<header class="ch-open"><div class="chno">{html.escape(pl)} · {n}장</div>'
                f'<div class="frame"><span class="tag">들어가기 전에</span><h2>{emph(c["meta"].get("open", c["meta"]["title"]))}</h2></div>'
                f'<p class="chtitle">{html.escape(c["meta"]["title"])} · Q{first_q:03d}–{last_q:03d}</p></header>'
                f'<section class="qsec intro intro-sec" id="c{cid}-intro">{intro}</section>{"".join(qs_html)}'
                f'<nav class="chapnav" aria-label="장 이동"></nav></article>')
            nav.append(f'<optgroup label="{n}장 {html.escape(c["meta"]["title"])}">{"".join(opts)}</optgroup>')
            rows.append(
                f'<li><a href="#c{cid}" data-go="c{cid}"><span class="cn">{n:02d}</span>'
                f'<span class="ct"><b>{html.escape(c["meta"]["title"])}</b><small>{" · ".join(html.escape(x["title"]) for x in c["qs"][:3])}{" …" if len(c["qs"]) > 3 else ""}</small></span>'
                f'<span class="cp" data-range="{first_q}-{last_q}">{last_q - first_q + 1}문</span></a></li>')
        toc_parts.append(f'<div class="part"><div class="pl">{html.escape(pl)}</div><div class="pt"><b>{html.escape(pt)}</b>'
                         f'<span>{html.escape(ps)}</span></div><ol>{"".join(rows)}</ol></div>')
    chopts = "".join(f'<option value="c{c["id"]}">{int(c["id"])}장 {html.escape(c["meta"]["title"])}</option>' for c in chs)
    pro = tables(md_to_html(open(os.path.join(ROOT, "content", "prologue.md"), encoding="utf-8").read()))
    app = tables(md_to_html(open(os.path.join(ROOT, "content", "appendix.md"), encoding="utf-8").read()))

    tpl = open(os.path.join(ROOT, "web_template.html"), encoding="utf-8").read()
    out = (tpl.replace("{{TITLE}}", BOOK_TITLE)
           .replace("{{SUBTITLE}}", html.escape(BOOK_SUBTITLE))
           .replace("{{CHOPTS}}", chopts)
           .replace("{{QOPTS}}", "".join(nav))
           .replace("{{TOC}}", "".join(toc_parts))
           .replace("{{PROLOGUE}}", pro)
           .replace("{{CHAPTERS}}", "".join(arts))
           .replace("{{APPENDIX}}", app)
           .replace("{{NOTES_CSS}}", notes_assets()[0])
           .replace("{{NOTES_JS}}", notes_assets()[1])
           .replace("{{SEARCH}}", json.dumps(search, ensure_ascii=False).replace("</", "<\\/")))
    os.makedirs(os.path.join(ROOT, "web"), exist_ok=True)
    path = os.path.join(ROOT, "web", "법인컨설팅-100문100답.html")
    open(path, "w", encoding="utf-8").write(out)
    print(path, f"{len(out.encode()) / 1024:.0f} KB", "questions", q)


if __name__ == "__main__":
    main()
