-- pgvector 확장 활성화
CREATE EXTENSION IF NOT EXISTS vector;

-- 뉴스 임베딩 테이블
CREATE TABLE IF NOT EXISTS news_embeddings (
    id          BIGSERIAL PRIMARY KEY,
    stock_code  VARCHAR(20)  NOT NULL,          -- 종목코드 (예: '005930')
    stock_name  VARCHAR(100) NOT NULL,          -- 종목명 (예: '삼성전자')
    title       TEXT         NOT NULL,          -- 뉴스 제목
    description TEXT,                           -- 뉴스 요약
    link        TEXT,                           -- 원문 URL
    pub_date    TIMESTAMP,                      -- 기사 발행일
    embedding   vector(3072),                   -- Gemini gemini-embedding-001 (3072차원)
    created_at  TIMESTAMP DEFAULT NOW(),

    -- 중복 방지: 같은 종목 + 같은 링크
    CONSTRAINT uq_news_link UNIQUE (stock_code, link)
);

-- 검색 성능을 위한 인덱스
CREATE INDEX IF NOT EXISTS idx_news_stock_code ON news_embeddings (stock_code);
CREATE INDEX IF NOT EXISTS idx_news_pub_date   ON news_embeddings (pub_date DESC);

-- HNSW 벡터 인덱스 (코사인 유사도 기반)
CREATE INDEX IF NOT EXISTS idx_news_embedding ON news_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
