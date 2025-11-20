from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ⛔️ 잘못된 경로 (컨테이너 안에서는 'domain'이 루트가 아님)
# from domain.stock_analyze.controller import router as stock_router
# from domain.portfolio_analyze.controller import router as portfolio_router

# ✅ 올바른 경로
from app.domain.stock_analyze.controller import router as stock_router
from app.domain.portfolio_analyze.controller import router as portfolio_router
from app.domain.company_describe.controller import router as company_router
from app.domain.performance_test.controller import router as performance_router

from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(
    title="Stock AI Analyze Server",
    version="0.1.16",
    description="AI 기반 주식 분석 및 기업 설명 서비스",
)

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 origin만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app)


@app.on_event("startup")
async def startup():
    pass


app.include_router(stock_router, prefix="/stock", tags=["Stock Analyze"])
app.include_router(portfolio_router, prefix="/portfolio", tags=["Portfolio Analyze"])
app.include_router(company_router, prefix="/company", tags=["Company Describe"])
app.include_router(
    performance_router, prefix="/test/performance", tags=["Performance Test"]
)


@app.get("/")
async def root():
    return {"message": "Server is running!"}
