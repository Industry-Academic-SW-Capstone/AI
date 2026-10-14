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
    embedding   vector(768),                    -- Gemini gemini-embedding-001 (768차원으로 축소, 정규화)
    created_at  TIMESTAMP DEFAULT NOW(),

    -- 중복 방지: 같은 종목 + 같은 링크
    CONSTRAINT uq_news_link UNIQUE (stock_code, link)
);

-- 검색 성능을 위한 인덱스
CREATE INDEX IF NOT EXISTS idx_news_stock_code ON news_embeddings (stock_code);
CREATE INDEX IF NOT EXISTS idx_news_pub_date   ON news_embeddings (pub_date DESC);

-- 벡터 인덱스(HNSW)는 두지 않는다. 검색이 stock_code·최근 30일로 먼저 좁혀져 종목당 수십~수백 건만
-- 비교하면 되고, 근사 인덱스는 필터를 나중에 적용해 상위 K건을 다 채우지 못할 수 있다.
