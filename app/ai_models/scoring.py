"""
Step 3: 멀티팩터 스코어링 알고리즘
- 코사인 유사도 (스타일 유사성)
- 성장성 점수 (ROE + PER 적정성)
- 안정성 점수 (부채비율 + 배당수익률)
"""

import numpy as np
import pandas as pd
from numpy.linalg import norm


# ============================================================
# 1. 코사인 유사도
# ============================================================

def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """
    두 벡터 간 코사인 유사도 계산.
    Returns: -1 ~ 1 (같은 방향일수록 1)
    """
    norm_a = norm(vec_a)
    norm_b = norm(vec_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))


def cosine_similarity_to_score(similarity: float) -> float:
    """코사인 유사도 [-1, 1] → 점수 [0, 100] 변환"""
    return round((similarity + 1) / 2 * 100, 2)


# ============================================================
# 2. 성장성 점수
# ============================================================

def growth_score(roe: float, per: float) -> float:
    """
    성장성 점수 (0~100)

    - ROE 점수 (60% 비중): ROE가 높을수록 좋음
      - ROE >= 20: 만점(100)
      - ROE 0~20: 선형 비례
      - ROE < 0: 0점

    - PER 적정성 점수 (40% 비중): 5~25 범위가 적정
      - PER 10~20: 만점 구간
      - PER 5~10, 20~25: 감점
      - PER < 0 (적자) 또는 > 50: 0점
    """
    # ROE 점수
    if roe <= 0:
        roe_score = 0.0
    elif roe >= 20:
        roe_score = 100.0
    else:
        roe_score = (roe / 20) * 100

    # PER 적정성 점수
    if per <= 0 or per > 100:
        per_score = 0.0
    elif 10 <= per <= 20:
        per_score = 100.0
    elif 5 <= per < 10:
        per_score = (per - 5) / 5 * 100
    elif 20 < per <= 35:
        per_score = (35 - per) / 15 * 100
    elif 35 < per <= 100:
        per_score = 0.0
    else:
        per_score = 0.0

    score = roe_score * 0.6 + per_score * 0.4
    return round(max(0, min(100, score)), 2)


# ============================================================
# 3. 안정성 점수
# ============================================================

def stability_score(debt_ratio: float, dividend_yield: float) -> float:
    """
    안정성 점수 (0~100)

    - 부채비율 점수 (60% 비중): 낮을수록 좋음
      - 부채비율 0~50: 만점(100)
      - 50~200: 선형 감소
      - 200 이상: 0점

    - 배당수익률 점수 (40% 비중): 높을수록 좋음
      - 배당 >= 5%: 만점(100)
      - 0~5%: 선형 비례
      - 0%: 0점
    """
    # 부채비율 점수
    if debt_ratio <= 50:
        debt_score = 100.0
    elif debt_ratio <= 200:
        debt_score = (200 - debt_ratio) / 150 * 100
    else:
        debt_score = 0.0

    # 배당수익률 점수
    if dividend_yield <= 0:
        div_score = 0.0
    elif dividend_yield >= 5:
        div_score = 100.0
    else:
        div_score = (dividend_yield / 5) * 100

    score = debt_score * 0.6 + div_score * 0.4
    return round(max(0, min(100, score)), 2)


# ============================================================
# 4. 종합 스코어
# ============================================================

# 페르소나별 가중치 프리셋
PERSONA_WEIGHTS = {
    "벤저민 그레이엄": {"similarity": 0.3, "growth": 0.1, "stability": 0.6},
    "워렌 버핏":       {"similarity": 0.3, "growth": 0.4, "stability": 0.3},
    "피터 린치":       {"similarity": 0.3, "growth": 0.5, "stability": 0.2},
    "캐시 우드":       {"similarity": 0.2, "growth": 0.7, "stability": 0.1},
    "제레미 시겔":     {"similarity": 0.3, "growth": 0.1, "stability": 0.6},
    "데이비드 드레먼": {"similarity": 0.4, "growth": 0.2, "stability": 0.4},
    "존 보글":         {"similarity": 0.3, "growth": 0.3, "stability": 0.4},
    "켄 피셔":         {"similarity": 0.3, "growth": 0.3, "stability": 0.4},
}

DEFAULT_WEIGHTS = {"similarity": 0.4, "growth": 0.3, "stability": 0.3}


def composite_score(
    similarity_score: float,
    growth: float,
    stability: float,
    weights: dict = None,
) -> float:
    """
    3축 결합 종합 점수 (0~100)

    Args:
        similarity_score: 코사인 유사도 점수 (0~100)
        growth: 성장성 점수 (0~100)
        stability: 안정성 점수 (0~100)
        weights: {"similarity": w1, "growth": w2, "stability": w3}
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS

    w1 = weights["similarity"]
    w2 = weights["growth"]
    w3 = weights["stability"]

    score = w1 * similarity_score + w2 * growth + w3 * stability
    return round(max(0, min(100, score)), 2)


# ============================================================
# 5. 종목 스코어링 (단일 종목)
# ============================================================

def score_stock(
    stock_features: dict,
    user_vector: np.ndarray = None,
    stock_cluster_vector: np.ndarray = None,
    persona: str = None,
) -> dict:
    """
    단일 종목에 대한 멀티팩터 스코어 계산

    Args:
        stock_features: {"roe": float, "per": float, "debt_ratio": float, "dividend_yield": float}
        user_vector: 사용자 포트폴리오 스타일 벡터 (8차원, 없으면 유사도 50점 기본)
        stock_cluster_vector: 종목의 클러스터 원-핫 벡터 (8차원)
        persona: 페르소나 이름 (가중치 프리셋 선택용)

    Returns:
        {"growth_score", "stability_score", "similarity_score", "composite_score", "weights_used"}
    """
    g_score = growth_score(
        roe=stock_features.get("roe", 0),
        per=stock_features.get("per", 0),
    )
    s_score = stability_score(
        debt_ratio=stock_features.get("debt_ratio", 0),
        dividend_yield=stock_features.get("dividend_yield", 0),
    )

    # 코사인 유사도 계산
    if user_vector is not None and stock_cluster_vector is not None:
        sim = cosine_similarity(user_vector, stock_cluster_vector)
        sim_score = cosine_similarity_to_score(sim)
    else:
        sim_score = 50.0  # 유사도 정보 없으면 중립

    weights = PERSONA_WEIGHTS.get(persona, DEFAULT_WEIGHTS)
    total = composite_score(sim_score, g_score, s_score, weights)

    return {
        "growth_score": g_score,
        "stability_score": s_score,
        "similarity_score": sim_score,
        "composite_score": total,
        "weights_used": weights,
    }


# ============================================================
# 6. 배치 스코어링 (전체 종목 대상 추천용)
# ============================================================

def score_all_stocks(
    stock_db: pd.DataFrame,
    scaler,
    model,
    user_vector: np.ndarray = None,
    persona: str = None,
    top_n: int = 10,
) -> list:
    """
    전체 종목 DB에서 종합 점수 기준 상위 N개 추천

    Args:
        stock_db: 전체 종목 DataFrame (시가총액, per, pbr, ROE, 부채비율, 배당수익률)
        scaler: StandardScaler (학습된 스케일러)
        model: KMeans 모델
        user_vector: 사용자 포트폴리오 스타일 벡터 (8차원)
        persona: 페르소나 이름
        top_n: 상위 몇 개 반환할지

    Returns:
        [{"stock_code", "stock_name", "composite_score", "growth_score", "stability_score", "similarity_score", "style_tag"}, ...]
    """
    from app.domain.stock_analyze.service import tag_mapping, is_valid_stock_for_analysis

    features = ["시가총액", "per", "pbr", "ROE", "부채비율", "배당수익률"]
    df = stock_db.copy()

    # 유효 종목만 필터링
    if "한글명" in df.columns:
        name_col = df["한글명"].astype(str).str.split().str[0]
        df["clean_name"] = name_col
        df = df[df["clean_name"].apply(is_valid_stock_for_analysis)]

    # inf/nan 처리
    df[features] = df[features].replace([np.inf, -np.inf], np.nan).fillna(0)

    # 클러스터 예측
    scaled = scaler.transform(df[features])
    df["cluster"] = model.predict(scaled)

    results = []
    for idx, row in df.iterrows():
        # 종목의 클러스터 원-핫 벡터
        cluster_vec = np.zeros(8)
        cluster_vec[int(row["cluster"])] = 1.0

        scores = score_stock(
            stock_features={
                "roe": row["ROE"],
                "per": row["per"],
                "debt_ratio": row["부채비율"],
                "dividend_yield": row["배당수익률"],
            },
            user_vector=user_vector,
            stock_cluster_vector=cluster_vec,
            persona=persona,
        )

        stock_code = idx if isinstance(idx, str) else row.get("단축코드", str(idx))
        stock_name = row.get("clean_name", row.get("한글명", "알 수 없음"))
        if isinstance(stock_name, str):
            stock_name = stock_name.split()[0]

        results.append({
            "stock_code": stock_code,
            "stock_name": stock_name,
            "style_tag": tag_mapping.get(int(row["cluster"]), ""),
            **scores,
        })

    # 종합 점수 기준 정렬
    results.sort(key=lambda x: x["composite_score"], reverse=True)
    return results[:top_n]
