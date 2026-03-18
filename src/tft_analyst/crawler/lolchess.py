"""lolchess.gg 크롤러 — tft.dakgg.io API 사용."""

from __future__ import annotations

import httpx

from ..data.models import Deck

API_BASE = "https://tft.dakgg.io/api/v1"
HEADERS = {"User-Agent": "tft-analyst/0.1"}


async def crawl_lolchess(patch: str | None = None) -> list[Deck]:
    """lolchess.gg에서 메타 덱 데이터 수집.

    두 가지 소스를 병합:
    1. /guide-decks — 에디터 큐레이션 덱 (아이템/배치 상세)
    2. /meta-deck-exalted — 데이터 기반 메타 덱 (승률/순위 통계)
    """
    async with httpx.AsyncClient(headers=HEADERS, timeout=30) as client:
        guide_decks = await _fetch_guide_decks(client)
        meta_decks = await _fetch_meta_decks(client, patch)

    # 가이드 덱에 통계 데이터 보강
    all_decks = _merge_decks(guide_decks, meta_decks, patch)
    return all_decks


async def _fetch_guide_decks(client: httpx.AsyncClient) -> list[dict]:
    """에디터 추천 가이드 덱 조회."""
    resp = await client.get(f"{API_BASE}/guide-decks", params={"q": "live"})
    resp.raise_for_status()
    data = resp.json()
    return data.get("guideDecks", [])


async def _fetch_meta_decks(client: httpx.AsyncClient, patch: str | None) -> list[dict]:
    """메타 덱 통계 조회."""
    resp = await client.get(f"{API_BASE}/meta-deck-exalted")
    resp.raise_for_status()
    data = resp.json()

    meta = data.get("metaDeckExalted", {})
    return meta.get("metaDeckExaltedStats", [])


def _merge_decks(guide_decks: list[dict], meta_decks: list[dict], patch: str | None) -> list[Deck]:
    """가이드 덱과 메타 덱 통계를 병합하여 Deck 리스트 생성."""
    decks: list[Deck] = []

    # 1. 가이드 덱 변환
    for gd in guide_decks:
        slots = gd.get("data", {}).get("slots", [])
        champions = []
        items_map: dict[str, list[str]] = {}

        for slot in slots:
            champ = slot.get("champion", "")
            if champ:
                champions.append(champ)
                slot_items = slot.get("items", [])
                if slot_items:
                    items_map[champ] = slot_items

        if not champions:
            continue

        decks.append(Deck(
            name=gd.get("name", "Unknown"),
            core_champions=champions,
            recommended_items=items_map,
            avg_placement=0.0,  # 가이드 덱은 통계 없음
            first_rate=0.0,
            difficulty="중",
            synergy_tags=[],
            recommended_augments=[],
            emblem_synergies=[],
            source="lolchess-guide",
            patch=patch or gd.get("season", ""),
        ))

    # 2. 메타 덱 통계 변환
    for md in meta_decks:
        champions = md.get("keys", [])
        if not champions:
            continue

        plays = md.get("plays", 0)
        wins = md.get("wins", 0)
        tops = md.get("tops", 0)

        first_rate = wins / plays if plays > 0 else 0
        avg_placement = md.get("avgPlacement", 0)

        # 이름 생성: 코어 챔피언 기반
        name = " ".join(champions[:3]) + " 덱"

        decks.append(Deck(
            name=name,
            core_champions=champions,
            recommended_items={},
            avg_placement=round(avg_placement, 2),
            first_rate=round(first_rate, 4),
            difficulty=_estimate_difficulty(len(champions), avg_placement),
            synergy_tags=[],
            recommended_augments=[],
            emblem_synergies=[],
            source="lolchess-meta",
            patch=patch or "",
        ))

    return decks


def _estimate_difficulty(champ_count: int, avg_placement: float) -> str:
    """덱 난이도 추정."""
    if champ_count >= 8:
        return "상"
    elif avg_placement <= 3.5:
        return "중"
    else:
        return "하"
