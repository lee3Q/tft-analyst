"""빌드업 데이터 등록/관리 도구."""

from __future__ import annotations

import json

from ..data.models import Buildup
from ..data.store import add_buildup as store_add_buildup, load_buildups


def add_buildup(
    name: str,
    champions: list[str],
    tier: str,
    strong_against: list[str] | None = None,
    weak_against: list[str] | None = None,
    item_matchups: dict[str, str] | None = None,
    transition_decks: list[str] | None = None,
) -> str:
    """빌드업 데이터 등록. 같은 이름이면 덮어쓰기."""
    buildup = Buildup(
        name=name,
        champions=champions,
        tier=tier,
        strong_against=strong_against or [],
        weak_against=weak_against or [],
        item_matchups=item_matchups or {},
        transition_decks=transition_decks or [],
    )
    store_add_buildup(buildup)

    return json.dumps({
        "status": "saved",
        "buildup": {
            "name": buildup.name,
            "champions": buildup.champions,
            "tier": buildup.tier,
        },
    }, ensure_ascii=False, indent=2)


def list_buildups() -> str:
    """등록된 빌드업 목록 조회."""
    buildups = load_buildups()
    if not buildups:
        return json.dumps({"message": "등록된 빌드업이 없습니다."}, ensure_ascii=False)

    result = []
    for b in sorted(buildups, key=lambda x: ("SABC".index(x.tier) if x.tier in "SABC" else 99)):
        result.append({
            "name": b.name,
            "tier": b.tier,
            "champions": b.champions,
            "transition_decks": b.transition_decks,
        })

    return json.dumps(result, ensure_ascii=False, indent=2)
