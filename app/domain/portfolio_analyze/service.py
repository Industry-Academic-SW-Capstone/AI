import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from numpy.linalg import norm
from app.ai_models import persona_definitions as pd_data  # '근거', '철학'을 모두 임포트
from .dto import PortfolioAnalyzeRequest

# 모델, 스케일러, DB 로드 (파일 절대경로)
BASE_DIR = Path(__file__).resolve().parents[2]  # /app/app
MODEL_DIR = BASE_DIR / "ai_models"
DATA_DIR = BASE_DIR / "data"

model = joblib.load(str(MODEL_DIR / "kmeans_model.pkl"))
scaler = joblib.load(str(MODEL_DIR / "scaler.pkl"))
stock_db = pd.read_csv(str(DATA_DIR / "dummy_stock_db.csv"), dtype={"단축코드": str})

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

# '주린이 해설' 버전의 상세한 description_mapping
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


def get_portfolio_style_vector(stocks_df: pd.DataFrame):
    feature_columns = ["시가총액", "per", "pbr", "ROE", "부채비율", "배당수익률"]

    # 안정성 강화: inf, -inf 값을 NaN으로 변경
    stocks_df[feature_columns] = stocks_df[feature_columns].replace(
        [np.inf, -np.inf], np.nan
    )
    # 안정성 강화: NaN 값을 0으로 채움 (모델 예측 시 오류 방지)
    stocks_df[feature_columns] = stocks_df[feature_columns].fillna(0)

    scaled_data = scaler.transform(stocks_df[feature_columns])
    predicted_groups = model.predict(scaled_data)
    stocks_df["group_tag"] = predicted_groups

    # 투자금액 0이거나 NaN인 경우 제외 (비중 계산 오류 방지)
    stocks_df = stocks_df[stocks_df["투자금액"] > 0]

    if stocks_df.empty:
        return None, None

    stocks_df["비중"] = stocks_df["투자금액"] / stocks_df["투자금액"].sum()
    user_style_raw = stocks_df.groupby("group_tag")["비중"].sum()
    all_groups = np.arange(8)
    user_style_vector = user_style_raw.reindex(all_groups, fill_value=0.0).values

    vector_sum = user_style_vector.sum()
    if vector_sum == 0:
        return None, None

    return user_style_vector / vector_sum, stocks_df


def calculate_persona_match(user_vector):
    results = {}
    for name, persona_style_dict in pd_data.ALL_PERSONAS.items():
        all_groups = np.arange(8)
        persona_vector = (
            pd.Series(persona_style_dict).reindex(all_groups, fill_value=0.0).values
        )
        distance = norm(user_vector - persona_vector)
        max_distance = np.sqrt(2.0)
        similarity = max(0, 100 - ((distance / max_distance) * 100))
        results[name] = round(similarity, 2)
    return results


def analyze_portfolio(request: PortfolioAnalyzeRequest):
    df = pd.DataFrame([s.dict() for s in request.stocks])

    style_vector, merged_df = get_portfolio_style_vector(df)

    if style_vector is None or merged_df is None or merged_df.empty:
        # 분석 실패 시 DTO에 정의된 빈 구조 반환
        return {
            "stock_details": [],
            "summary": {},
            "style_breakdown": [],
            "persona_match": [],
        }

    # --- [1] 보유 종목 상세 분석 ---
    merged_df["final_style_tag"] = merged_df["group_tag"].map(tag_mapping)
    merged_df["style_description"] = merged_df["group_tag"].map(description_mapping)

    df_with_names = pd.merge(
        merged_df, stock_db[["단축코드", "한글명"]], on="단축코드", how="left"
    )
    df_with_names["한글명"] = df_with_names["한글명"].fillna("알 수 없는 종목")

    stock_details = []
    for _, row in df_with_names.iterrows():
        if pd.notna(row["final_style_tag"]):
            stock_details.append(
                {
                    "stock_code": row["단축코드"],
                    "stock_name": row["한글명"],
                    "style_tag": row["final_style_tag"],
                    "description": row["style_description"],
                }
            )

    # --- [2] 포트폴리오 종합 성향 (가중 평균) ---
    feature_columns = ["시가총액", "per", "pbr", "ROE", "부채비율", "배당수익률"]
    summary = {}
    for col in feature_columns:
        weighted_avg = (merged_df[col] * merged_df["비중"]).sum()
        summary[col] = round(weighted_avg, 2)  # 소수점 2자리 반올림

    # --- [3] 최종 스타일 태그 비중 ---
    tag_names = list(tag_mapping.values())
    style_breakdown = []
    for i, percent in enumerate(style_vector):
        if percent > 0:
            style_breakdown.append(
                {"style_tag": tag_names[i], "percentage": round(percent * 100, 2)}
            )
    style_breakdown = sorted(
        style_breakdown, key=lambda x: x["percentage"], reverse=True
    )

    # --- [4] 페르소나 일치율 (근거 + 철학) ---
    persona_results = calculate_persona_match(style_vector)

    # [수정됨] '근거'와 '철학'을 pd_data에서 모두 가져옴
    persona_reason = pd_data.PERSONA_REASON
    persona_philosophy = pd_data.PERSONA_PHILOSOPHY

    persona_match = []
    sorted_matches = sorted(
        persona_results.items(), key=lambda item: item[1], reverse=True
    )

    for name, percent in sorted_matches:
        # [수정됨] '근거'와 '철학'을 조합
        reason_text = persona_reason.get(name, "[근거: 정보 없음]")
        philosophy_text = persona_philosophy.get(name, "관련 철학 정보가 없습니다.")
        full_philosophy = f"{reason_text} {philosophy_text}"  # 문자열 합치기

        persona_match.append(
            {
                "name": name,
                "percentage": percent,
                "philosophy": full_philosophy,  # 합쳐진 문자열을 반환
            }
        )

    # --- 최종 응답 조립 ---
    return {
        "stock_details": stock_details,
        "summary": summary,
        "style_breakdown": style_breakdown,
        "persona_match": persona_match,
    }
