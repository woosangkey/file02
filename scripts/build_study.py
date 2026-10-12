"""Render the 365-day bond study programme: daily lesson PDFs and the curriculum proposal."""
import glob, json, os, re, sys
from collections import Counter
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
                                PageBreak, NextPageTemplate, CondPageBreak, KeepTogether, Flowable)

sys.path.insert(0, os.path.dirname(__file__))
import build
build.CHART_H = 2.6
from build import styles, fmt, render_block, PAGE_W, PAGE_H, MARGIN  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..", "study")
NAVY, TEAL, GOLD = "#12355b", "#1b7f79", "#b8892b"
PROGRAM = "채권투자 365일 학습 과정"
TYPE_NAME = {"L": "학습일", "D": "실전 드릴", "R": "주간 복습"}
TYPE_COLOR = {"학습일": "#1b7f79", "실전 드릴": "#b8541b", "주간 복습": "#5b3f8f"}
LEVEL_COLOR = {"입문·중급": "#2e7d5b", "중급": "#2e6b4f", "상급": "#1f4e79", "하이엔드": "#8a1c3b"}

S = styles(NAVY)
S["h1"].fontSize = 13.5; S["h1"].leading = 19; S["h1"].spaceAfter = 6
S["body"].fontSize = 10; S["body"].leading = 16; S["body"].spaceAfter = 5
S["bullet"].fontSize = 10; S["bullet"].leading = 15.4; S["bullet"].spaceAfter = 2
S["callb"].fontSize = 9.1; S["callb"].leading = 13.8
S["cell"].fontSize = 8.2; S["cell"].leading = 11
S["q"] = ParagraphStyle("q", parent=S["body"], fontName="NanumB", spaceAfter=2)
S["small"] = ParagraphStyle("small", fontName="Nanum", fontSize=8.2, leading=11.5, textColor=colors.HexColor("#555555"), wordWrap="CJK")
AVAIL = PAGE_W - 2 * MARGIN


class NoteLines(Flowable):
    def __init__(self, w, h): super().__init__(); self.w, self.h = w, h
    def wrap(self, *a): return (self.w, self.h)
    def draw(self):
        c = self.canv; c.setStrokeColor(colors.HexColor("#c9d1da")); c.setLineWidth(0.5)
        y = self.h
        while y > 0:
            c.line(0, y, self.w, y); y -= 9 * mm


def box(flows, bg, line=None, pad=10):
    t = Table([[flows]], colWidths=[AVAIL])
    st = [("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg)), ("LEFTPADDING", (0, 0), (-1, -1), pad),
          ("RIGHTPADDING", (0, 0), (-1, -1), pad), ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]
    if line:
        st.append(("LINEABOVE", (0, 0), (-1, 0), 2, colors.HexColor(line)))
    t.setStyle(TableStyle(st)); return t


def badge(text, color, w=26):
    b = Table([[Paragraph(text, ParagraphStyle("b", fontName="NanumB", fontSize=8.3, textColor=colors.white, alignment=TA_CENTER))]], colWidths=[w * mm])
    b.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(color)), ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    return b


def load_syllabus():
    months = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "syllabus", "m*.json"))):
        d = json.load(open(f, encoding="utf-8")); months[d["month"]] = d
    return months


# ---------------------------------------------------------------- daily lesson
def build_day(path, months, cfg=None):
    """cfg: None for the 365-day programme, or dict(program, total, digits, out_dir, unit) for another course."""
    cfg = cfg or {"program": PROGRAM, "total": 365, "digits": 3, "out_dir": os.path.join(ROOT, "pdf"), "unit": "월"}
    program, total, nd = cfg["program"], cfg["total"], cfg["digits"]
    d = json.load(open(path, encoding="utf-8"))
    day, typ = int(d["day"]), d["type"]
    mon = months.get(d["month"], {})
    tc = TYPE_COLOR.get(typ, TEAL)
    out = os.path.join(cfg["out_dir"], f"Day{day:0{nd}d}.pdf")
    unit = f"{d['month']}{cfg['unit']}"

    def page(c, doc):
        c.saveState()
        c.setFillColor(colors.HexColor(NAVY)); c.rect(0, PAGE_H - 11 * mm, PAGE_W, 11 * mm, fill=1, stroke=0)
        c.setFillColor(colors.white); c.setFont("NanumB", 8.5)
        c.drawString(MARGIN, PAGE_H - 7 * mm, f"{program}  ·  DAY {day:0{nd}d} / {total}")
        c.setFont("Nanum", 8.5); c.drawRightString(PAGE_W - MARGIN, PAGE_H - 7 * mm, f"{unit}  {mon.get('title', '')}")
        # progress bar
        c.setFillColor(colors.HexColor("#e3e8ee")); c.rect(MARGIN, 11 * mm, AVAIL, 1.6 * mm, fill=1, stroke=0)
        c.setFillColor(colors.HexColor(GOLD)); c.rect(MARGIN, 11 * mm, AVAIL * day / total, 1.6 * mm, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#777777")); c.setFont("Nanum", 7.5)
        c.drawString(MARGIN, 7 * mm, f"과정 진도 {day / total * 100:.1f}%")
        c.drawRightString(PAGE_W - MARGIN, 7 * mm, f"{doc.page}")
        c.restoreState()

    doc = BaseDocTemplate(out, pagesize=(PAGE_W, PAGE_H), leftMargin=MARGIN, rightMargin=MARGIN, topMargin=18 * mm, bottomMargin=18 * mm,
                          title=f"Day {day:0{nd}d} {d['title']}", author=program)
    doc.addPageTemplates([PageTemplate("p", frames=[Frame(MARGIN, 16 * mm, AVAIL, PAGE_H - 33 * mm)], onPage=page)])
    st = []
    head = Table([[Paragraph(f"DAY<br/><font size=30>{day:0{nd}d}</font>", ParagraphStyle("dn", fontName="NanumEB", fontSize=11, leading=30, textColor=colors.white, alignment=TA_CENTER)),
                   [Paragraph(typ, ParagraphStyle("ty", fontName="NanumB", fontSize=10, textColor=colors.HexColor(tc), leading=14)),
                    Paragraph(fmt(d["title"]), ParagraphStyle("tt", fontName="NanumEB", fontSize=18, leading=24, textColor=colors.HexColor(NAVY), wordWrap="CJK")),
                    Paragraph(f"{unit} · {fmt(mon.get('title', ''))} · {mon.get('level', '')}  |  예상 학습시간 {fmt(d.get('time', ''))}", S["small"])]]],
                 colWidths=[30 * mm, AVAIL - 30 * mm])
    head.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, 0), colors.HexColor(tc)), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                              ("LEFTPADDING", (1, 0), (1, 0), 12), ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 10)]))
    st += [head, Spacer(1, 10)]
    st.append(box([Paragraph("오늘의 목표", S["callt"])] + [Paragraph(fmt(o), S["bullet"], bulletText="●") for o in d["objectives"]], "#eef3f6", NAVY))
    st.append(Spacer(1, 8))
    if d.get("warmup"):
        w = [Paragraph("워밍업 — 지난 내용 점검 (정답은 마지막 쪽)", S["callt"])] + \
            [Paragraph(f"W{i}. {fmt(q['q'])}", S["callb"]) for i, q in enumerate(d["warmup"], 1)]
        st += [box(w, "#fbf8ef", GOLD), Spacer(1, 10)]
    for k, sec in enumerate(d["sections"], 1):
        h = re.sub(r"^\s*([A-Z]\.|\d+[.)])\s*", "", sec["heading"]) if not re.match(r"^[A-D]\.", sec["heading"]) else sec["heading"]
        st += [CondPageBreak(35 * mm), Paragraph(f"{k}.&nbsp;&nbsp;{fmt(h)}", S["h1"])]
        for b in sec["blocks"]:
            st += render_block(b, S, NAVY, AVAIL)
    st.append(CondPageBreak(60 * mm))
    st.append(box([Paragraph("오늘의 핵심 정리", ParagraphStyle("kt", parent=S["callt"], textColor=colors.white))] +
                  [Paragraph(fmt(t), ParagraphStyle("kb", parent=S["bullet"], textColor=colors.white), bulletText="▶") for t in d["takeaways"]], NAVY))
    st.append(Spacer(1, 10))
    if d.get("practice"):
        st.append(Paragraph("연습문제", S["h1"]))
        for i, q in enumerate(d["practice"], 1):
            st.append(Paragraph(f"P{i}. {fmt(q['q'])}", S["body"]))
    if d.get("glossary"):
        st += render_block({"type": "table", "header": ["오늘의 용어", "정의"], "widths": [1, 3.2], "rows": d["glossary"]}, S, TEAL, AVAIL)
    st += [PageBreak(), Paragraph("정답과 해설", S["h1"])]
    for i, q in enumerate(d.get("warmup", []), 1):
        st.append(Paragraph(f"W{i}. {fmt(q['a'])}", S["body"]))
    for i, q in enumerate(d.get("practice", []), 1):
        st += [Paragraph(f"P{i}.", S["q"]), Paragraph(fmt(q["a"]), S["callb"]), Spacer(1, 6)]
    if d.get("tomorrow"):
        st += [Spacer(1, 6), box([Paragraph("내일 예고", S["callt"]), Paragraph(fmt(d["tomorrow"]), S["callb"])], "#eef3f6", TEAL)]
    log = Table([["학습일", "소요시간", "이해도", "다시 볼 부분"], ["      /      ", "        분", "□ □ □ □ □", ""]],
                colWidths=[AVAIL * 0.18, AVAIL * 0.18, AVAIL * 0.22, AVAIL * 0.42], rowHeights=[16, 26])
    log.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, 0), "NanumB"), ("FONTNAME", (0, 1), (-1, 1), "Nanum"), ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                             ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b0b8c0")), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef3f6")),
                             ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (0, 0), (-2, -1), "CENTER")]))
    st += [Spacer(1, 12), Paragraph("학습 기록", S["h2"]), log]
    st += [PageBreak(), Paragraph("나의 정리 노트", S["h1"]),
           Paragraph("오늘 배운 내용을 교재를 보지 않고 자신의 말로 정리해 보자. 핵심 공식 1개, 고객에게 설명할 문장 1개, 아직 헷갈리는 점 1개를 꼭 적는다.", S["small"]),
           Spacer(1, 8), NoteLines(AVAIL, PAGE_H - 70 * mm)]
    doc.build(st)
    return out, doc.page


# ---------------------------------------------------------------- proposal
def build_proposal(months, samples):
    out = os.path.join(ROOT, "채권투자_365일_학습과정_제안서.pdf")
    all_days = [x for m in sorted(months) for x in months[m]["days"]]

    def cover(c, doc):
        c.saveState()
        c.setFillColor(colors.HexColor(NAVY)); c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        # 365 dot calendar
        cell = 6.2 * mm; x0 = MARGIN; y0 = PAGE_H * 0.12
        for i, dd in enumerate(all_days or [{"type": "L"}] * 365):
            col, row = i // 7, i % 7
            x = x0 + col * (AVAIL / 53); y = y0 + (6 - row) * cell * 0.62
            c.setFillColor(colors.HexColor({"L": "#2a9d8f", "D": GOLD, "R": "#8e7cc3"}[dd["type"]])); c.setFillAlpha(0.85)
            c.circle(x + 1.2 * mm, y, 1.15 * mm, fill=1, stroke=0)
        c.setFillAlpha(1)
        c.setFillColor(colors.HexColor(GOLD)); c.setFont("NanumB", 11)
        c.drawString(MARGIN, PAGE_H - 32 * mm, "CURRICULUM PROPOSAL  ·  FIXED INCOME 365")
        c.setFillColor(colors.white); c.setFont("NanumEB", 34)
        c.drawString(MARGIN, PAGE_H * 0.68, "채권투자 365일")
        c.drawString(MARGIN, PAGE_H * 0.68 - 46, "학습 과정 제안서")
        c.setFont("Nanum", 13.5)
        c.drawString(MARGIN, PAGE_H * 0.68 - 82, "하루 10쪽 × 365일 — 입문·중급에서 하이엔드 판매자까지")
        c.setFont("Nanum", 9); c.setFillColor(colors.HexColor("#c9d3e0"))
        c.drawString(MARGIN, y0 + 7 * cell * 0.62 + 4 * mm, "● 학습일 261일    ● 실전 드릴 52일    ● 주간 복습 52일   (점 하나 = 하루)")
        c.setFillColor(colors.white); c.setFont("Nanum", 9.5)
        c.drawString(MARGIN, 18 * mm, "2026년 10월 · 교육·연수용 과정 설계안")
        c.restoreState()

    def page(c, doc):
        c.saveState()
        c.setStrokeColor(colors.HexColor(GOLD)); c.setLineWidth(0.8); c.line(MARGIN, PAGE_H - 13 * mm, PAGE_W - MARGIN, PAGE_H - 13 * mm)
        c.setFont("NanumB", 8); c.setFillColor(colors.HexColor(NAVY)); c.drawString(MARGIN, PAGE_H - 11.5 * mm, PROGRAM + " 제안서")
        c.setFont("Nanum", 8); c.setFillColor(colors.HexColor("#777777")); c.drawRightString(PAGE_W - MARGIN, 10 * mm, str(doc.page))
        c.restoreState()

    doc = BaseDocTemplate(out, pagesize=(PAGE_W, PAGE_H), leftMargin=MARGIN, rightMargin=MARGIN, topMargin=20 * mm, bottomMargin=18 * mm,
                          title=f"{PROGRAM} 제안서", author=PROGRAM)
    fr = Frame(MARGIN, 16 * mm, AVAIL, PAGE_H - 36 * mm)
    doc.addPageTemplates([PageTemplate("cover", frames=[fr], onPage=cover), PageTemplate("body", frames=[fr], onPage=page)])
    st = [NextPageTemplate("body"), PageBreak()]
    R = lambda b, color=NAVY: render_block(b, S, color, AVAIL)

    cnt = Counter(x["type"] for x in all_days)
    st.append(Paragraph("제안 요약", S["h1"]))
    for t in [
        f"**목표**: 1년 동안 매일 A4 10쪽 분량의 교재로 채권 투자를 체계적으로 학습해, 입문·중급(시장·계산) → 상급(신용·운용·구조화·해외·파생) → **하이엔드 판매자**(고객 솔루션·상담·규제) 수준에 도달한다.",
        f"**규모**: 365일 × 10쪽 = **약 3,650쪽**. 학습일 {cnt['L']}일, 실전 드릴 {cnt['D']}일, 주간 복습 {cnt['R']}일. 하루 학습시간 약 90~100분.",
        "**리듬**: 월~금 새 개념 학습, 토요일 계산·케이스 드릴, 일요일 주간 복습과 모의테스트. 매달 월말 과제, 분기마다 종합 모의고사.",
        "**산출물**: 매일 1편의 PDF 교재(목표·워밍업·본문·예제·연습문제·정답·용어·학습기록), 월별 합본, 연간 진도표.",
        "**검증된 제작 방식**: 앞서 제작한 112쪽 「채권투자 실무 가이드」와 같은 파이프라인으로 제작한다. 이 제안서에는 Day 1(학습일)과 Day 6(실전 드릴) 샘플 교재를 함께 첨부했다.",
    ]:
        st.append(Paragraph(fmt(t), S["bullet"], bulletText="■"))
    st.append(Spacer(1, 6))

    st.append(Paragraph("1. 과정 설계", S["h1"]))
    st.append(Paragraph(fmt("교재 한 권을 처음부터 끝까지 읽는 방식은 분량이 커질수록 중도 이탈이 많다. 이 과정은 **하루 단위로 완결되는 10쪽 교재**를 매일 제공하고, 주 단위로 드릴과 복습을 강제 배치해 「배우고 → 풀고 → 되돌아보는」 순환을 52번 반복하도록 설계했다. 난이도는 월 단위로 올라가며, 앞 달의 계산 도구(가격·듀레이션·스프레드)가 다음 달의 분석과 판매 실무에 계속 재사용되도록 주제 순서를 배치했다."), S["body"]))
    st += R({"type": "table", "header": ["요일", "유형", "내용", "분량·시간"], "widths": [0.8, 1, 3.4, 1.2], "rows": [
        ["월~금", "학습일 (L)", "새 개념 1개를 깊게: 목표 → 워밍업 → 본문 5~6섹션 → 예제 → 연습문제 8개 → 정답 → 정리 노트", "10쪽 · 약 90분"],
        ["토", "실전 드릴 (D)", "그 주 내용으로 개념 20제 + 계산 10제 + 케이스 2개 + 시장 데이터 해석", "10쪽 · 약 100분"],
        ["일", "주간 복습 (R)", "요약 노트, 공식 카드, 모의테스트 20문항, 오답노트 가이드, 다음 주 예고", "10쪽 · 약 80분"],
    ], "caption": "표 1. 주간 학습 리듬"})
    st += R({"type": "table", "header": ["순서", "구성 요소", "쪽수", "역할"], "widths": [0.6, 1.6, 0.7, 3.4], "rows": [
        ["1", "헤더·오늘의 목표·워밍업", "0.5", "어제 내용 2문항 인출 연습으로 기억 고정"],
        ["2", "본문 (5~6섹션)", "5", "개념 설명, 표·차트, 수식, 「예제」 단계별 계산, 「실무 팁」"],
        ["3", "핵심 정리·연습문제", "1.5", "5줄 요약과 8문항(개념·계산·사례 혼합)"],
        ["4", "오늘의 용어", "0.5", "용어 8~10개, 연간 누적 용어집으로 합본"],
        ["5", "정답과 해설·내일 예고·학습 기록", "1.5", "계산 과정 전체 공개, 이해도 자가평가"],
        ["6", "나의 정리 노트", "1", "교재 없이 스스로 요약하는 필기면(인출 학습)"],
    ], "caption": "표 2. 학습일 10쪽 구성 템플릿"})

    st += [CondPageBreak(80 * mm), Paragraph("2. 연간 로드맵", S["h1"])]
    rows = []
    for m in sorted(months):
        mo = months[m]; ds = mo["days"]; c = Counter(x["type"] for x in ds)
        rows.append([f"{m}월", fmt(mo["title"]), mo.get("level", ""), f"Day {ds[0]['day']}–{ds[-1]['day']}", f"{c['L']} / {c['D']} / {c['R']}"])
    st += R({"type": "table", "header": ["월", "주제", "수준", "범위", "학습/드릴/복습"], "widths": [0.6, 3, 1, 1.3, 1.3], "rows": rows,
             "caption": "표 3. 12개월 로드맵"})
    if months:
        ms = sorted(months)
        st += R({"type": "chart", "kind": "stacked", "title": "월별 학습일 구성", "x": [f"{m}월" for m in ms],
                 "series": {k: [sum(1 for x in months[m]["days"] if x["type"] == t) for m in ms] for t, k in TYPE_NAME.items()},
                 "ylabel": "일수", "caption": "그림 1. 월별 학습일·드릴·복습 일수"})
    st += R({"type": "table", "header": ["분기", "단계", "도달 수준"], "widths": [0.8, 1.6, 4], "rows": [
        ["1분기 (1~3월)", "기초 체력", "시장 구조와 상품을 설명하고, 가격·수익률·세후수익률·듀레이션을 손과 엑셀로 계산한다."],
        ["2분기 (4~6월)", "분석가", "금리 전망 논리를 세우고, 발행사 재무를 분석해 등급·스프레드의 적정성을 판단한다."],
        ["3분기 (7~9월)", "운용가", "캐리·커브·상대가치 전략을 설계하고 구조화·해외채권의 리스크를 분해한다."],
        ["4분기 (10~12월)", "하이엔드 판매자", "파생으로 헤지하고, 고객별 솔루션과 제안서를 만들며, 규제를 지키는 판매·사후관리를 수행한다."],
    ], "caption": "표 4. 분기별 성장 단계"}, TEAL)

    st += [CondPageBreak(70 * mm), Paragraph("3. 평가와 수료", S["h1"])]
    st += R({"type": "table", "header": ["평가", "주기", "방식", "기준"], "widths": [1.2, 0.9, 3, 1.4], "rows": [
        ["주간 모의테스트", "매주 일요일", "20문항(개념 10·계산 10), 자가 채점", "80점 이상"],
        ["월말 과제", "매월", "월별 종합 과제(분석 리포트·엑셀 모델·상담 스크립트 등)", "체크리스트 충족"],
        ["분기 모의고사", "3·6·9월 말", "50문항 + 사례형 2문항", "70점 이상"],
        ["캡스톤", "12월", "모의 포트폴리오 운용 + 모의 고객 제안 발표 + 연간 종합고사", "3개 모두 통과"],
    ], "caption": "표 5. 평가 체계 (수료 기준 예시)"})

    st += [CondPageBreak(70 * mm), Paragraph("4. 제작·운영 방안", S["h1"])]
    st.append(Paragraph(fmt("교재는 일차별 원고(JSON)를 작성한 뒤 공통 렌더러로 PDF를 만든다. 디자인·용어·난이도가 365일 내내 일관되고, 오류를 발견하면 원고 한 곳만 고쳐 다시 출력하면 된다. 이 제안서와 샘플 교재 2편이 바로 그 방식으로 만들어졌다."), S["body"]))
    st += R({"type": "table", "header": ["단계", "내용", "산출물"], "widths": [1, 3.6, 1.8], "rows": [
        ["① 커리큘럼 확정", "본 제안서의 365일 일차별 주제·산출물 검토와 수정", "확정 강의계획서"],
        ["② 월 단위 배치 제작", "한 달 분량(28~31편)을 병렬로 작성하고, 계산 검산과 표기 점검 후 PDF로 출력", "일일 PDF 30편, 월별 합본"],
        ["③ 품질 점검", "샘플링 검수(계산·용어·중복), 깨진 글자 자동 점검, 월간 용어집 갱신", "점검 리포트"],
        ["④ 배포", "매일 1편 공개 또는 월초 일괄 제공, 진도표·누적 용어집 함께 제공", "배포 패키지"],
    ], "caption": "표 6. 제작 프로세스"})
    st += R({"type": "callout", "title": "제안 일정", "text":
             "1단계로 1월분(Day 1~31) 31편을 제작해 실제 학습 흐름을 검증하고, 이후 매월 한 달 분량씩 제작하는 방식을 권한다. 한 번에 12개월 전체를 만드는 것도 가능하지만, 1월분을 써 본 뒤 난이도·분량을 조정하는 편이 완성도가 높다."}, GOLD)
    st += R({"type": "callout", "title": "유의사항", "text":
             "교재의 시장 수치·기업은 예시 또는 가상이며, 세율·법령·거래소 명세는 개정될 수 있으므로 실제 업무 적용 전 최신 기준 확인이 필요하다. 본 과정은 교육 목적이며 특정 금융상품의 매수·매도를 권유하지 않는다."}, NAVY)

    if samples:
        st += [CondPageBreak(60 * mm), Paragraph("5. 샘플 교재", S["h1"])]
        st += R({"type": "table", "header": ["파일", "유형", "제목", "쪽수"], "widths": [1.2, 1, 3.6, 0.6],
                 "rows": [[os.path.basename(p), t, fmt(ti), str(n)] for p, t, ti, n in samples], "caption": "표 7. 첨부 샘플 교재"})

    st += [PageBreak(), Paragraph("6. 월별 상세 커리큘럼 (365일)", S["h1"])]
    for m in sorted(months):
        mo = months[m]
        if m > 1: st.append(PageBreak())
        lv = mo.get("level", "")
        st.append(Table([[badge(f"{m}월", NAVY, 14), badge(lv, LEVEL_COLOR.get(lv, NAVY), 22),
                          Paragraph(fmt(mo["title"]), ParagraphStyle("mt", fontName="NanumEB", fontSize=16, leading=20, textColor=colors.HexColor(NAVY)))]],
                        colWidths=[16 * mm, 24 * mm, AVAIL - 40 * mm], style=[("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
        st.append(Spacer(1, 6))
        st.append(box([Paragraph(fmt(mo["goal"]), S["callb"]), Spacer(1, 4)] +
                      [Paragraph(fmt(o), ParagraphStyle("ob", parent=S["bullet"], fontSize=8.8, leading=13), bulletText="√") for o in mo.get("outcomes", [])] +
                      [Spacer(1, 3), Paragraph(f"<b>월말 과제</b>  {fmt(mo.get('project', ''))}", S["callb"])], "#eef3f6", NAVY))
        st.append(Spacer(1, 6))
        hdr = [Paragraph(h, S["cellh"]) for h in ["Day", "유형", "제목", "주요 내용", "실습·산출물"]]
        rws = []
        for x in mo["days"]:
            rws.append([Paragraph(str(x["day"]), S["cell"]), Paragraph(TYPE_NAME[x["type"]], S["cell"]), Paragraph(f"<b>{fmt(x['title'])}</b>", S["cell"]),
                        Paragraph(fmt(" · ".join(x.get("topics", []))), S["cell"]), Paragraph(fmt(x.get("deliverable", "")), S["cell"])])
        cw = [AVAIL * w for w in (0.07, 0.10, 0.27, 0.32, 0.24)]
        t = Table([hdr] + rws, colWidths=cw, repeatRows=1)
        sty = [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(NAVY)), ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#c8cdd2")),
               ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)]
        for i, x in enumerate(mo["days"], 1):
            if x["type"] == "D": sty.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#fbf1e6")))
            if x["type"] == "R": sty.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#f0ecf7")))
        t.setStyle(TableStyle(sty)); st.append(t)
    doc.build(st)
    return out, doc.page


# ---------------------------------------------------------------- 30-day course
def build_course30():
    c30 = json.load(open(os.path.join(ROOT, "syllabus30.json"), encoding="utf-8"))
    days, weeks = c30["days"], {w["week"]: w for w in c30["weeks"]}
    out = os.path.join(ROOT, "채권투자_30일_집중과정_커리큘럼.pdf")
    dot = {"L": "#2a9d8f", "D": GOLD, "R": "#8e7cc3"}

    def cover(c, doc):
        c.saveState()
        c.setFillColor(colors.HexColor(NAVY)); c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        sz = 11 * mm
        for i, d in enumerate(days):
            x = MARGIN + (i % 7) * sz * 1.25; y = PAGE_H * 0.36 - (i // 7) * sz * 1.25
            c.setFillColor(colors.HexColor(dot[d["type"]])); c.roundRect(x, y, sz, sz, 2, fill=1, stroke=0)
            c.setFillColor(colors.white); c.setFont("NanumB", 9); c.drawCentredString(x + sz / 2, y + sz / 2 - 3, str(d["day"]))
        c.setFillColor(colors.HexColor(GOLD)); c.setFont("NanumB", 11)
        c.drawString(MARGIN, PAGE_H - 32 * mm, "CURRICULUM  ·  FIXED INCOME 30-DAY INTENSIVE")
        c.setFillColor(colors.white); c.setFont("NanumEB", 34)
        c.drawString(MARGIN, PAGE_H * 0.70, "채권투자 30일")
        c.drawString(MARGIN, PAGE_H * 0.70 - 46, "집중 과정 커리큘럼")
        c.setFont("Nanum", 13.5); c.drawString(MARGIN, PAGE_H * 0.70 - 82, "하루 10쪽 × 30일 — 기초 계산에서 하이엔드 판매자까지 한 바퀴")
        c.setFont("Nanum", 9); c.setFillColor(colors.HexColor("#c9d3e0"))
        c.drawString(MARGIN, PAGE_H * 0.36 + sz + 5 * mm, "■ 학습일   ■ 실전 드릴   ■ 복습·평가")
        c.setFillColor(colors.white); c.setFont("Nanum", 9.5)
        c.drawString(MARGIN, 18 * mm, "2026년 10월 · 「채권투자 365일 학습 과정」 압축판")
        c.restoreState()

    def page(c, doc):
        c.saveState()
        c.setStrokeColor(colors.HexColor(GOLD)); c.setLineWidth(0.8); c.line(MARGIN, PAGE_H - 13 * mm, PAGE_W - MARGIN, PAGE_H - 13 * mm)
        c.setFont("NanumB", 8); c.setFillColor(colors.HexColor(NAVY)); c.drawString(MARGIN, PAGE_H - 11.5 * mm, c30["title"] + " 커리큘럼")
        c.setFont("Nanum", 8); c.setFillColor(colors.HexColor("#777777")); c.drawRightString(PAGE_W - MARGIN, 10 * mm, str(doc.page))
        c.restoreState()

    doc = BaseDocTemplate(out, pagesize=(PAGE_W, PAGE_H), leftMargin=MARGIN, rightMargin=MARGIN, topMargin=20 * mm, bottomMargin=18 * mm,
                          title=c30["title"] + " 커리큘럼", author=PROGRAM)
    fr = Frame(MARGIN, 16 * mm, AVAIL, PAGE_H - 36 * mm)
    doc.addPageTemplates([PageTemplate("cover", frames=[fr], onPage=cover), PageTemplate("body", frames=[fr], onPage=page)])
    R = lambda b, color=NAVY: render_block(b, S, color, AVAIL)
    st = [NextPageTemplate("body"), PageBreak(), Paragraph("과정 요약", S["h1"])]
    st += [Paragraph(fmt(t), S["bullet"], bulletText="■") for t in c30["summary"]]
    st += [Spacer(1, 6), Paragraph("1. 학습 리듬과 하루 구성", S["h1"])]
    st += R({"type": "table", "header": ["요일", "유형", "내용", "분량·시간"], "widths": [0.8, 1, 3.4, 1.2], "rows": [
        ["1~5일차", "학습일", "핵심 개념 1개를 압축 학습: 목표 → 워밍업 → 본문 → 예제 → 연습문제 → 정답 → 정리 노트", "10쪽 · 약 120분"],
        ["6일차", "실전 드릴", "그 주 내용으로 개념·계산 문제와 케이스 스터디", "10쪽 · 약 120분"],
        ["7일차", "주간 복습", "요약 노트, 공식 카드, 모의테스트 20문항, 오답 정리", "10쪽 · 약 90분"],
    ], "caption": "표 1. 주간 리듬 (4주 반복 후 29~30일차 캡스톤·수료)"})
    st += R({"type": "table", "header": ["구성 요소", "쪽수", "역할"], "widths": [2, 0.7, 3.6], "rows": [
        ["헤더·오늘의 목표·워밍업", "0.5", "전날 내용 2문항 인출 연습"],
        ["본문 (5~6섹션)", "5", "개념, 표·차트, 수식, 단계별 「예제」, 「실무 팁」"],
        ["핵심 정리·연습문제·용어", "2", "5줄 요약, 연습 8문항, 용어 8~10개"],
        ["정답과 해설·내일 예고·학습 기록", "1.5", "계산 과정 전체 공개, 이해도 자가평가"],
        ["나의 정리 노트", "1", "교재 없이 스스로 요약하는 필기면"],
    ], "caption": "표 2. 하루 10쪽 구성 (365일 과정과 동일한 템플릿)"}, TEAL)

    st += [CondPageBreak(80 * mm), Paragraph("2. 4주 로드맵", S["h1"])]
    rows = []
    for w in c30["weeks"]:
        ds = [d for d in days if d["week"] == w["week"]]
        rows.append([f"{w['week']}주차" if w["week"] < 5 else "마무리", w["title"], w["level"], f"Day {ds[0]['day']}–{ds[-1]['day']}",
                     " · ".join(w["outcomes"])])
    st += R({"type": "table", "header": ["주차", "주제", "수준", "범위", "도달 목표"], "widths": [0.7, 1.9, 0.9, 0.9, 3.2], "rows": rows,
             "caption": "표 3. 주차별 로드맵"})
    st += R({"type": "table", "header": ["평가", "시점", "방식", "기준"], "widths": [1.2, 1, 3, 1.2], "rows": [
        ["주간 모의테스트", "7·14·21·28일차", "20문항(개념 10·계산 10), 자가 채점", "80점 이상"],
        ["주차별 산출물", "매 학습일", "엑셀 시트·리포트·스크립트 등 그날의 산출물", "제출 완료"],
        ["캡스톤", "29일차", "가상 고객 2명 대상 포트폴리오 구성과 제안서", "체크리스트 충족"],
        ["종합 모의고사", "30일차", "50문항 + 사례형 2문항", "70점 이상 수료"],
    ], "caption": "표 4. 평가와 수료 기준"})
    st += R({"type": "table", "header": ["구분", "30일 집중 과정", "365일 학습 과정"], "widths": [1, 2.6, 2.6], "rows": [
        ["분량", "300쪽 (10쪽 × 30일)", "약 3,650쪽 (10쪽 × 365일)"],
        ["깊이", "핵심 개념과 대표 계산·케이스 위주", "주제별 심화, 변형 문제, 엑셀 실습 다수"],
        ["추천 대상", "단기간에 전 범위를 파악해야 하는 실무자, 연수·온보딩", "채권 전문가·세일즈로 성장하려는 학습자"],
        ["활용법", "먼저 완주해 전체 지도를 잡는다", "30일 과정에서 약했던 주제를 대응 범위부터 심화"],
    ], "caption": "표 5. 30일 과정과 365일 과정 비교"}, TEAL)

    for w in c30["weeks"]:
        st += [PageBreak() if w["week"] == 1 else CondPageBreak(95 * mm)]
        if w["week"] == 1: st.append(Paragraph("3. 일차별 상세 커리큘럼", S["h1"]))
        lv = w["level"]
        st.append(Table([[badge(f"{w['week']}주차" if w["week"] < 5 else "마무리", NAVY, 16), badge(lv, LEVEL_COLOR.get(lv.split("→")[-1], NAVY), 24),
                          Paragraph(fmt(w["title"]), ParagraphStyle("wt", fontName="NanumEB", fontSize=14, leading=19, textColor=colors.HexColor(NAVY), wordWrap="CJK"))]],
                        colWidths=[18 * mm, 26 * mm, AVAIL - 44 * mm], style=[("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
        st += [Spacer(1, 5), box([Paragraph(fmt(w["goal"]), S["callb"])], "#eef3f6", NAVY), Spacer(1, 5)]
        hdr = [Paragraph(h, S["cellh"]) for h in ["Day", "유형", "제목", "주요 내용", "산출물", "365일 대응"]]
        rws, sty = [], [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(NAVY)), ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#c8cdd2")),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
        for i, d in enumerate([d for d in days if d["week"] == w["week"]], 1):
            rws.append([Paragraph(f"<b>{d['day']}</b>", S["cell"]), Paragraph(TYPE_NAME[d["type"]], S["cell"]), Paragraph(f"<b>{fmt(d['title'])}</b>", S["cell"]),
                        Paragraph("<br/>".join("· " + fmt(t) for t in d["topics"]), S["cell"]), Paragraph(fmt(d["deliverable"]), S["cell"]), Paragraph(fmt(d["ref"]), S["cell"])])
            if d["type"] == "D": sty.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#fbf1e6")))
            if d["type"] == "R": sty.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#f0ecf7")))
        t = Table([hdr] + rws, colWidths=[AVAIL * x for x in (0.06, 0.09, 0.2, 0.33, 0.18, 0.14)], repeatRows=1); t.setStyle(TableStyle(sty))
        st += [t, Spacer(1, 10)]

    st += [PageBreak(), Paragraph("4. 30일 진도 체크표", S["h1"]),
           Paragraph("매일 학습을 마치면 체크하고, 이해도가 3 이하인 날은 「365일 대응」 범위를 보충 학습 목록에 적는다.", S["small"]), Spacer(1, 6)]
    rows = [["Day", "제목", "완료", "이해도(1~5)", "산출물", "보충 필요"]]
    for d in days:
        rows.append([str(d["day"]), Paragraph(fmt(d["title"]), S["cell"]), "□", "1  2  3  4  5", "□", "□"])
    t = Table(rows, colWidths=[AVAIL * x for x in (0.07, 0.48, 0.08, 0.17, 0.1, 0.1)], repeatRows=1, rowHeights=[16] + [19.5] * len(days))
    t.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, 0), "NanumB"), ("FONTNAME", (0, 1), (-1, -1), "Nanum"), ("FONTSIZE", (0, 0), (-1, -1), 8.3),
                           ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(NAVY)),
                           ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#c8cdd2")), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("ALIGN", (0, 0), (0, -1), "CENTER"), ("ALIGN", (2, 0), (-1, -1), "CENTER")] +
                          [("BACKGROUND", (0, i), (-1, i), colors.HexColor("#f3f5f7")) for i in range(2, len(rows), 2)]))
    st.append(t)
    st += [Spacer(1, 10)] + R({"type": "callout", "title": "유의사항", "text":
        "교재의 시장 수치·기업은 예시 또는 가상이며, 세율·법령·거래소 명세는 개정될 수 있으므로 실제 업무 적용 전 최신 기준 확인이 필요하다. 본 과정은 교육 목적이며 특정 금융상품의 매수·매도를 권유하지 않는다."}, GOLD)[:-1]
    doc.build(st)
    return out, doc.page


def build_week30(week):
    """Render 30-day course daily lessons for one week, plus a bound weekly volume with a cover."""
    c30 = json.load(open(os.path.join(ROOT, "syllabus30.json"), encoding="utf-8"))
    weeks = {w["week"]: w for w in c30["weeks"]}
    base = os.path.join(ROOT, "..", "study30")
    cfg = {"program": c30["title"], "total": 30, "digits": 2, "out_dir": os.path.join(base, "pdf"), "unit": "주차"}
    os.makedirs(cfg["out_dir"], exist_ok=True)
    outs = []
    for x in [d for d in c30["days"] if d["week"] == week]:
        p = os.path.join(base, "days", f"day{x['day']:02d}.json")
        if not os.path.exists(p):
            print("missing", p); continue
        o, n = build_day(p, weeks, cfg); outs.append((o, x, n)); print(f"{n:3d} pages  {os.path.basename(o)}")
    w = weeks[week]
    cov = os.path.join(cfg["out_dir"], f"_cover_w{week}.pdf")

    def cover(c, doc):
        c.saveState()
        c.setFillColor(colors.HexColor(NAVY)); c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        c.setFillColor(colors.HexColor(GOLD)); c.setFont("NanumB", 11)
        c.drawString(MARGIN, PAGE_H - 32 * mm, f"FIXED INCOME 30-DAY INTENSIVE  ·  WEEK {week}")
        c.setFillColor(colors.white); c.setFont("NanumEB", 30)
        c.drawString(MARGIN, PAGE_H * 0.74, c30["title"])
        c.setFont("NanumEB", 22); c.drawString(MARGIN, PAGE_H * 0.74 - 40, f"{week}주차  {w['title']}")
        c.setFont("Nanum", 11); c.setFillColor(colors.HexColor("#c9d3e0"))
        c.drawString(MARGIN, PAGE_H * 0.74 - 64, f"수준 · {w['level']}    교재 {len(outs)}편 · {sum(n for _, _, n in outs)}쪽")
        y = PAGE_H * 0.52
        for o, x, n in outs:
            c.setFillColor(colors.HexColor({"L": "#2a9d8f", "D": GOLD, "R": "#8e7cc3"}[x["type"]]))
            c.roundRect(MARGIN, y - 4, 16 * mm, 9 * mm, 2, fill=1, stroke=0)
            c.setFillColor(colors.white); c.setFont("NanumB", 10); c.drawCentredString(MARGIN + 8 * mm, y + 2, f"DAY {x['day']:02d}")
            c.setFont("NanumB", 12); c.drawString(MARGIN + 20 * mm, y + 2, x["title"])
            c.setFont("Nanum", 8.5); c.setFillColor(colors.HexColor("#c9d3e0")); c.drawString(MARGIN + 20 * mm, y - 9, f"{TYPE_NAME[x['type']]} · 산출물: {x['deliverable']}")
            y -= 15 * mm
        p = Paragraph(fmt(w["goal"]), ParagraphStyle("g", fontName="Nanum", fontSize=10, leading=16, textColor=colors.HexColor("#d5dde8"), wordWrap="CJK"))
        _, h = p.wrap(AVAIL, 100); p.drawOn(c, MARGIN, 30 * mm)
        c.setFillColor(colors.white); c.setFont("Nanum", 9); c.drawString(MARGIN, 18 * mm, "교육·연수용 교재 | 투자 권유 아님 | 예시·가상 수치 포함")
        c.restoreState()

    doc = BaseDocTemplate(cov, pagesize=(PAGE_W, PAGE_H))
    doc.addPageTemplates([PageTemplate("c", frames=[Frame(0, 0, PAGE_W, PAGE_H)], onPage=cover)])
    doc.build([Spacer(1, 1)])
    from pypdf import PdfWriter
    wtr = PdfWriter(); wtr.append(cov); page = 1
    for o, x, n in outs:
        wtr.append(o, outline_item=f"DAY {x['day']:02d}  {x['title']}"); page += n
    bound = os.path.join(base, f"채권투자_30일과정_{week}주차_교재.pdf")
    wtr.write(bound); os.remove(cov)
    return bound, 1 + sum(n for _, _, n in outs)


if __name__ == "__main__":
    if "--week" in sys.argv:
        o, n = build_week30(int(sys.argv[sys.argv.index("--week") + 1])); print(f"{n:3d} pages  {os.path.basename(o)}"); sys.exit()
    if "--30" in sys.argv:
        o, n = build_course30(); print(f"{n:3d} pages  {os.path.basename(o)}"); sys.exit()
    months = load_syllabus()
    os.makedirs(os.path.join(ROOT, "pdf"), exist_ok=True)
    samples = []
    for p in sorted(glob.glob(os.path.join(ROOT, "days", "day*.json"))):
        o, n = build_day(p, months); d = json.load(open(p, encoding="utf-8"))
        samples.append((o, d["type"], d["title"], n)); print(f"{n:3d} pages  {os.path.basename(o)}")
    o, n = build_proposal(months, samples); print(f"{n:3d} pages  {os.path.basename(o)}")
