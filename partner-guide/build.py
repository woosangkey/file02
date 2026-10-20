#!/usr/bin/env python3
"""content/*.md → guide.pdf (A4). 2-pass로 차례 쪽번호 계산."""
import glob, html, os, re, subprocess
from pypdf import PdfReader
ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "out"); os.makedirs(OUT, exist_ok=True)
TITLE = "고액자산가 세무·재무 자문 연결 가이드"

def chapters():
    res = []
    for f in sorted(glob.glob(os.path.join(ROOT, "content", "*.md"))):
        md = open(f, encoding="utf-8").read()
        h1 = re.search(r"^# (.+)$", md, re.M).group(1).strip()
        lead = re.search(r'<p class="lead">(.*?)</p>', md)
        body = subprocess.run(["pandoc", "-f", "markdown+raw_html-implicit_figures", "-t", "html5", "--wrap=none"],
                              input=md, capture_output=True, text=True, check=True).stdout
        res.append((h1, lead.group(1) if lead else "", body))
    return res

def page_html(chs, pages):
    css = open(os.path.join(ROOT, "style.css"), encoding="utf-8").read()
    rows = "".join(
        f'<div class="row"><b>{html.escape(h.split(".")[0])}</b><span class="t">{html.escape(h.split(".",1)[1].strip())}'
        f'<small>{html.escape(l)}</small></span><span class="p">{pages.get(h, "")}</span></div>' for h, l, _ in chs)
    parts = [f"<!doctype html><html lang='ko'><head><meta charset='utf-8'><title>{TITLE}</title><style>{css}</style></head><body>",
             '<section class="cover"><div class="eyebrow">PARTNER REFERRAL GUIDE</div>'
             f'<h1>{TITLE}</h1><div class="sub">투자자문사 상담사를 위한 회계법인 더위즈 연계 서비스 이해와 고객 판별</div>'
             '<div class="bar"></div><div class="meta">기준일 2026년 10월<br>대상: 프리즘 제휴 투자자문 상담사<br>'
             '참고: 회계법인 더위즈 「자산가를 위한 세무·재무 자문 서비스」(2026.4)</div>'
             '<div class="conf">내부 교육용 자료입니다. 고객 배포용이 아니며, 본 자료의 세법 설명은 일반 정보로서 개별 사안의 세무 판단을 대신하지 않습니다. '
             '개별 사안은 반드시 세무 전문가의 검토를 받으십시오.</div></section>',
             f'<section class="toc"><h2>차례</h2>{rows}</section>']
    for h, _, body in chs:
        parts.append(f'<section class="chapter">{body}</section>')
    parts.append("</body></html>")
    return "\n".join(parts)

def render(src, pdf):
    env = {**os.environ, "NODE_PATH": subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip()}
    subprocess.run(["node", os.path.join(ROOT, "..", "money-book", "print.js"), src, pdf], check=True, env=env)

def find_pages(pdf, chs):
    texts = [re.sub(r"\s+", "", p.extract_text() or "") for p in PdfReader(pdf).pages]
    pages, start = {}, 2
    for h, _, _ in chs:
        key = re.sub(r"\s+", "", h)[:14]
        for i in range(start, len(texts)):
            if key in texts[i]:
                pages[h] = i + 1; start = i; break
    return pages

chs = chapters(); pages = {}
src, pdf = os.path.join(OUT, "guide.html"), os.path.join(OUT, "guide.pdf")
for _ in range(2):
    open(src, "w", encoding="utf-8").write(page_html(chs, pages)); render(src, pdf); pages = find_pages(pdf, chs)
open(src, "w", encoding="utf-8").write(page_html(chs, pages)); render(src, pdf)
print(pages, "total", len(PdfReader(pdf).pages))
