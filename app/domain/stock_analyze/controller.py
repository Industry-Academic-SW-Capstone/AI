from fastapi import APIRouter
from .dto import StockAnalyzeRequest, StockAnalyzeResponse
from .service import analyze_stock

router = APIRouter()

@router.post("/analyze", response_model=StockAnalyzeResponse)
def stock_analyze_endpoint(request: StockAnalyzeRequest):
    return analyze_stock(request)
