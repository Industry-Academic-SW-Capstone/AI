from fastapi import FastAPI
# ⛔️ 잘못된 경로 (컨테이너 안에서는 'domain'이 루트가 아님)
# from domain.stock_analyze.controller import router as stock_router
# from domain.portfolio_analyze.controller import router as portfolio_router

# ✅ 올바른 경로
from app.domain.stock_analyze.controller import router as stock_router
from app.domain.portfolio_analyze.controller import router as portfolio_router

from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(title="Stock AI Analyze Server")

Instrumentator().instrument(app).expose(app)

@app.on_event("startup")
async def startup():
    pass

app.include_router(stock_router, prefix="/stock", tags=["Stock Analyze"])
app.include_router(portfolio_router, prefix="/portfolio", tags=["Portfolio Analyze"])

@app.get("/")
async def root():
    return {"message": "Server is running!"}
