import pandas as pd
import numpy as np
import joblib
import persona_definitions as pd_data  # 페르소나 정의
from numpy.linalg import norm  # 일치율 계산

# ----------------------------------------------------
# 1. AI 핵심 모듈 로드 (뇌 + 번역기)
# ----------------------------------------------------
try:
    model = joblib.load('kmeans_model.pkl')
    scaler = joblib.load('scaler.pkl')
    print("✅ AI 모델(kmeans_model.pkl) 및 번역기(scaler.pkl) 로드 성공.")
except FileNotFoundError:
    print("🚨 오류: 모델 파일(.pkl)을 찾을 수 없습니다. 01, 02 스크립트를 먼저 실행하세요.")
    exit()

# ----------------------------------------------------
# 2. 가상의 재무 데이터베이스 로드 (API 시뮬레이션)
# ----------------------------------------------------
try:
    # 실제로는 이 부분을 API 호출로 대체해야 합니다.
    stock_db = pd.read_csv('dummy_stock_db.csv', encoding='utf-8', dtype={'단축코드': str})
    stock_db['단축코드'] = stock_db['단축코드'].str.strip()
    print("✅ 가상 재무 DB(dummy_stock_db.csv) 로드 성공.")
except FileNotFoundError:
    print("🚨 오류: 'dummy_stock_db.csv' 파일이 없습니다. 먼저 생성해주세요.")
    exit()

# ----------------------------------------------------
# 3. 가상의 사용자 포트폴리오 (더미 데이터)
# ----------------------------------------------------
# 시뮬레이션: "삼성전자(50%) + DB하이텍(50%)"를 구매한 사용자
user_portfolio_data = {
    '단축코드': ['001040', '0036930'],
    '투자금액': [1000000, 1000000]  # 50% : 50%
}
user_df = pd.DataFrame(user_portfolio_data)
user_df['단축코드'] = user_df['단축코드'].astype(str).str.strip()


# ----------------------------------------------------
# 4. (핵심) AI 예측 엔진 (Phase 2)
# ----------------------------------------------------
def get_style_vector(user_portfolio_df, stock_db, scaler, model):
    # 1. 사용자의 주식 코드에 해당하는 재무 데이터를 DB에서 가져옵니다. (API 호출 시뮬레이션)
    merged_df = pd.merge(user_portfolio_df, stock_db, on='단축코드', how='left')

    # 2. AI가 분석할 6가지 재료(Feature)를 분리합니다.
    feature_columns = ['시가총액', 'per', 'pbr', 'ROE', '부채비율', '배당수익률']
    features_data = merged_df[feature_columns]

    # 3. AI '번역기(Scaler)'로 재무 데이터를 번역(스케일링)합니다.
    #    .transform() 사용이 중요!
    scaled_data = scaler.transform(features_data)

    # 4. AI '뇌(Model)'에게 예측을 명령합니다.
    predicted_groups = model.predict(scaled_data)  # [5, 1] (예시)

    # 5. 예측된 그룹 번호를 포트폴리오에 추가합니다.
    merged_df['group_tag'] = predicted_groups

    # 6. 투자금액 기준으로 비중(Weight)을 계산합니다.
    merged_df['비중'] = merged_df['투자금액'] / merged_df['투자금액'].sum()

    # 7. 그룹별로 비중을 합산하여 사용자의 최종 스타일 벡터(U)를 생성합니다.
    user_style_raw = merged_df.groupby('group_tag')['비중'].sum()
    all_groups = np.arange(8)
    user_style_vector = user_style_raw.reindex(all_groups, fill_value=0.0).values

    # 8. 정규화된 벡터(총합 1.0)를 반환합니다.
    vector_sum = user_style_vector.sum()
    if vector_sum == 0: return None

    return user_style_vector / vector_sum


# ----------------------------------------------------
# 5. 페르소나 매칭 (Phase 3) - (05번 스크립트와 동일)
# ----------------------------------------------------
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


# ----------------------------------------------------
# 6. 실행 및 결과 출력
# ----------------------------------------------------
if __name__ == "__main__":

    # AI 예측 엔진 실행!
    user_vector = get_style_vector(user_df, stock_db, scaler, model)

    if user_vector is not None:
        print("\n" + "=" * 40)
        print("           🚀 사용자 포트폴리오 분석 결과 (예측 엔진)")
        print("=" * 40)

        # 2-1. 사용자 스타일 태그 비중 출력
        print("📊 사용자 스타일 태그 비중:")
        tag_names = ['[안정형 일반주]', '[고효율 우량주]', '[초고배당 가치주]', '[고위험 저평가주]',
                     '[고성장 기대주]', '[초대형 우량주]', '[초저평가 가치주]', '[고가치 성장주]']

        user_style_summary = [(tag_names[i], user_vector[i] * 100) for i in range(8) if user_vector[i] > 0]

        for name, percent in sorted(user_style_summary, key=lambda item: item[1], reverse=True):
            print(f"- {name}: {percent:.2f}%")

        print("\n" + "-" * 40)

        # 3. 페르소나 매칭 결과 출력
        match_results = calculate_persona_match(user_vector)

        print("✨ 페르소나 일치율 (당신의 롤모델):")
        sorted_results = sorted(match_results.items(), key=lambda item: item[1], reverse=True)

        for name, percent in sorted_results:
            print(f"- {name}: {percent:.2f}%")

        print("\n" + "=" * 40)