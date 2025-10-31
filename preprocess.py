import pandas as pd
from sklearn.preprocessing import StandardScaler
import numpy as np

# --- 1. 데이터 로드 ---
try:
    # v1 CSV 파일 로드 (인코딩 문제 방지)
    df_raw = pd.read_csv('stockit_ai_features_v1.csv', encoding='utf-8')
    print(f"로드 성공: 원본 데이터 {len(df_raw)}개")
except Exception as e:
    print(f"파일 로드 실패: {e}")
    exit()

# --- 2. 데이터 전처리 (정제: Filtering) ---
feature_columns = ['시가총액', 'per', 'pbr', 'ROE', '부채비율', '배당수익률']
df = df_raw.copy()
initial_count = len(df)

for col in feature_columns:
    df = df[df[col] > 0]

print(f"--- 데이터 정제(Filtering) 완료 ---")
print(f"원본 {initial_count}개 종목")
print(f"제외된 종목 (ETF, 스팩, 적자기업, 데이터오류 등): {initial_count - len(df)}개")
print(f"최종 분석 대상 종목: {len(df)}개")

stock_info = df[['단축코드', '한글명']].reset_index(drop=True)
features_data = df[feature_columns]

# --- 3. 피처 엔지니어링 (스케일링: Scaling) ---
scaler = StandardScaler()
features_scaled = scaler.fit_transform(features_data)

print("--- 피처 엔지니어링(Scaling) 완료 ---")
print("스케일링된 데이터 (상위 5개):")
print(features_scaled[:5])

# --- 4. (★추가됨★) 전처리 결과 파일로 저장 ---
# AI가 학습할 숫자 벡터(Numpy 배열) 저장
np.save('features_scaled.npy', features_scaled)

# 숫자 벡터와 짝을 이룰 종목 정보(Pandas DataFrame) 저장
stock_info.to_csv('stock_info.csv', index=False, encoding='utf-8')

print("--- 전처리 결과 저장 완료 ---")
print("1. features_scaled.npy (AI 학습용 벡터)")
print("2. stock_info.csv (종목 정보) 파일이 생성되었습니다.")