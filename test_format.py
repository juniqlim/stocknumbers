import format as f


def test_parse_amount():
    assert f.parse_amount("300870903000000") == 300870903000000
    assert f.parse_amount("1,234") == 1234
    assert f.parse_amount("-1625229000000") == -1625229000000
    assert f.parse_amount("") is None
    assert f.parse_amount("-") is None
    assert f.parse_amount(None) is None


def test_to_eok():
    assert f.to_eok(300870903000000) == "3,008,709.0"
    assert f.to_eok(-1625229000000) == "-16,252.3"
    assert f.to_eok(None) == "-"


def test_parse_naver_num():
    assert f.parse_naver_num("29.14배") == 29.14
    assert f.parse_naver_num("12,372원") == 12372.0
    assert f.parse_naver_num("0.46%") == 0.46
    assert f.parse_naver_num("-1,668") == -1668.0
    assert f.parse_naver_num("N/A") is None
    assert f.parse_naver_num("") is None
    assert f.parse_naver_num(None) is None


def test_parse_market_value():
    assert f.parse_market_value("2,107조 5,834억") == 2107583400000000
    assert f.parse_market_value("5,834억") == 583400000000
    assert f.parse_market_value("3조") == 3000000000000
    assert f.parse_market_value("") is None
    assert f.parse_market_value(None) is None


def test_period_label():
    # 연간(11011): 사업연도와 직전 차수(offset)로 연도 계산
    assert f.period_label("2024", 0, "11011") == "2024"
    assert f.period_label("2024", 1, "11011") == "2023"
    assert f.period_label("2024", 2) == "2022"
    assert f.period_label(2024, 0) == "2024"
    # 분기/반기: 연도 + 분기 표기
    assert f.period_label("2024", 0, "11013") == "2024 1Q"
    assert f.period_label("2024", 0, "11012") == "2024 반기"
    assert f.period_label("2024", 0, "11014") == "2024 3Q"


if __name__ == "__main__":
    test_parse_amount()
    test_to_eok()
    test_parse_naver_num()
    test_parse_market_value()
    test_period_label()
    print("ok")
