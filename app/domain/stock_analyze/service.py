import pandas as pd
import numpy as np
import joblib
from ai_models import persona_definitions as pd_data

# 모델, 스케일러, DB 로드 (전역)
model = joblib.load("ai_models/kmeans_model.pkl")
scaler = joblib.load("ai_models/scaler.pkl")
stock_db = pd.read_csv("data/dummy_stock_db.csv", dtype={"단축코드": str}).set_index("단축코드")

tag_mapping = {
    0: '[안정형 일반주]', 1: '[고효율 우량주]', 2: '[초고배당 가치주]',
    3: '[고위험 저평가주]', 4: '[고성장 기대주]', 5: '[초대형 우량주]',
    6: '[초저평가 가치주]', 7: '[고가치 성장주]'
}

description_mapping = {
    0: "안정적인 보통 주식: 회사가 빚(부채)이 적어서 일단 망할 위험이 낮아요. 하지만 돈을 벌어들이는 효율(ROE)이 평범해서, 주가가 폭발적으로 오르지도 않을 거예요.",
    1: "숨겨진 보물 우량주: PER이 낮아서 저평가되어 있고, ROE가 높아 효율성이 뛰어난 믿음직한 기업이에요.",
    2: "초고배당 가치주: 배당수익률이 높고 PER이 낮아 현재 가치도 괜찮은 그룹이에요.",
    3: "고위험 저평가주: PBR이 낮지만 부채비율이 높아 위험할 수 있어요.",
    4: "고성장 기대주: PER이 매우 높고, 앞으로 엄청난 성장이 기대되는 기업이에요.",
    5: "초대형 우량주: 시가총액이 가장 크고 안정적인 그룹이에요.",
    6: "초저평가 가치주: PER과 PBR이 낮고 부채비율도 낮아 싸고 안전한 종목이에요.",
    7: "고가치 성장주: PBR과 ROE가 높아 시장에서 비싼 값을 지불할 가치가 있는 성장 기업이에요."
}

def analyze_stock(request):
    df = pd.DataFrame([request.dict()])
    features = ['시가총액', 'per', 'pbr', 'ROE', '부채비율', '배당수익률']
    scaled = scaler.transform(df[features])
    pred_group = model.predict(scaled)[0]

    return {
        "단축코드": request.단축코드,
        "final_style_tag": tag_mapping[pred_group],
        "style_description": description_mapping[pred_group]
    }
