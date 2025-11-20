from pydantic import BaseModel
from typing import List


class PerformanceTestRequest(BaseModel):
    """성능 테스트 요청"""
    company_names: List[str]  # 테스트할 기업 리스트
    request_count: int = 100  # 반복 횟수 (기본값: 100)


class PerformanceMetrics(BaseModel):
    """성능 지표"""
    avg_time_ms: float  # 평균 응답 시간 (ms)
    min_time_ms: float  # 최소 응답 시간 (ms)
    max_time_ms: float  # 최대 응답 시간 (ms)
    total_time_ms: float  # 총 소요 시간 (ms)
    cache_hits: int  # 캐시 히트 수
    cache_misses: int  # 캐시 미스 수
    cache_hit_rate: float  # 캐시 히트율 (%)


class PerformanceComparisonResponse(BaseModel):
    """성능 비교 결과"""
    test_config: dict  # 테스트 설정 정보
    with_cache: PerformanceMetrics  # 캐시 사용 O
    without_cache: PerformanceMetrics  # 캐시 사용 X
    improvement: dict  # 개선 효과

