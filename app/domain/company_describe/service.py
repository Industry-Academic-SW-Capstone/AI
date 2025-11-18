import os
import redis
from google import genai
from google.genai.errors import APIError


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
    기업 설명을 생성합니다.

    Args:
        company_name: 기업 한글명
        use_cache: 캐시 사용 여부 (기본값: True)

    Returns:
        (설명 텍스트, 캐시 히트 여부)
    """
    cache_key = f"company_desc:{company_name}"
    cached = False

    # 1. 캐시 확인
    if use_cache:
        try:
            cache_client = get_redis_client()
            cached_desc = cache_client.get(cache_key)
            if cached_desc:
                return cached_desc, True
        except Exception as e:
            print(f"Redis 캐시 조회 실패 (무시하고 계속): {e}")

    # 2. 캐시 미스 → LLM API 호출
    try:
        gemini_client = get_gemini_client()
        prompt = PROMPT_TEMPLATE.format(company_name=company_name)

        response = gemini_client.models.generate_content(
            model="gemini-1.5-flash-latest",  # 무료 티어에서 토큰이 더 많은 빠른 모델
            contents=prompt,
        )

        description = response.text.strip()

        if not description:
            raise Exception("LLM이 유효한 답변을 생성하지 못했습니다.")

        # 3. 캐시 저장 (TTL: 3시간 = 10800초)
        if use_cache:
            try:
                cache_client = get_redis_client()
                cache_client.setex(cache_key, 10800, description)
            except Exception as e:
                print(f"Redis 캐시 저장 실패 (무시하고 계속): {e}")

        return description, False

    except APIError as e:
        raise Exception(f"Gemini API 호출 오류: {e}")
    except Exception as e:
        raise Exception(f"기업 설명 생성 중 오류: {e}")


def get_company_description_no_cache(company_name: str) -> str:
    """
    캐시를 사용하지 않고 기업 설명을 생성합니다. (성능 비교용)

    Args:
        company_name: 기업 한글명

    Returns:
        설명 텍스트
    """
    description, _ = get_company_description(company_name, use_cache=False)
    return description
