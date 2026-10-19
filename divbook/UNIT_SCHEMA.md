# 단위 원고 JSON 스키마 (divbook/units/*.json)
```json
{
  "id": "p0_c1",                 // 파일명과 같게
  "part": 0,                     // 0=준비마당, 1~5=실전마당
  "kind": "principle | practice",
  "no": 1,                       // principle 일 때 원칙 번호
  "title": "고배당 ETF 몰빵 투자는 피한다",   // principle 일 때 원칙 제목 (practice 는 생략 가능)
  "lead": "원칙 도입 인용문 1~2문장 (principle 만)",
  "sections": [
    {"heading": "목차에 있는 제목 그대로",
     "level": 1,                // 1 = 큰 절(새 쪽에서 시작: 실전마당의 01/02/03 절, 각 실전사례), 2 = 일반 소절
     "tag": "",                 // "" | "양동석 pick" | "Tip" | "실전사례" | "실전 체감"
     "persona": {"name": "김종현", "age": "62세", "job": "은퇴자", "assets": "금융자산 1.5억 원 …", "concern": "고민 한 줄"},  // 실전사례만
     "blocks": [ ...블록... ]}
  ],
  "summary": ["원칙/절 핵심 정리 3~5개"]   // principle 필수, practice 는 마지막 단위만 선택
}
```
- 목차의 소제목은 빠짐없이 sections 로 만들고, heading 은 목차 문구를 그대로 쓴다(「곤쌤」→「양동석」으로만 바꿈).
- 실전사례 섹션 구성: persona 카드 → 상황 설명 → 양동석의 진단(숫자) → 처방(포트폴리오·계좌 배치 표) → 실행 체크리스트 → 한 줄 정리.
