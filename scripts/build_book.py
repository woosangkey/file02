"""Render book/chapters/*.json into a single bond-investing handbook PDF."""
import json, os, re, sys
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
                                PageBreak, NextPageTemplate, Flowable, CondPageBreak)
from reportlab.platypus.tableofcontents import TableOfContents

sys.path.insert(0, os.path.dirname(__file__))
from build import styles, fmt, render_block, PAGE_W, PAGE_H, MARGIN  # noqa: E402  (registers fonts)

ROOT = os.path.join(os.path.dirname(__file__), "..")
NAVY, GOLD = "#13315c", "#b8892b"
TITLE = "채권투자 실무 가이드"
SUBTITLE = "중급에서 하이엔드 세일즈까지"
LEVEL_COLOR = {"중급": "#2e6b4f", "상급": "#1f4e79", "하이엔드": "#8a1c3b", "부록": "#555555"}
PARTS = [
    ("PART I", "중급 — 실무의 기초 체력", "시장 구조, 가격과 수익률, 금리 리스크 측정, 수익률곡선. 모든 판단의 바탕이 되는 계산과 언어를 몸에 익힌다.", [1, 2, 3, 4]),
    ("PART II", "상급 — 분석과 운용 전략", "신용분석, 액티브 전략, 구조화·특수 채권, 해외채권과 환헤지, 금리파생과 레포. 수익의 원천을 분해하고 리스크를 설계한다.", [5, 6, 7, 8, 9]),
    ("PART III", "하이엔드 — 판매자의 기술", "고객별 솔루션 설계, 상담과 클로징, 판매 규제와 사후관리. 지식을 고객의 결과로 바꾸는 단계다.", [10, 11, 12]),
]

S = styles(NAVY)
S["h1"].fontSize = 15; S["h1"].leading = 21
S["toc0"] = ParagraphStyle("toc0", fontName="NanumB", fontSize=11.5, leading=20, textColor=colors.HexColor(NAVY), spaceBefore=8)
S["toc1"] = ParagraphStyle("toc1", fontName="Nanum", fontSize=10, leading=17, leftIndent=14)
S["toc2"] = ParagraphStyle("toc2", fontName="Nanum", fontSize=8.8, leading=14, leftIndent=30, textColor=colors.HexColor("#555555"))
S["q"] = ParagraphStyle("q", parent=S["body"], fontName="NanumB", spaceAfter=3)


class Marker(Flowable):
    """Zero-size flowable carrying TOC / running-header info."""
    def __init__(self, toc=None, chapter=None, opener=False):
        super().__init__(); self.toc, self.chapter, self.opener = toc, chapter, opener
    def wrap(self, *a): return (0, 0)
    def draw(self): pass


class BookDoc(BaseDocTemplate):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.cur_chapter = ""; self.no_header = set()
    def afterFlowable(self, f):
        if isinstance(f, Marker):
            if f.chapter is not None: self.cur_chapter = f.chapter
            if f.opener: self.no_header.add(self.page)
            if f.toc:
                level, text = f.toc
                key = f"k{id(f)}"; self.canv.bookmarkPage(key)
                self.canv.addOutlineEntry(re.sub("<[^>]+>", "", text), key, level=level)
                self.notify("TOCEntry", (level, text, self.page, key))


def page_end(c, doc):
    if doc.page in doc.no_header: 
        _footer(c, doc); return
    c.saveState()
    c.setStrokeColor(colors.HexColor(GOLD)); c.setLineWidth(0.8)
    c.line(MARGIN, PAGE_H - 13 * mm, PAGE_W - MARGIN, PAGE_H - 13 * mm)
    c.setFont("NanumB", 8); c.setFillColor(colors.HexColor(NAVY))
    c.drawString(MARGIN, PAGE_H - 11.5 * mm, TITLE)
    c.setFont("Nanum", 8); c.setFillColor(colors.HexColor("#666666"))
    c.drawRightString(PAGE_W - MARGIN, PAGE_H - 11.5 * mm, doc.cur_chapter)
    c.restoreState(); _footer(c, doc)


def _footer(c, doc):
    c.saveState(); c.setFont("NanumB", 9); c.setFillColor(colors.HexColor(NAVY))
    (c.drawRightString if doc.page % 2 else c.drawString)(PAGE_W - MARGIN if doc.page % 2 else MARGIN, 10 * mm, str(doc.page))
    c.restoreState()


def cover(c, doc):
    c.saveState()
    c.setFillColor(colors.HexColor(NAVY)); c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    # stylised yield curves
    c.setStrokeColor(colors.HexColor(GOLD)); c.setLineWidth(1.4)
    import math
    for k in range(6):
        p = c.beginPath(); y0 = PAGE_H * 0.30 + k * 14
        for i in range(0, 101):
            x = PAGE_W * i / 100
            y = y0 + 90 * (1 - math.exp(-i / (18 + 6 * k))) - k * 4
            p.moveTo(x, y) if i == 0 else p.lineTo(x, y)
        c.setStrokeAlpha(0.9 - k * 0.13); c.drawPath(p)
    c.setStrokeAlpha(1)
    c.setFillColor(colors.HexColor(GOLD)); c.setFont("NanumB", 11)
    c.drawString(MARGIN, PAGE_H - 32 * mm, "PRACTITIONER'S HANDBOOK  ·  FIXED INCOME")
    c.setFillColor(colors.white); c.setFont("NanumSquareB" if False else "NanumEB", 38)
    c.drawString(MARGIN, PAGE_H * 0.70, "채권투자")
    c.drawString(MARGIN, PAGE_H * 0.70 - 50, "실무 가이드")
    c.setFont("Nanum", 15); c.drawString(MARGIN, PAGE_H * 0.70 - 88, SUBTITLE)
    c.setFont("Nanum", 10.5); c.setFillColor(colors.HexColor("#c9d3e0"))
    c.drawString(MARGIN, PAGE_H * 0.70 - 112, "가격·수익률 계산부터 신용분석, 운용 전략, 파생 헤지, 고객 솔루션과 판매 규제까지")
    c.setFillColor(colors.white); c.setFont("Nanum", 10)
    c.drawString(MARGIN, 26 * mm, "제1판 · 2026년 10월")
    c.drawString(MARGIN, 20 * mm, "교육·연수용 실무서 | 투자 권유 아님")
    c.restoreState()


def part_page(c, doc):
    c.saveState()
    c.setFillColor(colors.HexColor(NAVY)); c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(colors.HexColor(GOLD)); c.rect(MARGIN, PAGE_H * 0.62, 30 * mm, 2.2, fill=1, stroke=0)
    c.restoreState()


class PartText(Flowable):
    def __init__(self, label, title, desc, chapters):
        super().__init__(); self.args = (label, title, desc, chapters)
    def wrap(self, w, h): return (w, h - 1)
    def draw(self):
        label, title, desc, chapters = self.args
        c = self.canv; top = PAGE_H * 0.62 - 18 * mm  # frame origin is at bottom margin
        c.setFillColor(colors.HexColor(GOLD)); c.setFont("NanumB", 14); c.drawString(0, top + 20 * mm, label)
        c.setFillColor(colors.white); c.setFont("NanumEB", 26); c.drawString(0, top - 4 * mm, title)
        p = Paragraph(desc, ParagraphStyle("pd", fontName="Nanum", fontSize=11, leading=19, textColor=colors.HexColor("#d5dde8"), wordWrap="CJK"))
        w, h = p.wrap(PAGE_W - 2 * MARGIN - 20 * mm, 200); p.drawOn(c, 0, top - 18 * mm - h)
        y = top - 34 * mm - h
        c.setFont("Nanum", 11); c.setFillColor(colors.white)
        for no, t in chapters:
            c.drawString(0, y, f"제{no}장   {t}"); y -= 18


def chapter_opener(ch, avail):
    lv = ch.get("level", "중급"); lc = LEVEL_COLOR.get(lv, NAVY)
    label = "부록" if str(ch["no"]) == "A" else f"CHAPTER {int(ch['no']):02d}"
    out = [Marker(chapter=(ch["title"] if str(ch["no"]) == "A" else f"제{ch['no']}장  {ch['title']}"), opener=True),
           Marker(toc=(1, ch["title"] if str(ch["no"]) == "A" else f"제{ch['no']}장&nbsp;&nbsp;{fmt(ch['title'])}"))]
    out.append(Spacer(1, 18 * mm))
    out.append(Paragraph(label, ParagraphStyle("cl", fontName="NanumB", fontSize=12, textColor=colors.HexColor(GOLD), leading=16)))
    out.append(Spacer(1, 4))
    out.append(Paragraph(fmt(ch["title"]), ParagraphStyle("ct", fontName="NanumEB", fontSize=24, leading=32, textColor=colors.HexColor(NAVY), wordWrap="CJK")))
    badge = Table([[Paragraph(f"난이도 · {lv}", ParagraphStyle("b", fontName="NanumB", fontSize=8.5, textColor=colors.white, alignment=TA_CENTER))]], colWidths=[28 * mm])
    badge.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(lc)), ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    badge.hAlign = "LEFT"
    out += [Spacer(1, 8), badge, Spacer(1, 14)]
    if ch.get("objectives"):
        inner = [Paragraph("학습 목표", S["callt"])] + [Paragraph(fmt(o), S["bullet"], bulletText="✓") for o in ch["objectives"]]
        t = Table([[inner]], colWidths=[avail])
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eef2f7")),
                               ("LINEABOVE", (0, 0), (-1, 0), 2, colors.HexColor(NAVY)),
                               ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                               ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 10)]))
        out += [t, Spacer(1, 14)]
    return out


def chapter_end(ch, avail):
    out = []
    if ch.get("takeaways"):
        inner = [Paragraph("핵심 정리", ParagraphStyle("kt", parent=S["callt"], textColor=colors.white))] + \
                [Paragraph(fmt(t), ParagraphStyle("kb", parent=S["bullet"], textColor=colors.white), bulletText="▸") for t in ch["takeaways"]]
        t = Table([[inner]], colWidths=[avail])
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(NAVY)),
                               ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                               ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
        out += [CondPageBreak(60 * mm), Spacer(1, 10), t, Spacer(1, 12)]
    if ch.get("quiz"):
        out.append(Paragraph("점검 문제", S["h1"]))
        for i, q in enumerate(ch["quiz"], 1):
            out.append(Paragraph(f"Q{i}. {fmt(q['q'])}", S["q"]))
            out += render_block({"type": "callout", "title": "해설", "text": q["a"]}, S, GOLD, avail)
    return out


def front_matter(avail):
    out = [Paragraph("머리말", S["h1"])]
    for p in [
        "채권은 흔히 「안전한 자산」으로 소개되지만, 실무에서 채권을 다루는 사람에게 채권만큼 계산이 많고 맥락이 중요한 자산도 드물다. 같은 3년 만기 채권이라도 쿠폰, 신용, 옵션, 통화, 세금, 회계 처리에 따라 고객이 실제로 손에 쥐는 결과는 완전히 달라진다. 이 책은 그 차이를 숫자로 설명하고, 고객의 언어로 전달할 수 있는 실무자를 위해 쓰였다.",
        "책은 세 부분으로 이루어진다. **1부(중급)**는 시장 구조와 가격·수익률·듀레이션·수익률곡선을 다루며, 모든 판단의 바탕이 되는 계산을 손에 익히는 단계다. **2부(상급)**는 신용분석, 액티브 운용 전략, 구조화·특수 채권, 해외채권과 환헤지, 금리파생과 레포를 다룬다. 수익의 원천을 분해하고 리스크를 설계하는 단계다. **3부(하이엔드)**는 고객 유형별 솔루션 설계, 상담·제안·클로징, 판매 규제와 사후관리를 다룬다. 지식을 고객의 결과와 신뢰로 바꾸는 판매자의 기술이다.",
        "각 장은 학습 목표로 시작해 핵심 정리와 점검 문제로 끝난다. 본문 곳곳의 「실무 팁」「판매자 노트」「주의」 상자는 현장에서 자주 겪는 상황을 압축한 것이다. 부록에는 공식집, 용어사전, 종합 실전문제와 체크리스트를 실어 책상 옆에 두고 찾아볼 수 있게 했다.",
    ]:
        out.append(Paragraph(fmt(p), S["body"]))
    out += render_block({"type": "table", "header": ["구분", "대상 독자", "이 책에서 얻을 것"], "widths": [1, 2, 3], "rows": [
        ["중급", "입사 1~3년차 PB·RM, 채권에 관심 있는 개인 투자자", "가격·수익률·듀레이션 계산, 시장 데이터 읽기, 기본 상품 설명"],
        ["상급", "채권 운용역, 세일즈·트레이딩 실무자, 고액 자산가", "신용·커브·상대가치 분석, 구조화 상품과 헤지 설계"],
        ["하이엔드", "WM 센터 팀장, 기관·HNW 전담 세일즈", "고객별 솔루션, 제안서·상담 스크립트, 판매 규제 준수"],
    ], "caption": "이 책의 구성과 대상 독자"}, S, NAVY, avail)
    out += render_block({"type": "callout", "title": "일러두기", "text":
        "본문의 수치 중 「예시」「가상」으로 표기된 것은 이해를 돕기 위한 가정이며 실제 시장 데이터가 아니다. 등장하는 기업명은 모두 가상이다. 세율·법령·거래소 명세는 개정될 수 있으므로 실제 업무 전 최신 법령, 감독규정, 거래소 공시, 회사 내규를 반드시 확인해야 한다. 이 책은 교육·연수 목적의 자료이며 특정 금융상품의 매수·매도를 권유하지 않는다."}, S, GOLD, avail)
    return out


def build():
    chs = {}
    cdir = os.environ.get("CH_DIR", os.path.join(ROOT, "book", "chapters"))
    for f in sorted(os.listdir(cdir)):
        if f.endswith(".json"):
            d = json.load(open(os.path.join(cdir, f), encoding="utf-8"))
            chs[str(d["no"])] = d
    out = os.environ.get("OUT", os.path.join(ROOT, "book", "채권투자_실무가이드.pdf"))
    doc = BookDoc(out, pagesize=(PAGE_W, PAGE_H), leftMargin=MARGIN, rightMargin=MARGIN, topMargin=20 * mm,
                  bottomMargin=18 * mm, title=f"{TITLE} — {SUBTITLE}", author="Fixed Income Practice Notes")
    frame = Frame(MARGIN, 18 * mm, PAGE_W - 2 * MARGIN, PAGE_H - 38 * mm, id="f")
    doc.addPageTemplates([PageTemplate("cover", frames=[frame], onPage=cover),
                          PageTemplate("part", frames=[frame], onPage=part_page),
                          PageTemplate("body", frames=[frame], onPageEnd=page_end)])
    avail = PAGE_W - 2 * MARGIN
    toc = TableOfContents(); toc.levelStyles = [S["toc0"], S["toc1"], S["toc2"]]; toc.dotsMinLevel = 1
    story = [NextPageTemplate("body"), PageBreak(), Marker(chapter="", opener=True)]
    story += front_matter(avail)
    story += [PageBreak(), Marker(chapter="차례", opener=True), Paragraph("차례", S["h1"]), toc]
    for label, ptitle, desc, nos in PARTS:
        story += [NextPageTemplate("part"), PageBreak(), Marker(toc=(0, f"{label}&nbsp;&nbsp;{ptitle}"), opener=True),
                  PartText(label, ptitle, desc, [(n, chs[str(n)]["title"]) for n in nos if str(n) in chs]),
                  NextPageTemplate("body")]
        for n in nos:
            ch = chs.get(str(n))
            if not ch: continue
            story += [PageBreak()] + chapter_opener(ch, avail)
            for k, sec in enumerate(ch["sections"], 1):
                h = re.sub(r"^\s*\d+([.-]\d+)*[.)]?\s*", "", sec["heading"])
                story += [CondPageBreak(40 * mm), Marker(toc=(2, f"{n}.{k}&nbsp;&nbsp;{fmt(h)}")),
                          Paragraph(f"{n}.{k}&nbsp;&nbsp;{fmt(h)}", S["h1"])]
                for b in sec["blocks"]:
                    story += render_block(b, S, NAVY, avail)
            story += chapter_end(ch, avail)
    if "A" in chs:
        ch = chs["A"]
        story += [PageBreak(), Marker(toc=(0, "APPENDIX&nbsp;&nbsp;부록"))] + chapter_opener(ch, avail)
        for sec in ch["sections"]:
            h = re.sub(r"^\s*[A-Z\d]+([.-]\d+)*[.)]?\s*", "", sec["heading"])
            story += [CondPageBreak(40 * mm), Marker(toc=(2, fmt(h))), Paragraph(fmt(h), S["h1"])]
            for b in sec["blocks"]:
                story += render_block(b, S, NAVY, avail)
    doc.multiBuild(story)
    return out, doc.page


if __name__ == "__main__":
    o, n = build(); print(n, "pages", o)
