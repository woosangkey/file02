#!/usr/bin/env python3
"""하루 단위 일본어 음성 파일 생성 (오프라인 음성합성 Open JTalk).

기기에 일본어 음성(TTS)이 없어도 들을 수 있도록 Day마다 mp3 한 개(audio/dNNN.mp3)를 만들고,
문장별 시작 위치를 data/audio-index.js 에 기록한다. 졸업 모의고사 청해는 audio/final.mp3.

준비: pip install pyopenjtalk-plus numpy  (ffmpeg 필요)
사용법: python3 gen_audio.py            # 전체
        python3 gen_audio.py 1 2 final  # 특정 Day만 다시
"""
import json
import os
import pathlib
import re
import subprocess
import sys
import wave
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pyopenjtalk

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "audio"
INDEX = ROOT / "data" / "audio-index.js"
GAP = 0.4  # 문장 사이 무음(초)

# 화자별 음높이(반음) — 청해에서 누가 말하는지 구분되도록
PITCH = {"男": -5, "女": 1, "男の学生": -3, "女の学生": 2, "部長": -7, "課長": -6, "店員": 0, "客": -4,
         "司会": -2, "先生": -5, "医者": -6, "社長": -7, "係員": -1, "アナウンサー": 0}


def pitch_of(who):
    if who in PITCH:
        return PITCH[who]
    if who and "女" in who:
        return 1
    if who and "男" in who:
        return -5
    return 0


def kata(s):
    return "".join(chr(ord(c) + 0x60) if "ぁ" <= c <= "ゖ" else c for c in s)


def skeleton(s):
    """장음·조사 표기 차이를 무시하고 읽기를 비교하기 위한 뼈대."""
    s = kata(s).replace("ワ", "ハ").replace("ヲ", "オ").replace("ヘ", "エ")
    return re.sub(r"[^ァ-ヶ]|[ーウオイエ]", "", s)


def prepare(ja, kana):
    """음성합성기의 읽기가 데이터의 요미가나와 다르면 요미가나로 읽힌다."""
    if kana:
        k = kana.replace(" ", "").replace("　", "")
        if skeleton(pyopenjtalk.g2p(ja, kana=True)) != skeleton(k):
            return k
    return ja


def items_of(D):
    out = [(D["passage"]["ja"], "", "")]
    out += [(l["ja"], l.get("kana", ""), l.get("who", "")) for l in D["lines"]]
    out += [(x["ja"], x.get("kana", ""), "") for x in D["grammar"]["ex"]]
    out += [(D["missionEx"]["ja"], D["missionEx"].get("kana", ""), "")]
    out += [(D["compare"]["exA"], "", ""), (D["compare"]["exB"], "", "")]
    out += [(w["w"], w["r"], "") for w in D["words"]]
    return out


def render(job):
    name, items = job
    seen, chunks, pos, sr = {}, [], 0.0, 48000
    for ja, kana, who in items:
        if not ja or ja in seen:
            continue
        x, sr = pyopenjtalk.tts(prepare(ja, kana), half_tone=pitch_of(who))
        x = x.astype(np.float32)
        x = x / max(1.0, np.abs(x).max() / 30000)
        dur = len(x) / sr
        seen[ja] = [round(pos, 3), round(dur, 3)]
        chunks += [x, np.zeros(int(GAP * sr), dtype=np.float32)]
        pos += dur + GAP
    pcm = np.concatenate(chunks).clip(-32768, 32767).astype(np.int16)
    tmp = OUT / f"{name}.wav"
    with wave.open(str(tmp), "wb") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(sr); f.writeframes(pcm.tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(tmp), "-ar", "24000", "-ac", "1",
                    "-b:a", "32k", str(OUT / f"{name}.mp3")], check=True)
    tmp.unlink()
    return name, seen


def main():
    OUT.mkdir(exist_ok=True)
    days = {}
    for f in sorted((ROOT / "data").glob("m[0-9][0-9].json")):
        days.update(json.loads(f.read_text(encoding="utf-8")))
    only = set(sys.argv[1:])
    jobs = [(f"d{int(k):03d}", items_of(D)) for k, D in days.items() if not only or k in only]
    fin = ROOT / "data" / "final.json"
    if fin.exists() and (not only or "final" in only):
        F = json.loads(fin.read_text(encoding="utf-8"))
        jobs.append(("final", [(l["ja"], "", l.get("who", "")) for q in F["qs"] for l in q.get("script", [])]))

    index = {}
    if INDEX.exists() and only:
        index = json.loads(INDEX.read_text(encoding="utf-8").split("=", 1)[1].rstrip().rstrip(";"))
    with ProcessPoolExecutor(max(1, os.cpu_count() or 1)) as ex:
        for name, seen in ex.map(render, jobs):
            index[name] = seen
            print(name, len(seen), file=sys.stderr)
    INDEX.write_text("// gen_audio.py 가 자동 생성합니다.\nwindow.N1_AUDIO = "
                     + json.dumps(dict(sorted(index.items())), ensure_ascii=False) + ";\n", encoding="utf-8")
    print(f"완료: {len(jobs)}개 파일")


if __name__ == "__main__":
    main()
