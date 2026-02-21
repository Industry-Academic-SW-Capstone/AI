"""
Gemini 임베딩 클라이언트
- text-embedding-004 모델 (768차원)
- 배치 임베딩 지원
"""

import os
import logging
import time

from google import genai

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "models/gemini-embedding-001"


def _get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다")
    return genai.Client(api_key=api_key)


def embed_text(text: str) -> list[float]:
    """
    단일 텍스트 임베딩 (768차원)

    Args:
        text: 임베딩할 텍스트

    Returns:
        768차원 float 리스트
    """
    client = _get_client()
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
    )
    return response.embeddings[0].values


def embed_texts(texts: list[str], batch_size: int = 20) -> list[list[float]]:
    """
    배치 텍스트 임베딩 (API rate limit 고려)

    Args:
        texts: 임베딩할 텍스트 리스트
        batch_size: 한번에 처리할 텍스트 수

    Returns:
        임베딩 벡터 리스트
    """
    client = _get_client()
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]

        try:
            response = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=batch,
            )
            batch_embeddings = [e.values for e in response.embeddings]
            all_embeddings.extend(batch_embeddings)
        except Exception as e:
            logger.warning("임베딩 배치 %d 실패, 개별 처리로 전환: %s", i, e)
            # 개별 처리 fallback
            for text in batch:
                try:
                    time.sleep(0.5)
                    resp = client.models.embed_content(
                        model=EMBEDDING_MODEL,
                        contents=text,
                    )
                    all_embeddings.append(resp.embeddings[0].values)
                except Exception as inner_e:
                    logger.error("임베딩 실패 (skip): %s", inner_e)
                    all_embeddings.append([0.0] * 3072)

        # rate limit 방지
        if i + batch_size < len(texts):
            time.sleep(0.3)

    logger.info("임베딩 완료: %d / %d건", len(all_embeddings), len(texts))
    return all_embeddings
