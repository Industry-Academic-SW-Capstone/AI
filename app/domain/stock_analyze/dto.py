from pydantic import BaseModel, Field
from typing import List


class StockAnalyzeRequest(BaseModel):
    """Spring 서버와의 연동을 위해 영문 필드명 사용 (한글도 alias로 지원)"""

    stock_code: str = Field(..., alias="단축코드")
    market_cap: float = Field(..., alias="시가총액")
    per: float
    pbr: float
    roe: float = Field(..., alias="ROE")
    debt_ratio: float = Field(..., alias="부채비율")
    dividend_yield: float = Field(..., alias="배당수익률")

    class Config:
        populate_by_name = True  # 한글 필드명과 영문 필드명 둘 다 허용


class StockAnalyzeResponse(BaseModel):
    """Spring 서버가 기대하는 응답 형식"""

    stock_code: str = Field(..., alias="단축코드")
    stock_name: str = Field(..., alias="한글명")
    style_tag: str = Field(..., alias="final_style_tag")
    style_description: str

    class Config:
        populate_by_name = True  # 한글 필드명과 영문 필드명 둘 다 허용
        json_schema_extra = {
            "example": {
                "stock_code": "005930",
                "stock_name": "삼성전자",
                "style_tag": "[초대형 우량주]",
                "style_description": "대한민국 대표 우량주...",
            }
        }
