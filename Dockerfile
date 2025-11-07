# Dockerfile 예시
FROM python:3.10-slim

WORKDIR /app

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

# uvicorn 실행 시 main.py 경로 지정
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
