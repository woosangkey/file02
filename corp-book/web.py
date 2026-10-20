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
                    f'<button type="button" class="memobtn" data-q="{qid}">메모</button><span class="saved" aria-live="polite"></span>'
                    f'<textarea class="memo" id="memo-{qid}" data-q="{qid}" hidden placeholder="이 질문에 대한 내 생각, 고객 사례, 다음에 물어볼 것"></textarea></div>'
                    f'</section>')
                opts.append(f'<option value="{qid}">{q:03d} {html.escape(qq["title"])}</option>')
                search.append({"id": qid, "n": q, "c": n, "t": qq["title"], "x": plain(body)[:6000]})
            last_q = q
            intro = tables(md_to_html(c["intro"]))
            arts.append(
                f'<article class="page view chap" id="c{cid}" hidden data-title="{n}장 {html.escape(c["meta"]["title"])}">'
                f'<header class="ch-open"><div class="chno">{html.escape(pl)} · {n}장</div>'
                f'<div class="frame"><span class="tag">들어가기 전에</span><h2>{emph(c["meta"].get("open", c["meta"]["title"]))}</h2></div>'
                f'<p class="chtitle">{html.escape(c["meta"]["title"])} · Q{first_q:03d}–{last_q:03d}</p></header>'
                f'<div class="intro">{intro}</div>{"".join(qs_html)}'
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
           .replace("{{SEARCH}}", json.dumps(search, ensure_ascii=False).replace("</", "<\\/")))
    os.makedirs(os.path.join(ROOT, "web"), exist_ok=True)
    path = os.path.join(ROOT, "web", "법인컨설팅-100문100답.html")
    open(path, "w", encoding="utf-8").write(out)
    print(path, f"{len(out.encode()) / 1024:.0f} KB", "questions", q)


if __name__ == "__main__":
    main()
