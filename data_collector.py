import requests
import pandas as pd
import time
import os
from dotenv import load_dotenv
import urllib.request
import ssl
import zipfile
from datetime import datetime, timedelta

# -----------------------------------------------------------------
# (사전 준비 1) .env 파일에서 API 키 불러오기
# -----------------------------------------------------------------
load_dotenv()
APP_KEY = os.getenv('APP_KEY')
APP_SECRET = os.getenv('APP_SECRET')

if not APP_KEY or not APP_SECRET:
    print("오류: .env 파일에 APP_KEY와 APP_SECRET를 설정해야 합니다.")
    # .env 파일이 없으면 스크립트 종료
    exit()

BASE_URL = 'https://openapi.koreainvestment.com:9443'
BASE_DIR = os.getcwd()  # 스크립트 실행 위치


# -----------------------------------------------------------------
# (사전 준비 2) 토큰 발급 및 공통 헤더
# -----------------------------------------------------------------
def get_access_token():
    """최초 1회 토큰 발급 함수"""
    try:
        headers = {"content-type": "application/json"}
        body = {
            "grant_type": "client_credentials",
            "appkey": APP_KEY,
            "appsecret": APP_SECRET
        }
        PATH = "/oauth2/tokenP"
        # 토큰 발급은 timeout을 5초로 짧게 설정
        res = requests.post(f"{BASE_URL}{PATH}", headers=headers, json=body, timeout=5)
        res.raise_for_status()  # 오류 발생 시 예외

        # API 키 유효성 검사
        if "access_token" not in res.json():
            print(f"API 키 인증 실패: {res.json()}")
            return None

        access_token = res.json()["access_token"]
        print("접근 토큰 발급 성공")
        return access_token
    except Exception as e:
        print(f"토큰 발급 오류: {e}")
        return None


ACCESS_TOKEN = get_access_token()

# API 호출을 위한 공통 헤더
HEADERS = {
    "authorization": f"Bearer {ACCESS_TOKEN}",
    "appkey": APP_KEY,
    "appsecret": APP_SECRET,
    "tr_id": "",  # 각 함수에서 개별 설정
    "custtype": "P"  # 개인
}


# -----------------------------------------------------------------
# (사전 준비 3) 마스터 파일 다운로드/정제 함수 (Git Logic)
# - (V4 수정) '종목코드'와 '한글명' 리스트만 가져오는 용도로 축소
# -----------------------------------------------------------------

def download_master_file(url, zip_path, mst_name, verbose=False):
    """코스피/코스닥 마스터 파일(.mst) 공통 다운로드 함수"""
    if (verbose): print(f"  {mst_name} 마스터 파일 다운로드 중...")
    ssl._create_default_https_context = ssl._create_unverified_context

    # OS 호환성을 위해 os.path.join 사용
    urllib.request.urlretrieve(url, zip_path)

    with zipfile.ZipFile(zip_path, 'r') as zip_f:
        zip_f.extractall(BASE_DIR)

    if os.path.exists(zip_path):
        os.remove(zip_path)
    if (verbose): print(f"  {mst_name} 마스터 파일 다운로드 완료.")


def get_stock_code_list():
    """코스피와 코스닥 마스터 파일을 다운로드하고 정제하여 종목코드 리스트 반환"""

    all_dfs = []

    # 1. KOSPI
    try:
        kospi_zip_path = os.path.join(BASE_DIR, "kospi_code.zip")
        kospi_mst_path = os.path.join(BASE_DIR, "kospi_code.mst")
        download_master_file("https://new.real.download.dws.co.kr/common/master/kospi_code.mst.zip", kospi_zip_path,
                             "KOSPI", verbose=True)

        # 코스피 마스터 파일 정제 (첫 3개 컬럼만)
        kospi_df = pd.read_fwf(kospi_mst_path, widths=[9, 12, 200], header=None, encoding="cp949", usecols=[0, 2])
        kospi_df.columns = ['단축코드', '한글명']
        kospi_df['단축코드'] = kospi_df['단축코드'].str.replace('A', '')
        all_dfs.append(kospi_df)

        if os.path.exists(kospi_mst_path):
            os.remove(kospi_mst_path)
    except Exception as e:
        print(f"[오류] KOSPI 마스터 파일 처리 실패: {e}")

    # 2. KOSDAQ
    try:
        kosdaq_zip_path = os.path.join(BASE_DIR, "kosdaq_code.zip")
        kosdaq_mst_path = os.path.join(BASE_DIR, "kosdaq_code.mst")
        download_master_file("https://new.real.download.dws.co.kr/common/master/kosdaq_code.mst.zip", kosdaq_zip_path,
                             "KOSDAQ", verbose=True)

        # 코스닥 마스터 파일 정제 (첫 3개 컬럼만)
        kosdaq_df = pd.read_fwf(kosdaq_mst_path, widths=[9, 12, 200], header=None, encoding="cp949", usecols=[0, 2])
        kosdaq_df.columns = ['단축코드', '한글명']
        kosdaq_df['단축코드'] = kosdaq_df['단축코드'].str.replace('A', '')
        all_dfs.append(kosdaq_df)

        if os.path.exists(kosdaq_mst_path):
            os.remove(kosdaq_mst_path)
    except Exception as e:
        print(f"[오류] KOSDAQ 마스터 파일 처리 실패: {e}")

    # 3. KOSPI + KOSDAQ
    if not all_dfs:
        print("[오류] KOSPI와 KOSDAQ 마스터 파일을 모두 불러오지 못했습니다.")
        return pd.DataFrame(columns=['단축코드', '한글명'])

    df_master = pd.concat(all_dfs, ignore_index=True)

    # ETF/ETN/SPAC 등 제외 (예시: '005930' 형태의 6자리 숫자 코드만 필터링)
    df_master = df_master[df_master['단축코드'].str.match(r'^\d{6}$')].reset_index(drop=True)
    df_master['한글명'] = df_master['한글명'].str.strip()  # 공백 제거

    return df_master


# -----------------------------------------------------------------
# (사전 준비 4) 6가지 재료 API 호출 함수 (V5.1 - Final Fixed)
# -----------------------------------------------------------------

# [재료 1, 2, 3] PER, PBR, 시가총액
def get_price_info(stock_code):
    """ '주식현재가 시세' API 호출 (PER, PBR, 시가총액) """
    PATH = '/uapi/domestic-stock/v1/quotations/inquire-price'
    HEADERS['tr_id'] = 'FHKST01010100'  # (확인 완료)

    params = {
        "FID_COND_MRKT_DIV_CODE": "J",  # J: 주식
        "FID_INPUT_ISCD": stock_code
    }

    try:
        # [V5.1 수정] timeout을 10초로 설정
        res = requests.get(f"{BASE_URL}{PATH}", headers=HEADERS, params=params, timeout=10)
        res.raise_for_status()

        json_data = res.json()
        if json_data['rt_cd'] == '0':
            data = json_data['output']
            # (확인 완료) hts_avls: HTS 시가총액
            return {
                'per': float(data.get('per', 0.0)),
                'pbr': float(data.get('pbr', 0.0)),
                '시가총액': float(data.get('hts_avls', 0.0))
            }
        else:
            # API 자체에서 오류 응답 (예: 존재하지 않는 종목)
            print(f"  [API 오류] get_price_info({stock_code}): {json_data.get('msg1', 'Unknown error')}")

    except Exception as e:
        # 네트워크 오류 (Timeout 등)
        print(f"  [네트워크 오류] get_price_info({stock_code}): {e}")

    return {'per': 0.0, 'pbr': 0.0, '시가총액': 0.0}


# [재료 4, 5] ROE, 부채비율
def get_finance_ratios(stock_code):
    """ '국내주식 재무비율' API 호출 (ROE, 부채비율 동시 확보) """
    PATH = '/uapi/domestic-stock/v1/finance/financial-ratio'
    HEADERS['tr_id'] = 'FHKST66430300'  # (확인 완료)

    # (확인 완료)
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",  # J: 주식시장
        "fid_input_iscd": stock_code,  # 종목 코드
        "FID_DIV_CLS_CODE": "0"  # 0: 년 (연간 재무제표)
    }

    try:
        # [V5.1 수정] timeout을 10초로 설정
        res = requests.get(f"{BASE_URL}{PATH}", headers=HEADERS, params=params, timeout=10)
        res.raise_for_status()

        json_data = res.json()
        if json_data['rt_cd'] == '0':
            data = json_data['output']

            # (확인 완료) Output은 리스트, 키 이름 'roe_val', 'lblt_rate' 확인
            if data and isinstance(data, list):
                # 가장 최근의 연간 재무제표(첫 번째 항목)에서 값을 가져옴
                return {
                    'ROE': float(data[0].get('roe_val', 0.0)),
                    '부채비율': float(data[0].get('lblt_rate', 0.0))
                }
        else:
            print(f"  [API 오류] get_finance_ratios({stock_code}): {json_data.get('msg1', 'Unknown error')}")

    except Exception as e:
        print(f"  [네트워크 오류] get_finance_ratios({stock_code}): {e}")

    return {'ROE': 0.0, '부채비율': 0.0}


# [재료 6] 배당수익률
def get_dividend_rate(stock_code):
    """ '예탁원정보(배당일정)' API 호출 (배당수익률 확보) """
    PATH = '/uapi/domestic-stock/v1/ksdinfo/dividend'
    HEADERS['tr_id'] = 'HHKDB669102C0'  # (확인 완료)

    # 최근 1년치 배당을 조회하기 위해 날짜 설정
    today = datetime.now()
    one_year_ago = today - timedelta(days=365)

    params = {
        "CTS": "",  # 연속 조회용 (공백)
        "GB1": "0",  # 0: 전체 (0:배당전체, 1:결산배당, 2:중간배당)
        "F_DT": one_year_ago.strftime('%Y%m%d'),  # 조회 시작일 (1년 전)
        "T_DT": today.strftime('%Y%m%d'),  # 조회 종료일 (오늘)
        "SHT_CD": stock_code,  # (확인 완료) 개별 종목 코드
        "HIGH_GB": ""  # 공백
    }

    try:
        # [V5.1 수정] timeout을 10초로 설정
        res = requests.get(f"{BASE_URL}{PATH}", headers=HEADERS, params=params, timeout=10)
        res.raise_for_status()

        json_data = res.json()
        if json_data['rt_cd'] == '0':
            data = json_data['output1']  # (주의) 'output1' 입니다

            # (확인 완료) Output이 리스트이고, 키 이름 'divi_rate' 확인
            if data and isinstance(data, list):
                # 가장 최근의 배당 정보(첫 번째 항목)에서 '현금배당률'을 가져옴
                return {
                    '배당수익률': float(data[0].get('divi_rate', 0.0))
                }
        else:
            print(f"  [API 오류] get_dividend_rate({stock_code}): {json_data.get('msg1', 'Unknown error')}")

    except Exception as e:
        print(f"  [네트워크 오류] get_dividend_rate({stock_code}): {e}")

    return {'배당수익률': 0.0}


# -----------------------------------------------------------------
# (실행) Day 1-2: 6가지 재료 수집 (V5.1 - 최종)
# -----------------------------------------------------------------
def collect_all_data():
    """스크립트의 메인 실행 함수"""

    if not ACCESS_TOKEN:
        print("토큰 발급 실패. 스크립트를 종료합니다.")
        return

    # [ 1. 마스터 파일 다운로드 및 정제 ]
    print("Day 1-2 (Step 1/3): 마스터 파일 다운로드 및 정제를 시작합니다...")
    try:
        df_master = get_stock_code_list()
    except Exception as e:
        print(f"[오류] 마스터 파일 처리 실패: {e}")
        return

    if df_master.empty:
        print("[오류] 조회할 종목 코드를 확보하지 못했습니다. 스크립트를 종료합니다.")
        return

    stock_codes = df_master['단축코드'].tolist()
    print(f"총 {len(stock_codes)}개 종목 코드를 확보했습니다.")
    print("--- 마스터 파일 (종목 리스트) 데이터 (상위 5개) ---")
    print(df_master.head())

    # [ 2. API 호출로 6가지 재료 수집 ]
    print(f"\nDay 1-2 (Step 2/3): API 호출로 6가지 재료({len(stock_codes)}개 종목) 수집을 시작합니다...")
    api_data_list = []
    count = 0

    # (테스트용) 10개 종목만 먼저 테스트
    # stock_codes_test = stock_codes[:10]
    # print(f"*** 테스트 모드: {len(stock_codes_test)}개 종목만 수집 ***")

    for code in stock_codes:  # 테스트 시 'stock_codes_test'로 변경
        count += 1

        try:
            print(f"[{count}/{len(stock_codes)}] {code} 종목 API 데이터 수집 중...", end='', flush=True)

            # [V5.1 수정] API 호출 사이에 1초씩 휴식(sleep)을 주어 서버 제한(throttling) 방지

            # [재료 1, 2, 3] PER, PBR, 시가총액 (10/sec 제한 - 비교적 여유)
            price_data = get_price_info(code)

            # (중요!) 재무 API는 1초에 1건 제한
            time.sleep(1.0)  # 1초 대기

            # [재료 4, 5] ROE, 부채비율
            finance_data = get_finance_ratios(code)

            # (중요!) 재무 API는 1초에 1건 제한
            time.sleep(1.0)  # 1초 대기

            # [재료 6] 배당수익률
            dividend_data = get_dividend_rate(code)

            # 6가지 재료를 하나로 합침
            final_data = {
                '단축코드': code,
                **price_data,
                **finance_data,
                **dividend_data
            }
            api_data_list.append(final_data)
            print(" (완료)")

        except KeyboardInterrupt:
            print("\n사용자에 의해 수동으로 중지되었습니다. 현재까지 수집된 데이터로 저장합니다.")
            break  # 루프 중단
        except Exception as e:
            print(f"  [심각한 오류] {code} 처리 중 알 수 없는 오류: {e}")
            continue  # 다음 종목으로 넘어감

    # [ 3. 최종 데이터 합치기 및 저장 ]
    print("\nDay 1-2 (Step 3/3): API 호출 데이터와 마스터 데이터를 합칩니다...")
    df_api_data = pd.DataFrame(api_data_list)

    if df_api_data.empty:
        print("[오류] API로부터 수집된 데이터가 없습니다. CSV 파일을 생성하지 않습니다.")
        return

    print("--- API 호출 (6가지 재료) 데이터 (상위 5개) ---")
    print(df_api_data.head())

    # 마스터 파일(한글명)과 API 데이터(6가지 재료)를 '단축코드' 기준으로 합치기
    final_df = pd.merge(df_master, df_api_data, on='단축코드', how='left')

    # [최종 컬럼 정리] (6가지 재료 + 식별자)
    final_feature_columns = [
        '단축코드',
        '한글명',
        '시가총액',
        'per',
        'pbr',
        'ROE',
        '부채비율',
        '배당수익률'  # '플랜 B'에서 '플랜 A'로 복귀!
    ]

    # 혹시 모를 누락 컬럼 대비
    final_feature_df = final_df.reindex(columns=final_feature_columns)
    # NaN (Not a Number) 값을 0.0으로 채우기 (AI 학습을 위해)
    final_feature_df = final_feature_df.fillna(0.0)

    # 4. CSV 파일로 저장
    output_filename = 'app/data/stockit_ai_features_v1.csv'
    final_feature_df.to_csv(output_filename, index=False, encoding='utf-8-sig')

    print(f"\nDay 1-2: 모든 재료 수집 및 정제 완료! '{output_filename}'에 저장됨.")
    print("--- 최종 결과물 (상위 5개) ---")
    print(final_feature_df.head())


# -----------------------------------------------------------------
# (메인 실행)
# -----------------------------------------------------------------
if __name__ == "__main__":
    if ACCESS_TOKEN:
        collect_all_data()
    else:
        print("토큰 발급에 실패하여 프로그램을 종료합니다.")

