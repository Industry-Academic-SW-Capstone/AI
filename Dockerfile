FROM python:3.10-slim

WORKDIR /app

# requirements 설치
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 앱 코드 복사
COPY app/ .

# PYTHONPATH 지정
ENV PYTHONPATH=/app

# 컨테이너가 노출할 포트
EXPOSE 8000

# uvicorn 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
