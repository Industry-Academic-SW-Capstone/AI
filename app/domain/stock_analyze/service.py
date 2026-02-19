import pandas as pd
import numpy as np
import joblib
import json
import hashlib
import os
import redis
import re
from pathlib import Path
from numpy.linalg import norm
from .dto import StockAnalyzeRequest, StockAnalyzeResponse
from app.ai_models.scoring import (
    growth_score, stability_score, composite_score, DEFAULT_WEIGHTS,
    score_all_stocks, compute_user_feature_vector,
)
from .recommend_dto import RecommendRequest


# 모델, 스케일러, DB 로드 (절대 경로 사용)
BASE_DIR = Path(__file__).resolve().parents[2]  # /app
MODEL_DIR = BASE_DIR / "ai_models"
DATA_DIR = BASE_DIR / "data"

model = joblib.load(str(MODEL_DIR / "kmeans_model.pkl"))
scaler = joblib.load(str(MODEL_DIR / "scaler.pkl"))
# stockit_ai_features_v1.csv 사용 (3621개 종목)
stock_db = pd.read_csv(
    str(DATA_DIR / "stockit_ai_features_v1.csv"), dtype={"단축코드": str}
).set_index("단축코드")


tag_mapping = {
    0: "[안정형 일반주]",
    1: "[고효율 우량주]",
    2: "[초고배당 가치주]",
    3: "[고위험 저평가주]",
    4: "[고성장 기대주]",
    5: "[초대형 우량주]",
    6: "[초저평가 가치주]",
    7: "[고가치 성장주]",
}

# [수정됨] '주린이 해설' 버전의 상세한 description_mapping
description_mapping = {
    0: "안정적인 보통 주식: 회사가 빚(부채)이 적어서 일단 망할 위험이 낮아요. 하지만 돈을 벌어들이는 효율(ROE)이 평범해서, 주가가 폭발적으로 오르지도 않을 거예요.",
    1: "숨겨진 보물 우량주: PER이 낮아서 (버는 돈 대비 주가가 저렴해서) 저평가되어 있어요. 게다가 ROE가 높아서 (자기 돈으로 장사를 매우 잘해서) 효율성이 뛰어난 믿음직한 기업이에요.",
    2: "미친 듯이 배당 주는 주식: 다른 주식들보다 배당수익률이 압도적으로 높아요. (주식을 은행 이자처럼 사는 개념) PER이 낮아 (저렴해서) 현재의 가치도 괜찮은 그룹이에요.",
    3: "대박 아니면 쪽박 주식: PBR이 매우 낮아 (회사가 가진 재산보다 주가가 훨씬 싸요). But! 부채비율이 너무 높아 (빚이 많아) 잘못되면 크게 위험해질 수 있어요.",
    4: "미래를 꿈꾸는 성장주: PER이 엄청나게 높아요. (회사가 버는 돈에 비해 주가가 매우 비싸요). 이는 사람들이 이 회사가 '앞으로 엄청난 대박을 칠 것'이라고 기대하기 때문이에요.",
    5: "대한민국 대표 우량주: 시가총액이 가장 커요. (회사의 덩치가 가장 커요). 워낙 크기 때문에 크게 오르기는 어렵지만, 시장을 대표하는 안정적인 그룹이에요.",
    6: "워렌 버핏이 좋아하는 주식: PER과 PBR이 가장 낮고 (가장 저렴함) 부채비율도 가장 낮아 (가장 안전함) '싸고 안전한 종목'을 찾는 정석적인 가치투자자들이 선호하는 그룹이에요.",
    7: "프리미엄 붙은 최고급 주식: PBR이 높아 (이미 비싸지만) ROE도 높아 (실제로 돈도 잘 벌고 효율도 좋음). 시장에서 '비싼 값을 지불할 가치'가 있다고 인정받는 성장 기업 그룹이에요.",
}


# Redis 클라이언트 초기화
def get_redis_client():
    """Redis 클라이언트 반환"""
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    return redis.Redis(
        host=redis_host,
        port=redis_port,
        decode_responses=True,
        socket_connect_timeout=2,
    )


def generate_cache_key(request: StockAnalyzeRequest) -> str:
    """요청 데이터로 캐시 키 생성 (재무 지표 변경 시 다른 캐시)"""
    # 단축코드와 재무 지표들을 조합하여 고유한 해시 생성
    data_str = f"{request.stock_code}:{request.market_cap}:{request.per}:{request.pbr}:{request.roe}:{request.debt_ratio}:{request.dividend_yield}"
    hash_key = hashlib.md5(data_str.encode()).hexdigest()
    return f"stock_analyze:{hash_key}"


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

    # 4. 홀딩스/지주 필터링 (선택적 - 필요시 주석 해제)
    # if "홀딩스" in stock_name or "홀딩" in stock_name or "지주" in stock_name:
    #     return False

    return True


def get_unanalyzable_reason(stock_name: str, in_db: bool = True) -> str:
    """분석 불가 사유 생성"""
    if not in_db:
        return "이 종목은 AI 학습 데이터에 포함되지 않아 투자 스타일 분석이 불가능합니다. 포트폴리오 분석을 위해 다른 종목을 선택해주세요."

    if "(우)" in stock_name or re.search(r"\d+우[A-Z]?$", stock_name):
        return "이 종목은 우선주로 분류되어 투자 스타일 분석이 불가능합니다. 포트폴리오 분석을 위해 보통주를 선택해주세요."
    elif "스팩" in stock_name or "SPAC" in stock_name.upper():
        return "이 종목은 SPAC(기업인수목적회사)으로 투자 스타일 분석이 불가능합니다."
    elif "인버스" in stock_name or "레버리지" in stock_name:
        return "이 종목은 인버스/레버리지 상품으로 투자 스타일 분석이 불가능합니다."
    elif "홀딩스" in stock_name or "홀딩" in stock_name or "지주" in stock_name:
        return "이 종목은 지주회사로 투자 스타일 분석이 불가능합니다."
    else:
        return (
            "이 종목은 AI 학습 데이터에 포함되지 않아 투자 스타일 분석이 불가능합니다."
        )


def analyze_stock(request: StockAnalyzeRequest, use_cache: bool = True):
    """
    주식 분석 with Redis 캐싱 + SPAC/우선주 필터링

    핵심: 스타일 태그를 생성할 수 있는지 판단하여 analyzable 반환

    Args:
        request: 주식 분석 요청 데이터
        use_cache: 캐시 사용 여부 (기본값: True)

    Returns:
        - analyzable: True → 정상 분석 가능 (포트폴리오 분석 가능)
        - analyzable: False → 분석 불가 (SPAC, 우선주 등) → 매수 차단
    """
    # ===== 1. 캐시 확인 =====
    if use_cache:
        try:
            cache_client = get_redis_client()
            cache_key = generate_cache_key(request)
            cached_result = cache_client.get(cache_key)

            if cached_result:
                return json.loads(cached_result)
        except Exception as e:
            print(f"Redis 캐시 조회 실패 (무시하고 계속): {e}")

    # ===== 2. AI 학습 DB에 있는지 확인 (핵심!) =====
    if request.stock_code not in stock_db.index:
        # AI 학습 데이터에 없음 → 스타일 태그 생성 불가
        result = {
            "stock_code": request.stock_code,
            "stock_name": "알 수 없는 종목",
            "final_style_tag": None,
            "style_description": None,
            "analyzable": False,
            "reason": get_unanalyzable_reason("", in_db=False),
        }

        # 분석 불가 결과도 캐싱 (TTL: 1시간)
        if use_cache:
            try:
                cache_client = get_redis_client()
                cache_key = generate_cache_key(request)
                cache_client.setex(
                    cache_key, 3600, json.dumps(result, ensure_ascii=False)
                )
            except Exception as e:
                print(f"Redis 캐시 저장 실패 (무시하고 계속): {e}")

        return result

    # ===== 3. 종목명 조회 =====
    try:
        stock_name_full = stock_db.loc[request.stock_code]["한글명"]
        # 한글명에 불필요한 텍스트가 붙어있을 수 있으므로 첫 단어만 추출
        stock_name = (
            str(stock_name_full).split()[0] if stock_name_full else "알 수 없는 종목"
        )
    except KeyError:
        stock_name = "알 수 없는 종목"

    # ===== 4. 종목명 필터링 (SPAC, 우선주 등) =====
    if not is_valid_stock_for_analysis(stock_name):
        result = {
            "stock_code": request.stock_code,
            "stock_name": stock_name,
            "final_style_tag": None,
            "style_description": None,
            "analyzable": False,
            "reason": get_unanalyzable_reason(stock_name, in_db=True),
        }

        # 분석 불가 결과도 캐싱
        if use_cache:
            try:
                cache_client = get_redis_client()
                cache_key = generate_cache_key(request)
                cache_client.setex(
                    cache_key, 3600, json.dumps(result, ensure_ascii=False)
                )
            except Exception as e:
                print(f"Redis 캐시 저장 실패 (무시하고 계속): {e}")

        return result

    # ===== 5. K-means 모델로 스타일 태그 생성 =====
    df = pd.DataFrame(
        [
            {
                "단축코드": request.stock_code,
                "시가총액": request.market_cap,
                "per": request.per,
                "pbr": request.pbr,
                "ROE": request.roe,
                "부채비율": request.debt_ratio,
                "배당수익률": request.dividend_yield,
            }
        ]
    )
    features = ["시가총액", "per", "pbr", "ROE", "부채비율", "배당수익률"]

    try:
        # inf, nan 처리
        df[features] = df[features].replace([np.inf, -np.inf], np.nan)
        df[features] = df[features].fillna(0)

        scaled = scaler.transform(df[features])
        pred_group = model.predict(scaled)[0]

        # ✅ 성공: 스타일 태그 생성 완료 + 멀티팩터 스코어링 (Step 3)
        g_score = growth_score(roe=request.roe, per=request.per)
        s_score = stability_score(
            debt_ratio=request.debt_ratio,
            dividend_yield=request.dividend_yield,
        )
        # 개별 종목 분석 시 유사도 정보 없으므로 중립값(50) 사용
        c_score = composite_score(50.0, g_score, s_score, DEFAULT_WEIGHTS)

        result = {
            "stock_code": request.stock_code,
            "stock_name": stock_name,
            "final_style_tag": tag_mapping[pred_group],
            "style_description": description_mapping[pred_group],
            "analyzable": True,  # ✅ 분석 가능
            "reason": None,
            "scores": {
                "growth_score": g_score,
                "stability_score": s_score,
                "similarity_score": 50.0,
                "composite_score": c_score,
            },
        }

    except Exception as e:
        # AI 모델 오류
        print(f"AI 분석 오류: {e}")
        result = {
            "stock_code": request.stock_code,
            "stock_name": stock_name,
            "final_style_tag": None,
            "style_description": None,
            "analyzable": False,
            "reason": "AI 모델 오류로 투자 스타일 분석에 실패했습니다.",
        }

    # ===== 6. 캐시 저장 (TTL: 1시간 = 3600초) =====
    if use_cache:
        try:
            cache_client = get_redis_client()
            cache_key = generate_cache_key(request)
            cache_client.setex(cache_key, 3600, json.dumps(result, ensure_ascii=False))
        except Exception as e:
            print(f"Redis 캐시 저장 실패 (무시하고 계속): {e}")

    return result


def recommend_stocks(request) -> dict:
    """
    사용자 포트폴리오 기반 종목 추천 (Step 3)

    2단계 유사도 계산:
    - 피처 유사도 (70%): 스케일링된 6차원 재무지표 벡터 간 코사인 유사도
    - 클러스터 유사도 (30%): 8차원 스타일 벡터 간 코사인 유사도
    """
    from app.domain.portfolio_analyze.service import get_portfolio_style_vector

    # 사용자 보유 종목 데이터 준비
    stocks_data = []
    portfolio_rows = []
    for s in request.stocks:
        stocks_data.append({
            "market_cap": s.market_cap,
            "per": s.per,
            "pbr": s.pbr,
            "roe": s.roe,
            "debt_ratio": s.debt_ratio,
            "dividend_yield": s.dividend_yield,
            "investment_amount": s.investment_amount,
        })
        portfolio_rows.append({
            "단축코드": s.stock_code,
            "시가총액": s.market_cap,
            "per": s.per,
            "pbr": s.pbr,
            "ROE": s.roe,
            "부채비율": s.debt_ratio,
            "배당수익률": s.dividend_yield,
            "투자금액": s.investment_amount,
        })

    # 6차원 피처 벡터 (스케일링된 가중평균)
    user_feature_vec = compute_user_feature_vector(stocks_data, scaler)

    # 8차원 클러스터 벡터 (투자비중 기반)
    portfolio_df = pd.DataFrame(portfolio_rows)
    user_cluster_vec, _ = get_portfolio_style_vector(portfolio_df)

    # 전체 종목 스코어링
    results = score_all_stocks(
        stock_db=stock_db,
        scaler=scaler,
        model=model,
        user_feature_vector=user_feature_vec,
        user_cluster_vector=user_cluster_vec if user_cluster_vec is not None else None,
        persona=request.persona,
        top_n=request.top_n,
    )

    return {
        "persona": request.persona,
        "total_scored": len(stock_db),
        "recommendations": results,
    }
