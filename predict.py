import pandas as pd
import numpy as np
import joblib

# ----------------------------------------------------
# 1. AI 모델 및 '번역기(Scaler)' 로드
# ----------------------------------------------------
try:
    model = joblib.load('kmeans_model.pkl')
    scaler = joblib.load('scaler.pkl')
    print("✅ AI 모델과 번역기(Scaler) 로드 성공.")
except FileNotFoundError:
    print("🚨 오류: 'kmeans_model.pkl' 또는 'scaler.pkl' 파일이 없습니다.")
    print("01_preprocess.py와 02_train_model.py를 먼저 실행해야 합니다.")
    exit()

# ----------------------------------------------------
# 2. 가상의 신규 주식 데이터 (삼성전자)
# ----------------------------------------------------
# (예시 데이터: 실제로는 API로 이 6개 값을 가져와야 합니다)
# 삼성전자의 실제 재무 지표 (예시 값)
new_stock_data = {
    '시가총액': [10000],  # 5000조 (실제 값과 다름, 테스트용 극단치)
    'per': [15.0],
    'pbr': [1.8],
    'ROE': [12.0],
    '부채비율': [40.0],
    '배당수익률': [10000]
}
new_df = pd.DataFrame(new_stock_data)


# ----------------------------------------------------
# 3. 신규 데이터 '예측(Prediction)' 실행
# ----------------------------------------------------
def predict_style(stock_df):
    # 1. 훈련 때 사용한 '번역기'로 신규 데이터를 번역 (스케일링)
    # (주의: .fit_transform()이 아닌 .transform()을 사용해야 함)
    scaled_data = scaler.transform(stock_df)

    # 2. AI의 뇌(모델)에게 예측 명령
    predicted_group = model.predict(scaled_data)

    return predicted_group[0]  # [5] -> 5 (숫자 반환)


# ----------------------------------------------------
# 4. 실행 및 결과 출력
# ----------------------------------------------------
if __name__ == "__main__":
    # 태그 매핑 (결과 해석용)
    tag_names = ['[안정형 일반주]', '[고효율 우량주]', '[초고배당 가치주]', '[고위험 저평가주]',
                 '[고성장 기대주]', '[초대형 우량주]', '[초저평가 가치주]', '[고가치 성장주]']

    print(f"\n분석 대상: 삼성전자 (가상 데이터)")

    # AI 예측 실행
    group_num = predict_style(new_df)

    print("\n--- 🚀 AI 예측 결과 ---")
    print(f"AI가 예측한 그룹 번호: {group_num}")
    print(f"매칭된 최종 스타일 태그: {tag_names[group_num]}")