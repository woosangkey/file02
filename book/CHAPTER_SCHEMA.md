# Chapter JSON schema (rendered by scripts/build_book.py)

```json
{
  "no": 3,                                  // 장 번호 (부록은 "A")
  "title": "듀레이션·컨벡시티·DV01 실전",
  "level": "중급 | 상급 | 하이엔드",
  "objectives": ["이 장을 마치면 ~할 수 있다", "... 3~4개"],
  "sections": [
    {"heading": "섹션 제목(번호 붙이지 말 것)", "blocks": [
      {"type": "p", "text": "본문. **굵게** 지원"},
      {"type": "h2", "text": "소제목"},
      {"type": "bullets", "items": ["..."]},
      {"type": "table", "header": ["..."], "rows": [["..."]], "widths": [1,2], "caption": "표 3-1. ..."},
      {"type": "chart", "kind": "line|area|bar|barh|stacked|pie", "title": "...", "x": ["..."],
       "series": {"이름": [숫자...]}, "ylabel": "단위", "caption": "그림 3-1. ... (예시 데이터)"},
      {"type": "callout", "title": "실무 팁 / 판매자 노트 / 주의 등", "text": "..."},
      {"type": "formula", "text": "유니코드 수식 한 줄 (LaTeX 금지)", "note": "기호 설명"}
    ]}
  ],
  "takeaways": ["핵심 정리 4~6개"],
  "quiz": [{"q": "점검 문제", "a": "해설(계산 과정 포함)"}]   // 3~4문항
}
```
- pie 는 series 1개. 모든 series 배열 길이 = x 길이.
- JSON 문자열 안 큰따옴표 금지(「」 또는 ' 사용).
