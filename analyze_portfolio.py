import pandas as pd
import numpy as np
import persona_definitions as pd_data  # 방금 만든 페르소나 정의 파일 로드

# 코사인 유사도 대신, 직관적인 '유클리디안 거리'를 사용하여 유사도를 측정합니다.
from numpy.linalg import norm

# ----------------------------------------------------
# 1. 가상의 사용자 포트폴리오 (더미 데이터) 정의
# ----------------------------------------------------
# 시뮬레이션: 사용자가 이 종목들을 이 비중만큼 샀다고 가정합니다.
# NOTE: 실제 앱에서는 API를 통해 이 데이터를 받게 됩니다.
user_portfolio_data = {
    '단축코드': ['005930', '005490', '000020', '005380', '006400'],  # 삼성전자, POSCO홀딩스, 동화약품, 현대차, 삼성바이오
    '투자금액': [1000000, 500000, 200000, 100000, 200000]  # 투자금액 (비중 계산에 사용)
}
user_df = pd.DataFrame(user_portfolio_data)


# ----------------------------------------------------
# 2. 사용자 스타일 태그 비중 계산 (Phase 2 구현)
# ----------------------------------------------------
def analyze_user_style(user_portfolio_df):
    # AI 태그 데이터베이스 로드
    try:
        df_tags = pd.read_csv('stockit_final_tagged_data.csv', encoding='utf-8')
    except FileNotFoundError:
        print("오류: stockit_final_tagged_data.csv 파일을 찾을 수 없습니다. 04_apply_final_tags.py를 먼저 실행하세요.")
        return None

    # 사용자 포트폴리오와 AI 태그 정보를 단축코드를 기준으로 병합
    merged_df = pd.merge(user_portfolio_df, df_tags, on='단축코드', how='left')

    # 투자금액으로 비중 계산
    merged_df['비중'] = merged_df['투자금액'] / merged_df['투자금액'].sum()

    # 그룹별 투자 비중 합산 (사용자의 최종 투자 스타일 벡터 U)
    # Series로 반환되어 group_tag: 비중 의 형태를 가집니다.
    user_style_raw = merged_df.groupby('group_tag')['비중'].sum()

    # K-Means는 0~7번 그룹이 모두 필요하므로, 없는 그룹은 0으로 채워줍니다.
    all_groups = np.arange(8)
    user_style_vector = user_style_raw.reindex(all_groups, fill_value=0.0).values

    return user_style_vector, merged_df


# ----------------------------------------------------
# 3. 페르소나 매칭 및 일치율 계산 (Phase 3 구현)
# ----------------------------------------------------
def calculate_persona_match(user_vector):
    results = {}

    # 모든 페르소나와 비교합니다.
    for name, persona_style_dict in pd_data.ALL_PERSONAS.items():
        # 페르소나의 스타일 벡터 P (없는 그룹은 0으로 채움)
        all_groups = np.arange(8)
        persona_vector = pd.Series(persona_style_dict).reindex(all_groups, fill_value=0.0).values

        # 1. 유클리디안 거리 (Distance) 계산
        # D = sqrt(sum((U_i - P_i)^2))
        distance = norm(user_vector - persona_vector)

        # 2. 거리를 유사도(Similarity)로 변환
        # 최대 거리는 sqrt(1^2 + ... + 1^2) = sqrt(8) = 약 2.828 입니다.
        # 정규화된 거리: distance / sqrt(2) (순수형 페르소나 비교 시 최대 거리는 sqrt(2)가 됨)

        # 최대 불일치 거리는 순수형 페르소나(100% 한 그룹)끼리 비교 시 sqrt(1^2 + 1^2) = 1.414 입니다.
        max_distance = np.sqrt(2.0)

        # 일치율 = 100% - (정규화된 거리) * 100
        unmatched_ratio = distance / max_distance
        similarity = max(0, 100 - (unmatched_ratio * 100))  # 0% 이하로 가지 않게 처리

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
        # user_vector의 값을 최종 태그 이름으로 변환하여 출력 (가독성 향상)
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