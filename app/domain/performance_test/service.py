import time
import statistics
from typing import List
from ..company_describe.service import (
    get_company_description,
    get_company_description_no_cache,
)
from .dto import PerformanceMetrics


def run_performance_test_with_cache(
    company_names: List[str], request_count: int
) -> PerformanceMetrics:
    """
    캐시를 사용하는 성능 테스트
    """
    times = []
    cache_hits = 0
    cache_misses = 0

    for i in range(request_count):
        # 각 반복마다 기업 리스트를 순회
        company_name = company_names[i % len(company_names)]

        start_time = time.time()
        try:
            description, cached = get_company_description(company_name, use_cache=True)
            if cached:
                cache_hits += 1
            else:
                cache_misses += 1
        except Exception as e:
            print(f"Error: {e}")
            cache_misses += 1
        end_time = time.time()

        elapsed_ms = (end_time - start_time) * 1000
        times.append(elapsed_ms)

    return PerformanceMetrics(
        avg_time_ms=round(statistics.mean(times), 3),
        min_time_ms=round(min(times), 3),
        max_time_ms=round(max(times), 3),
        total_time_ms=round(sum(times), 3),
        cache_hits=cache_hits,
        cache_misses=cache_misses,
        cache_hit_rate=(
            round((cache_hits / request_count) * 100, 2) if request_count > 0 else 0
        ),
    )


def run_performance_test_without_cache(
    company_names: List[str], request_count: int
) -> PerformanceMetrics:
    """
    캐시를 사용하지 않는 성능 테스트
    """
    times = []

    for i in range(request_count):
        # 각 반복마다 기업 리스트를 순회
        company_name = company_names[i % len(company_names)]

        start_time = time.time()
        try:
            description = get_company_description_no_cache(company_name)
        except Exception as e:
            print(f"Error: {e}")
        end_time = time.time()

        elapsed_ms = (end_time - start_time) * 1000
        times.append(elapsed_ms)

    return PerformanceMetrics(
        avg_time_ms=round(statistics.mean(times), 3),
        min_time_ms=round(min(times), 3),
        max_time_ms=round(max(times), 3),
        total_time_ms=round(sum(times), 3),
        cache_hits=0,
        cache_misses=request_count,
        cache_hit_rate=0,
    )


def calculate_improvement(
    with_cache: PerformanceMetrics, without_cache: PerformanceMetrics
) -> dict:
    """
    개선 효과 계산
    """
    speed_improvement = (
        round(without_cache.avg_time_ms / with_cache.avg_time_ms, 1)
        if with_cache.avg_time_ms > 0
        else 0
    )
    time_reduction_percent = (
        round(
            (
                (without_cache.avg_time_ms - with_cache.avg_time_ms)
                / without_cache.avg_time_ms
            )
            * 100,
            1,
        )
        if without_cache.avg_time_ms > 0
        else 0
    )

    return {
        "speed_improvement": f"{speed_improvement}배",
        "avg_time_reduction": f"{without_cache.avg_time_ms - with_cache.avg_time_ms:.3f}ms",
        "time_reduction_percent": f"{time_reduction_percent}%",
        "total_time_saved": f"{without_cache.total_time_ms - with_cache.total_time_ms:.3f}ms",
        "api_calls_reduced": with_cache.cache_hits,
        "api_call_reduction_percent": f"{with_cache.cache_hit_rate}%",
    }
