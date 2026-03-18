"""TFT Analyst MCP 서버."""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from .tools.add_buildup import add_buildup as _add_buildup, list_buildups as _list_buildups
from .tools.get_meta import get_meta as _get_meta
from .tools.get_stats import get_stats as _get_stats
from .tools.quiz import quiz as _quiz
from .tools.recommend import recommend as _recommend
from .tools.record_game import record_game as _record_game

mcp = FastMCP("tft-analyst", instructions="TFT 분석가 도구. 메타 덱 조회, 상황 추천, 게임 기록, 통계, 퀴즈 제공.")


@mcp.tool()
def crawl(source: str = "all") -> str:
    """크롤링 실행. source: 'lolchess', 'metatft', 'all'

    패치마다 수동 트리거. CLI에서 tft-crawl 명령어를 사용하세요.
    MCP 도구로는 현재 크롤링 상태 확인만 가능합니다.
    """
    from .data.store import load_decks
    decks = load_decks()
    return json.dumps({
        "message": "크롤링은 CLI(tft-crawl)로 실행하세요.",
        "current_data": {
            "decks_count": len(decks),
            "patch": decks[0].patch if decks else "없음",
        },
    }, ensure_ascii=False, indent=2)


@mcp.tool()
def get_meta(mode: str = "brief") -> str:
    """메타 덱 조회. mode: 'brief' (상위 5개) 또는 'full' (전체 티어 리스트)"""
    return _get_meta(mode)


@mcp.tool()
def recommend(
    champions: list[str],
    items: list[str] | None = None,
    level: int | None = None,
    gold: int | None = None,
    stage: str | None = None,
    hp: int | None = None,
    opponent_info: str | None = None,
) -> str:
    """상황 기반 종합 추천.

    - 기본: 챔피언 → 덱/빌드업 추천 (리스크 vs 안정)
    - +아이템: 아이템 상성 고려
    - +상대 정보: 배치 가이드 포함
    - 초반/중반 자동 판단
    """
    return _recommend(champions, items, level, gold, stage, hp, opponent_info)


@mcp.tool()
def record_game(
    placement: int,
    deck_used: str,
    items: list[str] | None = None,
    augments: list[str] | None = None,
    mistakes: list[str] | None = None,
    notes: str = "",
) -> str:
    """게임 결과 기록. 순위, 사용 덱, 아이템, 증강, 실수, 메모 저장."""
    return _record_game(placement, deck_used, items, augments, mistakes, notes)


@mcp.tool()
def get_stats() -> str:
    """누적 게임 통계 조회. 전체 평균 순위, 덱별 통계, 자주 하는 실수 등."""
    return _get_stats()


@mcp.tool()
def quiz() -> str:
    """패치 브리핑 + 빌드업 퀴즈. 게임 전 메타 핵심 확인용."""
    return _quiz()


@mcp.tool()
def add_buildup(
    name: str,
    champions: list[str],
    tier: str,
    strong_against: list[str] | None = None,
    weak_against: list[str] | None = None,
    item_matchups: str | None = None,
    transition_decks: list[str] | None = None,
) -> str:
    """빌드업 데이터 등록. 이름, 챔피언, 티어, 상성, 아이템 상성, 전환 덱.

    item_matchups는 JSON 문자열: '{"no_item": "설명", "recurve_bow": "설명"}'
    """
    parsed_matchups = json.loads(item_matchups) if item_matchups else None
    return _add_buildup(name, champions, tier, strong_against, weak_against, parsed_matchups, transition_decks)


@mcp.tool()
def list_buildups() -> str:
    """등록된 빌드업 목록 조회."""
    return _list_buildups()


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
