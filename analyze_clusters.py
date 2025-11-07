import pandas as pd

# --- 1. 파일 로드 ---
try:
    # 1-1. 최종 태그 결과 파일 로드 (단축코드, 한글명, group_tag)
    df_tags = pd.read_csv('app/data/stockit_ai_tags_final_v1.csv', encoding='utf-8')
    print(f"1. AI 태그 결과 로드 성공: {len(df_tags)}개 종목")

    # 1-2. 원본 피처 데이터 로드 (단축코드, 한글명, 6가지 지표 포함)
    # 이 파일은 01_preprocess.py의 입력 파일이었습니다.
    df_features_raw = pd.read_csv('app/data/stockit_ai_features_v1.csv', encoding='utf-8')
    print(f"2. 원본 피처 데이터 로드 성공: {len(df_features_raw)}개 종목")

except Exception as e:
    print(f"파일 로드 실패: {e}")
    exit()

# --- 2. 데이터 병합 (Merge) ---
# df_tags에 6가지 재무 지표를 추가하기 위해 '단축코드', '한글명'을 기준으로 병합합니다.
# df_tags에는 500개 종목만 있으므로, 최종적으로 500개만 남습니다.
df_analysis = pd.merge(df_tags, df_features_raw, on=['단축코드', '한글명'], how='left')

print(f"3. 데이터 병합 완료: 최종 분석 대상 {len(df_analysis)}개 종목")

# --- 3. 그룹별 평균 지표 계산 ---
feature_columns = ['시가총액', 'per', 'pbr', 'ROE', '부채비율', '배당수익률']
# 'group_tag'를 기준으로 6가지 핵심 재무 지표의 평균 계산
group_analysis = df_analysis.groupby('group_tag')[feature_columns].mean()

# 4. 결과를 소수점 둘째 자리까지 보기 좋게 출력
pd.options.display.float_format = '{:,.2f}'.format
print("\n--- 📊 그룹별 평균 재무 지표 (투자 스타일 분석 자료) ---")
print(group_analysis)