"""
Step 4-5: 리포트 생성기
- 스코어링 결과 + RAG 뉴스 → Gemini LLM → 투자 분석 리포트
"""

import os
import logging
import time

from google import genai
from google.genai.errors import ClientError

logger = logging.getLogger(__name__)


def _get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다")
    return genai.Client(api_key=api_key)


REPORT_PROMPT = """당신은 한국 주식시장 전문 애널리스트입니다.

아래 정보를 바탕으로 해당 종목에 대한 **투자 분석 리포트**를 작성해주세요.

## 종목 정보
- 종목명: {stock_name} ({stock_code})
- 스타일 태그: {style_tag}

## 스코어링 결과 (100점 만점)
- 성장성 점수: {growth_score}점
- 안정성 점수: {stability_score}점
- 유사도 점수: {similarity_score}점
- **종합 점수: {composite_score}점**

## 최근 관련 뉴스
{news_section}

## 작성 규칙
1. **종합 평가** (2~3문장): 종합 점수와 스코어링 결과를 바탕으로 한 줄 평가
2. **강점 분석** (2~3개 bullet): 높은 점수 항목 위주
3. **리스크 요인** (2~3개 bullet): 낮은 점수 항목 + 뉴스에서 도출되는 리스크
4. **뉴스 기반 인사이트** (2~3문장): 최근 뉴스 흐름에서 읽히는 시장 분위기
5. **투자 의견**: '적극 매수 / 매수 / 중립 / 주의 / 매도' 중 하나 선택 + 한 줄 이유

한국어로 작성하고, 전문적이면서도 개인 투자자가 이해할 수 있는 수준으로 써주세요.
총 길이는 300~500자 이내로 간결하게 작성하세요.
"""


def _format_news_section(news_list: list[dict]) -> str:
    """뉴스 리스트를 프롬프트용 문자열로 변환"""
    if not news_list:
        return "- 최근 관련 뉴스가 없습니다."

    lines = []
    for i, n in enumerate(news_list, 1):
        title = n.get("title", "")
        desc = n.get("description", "")
        similarity = n.get("similarity", 0)
        lines.append(f"{i}. [{title}] (관련도: {similarity:.2f})")
        if desc:
            lines.append(f"   요약: {desc[:100]}")
    return "\n".join(lines)


def generate_report(
    stock_code: str,
    stock_name: str,
    style_tag: str,
    growth_score: float,
    stability_score: float,
    similarity_score: float,
    composite_score: float,
    news_list: list[dict],
) -> str:
    """
    스코어링 + 뉴스 기반 투자 분석 리포트 생성

    Args:
        stock_code: 종목코드
        stock_name: 종목명
        style_tag: 스타일 태그 (예: '가치주')
        growth_score: 성장성 점수
        stability_score: 안정성 점수
        similarity_score: 유사도 점수
        composite_score: 종합 점수
        news_list: RAG 검색 결과 뉴스 리스트

    Returns:
        LLM 생성 리포트 텍스트
    """
    news_section = _format_news_section(news_list)

    prompt = REPORT_PROMPT.format(
        stock_code=stock_code,
        stock_name=stock_name,
        style_tag=style_tag,
        growth_score=growth_score,
        stability_score=stability_score,
        similarity_score=similarity_score,
        composite_score=composite_score,
        news_section=news_section,
    )

    client = _get_client()
    max_retries = 3

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="models/gemini-2.5-flash",
                contents=prompt,
            )
            report = response.text.strip()
            if report:
                return report
        except ClientError as e:
            error_str = str(e)
            if "429" in error_str or "503" in error_str:
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
            logger.error("리포트 생성 API 오류: %s", e)
            break
        except Exception as e:
            logger.error("리포트 생성 실패: %s", e)
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            break

    return f"{stock_name}({stock_code})의 종합 점수는 {composite_score}점입니다. (현재 AI 분석량이 많아 상세 리포트를 생성하지 못했습니다.)"
