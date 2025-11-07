# 1. 베이스 이미지 (Python 3.10-slim을 권장합니다)
FROM python:3.10-slim

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. 의존성 파일 복사 및 설치
COPY requirements.txt requirements.txt
# --no-cache-dir : 도커 이미지 용량을 줄이는 옵션
RUN pip install --no-cache-dir -r requirements.txt

# 4. (중요) AI 모델, DB, 커스텀 모듈 등 모든 파일을 이미지 안으로 복사
# (Dockerfile과 같은 위치에 파일들이 있다고 가정)
COPY kmeans_model.pkl .
COPY scaler.pkl .
COPY dummy_stock_db.csv .
# [수정완료] 이 줄이 'analyze_portfolio.py'가 되어야 합니다.
COPY analyze_portfolio.py .
COPY persona_definitions.py .

# 5. 메인 서버 코드 복사
COPY main.py .

# 6. (변경) 서버 실행 명령어
# Flask: CMD ["python", "main.py"]
# FastAPI: uvicorn을 직접 실행합니다. 포트는 5001로 지정.
# K8s 환경에서는 0.0.0.0 호스트가 필수입니다.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5001"]