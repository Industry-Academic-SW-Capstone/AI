"""
필터링 로직 단위 테스트 (의존성 없이)
"""
import re


def is_valid_stock_for_analysis(stock_name: str) -> bool:
    """
    스타일 태그 생성이 가능한 종목인지 검증
    
    Returns:
        True: 분석 가능 (정상 종목)
        False: 분석 불가 (SPAC, 우선주, 인버스 등)
    """
    if not stock_name or stock_name == "알 수 없는 종목":
        return False

    # 1. 우선주 필터링
    if "(우)" in stock_name:
        return False
    # "숫자+우" 또는 "숫자+우+영문" 패턴 (예: 1우, 2우B, 3우C)
    if re.search(r"\d+우[A-Z]?$", stock_name):
        return False
    # 종목명 끝이 "우"로 끝나는 경우 (예: SK텔레콤우, LG화학우)
    if stock_name.endswith("우"):
        return False

    # 2. SPAC 필터링
    if "스팩" in stock_name or "SPAC" in stock_name.upper():
        return False

    # 3. 인버스/레버리지 필터링
    if "인버스" in stock_name or "레버리지" in stock_name:
        return False

    return True


def test_normal_stocks():
    """정상 종목 테스트"""
    print("=" * 60)
    print("테스트 1: 정상 종목 (분석 가능)")
    print("=" * 60)
    
    test_cases = [
        "삼성전자",
        "SK하이닉스",
        "NAVER",
        "카카오",
        "현대차",
    ]
    
    for stock_name in test_cases:
        result = is_valid_stock_for_analysis(stock_name)
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} | {stock_name:20s} → {result}")
    
    print()


def test_preferred_stocks():
    """우선주 테스트"""
    print("=" * 60)
    print("테스트 2: 우선주 (분석 불가)")
    print("=" * 60)
    
    test_cases = [
        "삼성화재(우)",
        "현대차2우B",
        "SK텔레콤우",
        "LG화학우",
        "삼성전자1우",
    ]
    
    for stock_name in test_cases:
        result = is_valid_stock_for_analysis(stock_name)
        status = "✅ PASS" if not result else "❌ FAIL"
        expected = "분석 불가" if not result else "분석 가능(?)"
        print(f"{status} | {stock_name:20s} → {expected}")
    
    print()


def test_spac_stocks():
    """SPAC 테스트"""
    print("=" * 60)
    print("테스트 3: SPAC (분석 불가)")
    print("=" * 60)
    
    test_cases = [
        "삼성스팩10호",
        "교보18호스팩",
        "미래에셋SPAC5호",
        "한국SPAC",
    ]
    
    for stock_name in test_cases:
        result = is_valid_stock_for_analysis(stock_name)
        status = "✅ PASS" if not result else "❌ FAIL"
        expected = "분석 불가" if not result else "분석 가능(?)"
        print(f"{status} | {stock_name:20s} → {expected}")
    
    print()


def test_inverse_etf():
    """인버스/레버리지 ETF 테스트"""
    print("=" * 60)
    print("테스트 4: 인버스/레버리지 (분석 불가)")
    print("=" * 60)
    
    test_cases = [
        "KODEX 인버스",
        "TIGER 레버리지",
        "삼성 인버스 2X",
    ]
    
    for stock_name in test_cases:
        result = is_valid_stock_for_analysis(stock_name)
        status = "✅ PASS" if not result else "❌ FAIL"
        expected = "분석 불가" if not result else "분석 가능(?)"
        print(f"{status} | {stock_name:20s} → {expected}")
    
    print()


def test_edge_cases():
    """엣지 케이스 테스트"""
    print("=" * 60)
    print("테스트 5: 엣지 케이스")
    print("=" * 60)
    
    test_cases = [
        ("", False, "빈 문자열"),
        (None, False, "None"),
        ("알 수 없는 종목", False, "알 수 없는 종목"),
        ("우리금융지주", True, "정상 종목 (우리금융지주)"),  # '우'가 앞에 있어도 OK
    ]
    
    for stock_name, expected, description in test_cases:
        try:
            result = is_valid_stock_for_analysis(stock_name)
            status = "✅ PASS" if result == expected else "❌ FAIL"
            print(f"{status} | {description:30s} → {result} (expected: {expected})")
        except Exception as e:
            print(f"❌ ERROR | {description:30s} → {e}")
    
    print()


def main():
    print("\n" + "=" * 60)
    print("SPAC/우선주 필터링 로직 테스트")
    print("=" * 60)
    print()
    
    test_normal_stocks()
    test_preferred_stocks()
    test_spac_stocks()
    test_inverse_etf()
    test_edge_cases()
    
    print("=" * 60)
    print("✅ 테스트 완료!")
    print("=" * 60)


if __name__ == "__main__":
    main()

