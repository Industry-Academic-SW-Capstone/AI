from pydantic import BaseModel, Field
from typing import List, Dict, Optional


# --- 요청 DTO ---
class PortfolioStock(BaseModel):
    """Spring 서버와의 연동을 위해 영문 필드명 사용 (한글도 alias로 지원)"""

    stock_code: str = Field(..., alias="단축코드")
    stock_name: Optional[str] = Field(
        None, alias="한글명"
    )  # Spring 서버에서 전달하는 종목명 (Optional)
    market_cap: float = Field(..., alias="시가총액")
    per: float
    pbr: float
    roe: float = Field(..., alias="ROE")
    debt_ratio: float = Field(..., alias="부채비율")
    dividend_yield: float = Field(..., alias="배당수익률")
    investment_amount: float = Field(..., alias="투자금액")

    class Config:
        populate_by_name = True  # 한글 필드명과 영문 필드명 둘 다 허용


class PortfolioAnalyzeRequest(BaseModel):
    stocks: List[PortfolioStock]


# --- 응답 DTO (final_analyzer.py에 맞춰 전면 수정) ---


class StockScoreDetail(BaseModel):
    """멀티팩터 스코어링 결과 (Step 3)"""
    growth_score: float
    stability_score: float
    similarity_score: float
    composite_score: float


class StockDetail(BaseModel):
    stock_code: str
    stock_name: str
    style_tag: str
    description: str  # '주린이 해설'이 여기에 담깁니다.
    scores: Optional[StockScoreDetail] = None  # Step 3: 멀티팩터 스코어


class StyleBreakdown(BaseModel):
    style_tag: str
    percentage: float


class PersonaMatch(BaseModel):
    name: str
    percentage: float
    philosophy: str  # '[근거: ...]'와 '철학'이 합쳐져 여기에 담깁니다.


class PortfolioAnalyzeResponse(BaseModel):
    stock_details: List[StockDetail]  # [1] 보유 종목 상세
    summary: Dict[str, float]  # [2] 종합 성향 ({"per": 15.86, ...})
    style_breakdown: List[StyleBreakdown]  # [3] 스타일 태그 비중
    persona_match: List[PersonaMatch]  # [4] 페르소나 일치율 (근거 + 철학 포함)
