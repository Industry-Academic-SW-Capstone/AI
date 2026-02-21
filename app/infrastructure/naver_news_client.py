"""
네이버 검색 API (뉴스) 클라이언트
- 종목명 기반 뉴스 검색
- HTML 태그 제거 + 날짜 파싱
"""

import os
import re
import logging
from datetime import datetime

import requests

logger = logging.getLogger(__name__)

NAVER_SEARCH_URL = "https://openapi.naver.com/v1/search/news.json"


def _strip_html(text: str) -> str:
    """HTML 태그 및 엔티티 제거"""
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&quot;", '"').replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    return text.strip()


def _parse_pub_date(date_str: str) -> datetime | None:
    """네이버 API 날짜 형식 파싱 (예: 'Thu, 20 Feb 2026 09:00:00 +0900')"""
    try:
        return datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
    except (ValueError, TypeError):
        return None


def search_news(
    query: str,
    display: int = 20,
    sort: str = "date",
) -> list[dict]:
    """
    네이버 뉴스 검색

    Args:
        query: 검색어 (예: '삼성전자 주식')
        display: 검색 결과 수 (최대 100)
        sort: 정렬 기준 ('date': 최신순, 'sim': 정확도순)

    Returns:
        [{"title", "description", "link", "pub_date"(datetime)}]
    """
    client_id = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")

    if not client_id or not client_secret:
        logger.error("NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 환경변수가 설정되지 않았습니다")
        return []

    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
    }
    params = {
        "query": query,
        "display": min(display, 100),
        "start": 1,
        "sort": sort,
    }

    try:
        resp = requests.get(NAVER_SEARCH_URL, headers=headers, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        logger.error("네이버 뉴스 검색 실패: %s", e)
        return []

    results = []
    for item in data.get("items", []):
        results.append({
            "title": _strip_html(item.get("title", "")),
            "description": _strip_html(item.get("description", "")),
            "link": item.get("originallink") or item.get("link", ""),
            "pub_date": _parse_pub_date(item.get("pubDate")),
        })

    logger.info("네이버 뉴스 검색 '%s': %d건", query, len(results))
    return results


def search_stock_news(stock_name: str, display: int = 20) -> list[dict]:
    """
    종목명 기반 주식 뉴스 검색 (검색어에 '주식' 추가)

    Args:
        stock_name: 종목명 (예: '삼성전자')
        display: 결과 수

    Returns:
        뉴스 리스트
    """
    return search_news(f"{stock_name} 주식", display=display, sort="date")
