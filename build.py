#!/usr/bin/env python3
"""data/mNN.json, data/final.json → data/mNN.js, data/final.js (앱이 읽는 파일)

사용법: python3 build.py
"""
import json
import pathlib

D = pathlib.Path(__file__).parent / "data"
for f in sorted(D.glob("m[0-9][0-9].json")):
    days = json.loads(f.read_text(encoding="utf-8"))
    a, b = min(map(int, days)), max(map(int, days))
    f.with_suffix(".js").write_text(
        f"// {int(f.stem[1:])}개월차 (Day {a}~{b}) — build.py 가 data/{f.name} 에서 생성\n"
        "window.N1_DAYS = Object.assign(window.N1_DAYS || {}, "
        + json.dumps(days, ensure_ascii=False) + ");\n", encoding="utf-8")
    print(f.name, len(days), "일")
fin = D / "final.json"
if fin.exists():
    (D / "final.js").write_text("// Day 365 졸업 모의고사 — build.py 생성\nwindow.N1_FINAL = "
                                + fin.read_text(encoding="utf-8").strip() + ";\n", encoding="utf-8")
    print("final.json")
