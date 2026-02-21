"""
뉴스 RAG 파이프라인
- 종목명 → 네이버 뉴스 검색 → Gemini 임베딩 → pgvector 저장
"""

import logging

from app.infrastructure.naver_news_client import search_stock_news
from app.infrastructure.gemini_embedding_client import embed_texts
from app.infrastructure.pgvector_client import insert_news_embeddings

logger = logging.getLogger(__name__)


def collect_and_store_news(
    stock_code: str,
    stock_name: str,
    display: int = 20,
) -> int:
    """
    종목의 최신 뉴스를 수집 → 임베딩 → DB 저장

    Args:
        stock_code: 종목코드 (예: '005930')
        stock_name: 종목명 (예: '삼성전자')
        display: 수집할 뉴스 수

    Returns:
        저장된 뉴스 수
    """
    # 1. 뉴스 검색
    news_list = search_stock_news(stock_name, display=display)
    if not news_list:
        logger.warning("뉴스 검색 결과 없음: %s", stock_name)
        return 0

    # 2. 임베딩 텍스트 준비 (제목 + 요약)
    texts = [
        f"{n['title']}. {n['description']}" for n in news_list
    ]

    # 3. Gemini 임베딩
    embeddings = embed_texts(texts)

    # 4. DB 저장용 데이터 조합
    rows = []
    for news, embedding in zip(news_list, embeddings):
        rows.append({
            "stock_code": stock_code,
            "stock_name": stock_name,
            "title": news["title"],
            "description": news["description"],
            "link": news["link"],
            "pub_date": news["pub_date"],
            "embedding": embedding,
        })

    # 5. pgvector 벌크 INSERT
    inserted = insert_news_embeddings(rows)
    logger.info("[%s] %s: %d건 수집, %d건 저장", stock_code, stock_name, len(rows), inserted)
    return inserted
