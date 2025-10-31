import requests
import pandas as pd
import time
import os
from dotenv import load_dotenv
import urllib.request
import ssl
import zipfile

# -----------------------------------------------------------------
# (사전 준비 1) .env 파일에서 API 키 불러오기
# -----------------------------------------------------------------
load_dotenv()
APP_KEY = os.getenv('APP_KEY')
APP_SECRET = os.getenv('APP_SECRET')
BASE_URL = 'https://openapi.koreainvestment.com:9443'
BASE_DIR = os.getcwd()  # 스크립트 실행 위치


# -----------------------------------------------------------------
# (사전 준비 2) 토큰 발급 및 공통 헤더
# -----------------------------------------------------------------
def get_access_token():
    """최초 1회 토큰 발급 함수"""
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


# API 호출을 위한 공통 헤더
HEADERS = {
    "authorization": f"Bearer {get_access_token()}",
    "appkey": APP_KEY,
    "appsecret": APP_SECRET,
    "tr_id": "",  # 각 함수에서 개별 설정
    "custtype": "P"
}


# -----------------------------------------------------------------
# (사전 준비 3) 마스터 파일 다운로드/정제 함수 (Git Llogic)
# -----------------------------------------------------------------

# [ 1. 코스피 마스터 파일 ]
def kospi_master_download(base_dir, verbose=False):
    """코스피 마스터 파일(.mst) 다운로드"""
    if (verbose): print("코스피 마스터 파일 다운로드 중...")
    ssl._create_default_https_context = ssl._create_unverified_context

    zip_path = os.path.join(base_dir, "kospi_code.zip")
    urllib.request.urlretrieve("https://new.real.download.dws.co.kr/common/master/kospi_code.mst.zip", zip_path)

    with zipfile.ZipFile(zip_path) as kospi_zip:
        kospi_zip.extractall(base_dir)

    if os.path.exists(zip_path):
        os.remove(zip_path)
    if (verbose): print("코스피 마스터 파일 다운로드 완료.")


def get_kospi_master_dataframe(base_dir):
    """다운로드한 코스피 마스터 파일을 DataFrame으로 정제"""
    file_name = os.path.join(base_dir, "kospi_code.mst")
    tmp_fil1 = os.path.join(base_dir, "kospi_code_part1.tmp")
    tmp_fil2 = os.path.join(base_dir, "kospi_code_part2.tmp")

    # (한투 Github 로직) .mst 파일을 2개의 임시 파일로 분리
    wf1 = open(tmp_fil1, mode="w", encoding="cp949")
    wf2 = open(tmp_fil2, mode="w", encoding="cp949")

    with open(file_name, mode="r", encoding="cp949") as f:
        for row in f:
            rf1 = row[0:len(row) - 228]
            rf1_1 = rf1[0:9].rstrip()
            rf1_2 = rf1[9:21].rstrip()
            rf1_3 = rf1[21:].strip()
            wf1.write(rf1_1 + ',' + rf1_2 + ',' + rf1_3 + '\n')
            rf2 = row[-228:]
            wf2.write(rf2)
    wf1.close()
    wf2.close()

    # (한투 Github 로직) 2개 파일을 각각 DataFrame으로 읽기
    part1_columns = ['단축코드', '표준코드', '한글명']
    df1 = pd.read_csv(tmp_fil1, header=None, names=part1_columns, encoding='cp949')

    field_specs = [2, 1, 4, 4, 4, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 9, 5, 5,
                   1, 1, 1, 2, 1, 1, 1, 2, 2, 2, 3, 1, 3, 12, 12, 8, 15, 21, 2, 7, 1, 1, 1, 1, 9, 9, 9, 5, 9, 8, 9, 3,
                   1, 1, 1]
    part2_columns = ['그룹코드', '시가총액규모', '지수업종대분류', '지수업종중분류', '지수업종소분류', '제조업', '저유동성', '지배구조지수종목', 'KOSPI200섹터업종',
                     'KOSPI100', 'KOSPI50', 'KRX', 'ETP', 'ELW발행', 'KRX100', 'KRX자동차', 'KRX반도체', 'KRX바이오', 'KRX은행',
                     'SPAC', 'KRX에너지화학', 'KRX철강', '단기과열', 'KRX미디어통신', 'KRX건설', 'Non1', 'KRX증권', 'KRX선박', 'KRX섹터_보험',
                     'KRX섹터_운송', 'SRI', '기준가', '매매수량단위', '시간외수량단위', '거래정지', '정리매매', '관리종목', '시장경고', '경고예고', '불성실공시',
                     '우회상장', '락구분', '액면변경', '증자구분', '증거금비율', '신용가능', '신용기간', '전일거래량', '액면가', '상장일자', '상장주수', '자본금',
                     '결산월', '공모가', '우선주', '공매도과열', '이상급등', 'KRX300', 'KOSPI', '매출액', '영업이익', '경상이익', '당기순이익', 'ROE',
                     '기준년월', '시가총액', '그룹사코드', '회사신용한도초과', '담보대출가능', '대주가능']
    df2 = pd.read_fwf(tmp_fil2, widths=field_specs, names=part2_columns, encoding='cp949')

    # (한투 Github 로직) 두 DataFrame을 합치기
    df = pd.merge(df1, df2, how='outer', left_index=True, right_index=True)

    # 임시 파일 삭제
    os.remove(tmp_fil1)
    os.remove(tmp_fil2)
    os.remove(file_name)

    # [중요] 6자리 단축코드로 통일 (예: 005930)
    df['단축코드'] = df['단축코드'].str.replace('A', '')

    # [중요] 우리가 필요한 재료만 선택
    return df[['단축코드', '한글명', 'ROE', '시가총액']]


# [ 2. 코스닥 마스터 파일 ]
def kosdaq_master_download(base_dir, verbose=False):
    """코스닥 마스터 파일(.mst) 다운로드"""
    if (verbose): print("코스닥 마스터 파일 다운로드 중...")
    ssl._create_default_https_context = ssl._create_unverified_context
    zip_path = os.path.join(base_dir, "kosdaq_code.zip")
    urllib.request.urlretrieve("https://new.real.download.dws.co.kr/common/master/kosdaq_code.mst.zip", zip_path)

    with zipfile.ZipFile(zip_path) as kosdaq_zip:
        kosdaq_zip.extractall(base_dir)

    kosdaq_zip.close()

    if os.path.exists(zip_path):
        os.remove(zip_path)
    if (verbose): print("코스닥 마스터 파일 다운로드 완료.")


def get_kosdaq_master_dataframe(base_dir):
    """다운로드한 코스닥 마스터 파일을 DataFrame으로 정제"""
    file_name = os.path.join(base_dir, "kosdaq_code.mst")
    tmp_fil1 = os.path.join(base_dir, "kosdaq_code_part1.tmp")
    tmp_fil2 = os.path.join(base_dir, "kosdaq_code_part2.tmp")

    wf1 = open(tmp_fil1, mode="w", encoding="cp949")
    wf2 = open(tmp_fil2, mode="w", encoding="cp949")

    with open(file_name, mode="r", encoding="cp949") as f:
        for row in f:
            rf1 = row[0:len(row) - 222]
            rf1_1 = rf1[0:9].rstrip()
            rf1_2 = rf1[9:21].rstrip()
            rf1_3 = rf1[21:].strip()
            wf1.write(rf1_1 + ',' + rf1_2 + ',' + rf1_3 + '\n')
            rf2 = row[-222:]
            wf2.write(rf2)
    wf1.close()
    wf2.close()

    part1_columns = ['단축코드', '표준코드', '한글종목명']
    df1 = pd.read_csv(tmp_fil1, header=None, names=part1_columns, encoding='cp949')

    field_specs = [2, 1, 4, 4, 4, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 9, 5, 5, 1, 1, 1, 2,
                   1, 1, 1, 2, 2, 2, 3, 1, 3, 12, 12, 8, 15, 21, 2, 7, 1, 1, 1, 1, 9, 9, 9, 5, 9, 8, 9, 3, 1, 1, 1]
    part2_columns = ['증권그룹구분코드', '시가총액 규모 구분 코드 유가', '지수업종 대분류 코드', '지수 업종 중분류 코드', '지수업종 소분류 코드', '벤처기업 여부 (Y/N)',
                     '저유동성종목 여부', 'KRX 종목 여부', 'ETP 상품구분코드', 'KRX100 종목 여부 (Y/N)', 'KRX 자동차 여부', 'KRX 반도체 여부',
                     'KRX 바이오 여부', 'KRX 은행 여부', '기업인수목적회사여부', 'KRX 에너지 화학 여부', 'KRX 철강 여부', '단기과열종목구분코드',
                     'KRX 미디어 통신 여부', 'KRX 건설 여부', '(코스닥)투자주의환기종목여부', 'KRX 증권 구분', 'KRX 선박 구분', 'KRX섹터지수 보험여부',
                     'KRX섹터지수 운송여부', 'KOSDAQ150지수여부 (Y,N)', '주식 기준가', '정규 시장 매매 수량 단위', '시간외 시장 매매 수량 단위', '거래정지 여부',
                     '정리매매 여부', '관리 종목 여부', '시장 경고 구분 코드', '시장 경고위험 예고 여부', '불성실 공시 여부', '우회 상장 여부', '락구분 코드',
                     '액면가 변경 구분 코드', '증자 구분 코드', '증거금 비율', '신용주문 가능 여부', '신용기간', '전일 거래량', '주식 액면가', '주식 상장 일자',
                     '상장 주수(천)', '자본금', '결산 월', '공모 가격', '우선주 구분 코드', '공매도과열종목여부', '이상급등종목여부', 'KRX300 종목 여부 (Y/N)',
                     '매출액', '영업이익', '경상이익', '단기순이익', 'ROE(자기자본이익률)', '기준년월', '전일기준 시가총액 (억)', '그룹사 코드', '회사신용한도초과여부',
                     '담보대출가능여부', '대주가능여부']
    df2 = pd.read_fwf(tmp_fil2, widths=field_specs, names=part2_columns, encoding='cp949')

    df = pd.merge(df1, df2, how='outer', left_index=True, right_index=True)

    os.remove(tmp_fil1)
    os.remove(tmp_fil2)
    os.remove(file_name)

    # [중요] 6자리 단축코드로 통일 (예: 005930)
    df['단축코드'] = df['단축코드'].str.replace('A', '')

    # [중요] 우리가 필요한 재료만 선택 (Kospi와 컬럼명 통일)
    df = df.rename(columns={
        '한글종목명': '한글명',
        'ROE(자기자본이익률)': 'ROE',
        '전일기준 시가총액 (억)': '시가총액'
    })
    # 코스닥 '시가총액'은 '억' 단위이므로 100,000,000을 곱해 단위를 통일
    df['시가총액'] = pd.to_numeric(df['시가총액'], errors='coerce').fillna(0) * 100000000

    return df[['단축코드', '한글명', 'ROE', '시가총액']]


# -----------------------------------------------------------------
# (사전 준비 4) 나머지 재료 API 호출 함수 (재현님이 채워주세요)
# -----------------------------------------------------------------

# 2, 3, 6번 재료 (PER, PBR, 배당수익률)
def get_price_info(stock_code):
    """ '주식현재가 시세' API 호출 (시총, PER, PBR, 배당수익률 등) """
    PATH = '/uapi/domestic-stock/v1/quotations/inquire-price'
    HEADERS['tr_id'] = 'FHKST01010100'  # (재현님 확인) 이 TR_ID가 맞는지 확인

    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": stock_code
    }

    try:
        res = requests.get(f"{BASE_URL}{PATH}", headers=HEADERS, params=params)
        res.raise_for_status()  # 200 OK 아니면 오류 발생

        if res.json()['rt_cd'] == '0':
            data = res.json()['output']
            # (재현님 숙제) 'per', 'pbr', 'dvdn_yld', 'hgrn_sum_amt'가 실제 키 이름인지 확인!
            return {
                'per': float(data.get('per', 0)),
                'pbr': float(data.get('pbr', 0)),
                '배당수익률': float(data.get('dvdn_yld', 0)),
                '시가총액_API': float(data.get('hgrn_sum_amt', 0))  # 마스터파일과 비교/검증용
            }
    except Exception as e:
        print(f"  [오류] get_price_info({stock_code}): {e}")

    return {'per': 0, 'pbr': 0, '배당수익률': 0, '시가총액_API': 0}


# 5번 재료 (부채비율)
# 5번 재료 (부채비율)
def get_debt_ratio(stock_code):
    """ '국내주식 안정성비율' API 호출 (부채비율 등) """
    PATH = '/uapi/domestic-stock/v1/finance/stability-ratio'
    HEADERS['tr_id'] = 'FHKST66430600'  # (재현님이 찾아주신 TR_ID)

    # (숙제 1 완료) API 명세서(엑셀) 기준으로 params 완성
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",  # J: 주식시장
        "FID_INPUT_ISCD": stock_code,  # 종목 코드
        "fid_div_cls_code": "0"  # 0: 년, 1: 분기 (우리는 '연간' 기준인 '0' 사용)
    }

    try:
        res = requests.get(f"{BASE_URL}{PATH}", headers=HEADERS, params=params)
        res.raise_for_status()  # 200 OK 아니면 오류 발생

        json_data = res.json()
        if json_data['rt_cd'] == '0':
            data = json_data['output']

            # (숙제 2, 3 완료) Output이 리스트이고, 키 이름이 'lblt_rate'임을 확인
            if data and isinstance(data, list):
                # 가장 최근의 재무제표(첫 번째 항목)에서 'lblt_rate'(부채비율)을 가져옴
                return {
                    '부채비율': float(data[0].get('lblt_rate', 0.0))
                }
    except Exception as e:
        print(f"  [오류] get_debt_ratio({stock_code}): {e}")

    return {'부채비율': 0.0}  # 실패 시 0.0 반환


# -----------------------------------------------------------------
# (실행) Day 1-2: 2,000개 종목 데이터 수집 (V2 - 최적화 버전)
# -----------------------------------------------------------------
def collect_all_data():
    """스크립트의 메인 실행 함수"""

    # [ 1. 마스터 파일 다운로드 및 정제 ]
    print("Day 1-2 (Step 1/3): 마스터 파일 다운로드를 시작합니다...")
    kospi_master_download(BASE_DIR, verbose=True)
    kosdaq_master_download(BASE_DIR, verbose=True)

    print("Day 1-2 (Step 2/3): 마스터 파일 정제를 시작합니다...")
    df_kospi = get_kospi_master_dataframe(BASE_DIR)
    df_kosdaq = get_kosdaq_master_dataframe(BASE_DIR)

    # 코스피, 코스닥 DataFrame 합치기
    df_master = pd.concat([df_kospi, df_kosdaq], ignore_index=True)
    stock_codes = df_master['단축코드'].tolist()

    # (중요) 마스터 파일의 '시가총액'은 단위가 '억' 또는 '원'일 수 있습니다.
    # 코스닥은 '억'이었으므로 100,000,000을 곱해줍니다. 코스피도 확인 필요.
    df_master['시가총액'] = pd.to_numeric(df_master['시가총액'], errors='coerce').fillna(0)
    # 코스피 시가총액이 이미 원 단위라면 위 코스닥 함수처럼 억 단위를 곱할 필요 없음
    # (df_kosdaq에서 이미 단위를 맞춰주었음)

    print(f"총 {len(stock_codes)}개 종목 코드를 확보했습니다.")
    print("--- 마스터 파일 (ROE, 시총) 데이터 (상위 5개) ---")
    print(df_master.head())

    # [ 2. API 호출로 나머지 재료 수집 ]
    print("\nDay 1-2 (Step 3/3): API 호출로 나머지 재료(PBR, PER, 배당, 부채비율) 수집을 시작합니다...")
    api_data_list = []
    count = 0

    for code in stock_codes:
        count += 1
        print(f"[{count}/{len(stock_codes)}] {code} 종목 API 데이터 수집 중...")

        # (중요!) API 초당 호출 횟수 제한 (재무 API: 1초 1건)
        # 1초에 1건이 가장 안전합니다.
        time.sleep(1)

        try:
            # PBR, PER, 배당수익률 호출
            price_data = get_price_info(code)

            # 부채비율 호출
            debt_data = get_debt_ratio(code)

            final_data = {
                '단축코드': code,
                **price_data,
                **debt_data
            }
            api_data_list.append(final_data)

        except Exception as e:
            print(f"  [오류] {code} 처리 중 알 수 없는 오류: {e}")

    # [ 3. 최종 데이터 합치기 및 저장 ]
    df_api_data = pd.DataFrame(api_data_list)
    print("\n--- API 호출 (PER, PBR, 배당, 부채비율) 데이터 (상위 5개) ---")
    print(df_api_data.head())

    # 마스터 파일(ROE, 시총)과 API 데이터(나머지 4개)를 '단축코드' 기준으로 합치기
    final_df = pd.merge(df_master, df_api_data, on='단축코드')

    # [최종 컬럼 정리]
    # (get_price_info의 '시가총액_API'는 마스터 파일과 비교/검증용이었으므로 제거)
    if '시가총액_API' in final_df.columns:
        final_df = final_df.drop(columns=['시가총액_API'])

    # (최종 6가지 재료 + 식별자)
    final_feature_df = final_df[[
        '단축코드',
        '한글명',
        'per',
        'pbr',
        'ROE',
        '시가총액',
        '부채비율',
        '배당수익률'
    ]]

    # 4. CSV 파일로 저장
    output_filename = 'stockit_ai_features_v1.csv'
    final_feature_df.to_csv(output_filename, index=False, encoding='utf-8-sig')

    print(f"\nDay 1-2: 모든 재료 수집 및 정제 완료! '{output_filename}'에 저장됨.")
    print(final_feature_df.head())


# -----------------------------------------------------------------
# (메인 실행)
# -----------------------------------------------------------------
if __name__ == "__main__":
    collect_all_data()

