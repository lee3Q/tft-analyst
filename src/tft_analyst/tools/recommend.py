"""상황 기반 종합 추천 도구."""

from __future__ import annotations

import json

from ..data.models import Buildup, Champion, Deck
from ..data.store import get_champion, load_buildups, load_champions, load_decks


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
        stable = sorted(deck_matches, key=lambda d: d["avg_placement"] if d["avg_placement"] > 0 else 99)[:3]
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
    """상대 정보 기반 배치 가이드 — 챔피언 스킬 데이터 기반."""
    guides = []
    champions = load_champions()
    champ_by_name = {c.name.lower(): c for c in champions}

    # 상대 정보에서 챔피언 이름 추출
    mentioned_champs: list[Champion] = []
    for name, champ in champ_by_name.items():
        if name in opponent_info.lower():
            mentioned_champs.append(champ)

    # 챔피언 스킬 데이터 기반 배치 가이드
    for champ in mentioned_champs:
        # CC기 챔피언 대응
        if champ.has_cc:
            if champ.skill_target == "farthest":
                guides.append(f"{champ.name} 대응: 스킬이 가장 먼 대상 타겟 ({champ.cc_type} {champ.cc_duration}초) → 캐리를 가까이 배치")
            elif champ.skill_target == "nearest":
                guides.append(f"{champ.name} 대응: 스킬이 가장 가까운 대상 타겟 ({champ.cc_type} {champ.cc_duration}초) → 탱커로 스킬 받기")
            elif champ.skill_target == "aoe":
                guides.append(f"{champ.name} 대응: 광역 {champ.cc_type} (범위 {champ.skill_range}칸) → 유닛을 분산 배치")
            elif champ.skill_target == "lowest_hp":
                guides.append(f"{champ.name} 대응: 체력 낮은 대상 타겟 → 캐리 체력 아이템 고려")
            else:
                guides.append(f"{champ.name}: {champ.cc_type} {champ.cc_duration}초 ({champ.skill_target} 타겟) 주의")

        # 뒷라인 위협 챔피언 대응
        if champ.is_backline_threat and not champ.has_cc:
            if champ.role == "assassin":
                guides.append(f"{champ.name} (암살자): 캐리를 앞줄 또는 중앙으로 이동하여 점프 방지")
            else:
                guides.append(f"{champ.name}: 뒷라인 위협 — 캐리 위치 조정 필요")

    # 시너지 기반 가이드
    if "암살자" in opponent_info.lower() or "assassin" in opponent_info.lower():
        if not any("암살자" in g for g in guides):
            guides.append("암살자 시너지 대응: 캐리를 앞줄/중앙에 배치, 뒤쪽에 미끼 유닛")

    # 가이드가 없으면 일반 조언
    if not guides:
        if champions:
            guides.append("상대 챔피언의 스킬 타겟 방식을 확인하고 그에 맞게 배치를 조정하세요")
        else:
            guides.append("챔피언 데이터가 없습니다. 챔피언 데이터를 먼저 등록해주세요.")

    return guides
