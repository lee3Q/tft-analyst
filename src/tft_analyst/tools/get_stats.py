"""누적 통계 조회 도구."""

from __future__ import annotations

import json

from ..data.store import get_stats as store_get_stats


def get_stats() -> str:
    """누적 게임 통계 조회."""
    return json.dumps(store_get_stats(), ensure_ascii=False, indent=2)
