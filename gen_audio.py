#!/usr/bin/env python3
"""주차별 일본어 음성 파일 생성 (오프라인 음성합성 Open JTalk).

기기 음성(TTS)이 없는 휴대폰·앱에서도 들을 수 있도록 주마다 mp3 한 개(audio/wNN.mp3)를 만들고,
문장별 시작 위치를 app/audio-index.js 에 기록한다.

준비: pip install pyopenjtalk-plus numpy  (ffmpeg 필요)
사용법: python3 gen_audio.py
"""
import json
import pathlib
import re
import subprocess
import sys
import wave

import numpy as np
import pyopenjtalk

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "audio"
INDEX = ROOT / "app" / "audio-index.js"
GAP = 0.35  # 문장 사이 무음(초)

# 음성합성기가 잘못 읽는 고유명사 → 읽기
NAMES = {
    "桜木": "さくらぎ", "花道": "はなみち", "晴子": "はるこ", "赤木": "あかぎ", "剛憲": "たけのり",
    "流川": "るかわ", "宮城": "みやぎ", "三井": "みつい", "木暮": "こぐれ", "安西": "あんざい",
    "彩子": "あやこ", "洋平": "ようへい", "仙道": "せんどう", "魚住": "うおずみ", "藤真": "ふじま",
    "花形": "はながた", "清田": "きよた", "沢北": "さわきた", "深津": "ふかつ", "湘北": "しょうほく",
    "陵南": "りょうなん", "海南": "かいなん", "翔陽": "しょうよう", "山王": "さんのう", "豊玉": "とよたま",
    "三浦台": "みうらだい", "牧": "まき", "楓": "かえで", "寿": "ひさし",
}
# 인물별 음높이(반음) — 대화에서 누가 말하는지 구분되도록
PITCH = {"桜木": -3, "赤木": -6, "流川": -4, "宮城": -2, "三井": -3, "木暮": -2, "安西先生": -7,
         "洋平": -2, "仙道": -4, "魚住": -6, "牧": -5, "藤真": -2, "花形": -4, "清田": -1,
         "沢北": -3, "深津": -5, "記者": -2, "店員": 0, "先生": -4, "晴子": 1, "彩子": 0, "母": 0}


def kata(s):
    return "".join(chr(ord(c) + 0x60) if "ぁ" <= c <= "ゖ" else c for c in s)


def skeleton(s):
    """장음·조사 표기 차이를 무시하고 읽기를 비교하기 위한 뼈대."""
    s = kata(s).replace("ワ", "ハ").replace("ヲ", "オ")
    return re.sub(r"[^ァ-ヶ]|[ーウオイエ]", "", s)


def prepare(ja, yomi):
    text = ja
    for k in sorted(NAMES, key=len, reverse=True):
        text = text.replace(k, NAMES[k])
    if yomi and skeleton(pyopenjtalk.g2p(text, kana=True)) != skeleton(yomi):
        return yomi, True  # 읽기가 다르면 데이터의 읽는 법(yomi)으로 합성
    return text, False


def synth(text, who):
    x, sr = pyopenjtalk.tts(text, half_tone=PITCH.get(who, 0))
    return x.astype(np.float32), sr


def main():
    weeks = []
    for q in range(1, 5):
        weeks += json.loads((ROOT / "data" / f"q{q}.json").read_text(encoding="utf-8"))
    OUT.mkdir(exist_ok=True)
    index, fallback = {}, 0
    for w in weeks:
        n = w["week"]
        items = []
        for x in w["vocab"] + w["grammar"]["examples"] + w["phrases"] + w["dialogue"]:
            items.append((x["ja"], x.get("yomi", ""), x.get("who", "")))
        items.append((w["writingExample"]["ja"], "", ""))
        seen, chunks, pos, sr = {}, [], 0.0, 48000
        for ja, yomi, who in items:
            key = (ja, who)
            if key in seen:
                continue
            text, fb = prepare(ja, yomi)
            fallback += fb
            x, sr = synth(text, who)
            x = x / max(1.0, np.abs(x).max() / 30000)
            dur = len(x) / sr
            seen[key] = [round(pos, 3), round(dur, 3)]
            chunks += [x, np.zeros(int(GAP * sr), dtype=np.float32)]
            pos += dur + GAP
        pcm = np.concatenate(chunks).clip(-32768, 32767).astype(np.int16)
        tmp = OUT / f"w{n:02d}.wav"
        with wave.open(str(tmp), "wb") as f:
            f.setnchannels(1); f.setsampwidth(2); f.setframerate(sr); f.writeframes(pcm.tobytes())
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(tmp), "-ar", "24000", "-ac", "1",
                        "-b:a", "40k", str(OUT / f"w{n:02d}.mp3")], check=True)
        tmp.unlink()
        index[n] = {f"{who}\t{ja}": v for (ja, who), v in seen.items()}
        print(f"{n}주: {len(seen)}문장 {pos:.0f}초", file=sys.stderr)
    INDEX.write_text("// gen_audio.py 가 자동 생성합니다.\nwindow.AUDIO_INDEX = "
                     + json.dumps(index, ensure_ascii=False) + ";\n", encoding="utf-8")
    print(f"완료 (읽는 법으로 대체 합성: {fallback}문장)")


if __name__ == "__main__":
    main()
