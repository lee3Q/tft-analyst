"""메타 덱 조회 도구."""

from __future__ import annotations

import json

from ..data.store import load_decks


def get_meta(mode: str = "brief") -> str:
    """메타 덱 조회.

    Args:
        mode: "brief" (상위 5개) 또는 "full" (전체 티어 리스트)
    """
    decks = load_decks()
    if not decks:
        return json.dumps({"error": "메타 덱 데이터가 없습니다. 먼저 crawl을 실행하세요."}, ensure_ascii=False)

    # 통계 있는 덱 우선, 평균 순위 낮은 순 정렬 (0.0은 통계 없음 → 뒤로)
    decks.sort(key=lambda d: d.avg_placement if d.avg_placement > 0 else 99)

    if mode == "brief":
        decks = decks[:5]

    result = []
    for i, d in enumerate(decks):
        tier = _calc_tier(i, len(decks)) if mode == "full" else ""
        entry = {
            "rank": i + 1,
            "name": d.name,
            "core_champions": d.core_champions,
            "avg_placement": d.avg_placement,
            "first_rate": f"{d.first_rate:.0%}",
            "difficulty": d.difficulty,
            "synergy_tags": d.synergy_tags,
        }
        if tier:
            entry["tier"] = tier
        result.append(entry)

    return json.dumps(result, ensure_ascii=False, indent=2)


def _calc_tier(index: int, total: int) -> str:
    """순위 기반 티어 계산."""
    if total == 0:
        return "?"
    ratio = index / total
    if ratio < 0.15:
        return "S"
    elif ratio < 0.35:
        return "A"
    elif ratio < 0.60:
        return "B"
    else:
        return "C"
