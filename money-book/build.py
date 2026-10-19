#!/usr/bin/env python3
"""책 조판 빌드: content/*.md → book.html → (1차 PDF로 쪽번호 계산) → 최종 PDF + 펼침면 미리보기.

사용법: python3 build.py [--preview]
"""
import html
import os
import re
import subprocess
import sys

from pypdf import PdfReader

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from toc import APPENDIX, AUTHOR, BOOK_SUBTITLE, BOOK_TITLE, FRONT, PARTS  # noqa: E402

CONTENT = os.path.join(ROOT, "content")
OUT = os.path.join(ROOT, "out")
NAVY = "#2f4f9a"
GRAY = "#8a93a6"


def read_section(sid):
    path = os.path.join(CONTENT, f"{sid}.md")
    if not os.path.exists(path):
        return None
    raw = open(path, encoding="utf-8").read()
    head, body = raw.split("\n---\n", 1)
    meta = dict(line.split(":", 1) for line in head.strip().splitlines())
    meta = {k.strip(): v.strip() for k, v in meta.items()}
    body = curly_quotes(body)
    body_html = subprocess.run(
        ["pandoc", "-f", "markdown+raw_html-implicit_figures-smart", "-t", "html5", "--wrap=none"],
        input=body, capture_output=True, text=True, check=True).stdout
    return meta, body_html


def curly_quotes(text):
    """한글 문장 속 곧은 따옴표를 짝 맞춘 둥근 따옴표로 바꾼다(HTML 태그·코드 블록 안은 제외)."""
    out = []
    for chunk in re.split(r"(<[^>]*>|```.*?```)", text, flags=re.S):
        if chunk.startswith("<") or chunk.startswith("```"):
            out.append(chunk)
            continue
        chunk = re.sub(r'"([^"\n]+)"', "\u201c\\1\u201d", chunk)
        chunk = re.sub(r"'([^'\n]+)'", "\u2018\\1\u2019", chunk)
        out.append(chunk)
    return "".join(out)


def two_line_title(t):
    if "|" in t:
        a, b = t.split("|", 1)
        return f"{html.escape(a)}<b>{html.escape(b)}</b>"
    return f"<b>{html.escape(t)}</b>"


def part_page_rules():
    rules = []
    groups = [(f"p{n}", f"PART {n}", name, str(n)) for n, name, _ in PARTS]
    groups.append(("pa", "별첨", "별첨", "+"))
    for page, label, name, tab in groups:
        tab_style = (f'content: "{tab}"; background: {NAVY}; color: #fff; font: 700 9pt "Noto Sans CJK KR"; '
                     "text-align: center; vertical-align: middle; height: 16mm; width: 6mm;")
        rules.append(
            f'@page {page}:left {{ @bottom-left {{ content: counter(page) "   {BOOK_TITLE}"; '
            f'font: 8pt "Noto Sans CJK KR"; color: {GRAY}; }} '
            f'@left-middle {{ {tab_style} margin-right: 10mm; }} }}')
        rules.append(
            f'@page {page}:right {{ @bottom-right {{ content: "{label}  {name}   " counter(page); '
            f'font: 8pt "Noto Sans CJK KR"; color: {GRAY}; }} '
            f'@right-middle {{ {tab_style} margin-left: 10mm; }} }}')
    return "\n".join(rules)


def toc_html(pages):
    def row(sid, title, detail="", cls=""):
        p = pages.get(sid)
        todo = "" if os.path.exists(os.path.join(CONTENT, f"{sid}.md")) else " todo"
        small = f"<small>{html.escape(detail)}</small>" if detail else ""
        num = f'<span class="p">{p}</span>' if p else '<span class="p"></span>'
        return (f'<div class="row {cls}{todo}"><span class="t">{html.escape(title)}{small}</span>'
                f'<span class="lead"></span>{num}</div>')

    out = ['<section class="toc"><div class="toc-title">차례</div>']
    for sid, title in FRONT:
        out.append(row(sid, title, cls="front"))
    for n, name, secs in PARTS:
        out.append(f'<div class="part"><span class="pill">PART {n}</span>'
                   f'<span class="name">{html.escape(name)}</span><span class="line"></span></div>')
        for sid, title, detail in secs:
            out.append(row(sid, title, detail))
    out.append('<div class="part"><span class="pill">별첨</span><span class="name">부록</span>'
               '<span class="line"></span></div>')
    for sid, title, detail in APPENDIX:
        out.append(row(sid, title, detail))
    out.append("</section>")
    return "\n".join(out)


def section_html(sid, page_name, only):
    got = read_section(sid)
    if not got:
        return ""
    meta, body = got
    return (f'<section class="section" id="s-{sid}" style="page:{page_name}">'
            f'<div class="opener"><h1>{two_line_title(meta["title"])}</h1>'
            f'<div class="band">{html.escape(meta.get("band", ""))}</div></div>'
            f'{body}</section>')


def build_html(pages, only_written=True):
    css = open(os.path.join(ROOT, "style.css"), encoding="utf-8").read()
    css = css.replace("PART_PAGE_RULES", part_page_rules())
    parts = [f"<!doctype html><html lang='ko'><head><meta charset='utf-8'><title>{BOOK_TITLE}</title>"
             f"<style>{css}</style></head><body>"]
    parts.append(f'<section class="cover"><div class="eyebrow">MONEY TEXTBOOK</div>'
                 f'<h1>{html.escape(BOOK_TITLE)}</h1><div class="bar"></div>'
                 f'<div class="sub">{html.escape(BOOK_SUBTITLE)}</div>'
                 f'<div class="author">{html.escape(AUTHOR)}</div></section>')
    parts.append(toc_html(pages))
    pro = read_section("prologue")
    if pro:
        meta, body = pro
        parts.append(f'<section class="prologue" id="s-prologue"><div class="kicker">PROLOGUE</div>'
                     f'<h1>{two_line_title(meta["title"])}</h1>{body}</section>')
    for n, name, secs in PARTS:
        written = [s for s in secs if os.path.exists(os.path.join(CONTENT, f"{s[0]}.md"))]
        if only_written and not written:
            continue
        lis = "".join(f"<li><span>{i+1:02d}</span>{html.escape(t)}</li>" for i, (_, t, _) in enumerate(secs))
        parts.append(f'<section class="part-open" id="s-part{n}"><div class="num">PART<b>{n}</b></div>'
                     f'<h2>{html.escape(name)}</h2><ul>{lis}</ul></section>')
        for sid, _, _ in secs:
            parts.append(section_html(sid, f"p{n}", only_written))
    if any(os.path.exists(os.path.join(CONTENT, f"{s}.md")) for s, _, _ in APPENDIX):
        lis = "".join(f"<li><span>{i+1:02d}</span>{html.escape(t)}</li>" for i, (_, t, _) in enumerate(APPENDIX))
        parts.append(f'<section class="part-open"><div class="num">APPENDIX<b>+</b></div>'
                     f'<h2>별첨</h2><ul>{lis}</ul></section>')
        for sid, _, _ in APPENDIX:
            parts.append(section_html(sid, "pa", only_written))
    parts.append("</body></html>")
    return "\n".join(parts)


def render(html_path, pdf_path):
    subprocess.run(["node", os.path.join(ROOT, "print.js"), html_path, pdf_path], check=True,
                   env={**os.environ, "NODE_PATH": subprocess.run(["npm", "root", "-g"], capture_output=True,
                                                                   text=True).stdout.strip()})


def find_pages(pdf_path):
    """각 섹션 첫 페이지를 띠(band) 문구나 제목으로 찾아 쪽번호 매핑."""
    reader = PdfReader(pdf_path)
    texts = [re.sub(r"\s+", "", (pg.extract_text() or "")) for pg in reader.pages]
    pages = {}
    keys = [(sid, None) for sid, _ in FRONT]
    for _, _, secs in PARTS:
        keys += [(s, None) for s, _, _ in secs]
    keys += [(s, None) for s, _, _ in APPENDIX]
    start = 2  # 표지·차례 이후부터 검색
    for sid, _ in keys:
        got = read_section(sid)
        if not got:
            continue
        meta, _ = got
        needle = re.sub(r"\s+", "", meta.get("band") or meta["title"].replace("|", ""))
        for i in range(start, len(texts)):
            if needle and needle in texts[i]:
                pages[sid] = i + 1
                start = i
                break
    return pages


def main():
    os.makedirs(OUT, exist_ok=True)
    html_path = os.path.join(OUT, "book.html")
    pdf_path = os.path.join(OUT, "book.pdf")
    pages = {}
    for _ in range(2):  # 1차: 쪽번호 계산, 2차: 차례에 반영
        open(html_path, "w", encoding="utf-8").write(build_html(pages))
        render(html_path, pdf_path)
        pages = find_pages(pdf_path)
    open(html_path, "w", encoding="utf-8").write(build_html(pages))
    render(html_path, pdf_path)
    print("pages:", pages, "total:", len(PdfReader(pdf_path).pages))
    if "--preview" in sys.argv:
        subprocess.run(["python3", os.path.join(ROOT, "spreads.py"), pdf_path, os.path.join(OUT, "preview")], check=True)


if __name__ == "__main__":
    main()
