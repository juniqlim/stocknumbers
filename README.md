# stocknumbers — 한국주식 펀더멘털

종목별 정적 JSON을 브라우저(`index.html`)가 직접 fetch해 표·차트로 보여주는 정적 사이트. 백엔드 없음.

열기: `python3 -m http.server` 후 `index.html?code=<종목코드>` (기본 005930). 헤더의 셀렉트박스로 종목 전환.

## 종목 목록 매니페스트 (`data/companies.json`)

셀렉트박스에 뜨는 종목 목록. **새 회사 추가 시 여기에 한 줄 등록**해야 드롭다운에 나온다.

```json
[ { "code": "018290", "name": "브이티" }, { "code": "003350", "name": "한국화장품제조" } ]
```

## 종목당 파일 (`data/<code>*.json`)

| 파일 | 내용 | 생성 |
|------|------|------|
| `<code>.json` | DART 3대 재무제표(당기·전기·전전기) | `python3 fetch.py <corp_code> <code> <회사명> [연도]` |
| `<code>_quote.json` | 네이버 시세·밸류에이션(PER/PBR/시총…) | `python3 fetch_quote.py <code>` |
| `<code>_annual.json` | 연간 실적 표(큐레이션) | 수기 작성 (아래 스키마) |
| `<code>_quarter.json` | 분기 실적 표 | 수기 작성 |
| `<code>_balance.json` | 재무상태표(다년) | 수기 작성 |
| `<code>_extra.json` | 종목별 추가 year-row 표(선택). 페이지 **말미**에 렌더 | 수기 작성 |

`<code>.json`·`_quote.json`만 있으면 페이지는 뜬다. 나머지는 있으면 해당 섹션이 추가되고, 없으면 자동 생략된다(`index.html`이 404를 null로 처리). `_extra`는 year-row 공용 스키마를 그대로 쓰는 범용 슬롯으로, 종목 특화 표(예: 005930 우선주 괴리율)를 맨 아래 붙일 때 쓴다.

## year-row 공용 스키마 (`_annual` / `_quarter` / `_balance`)

세 파일 모두 **같은 포맷**. 첫 열이 기간(연도 또는 분기), 나머지가 지표. `index.html`의 `yearTable()`이 공통 렌더.

```json
{
  "stock_code": "003350",
  "title": "연간 실적",
  "unit": "단위: 억원 ... 출처/주석 (표 아래 회색 캡션, 각주도 여기에)",
  "headers": ["연도", "매출", "매출YoY", "GPM", "영업이익", "..."],
  "rows": [
    ["2024", "1,675", "+53.2%", "23.9%", "265", "..."],
    ["2025", "1,846", "+10.2%", "26.5%", "329", "..."]
  ],
  "highlight": ["2024", "2025"]
}
```

규칙:
- `rows`의 각 항목은 **문자열 배열**(헤더 순서와 일치). 콤마·`%`·`+`·`적자`·`흑전` 등 표시값을 그대로 넣는다.
- 셀 색: 음수(`-12`, `적자`, `~-2.8%`)는 빨강, 증가(`+53.2%`, `흑전`)는 초록 — `annualClass()`가 문자열로 판별.
- `highlight`: 강조(노랑 배경)할 첫 열 값 목록.
- `"-"`/빈칸 = 데이터 없음(중립).
- 열 배치 관례: 파생지표는 기준지표 오른쪽에 붙인다 — `매출→매출YoY→매출QoQ`, `매출총이익→GPM`, `영업이익→영익YoY→영익QoQ→OPM`, `배당률→PER(연말)→FCF수익률`. **시총(연말)은 맨 끝**에 둔다(밸류에이션 규모 지표). `FCF수익률 = 연간 FCF ÷ 시총(연말)`(비율 자체가 %라 `money_cols` 아님, 차트선 자동); FCF 컬럼 없는 종목(예 2209)은 생략. 음수면 빨강.
- **분기표(`_quarter`) 표준 컬럼**: `분기·매출·매출YoY·매출QoQ·매출총이익·GPM·영업이익·영익YoY·영익QoQ·OPM·순이익·영업CF·FCF·CAPEX`. QoQ=직전 분기(반기표는 직전 반기) 대비. CAPEX는 **양수**(abs), `FCF=영업CF−CAPEX`. 부호·적자전환은 `흑전`/`적자` 마커.

선택 필드(통화):
- `currency`: `"KRW"`(기본, 생략 가능) 또는 `"USD"`. 외국주식(미국·홍콩 등)은 `"USD"`.
- `value_unit`: 표 캡션·차트축에 쓰는 native 단위 라벨 — `"억원"`(KRW) / `"십억$"`(대형 미국주식) / `"백만$"`(~$10억 미만 외국주식). 통화 전환 환산은 이 라벨로 native 스케일을 판별하므로 정확히 적는다.
- `money_cols`: 금액 컬럼(헤더명 배열). 통화 전환 대상. 생략 시 `index.html`이 추론(순수 숫자 컬럼, `PER` 류 배수는 제외) — 한국주식은 추론으로 충분, 달러주식은 명시 권장.

### 통화 전환 ($/₩)
헤더의 통화 셀렉트박스로 표·차트 금액을 환산. 종목 native 통화로 시작.
- **한국주식(KRW): 토글 셀렉터 자체를 숨긴다**(달러 표시 불필요). 항상 ₩(억원).
- **외국주식(USD)만 ₩/$ 토글 노출**. ₩ 표시 단위는 native 스케일 따라감: `십억$`→**조원**, `백만$`→**억원**.
- 표 위 캡션의 `단위: …` 토큰도 표시통화에 맞춰 동적 교체(`백만$(USD)`↔`억원`). "반기 기준" 등 단서는 보존.
- %·YoY·QoQ·PER 등 비금액 열은 그대로. 환율은 `index.html`의 `FX`(현재 1,380원/$ 고정).

### 추이 차트
`_annual.json`이 있으면 막대(금액, 좌축)+선(%·배수, 우축) 혼합 차트가 자동 생성된다(Chart.js, 범례 클릭 토글). 좌축 단위는 표시 통화 따라감. 막대로 그릴 금액 계열은 `index.html`의 `CHART_EOK`, 처음 켜둘 지표는 `CHART_DEFAULT`로 조정. **좌축 금액인데 선으로 그릴 계열은 `CHART_LINE_EOK`**(예: `시총` — 막대들과 같은 좌축이지만 추이를 선으로). 시총 컬럼이 있는 종목에서만 자동 표시되고, 없는 종목엔 무영향.

## 데이터 산출 방법론 (검증된 절차)

- **분기 손익·현금흐름**: DART는 분기를 누적공시 → **분기값 = 당분기누적 − 직전분기누적**, Q4 = 연간 − 3Q누적.
  - reprt_code: 1Q=11013, 반기=11012, 3Q=11014, 사업(연간)=11011.
  - 손익(IS)은 `thstrm_add_amount`(누적), 연간은 `thstrm_amount`. CF는 항상 누적이라 `thstrm_amount`.
  - 계정은 `account_id` 우선, 비면 `account_nm`로 폴백(분기보고서는 id가 비기도 함).
  - CAPEX = 유형자산의 취득(무형 제외), FCF = 영업CF − CAPEX.
  - **검증 습관**: 분기 합이 연간값과 맞는지 대조한 뒤 채택.
- **배당률(연도별)**: DART 배당공시 API `alotMatter.json`의 `현금배당수익률(%)`(보통주, 시가배당율). 한 호출이 thstrm/frmtrm/bfefrmtrm 3개년을 주므로 연도별 dict로 모아 보강(특정 연도가 빈 호출은 인접 연도 호출의 frmtrm/bfefrmtrm로 폴백). 무배당·미공시 연도는 `0.00%` 또는 `-`. 주의: quote의 배당수익률은 현재가 기준이라 시가배당율과 다름.
- **재무상태표(다년)**: DART 사업보고서 XML 파싱(한 보고서가 당기·전기·전전기 3개년 제공). 인코딩이 연도별로 다름(구버전 EUC-KR, 신버전 UTF-8) → 자동감지. 단위 백만원 → 억원(÷100). DOCUMENT-NAME이 "사업보고서"인 본문 선택(감사보고서 첨부 제외).
- **교차검증**: 파싱값을 노트/공시 지표(예: ROE = 순이익÷자본)와 대조해 확인.
- **손익 = 포괄손익(CIS)**: 다수 회사가 손익을 `sj_div="CIS"`로 공시 → `fetch.py`의 IS가 빈다(정상). 연간 표는 API(`fnlttSinglAcntAll`, CFS)에서 CIS 계정 직접 수집. 핵심 `account_id`: 매출 `ifrs-full_Revenue`, 매출총이익 `ifrs-full_GrossProfit`, 영업이익 `dart_OperatingIncomeLoss`, 순이익(지배) `ifrs-full_ProfitLossAttributableToOwnersOfParent`(폴백 `ifrs-full_ProfitLoss`).
- **2016 이전 함정**: 구버전 XBRL은 매출·순익이 미태깅(영업이익·CAPEX만 옴) → 한국주식 연간표는 보통 **2017부터** 시작. 한 번 호출이 3개년 제공하므로 2019·2022·2025 호출로 2017~2025 커버.
- **CAPEX 부호**: 보고서별로 `유형자산의 취득`이 음수로 오기도 함 → 항상 `abs()` 후 사용.
- **PER(연말)**: 연말종가 ÷ 주당순이익(EPS, 지배 기본 `ifrs-full_BasicEarningsLossPerShare`). 종가는 네이버 일별시세(`api.finance.naver.com/siseJson.naver`, 수정주가). 적자(EPS≤0) 연도는 `적자`.
- **시총(연말)**: KRX/네이버가 과거 일별 시총을 무인증 API로 안 주므로(KRX는 세션/OTP, pykrx는 계정 필요) **연말종가 × 발행주식수**로 계산. 발행주식수는 DART `stockTotqySttus.json`(보통주 `istc_totqy`), 종가는 네이버 수정주가.
  - **분할/액면분할 보정**: 수정종가는 분할 반영, 발행주식수는 보고시점값 → 불일치 주의. 예 삼성(2018 50:1)은 분할후 보통주수(5,969,782,550, 2025 소각 후 5,919,637,922)로 통일.
  - **검증 습관**: `EPS×주식수 ≈ 지배순이익`(우선주 있으면 보통주만이라 어긋남은 정상), 또는 `시총÷순이익 ≈ PER(연말)`로 정합 확인. 분할·증자 종목은 이 대조로 걸러낸다.

### 미국주식 (SEC EDGAR)
DART가 없는 미국주식은 SEC EDGAR `companyconcept` API(`data.sec.gov/api/xbrl/companyconcept/CIK{10자리}/us-gaap/{태그}.json`, User-Agent 헤더 필수)로 받는다.
- 연도별 값: 사실(fact)의 `frame` 필드 사용 — flow는 `CY2024`, instant(재무상태표)는 `CY2024Q4I`.
- 분기: 손익은 3개월 fact 직접(start/end가 해당 분기), Q4 = 연간 − (Q1+Q2+Q3). 현금흐름은 YTD라 직전 분기 차분.
- 태그 예: `Revenues`, `CostOfRevenue`(GP=매출−원가), `OperatingIncomeLoss`, `NetIncomeLoss`, `Assets`, `Liabilities`, `StockholdersEquity`, `NetCashProvidedByUsedInOperatingActivities`, `PaymentsToAcquirePropertyPlantAndEquipment`.
- `currency:"USD"`, `value_unit:"십억$"`(대형) 또는 `"백만$"`(~$10억 미만), `money_cols` 명시. DART `<code>.json`은 없어도 됨(제목은 companies.json에서).
- **시총(EDGAR)**: 회계기간말 종가(야후 `query1.finance.yahoo.com/v8/finance/chart/{ticker}`) × 발행주식수(`us-gaap:CommonStockSharesOutstanding` instant 또는 `dei:EntityCommonStockSharesOutstanding`). **분할 함정**: EDGAR가 같은 날짜를 보고서마다 분할전/후로 다르게 재표시(예 NFLX 2025 10:1, AAPL 2020 4:1) → 종가·주식수·EPS를 모두 **분할후 기준으로 통일**한 뒤 계산. `시총÷순이익 ≈ PER(연말)`로 검증. `money_cols`에 `시총` 추가(통화 전환 대상).

### 홍콩주식 (HKEX)
DART·EDGAR가 없으면 HKEX 연차/반기 보고서 PDF를 받아 파싱(회사 IR 사이트 `e_<code>_annualreport<YYYY>.pdf` 또는 hkexnews.hk, `pdftotext -layout`). 반기 공시(분기 없음)라 `_quarter`는 반기표로 작성(첫 열 `1H2024`…, `2H=연간−1H`). 표시통화가 USD인 경우가 많음(예: YesAsia는 기능·표시통화가 US$, 주식·배당은 HKD). `value_unit:"백만$"` 권장. 시총·PER·배당은 야후(`<code>.HK`) 연말종가(HKD)와 보고서값(EPS·발행주식수·주당배당)으로 산출: PER=종가÷EPS, 시총=종가×주식수÷7.8(HKD→USD 페그), 배당률=주당배당(HKcents)÷종가. (`pdftotext`가 표를 깨면 본문 서술·현금흐름표 라인에서 값 회수.)

### 대만주식 (SEC 20-F, IFRS)
TSMC 등 대만 ADR은 SEC에 **20-F(연간)를 IFRS 택소노미로** 제출 → `companyconcept` API의 `ifrs-full` 네임스페이스 사용(`.../CIK{10자리}/ifrs-full/{태그}.json`).
- **분기 없음**: 20-F는 연간만, 6-K 중간보고는 비구조화(분기 fact 0개) → `_quarter` 생략.
- 통화: 보고통화는 TWD지만 20-F가 **USD 환산치(감사)**를 2017~ 제공 → USD 그대로 사용(별도 환율 변환 불필요). `currency:"USD"`, `value_unit:"십억$"`. (2015~2016은 USD 미제공 → 2017부터.)
- 연도 매칭: `frame`이 비는 경우가 많아 **기간 종료일**로 연도 판별(flow는 ~365일, instant는 연말).
- 태그(ifrs-full): `Revenue`, `GrossProfit`, `ProfitLossFromOperatingActivities`, `ProfitLossAttributableToOwnersOfParent`, `Assets`, `Liabilities`, `Equity`, `CashFlowsFromUsedInOperatingActivities`, `PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities`, EPS `BasicEarningsLossPerShare`.
- PER(연말)·배당률: 본주(TWSE `2330.TW`) 연말종가·EPS(TWD)로 계산(배수·비율은 통화무관). 주당배당은 총배당(`DividendsPaidClassifiedAsFinancingActivities`)÷발행주식(2019년 분기배당 전환 후 per-share 태그가 끊겨 총액 기준으로 산출).
- **시총(USD)**: ADR(`TSM`) 1:5 비율로 환율 없이 전체 시총 = ADR 연말종가($) × (총발행주식수 ÷ 5). 차익거래로 본주 전체 시총과 일치(ADR 프리미엄은 포함).

## 레퍼런스 예시
- **003350 (한국화장품제조)** — 한국주식(KRW) 표준 예시. 5개 파일 전부 + 사업보고서 XML 파싱.
- **003230 (삼양식품) / 214450 (파마리서치)** — KRW, DART API(`fnlttSinglAcntAll`, CIS)로 연간 2017~ 직접 수집. 분기는 누적 차분.
- **000660 (SK하이닉스)** — KRW 대형 반도체(삼성전자형). 연간·분기·재무상태표 전부 + 시총. 메모리 사이클(2023 적자→2025 사상최대) 예시.
- **NFLX (넷플릭스)** — 미국주식(USD, `십억$`). EDGAR API 기반, `_quote`/DART `<code>.json` 없이 동작.
- **SNDK (샌디스크)** — 미국주식(USD, `십억$`). EDGAR API 기반, 연간(FY2023~2025)·분기(FY25Q1~FY26Q3)·재무상태표(FY2024~2025). 2025-02 웨스턴디지털에서 NAND 사업 분사 상장 → **FY2023~2024는 분사 전 carve-out 재무**(자산총계는 FY2023 미제공). **회계연도 6월 말 종료**(em∈{6,7}로 FY 판별, FY26Q3=2026-04-03). 매출 `RevenueFromContract...`, CAPEX `PaymentsToAcquirePropertyPlantAndEquipment`. 3개년 순손실→PER '적자', 무배당. 시총은 상장 후 FY2025말만(2025-06-27 종가×146M주), FY23·24는 '-'. NAND 사이클 종목: FY23~24 GPM 급락·영업적자, **FY25Q3 영업권 손상 약 18억$**, **FY26 AI 메모리 슈퍼사이클로 매출·GPM 급등**(FY26Q3 매출 +251%·GPM 78%, 주가 $47→$600+).
- **NVDA (엔비디아)** — 미국주식(USD, `십억$`). EDGAR API 기반, 연간·분기·재무상태표 전부 + 시총. 매출 `Revenues`(FY2019만 `RevenueFromContract...`), CAPEX `PaymentsToAcquireProductiveAssets`(FY2022~; FY2019~2021은 옛 태그가 companyfacts에서 잘려 10-K 현금흐름표 직접 파싱). **함정 ①회계연도 1월 말 종료**: 연/분기 모두 종료일 월(em∈{1,2})로 FY 판별, FY2026=2026-01-25 종료. **②분할 2회**(2021-07 4:1, 2024-06 10:1): 발행주식수를 크기로 감지해 post-10:1로 통일(0.6B→×40, 2.5B→×10), 종가는 야후 `close`(분할반영). 시총·PER은 회계연도말 종가 기준. 배당은 토큰수준이라 배당률=총배당(`PaymentsOfDividends`)÷시총. FY2023 재고조정 후 FY2024~ AI가속기 폭증(매출 27→216십억$).
- **RDDT (레딧)** — 미국주식이나 규모가 작아 `백만$` 사용(대형 미국주식 중 유일). EDGAR API 기반, 연간·분기·재무상태표 전부 + 시총. 매출 태그는 `RevenueFromContractWithCustomerExcludingAssessedTax`, 원가 `CostOfGoodsAndServicesSold`(GP=매출−원가). 2024-03 IPO라 시총·PER은 2024~, 분기는 3개월 fact 직접 제공(Q4=연간−3Q). 함정: ①발행주식수가 Class A/B 커스텀 태그라 companyfacts에 없음 → 10-K 대차대조표 "X and Y shares issued and outstanding" 파싱해 A+B 합산. ②2022·2023 자본총계 음수(전환우선주=임시자본/메자닌)라 ROE·부채비율 '-'; IPO 시 우선주가 보통주로 전환되며 정상화. ③2024 순손실·Q1'24은 IPO 관련 주식보상 대량 인식분($약 595M) 포함. ④흑자전환 초기라 영익 YoY/QoQ %가 저기저효과로 크게 튐.
- **2209 (예스아시아홀딩스)** — 홍콩주식(USD, `백만$`, 반기 공시). HKEX PDF 파싱.
- **TSM (TSMC)** — 대만 ADR(USD, `십억$`). SEC 20-F(IFRS) API 기반, 연간·재무상태표만(분기 XBRL 없음). PER(연말)·배당률은 본주 2330 기준.
- **GOOGL (알파벳/구글)** — 미국주식(USD, `십억$`). EDGAR API 기반, 연간·분기·재무상태표 전부 + 시총. 2022년 20:1 분할로 종가·EPS·주식수 분할후 통일, 2024 배당 개시.
- **035600 (KG이니시스)** — KRW 전자결제(PG). DART API(`fnlttSinglAcntAll`, CFS) 연간 2017~ + 분기 누적차분 + 재무상태표. PG 특성: 매출은 결제대행 인식이라 GPM·OPM 낮고, 부채에 가맹점 정산 예수금이 커서 부채비율 구조적으로 높음, 영업CF는 정산예수금 변동으로 분기 변동성 큼(Q4 유입). 2020 일부 매출 순액인식 전환, 2024 3Q 일회성 영업적자.
- **KO (코카콜라)** — 미국주식(USD, `십억$`). EDGAR API 기반, 연간·분기·재무상태표 전부 + 시총. 무분할(정합). 매출은 2015 `SalesRevenueGoodsNet`+2016~ `Revenues` 병합, 주 단위 회계로 분기말일 변동 → 회계분기 순번으로 YoY/QoQ 매칭.
- **307950 (현대오토에버)** — KRW 현대차그룹 IT서비스(SI·차량SW·ERP). DART API(`fnlttSinglAcntAll`, CFS) 연간 2019~2025 + 분기 누적차분 + 재무상태표 + 시총. 손익=CIS, 지배순익 `ifrs-full_ProfitLossAttributableToOwnersOfParent`. **함정: `ifrs-full_Equity`(자본총계)가 자본변동표(SCE)에도 다수 중복 → 반드시 `sj_div=="BS"`로 한정**(자산=부채+자본 검증). 2019·2020 발행주식 21,000,000주 → 2021-04 현대엠엔소프트·현대오트론 흡수합병 신주로 27,423,982주(매출·자본 급증, 시총 계산 시 연도별 주식수 분기). 2019 시가배당율 미공시라 주당710원÷연말종가로 근사.
- **260970 (에스앤디)** — KRW 식품 소재(분말·소스 원료), **삼양식품 불닭 시리즈 핵심 파트너사**(매출 80%+ 삼양향). DART API(`fnlttSinglAcntAll`, **OFS**=별도; 연결 미공시) 연간 2019~2025 + 분기 + 재무상태표. 2017·2018은 DART 미제공(2018-11 상장). 주의: 분기 손익은 보고서 3개월값 직접 사용(누적 아님), 영업CF·CAPEX만 누적차분. 2021 액면분할(5,000→500원, 10:1)로 EPS·주가·주식수 단절, 2024 자기주식 대량 소각(4,059,420→2,892,754주)으로 자본 감소·ROE 상승. 시총=연말종가(네이버)×발행주식수(`stockTotqySttus`).

새 회사 추가 시: ① `_annual`/`_balance`(+가능하면 `_quarter`) 작성 → ② `data/companies.json`에 등록 → ③ 새 데이터 소스/통화 유형이면 위 방법론·예시에 한 줄 추가 → ④ 다운로드한 원본 문서가 있으면 note 저장소에 보관(아래).

## 원자료 보관 (note 저장소)
보고서 원본(DART XML, HKEX/EDGAR PDF 등)은 **stocknumbers와 별개인 `note` git 저장소**(`/Users/juniq/develop/code/juniqlim/note`, 브랜치 `master`)에 보관하고 따로 커밋·푸시한다. 경로 관례: `investment/<카테고리>/<회사>/reports/<period>/` (예: `investment/KBeautyDistribution/silicon2/reports/annual_2025/`). period 슬러그: `annual_YYYY` / `half_YYYY` / `q1_YYYY` / `q3_YYYY`. 정정본이 있으면 정정본 우선. stocknumbers repo엔 원자료를 넣지 않는다.
