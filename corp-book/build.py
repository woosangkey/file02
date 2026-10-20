#!/usr/bin/env python3
"""법인 컨설팅 100문 100답 — content/NN.md → out/book.pdf (2-pass로 차례 쪽번호 계산).

장 파일 형식:
    chapter: 03
    title: 정리하지 않으면 위험한 가지급금
    open: 대표님 통장과 회사 통장,|*경계*가 무너질 때      ← '들어가기 전에' 큰 제목(| 줄바꿈, *강조*=코랄)
    ---
    (들어가기 전에 본문)
    ## 질문 제목         ← 질문마다 h2, 번호(Q001~)는 자동
    ### 소제목            ← 차례에 쪽번호와 함께 표시
"""
import html
import os
import re
import subprocess
import sys

from pypdf import PdfReader

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from toc import AUTHOR, BOOK_SUBTITLE, BOOK_TITLE, PARTS  # noqa: E402

OUT = os.path.join(ROOT, "out")


def md_to_html(md):
    md = curly(md)
    return subprocess.run(["pandoc", "-f", "markdown+raw_html-implicit_figures-smart", "-t", "html5", "--wrap=none"],
                          input=md, capture_output=True, text=True, check=True).stdout


def curly(text):
    out = []
    for chunk in re.split(r"(<[^>]*>|```.*?```)", text, flags=re.S):
        if chunk.startswith("<") or chunk.startswith("```"):
            out.append(chunk)
            continue
        chunk = re.sub(r'"([^"\n]+)"', "“\\1”", chunk)
        chunk = re.sub(r"'([^'\n]+)'", "‘\\1’", chunk)
        out.append(chunk)
    return "".join(out)


def emph(t):
    t = html.escape(t)
    t = re.sub(r"\*(.+?)\*", r"<em>\1</em>", t)
    return t.replace("|", "<br>")


def load_chapters():
    chs = []
    for _, _, _, ids in PARTS:
        for cid in ids:
            path = os.path.join(ROOT, "content", f"{cid}.md")
            if not os.path.exists(path):
                continue
            raw = open(path, encoding="utf-8").read()
            head, body = raw.split("\n---\n", 1)
            meta = {k.strip(): v.strip() for k, v in (l.split(":", 1) for l in head.strip().splitlines())}
            parts = re.split(r"(?m)^## ", body)
            intro = parts[0]
            qs = []
            for blk in parts[1:]:
                title, rest = blk.split("\n", 1)
                subs = re.findall(r"(?m)^### (.+)$", rest)
                qs.append({"title": title.strip(), "body": rest, "subs": [s.strip() for s in subs]})
            chs.append({"id": cid, "meta": meta, "intro": intro, "qs": qs})
    return chs


def page_rules(chs):
    rules = []
    for c in chs:
        n = int(c["id"])
        label = f'{n}장  {c["meta"]["title"]}'.replace('"', "'")
        rules.append(f'@page ch{c["id"]}:right {{ @bottom-center {{ content: "{label}"; font: 6.8pt "Noto Sans CJK KR"; '
                     f'color: #888; text-align: right; vertical-align: middle; }} }}')
    return "\n".join(rules)


def build_html(chs, pages):
    css = open(os.path.join(ROOT, "style.css"), encoding="utf-8").read().replace("CHAPTER_PAGE_RULES", page_rules(chs))
    out = [f"<!doctype html><html lang='ko'><head><meta charset='utf-8'><title>{BOOK_TITLE}</title><style>{css}</style></head><body>"]
    # 표지
    out.append('<section class="cover"><div class="band"></div><div class="frame"><div class="tag">CEO가 묻고 컨설턴트가 답하다</div>'
               '<h1>법인 컨설팅<br><em>100문 100답</em></h1>'
               f'<div class="sub">{html.escape(BOOK_SUBTITLE)}</div></div>'
               '<div class="keys">법인전환 · 정관 · 가지급금 · 명의신탁주식 · 비상장주식 · 자기주식 · 퇴직금 · 상속·증여 · 가업승계 · 인사노무</div>'
               f'<div class="author">{html.escape(AUTHOR)}</div><div class="foot"></div></section>')
    # 차례
    q = 0
    toc = ['<section class="toc"><div class="toc-h">차례</div>']
    for key in ("prologue",):
        if pages.get(key):
            toc.append(f'<div class="q"><span class="no">P</span><span class="t">프롤로그</span><span class="p">{pages[key]:03d}</span></div>')
    by_id = {c["id"]: c for c in chs}
    for pl, pt, ps, ids in PARTS:
        toc.append(f'<div class="part"><div class="pl">{pl[:-2]}<br>마당</div><div class="pt"><b>{html.escape(pt)}</b>'
                   f'<span>: {html.escape(ps)}</span></div></div>')
        for cid in ids:
            c = by_id.get(cid)
            if not c:
                continue
            p = pages.get(f"ch{cid}")
            toc.append(f'<div class="ch"><span class="tagc">{int(cid)}장</span><span class="t">{html.escape(c["meta"]["title"])}</span>'
                       f'<span class="p">{p:03d}</span></div>' if p else
                       f'<div class="ch"><span class="tagc">{int(cid)}장</span><span class="t">{html.escape(c["meta"]["title"])}</span></div>')
            for qq in c["qs"]:
                q += 1
                p = pages.get(f"q{q}")
                toc.append(f'<div class="q"><span class="no">{q:03d}</span><span class="t">{html.escape(qq["title"])}</span>'
                           f'<span class="p">{f"{p:03d}" if p else ""}</span></div>')
    if pages.get("appendix"):
        toc.append(f'<div class="ch"><span class="tagc">부록</span><span class="t">핵심 질문 100 · 2026 주요 세율표</span><span class="p">{pages["appendix"]:03d}</span></div>')
    toc.append("</section>")
    out.append("".join(toc))
    # 프롤로그
    pro = os.path.join(ROOT, "content", "prologue.md")
    if os.path.exists(pro):
        out.append(f'<section class="plain" id="prologue">{md_to_html(open(pro, encoding="utf-8").read())}</section>')
    # 본문
    q = 0
    for pl, pt, ps, ids in PARTS:
        chs_in = [by_id[i] for i in ids if i in by_id]
        if not chs_in:
            continue
        lis = "".join(f'<li><span>{int(c["id"])}장</span>{html.escape(c["meta"]["title"])}</li>' for c in chs_in)
        out.append(f'<section class="part-open"><div class="pl">{pl}</div><h2>{html.escape(pt)}</h2>'
                   f'<div class="ps">: {html.escape(ps)}</div><ul>{lis}</ul></section>')
        for c in chs_in:
            n = int(c["id"])
            sec = [f'<section class="chapter" style="page: ch{c["id"]}">',
                   f'<div class="ch-open"><div class="chno">CHAPTER {n:02d} · {html.escape(c["meta"]["title"])}</div>'
                   f'<div class="frame"><div class="tag">들어가기 전에</div><h1>{emph(c["meta"].get("open", c["meta"]["title"]))}</h1></div>'
                   f'<div class="frame-bottom"></div></div>',
                   md_to_html(c["intro"])]
            for i, qq in enumerate(c["qs"]):
                q += 1
                sec.append(f'<div class="qsec">'
                           f'<div class="qhead"><span class="qno"><small>Q</small>{q:03d}</span><h2>{html.escape(qq["title"])}</h2>'
                           f'<span class="chq">{n}장</span></div>{md_to_html(qq["body"])}</div>')
            sec.append("</section>")
            out.append("".join(sec))
    app = os.path.join(ROOT, "content", "appendix.md")
    if os.path.exists(app):
        out.append(f'<section class="plain" id="appendix">{md_to_html(open(app, encoding="utf-8").read())}</section>')
    out.append("</body></html>")
    return "\n".join(out)


def render(src, pdf):
    env = {**os.environ, "NODE_PATH": subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip()}
    subprocess.run(["node", os.path.join(ROOT, "..", "money-book", "print.js"), src, pdf], check=True, env=env)


def norm(s):
    return re.sub(r"[\s‘’“”'\"]", "", s)


def find_pages(pdf, chs):
    texts = [norm(p.extract_text() or "") for p in PdfReader(pdf).pages]
    pages, start, q = {}, 2, 0

    def seek(key, frm):
        for i in range(frm, len(texts)):
            if key and key in texts[i]:
                return i
        return None
    i = seek("프롤로그", start)
    if i is not None:
        pages["prologue"] = i + 1
    for c in chs:
        i = seek("CHAPTER" + f"{int(c['id']):02d}", start)
        if i is not None:
            pages[f"ch{c['id']}"] = i + 1
            start = i
        for qq in c["qs"]:
            q += 1
            i = seek(f"Q{q:03d}" + norm(qq["title"])[:8], start)
            if i is not None:
                pages[f"q{q}"] = i + 1
                start = i
    i = seek("핵심질문100", start)
    if i is not None:
        pages["appendix"] = i + 1
    return pages


def main():
    os.makedirs(OUT, exist_ok=True)
    chs = load_chapters()
    src, pdf = os.path.join(OUT, "book.html"), os.path.join(OUT, "book.pdf")
    pages = {}
    for _ in range(2):
        open(src, "w", encoding="utf-8").write(build_html(chs, pages))
        render(src, pdf)
        pages = find_pages(pdf, chs)
    open(src, "w", encoding="utf-8").write(build_html(chs, pages))
    render(src, pdf)
    nq = sum(len(c["qs"]) for c in chs)
    print(f"chapters={len(chs)} questions={nq} pages={len(PdfReader(pdf).pages)} located={len(pages)}")
    if "--preview" in sys.argv:
        subprocess.run(["python3", os.path.join(ROOT, "..", "money-book", "spreads.py"), pdf, os.path.join(OUT, "preview")], check=True)


if __name__ == "__main__":
    main()
