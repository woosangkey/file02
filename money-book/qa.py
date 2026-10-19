#!/usr/bin/env python3
"""조판 점검: 글자가 거의 없는 쪽(고아 쪽)과 빈 쪽 목록."""
import sys
from pypdf import PdfReader
r = PdfReader(sys.argv[1])
for i, p in enumerate(r.pages, 1):
    t = (p.extract_text() or "").strip()
    n = len("".join(t.split()))
    if 0 < n < 260:
        print(f"p{i}: {n} chars | {t[:70]!r}")
