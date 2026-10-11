# 일일 교재 JSON (study/days/dayNNN.json) — 렌더링 시 A4 약 10쪽
```json
{
  "day": 1, "month": 1, "type": "학습일 | 실전 드릴 | 주간 복습",
  "title": "오늘의 제목", "time": "예상 학습시간 (예: 약 90분)",
  "objectives": ["오늘의 학습 목표 3개"],
  "warmup": [{"q": "어제 내용 확인 질문", "a": "정답"}],      // Day 1 은 [] 가능
  "sections": [ {"heading": "섹션 제목", "blocks": [ ...블록... ]} ],
  "practice": [{"q": "연습문제", "a": "정답과 해설(계산 과정)"}],
  "takeaways": ["오늘의 핵심 정리 4~5개"],
  "glossary": [["용어", "정의"]],                              // 오늘 나온 용어 6~10개
  "tomorrow": "내일 학습 예고 한두 문장"
}
```
블록 타입은 /home/user/file02/book/CHAPTER_SCHEMA.md 와 동일
(p, h2, bullets, table, chart, callout, formula). pie 는 series 1개, series 길이 = x 길이.
JSON 문자열 안 큰따옴표 금지(「」 사용).
