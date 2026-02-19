from fastapi import APIRouter
from .dto import StockAnalyzeRequest, StockAnalyzeResponse
from .recommend_dto import RecommendRequest, RecommendResponse
from .service import analyze_stock, recommend_stocks

router = APIRouter()


@router.post("/analyze", response_model=StockAnalyzeResponse, response_model_by_alias=False)
def stock_analyze_endpoint(request: StockAnalyzeRequest):
    return analyze_stock(request)


@router.post("/recommend", response_model=RecommendResponse)
def stock_recommend_endpoint(request: RecommendRequest):
    """
    사용자 포트폴리오 기반 종목 추천 (Step 3)

    사용자의 보유 종목 + 페르소나를 기반으로
    3,600+ 종목을 멀티팩터 스코어링하여 Top N 추천
    """
    return recommend_stocks(request)
