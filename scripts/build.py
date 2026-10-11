"""Render content/*.json into styled Korean PDF reports (reportlab + matplotlib)."""
import io, json, sys, glob, os
from datetime import date
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table,
                                TableStyle, Image, PageBreak, KeepTogether, NextPageTemplate)
from xml.sax.saxutils import escape

FONT_DIR = "/usr/share/fonts/truetype/nanum"
pdfmetrics.registerFont(TTFont("Nanum", f"{FONT_DIR}/NanumGothic.ttf"))
pdfmetrics.registerFont(TTFont("NanumB", f"{FONT_DIR}/NanumGothicBold.ttf"))
pdfmetrics.registerFont(TTFont("NanumEB", f"{FONT_DIR}/NanumSquareB.ttf"))
from reportlab.pdfbase.pdfmetrics import registerFontFamily
registerFontFamily("Nanum", normal="Nanum", bold="NanumB", italic="Nanum", boldItalic="NanumB")
font_manager.fontManager.addfont(f"{FONT_DIR}/NanumGothic.ttf")
font_manager.fontManager.addfont(f"{FONT_DIR}/NanumGothicBold.ttf")
plt.rcParams["font.family"] = "NanumGothic"
plt.rcParams["axes.unicode_minus"] = False

PAGE_W, PAGE_H = A4
MARGIN = 20 * mm
PALETTE = ["#1f4e79", "#e07b39", "#3a9d6b", "#8c5bb5", "#c94a4a", "#7f8c8d", "#d4a017"]


def styles(accent):
    s = {}
    s["body"] = ParagraphStyle("body", fontName="Nanum", fontSize=10, leading=16.5, alignment=TA_JUSTIFY,
                               spaceAfter=6, wordWrap="CJK")
    s["h1"] = ParagraphStyle("h1", fontName="NanumEB", fontSize=17, leading=23, textColor=colors.HexColor(accent),
                             spaceBefore=4, spaceAfter=10)
    s["h2"] = ParagraphStyle("h2", fontName="NanumB", fontSize=12.5, leading=18, textColor=colors.HexColor("#222222"),
                             spaceBefore=10, spaceAfter=5)
    s["bullet"] = ParagraphStyle("bullet", parent=s["body"], leftIndent=12, bulletIndent=2, spaceAfter=3)
    s["cell"] = ParagraphStyle("cell", fontName="Nanum", fontSize=8.6, leading=12, wordWrap="CJK")
    s["cellh"] = ParagraphStyle("cellh", fontName="NanumB", fontSize=8.8, leading=12, textColor=colors.white,
                                wordWrap="CJK", alignment=TA_CENTER)
    s["caption"] = ParagraphStyle("caption", fontName="Nanum", fontSize=8, leading=11,
                                  textColor=colors.HexColor("#666666"), alignment=TA_CENTER, spaceAfter=10)
    s["callt"] = ParagraphStyle("callt", fontName="NanumB", fontSize=10, leading=14,
                                textColor=colors.HexColor(accent), spaceAfter=3)
    s["callb"] = ParagraphStyle("callb", parent=s["body"], fontSize=9.4, leading=15, spaceAfter=0)
    s["formula"] = ParagraphStyle("formula", fontName="NanumB", fontSize=10.5, leading=16, alignment=TA_CENTER,
                                  textColor=colors.HexColor("#333333"))
    s["toc"] = ParagraphStyle("toc", fontName="Nanum", fontSize=11, leading=22)
    return s


def fmt(text):
    """Escape text but allow **bold** markup."""
    t = escape(str(text))
    parts = t.split("**")
    return "".join(f"<b>{p}</b>" if i % 2 else p for i, p in enumerate(parts))


def chart_image(b, accent, width):
    kind = b.get("kind", "line")
    fig, ax = plt.subplots(figsize=(7.2, 3.4), dpi=160)
    x = b.get("x", [])
    series = b.get("series", {})
    cols = [accent] + [c for c in PALETTE if c.lower() != accent.lower()]
    if kind == "pie":
        name, vals = next(iter(series.items()))
        ax.pie(vals, labels=x, autopct="%1.1f%%", colors=cols[:len(vals)], startangle=90,
               wedgeprops=dict(width=0.45, edgecolor="white"), textprops=dict(fontsize=9))
        ax.axis("equal")
    elif kind in ("bar", "barh", "stacked"):
        n = len(series)
        import numpy as np
        idx = np.arange(len(x))
        if kind == "stacked":
            bottom = np.zeros(len(x))
            for i, (name, vals) in enumerate(series.items()):
                ax.bar(idx, vals, 0.6, bottom=bottom, label=name, color=cols[i % len(cols)])
                bottom += np.array(vals, dtype=float)
        else:
            w = 0.8 / max(n, 1)
            for i, (name, vals) in enumerate(series.items()):
                pos = idx - 0.4 + w * (i + 0.5)
                if kind == "barh":
                    ax.barh(pos, vals, w, label=name, color=cols[i % len(cols)])
                else:
                    ax.bar(pos, vals, w, label=name, color=cols[i % len(cols)])
        if kind == "barh":
            ax.set_yticks(idx); ax.set_yticklabels(x, fontsize=8.5); ax.invert_yaxis()
        else:
            ax.set_xticks(idx); ax.set_xticklabels(x, fontsize=8.5, rotation=0 if len(x) < 9 else 45)
        ax.axhline(0, color="#999", lw=0.6) if kind != "barh" else ax.axvline(0, color="#999", lw=0.6)
    else:
        for i, (name, vals) in enumerate(series.items()):
            if kind == "area":
                ax.fill_between(range(len(vals)), vals, alpha=0.25, color=cols[i % len(cols)])
            ax.plot(range(len(vals)), vals, label=name, color=cols[i % len(cols)], lw=2,
                    marker="o" if len(vals) <= 12 else None, ms=3.5)
        step = max(1, len(x) // 10)
        ax.set_xticks(range(0, len(x), step)); ax.set_xticklabels(x[::step], fontsize=8.5)
    if kind != "pie":
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="x" if kind == "barh" else "y", alpha=0.3)
        ax.tick_params(labelsize=8.5)
        if b.get("ylabel"):
            (ax.set_xlabel if kind == "barh" else ax.set_ylabel)(b["ylabel"], fontsize=9)
        if len(series) > 1:
            ax.legend(fontsize=8.5, frameon=False)
    ax.set_title(b.get("title", ""), fontsize=11, fontweight="bold", loc="left")
    fig.tight_layout()
    buf = io.BytesIO(); fig.savefig(buf, format="png"); plt.close(fig); buf.seek(0)
    img = Image(buf, width=width, height=width * 3.4 / 7.2)
    return img


def render_block(b, s, accent, avail):
    t = b.get("type")
    if t == "p":
        return [Paragraph(fmt(b["text"]), s["body"])]
    if t == "h2":
        return [Paragraph(fmt(b["text"]), s["h2"])]
    if t == "bullets":
        return [Paragraph(fmt(i), s["bullet"], bulletText="•") for i in b["items"]] + [Spacer(1, 4)]
    if t == "formula":
        tbl = Table([[Paragraph(fmt(b["text"]), s["formula"])]], colWidths=[avail])
        tbl.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f4f6f8")),
                                 ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cfd6dd")),
                                 ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
        out = [tbl]
        if b.get("note"):
            out.append(Paragraph(fmt(b["note"]), s["caption"]))
        else:
            out.append(Spacer(1, 8))
        return out
    if t == "callout":
        inner = []
        if b.get("title"):
            inner.append(Paragraph(fmt(b["title"]), s["callt"]))
        inner.append(Paragraph(fmt(b["text"]), s["callb"]))
        tbl = Table([[inner]], colWidths=[avail])
        tbl.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fbf8ef")),
                                 ("LINEBEFORE", (0, 0), (0, -1), 3, colors.HexColor(accent)),
                                 ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                                 ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
        return [Spacer(1, 4), tbl, Spacer(1, 10)]
    if t == "table":
        header = [Paragraph(fmt(h), s["cellh"]) for h in b["header"]]
        rows = [[Paragraph(fmt(c), s["cell"]) for c in r] for r in b["rows"]]
        ncol = len(b["header"])
        widths = b.get("widths")
        cw = [avail * w / sum(widths) for w in widths] if widths else [avail / ncol] * ncol
        tbl = Table([header] + rows, colWidths=cw, repeatRows=1)
        st = [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(accent)),
              ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c8cdd2")),
              ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
              ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]
        for i in range(1, len(rows) + 1):
            if i % 2 == 0:
                st.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#f3f5f7")))
        tbl.setStyle(TableStyle(st))
        out = [Spacer(1, 4), tbl]
        out.append(Paragraph(fmt(b["caption"]), s["caption"]) if b.get("caption") else Spacer(1, 10))
        return [KeepTogether(out)] if len(rows) < 14 else out
    if t == "chart":
        out = [chart_image(b, accent, avail)]
        if b.get("caption"):
            out.append(Paragraph(fmt(b["caption"]), s["caption"]))
        return [KeepTogether(out)]
    raise ValueError(f"unknown block type {t}")


def build(json_path, out_dir):
    d = json.load(open(json_path, encoding="utf-8"))
    accent = d.get("color", "#1f4e79")
    s = styles(accent)
    out = os.path.join(out_dir, os.path.splitext(os.path.basename(json_path))[0] + ".pdf")
    title = d["title"]

    def cover(c, doc):
        c.saveState()
        c.setFillColor(colors.HexColor(accent)); c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#ffffff")); c.setFillAlpha(0.08)
        c.circle(PAGE_W * 0.85, PAGE_H * 0.78, 140, fill=1, stroke=0)
        c.circle(PAGE_W * 0.1, PAGE_H * 0.15, 90, fill=1, stroke=0)
        c.setFillAlpha(1)
        c.setFont("NanumB", 11); c.drawString(MARGIN, PAGE_H - 30 * mm, d.get("series", "FINANCE REPORT"))
        c.setLineWidth(1.2); c.setStrokeColor(colors.white)
        c.line(MARGIN, PAGE_H - 33 * mm, MARGIN + 40 * mm, PAGE_H - 33 * mm)
        y = PAGE_H * 0.58
        for line in title.split("\n"):
            c.setFont("NanumEB", 28); c.drawString(MARGIN, y, line); y -= 40
        c.setFont("Nanum", 13)
        for line in d.get("subtitle", "").split("\n"):
            y -= 4; c.drawString(MARGIN, y, line); y -= 20
        c.setFont("Nanum", 10)
        c.drawString(MARGIN, 30 * mm, f"발행일 {d.get('date', date.today().isoformat())}")
        c.drawString(MARGIN, 24 * mm, "교육·참고용 자료 | 투자 권유 아님")
        c.restoreState()

    def normal(c, doc):
        c.saveState()
        c.setFillColor(colors.HexColor(accent)); c.rect(0, PAGE_H - 9 * mm, PAGE_W, 9 * mm, fill=1, stroke=0)
        c.setFillColor(colors.white); c.setFont("NanumB", 8.5)
        c.drawString(MARGIN, PAGE_H - 6 * mm, title.replace("\n", " "))
        c.setFillColor(colors.HexColor("#888888")); c.setFont("Nanum", 8)
        c.drawRightString(PAGE_W - MARGIN, 10 * mm, f"{doc.page}")
        c.drawString(MARGIN, 10 * mm, d.get("series", ""))
        c.restoreState()

    doc = BaseDocTemplate(out, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
                          topMargin=18 * mm, bottomMargin=18 * mm, title=title.replace("\n", " "),
                          author="Finance Research Notes")
    frame = Frame(MARGIN, 18 * mm, PAGE_W - 2 * MARGIN, PAGE_H - 36 * mm, id="f")
    doc.addPageTemplates([PageTemplate("cover", frames=[frame], onPage=cover),
                          PageTemplate("normal", frames=[frame], onPage=normal)])
    avail = PAGE_W - 2 * MARGIN
    story = [NextPageTemplate("normal"), PageBreak()]
    # Summary + TOC page
    story.append(Paragraph("요약 (Executive Summary)", s["h1"]))
    for p in d.get("summary", []):
        story.append(Paragraph(fmt(p), s["bullet"], bulletText="▪"))
    story.append(Spacer(1, 14))
    story.append(Paragraph("목차", s["h1"]))
    for i, sec in enumerate(d["sections"], 1):
        story.append(Paragraph(f"{i}.&nbsp;&nbsp;{fmt(sec['heading'])}", s["toc"]))
    for i, sec in enumerate(d["sections"], 1):
        story.append(PageBreak() if i == 1 or sec.get("new_page") else Spacer(1, 10))
        story.append(Paragraph(f"{i}. {fmt(sec['heading'])}", s["h1"]))
        for b in sec["blocks"]:
            story.extend(render_block(b, s, accent, avail))
    story.append(Spacer(1, 16))
    story.extend(render_block({"type": "callout", "title": "유의사항",
                               "text": d.get("disclaimer", "본 자료는 금융 지식 전달을 위한 교육·참고용 자료이며, 특정 금융상품의 매수·매도를 권유하지 않습니다. 본문의 수치 중 '예시' 또는 '가상'으로 표기된 값은 이해를 돕기 위한 가정이며 실제 시장 데이터가 아닙니다. 제도·세율·규제는 개정될 수 있으므로 실제 의사결정 전 최신 공시와 전문가 상담을 확인하시기 바랍니다.")},
                              s, accent, avail))
    doc.build(story)
    return out, doc.page


if __name__ == "__main__":
    paths = sys.argv[1:] or sorted(glob.glob(os.path.join(os.path.dirname(__file__), "..", "content", "*.json")))
    out_dir = os.path.join(os.path.dirname(__file__), "..", "pdf")
    for p in paths:
        o, n = build(p, out_dir)
        print(f"{n:3d} pages  {os.path.basename(o)}")
