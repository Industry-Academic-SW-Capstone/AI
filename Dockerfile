FROM python:3.10-slim

WORKDIR /

# requirements 설치
COPY app/requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# app 폴더를 루트에 복사
COPY app/ /app/

# PYTHONPATH 지정
ENV PYTHONPATH=/

# 컨테이너가 노출할 포트
EXPOSE 8000

# uvicorn 실행 (from app.domain... import가 작동하도록)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
