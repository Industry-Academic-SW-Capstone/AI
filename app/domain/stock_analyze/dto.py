from pydantic import BaseModel
from typing import List

class StockAnalyzeRequest(BaseModel):
    단축코드: str
    시가총액: float
    per: float
    pbr: float
    ROE: float
    부채비율: float
    배당수익률: float

class StockAnalyzeResponse(BaseModel):
    단축코드: str
    final_style_tag: str
    style_description: str
