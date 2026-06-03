"""DART에서 한 회사의 3대 재무제표를 받아 data/<stock_code>.json 저장.

usage: python3 fetch.py <corp_code> <stock_code> <corp_name> [bsns_year]
예:    python3 fetch.py 00126380 005930 삼성전자 2024
"""
import json
import sys
import urllib.request
from pathlib import Path

from format import parse_amount, period_label

API = "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json"
SJ_NAMES = {"BS": "재무상태표", "IS": "손익계산서", "CF": "현금흐름표"}
REPRT_CODE = "11011"  # 11011=사업(연간), 11013=1Q, 11012=반기, 11014=3Q
KEY = (Path.home() / ".dart_api_key").read_text().strip()


def fetch(corp_code, bsns_year, fs_div):
    url = (
        f"{API}?crtfc_key={KEY}&corp_code={corp_code}"
        f"&bsns_year={bsns_year}&reprt_code={REPRT_CODE}&fs_div={fs_div}"
    )
    with urllib.request.urlopen(url) as r:
        return json.load(r)


def build(corp_code, bsns_year):
    """연결(CFS) 우선, 없으면 개별(OFS). 3대 제표만 추려 반환."""
    for fs_div in ("CFS", "OFS"):
        d = fetch(corp_code, bsns_year, fs_div)
        if d.get("status") == "000":
            break
    else:
        raise SystemExit(f"DART 오류: {d.get('status')} {d.get('message')}")

    items = [i for i in d["list"] if i["sj_div"] in SJ_NAMES]
    if not items:
        raise SystemExit("3대 재무제표 항목 없음")

    periods = {
        "thstrm": period_label(bsns_year, 0, REPRT_CODE),
        "frmtrm": period_label(bsns_year, 1, REPRT_CODE),
        "bfefrmtrm": period_label(bsns_year, 2, REPRT_CODE),
    }
    statements = {k: [] for k in SJ_NAMES}
    for i in sorted(items, key=lambda x: (x["sj_div"], int(x.get("ord") or 0))):
        statements[i["sj_div"]].append({
            "account_id": i.get("account_id"),
            "account_nm": i["account_nm"],
            "thstrm": parse_amount(i.get("thstrm_amount")),
            "frmtrm": parse_amount(i.get("frmtrm_amount")),
            "bfefrmtrm": parse_amount(i.get("bfefrmtrm_amount")),
        })
    return {"fs_div": fs_div, "periods": periods, "statements": statements}


def main():
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    corp_code, stock_code, corp_name = sys.argv[1:4]
    bsns_year = sys.argv[4] if len(sys.argv) > 4 else "2024"

    data = build(corp_code, bsns_year)
    data.update({
        "stock_code": stock_code,
        "corp_name": corp_name,
        "corp_code": corp_code,
        "bsns_year": bsns_year,
    })
    out = Path(__file__).parent / "data" / f"{stock_code}.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    n = sum(len(v) for v in data["statements"].values())
    print(f"saved {out} ({data['fs_div']}, {n} accounts)")


if __name__ == "__main__":
    main()
