from pydantic import BaseModel
from typing import List

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
    stocks: list[PortfolioStock]

class PortfolioAnalyzeResponse(BaseModel):
    portfolio_style_vector: list[float]
    summary: dict
    persona_match: dict
