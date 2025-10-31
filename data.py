import requests
import pandas as pd
import time
import os
from dotenv import load_dotenv

# (사전 준비 1) .env 파일에서 API 키 불러오기
load_dotenv()

APP_KEY = os.getenv('APP_KEY')
APP_SECRET = os.getenv('APP_SECRET')
BASE_URL = 'https://openapi.koreainvestment.com:9443' # 실전투자 기준

# 최초 1회 토큰 발급 함수
def get_access_token():
    headers = {"content-type": "application/json"}
    body = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET
    }
    PATH = "/oauth2/tokenP"
    res = requests.post(f"{BASE_URL}{PATH}", headers=headers, json=body)
    access_token = res.json()["access_token"]
    return access_token


# -----------------------------------------------------------------
# (사전 준비 2) API 호출 함수 (재현님이 채워주세요)
# -----------------------------------------------------------------
# 6가지 재료를 가져올 API 호출 함수들 (예시입니다)

# 공통 헤더
HEADERS = {
    "authorization": f"Bearer {get_access_token()}",
    "appkey": APP_KEY,
    "appsecret": APP_SECRET,
    "tr_id": "YOUR_TR_ID",  # 각 API의 TR ID (예: FHKST01010100)
    "custtype": "P"  # 개인
}


# 1, 2, 3, 6번 재료 (시총, PER, PBR, 배당수익률)
def get_price_info(stock_code):
    # (재현님 숙제) '주식현재가 시세' API의 실제 엔드포인트와 TR_ID를 넣어주세요.
    PATH = '/uapi/domestic-stock/v1/quotations/inquire-price'  # 예시 URL
    HEADERS['tr_id'] = 'FHKST01010100'  # 예시 TR_ID

    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": stock_code
    }
    res = requests.get(f"{BASE_URL}{PATH}", headers=HEADERS, params=params)

    if res.status_code == 200:
        data = res.json()['output']
        # (재현님 숙제) JSON 응답에서 실제 '키(Key)' 이름을 찾아서 넣어주세요.
        return {
            '시가총액': float(data.get('hgrn_sum_amt', 0)),  # '시가총액'의 실제 키 이름
            'per': float(data.get('per', 0)),  # 'PER'의 실제 키 이름
            'pbr': float(data.get('pbr', 0)),  # 'PBR'의 실제 키 이름
            '배당수익률': float(data.get('dvdn_yld', 0))  # '배당수익률'의 실제 키 이름
        }
    return {}  # 실패 시 빈 딕셔너리


# 4번 재료 (ROE)
def get_roe_info(stock_code):
    # (재현님 숙제) '국내주식 수익성비율' API의 실제 엔드포인트와 TR_ID를 넣어주세요.
    PATH = '/uapi/domestic-stock/v1/finance/profitability-ratio'  # 예시 URL
    HEADERS['tr_id'] = 'YOUR_TR_ID_FOR_ROE'

    # ... (params 설정) ...

    # (API 호출 로직) ...
    # data = res.json()['output']

    # (재현님 숙제) JSON 응답에서 실제 '키(Key)' 이름을 찾아서 넣어주세요.
    # return {'roe': float(data.get('roe_val', 0))} # 예시
    pass  # 이 부분은 재현님이 직접 구현


# 5번 재료 (부채비율)
def get_debt_ratio(stock_code):
    # (재현님 숙제) '국내주식 안정성비율' API의 실제 엔드포인트와 TR_ID를 넣어주세요.
    PATH = '/uapi/domestic-stock/v1/finance/stability-ratio'  # 예시 URL
    HEADERS['tr_id'] = 'YOUR_TR_ID_FOR_DEBT'

    # ... (params 설정) ...

    # (API 호출 로직) ...
    # data = res.json()['output']

    # (재현님 숙제) JSON 응답에서 실제 '키(Key)' 이름을 찾아서 넣어주세요.
    # return {'부채비율': float(data.get('lblt_rate', 0))} # 예시
    pass  # 이 부분은 재현님이 직접 구현


# -----------------------------------------------------------------
# (실행) Day 1-2: 2,000개 종목 데이터 수집
# -----------------------------------------------------------------
print("Day 1-2: 2,000개 종목 데이터 수집을 시작합니다...")

# 1. (재현님 숙제) '종목정보파일' API를 통해 2,000개 종목 코드 리스트(stock_codes)를 가져옵니다.
# 우선 테스트를 위해 몇 개 종목만 하드코딩합니다.
stock_codes = ['005930', '000660', '035420', '005380']  # [삼성전자, SK하이닉스, NAVER, 현대차]

all_stock_data = []

for code in stock_codes:
    print(f"{code} 종목 데이터 수집 중...")
    try:
        price_data = get_price_info(code)
        # roe_data = get_roe_info(code) # (재현님 숙제) 주석 해제
        # debt_data = get_debt_ratio(code) # (재현님 숙제) 주석 해제

        # 6가지 재료를 하나로 합칩니다.
        final_data = {
            '종목코드': code,
            **price_data,
            # **roe_data,
            # **debt_data
        }
        all_stock_data.append(final_data)

    except Exception as e:
        print(f"{code} 처리 중 오류 발생: {e}")

    # (중요!) API는 초당 호출 횟수 제한(Rate Limit)이 있습니다.
    # 0.1초 ~ 0.5초 정도 쉬어줍니다. (문서 확인 필수)
    time.sleep(0.2)

# 2. 하나의 CSV 파일로 저장
df = pd.DataFrame(all_stock_data)
df.to_csv('stockit_ai_features_v1.csv', index=False, encoding='utf-8-sig')

print("\nDay 1-2: 데이터 수집 완료!")
print(df.head())