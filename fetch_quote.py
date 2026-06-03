"""네이버 금융에서 한 종목의 시세·밸류에이션을 받아 data/<stock_code>_quote.json 저장.

DART엔 주가가 없어 PER/PBR/시총 등 밸류에이션은 네이버에서 받는다.

usage: python3 fetch_quote.py <stock_code>
예:    python3 fetch_quote.py 005930
"""
import json
import sys
import urllib.request
from pathlib import Path

from format import parse_naver_num, parse_market_value

API = "https://m.stock.naver.com/api/stock/{}/integration"
UA = "Mozilla/5.0"

# 네이버 totalInfos의 code → (저장 키, 파서)
FIELDS = {
    "marketValue": ("market_value", parse_market_value),
    "per": ("per", parse_naver_num),
    "eps": ("eps", parse_naver_num),
    "pbr": ("pbr", parse_naver_num),
    "bps": ("bps", parse_naver_num),
    "dividendYieldRatio": ("dividend_yield", parse_naver_num),
    "dividend": ("dividend", parse_naver_num),
    "highPriceOf52Weeks": ("high_52w", parse_naver_num),
    "lowPriceOf52Weeks": ("low_52w", parse_naver_num),
}


def fetch(stock_code):
    req = urllib.request.Request(API.format(stock_code), headers={"User-Agent": UA})
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def build(stock_code):
    d = fetch(stock_code)
    totals = {t["code"]: t["value"] for t in d.get("totalInfos", [])}
    out = {"stock_code": stock_code, "stock_name": d.get("stockName")}
    out["price"] = parse_naver_num(totals.get("lastClosePrice"))
    for code, (key, parser) in FIELDS.items():
        out[key] = parser(totals.get(code))
    # 현재가는 dealTrendInfos 최신 종가 우선
    deals = d.get("dealTrendInfos") or []
    if deals:
        out["price"] = parse_naver_num(deals[0].get("closePrice")) or out["price"]
        out["bizdate"] = deals[0].get("bizdate")
    return out


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    stock_code = sys.argv[1]
    data = build(stock_code)
    out = Path(__file__).parent / "data" / f"{stock_code}_quote.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"saved {out} (PER {data['per']}, PBR {data['pbr']})")


if __name__ == "__main__":
    main()
