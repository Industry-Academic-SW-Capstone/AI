from pydantic import BaseModel


class CompanyDescribeRequest(BaseModel):
    """기업 설명 요청"""

    한글명: str


class CompanyDescribeResponse(BaseModel):
    """기업 설명 응답"""

    한글명: str
    description: str
    cached: bool = False  # 캐시에서 가져왔는지 여부
