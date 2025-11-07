from pydantic import BaseModel
from typing import List, Dict

# --- 요청 DTO ---
class PortfolioStock(BaseModel):
    단축코드: str
    시가총액: float
    per: float
    pbr: float
    ROE: float
    부채비율: float
    배당수익률: float
    투자금액: float

class PortfolioAnalyzeRequest(BaseModel):
    stocks: List[PortfolioStock]


# --- 응답 DTO (final_analyzer.py에 맞춰 전면 수정) ---

class StockDetail(BaseModel):
    stock_code: str
    stock_name: str
    style_tag: str
    description: str  # '주린이 해설'이 여기에 담깁니다.

class StyleBreakdown(BaseModel):
    style_tag: str
    percentage: float

class PersonaMatch(BaseModel):
    name: str
    percentage: float
    philosophy: str  # '[근거: ...]'와 '철학'이 합쳐져 여기에 담깁니다.

class PortfolioAnalyzeResponse(BaseModel):
    stock_details: List[StockDetail]       # [1] 보유 종목 상세
    summary: Dict[str, float]              # [2] 종합 성향 ({"per": 15.86, ...})
    style_breakdown: List[StyleBreakdown]  # [3] 스타일 태그 비중
    persona_match: List[PersonaMatch]      # [4] 페르소나 일치율 (근거 + 철학 포함)