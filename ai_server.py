from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
import joblib

# --- [중요] final_analyzer.py의 핵심 함수들을 가져옵니다 ---
# (이 파일들은 같은 폴더에 있어야 합니다)
import persona_definitions as pd_data
from final_analyzer import get_style_vector, calculate_persona_match

app = Flask(__name__)  # Flask 앱 초기화

# --- AI 모듈 로드 (서버가 켜질 때 1번만 실행) ---
try:
    model = joblib.load('kmeans_model.pkl')
    scaler = joblib.load('scaler.pkl')
    # 가상 재무 DB (API 시뮬레이션용)
    stock_db = pd.read_csv('dummy_stock_db.csv', encoding='utf-8', dtype={'단축코드': str})
    stock_db['단축코드'] = stock_db['단축코드'].str.strip()
    print("✅ AI 모델, 번역기, 가상 DB 로드 완료. 서버 준비됨.")
except Exception as e:
    print(f"🚨 치명적 오류: AI 모듈 로드 실패! {e}")
    model = None  # 서버가 죽지 않도록 None으로 처리

# 8가지 스타일 태그 이름 (결과 전송용)
TAG_NAMES = ['[안정형 일반주]', '[고효율 우량주]', '[초고배당 가치주]', '[고위험 저평가주]',
             '[고성장 기대주]', '[초대형 우량주]', '[초저평가 가치주]', '[고가치 성장주]']


# --- API 엔드포인트 정의 ---
# Spring Boot가 http://[AI서버주소]/analyze 로 POST 요청을 보낼 주소
@app.route("/analyze", methods=['POST'])
def analyze_portfolio():
    if model is None:
        return jsonify({"error": "AI 모델이 로드되지 않았습니다."}), 500

    # 1. Spring Boot 서버로부터 JSON 데이터를 받습니다.
    # (예: { "단축코드": ["005930", "000990"], "투자금액": [1000000, 1000000] })
    data = request.get_json()

    # 2. 받은 JSON을 DataFrame으로 변환
    try:
        user_df = pd.DataFrame(data)
        user_df['단축코드'] = user_df['단축코드'].astype(str).str.strip()
    except Exception as e:
        return jsonify({"error": "잘못된 요청 데이터 형식입니다.", "message": str(e)}), 400

    # 3. AI 엔진 실행 (final_analyzer.py의 함수들 재사용)
    user_vector, merged_details = get_style_vector(user_df, stock_db, scaler, model)

    if user_vector is None:
        return jsonify({"error": "포트폴리오 분석에 실패했습니다. (DB 매칭 실패)"}), 404

    # 4. 페르소나 매칭 실행
    match_results = calculate_persona_match(user_vector)

    # 5. 최종 결과를 JSON으로 조립하여 Spring Boot에 반환

    # 5-1. 사용자 스타일 비중 (Phase 2)
    style_summary = []
    for i in range(8):
        if user_vector[i] > 0:
            style_summary.append({
                "style_tag": TAG_NAMES[i],
                "percentage": round(user_vector[i] * 100, 2)
            })
    style_summary = sorted(style_summary, key=lambda x: x['percentage'], reverse=True)

    # 5-2. 페르소나 일치율 (Phase 3)
    persona_summary = []
    sorted_matches = sorted(match_results.items(), key=lambda item: item[1], reverse=True)
    for name, percent in sorted_matches:
        persona_summary.append({
            "name": name,
            "percentage": percent,
            "philosophy": pd_data.PERSONA_PHILOSOPHY.get(name, "")  # 정의된 철학 추가
        })

    # 5-3. 보유 종목 상세 (주린이 해설)
    stock_details = []
    for _, row in merged_details.iterrows():
        if pd.notna(row['final_style_tag']):
            stock_details.append({
                "stock_code": row['단축코드'],
                "stock_name": row['한글명'],
                "style_tag": row['final_style_tag'],
                "description": row['style_description']
            })

    # 최종 JSON 응답
    response = {
        "user_style_breakdown": style_summary,
        "persona_match": persona_summary,
        "stock_details": stock_details
    }

    return jsonify(response)


# --- 서버 실행 ---
if __name__ == '__main__':
    # 0.0.0.0: 모든 IP에서 접속 허용 (Spring Boot가 호출할 수 있도록)
    # port=5001: 5001번 포트 사용 (다른 서버와 겹치지 않게)
    app.run(host='0.0.0.0', port=5001, debug=True)