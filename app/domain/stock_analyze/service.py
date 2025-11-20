import pandas as pd
import numpy as np
import joblib
import json
import hashlib
import os
import redis
from pathlib import Path
from numpy.linalg import norm
from .dto import StockAnalyzeRequest, StockAnalyzeResponse


# 모델, 스케일러, DB 로드 (파일 절대경로)
BASE_DIR = Path(__file__).resolve().parents[2]  # /app/app
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


def analyze_stock(request: StockAnalyzeRequest, use_cache: bool = True):
    """
    주식 분석 with Redis 캐싱

    Args:
        request: 주식 분석 요청 데이터
        use_cache: 캐시 사용 여부 (기본값: True)
    """
    # 1. 캐시 확인
    if use_cache:
        try:
            cache_client = get_redis_client()
            cache_key = generate_cache_key(request)
            cached_result = cache_client.get(cache_key)

            if cached_result:
                return json.loads(cached_result)
        except Exception as e:
            print(f"Redis 캐시 조회 실패 (무시하고 계속): {e}")

    # 2. 캐시 미스 → AI 모델 추론
    # Spring 서버가 보내는 영문 필드명을 모델이 기대하는 한글 필드명으로 변환
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
        scaled = scaler.transform(df[features])
        pred_group = model.predict(scaled)[0]
    except Exception as e:
        # TODO: 실제 서비스에서는 500 에러를 반환하도록 예외 처리 필요
        return {"error": f"AI 분석 중 오류 발생: {str(e)}"}

    # stock_db에서 한글명 조회 (첫 단어만 추출하여 한글명만 가져옴)
    try:
        stock_name_full = stock_db.loc[request.stock_code]["한글명"]
        # 한글명에 불필요한 텍스트가 붙어있을 수 있으므로 첫 단어만 추출
        stock_name = (
            str(stock_name_full).split()[0] if stock_name_full else "알 수 없는 종목"
        )
    except KeyError:
        stock_name = "알 수 없는 종목"  # DB에 없는 경우

    # Spring 서버가 기대하는 응답 형식으로 반환 (영문 필드명)
    result = {
        "stock_code": request.stock_code,
        "stock_name": stock_name,
        "style_tag": tag_mapping[pred_group],
        "style_description": description_mapping[pred_group],
    }

    # 3. 캐시 저장 (TTL: 1시간 = 3600초)
    # 재무 지표는 LLM 기업 설명보다 자주 변할 수 있으므로 TTL을 짧게 설정
    if use_cache:
        try:
            cache_client = get_redis_client()
            cache_key = generate_cache_key(request)
            cache_client.setex(cache_key, 3600, json.dumps(result, ensure_ascii=False))
        except Exception as e:
            print(f"Redis 캐시 저장 실패 (무시하고 계속): {e}")

    return result
