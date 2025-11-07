from fastapi import APIRouter
from .dto import PortfolioAnalyzeRequest, PortfolioAnalyzeResponse
from .service import analyze_portfolio

router = APIRouter()

@router.post("/analyze", response_model=PortfolioAnalyzeResponse)
def portfolio_analyze_endpoint(request: PortfolioAnalyzeRequest):
    return analyze_portfolio(request)
