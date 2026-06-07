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

`<code>.json`·`_quote.json`만 있으면 페이지는 뜬다. 나머지 3개는 있으면 해당 섹션이 추가되고, 없으면 자동 생략된다(`index.html`이 404를 null로 처리).

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
- 열 배치 관례: 파생지표는 기준지표 오른쪽에 붙인다 — `매출→매출YoY→매출QoQ`, `매출총이익→GPM`, `영업이익→영익YoY→영익QoQ→OPM`, `배당률→PER(연말)`.
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
`_annual.json`이 있으면 막대(금액, 좌축)+선(%·배수, 우축) 혼합 차트가 자동 생성된다(Chart.js, 범례 클릭 토글). 좌축 단위는 표시 통화 따라감. 막대로 그릴 금액 계열은 `index.html`의 `CHART_EOK`, 처음 켜둘 지표는 `CHART_DEFAULT`로 조정.

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

### 미국주식 (SEC EDGAR)
DART가 없는 미국주식은 SEC EDGAR `companyconcept` API(`data.sec.gov/api/xbrl/companyconcept/CIK{10자리}/us-gaap/{태그}.json`, User-Agent 헤더 필수)로 받는다.
- 연도별 값: 사실(fact)의 `frame` 필드 사용 — flow는 `CY2024`, instant(재무상태표)는 `CY2024Q4I`.
- 분기: 손익은 3개월 fact 직접(start/end가 해당 분기), Q4 = 연간 − (Q1+Q2+Q3). 현금흐름은 YTD라 직전 분기 차분.
- 태그 예: `Revenues`, `CostOfRevenue`(GP=매출−원가), `OperatingIncomeLoss`, `NetIncomeLoss`, `Assets`, `Liabilities`, `StockholdersEquity`, `NetCashProvidedByUsedInOperatingActivities`, `PaymentsToAcquirePropertyPlantAndEquipment`.
- `currency:"USD"`, `value_unit:"십억$"`(대형) 또는 `"백만$"`(~$10억 미만), `money_cols` 명시. DART `<code>.json`은 없어도 됨(제목은 companies.json에서).

### 홍콩주식 (HKEX)
DART·EDGAR가 없으면 HKEX 연차/반기 보고서 PDF를 받아 파싱(회사 IR 사이트 `e_<code>_annualreport<YYYY>.pdf` 또는 hkexnews.hk, `pdftotext -layout`). 반기 공시(분기 없음)라 `_quarter`는 반기표로 작성(첫 열 `1H2024`…, `2H=연간−1H`). 표시통화가 USD인 경우가 많음(예: YesAsia는 기능·표시통화가 US$, 주식·배당은 HKD). `value_unit:"백만$"` 권장.

## 레퍼런스 예시
- **003350 (한국화장품제조)** — 한국주식(KRW) 표준 예시. 5개 파일 전부 + 사업보고서 XML 파싱.
- **003230 (삼양식품) / 214450 (파마리서치)** — KRW, DART API(`fnlttSinglAcntAll`, CIS)로 연간 2017~ 직접 수집. 분기는 누적 차분.
- **NFLX (넷플릭스)** — 미국주식(USD, `십억$`). EDGAR API 기반, `_quote`/DART `<code>.json` 없이 동작.
- **2209 (예스아시아홀딩스)** — 홍콩주식(USD, `백만$`, 반기 공시). HKEX PDF 파싱.

새 회사 추가 시 같은 구조를 복제하고 `data/companies.json`에 등록한다.

## 원자료 보관 (note 저장소)
보고서 원본(DART XML, HKEX/EDGAR PDF 등)은 **stocknumbers와 별개인 `note` git 저장소**(`/Users/juniq/develop/code/juniqlim/note`, 브랜치 `master`)에 보관하고 따로 커밋·푸시한다. 경로 관례: `investment/<카테고리>/<회사>/reports/<period>/` (예: `investment/KBeautyDistribution/silicon2/reports/annual_2025/`). period 슬러그: `annual_YYYY` / `half_YYYY` / `q1_YYYY` / `q3_YYYY`. 정정본이 있으면 정정본 우선. stocknumbers repo엔 원자료를 넣지 않는다.
