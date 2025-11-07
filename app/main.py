from fastapi import FastAPI
from domain.stock_analyze.controller import router as stock_router
from domain.portfolio_analyze.controller import router as portfolio_router

app = FastAPI(title="Stock AI Analyze Server")

# 라우터 등록
app.include_router(stock_router, prefix="/stock", tags=["Stock Analyze"])
app.include_router(portfolio_router, prefix="/portfolio", tags=["Portfolio Analyze"])

# 루트 엔드포인트
@app.get("/")
async def root():
    return {"message": "Server is running!"}
