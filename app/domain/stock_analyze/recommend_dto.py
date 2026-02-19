from pydantic import BaseModel, Field
from typing import List, Optional


class RecommendStock(BaseModel):
    """추천 요청 시 사용자 보유 종목 정보"""
    stock_code: str
    market_cap: float
    per: float
    pbr: float
    roe: float
    debt_ratio: float
    dividend_yield: float
    investment_amount: float


class RecommendRequest(BaseModel):
    """추천 요청 DTO"""
    stocks: List[RecommendStock] = Field(..., description="사용자 보유 종목 리스트")
    persona: Optional[str] = Field(None, description="페르소나 이름 (예: '워렌 버핏')")
    top_n: int = Field(10, description="추천 종목 수", ge=1, le=50)


class RecommendStockResult(BaseModel):
    """추천 결과 개별 종목"""
    stock_code: str
    stock_name: str
    style_tag: str
    growth_score: float
    stability_score: float
    similarity_score: float
    composite_score: float


class RecommendResponse(BaseModel):
    """추천 응답 DTO"""
    persona: Optional[str] = Field(None, description="적용된 페르소나")
    total_scored: int = Field(..., description="스코어링 대상 총 종목 수")
    recommendations: List[RecommendStockResult]
