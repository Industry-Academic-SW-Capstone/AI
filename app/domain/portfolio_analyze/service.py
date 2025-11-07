import pandas as pd
import numpy as np
import joblib
from numpy.linalg import norm
from ai_models import persona_definitions as pd_data

# 모델, 스케일러, DB 로드
model = joblib.load("ai_models/kmeans_model.pkl")
scaler = joblib.load("ai_models/scaler.pkl")
stock_db = pd.read_csv("data/dummy_stock_db.csv", dtype={"단축코드": str}).set_index("단축코드")

tag_mapping = {
    0: '[안정형 일반주]', 1: '[고효율 우량주]', 2: '[초고배당 가치주]',
    3: '[고위험 저평가주]', 4: '[고성장 기대주]', 5: '[초대형 우량주]',
    6: '[초저평가 가치주]', 7: '[고가치 성장주]'
}

description_mapping = {
    0: "안정적인 보통 주식...",
    1: "숨겨진 보물 우량주...",
    2: "초고배당 가치주...",
    3: "고위험 저평가주...",
    4: "고성장 기대주...",
    5: "초대형 우량주...",
    6: "초저평가 가치주...",
    7: "고가치 성장주..."
}

def get_portfolio_style_vector(stocks_df: pd.DataFrame):
    feature_columns = ['시가총액', 'per', 'pbr', 'ROE', '부채비율', '배당수익률']
    scaled_data = scaler.transform(stocks_df[feature_columns])
    predicted_groups = model.predict(scaled_data)
    stocks_df['group_tag'] = predicted_groups

    stocks_df['비중'] = stocks_df['투자금액'] / stocks_df['투자금액'].sum()
    user_style_raw = stocks_df.groupby('group_tag')['비중'].sum()
    all_groups = np.arange(8)
    user_style_vector = user_style_raw.reindex(all_groups, fill_value=0.0).values
    vector_sum = user_style_vector.sum()
    if vector_sum == 0: return None, None
    return user_style_vector / vector_sum, stocks_df

def calculate_persona_match(user_vector):
    results = {}
    for name, persona_style_dict in pd_data.ALL_PERSONAS.items():
        all_groups = np.arange(8)
        persona_vector = pd.Series(persona_style_dict).reindex(all_groups, fill_value=0.0).values
        distance = norm(user_vector - persona_vector)
        max_distance = np.sqrt(2.0)
        similarity = max(0, 100 - ((distance / max_distance) * 100))
        results[name] = round(similarity, 2)
    return results

def analyze_portfolio(request):
    df = pd.DataFrame([s.dict() for s in request.stocks])
    style_vector, merged_df = get_portfolio_style_vector(df)
    if style_vector is None:
        return {"portfolio_style_vector": [], "summary": {}, "persona_match": {}}

    # 포트폴리오 평균 지표
    feature_columns = ['시가총액', 'per', 'pbr', 'ROE', '부채비율', '배당수익률']
    avg_metrics = {col: (merged_df[col] * merged_df['비중']).sum() for col in feature_columns}
    persona_results = calculate_persona_match(style_vector)

    return {
        "portfolio_style_vector": style_vector.tolist(),
        "summary": avg_metrics,
        "persona_match": persona_results
    }
