import os
import time
import redis
from google import genai
from google.genai.errors import APIError, ClientError


# Redis 클라이언트 초기화
def get_redis_client():
    """Redis 클라이언트 반환 (싱글톤 패턴)"""
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    return redis.Redis(
        host=redis_host,
        port=redis_port,
        decode_responses=True,
        socket_connect_timeout=2,
    )


# Gemini 클라이언트 초기화
def get_gemini_client():
    """Gemini LLM 클라이언트 반환"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")
    return genai.Client(api_key=api_key)


# 프롬프트 템플릿
PROMPT_TEMPLATE = """당신은 한국 주식시장의 상장 기업을 전문적으로 분석하는 금융 AI 전문가입니다.

사용자가 요청한 기업명인 '{company_name}'에 대해 설명해 주세요.

답변은 핵심 사업 분야, 주요 제품, 그리고 산업에서의 위치를 포함하여 **두 문장 이내**로 간결하게 작성해야 합니다.

예시 답변 형식:
"삼성전자(Samsung Electronics)는 대한민국을 대표하는 세계적인 종합 전자 기업입니다. 메모리 반도체, 스마트폰, TV, 가전제품 등 광범위한 분야에서 글로벌 리더십을 가지고 있습니다."
"""


def get_company_description(
    company_name: str, use_cache: bool = True
) -> tuple[str, bool]:
    """
    기업 설명을 생성합니다. (재시도 및 에러 처리 강화)

    """
    cache_key = f"company_desc:{company_name}"

    # 1. 캐시 확인
    if use_cache:
        try:
            cache_client = get_redis_client()
            cached_desc = cache_client.get(cache_key)
            if cached_desc:
                return cached_desc, True
        except Exception as e:
            print(f"Redis 캐시 조회 실패 (무시): {e}")

    # 2. 캐시 미스 → LLM API 호출 (재시도 로직 포함)
    gemini_client = get_gemini_client()
    prompt = PROMPT_TEMPLATE.format(company_name=company_name)

    # ✅ 수정됨: 가장 확실한 모델명 사용
    model_name = "gemini-1.5-flash"
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = gemini_client.models.generate_content(
                model=model_name,
                contents=prompt,
            )

            description = response.text.strip()
            if not description:
                raise Exception("Empty response")

            # 3. 캐시 저장 (TTL: 3시간)
            if use_cache:
                try:
                    cache_client = get_redis_client()
                    cache_client.setex(cache_key, 10800, description)
                except Exception as e:
                    print(f"Redis 캐시 저장 실패 (무시): {e}")

            return description, False

        except ClientError as e:
            # 429(한도초과) 또는 503(서버과부하) 등은 재시도
            error_str = str(e)
            if (
                "429" in error_str
                or "503" in error_str
                or "RESOURCE_EXHAUSTED" in error_str
            ):
                if attempt < max_retries - 1:
                    print(
                        f"⚠️ API 과부하/제한 ({attempt+1}/{max_retries}). 2초 후 재시도..."
                    )
                    time.sleep(2)
                    continue

            # 재시도 불가능한 에러면 루프 탈출
            print(f"❌ Gemini API 호출 치명적 오류: {e}")
            break

        except Exception as e:
            print(f"❌ 알 수 없는 오류: {e}")
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            break

    # 4. 모든 시도 실패 시 '안전한 기본값' 리턴 (사용자에게 에러창 안 띄우기 위함)
    fallback_text = f"{company_name}은(는) 한국 주식시장에 상장된 기업입니다. (현재 AI 분석량이 많아 상세 정보를 불러오지 못했습니다.)"
    return fallback_text, False


def get_company_description_no_cache(company_name: str) -> str:
    description, _ = get_company_description(company_name, use_cache=False)
    return description
