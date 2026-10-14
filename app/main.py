from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ⛔️ 잘못된 경로 (컨테이너 안에서는 'domain'이 루트가 아님)
# from domain.stock_analyze.controller import router as stock_router
# from domain.portfolio_analyze.controller import router as portfolio_router

# ✅ 올바른 경로
from app.domain.stock_analyze.controller import router as stock_router
from app.domain.portfolio_analyze.controller import router as portfolio_router

app = FastAPI(
    title="Stock AI Analyze Server",
    version="0.2.0",
    description="AI 기반 주식 분석 서비스 (SPAC/우선주 필터링 + 멀티팩터 스코어링)",
)

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 origin만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    pass


app.include_router(stock_router, prefix="/stock", tags=["Stock Analyze"])
app.include_router(portfolio_router, prefix="/portfolio", tags=["Portfolio Analyze"])


@app.get("/")
async def root():
    return {"message": "Server is running!"}
