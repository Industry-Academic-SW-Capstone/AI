from fastapi import APIRouter, HTTPException
from .dto import CompanyDescribeRequest, CompanyDescribeResponse
from .service import get_company_description

router = APIRouter()


@router.post("/describe", response_model=CompanyDescribeResponse)
async def describe_company(request: CompanyDescribeRequest):
    """
    기업명을 받아 Gemini LLM을 활용하여 두 문장 요약을 생성합니다.
    Redis 캐시를 사용하여 API 호출을 최소화합니다 (TTL: 3시간).
    """
    try:
        description, cached = get_company_description(request.한글명)
        
        return CompanyDescribeResponse(
            한글명=request.한글명,
            description=description,
            cached=cached
        )
    except Exception as e:
        print(f"기업 설명 생성 오류: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"기업 설명 생성에 실패했습니다: {str(e)}"
        )

