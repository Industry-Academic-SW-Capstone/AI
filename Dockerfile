FROM python:3.10-slim

WORKDIR /app

# requirements 설치
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 앱 코드 복사
COPY app/ .

# PYTHONPATH 지정: /app 폴더를 최상위 패키지로 인식
ENV PYTHONPATH=/app

# uvicorn 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
