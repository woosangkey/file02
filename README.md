# 금융 교육 자료 PDF 시리즈 (10편)

| No | 파일 | 주제 |
|---|---|---|
| 01 | pdf/01_macro_outlook.pdf | 2027 글로벌 거시경제 전망 시나리오 |
| 02 | pdf/02_asset_allocation.pdf | 생애주기별 자산배분·포트폴리오 |
| 03 | pdf/03_bond_basics.pdf | 채권: 수익률곡선·듀레이션·신용위험 |
| 04 | pdf/04_financial_statements.pdf | 재무제표 분석 실무 (가상기업 사례) |
| 05 | pdf/05_dcf_valuation.pdf | DCF 기업가치평가 실전 |
| 06 | pdf/06_retirement.pdf | 은퇴설계와 3층 연금 전략 |
| 07 | pdf/07_derivatives.pdf | 파생상품: 선물·옵션·스왑과 헤지 |
| 08 | pdf/08_digital_assets.pdf | 디지털자산: 스테이블코인·STO·CBDC |
| 09 | pdf/09_real_estate_finance.pdf | 부동산 금융: 주담대·PF·리츠 |
| 10 | pdf/10_risk_management.pdf | 리스크관리: VaR·스트레스테스트·바젤III |

본문 원고는 `content/*.json`, 재생성은 `python3 scripts/build.py` (reportlab, matplotlib, 나눔고딕 필요).
교육·참고용 자료이며 '예시/가상'으로 표기된 수치는 실제 데이터가 아닙니다.

## 채권투자 실무 가이드 (단행본, 112쪽)

`book/채권투자_실무가이드.pdf` — 중급(1부) · 상급(2부) · 하이엔드 판매자(3부) 12장 + 부록(공식집·용어사전·종합문제).
원고는 `book/chapters/*.json`, 재생성은 `python3 scripts/build_book.py`.

## 채권투자 365일 학습 과정 (제안)

- `study/채권투자_365일_학습과정_제안서.pdf` — 과정 설계, 연간 로드맵, 평가 체계, 제작 방안, 365일 일차별 커리큘럼
- `study/pdf/Day001.pdf`, `Day006.pdf` — 샘플 교재 (학습일 / 실전 드릴, 각 10쪽)
- 원고: `study/syllabus/m01~m12.json`, `study/days/dayNNN.json` · 재생성: `python3 scripts/build_study.py`

## 채권투자 30일 집중 과정 (전체 교재, 2026년 10월 시장 반영)

- `study30/채권투자_30일_집중과정_전체교재.pdf` — 30일 전체 합본 (345쪽, 주차·일차 책갈피)
- `study30/채권투자_30일과정_N주차_교재.pdf` — 주차별 합본 (표지 + 2026년 10월 채권시장 브리핑 + 일일 교재)
- `study/채권투자_30일_집중과정_커리큘럼.pdf` — 커리큘럼
- 원고: `study30/days/day01~30.json`, 시장 기준값: `study30/MARKET_2026-10.md` · 재생성: `python3 scripts/build_study.py --all30`

## 양동석의 월배당 설계 (단행본, 249쪽)

- `divbook/양동석의_월배당설계.pdf` — 준비마당(원칙 8) + 실전마당 1~5, 크라운판(176×248mm)
- 원고: `divbook/units/*.json`, 집필 기준서: `divbook/BRIEF.md`, 출간 전 확인 목록: `divbook/출간전_확인목록.md`
- 재생성: `python3 scripts/build_divbook.py`
