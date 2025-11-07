from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
import pandas as pd
import numpy as np
import joblib
from fastapi.responses import JSONResponse

# --- [중요] 핵심 로직 파일을 가져옵니다 ---
# (이 파일들은 main.py와 같은 폴더에 있어야 합니다)
import persona_definitions as pd_data
# [수정완료] 'final_analyzer' -> 'analyze_portfolio'로 변경했습니다.
from analyze_portfolio import get_style_vector, calculate_persona_match

# --- 1. Pydantic으로 입/출력 모델 정의 ---

# (입력) Spring Boot가 보낼 데이터 형식
class PortfolioRequest(BaseModel):
    단축코드: List[str]
    투자금액: List[float]  # 돈 관련 데이터는 float이 더 안전합니다.

# (출력) FastAPI가 반환할 데이터 형식 (API 문서를 위해 상세히 정의)
class StyleBreakdown(BaseModel):
    style_tag: str
    percentage: float

class PersonaMatch(BaseModel):
    name: str
    percentage: float
    philosophy: str

class StockDetail(BaseModel):
    stock_code: str
    stock_name: str
    style_tag: str
    description: str

class AnalysisResponse(BaseModel):
    user_style_breakdown: List[StyleBreakdown]
    persona_match: List[PersonaMatch]
    stock_details: List[StockDetail]


# --- 2. FastAPI 앱 생성 ---
app = FastAPI()

# --- 3. AI 모듈 로드 (서버가 켜질 때 1번만 실행) ---
try:
    model = joblib.load('kmeans_model.pkl')
    scaler = joblib.load('scaler.pkl')
    stock_db = pd.read_csv('dummy_stock_db.csv', encoding='utf-8', dtype={'단축코드': str})
    stock_db['단축코드'] = stock_db['단축코드'].str.strip()
    print("✅ AI 모델, 번역기, 가상 DB 로드 완료. FastAPI 서버 준비됨.")
except Exception as e:
    print(f"🚨 치명적 오류: AI 모듈 로드 실패! {e}")
    model = None

# (Flask 코드와 동일) 8가지 스타일 태그 이름 (결과 전송용)
TAG_NAMES = ['[안정형 일반주]', '[고효율 우량주]', '[초고배당 가치주]', '[고위험 저평가주]',
             '[고성장 기대주]', '[초대형 우량주]', '[초저평가 가치주]', '[고가치 성장주]']


# --- 4. API 엔드포인트 정의 ---
# @app.route("/analyze", methods=['POST']) -> @app.post("/analyze")로 변경
# response_model=AnalysisResponse : 이 함수의 리턴값이 AnalysisResponse 형식인지 FastAPI가 검사
@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_portfolio(portfolio_data: PortfolioRequest):
    """
    Spring Boot 서버로부터 사용자의 포트폴리오(종목코드, 투자금액)를 받아,
    AI 모델로 분석 후 스타일 비중, 페르이, 종목별 상세 설명을 반환합니다.
    """
    if model is None:
        return JSONResponse(
            status_code=500,
            content={"error": "AI 모델이 로드되지 않았습니다."}
        )

    # 1. (변경) Pydantic 모델을 딕셔너리로 변환
    data = portfolio_data.dict() # <-- Pydantic 모델을 dict로 변경

    # 2. (동일) 받은 딕셔너리를 DataFrame으로 변환
    try:
        user_df = pd.DataFrame(data)
        user_df['단축코드'] = user_df['단축코드'].astype(str).str.strip()
    except Exception as e:
        return JSONResponse(
            status_code=400, # 잘못된 요청
            content={"error": "잘못된 요청 데이터 형식입니다.", "message": str(e)}
        )

    # 3. (동일) AI 엔진 실행
    user_vector, merged_details = get_style_vector(user_df, stock_db, scaler, model)

    if user_vector is None:
        return JSONResponse(
            status_code=404, # 리소스 없음 (매칭 실패)
            content={"error": "포트폴리오 분석에 실패했습니다. (DB 매칭 실패)"}
        )

    # 4. (동일) 페르소나 매칭 실행
    match_results = calculate_persona_match(user_vector)

    # 5. (동일) 최종 결과를 JSON으로 조립

    # 5-1. 사용자 스타일 비중
    style_summary = []
    for i in range(8):
        if user_vector[i] > 0:
            style_summary.append({
                "style_tag": TAG_NAMES[i],
                "percentage": round(user_vector[i] * 100, 2)
            })
    style_summary = sorted(style_summary, key=lambda x: x['percentage'], reverse=True)

    # 5-2. 페르소나 일치율
    persona_summary = []
    sorted_matches = sorted(match_results.items(), key=lambda item: item[1], reverse=True)
    for name, percent in sorted_matches:
        persona_summary.append({
            "name": name,
            "percentage": percent,
            "philosophy": pd_data.PERSONA_PHILOSOPHY.get(name, "")
        })

    # 5-3. 보유 종목 상세
    stock_details = []
    for _, row in merged_details.iterrows():
        if pd.notna(row['final_style_tag']):
            stock_details.append({
                "stock_code": row['단축코드'],
                "stock_name": row['한글명'],
                "style_tag": row['final_style_tag'],
                "description": row['style_description']
            })

    # (거의 동일) 최종 JSON 응답
    response = {
        "user_style_breakdown": style_summary,
        "persona_match": persona_summary,
        "stock_details": stock_details
    }

    # FastAPI: 그냥 딕셔너리(response)를 리턴하면 Pydantic이 JSON으로 변환
    return response

# --- 5. (삭제) 서버 실행 코드 ---
# if __name__ == '__main__':
#     app.run(...)
# (이 부분은 uvicorn 명령어로 대체되므로 main.py에서 삭제합니다)