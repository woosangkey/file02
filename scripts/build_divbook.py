"""Typeset the monthly-dividend ETF book (divbook/units/*.json) in a Korean trade-book style."""
import json, os, re, sys, glob, math
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
                                PageBreak, NextPageTemplate, Flowable, CondPageBreak, KeepTogether)

sys.path.insert(0, os.path.dirname(__file__))
import build  # registers Nanum fonts, chart helper, fmt()
from build import fmt
import matplotlib.pyplot as plt

ROOT = os.path.join(os.path.dirname(__file__), "..", "divbook")
FD = "/usr/share/fonts/truetype/nanum"
for name, f in [("MJ", "NanumMyeongjo"), ("MJB", "NanumMyeongjoBold"), ("SR", "NanumSquareRoundR"),
                ("SRB", "NanumSquareRoundB"), ("SQB", "NanumSquareB"), ("SQ", "NanumSquareR")]:
    pdfmetrics.registerFont(TTFont(name, f"{FD}/{f}.ttf"))
registerFontFamily("MJ", normal="MJ", bold="MJB", italic="MJ", boldItalic="MJB")
registerFontFamily("SR", normal="SR", bold="SRB", italic="SR", boldItalic="SRB")
registerFontFamily("SQ", normal="SQ", bold="SQB", italic="SQ", boldItalic="SQB")

W, H = 176 * mm, 248 * mm                      # 크라운판
ML, MR, MT, MB = 17 * mm, 17 * mm, 19 * mm, 19 * mm
AV = W - ML - MR
IVORY, TEAL, DTEAL, ORANGE, RED, INK, GRAY = "#fffdf1", "#14a39f", "#0d6f6c", "#f0861e", "#e2483d", "#2b2b2b", "#8a8a8a"
C = colors.HexColor
TITLE = "양동석의 월배당 설계"
SUBTITLE = "월 100만 원부터 500만 원까지, 마르지 않는 현금흐름 만들기"

# charts: teal/orange palette on ivory
build.PALETTE = [TEAL, ORANGE, "#5b8db8", "#9c6ade", "#7aa95c", "#c9a227", "#8a8a8a"]
build.CHART_H = 3.1
for k in ("figure.facecolor", "axes.facecolor", "savefig.facecolor"):
    plt.rcParams[k] = IVORY

S = {
    "body": ParagraphStyle("body", fontName="MJ", fontSize=9.6, leading=16.6, alignment=TA_JUSTIFY, firstLineIndent=9.6,
                           spaceAfter=4, textColor=C(INK), wordWrap="CJK"),
    "bullet": ParagraphStyle("bullet", fontName="MJ", fontSize=9.1, leading=14.6, leftIndent=12, bulletIndent=2,
                             spaceAfter=2.5, textColor=C(INK), wordWrap="CJK", bulletFontName="SRB", bulletColor=C(TEAL)),
    "h2": ParagraphStyle("h2", fontName="SRB", fontSize=11.2, leading=16, textColor=C(DTEAL), spaceBefore=9, spaceAfter=5,
                         keepWithNext=1, wordWrap="CJK"),
    "sec": ParagraphStyle("sec", fontName="SRB", fontSize=14.5, leading=20, textColor=C(ORANGE), spaceBefore=4,
                          spaceAfter=2, keepWithNext=1, wordWrap="CJK"),
    "cell": ParagraphStyle("cell", fontName="SQ", fontSize=7.6, leading=10.2, textColor=C(INK), wordWrap="CJK"),
    "cellh": ParagraphStyle("cellh", fontName="SRB", fontSize=8.2, leading=11, textColor=C(DTEAL), wordWrap="CJK"),
    "cap": ParagraphStyle("cap", fontName="SQ", fontSize=7.4, leading=10, textColor=C(GRAY), alignment=TA_CENTER,
                          spaceBefore=2, spaceAfter=9, wordWrap="CJK"),
    "box": ParagraphStyle("box", fontName="SQ", fontSize=8.6, leading=13.2, textColor=C(DTEAL), wordWrap="CJK"),
    "boxt": ParagraphStyle("boxt", fontName="SRB", fontSize=10, leading=14, textColor=C(DTEAL), spaceAfter=3, wordWrap="CJK"),
    "formula": ParagraphStyle("formula", fontName="SRB", fontSize=10, leading=15, alignment=TA_CENTER, textColor=C(DTEAL),
                              wordWrap="CJK"),
    "lead": ParagraphStyle("lead", fontName="MJB", fontSize=11, leading=19, textColor=C(DTEAL), alignment=TA_LEFT, wordWrap="CJK"),
    "toc": ParagraphStyle("toc", fontName="SRB", fontSize=9.4, leading=13.5, textColor=C(ORANGE), wordWrap="CJK"),
    "toc2": ParagraphStyle("toc2", fontName="SR", fontSize=8.4, leading=12, textColor=C(INK), leftIndent=14, wordWrap="CJK"),
    "tocp": ParagraphStyle("tocp", fontName="SRB", fontSize=8.8, leading=12, textColor=C(ORANGE), alignment=TA_RIGHT),
}


_fmt0 = fmt


def fmt(text):
    return _fmt0(str(text).replace("\u2248", "\u2252"))


def P(text, style):
    return Paragraph(fmt(text), S[style] if isinstance(style, str) else style)


# ------------------------------------------------------------------ custom flowables
class Marker(Flowable):
    def __init__(self, key=None, part=None, nohead=False):
        super().__init__(); self.key, self.part, self.nohead = key, part, nohead
    def wrap(self, *a): return (0, 0)
    def draw(self): pass


class Rule(Flowable):
    """Orange rule with a rounded hook at the right end (reference TOC style)."""
    def __init__(self, w=AV, color=ORANGE, hook=True, width=2.2):
        super().__init__(); self.w, self.color, self.hook, self.lw = w, color, hook, width
    def wrap(self, *a): return (self.w, 8)
    def draw(self):
        c = self.canv; c.setStrokeColor(C(self.color)); c.setLineWidth(self.lw); c.setLineCap(1)
        p = c.beginPath(); p.moveTo(0, 6)
        if self.hook:
            p.lineTo(self.w - 6, 6); p.curveTo(self.w - 1, 6, self.w, 5, self.w, 0)
        else:
            p.lineTo(self.w, 6)
        c.drawPath(p, stroke=1, fill=0)


class Dotted(Flowable):
    def __init__(self, w, color=ORANGE): super().__init__(); self.w, self.color = w, color
    def wrap(self, *a): return (self.w, 5)
    def draw(self):
        c = self.canv; c.setStrokeColor(C(self.color)); c.setLineWidth(1.6); c.setDash(1.2, 3.2); c.setLineCap(1)
        c.line(0, 2, self.w, 2)


class Avatar(Flowable):
    def __init__(self, d=15 * mm): super().__init__(); self.d = d
    def wrap(self, *a): return (self.d, self.d)
    def draw(self):
        c = self.canv; r = self.d / 2
        c.setFillColor(C(TEAL)); c.circle(r, r, r, fill=1, stroke=0)
        c.setFillColor(C(IVORY)); c.circle(r, r * 1.18, r * 0.36, fill=1, stroke=0)
        p = c.beginPath(); p.arc(r - r * 0.62, r * -0.05, r + r * 0.62, r * 1.15, 0, 180); c.drawPath(p, fill=1, stroke=0)
        c.setFillColor(C(DTEAL)); c.setFont("SRB", 6.2); c.drawCentredString(r, -7, "양동석")


class TipBadge(Flowable):
    def __init__(self, w=AV): super().__init__(); self.w = w
    def wrap(self, *a): return (self.w, 18)
    def draw(self):
        c = self.canv; cx = self.w / 2
        c.setStrokeColor(C(TEAL)); c.setLineWidth(1.2)
        c.line(0, 9, cx - 30, 9); c.line(cx + 30, 9, self.w, 9)
        for i, ch in enumerate("TIP"):
            x = cx - 18 + i * 18
            c.setFillColor(C(TEAL)); c.circle(x, 9, 7.5, fill=1, stroke=0)
            c.setFillColor(C(IVORY)); c.setFont("SRB", 8.5); c.drawCentredString(x, 6, ch)


class CaseHeader(Flowable):
    """Vertical 실전사례 label + teal title + dotted underline + persona line (reference case page)."""
    def __init__(self, title, who, label="실전사례"):
        super().__init__(); self.title, self.who, self.label = title, who, label
        self.tp = Paragraph(fmt(title), ParagraphStyle("ct", fontName="SRB", fontSize=17, leading=24, textColor=C(DTEAL), wordWrap="CJK"))
        self.wp = Paragraph(fmt(who), ParagraphStyle("cw", fontName="SRB", fontSize=10, leading=14, textColor=C(TEAL), wordWrap="CJK"))
    def wrap(self, aw, ah):
        self.inner = aw - 16 * mm
        _, self.th = self.tp.wrap(self.inner, ah); _, self.wh = self.wp.wrap(self.inner, ah)
        self.h = max(self.th + self.wh + 18, len(self.label) * 13 + 14)
        return (aw, self.h)
    def draw(self):
        c = self.canv; x0 = 16 * mm
        c.setFillColor(C(TEAL)); c.setFont("SRB", 10.5)
        for i, ch in enumerate(self.label):
            c.drawCentredString(5 * mm, self.h - 12 - i * 13, ch)
        c.setStrokeColor(C(TEAL)); c.setLineWidth(1.4)
        c.line(10.5 * mm, self.h - 2, 10.5 * mm, 4); c.line(10.5 * mm, 4, 10.5 * mm + 8, 4)
        self.tp.drawOn(c, x0, self.h - self.th)
        d = Dotted(self.inner); d.canv = c
        c.saveState(); c.translate(x0, self.h - self.th - 7); d.draw(); c.restoreState()
        self.wp.drawOn(c, x0, self.h - self.th - 12 - self.wh)


class QLine(Flowable):
    def __init__(self, text):
        super().__init__()
        self.p = Paragraph(fmt(text), ParagraphStyle("q", fontName="SRB", fontSize=12.5, leading=18, textColor=C(ORANGE), wordWrap="CJK"))
    def wrap(self, aw, ah):
        self.aw = aw; _, self.ph = self.p.wrap(aw - 11 * mm, ah); self.h = max(self.ph, 26); return (aw, self.h + 4)
    def draw(self):
        c = self.canv
        c.setStrokeColor(C(TEAL)); c.setLineWidth(3); c.setLineCap(1)
        c.roundRect(1.5, self.h - 22, 9, 19, 4.5, stroke=1, fill=0); c.line(6, self.h - 22, 6, self.h - 28)
        self.p.drawOn(c, 11 * mm, self.h - self.ph + 1)


# ------------------------------------------------------------------ blocks
def table_flow(b):
    hdr = [Paragraph(fmt(h), S["cellh"]) for h in b["header"]]
    rows = [[Paragraph(fmt(x), S["cell"]) for x in r] for r in b["rows"]]
    n = len(b["header"]); ws = b.get("widths")
    cw = [AV * w / sum(ws) for w in ws] if ws and len(ws) == n else [AV / n] * n
    t = Table([hdr] + rows, colWidths=cw, repeatRows=1)
    t.setStyle(TableStyle([("LINEABOVE", (0, 0), (-1, 0), 1.4, C(TEAL)), ("LINEBELOW", (0, 0), (-1, 0), 0.7, C(TEAL)),
                           ("LINEBELOW", (0, 1), (-1, -1), 0.35, C("#d6d2c4")), ("LINEBELOW", (0, -1), (-1, -1), 1.0, C(TEAL)),
                           ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 3.2),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 3.2), ("LEFTPADDING", (0, 0), (-1, -1), 3.5),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 3.5)]))
    out = [Spacer(1, 3), t, P(b["caption"], "cap") if b.get("caption") else Spacer(1, 9)]
    return [KeepTogether(out)] if len(rows) < 12 else out


def callout_flow(b):
    title, text = b.get("title", ""), b.get("text", "")
    if any(k in title for k in ("양동석", "한마디", "코멘트", "진단")) or not title:
        inner = ([P(title, "boxt")] if title else []) + [P(text, "box")]
        t = Table([[Avatar(), inner]], colWidths=[19 * mm, AV - 19 * mm])
        t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOX", (1, 0), (1, 0), 1.1, C(TEAL)),
                               ("ROUNDEDCORNERS", [8, 8, 8, 8]), ("LEFTPADDING", (1, 0), (1, 0), 9), ("RIGHTPADDING", (1, 0), (1, 0), 9),
                               ("TOPPADDING", (1, 0), (1, 0), 7), ("BOTTOMPADDING", (1, 0), (1, 0), 8), ("LEFTPADDING", (0, 0), (0, 0), 0)]))
        return [Spacer(1, 5), t, Spacer(1, 10)]
    warn = any(k in title for k in ("주의", "위험", "경고", "함정"))
    col = ORANGE if warn else TEAL
    tst = ParagraphStyle("bt2", parent=S["boxt"], textColor=C(col))
    inner = [Paragraph(fmt(title), tst), Paragraph(fmt(text), ParagraphStyle("bx2", parent=S["box"], textColor=C(INK)))]
    t = Table([[inner]], colWidths=[AV])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), C("#fbf3e3" if warn else "#eaf6f3")),
                           ("ROUNDEDCORNERS", [6, 6, 6, 6]), ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                           ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    return [Spacer(1, 4), t, Spacer(1, 10)]


def block(b):
    t = b.get("type")
    if t == "p": return [P(b["text"], "body")]
    if t == "h2": return [Paragraph(f"<font color='{ORANGE}'>●</font> " + fmt(b["text"]), S["h2"])]
    if t == "bullets": return [Paragraph(fmt(i), S["bullet"], bulletText="·") for i in b["items"]] + [Spacer(1, 4)]
    if t == "table": return table_flow(b)
    if t == "callout": return callout_flow(b)
    if t == "formula":
        tb = Table([[P(b["text"], "formula")]], colWidths=[AV])
        tb.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), C("#eaf6f3")), ("ROUNDEDCORNERS", [10, 10, 10, 10]),
                                ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
        return [Spacer(1, 3), tb] + ([P(b["note"], "cap")] if b.get("note") else [Spacer(1, 8)])
    if t == "chart":
        img = build.chart_image(b, TEAL, AV)
        return [KeepTogether([img] + ([P(b["caption"], "cap")] if b.get("caption") else []))]
    return []


# ------------------------------------------------------------------ section headers
def badge_para(text, bg, fg=IVORY, size=8.2):
    return f"<font name='SRB' size='{size}' color='{fg}' backColor='{bg}'>&nbsp;{text}&nbsp;</font>"


def clean_heading(h):
    return h.replace("곤쌤", "양동석").strip()


def sec_heading(sec, key):
    h, tag = clean_heading(sec["heading"]), sec.get("tag", "")
    h = re.sub(r"^\[(양동석 pick|양동석 PICK!?|Tip|TIP|실전 체감)\]\s*", "", h, flags=re.I)
    out = [CondPageBreak(42 * mm), Marker(key)]
    if tag == "Tip":
        out += [Spacer(1, 6), TipBadge(), Spacer(1, 2),
                Paragraph(fmt(h), ParagraphStyle("tt", fontName="SRB", fontSize=12.5, leading=18, textColor=C(DTEAL), alignment=TA_CENTER, keepWithNext=1, wordWrap="CJK")),
                Spacer(1, 6)]
    elif tag in ("양동석 pick", "실전 체감"):
        lab = "양동석 PICK" if tag == "양동석 pick" else "실전 체감"
        out += [Paragraph(badge_para(lab, ORANGE) + "<br/>" + fmt(h),
                          ParagraphStyle("pk", parent=S["sec"], textColor=C(DTEAL), leading=21, spaceBefore=8))]
        out.append(Rule(AV * 0.35, TEAL, hook=False, width=1.6))
    else:
        out += [Paragraph(fmt(h), S["sec"]), Rule(AV * 0.22, TEAL, hook=False, width=1.6)]
    return out


PERSONA_RE = re.compile(r"\s*\(([^()]*님)\)\s*$")


def case_parts(heading):
    h = re.sub(r"^\[\s*실전\s*사례\s*\d*\s*\]\s*", "", clean_heading(heading))
    m = PERSONA_RE.search(h)
    who = m.group(1) if m else ""
    return (h[:m.start()].strip() if m else h), (f"({who})" if who else "")


# ------------------------------------------------------------------ content model
PARTS = [
    (0, "준비마당", "양동석의 월배당 투자 원칙 8", "(ft. 족집게 ETF 리스트)",
     "ETF를 고르기 전에 먼저 세워야 할 여덟 가지 원칙입니다. 무엇을 담고, 얼마를 받고, 어느 계좌에 둘지 — 이 세 질문에 답하면 실전마당의 포트폴리오가 저절로 이해됩니다."),
    (1, "실전마당 1", "월 100만원 현금흐름", "(ft. 1.5억원, 목표 분배율 8%)", "1.5억 원으로 월 100만 원. 이 책의 모든 설계가 시작되는 기본 공식입니다."),
    (2, "실전마당 2", "월 200만원 현금흐름", "(ft. 3억원, 목표 분배율 8%)", "연 분배금 2,400만 원. 금융소득종합과세와 건강보험 피부양자 문턱을 넘는 구간입니다."),
    (3, "실전마당 3", "월 300만원 현금흐름", "(ft. 4.5억원, 목표 분배율 8%)", "근로소득을 온전히 대체하는 숫자. 절세계좌만으로는 담을 수 없어 계좌 이원화가 필수가 됩니다."),
    (4, "실전마당 4", "월 400만원 현금흐름", "(ft. 6억원, 목표 분배율 8%)", "일반계좌가 조연에서 주연이 되는 구간. 계좌 선택만으로 월 수령액이 달라집니다."),
    (5, "실전마당 5", "월 500만원 현금흐름", "(ft. 7.5억원, 목표 분배율 8%)", "월급의 대체가 아니라 월급의 졸업. 재원을 나눠 세금과 건강보험료를 함께 설계합니다."),
]


def load_units():
    us = [json.load(open(f, encoding="utf-8")) for f in sorted(glob.glob(os.path.join(ROOT, "units", "*.json")))]
    order = lambda u: (u.get("part", 0), u.get("no", 0), u["id"])
    return sorted(us, key=order)


def walk(units):
    """Yield (key, part, unit, section_index, section) in reading order with stable keys."""
    for u in units:
        for i, s in enumerate(u["sections"]):
            yield f"{u['id']}:{i}", u.get("part", 0), u, i, s


# ------------------------------------------------------------------ front / back matter
def part_divider(p, units=()):
    no, lab, title, sub, desc = PARTS[p]
    items = []
    for u in units:
        if u.get("part", 0) != p: continue
        if u.get("kind") == "principle":
            items.append(f"<font color='{ORANGE}'>원칙 {u['no']}</font>&nbsp; {fmt(u['title'])}")
        else:
            for s_ in u["sections"]:
                if s_.get("level", 2) == 1 and s_.get("tag") != "Tip":
                    t_ = case_parts(s_["heading"])[0] if s_.get("tag") == "실전사례" else clean_heading(s_["heading"])
                    pre = f"<font color='{RED}'>사례</font>&nbsp; " if s_.get("tag") == "실전사례" else ""
                    items.append(pre + fmt(t_))
    st = [NextPageTemplate("divider"), PageBreak(), Marker(f"part{no}", part=f"{lab}  {title}", nohead=True), Spacer(1, 38 * mm),
          Paragraph(badge_para(lab, ORANGE, size=11), ParagraphStyle("pl", fontName="SRB", fontSize=11, leading=16)),
          Spacer(1, 10),
          Paragraph(fmt(title), ParagraphStyle("pt", fontName="SRB", fontSize=26, leading=34, textColor=C(DTEAL), wordWrap="CJK")),
          Paragraph(fmt(sub), ParagraphStyle("ps", fontName="SRB", fontSize=13, leading=20, textColor=C(TEAL))),
          Spacer(1, 6), Rule(AV), Spacer(1, 14),
          Paragraph(fmt(desc), ParagraphStyle("pd", fontName="MJ", fontSize=10.5, leading=19, textColor=C(INK), wordWrap="CJK")),
          Spacer(1, 16)]
    li = ParagraphStyle("pli", fontName="SR", fontSize=9, leading=15, textColor=C(DTEAL), leftIndent=10, bulletIndent=0, wordWrap="CJK")
    st += [Paragraph(x, li, bulletText="·") for x in items]
    st.append(NextPageTemplate("body"))
    return st


def principle_opener(u, key):
    lab = ParagraphStyle("ol", fontName="SRB", fontSize=10.5, leading=13.5, textColor=C(TEAL))
    num = ParagraphStyle("on", fontName="SRB", fontSize=58, leading=58, textColor=C(ORANGE))
    tit = ParagraphStyle("ot", fontName="SRB", fontSize=19, leading=27, textColor=C(DTEAL), alignment=TA_RIGHT, wordWrap="CJK")
    left = [Paragraph("양동석의<br/>월배당 투자<br/>원칙", lab), Spacer(1, 2), Paragraph(str(u["no"]), num)]
    t = Table([[left, Paragraph(fmt(u["title"]), tit)]], colWidths=[32 * mm, AV - 32 * mm])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "BOTTOM"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    out = [PageBreak(), Marker(key, part=f"원칙 {u['no']}  {u['title']}", nohead=True), Spacer(1, 26 * mm), t, Spacer(1, 2), Rule(), Spacer(1, 16)]
    if u.get("lead"):
        out += [Paragraph(fmt(u["lead"]), S["lead"]), Spacer(1, 16)]
    return out


def numbered_opener(sec, key):
    h = clean_heading(sec["heading"])
    m = re.match(r"^(\d{2})\s+(.*)$", h)
    num, rest = (m.group(1), m.group(2)) if m else ("", h)
    out = [PageBreak(), Marker(key), Spacer(1, 8 * mm)]
    if num:
        out.append(Paragraph(num, ParagraphStyle("nn", fontName="SRB", fontSize=34, leading=38, textColor=C(ORANGE))))
    out += [Paragraph(fmt(rest), ParagraphStyle("nt", fontName="SRB", fontSize=17, leading=24, textColor=C(DTEAL), wordWrap="CJK")),
            Spacer(1, 3), Rule(), Spacer(1, 12)]
    return out


def case_opener(sec, key):
    title, who = case_parts(sec["heading"])
    pr = sec.get("persona") or {}
    out = [PageBreak(), Marker(key), Spacer(1, 6 * mm), CaseHeader(title, who), Spacer(1, 16)]
    if pr.get("concern"):
        out += [QLine(pr["concern"]), Spacer(1, 6)]
    rows = [[k, pr[f]] for k, f in (("이름", "name"), ("나이", "age"), ("상황", "job"), ("자산", "assets")) if pr.get(f)]
    if rows:
        t = Table([[Paragraph(f"<font color='{TEAL}'><b>{a}</b></font>", S["cell"]), Paragraph(fmt(b), S["cell"])] for a, b in rows],
                  colWidths=[16 * mm, AV - 16 * mm])
        t.setStyle(TableStyle([("LINEABOVE", (0, 0), (-1, 0), 1, C(TEAL)), ("LINEBELOW", (0, -1), (-1, -1), 1, C(TEAL)),
                               ("LINEBELOW", (0, 0), (-1, -2), 0.3, C("#d6d2c4")), ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        out += [t, Spacer(1, 12)]
    return out


def summary_box(title, items):
    st = ParagraphStyle("sbt", fontName="SRB", fontSize=11, leading=15, textColor=C(IVORY), spaceAfter=4)
    sb = ParagraphStyle("sbb", fontName="SQ", fontSize=9, leading=14.5, textColor=C(IVORY), leftIndent=10, bulletIndent=0, wordWrap="CJK")
    inner = [Paragraph(fmt(title), st)] + [Paragraph(fmt(x), sb, bulletText="✓" if False else "▶") for x in items]
    t = Table([[inner]], colWidths=[AV])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), C(TEAL)), ("ROUNDEDCORNERS", [8, 8, 8, 8]),
                           ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                           ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 10)]))
    return [CondPageBreak(55 * mm), Spacer(1, 10), t]


def front_matter(units):
    cases = sum(1 for *_, s in walk(units) if s.get("tag") == "실전사례")
    st = [NextPageTemplate("body"), PageBreak(), Marker("prologue", part="프롤로그", nohead=True), Spacer(1, 10 * mm),
          Paragraph("프롤로그", ParagraphStyle("pg", fontName="SRB", fontSize=20, leading=26, textColor=C(DTEAL))), Rule(AV * 0.3, ORANGE, False), Spacer(1, 4),
          Paragraph("월급이 끊긴 다음 날에도, 통장에는 돈이 들어와야 합니다", ParagraphStyle("pgs", fontName="SRB", fontSize=12.5, leading=19, textColor=C(ORANGE))),
          Spacer(1, 10)]
    for t in [
        "은퇴 상담을 하다 보면 가장 많이 듣는 질문은 「얼마를 모아야 하나요?」가 아니라 「매달 얼마가 나오나요?」입니다. 사람은 자산의 크기로 사는 것이 아니라 매달 들어오는 현금흐름으로 삽니다. 월급이 끊긴 뒤에도 매달 같은 날 생활비가 들어온다는 확신, 그것이 은퇴 준비의 본질이라고 저는 믿습니다.",
        "그래서 많은 분이 월배당 ETF에 관심을 가집니다. 그런데 막상 시장을 들여다보면 연 15%, 20%를 넘는 분배율을 내건 상품들이 넘쳐 납니다. 높은 숫자는 달콤하지만, 분배금이 원금을 갉아먹으며 나오는 구조라면 몇 년 뒤 계좌에 남는 것은 줄어든 원금과 줄어든 분배금뿐입니다. 이 책은 바로 그 함정을 피하면서 「오래 유지할 수 있는」 월배당 포트폴리오를 만드는 방법을 다룹니다.",
        "책은 두 부분으로 이루어져 있습니다. **준비마당**에서는 제가 상담 현장에서 지켜 온 여덟 가지 원칙을 정리했습니다. 기초자산은 시장대표지수로, 커버드콜도 지수형으로, 같은 기초자산이면 큰 ETF로, 그리고 무엇보다 높은 분배율보다 지속 가능한 분배율을 고르는 법입니다. **실전마당**에서는 월 100만 원(1.5억 원)부터 월 500만 원(7.5억 원)까지 다섯 단계의 현금흐름을 실제 포트폴리오와 계좌 배치로 설계합니다.",
        f"각 실전마당에는 모두 {cases}개의 실전사례를 담았습니다. 국민연금 개시 전 소득 공백기, 퇴직금이 IRP에 묶인 명예퇴직자, 건강보험 피부양자에서 탈락한 부부, 가게나 상가를 정리한 자영업자까지 — 상담실에서 실제로 마주하는 고민들을 재구성해 숫자로 답했습니다. 여러분의 상황과 가장 닮은 사례부터 읽으셔도 좋습니다.",
        "한 가지 약속을 드리겠습니다. 이 책은 「무조건 오른다」거나 「분배금이 보장된다」고 말하지 않습니다. 월배당 ETF도 원금 손실이 날 수 있고 분배금은 줄어들 수 있습니다. 그 위험을 숫자로 보여 드리고, 그 위에서도 버틸 수 있는 설계를 함께 만드는 것이 이 책의 목표입니다. 이 책을 덮을 때, 여러분만의 「월급날」이 그려지기를 바랍니다.",
    ]:
        st.append(P(t, "body"))
    st += [Spacer(1, 8), Paragraph("양동석", ParagraphStyle("sg", fontName="SRB", fontSize=11, textColor=C(DTEAL), alignment=TA_RIGHT))]
    # how to read
    st += [PageBreak(), Marker("howto", part="이 책의 활용법", nohead=True), Spacer(1, 6 * mm),
           Paragraph("이 책의 활용법", ParagraphStyle("hw", fontName="SRB", fontSize=18, leading=24, textColor=C(DTEAL))), Rule(AV * 0.3, ORANGE, False), Spacer(1, 8)]
    st += table_flow({"header": ["목표 월 현금흐름", "필요 원금(분배율 8%)", "읽을 곳", "핵심 주제"], "widths": [1.2, 1.3, 1, 2.6], "rows": [
        ["월 100만 원", "1.5억 원", "실전마당 1", "8% 설계의 기본, 6%·4% 대안, 인출기 vs 적립기"],
        ["월 200만 원", "3억 원", "실전마당 2", "금융소득종합과세·건보 피부양자, 절세계좌 3총사"],
        ["월 300만 원", "4.5억 원", "실전마당 3", "계좌 이원화, 국내 커버드콜 일반계좌, IRP 인출"],
        ["월 400만 원", "6억 원", "실전마당 4", "계좌 삼원화, 세후 수령액 차이, 파이어족 브리지"],
        ["월 500만 원", "7.5억 원", "실전마당 5", "재원 3분류, 건강보험료, 증여·상속 연계"],
    ], "caption": "원금 × 8% ÷ 12 = 월 분배금(세전). 실제 분배금은 시장 상황에 따라 달라질 수 있습니다."})
    st += callout_flow({"title": "양동석의 한마디", "text": "준비마당의 원칙 1~8을 먼저 읽고, 그다음 내 목표 금액에 해당하는 실전마당으로 가세요. 실전사례는 나와 나이·상황이 비슷한 분부터 찾아 읽으면 훨씬 빠르게 내 설계도가 그려집니다."})
    st += callout_flow({"title": "꼭 읽어 주세요", "text": "이 책에 나오는 ETF는 설명을 위한 예시이며 매수·매도 권유가 아닙니다. 분배율·순자산·보수 등 시장 수치는 2026년 10월 기준이고, 세법·건강보험·연금 제도는 집필 시점의 현행 기준으로 이후 개정될 수 있습니다. 실전사례는 이해를 돕기 위해 재구성했습니다. 실제 투자와 절세 결정 전에는 운용사 공시와 세무·연금 전문가의 확인을 받으시기 바랍니다."})
    return st


def back_matter():
    st = [NextPageTemplate("body"), PageBreak(), Marker("epilogue", part="에필로그", nohead=True), Spacer(1, 10 * mm),
          Paragraph("에필로그", ParagraphStyle("eg", fontName="SRB", fontSize=20, leading=26, textColor=C(DTEAL))), Rule(AV * 0.3, ORANGE, False), Spacer(1, 4),
          Paragraph("가장 좋은 분배율은 끝까지 지킬 수 있는 분배율입니다", ParagraphStyle("egs", fontName="SRB", fontSize=12.5, leading=19, textColor=C(ORANGE))), Spacer(1, 10)]
    for t in [
        "여기까지 함께 걸어오신 여러분께 감사드립니다. 월 100만 원에서 시작해 월 500만 원까지, 숫자는 커졌지만 원칙은 한 번도 바뀌지 않았습니다. 시장대표지수를 중심에 두고, 지수형 커버드콜로 현금흐름을 만들고, 곁들임으로 균형을 잡고, 계좌를 나눠 세금을 줄이는 것. 이 단순한 원칙이 수많은 상담 사례에서 가장 오래 버틴 방법이었습니다.",
        "시장은 늘 새로운 상품을 내놓습니다. 더 높은 분배율, 더 짧은 옵션 만기, 더 화려한 테마가 등장할 것입니다. 그때마다 이 책의 질문으로 돌아와 주세요. 기초자산은 무엇인가, 분배율이 장기 총수익보다 높지 않은가, 내 목표 분배율과 맞는가, 어느 계좌에 담아야 하는가. 이 네 가지 질문에 답할 수 있다면 어떤 상품 앞에서도 흔들리지 않을 것입니다.",
        "마지막으로, 포트폴리오는 한 번 만들고 끝나는 것이 아닙니다. 1년에 한 번은 비중을 점검하고, 세법과 제도가 바뀌면 계좌 배치를 다시 살펴보세요. 그리고 무엇보다 분배금으로 누리는 오늘의 삶을 소중히 여기시기 바랍니다. 현금흐름은 목적이 아니라, 더 좋은 하루를 위한 도구니까요.",
    ]:
        st.append(P(t, "body"))
    st += [Spacer(1, 8), Paragraph("양동석", ParagraphStyle("sg2", fontName="SRB", fontSize=11, textColor=C(DTEAL), alignment=TA_RIGHT))]
    st += [PageBreak(), Marker("appendix", part="부록", nohead=False),
           Paragraph("부록  세금·제도 한눈에 보기", ParagraphStyle("ap", fontName="SRB", fontSize=16, leading=22, textColor=C(DTEAL))), Rule(AV * 0.3, ORANGE, False), Spacer(1, 8)]
    st += table_flow({"header": ["구분", "핵심 내용 (현행 기준, 개정 가능)"], "widths": [1.3, 4.7], "rows": [
        ["일반계좌 분배금", "배당소득 15.4% 원천징수. 국내 주식형 ETF의 국내주식·장내파생 매매차익 분배분은 비과세(상품별 과세표준 비율 확인)"],
        ["금융소득종합과세", "개인별 이자+배당 연 2,000만 원 초과분을 다른 소득과 합산해 누진과세(6.6~49.5%)"],
        ["건강보험", "피부양자: 연소득 2,000만 원 초과 시 자격 상실. 지역가입자: 금융소득 연 1,000만 원 초과 시 전액 반영. 직장가입자: 보수 외 소득 2,000만 원 초과 시 추가 보험료"],
        ["ISA(중개형)", "연 2,000만 원·총 1억 원 납입, 비과세 200만 원(서민형 400만 원), 초과분 9.9% 분리과세, 의무 3년. 한도 확대·2027년 개편안은 시행 여부 확인"],
        ["연금저축·IRP", "합산 연 1,800만 원 납입, 세액공제 900만 원(13.2%/16.5%), 55세 이후 연금소득세 3.3~5.5%, 사적연금 연 1,500만 원 초과 시 종합과세 또는 16.5% 분리과세 선택"],
        ["퇴직금 IRP", "연금 수령 시 퇴직소득세 30% 감면(10년 초과분 40%), 연금수령한도 = 평가액 ÷ (11 - 연차) × 120%"],
        ["주택연금", "만 55세 이상, 공시가격 12억 원 이하. 월 지급액은 한국주택금융공사 조회"],
        ["노란우산공제", "소상공인 퇴직금 성격, 연 최대 600만 원 소득공제(소득 구간별), 압류 금지"],
        ["증여재산공제", "배우자 10년 6억 원, 성년 자녀 10년 5,000만 원, 혼인·출산 추가 1억 원"],
    ], "caption": "집필 시점(2026년 10월) 기준 요약입니다. 실제 적용 전 국세청·국민건강보험공단·금융회사에서 최신 기준을 확인하세요."})
    st += [Spacer(1, 6), Paragraph("월배당 포트폴리오 연간 점검 체크리스트", S["h2"])]
    for x in ["목표 분배율과 실제 분배율의 차이가 ±1%p 이내인가?", "분배금 재투자 기준 NAV가 3년 연속 감소하지 않았는가?",
              "메인(시장대표지수+지수형 커버드콜) 비중이 70~80%를 유지하는가?", "같은 기초자산 안에서 더 크고 보수가 낮은 ETF가 있지 않은가?",
              "올해 금융소득이 개인별 2,000만 원을 넘지 않도록 계좌 배치가 되어 있는가?", "연금저축·IRP·ISA 납입 한도를 올해 모두 활용했는가?",
              "세법·건강보험 제도 개정 사항을 확인했는가?", "6개월~1년치 생활비가 현금성 자산으로 따로 준비되어 있는가?"]:
        st.append(Paragraph("□ " + fmt(x), S["bullet"]))
    return st


# ------------------------------------------------------------------ TOC
def toc_story(units, pages):
    pg = lambda k: str(pages.get(k, 0)) if pages else "000"
    st = [PageBreak(), Marker("toc", part="차례", nohead=True), Spacer(1, 4 * mm),
          Paragraph("차례", ParagraphStyle("tc", fontName="SRB", fontSize=20, leading=26, textColor=C(DTEAL))), Rule(AV * 0.25, ORANGE, False), Spacer(1, 6)]
    row = lambda left, right, style="toc": Table([[left, Paragraph(right, S["tocp"])]], colWidths=[AV - 14 * mm, 14 * mm],
                                                 style=[("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                                                        ("TOPPADDING", (0, 0), (-1, -1), 1.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
                                                        ("VALIGN", (0, 0), (-1, -1), "TOP")])
    st += [row(Paragraph("프롤로그", S["toc"]), pg("prologue")), row(Paragraph("이 책의 활용법", S["toc"]), pg("howto"))]
    cur_part = None
    for u in units:
        part = u.get("part", 0)
        if part != cur_part:
            cur_part = part
            no, lab, title, sub, _ = PARTS[part]
            st += [Spacer(1, 10), row(Paragraph(badge_para(lab, ORANGE) + "&nbsp;&nbsp;" + f"<font color='{DTEAL}'>{fmt(title)}</font> "
                                                f"<font size='8' color='{TEAL}'>{fmt(sub)}</font>",
                                                ParagraphStyle("tp", fontName="SRB", fontSize=11, leading=16, wordWrap="CJK")), pg(f"part{no}")), Spacer(1, 2)]
        if u.get("kind") == "principle":
            lab = ParagraphStyle("tl", fontName="SRB", fontSize=7.6, leading=9.5, textColor=C(TEAL))
            num = ParagraphStyle("tn", fontName="SRB", fontSize=26, leading=27, textColor=C(ORANGE))
            tit = ParagraphStyle("tt2", fontName="SRB", fontSize=12.5, leading=17, textColor=C(DTEAL), alignment=TA_RIGHT, wordWrap="CJK")
            t = Table([[[Paragraph("양동석의<br/>월배당 투자 원칙", lab), Paragraph(str(u["no"]), num)], Paragraph(fmt(u["title"]), tit)]],
                      colWidths=[30 * mm, AV - 30 * mm],
                      style=[("VALIGN", (0, 0), (-1, -1), "BOTTOM"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)])
            st += [CondPageBreak(45 * mm), Spacer(1, 6), t, Rule(), Spacer(1, 3)]
        for key, _, uu, i, s in walk([u]):
            h, tag, lvl = clean_heading(s["heading"]), s.get("tag", ""), s.get("level", 2)
            if tag == "실전사례":
                title, who = case_parts(s["heading"])
                txt = f"<font color='{RED}'>[ 실전사례 ]</font>&nbsp; <font color='{INK}'>{fmt(title)}</font> <font size='7.6' color='{GRAY}'>{fmt(who)}</font>"
                st.append(row(Paragraph(txt, ParagraphStyle("tcs", parent=S["toc"], fontSize=8.9)), pg(key)))
            elif tag == "Tip":
                h2 = re.sub(r"^\[(Tip|TIP)\]\s*", "", h)
                txt = badge_para("TIP", RED, size=7.4) + f"&nbsp; <font color='{INK}'>{fmt(h2)}</font>"
                st.append(row(Paragraph(txt, ParagraphStyle("tct", parent=S["toc2"], leftIndent=14 if lvl == 2 else 0, fontName="SRB")), pg(key)))
            elif lvl == 1 or u.get("kind") == "principle":
                h2 = re.sub(r"^\[(양동석 pick|양동석 PICK!?|실전 체감)\]\s*", "", h, flags=re.I)
                pre = badge_para("PICK", TEAL, size=7.2) + "&nbsp; " if tag == "양동석 pick" else ""
                st.append(row(Paragraph(pre + fmt(h2), S["toc"] if lvl == 1 or u.get("kind") == "principle" else S["toc2"]), pg(key)))
            else:
                h2 = re.sub(r"^\[(양동석 pick|양동석 PICK!?|실전 체감)\]\s*", "", h, flags=re.I)
                pre = badge_para("PICK", TEAL, size=7) + "&nbsp; " if tag == "양동석 pick" else ""
                st.append(row(Paragraph(pre + fmt(h2), S["toc2"]), pg(key)))
    st += [Spacer(1, 10), row(Paragraph("에필로그", S["toc"]), pg("epilogue")), row(Paragraph("부록  세금·제도 한눈에 보기", S["toc"]), pg("appendix"))]
    return st


# ------------------------------------------------------------------ document
class Doc(BaseDocTemplate):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw); self.pages = {}; self.part = ""; self.nohead = set()
    def afterFlowable(self, f):
        if isinstance(f, Marker):
            if f.key and f.key not in self.pages: self.pages[f.key] = self.page
            if f.part: self.part = f.part
            if f.nohead: self.nohead.add(self.page)


def bg(c, doc):
    c.saveState(); c.setFillColor(C(IVORY)); c.rect(0, 0, W, H, fill=1, stroke=0); c.restoreState()


def page_end(c, doc):
    c.saveState()
    odd = doc.page % 2 == 1
    c.setFont("SR", 7.6); c.setFillColor(C(GRAY))
    c.drawCentredString(W / 2, 11 * mm, str(doc.page))
    if doc.page not in doc.nohead:
        c.setFont("SR", 7.2); c.setFillColor(C(TEAL))
        if odd: c.drawRightString(W - MR, H - 12 * mm, doc.part)
        else: c.drawString(ML, H - 12 * mm, TITLE)
    c.restoreState()


def cover(c, doc):
    bg(c, doc)
    c.saveState()
    # coin stack motif
    for i, (x, y, r, col) in enumerate([(W * 0.72, H * 0.30, 34 * mm, TEAL), (W * 0.86, H * 0.22, 22 * mm, ORANGE),
                                        (W * 0.60, H * 0.16, 16 * mm, ORANGE), (W * 0.18, H * 0.86, 10 * mm, TEAL)]):
        c.setFillColor(C(col)); c.setFillAlpha(0.14 if i else 0.12); c.circle(x, y, r, fill=1, stroke=0)
    c.setFillAlpha(1)
    for k in range(6):  # stacked coins
        y = 34 * mm + k * 7 * mm; c.setFillColor(C(ORANGE if k % 2 else TEAL)); c.roundRect(W * 0.62, y, 46 * mm, 6 * mm, 3 * mm, fill=1, stroke=0)
    c.setFillColor(C(DTEAL)); c.setFont("SRB", 12); c.drawCentredString(W * 0.62 + 23 * mm, 34 * mm + 6 * 7 * mm + 3 * mm, "매달 같은 날, 내 월급날")
    c.setFillColor(C(TEAL)); c.setFont("SRB", 10.5); c.drawString(ML, H - 30 * mm, "8가지 원칙 · 5단계 실전 포트폴리오 · 실전사례")
    c.setStrokeColor(C(ORANGE)); c.setLineWidth(2.4); c.setLineCap(1); c.line(ML, H - 34 * mm, ML + 52 * mm, H - 34 * mm)
    c.setFillColor(C(DTEAL)); c.setFont("SRB", 36)
    c.drawString(ML, H - 62 * mm, "양동석의"); c.drawString(ML, H - 78 * mm, "월배당 설계")
    c.setFillColor(C(ORANGE)); c.setFont("SRB", 13); c.drawString(ML, H - 92 * mm, SUBTITLE)
    c.setFillColor(C(INK)); c.setFont("SR", 10)
    c.drawString(ML, H - 101 * mm, "시장대표지수 + 지수형 커버드콜로 만드는 목표 분배율 8% 포트폴리오")
    c.setFillColor(C(DTEAL)); c.setFont("SRB", 13); c.drawString(ML, 26 * mm, "양동석 지음")
    c.setFillColor(C(GRAY)); c.setFont("SR", 7.5); c.drawString(ML, 18 * mm, "2026년 10월 기준 · 투자 권유 아님 · 사례는 재구성")
    c.restoreState()


def make_story(units, pages):
    st = [NextPageTemplate("body"), PageBreak()]
    st += front_matter(units)
    st += toc_story(units, pages)
    cur = None
    for u in units:
        part = u.get("part", 0)
        if part != cur:
            cur = part; st += part_divider(part, units)
        if u.get("kind") == "principle":
            first = True
            st += principle_opener(u, f"{u['id']}:open")
        for key, _, uu, i, s in walk([u]):
            tag, lvl = s.get("tag", ""), s.get("level", 2)
            if tag == "실전사례":
                st += case_opener(s, key)
            elif lvl == 1 and tag != "Tip":
                st += numbered_opener(s, key)
            else:
                st += sec_heading(s, key)
            for b in s.get("blocks", []):
                st += block(b)
            if tag == "Tip":
                st += [Spacer(1, 2), Rule(AV, TEAL, False, 1.0), Spacer(1, 8)]
        if u.get("summary"):
            ttl = f"원칙 {u['no']} 핵심 정리" if u.get("kind") == "principle" else f"{PARTS[part][1]} 핵심 정리"
            st += summary_box(ttl, u["summary"])
    st += back_matter()
    return st


def build_book(out):
    units = load_units()
    pages = {}
    for _ in range(2):
        doc = Doc(out, pagesize=(W, H), leftMargin=ML, rightMargin=MR, topMargin=MT, bottomMargin=MB,
                  title=f"{TITLE} — {SUBTITLE}", author="양동석")
        fr = Frame(ML, MB, AV, H - MT - MB, id="f", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        doc.addPageTemplates([PageTemplate("cover", frames=[fr], onPage=cover),
                              PageTemplate("divider", frames=[fr], onPage=bg, onPageEnd=page_end),
                              PageTemplate("body", frames=[fr], onPage=bg, onPageEnd=page_end)])
        doc.build(make_story(units, pages))
        pages = doc.pages
    return out, doc.page


if __name__ == "__main__":
    out = os.environ.get("OUT", os.path.join(ROOT, "양동석의_월배당설계.pdf"))
    o, n = build_book(out); print(n, "pages", o)
