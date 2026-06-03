"""금액 파싱·포맷 유틸. 외부 의존 없는 순수 함수."""
# DART 보고서 코드 → 기간 라벨 접미사 (연간은 접미사 없음)
REPRT_SUFFIX = {"11011": "", "11013": " 1Q", "11012": " 반기", "11014": " 3Q"}


def period_label(bsns_year, offset, reprt_code="11011"):
    """사업연도와 직전 차수(offset)로 기간 라벨 생성. (2024,0,연간)→'2024', (2024,1)→'2023'.

    분기/반기 보고서는 연도 뒤에 분기 표기를 붙인다.
    """
    year = int(bsns_year) - offset
    return f"{year}{REPRT_SUFFIX.get(reprt_code, '')}"


def parse_amount(s):
    """DART 금액 문자열을 int로. 빈값/하이픈은 None."""
    if s is None:
        return None
    s = s.strip().replace(",", "")
    if s in ("", "-"):
        return None
    try:
        return int(s)
    except ValueError:
        return None


def to_eok(amount):
    """원 단위 정수를 억원(소수1) 문자열로. None은 '-'."""
    if amount is None:
        return "-"
    return f"{amount / 1_0000_0000:,.1f}"


def parse_naver_num(s):
    """네이버 지표 문자열을 float로. '29.14배'→29.14, '0.46%'→0.46.

    단위(배·원·%)와 콤마를 떼고 숫자만. 빈값/N/A는 None.
    """
    if s is None:
        return None
    s = s.strip().replace(",", "").rstrip("배원%")
    if s in ("", "N/A", "-"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def parse_market_value(s):
    """'2,107조 5,834억' 같은 시가총액 문자열을 원 단위 int로. 빈값은 None."""
    if s is None:
        return None
    s = s.strip().replace(",", "")
    if s in ("", "N/A", "-"):
        return None
    total, num = 0, ""
    for ch in s:
        if ch.isdigit():
            num += ch
        elif ch == "조":
            total += int(num or 0) * 1_0000_0000_0000
            num = ""
        elif ch == "억":
            total += int(num or 0) * 1_0000_0000
            num = ""
    if num:  # 단위 없는 끝자리는 원
        total += int(num)
    return total or None
