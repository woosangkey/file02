#!/usr/bin/env python3
"""data/q1~q4.json → app/data.js (웹 앱용) + weeks/weekNN.md (인쇄/열람용) 생성.

사용법: python3 build.py
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent
DATA = ROOT / "data"
WEEKS_DIR = ROOT / "weeks"
APP_DATA = ROOT / "app" / "data.js"

# 요일별 학습 루틴 (하루 20~30분). sections 는 앱/마크다운에서 그날 보여 줄 자료.
ROUTINE = [
    {
        "day": 1, "name": "장면·단어", "minutes": 20,
        "sections": ["scene", "kana", "vocab"],
        "tasks": [
            "이번 주 장면 설명과 목표를 읽는다",
            "단어 10개를 듣고 하나당 3번씩 소리 내어 따라 한다",
            "단어를 노트에 한 번씩 쓰고 뜻을 가린 채 셀프 테스트한다",
            "(가나가 있는 주) 이번 주 가나를 5번씩 쓰며 소리 낸다",
        ],
    },
    {
        "day": 2, "name": "문법·핵심표현", "minutes": 25,
        "sections": ["grammar", "phrases"],
        "tasks": [
            "문법 설명을 읽고 예문 4개를 듣고 따라 한다",
            "예문을 바꿔서 '나에 관한' 문장 3개를 노트에 쓴다",
            "핵심표현 5개를 듣고 3번씩 따라 말한다",
            "어제 단어를 뜻만 보고 일본어로 말해 본다",
        ],
    },
    {
        "day": 3, "name": "듣기", "minutes": 20,
        "sections": ["dialogue_hidden", "quiz"],
        "tasks": [
            "대본을 가린 채 대화를 2번 듣는다",
            "듣기 퀴즈 3문제를 푼다",
            "대본을 보면서 다시 듣고, 못 들은 부분에 표시한다",
            "표시한 문장만 3번 더 듣는다",
        ],
    },
    {
        "day": 4, "name": "쉐도잉", "minutes": 25,
        "sections": ["dialogue"],
        "tasks": [
            "한 줄씩 듣고 멈춘 뒤 똑같이 따라 말한다 (전체 2회)",
            "대본을 보며 소리와 동시에 겹쳐 말한다 (쉐도잉 3회)",
            "한국어 번역만 보고 일본어로 말해 본다",
            "가장 어려운 문장 1개를 외운다",
        ],
    },
    {
        "day": 5, "name": "말하기", "minutes": 25,
        "sections": ["speaking", "roleplay", "phrases"],
        "tasks": [
            "역할극: 캐릭터 하나를 골라 내 대사를 직접 말한다 (상대 대사는 음성)",
            "역할을 바꿔서 한 번 더 한다",
            "말하기 과제를 1분 동안 휴대폰으로 녹음한다",
            "녹음을 듣고 고칠 점 1가지를 메모한다",
        ],
    },
    {
        "day": 6, "name": "받아쓰기·쓰기", "minutes": 30,
        "sections": ["dictation", "writing"],
        "tasks": [
            "받아쓰기 3문장 (들리는 대로 쓰고 정답 확인)",
            "쓰기 과제를 노트에 쓴다",
            "모범 답안과 비교해 고친 뒤 소리 내어 읽는다",
        ],
    },
    {
        "day": 7, "name": "주간 복습", "minutes": 25,
        "sections": ["vocab_test", "dialogue", "prev_phrases", "selfcheck"],
        "tasks": [
            "단어 셀프 테스트: 10개 중 8개 이상이면 통과",
            "대화문 전체를 대본 없이 말해 본다 (막히면 대본 보기)",
            "지난주 핵심표현 5개를 다시 말해 본다",
            "말하기·듣기·쓰기 자기평가(1~5점)를 기록한다",
        ],
    },
]

FINAL_DAY = {
    "day": 365, "name": "최종 평가", "minutes": 60,
    "tasks": [
        "듣기: 무작위 대화 5개를 대본 없이 듣고 내용을 한국어로 요약한다 (4개 이상 이해하면 합격)",
        "말하기: '나의 1년과 일본어' 3분 발표를 녹음한다 (1주차 녹음과 비교해 보기)",
        "쓰기: '내가 좋아하는 슬램덩크 장면' 400자 작문 (원고지 형식)",
        "받아쓰기: 무작위 문장 10개 (8개 이상 정답이면 합격)",
        "1년 동안 기록한 자기평가 점수를 그래프로 그려 본다",
    ],
}

COUNTS = {"vocab": 10, "phrases": 5, "quiz": 3, "dictation": 3}


def load_weeks():
    weeks = []
    for q in range(1, 5):
        path = DATA / f"q{q}.json"
        if not path.exists():
            print(f"[경고] {path.name} 없음 — 건너뜀", file=sys.stderr)
            continue
        weeks.extend(json.loads(path.read_text(encoding="utf-8")))
    weeks.sort(key=lambda w: w["week"])
    return weeks


def validate(weeks):
    problems = []
    for w in weeks:
        n = w["week"]
        for key, count in COUNTS.items():
            if len(w.get(key, [])) != count:
                problems.append(f"{n}주 {key}: {len(w.get(key, []))}개 (기대 {count})")
        if len(w["grammar"]["examples"]) != 4:
            problems.append(f"{n}주 grammar.examples: {len(w['grammar']['examples'])}개")
        if not 8 <= len(w["dialogue"]) <= 10:
            problems.append(f"{n}주 dialogue: {len(w['dialogue'])}줄")
    nums = [w["week"] for w in weeks]
    if nums != list(range(1, len(nums) + 1)):
        problems.append(f"주차 번호가 연속되지 않음: {nums}")
    return problems


def md_escape(s):
    return s.replace("|", "\\|")


def table(rows, cols):
    head = "| " + " | ".join(c[0] for c in cols) + " |\n"
    head += "|" + "---|" * len(cols) + "\n"
    body = "".join(
        "| " + " | ".join(md_escape(str(r.get(c[1], ""))) for c in cols) + " |\n"
        for r in rows
    )
    return head + body


def week_md(w, prev):
    n = w["week"]
    first_day = (n - 1) * 7 + 1
    out = [f"# {n}주차 · {w['title']}\n"]
    out.append(f"**Day {first_day}–{first_day + 6}** · 문법: `{w['grammar']['point']}`\n")
    out.append(f"> {w['scene']}\n")
    out.append(f"**이번 주 목표:** {w['goal']}\n")
    if w.get("kana"):
        out.append(f"**이번 주 가나:** {w['kana']}\n")

    out.append("## 7일 학습 계획\n")
    for r in ROUTINE:
        out.append(f"### Day {first_day + r['day'] - 1} — {r['name']} (약 {r['minutes']}분)\n")
        out.extend(f"- [ ] {t}\n" for t in r["tasks"])
        out.append("")

    out.append("## 단어\n")
    out.append(table(w["vocab"], [("일본어", "ja"), ("읽기", "yomi"), ("뜻", "ko")]))

    g = w["grammar"]
    out.append(f"## 문법: {g['point']}\n")
    out.append(g["explain"] + "\n")
    out.append(table(g["examples"], [("예문", "ja"), ("읽기", "yomi"), ("뜻", "ko")]))

    out.append("## 핵심표현\n")
    out.append(table(w["phrases"], [("표현", "ja"), ("읽기", "yomi"), ("뜻", "ko")]))

    out.append("## 대화\n")
    out.append(table(w["dialogue"], [("인물", "who"), ("대사", "ja"), ("읽기", "yomi"), ("뜻", "ko")]))

    out.append("## 듣기 퀴즈\n")
    for i, q in enumerate(w["quiz"], 1):
        out.append(f"{i}. {q['q']}\n   <details><summary>정답</summary>{q['a']}</details>\n")

    out.append("\n## 받아쓰기 (정답)\n")
    out.append("<details><summary>정답 보기 — 먼저 앱에서 듣고 쓰세요</summary>\n")
    out.extend(f"{i}. {s}\n" for i, s in enumerate(w["dictation"], 1))
    out.append("</details>\n")

    out.append("## 말하기 과제\n")
    out.append(w["speaking"] + "\n")

    out.append("## 쓰기 과제\n")
    out.append(w["writing"] + "\n")
    ex = w["writingExample"]
    out.append(f"<details><summary>모범 답안</summary>\n\n{ex['ja']}\n\n{ex['ko']}\n</details>\n")

    if prev:
        out.append("## 지난주 핵심표현 복습 (Day 7)\n")
        out.extend(f"- {p['ja']} — {p['ko']}\n" for p in prev["phrases"])
        out.append("")

    out.append("## 자기평가 (Day 7)\n")
    out.append("| 영역 | 1 | 2 | 3 | 4 | 5 |\n|---|---|---|---|---|---|\n")
    out.extend(f"| {a} | ☐ | ☐ | ☐ | ☐ | ☐ |\n" for a in ("말하기", "듣기", "쓰기"))

    nav = []
    if n > 1:
        nav.append(f"[← {n - 1}주차](week{n - 1:02d}.md)")
    nav.append("[목차](README.md)")
    if n < 52:
        nav.append(f"[{n + 1}주차 →](week{n + 1:02d}.md)")
    out.append("\n---\n" + " · ".join(nav) + "\n")
    return "\n".join(out)


def index_md(weeks):
    out = ["# 주차별 학습지 목차\n"]
    out.append("| 주 | Day | 제목 | 문법 |\n|---|---|---|---|\n")
    for w in weeks:
        n = w["week"]
        d = (n - 1) * 7 + 1
        out.append(f"| [{n}주](week{n:02d}.md) | {d}–{d + 6} | {w['title']} | {md_escape(w['grammar']['point'])} |\n")
    out.append("| [최종](final.md) | 365 | 최종 평가 | 종합 |\n")
    return "".join(out)


def final_md():
    out = ["# Day 365 · 최종 평가\n"]
    out.extend(f"- [ ] {t}\n" for t in FINAL_DAY["tasks"])
    out.append("\n앱에서 Day 365를 열면 무작위 듣기·받아쓰기 문제가 자동으로 나옵니다.\n")
    return "".join(out)


def main():
    weeks = load_weeks()
    problems = validate(weeks)
    for p in problems:
        print("[검증]", p, file=sys.stderr)

    WEEKS_DIR.mkdir(exist_ok=True)
    for i, w in enumerate(weeks):
        prev = weeks[i - 1] if i > 0 else None
        (WEEKS_DIR / f"week{w['week']:02d}.md").write_text(week_md(w, prev), encoding="utf-8")
    (WEEKS_DIR / "README.md").write_text(index_md(weeks), encoding="utf-8")
    (WEEKS_DIR / "final.md").write_text(final_md(), encoding="utf-8")

    APP_DATA.parent.mkdir(exist_ok=True)
    payload = {"weeks": weeks, "routine": ROUTINE, "final": FINAL_DAY}
    APP_DATA.write_text(
        "// build.py 가 자동 생성합니다. 직접 수정하지 말고 data/*.json 을 고친 뒤 다시 빌드하세요.\n"
        "window.COURSE = " + json.dumps(payload, ensure_ascii=False, indent=1) + ";\n",
        encoding="utf-8",
    )
    print(f"{len(weeks)}주 빌드 완료 → weeks/, app/data.js")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
