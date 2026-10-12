# 30일 집중 과정 일일 교재 공통 지침

- 과정: 「채권투자 30일 집중 과정」 — 하루 A4 10쪽, 30일 동안 중급 계산 → 분석 → 운용 → 하이엔드 판매자까지 압축 완주. 독자: 금융권 실무자·PB·채권 세일즈·투자자. 하루 약 2시간.
- 커리큘럼 전체: /home/user/file02/study/syllabus30.json (자기 날의 title·topics·deliverable 를 반드시 반영하고, 다른 날 주제는 한두 줄 예고·참조만).
- 1주차 완성 교재(형식·문체·분량의 기준): /home/user/file02/study30/days/day02.json, day05.json 을 먼저 훑어볼 것(문장 복사 금지).
- **시장 수치**: /home/user/file02/study30/MARKET_2026-10.md 를 읽고 그 규칙대로 「2026년 10월 초 수준」 실제 수치를 예제·표·시황 설명에 적극 활용할 것. 이 과정은 2026년 10월 현재 시장(한·미 금리 인상기, 장기금리 상승)을 반영하는 것이 중요하다.
- 스키마: /home/user/file02/study/DAY_SCHEMA.md, 블록 정의: /home/user/file02/book/CHAPTER_SCHEMA.md. 파일명 /home/user/file02/study30/days/dayNN.json (두 자리), 필드 day=N, month=주차번호(1~5), type 「학습일」「실전 드릴」「주간 복습」, time.
- 분량(렌더링 시 A4 약 10쪽): 학습일은 sections 5~6, 본문(p/bullets/callout) 9,000~10,000자, chart 2~3, table 3~4, callout 4개 이상(「예제」 단계별 계산, 「실무 팁」, 「판매자 노트」, 「2026년 10월 시장에서는」, 「자주 하는 오해」 등), formula 주제에 맞게, practice 8(해설에 계산 과정), takeaways 5, glossary 8~10, warmup 2(전날 내용), tomorrow(다음 날 예고). 드릴·복습일은 각자 지시 참고.
- 문체: 친절하지만 전문적인 교재 문체(~이다/~한다), 문단 250~400자.
- 정확성: 모든 계산은 python으로 검산. 실존 기업을 분석·추천하지 말고 가상 기업 사용. 세율·법령·거래소 명세는 확실한 일반 원칙만, 「개정될 수 있음 / 최신 기준 확인」 표기. JSON 문자열 안 큰따옴표 금지(「」 사용). 차트 series 길이 = x 길이, pie 는 series 1개.
- 작성 후 python 으로 json.load, 글자수, series 길이를 검증. 최종 응답은 파일별 글자수와 블록 구성 한 줄씩.
- scratchpad 를 다른 작성자와 공유하므로 임시 스크립트는 자기 이름의 하위 폴더(예: scratchpad/d30_08/)에 둘 것.
