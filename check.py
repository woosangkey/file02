#!/usr/bin/env python3
"""data/mNN.json 형식 검사. 사용법: python3 check.py [data/m01.json ...]"""
import json, sys, glob
files = sys.argv[1:] or sorted(glob.glob("data/m*.json"))
bad = 0
for f in files:
    d = json.load(open(f, encoding="utf-8"))
    pos = [0, 0, 0, 0]
    for k, x in d.items():
        p = f"{f} Day {k}"
        def err(m):
            global bad; bad += 1; print(p, m)
        if int(k) != x["day"] or int(k) % 7 == 0 or int(k) % 30 == 0: err("day 번호 오류")
        for key in ["part", "title", "topic", "passage", "lines", "words", "grammar", "compare", "mission", "missionEx", "quiz"]:
            if key not in x: err("누락 " + key)
        if not 4 <= len(x["lines"]) <= 6: err(f"lines {len(x['lines'])}")
        if len(x["words"]) != 8: err(f"words {len(x['words'])}")
        if len(x["grammar"]["ex"]) != 3: err("grammar.ex != 3")
        if len(x["quiz"]) != 3: err("quiz != 3")
        for q in x["quiz"]:
            if len(q["choices"]) != 4 or not 0 <= q["a"] <= 3: err("quiz 보기/정답 오류")
            pos[q["a"]] += 1
        n = len(x["passage"]["ja"])
        if not 180 <= n <= 450: err(f"passage {n}자")
        for l in x["lines"] + x["grammar"]["ex"] + [x["missionEx"]]:
            if not l.get("kana"): err("kana 없음: " + l["ja"][:15])
    print(f"{f}: {len(d)}일, 정답 위치 분포 {pos}")
print("오류", bad)
sys.exit(1 if bad else 0)
