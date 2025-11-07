import pandas as pd
import numpy as np
import joblib
from app.ai_models import persona_definitions as pd_data
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
    stock_db = pd.read_csv('app/data/dummy_stock_db.csv', encoding='utf-8', dtype={'단축코드': str})
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
    '단축코드': ['005930', '000990'],
    '투자금액': [1000000, 1000000]  # 50% : 50%
}
user_df = pd.DataFrame(user_portfolio_data)
user_df['단축코드'] = user_df['단축코드'].astype(str).str.strip()


# ----------------------------------------------------
# 4. (핵심) AI 예측 엔진 (Phase 2)
# ----------------------------------------------------
def get_style_vector(user_portfolio_df, stock_db, scaler, model):
    merged_df = pd.merge(user_portfolio_df, stock_db, on='단축코드', how='left')
    feature_columns = ['시가총액', 'per', 'pbr', 'ROE', '부채비율', '배당수익률']
    features_data = merged_df[feature_columns]
    scaled_data = scaler.transform(features_data)
    predicted_groups = model.predict(scaled_data)
    merged_df['group_tag'] = predicted_groups

    tag_mapping = {
        0: '[안정형 일반주]', 1: '[고효율 우량주]', 2: '[초고배당 가치주]',
        3: '[고위험 저평가주]', 4: '[고성장 기대주]', 5: '[초대형 우량주]',
        6: '[초저평가 가치주]', 7: '[고가치 성장주]'
    }
    description_mapping = {
        0: "안정적인 보통 주식: 회사가 빚(부채)이 적어서 일단 망할 위험이 낮아요. 하지만 돈을 벌어들이는 효율(ROE)이 평범해서, 주가가 폭발적으로 오르지도 않을 거예요.",
        1: "숨겨진 보물 우량주: PER이 낮아서 (버는 돈 대비 주가가 저렴해서) 저평가되어 있어요. 게다가 ROE가 높아서 (자기 돈으로 장사를 매우 잘해서) 효율성이 뛰어난 믿음직한 기업이에요.",
        2: "초고배당 가치주: 다른 주식들보다 배당수익률이 압도적으로 높아요. (주식을 은행 이자처럼 사는 개념) PER이 낮아 (저렴해서) 현재의 가치도 괜찮은 그룹이에요.",
        3: "고위험 저평가주: PBR이 매우 낮아 (회사가 가진 재산보다 주가가 훨씬 싸요). But! 부채비율이 너무 높아 (빚이 많아) 잘못되면 크게 위험해질 수 있어요.",
        4: "고성장 기대주: PER이 엄청나게 높아요. (회사가 버는 돈에 비해 주가가 매우 비싸요). 이는 사람들이 이 회사가 '앞으로 엄청난 대박을 칠 것'이라고 기대하기 때문이에요.",
        5: "초대형 우량주: 시가총액이 가장 커요. (회사의 덩치가 가장 커요). 워낙 크기 때문에 크게 오르기는 어렵지만, 시장을 대표하는 안정적인 그룹이에요.",
        6: "초저평가 가치주: PER과 PBR이 가장 낮고 (가장 저렴함) 부채비율도 가장 낮아 (가장 안전함) '싸고 안전한 종목'을 찾는 정석적인 가치투자자들이 선호하는 그룹이에요.",
        7: "고가치 성장주: PBR이 높아 (이미 비싸지만) ROE도 높아 (실제로 돈도 잘 벌고 효율도 좋음). 시장에서 '비싼 값을 지불할 가치'가 있다고 인정받는 성장 기업 그룹이에요."
    }

    merged_df['final_style_tag'] = merged_df['group_tag'].map(tag_mapping)
    merged_df['style_description'] = merged_df['group_tag'].map(description_mapping)

    merged_df['비중'] = merged_df['투자금액'] / merged_df['투자금액'].sum()
    user_style_raw = merged_df.groupby('group_tag')['비중'].sum()
    all_groups = np.arange(8)
    user_style_vector = user_style_raw.reindex(all_groups, fill_value=0.0).values

    vector_sum = user_style_vector.sum()
    if vector_sum == 0: return None, None

    return user_style_vector / vector_sum, merged_df


# ----------------------------------------------------
# 5. 페르소나 매칭 (Phase 3) - (변경 없음)
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
# 6. 실행 및 결과 출력 (★업그레이드된 부분★)
# ----------------------------------------------------
if __name__ == "__main__":

    user_vector, merged_details = get_style_vector(user_df, stock_db, scaler, model)

    if user_vector is not None:
        print("\n" + "=" * 50)
        print("           🚀 사용자 포트폴리오 종합 분석 리포트")
        print("=" * 50)

        # [1] 보유 종목 상세 분석
        print("✅ [1] 보유 종목 상세 분석 (AI 예측)")
        print("-" * 50)
        for index, row in merged_details.iterrows():
            if pd.notna(row['final_style_tag']):
                print(f"📊 종목명: {row['한글명']} ({row['단축코드']})")
                print(f"   - AI 스타일: {row['final_style_tag']}")
                print(f"   - 주린이 해설: {row['style_description']}")

        # [2] 포트폴리오 종합 성향
        print("\n" + "=" * 50)
        print("✅ [2] 포트폴리오 종합 성향 (가중 평균)")
        print("-" * 50)

        feature_columns = ['시가총액', 'per', 'pbr', 'ROE', '부채비율', '배당수익률']
        avg_metrics = {}
        for col in feature_columns:
            weighted_avg = (merged_details[col] * merged_details['비중']).sum()
            avg_metrics[col] = weighted_avg

        print(f"   - 평균 PER (성장성): {avg_metrics['per']:.2f} 배")
        print(f"   - 평균 PBR (자산가치): {avg_metrics['pbr']:.2f} 배")
        print(f"   - 평균 ROE (효율성): {avg_metrics['ROE']:.2f} %")
        print(f"   - 평균 부채비율 (안정성): {avg_metrics['부채비율']:.2f} %")
        print(f"   - 평균 배당수익률: {avg_metrics['배당수익률']:.2f} %")

        # [3] 최종 스타일 태그 비중
        print("\n" + "=" * 50)
        print("✅ [3] 최종 스타일 태그 비중")
        print("-" * 50)
        tag_names = ['[안정형 일반주]', '[고효율 우량주]', '[초고배당 가치주]', '[고위험 저평가주]',
                     '[고성장 기대주]', '[초대형 우량주]', '[초저평가 가치주]', '[고가치 성장주]']

        user_style_summary = [(tag_names[i], user_vector[i] * 100) for i in range(8) if user_vector[i] > 0]

        for name, percent in sorted(user_style_summary, key=lambda item: item[1], reverse=True):
            print(f"   - {name}: {percent:.2f}%")

        # [4] 페르소나 일치율 (★수정된 부분★)
        print("\n" + "=" * 50)
        print("✅ [4] 페르소나 일치율 (당신의 롤모델)")
        print("-" * 50)
        match_results = calculate_persona_match(user_vector)
        sorted_results = sorted(match_results.items(), key=lambda item: item[1], reverse=True)

        # 페르소나 철학 데이터 로드
        philosophies = pd_data.PERSONA_PHILOSOPHY

        for i, (name, percent) in enumerate(sorted_results):
            # 15% 이상 비중이 있는 유의미한 페르소나만 출력
            if percent > 15:
                if i == 0:
                    print(f"   🥇 {name}: {percent:.2f}% (가장 유사!)")
                else:
                    print(f"   🥈 {name}: {percent:.2f}%")

                # '왜' 매칭되었는지 근거(철학)를 출력
                if name in philosophies:
                    print(f"       ➡️ 이유: {philosophies[name]}\n")

        print("\n" + "=" * 50)