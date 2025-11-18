import os
from google import genai

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")
    exit(1)

client = genai.Client(api_key=api_key)

print("사용 가능한 모델 목록:")
try:
    models = client.models.list()
    for model in models:
        print(f"- {model.name}")
except Exception as e:
    print(f"에러: {e}")

