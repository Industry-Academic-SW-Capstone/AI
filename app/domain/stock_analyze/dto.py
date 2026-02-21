from pydantic import BaseModel, Field
from typing import List, Optional


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


class ScoreDetail(BaseModel):
    """멀티팩터 스코어링 결과 (Step 3)"""
    growth_score: float = Field(..., description="성장성 점수 (0~100)")
    stability_score: float = Field(..., description="안정성 점수 (0~100)")
    similarity_score: float = Field(..., description="코사인 유사도 점수 (0~100)")
    composite_score: float = Field(..., description="종합 점수 (0~100)")


class StockAnalyzeResponse(BaseModel):
    """Spring 서버가 기대하는 응답 형식 (SPAC/우선주 필터링 + 스코어링 포함)"""

    stock_code: str = Field(..., alias="단축코드")
    stock_name: str = Field(..., alias="한글명")
    final_style_tag: Optional[str] = Field(None, alias="style_tag")  # 분석 불가 시 None
    style_description: Optional[str] = None  # 분석 불가 시 None
    analyzable: bool  # ✅ 추가: 분석 가능 여부
    reason: Optional[str] = None  # ✅ 추가: 분석 불가 사유
    scores: Optional[ScoreDetail] = None  # ✅ Step 3: 멀티팩터 스코어
    report: Optional[str] = None  # ✅ Step 4: AI 투자 분석 리포트

    class Config:
        populate_by_name = True  # 한글 필드명과 영문 필드명 둘 다 허용
        json_schema_extra = {
            "example": {
                "stock_code": "005930",
                "stock_name": "삼성전자",
                "final_style_tag": "[초대형 우량주]",
                "style_description": "대한민국 대표 우량주...",
                "analyzable": True,
                "reason": None,
                "scores": {
                    "growth_score": 65.0,
                    "stability_score": 72.5,
                    "similarity_score": 50.0,
                    "composite_score": 62.75,
                },
            }
        }
