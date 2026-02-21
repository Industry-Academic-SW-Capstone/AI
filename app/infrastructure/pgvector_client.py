"""
pgvector 연결 및 쿼리 헬퍼
- 커넥션 풀 기반 (psycopg2)
- 뉴스 임베딩 저장 / 유사도 검색
"""

import os
import logging
from contextlib import contextmanager

import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import execute_values

logger = logging.getLogger(__name__)

_pool: ThreadedConnectionPool | None = None


def get_pool() -> ThreadedConnectionPool:
    global _pool
    if _pool is None:
        _pool = ThreadedConnectionPool(
            minconn=2,
            maxconn=10,
            host=os.getenv("PGVECTOR_HOST", "localhost"),
            port=int(os.getenv("PGVECTOR_PORT", "5433")),
            user=os.getenv("PGVECTOR_USER", "stockai"),
            password=os.getenv("PGVECTOR_PASSWORD", "stockai1234"),
            dbname=os.getenv("PGVECTOR_DB", "stock_news"),
        )
        logger.info("pgvector connection pool created")
    return _pool


@contextmanager
def get_conn():
    """커넥션 풀에서 연결을 빌려 쓰고 반납하는 컨텍스트 매니저"""
    pool = get_pool()
    conn = pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


def insert_news_embeddings(rows: list[dict]) -> int:
    """
    뉴스 임베딩 벌크 INSERT (중복 무시)

    Args:
        rows: [{"stock_code", "stock_name", "title", "description",
                "link", "pub_date", "embedding"(list[float])}]

    Returns:
        삽입된 행 수
    """
    if not rows:
        return 0

    sql = """
        INSERT INTO news_embeddings
            (stock_code, stock_name, title, description, link, pub_date, embedding)
        VALUES %s
        ON CONFLICT (stock_code, link) DO NOTHING
    """

    values = [
        (
            r["stock_code"],
            r["stock_name"],
            r["title"],
            r.get("description", ""),
            r["link"],
            r.get("pub_date"),
            r["embedding"],  # list[float] → psycopg2가 자동 변환
        )
        for r in rows
    ]

    with get_conn() as conn:
        with conn.cursor() as cur:
            execute_values(cur, sql, values, page_size=100)
            inserted = cur.rowcount
    logger.info("inserted %d / %d news embeddings", inserted, len(rows))
    return inserted


def search_similar_news(
    stock_code: str,
    query_embedding: list[float],
    top_k: int = 5,
    days: int = 30,
) -> list[dict]:
    """
    종목코드 필터 + 코사인 유사도 상위 K개 뉴스 검색

    Args:
        stock_code: 종목코드
        query_embedding: 쿼리 임베딩 벡터 (768차원)
        top_k: 반환할 뉴스 수
        days: 최근 N일 이내 뉴스만

    Returns:
        [{"title", "description", "link", "pub_date", "similarity"}]
    """
    sql = """
        SELECT title, description, link, pub_date,
               1 - (embedding <=> %s::vector) AS similarity
        FROM news_embeddings
        WHERE stock_code = %s
          AND pub_date >= NOW() - INTERVAL '%s days'
        ORDER BY embedding <=> %s::vector
        LIMIT %s
    """

    embedding_str = "[" + ",".join(str(v) for v in query_embedding) + "]"

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (embedding_str, stock_code, days, embedding_str, top_k))
            columns = ["title", "description", "link", "pub_date", "similarity"]
            results = [dict(zip(columns, row)) for row in cur.fetchall()]

    return results


def close_pool():
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None
        logger.info("pgvector connection pool closed")
