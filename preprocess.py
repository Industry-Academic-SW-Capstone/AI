import pandas as pd
from sklearn.preprocessing import StandardScaler
import numpy as np

# --- 1. 데이터 로드 ---
try:
    # v1 CSV 파일 로드 (utf-8)
    df_raw = pd.read_csv('stockit_ai_features_v1.csv', encoding='utf-8')
    print(f"로드 성공: 원본 데이터 {len(df_raw)}개")
except Exception as e:
    print(f"파일 로드 실패: {e}")
    exit()

# --- 2. 1차 정제 (0 이하 값 제거) ---
feature_columns = ['시가총액', 'per', 'pbr', 'ROE', '부채비율', '배당수익률']
df = df_raw.copy()
initial_count = len(df)

# 1차 필터링: 0 이하 값 (ETF, 적자기업 등) 제거
for col in feature_columns:
    df = df[df[col] > 0]

filtered_count = len(df)
print(f"--- 1차 정제 완료 (0 이하 값 제거) ---")
print(f"원본 {initial_count}개 -> {filtered_count}개 종목")  # (여기까지 937개)

# --- 2.5 (★추가됨★) 2차 정제 (극단치 제거) ---
# 1차 정제된 937개 중, 각 지표별 상/하위 5%의 극단적인 값을 추가로 제거합니다.
# (예: PER 5000배, 부채비율 8000% 등)
# 이것이 K-Means 계산 오류(overflow)를 일으키는 주범입니다.
print(f"--- 2차 정제 시작 (극단치 제거) ---")

# 6개 지표 각각에 대해 극단치(상/하위 5%)를 제거합니다.
for col in feature_columns:
    # 5% 백분위수 (하위 5% 값)
    q_low = df[col].quantile(0.05)
    # 95% 백분위수 (상위 5% 값)
    q_high = df[col].quantile(0.95)

    # 5% ~ 95% 사이의 "정상 범위" 값만 남김
    df = df[(df[col] >= q_low) & (df[col] <= q_high)]

    print(f"'{col}' 극단치(상/하위 5%) 제거 후 남은 종목: {len(df)}개")

print(f"--- 2차 정제(극단치 제거) 완료 ---")
print(f"1차 정제 {filtered_count}개 -> 최종 분석 {len(df)}개")

# (중요) 최종적으로 살아남은 종목들로 정보와 데이터를 분리
stock_info = df[['단축코드', '한글명']].reset_index(drop=True)
features_data = df[feature_columns]

# --- 3. 피처 엔지니어링 (스케일링: Scaling) ---
# 이제 '진짜' 데이터만 가지고 스케일링을 수행합니다.
scaler = StandardScaler()
features_scaled = scaler.fit_transform(features_data)

print("--- 피처 엔지니어링(Scaling) 완료 ---")
print("극단치가 제거된 '진짜' 데이터가 벡터로 변환되었습니다.")
print("스케일링된 데이터 (상위 5개):")
print(features_scaled[:5])

# --- 4. 전처리 결과 파일로 저장 ---
# AI가 학습할 숫자 벡터(Numpy 배열) 저장
np.save('features_scaled.npy', features_scaled)

# 숫자 벡터와 짝을 이룰 종목 정보(Pandas DataFrame) 저장
stock_info.to_csv('stock_info.csv', index=False, encoding='utf-8')

import joblib
joblib.dump(scaler, 'scaler.pkl')

print("3. scaler.pkl (AI 예측용 번역기) 파일이 생성되었습니다.")

print("--- 전처리 결과 저장 완료 ---")
print("1. features_scaled.npy (AI 학습용 벡터)")
print("2. stock_info.csv (종목 정보) 파일이 생성되었습니다.")