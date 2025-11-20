from fastapi import APIRouter, HTTPException
from .dto import PerformanceTestRequest, PerformanceComparisonResponse
from .service import (
    run_performance_test_with_cache,
    run_performance_test_without_cache,
    calculate_improvement
)

router = APIRouter()


@router.post("/compare", response_model=PerformanceComparisonResponse)
async def compare_performance(request: PerformanceTestRequest):
    """
    Redis 캐시 사용 O vs 사용 X 성능 비교 테스트
    
    **주의**: 캐시 없는 테스트는 Gemini API를 많이 호출하므로 무료 한도에 주의하세요!
    
    **예시 요청**:
    ```json
    {
        "company_names": ["삼성전자", "SK하이닉스", "NAVER", "카카오"],
        "request_count": 100
    }
    ```
    
    **테스트 시나리오**:
    - 지정한 기업들을 순회하며 총 request_count 번 조회
    - 예: 기업 4개, 100회 요청 → 각 기업당 25회씩 조회
    """
    try:
        # 1. 캐시 사용 O 테스트
        print(f"[테스트 시작] 캐시 사용 O - {request.request_count}회")
        with_cache_metrics = run_performance_test_with_cache(
            request.company_names,
            request.request_count
        )
        
        # 2. 캐시 사용 X 테스트
        print(f"[테스트 시작] 캐시 사용 X - {request.request_count}회")
        without_cache_metrics = run_performance_test_without_cache(
            request.company_names,
            request.request_count
        )
        
        # 3. 개선 효과 계산
        improvement = calculate_improvement(with_cache_metrics, without_cache_metrics)
        
        return PerformanceComparisonResponse(
            test_config={
                "company_names": request.company_names,
                "company_count": len(request.company_names),
                "request_count": request.request_count,
                "requests_per_company": request.request_count // len(request.company_names)
            },
            with_cache=with_cache_metrics,
            without_cache=without_cache_metrics,
            improvement=improvement
        )
    except Exception as e:
        print(f"성능 테스트 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"성능 테스트 실행 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/health")
async def performance_test_health():
    """성능 테스트 모듈 헬스 체크"""
    return {
        "status": "healthy",
        "message": "Performance test module is ready",
        "endpoints": [
            "/test/performance/compare - Redis 캐시 성능 비교 테스트"
        ]
    }

