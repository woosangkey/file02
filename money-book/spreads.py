#!/usr/bin/env python3
"""PDF를 펼침면(좌·우 2쪽) PNG로 렌더링. 1쪽(표지)은 단독 오른쪽 페이지."""
import os, subprocess, sys
from PIL import Image

pdf, outdir = sys.argv[1], sys.argv[2]
os.makedirs(outdir, exist_ok=True)
for f in os.listdir(outdir):
    os.remove(os.path.join(outdir, f))
tmp = os.path.join(outdir, "_p")
subprocess.run(["pdftoppm", "-png", "-r", "110", pdf, tmp], check=True)
pages = sorted(f for f in os.listdir(outdir) if f.startswith("_p"))
imgs = [Image.open(os.path.join(outdir, f)).convert("RGB") for f in pages]
w, h = imgs[0].size
blank = Image.new("RGB", (w, h), "white")
seq = [blank] + imgs
if len(seq) % 2:
    seq.append(blank)
for i in range(0, len(seq), 2):
    canvas = Image.new("RGB", (w * 2 + 40, h + 40), "#d9dbe0")
    canvas.paste(seq[i], (20, 20)); canvas.paste(seq[i + 1], (20 + w, 20))
    canvas.save(os.path.join(outdir, f"spread-{i//2:02d}.png"))
for f in pages:
    os.remove(os.path.join(outdir, f))
print("spreads:", len(seq) // 2)
