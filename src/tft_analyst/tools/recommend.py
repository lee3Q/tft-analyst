"""상황 기반 종합 추천 도구."""

from __future__ import annotations

import json

from ..data.models import Buildup, Deck
from ..data.store import load_buildups, load_decks


def recommend(
    champions: list[str],
    items: list[str] | None = None,
    level: int | None = None,
    gold: int | None = None,
    stage: str | None = None,
    hp: int | None = None,
    opponent_info: str | None = None,
) -> str:
    """상황 기반 추천.

    입력 범위에 따라 응답 깊이가 달라짐:
    - 챔피언만: 기본 덱 추천
    - +아이템: 아이템 고려 추천
    - +상대 정보: 상성/배치까지 분석

    초반 빌드업 vs 완성 덱은 챔피언 수와 맥락으로 자동 판단.
    """
    items = items or []
    buildups = load_buildups()
    decks = load_decks()

    # 초반/중반 판단: 빌드업 데이터에 매칭되면 초반, 아니면 중반
    buildup_matches = _match_buildups(champions, items, buildups)
    deck_matches = _match_decks(champions, items, decks)

    result: dict = {"input": {"champions": champions, "items": items}}

    if level:
        result["input"]["level"] = level
    if gold is not None:
        result["input"]["gold"] = gold
    if stage:
        result["input"]["stage"] = stage
    if hp is not None:
        result["input"]["hp"] = hp

    # 빌드업 추천 (초반)
    if buildup_matches:
        result["phase"] = "초반 (빌드업)"
        result["buildup_recommendations"] = buildup_matches

    # 완성 덱 추천 (중반 이후)
    if deck_matches:
        result["phase"] = result.get("phase", "") + " → 중반 (완성 덱)" if "phase" in result else "중반 (완성 덱)"

        # 안정 루트 vs 리스크 루트 분리
        stable = sorted(deck_matches, key=lambda d: d["avg_placement"])[:3]
        risky = sorted(deck_matches, key=lambda d: -d["first_rate"])[:3]

        result["stable_route"] = {
            "description": "순방 루트 — 평균 순위 안정적",
            "decks": stable,
        }
        result["risk_route"] = {
            "description": "도박 루트 — 1등 확률 높음",
            "decks": risky,
        }

    # 상대 정보가 있으면 배치 가이드 추가
    if opponent_info:
        result["positioning_guide"] = _positioning_guide(opponent_info)

    if not buildup_matches and not deck_matches:
        result["message"] = "매칭되는 덱/빌드업이 없습니다. 더 많은 정보를 입력해주세요."

    return json.dumps(result, ensure_ascii=False, indent=2)


def _match_buildups(champions: list[str], items: list[str], buildups: list[Buildup]) -> list[dict]:
    """보유 챔피언/아이템과 매칭되는 빌드업 찾기."""
    matches = []
    champ_set = {c.lower() for c in champions}

    for b in buildups:
        buildup_set = {c.lower() for c in b.champions}
        overlap = champ_set & buildup_set
        if not overlap:
            continue

        match_score = len(overlap) / len(buildup_set)
        missing = buildup_set - champ_set

        # 아이템 상성 확인
        item_notes = []
        for item in items:
            item_key = item.lower().replace(" ", "_")
            if item_key in b.item_matchups:
                item_notes.append(f"{item}: {b.item_matchups[item_key]}")

        matches.append({
            "name": b.name,
            "tier": b.tier,
            "match_score": round(match_score, 2),
            "missing_champions": list(missing),
            "item_notes": item_notes,
            "strong_against": b.strong_against,
            "weak_against": b.weak_against,
            "transition_decks": b.transition_decks,
        })

    matches.sort(key=lambda m: -m["match_score"])
    return matches[:5]


def _match_decks(champions: list[str], items: list[str], decks: list[Deck]) -> list[dict]:
    """보유 챔피언/아이템과 매칭되는 완성 덱 찾기."""
    matches = []
    champ_set = {c.lower() for c in champions}

    for d in decks:
        deck_set = {c.lower() for c in d.core_champions}
        overlap = champ_set & deck_set
        if not overlap:
            continue

        transition_cost = len(deck_set - champ_set)

        matches.append({
            "name": d.name,
            "avg_placement": d.avg_placement,
            "first_rate": d.first_rate,
            "difficulty": d.difficulty,
            "transition_cost": transition_cost,
            "missing_champions": list(deck_set - champ_set),
            "recommended_items": d.recommended_items,
            "recommended_augments": d.recommended_augments[:3],
            "synergy_tags": d.synergy_tags,
        })

    matches.sort(key=lambda m: (m["transition_cost"], m["avg_placement"]))
    return matches[:10]


def _positioning_guide(opponent_info: str) -> list[str]:
    """상대 정보 기반 배치 가이드 (규칙 기반)."""
    guides = []
    info_lower = opponent_info.lower()

    # 기본 배치 규칙
    if "암살자" in info_lower or "assassin" in info_lower:
        guides.append("상대에 암살자가 있으면: 딜러를 앞줄 중앙에 배치하여 백라인 침투 방지")
    if "블리츠" in info_lower or "blitz" in info_lower:
        guides.append("블리츠크랭크 대응: 가장 뒤 줄에 미끼 유닛 배치")
    if "제피르" in info_lower or "zephyr" in info_lower:
        guides.append("제피르 대응: 캐리 위치를 매 라운드 변경")

    if not guides:
        guides.append("상대 딜러 위치에 맞춰 탱커를 대각선으로 배치")
        guides.append("CC기 챔피언은 상대 캐리 사정거리 내에 배치")

    return guides
