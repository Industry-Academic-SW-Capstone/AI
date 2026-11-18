"""
pgvector 연결 및 쿼리 헬퍼
- 커넥션 풀 기반 (psycopg2)
- 뉴스 임베딩 저장 / 유사도 검색
"""

import os
import logging
import threading
from contextlib import contextmanager

import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import execute_values

logger = logging.getLogger(__name__)

_pool: ThreadedConnectionPool | None = None
_pool_lock = threading.Lock()

# 뉴스 테이블 정의는 여기 한 곳에만 둔다. 서버가 처음 DB 에 붙을 때 만들고, 있으면 건너뛴다.
# 벡터 인덱스(HNSW)는 두지 않는다. 검색이 stock_code·최근 30일로 먼저 좁혀져 종목당 수십~수백 건만
# 비교하면 되고, 근사 인덱스는 필터를 나중에 적용해 상위 K건을 다 채우지 못할 수 있다.
SCHEMA_SQL = """
    CREATE EXTENSION IF NOT EXISTS vector;

    CREATE TABLE IF NOT EXISTS news_embeddings (
        id          BIGSERIAL PRIMARY KEY,
        stock_code  VARCHAR(20)  NOT NULL,
        stock_name  VARCHAR(100) NOT NULL,
        title       TEXT         NOT NULL,
        description TEXT,
        link        TEXT,
        pub_date    TIMESTAMP,
        embedding   vector(768),  -- gemini_embedding_client.EMBEDDING_DIM 과 맞아야 한다
        created_at  TIMESTAMP DEFAULT NOW(),
        CONSTRAINT uq_news_link UNIQUE (stock_code, link)
    );

    CREATE INDEX IF NOT EXISTS idx_news_stock_code ON news_embeddings (stock_code);
    CREATE INDEX IF NOT EXISTS idx_news_pub_date   ON news_embeddings (pub_date DESC);
"""


def get_pool() -> ThreadedConnectionPool:
    global _pool
    # 리포트 스트리밍이 스레드풀에서 동시에 처음 부르면 풀이 두 번 만들어질 수 있다.
    with _pool_lock:
        if _pool is None:
            pool = ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                host=os.getenv("PGVECTOR_HOST", "localhost"),
                port=int(os.getenv("PGVECTOR_PORT", "5433")),
                user=os.getenv("PGVECTOR_USER", "stockai"),
                password=os.getenv("PGVECTOR_PASSWORD", "stockai1234"),
                dbname=os.getenv("PGVECTOR_DB", "stock_news"),
            )
            _ensure_schema(pool)
            _pool = pool
            logger.info("pgvector connection pool created")
    return _pool


def _ensure_schema(pool: ThreadedConnectionPool) -> None:
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(SCHEMA_SQL)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


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


# 검색 기간(search_similar_news 의 days)보다 짧으면 안 된다.
RETENTION_DAYS = 30


def delete_expired_news(days: int = RETENTION_DAYS) -> int:
    """검색에 쓰이지 않는 오래된 뉴스를 지운다 (pub_date 가 없으면 수집 시각 기준)"""
    sql = """
        DELETE FROM news_embeddings
        WHERE pub_date < NOW() - make_interval(days => %s)
           OR (pub_date IS NULL AND created_at < NOW() - make_interval(days => %s))
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (days, days))
            deleted = cur.rowcount
    if deleted:
        logger.info("deleted %d expired news embeddings", deleted)
    return deleted


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
