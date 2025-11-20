from fastapi import APIRouter
from .dto import StockAnalyzeRequest, StockAnalyzeResponse
from .service import analyze_stock

router = APIRouter()

@router.post("/analyze", response_model=StockAnalyzeResponse, response_model_by_alias=False)
def stock_analyze_endpoint(request: StockAnalyzeRequest):
    return analyze_stock(request)
