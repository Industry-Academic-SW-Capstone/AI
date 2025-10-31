import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
import joblib # 모델 저장을 위해 joblib 사용

# --- 1. (★추가됨★) 전처리된 데이터 로드 ---
try:
    # 01_preprocess.py가 저장한 파일들을 불러옵니다.
    features_scaled = np.load('features_scaled.npy')
    stock_info = pd.read_csv('stock_info.csv', encoding='utf-8')
    print(f"전처리된 데이터 로드 성공: {len(stock_info)}개 종목")
except Exception as e:
    print(f"파일 로드 실패: {e}")
    print("오류: 01_preprocess.py를 먼저 실행하여 features_scaled.npy와 stock_info.csv 파일을 생성해야 합니다.")
    exit()

# --- 2. K-Means 모델 학습 (Day 3-4) ---
# (중요) AI에게 "몇 개의 그룹으로 나눌지(K)"를 알려줘야 합니다.
# 6가지 재료로 [우량주, 가치주, 성장주, 배당주...] 등
# 8개 정도의 그룹으로 나눠보겠습니다. (이 숫자는 나중에 변경 가능)
K = 8

print(f"--- K-Means 모델 학습 시작 (K={K}) ---")

# n_init='auto' : AI가 최적의 중심점을 찾도록 자동으로 여러 번 시도합니다.
# random_state=42 : 실행할 때마다 결과가 똑같이 나오도록 '씨앗값'을 고정합니다. (디버깅에 필수)
model = KMeans(n_clusters=K, n_init='auto', random_state=42)

# AI 학습 실행! (스케일링된 데이터를 입력)
model.fit(features_scaled)

print("--- 모델 학습 완료 ---")

# --- 3. 학습 결과 저장 ---
# 1. 학습된 AI 모델 자체를 저장 (나중에 웹서버에서 불러다 쓸 수 있음)
joblib.dump(model, 'kmeans_model.pkl')
print("1. kmeans_model.pkl (학습된 AI 모델) 저장 완료")

# 2. 각 종목이 몇 번 그룹에 속하는지 '태그'를 붙입니다.
# model.labels_ 는 [0, 3, 1, 7, 2, ... 5] 처럼 각 종목의 그룹 번호를 담고 있습니다.
stock_info['group_tag'] = model.labels_

# 3. 최종 결과 CSV 파일로 저장
# (이것이 1단계의 최종 산출물입니다)
final_output_file = 'stockit_ai_tags_final_v1.csv'
stock_info.to_csv(final_output_file, index=False, encoding='utf-8')

print(f"2. {final_output_file} (종목별 태그 결과) 저장 완료")
print("\n--- 그룹별 종목 개수 ---")
print(stock_info['group_tag'].value_counts().sort_index())