"""
Gemini 임베딩 클라이언트
- gemini-embedding-001 모델 (768차원으로 축소)
- 배치 임베딩 지원
"""

import os
import logging
import time

import numpy as np
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "models/gemini-embedding-001"
# MRL 로 학습된 모델이라 앞쪽 768차원만 써도 품질이 거의 같다(MTEB 67.99, 1536차원 68.17).
# pgvector_client.SCHEMA_SQL 의 vector(768) 과 맞아야 한다.
EMBEDDING_DIM = 768
_EMBED_CONFIG = types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIM)


def _normalize(values: list[float]) -> list[float]:
    # 3072 가 아닌 차원은 정규화돼 나오지 않는다(Gemini 문서). 코사인 순위엔 영향 없지만 거리 값을 맞춘다.
    vec = np.asarray(values, dtype=np.float64)
    norm = np.linalg.norm(vec)
    return (vec / norm).tolist() if norm > 0 else vec.tolist()


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
        768차원 float 리스트 (정규화됨)
    """
    client = _get_client()
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=_EMBED_CONFIG,
    )
    return _normalize(response.embeddings[0].values)


def embed_texts(texts: list[str], batch_size: int = 20) -> list[list[float] | None]:
    """
    배치 텍스트 임베딩 (API rate limit 고려)

    Args:
        texts: 임베딩할 텍스트 리스트
        batch_size: 한번에 처리할 텍스트 수

    Returns:
        임베딩 벡터 리스트 (입력과 같은 순서, 실패한 항목은 None)
    """
    client = _get_client()
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]

        try:
            response = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=batch,
                config=_EMBED_CONFIG,
            )
            batch_embeddings = [_normalize(e.values) for e in response.embeddings]
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
                        config=_EMBED_CONFIG,
                    )
                    all_embeddings.append(_normalize(resp.embeddings[0].values))
                except Exception as inner_e:
                    # 영벡터를 넣으면 코사인 거리가 NaN 이 되어 검색을 망친다. 저장하지 않도록 None 으로 표시한다.
                    logger.error("임베딩 실패 (skip): %s", inner_e)
                    all_embeddings.append(None)

        # rate limit 방지
        if i + batch_size < len(texts):
            time.sleep(0.3)

    logger.info("임베딩 완료: %d / %d건", sum(e is not None for e in all_embeddings), len(texts))
    return all_embeddings
