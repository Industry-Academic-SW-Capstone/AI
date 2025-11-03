import pandas as pd
import numpy as np
import persona_definitions as pd_data
from numpy.linalg import norm  # 유클리디안 거리 계산을 위해 사용

# ----------------------------------------------------
# 1. 가상의 사용자 포트폴리오 (더미 데이터) 정의
# ----------------------------------------------------
# NOTE: 이 종목들이 AI DB에 없을 경우, 아래 DEBUG 섹션에서 경고가 출력됩니다.
user_portfolio_data = {
    # KB금융, LG화학, 롯데정밀화학, 포스코퓨처엠, 하나금융지주 (가장 최근에 사용한 안전 데이터)
    '단축코드': ['10690', '44450', '79940'], # 079940이 맞습니다 (79940 -> 079940)
    '투자금액': [1000000, 1000000, 1000000]
}
user_df = pd.DataFrame(user_portfolio_data)


# ----------------------------------------------------
# 2. 사용자 스타일 태그 비중 계산 (Phase 2 구현)
# ----------------------------------------------------
def analyze_user_style(user_portfolio_df):
    # --- [1. 코드 타입 통일 및 공백 제거] ---
    # 1-1. 사용자 포트폴리오의 '단축코드'를 확실히 문자열로 변환하고 양 끝 공백 제거 (★Fix 1★)
    user_portfolio_df['단축코드'] = user_portfolio_df['단축코드'].astype(str).str.strip()

    # 1-2. AI 태그 데이터베이스 로드 시, '단축코드'를 문자열로 지정하여 로드합니다.
    try:
        df_tags = pd.read_csv('stockit_final_tagged_data.csv', encoding='utf-8', dtype={'단축코드': str})
    except FileNotFoundError:
        print("오류: stockit_final_tagged_data.csv 파일을 찾을 수 없습니다. 04_apply_final_tags.py를 먼저 실행하세요.")
        return None, None

    # 1-3. df_tags의 '단축코드' 공백 제거 (★Fix 2★)
    df_tags['단축코드'] = df_tags['단축코드'].str.strip()

    # 사용자 포트폴리오와 AI 태그 정보를 단축코드를 기준으로 병합 (Left Join)
    merged_df = pd.merge(user_portfolio_df, df_tags, on='단축코드', how='left')

    # --- [DEBUG 코드: 매칭 실패 종목 확인] ---
    unmatched_stocks = merged_df[merged_df['final_style_tag'].isna()]
    if not unmatched_stocks.empty:
        print("\n--- ⚠️ 경고: 다음 종목들은 AI 분석 DB에 없습니다! (매칭 실패) ---")
        print(unmatched_stocks[['단축코드', '투자금액']])
        print("----------------------------------------------------------------------\n")

        # 매칭된 종목이 하나도 없으면 (총 투자금액 대비 NaN이 100%면) 분석 중단
        matched_count = merged_df['final_style_tag'].count()
        if matched_count == 0:
            print("🚨 치명적 오류: 포트폴리오의 모든 종목이 DB와 매칭에 실패했습니다. (29.29% 오류 원인)")
            return None, None  # 분석 중단

    # 투자금액으로 비중 계산 (NaN 값은 자동 제외됨)
    # NOTE: NaN이 아닌 종목의 투자금액만으로 전체 투자금액을 나눕니다.
    merged_df['비중'] = merged_df['투자금액'] / merged_df['투자금액'].sum()

    # 그룹별 투자 비중 합산 (사용자의 최종 투자 스타일 벡터 U)
    # 'group_tag'는 정수형이므로 정수형으로 그룹핑합니다.
    user_style_raw = merged_df.groupby('group_tag')['비중'].sum()

    # K-Means는 0~7번 그룹이 모두 필요하므로, 없는 그룹은 0.0으로 채워줍니다.
    all_groups = np.arange(8)
    user_style_vector = user_style_raw.reindex(all_groups, fill_value=0.0).values

    # 정규화된 벡터 반환 (총합이 1.0이 되도록)
    vector_sum = user_style_vector.sum()
    if vector_sum == 0:
        return None, None  # 비정상 데이터 (모든 종목 매칭 실패)

    return user_style_vector / vector_sum, merged_df  # 벡터 정규화


# ----------------------------------------------------
# 3. 페르소나 매칭 및 일치율 계산 (Phase 3 구현)
# ----------------------------------------------------
def calculate_persona_match(user_vector):
    results = {}

    # 모든 페르소나와 비교합니다.
    for name, persona_style_dict in pd_data.ALL_PERSONAS.items():
        all_groups = np.arange(8)
        # 페르소나의 스타일 벡터 P (정규화된 100% 벡터)
        persona_vector = pd.Series(persona_style_dict).reindex(all_groups, fill_value=0.0).values

        # 1. 유클리디안 거리 (Distance) 계산
        distance = norm(user_vector - persona_vector)

        # 2. 거리를 유사도(Similarity)로 변환
        # 최대 불일치 거리는 순수형 페르소나(100% 한 그룹)끼리 비교 시 sqrt(1^2 + 1^2) = 1.414 입니다.
        max_distance = np.sqrt(2.0)

        # 일치율 = 100% - (정규화된 거리) * 100
        unmatched_ratio = distance / max_distance
        similarity = max(0, 100 - (unmatched_ratio * 100))

        results[name] = round(similarity, 2)

    return results


# ----------------------------------------------------
# 4. 실행 및 결과 출력
# ----------------------------------------------------
if __name__ == "__main__":
    user_vector, merged_details = analyze_user_style(user_df)

    if user_vector is not None:
        print("\n" + "=" * 40)
        print("           🚀 사용자 포트폴리오 분석 결과")
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

        # 일치율이 높은 순서대로 정렬
        sorted_results = sorted(match_results.items(), key=lambda item: item[1], reverse=True)

        for name, percent in sorted_results:
            print(f"- {name}: {percent:.2f}%")

        print("\n" + "=" * 40)