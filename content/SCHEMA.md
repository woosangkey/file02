# Content JSON schema (rendered by scripts/build.py)

```json
{
  "title": "보고서 제목 (줄바꿈은 \n, 최대 2줄, 줄당 14자 내외)",
  "subtitle": "부제 (줄바꿈 \n 가능)",
  "series": "영문 시리즈 라벨, 예: FINANCE REPORT No.03",
  "color": "#1f4e79",            // 문서별 대표색 (진한 색)
  "date": "2026-10-12",
  "summary": ["핵심 요약 문장 5~6개, **굵게** 가능"],
  "sections": [
    {"heading": "섹션 제목", "new_page": false, "blocks": [
      {"type": "p", "text": "본문 문단. **굵게** 지원"},
      {"type": "h2", "text": "소제목"},
      {"type": "bullets", "items": ["항목", "항목"]},
      {"type": "table", "header": ["열1","열2"], "rows": [["a","b"]], "widths": [1,2], "caption": "표 1. ..."},
      {"type": "chart", "kind": "line|area|bar|barh|stacked|pie", "title": "차트 제목",
       "x": ["라벨", ...], "series": {"시리즈명": [숫자, ...]}, "ylabel": "단위", "caption": "그림 1. ... (예시 데이터)"},
      {"type": "callout", "title": "박스 제목", "text": "강조 박스 내용"},
      {"type": "formula", "text": "수식 한 줄 (유니코드 기호 사용, LaTeX 금지)", "note": "기호 설명"}
    ]}
  ]
}
```
pie: series 는 1개만. 모든 series 배열 길이 = x 길이.
