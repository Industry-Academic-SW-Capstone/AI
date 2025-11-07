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
    한글명: str  # [추가됨]
    final_style_tag: str
    style_description: str # '주린이 해설'이 여기에 담깁니다.