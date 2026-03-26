import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from .dto import StockAnalyzeRequest, StockAnalyzeResponse, ReportStreamRequest
from .recommend_dto import RecommendRequest, RecommendResponse
from .service import analyze_stock, recommend_stocks, score_stock_only

router = APIRouter()


@router.post("/analyze", response_model=StockAnalyzeResponse, response_model_by_alias=False)
def stock_analyze_endpoint(request: StockAnalyzeRequest):
    return analyze_stock(request)


@router.post("/score")
def stock_score_endpoint(request: StockAnalyzeRequest):
    """
    빠른 스코어링만 반환 — 뉴스/LLM 없음 (< 1초)

    프론트는 이 결과를 먼저 화면에 표시하고,
    이후 /stock/report/stream 으로 AI 리포트를 별도 요청한다.
    """
    return score_stock_only(request)


@router.post("/report/stream")
async def stock_report_stream_endpoint(request: ReportStreamRequest):
    """
    AI 투자 리포트를 SSE(Server-Sent Events)로 스트리밍

    이벤트 형식:
      data: {"type": "news_ready", "count": 5}       ← 뉴스 수집 완료 알림
      data: {"type": "token", "text": "삼성전자의 "}  ← 리포트 토큰
      data: {"type": "done"}                          ← 완료
    """
    async def event_generator():
        # 1. 뉴스 수집 + RAG (sync → thread pool)
        news_list = []
        try:
            from app.infrastructure.news_pipeline import collect_and_store_news
            from app.infrastructure.gemini_embedding_client import embed_text
            from app.infrastructure.pgvector_client import search_similar_news

            await asyncio.to_thread(
                collect_and_store_news, request.stock_code, request.stock_name, 10
            )
            query_vec = await asyncio.to_thread(
                embed_text, f"{request.stock_name} 투자 분석"
            )
            news_list = await asyncio.to_thread(
                search_similar_news, request.stock_code, query_vec, 5, 30
            )
            yield f"data: {json.dumps({'type': 'news_ready', 'count': len(news_list)}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'news_ready', 'count': 0}, ensure_ascii=False)}\n\n"

        # 2. Gemini 스트리밍 리포트
        from app.infrastructure.report_generator import generate_report_stream
        try:
            async for chunk in generate_report_stream(
                stock_code=request.stock_code,
                stock_name=request.stock_name,
                style_tag=request.style_tag,
                growth_score=request.growth_score,
                stability_score=request.stability_score,
                similarity_score=50.0,
                composite_score=request.composite_score,
                news_list=news_list,
            ):
                yield f"data: {json.dumps({'type': 'token', 'text': chunk}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'token', 'text': f'리포트 생성 중 오류가 발생했습니다: {str(e)}'}, ensure_ascii=False)}\n\n"

        yield 'data: {"type": "done"}\n\n'

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Nginx 버퍼링 비활성화
        },
    )


@router.post("/recommend", response_model=RecommendResponse)
def stock_recommend_endpoint(request: RecommendRequest):
    """
    사용자 포트폴리오 기반 종목 추천 (Step 3)

    사용자의 보유 종목 + 페르소나를 기반으로
    3,600+ 종목을 멀티팩터 스코어링하여 Top N 추천
    """
    return recommend_stocks(request)
