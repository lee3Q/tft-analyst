"""게임 결과 기록 도구."""

from __future__ import annotations

import json

from ..data.models import GameRecord
from ..data.store import add_game


def record_game(
    placement: int,
    deck_used: str,
    items: list[str] | None = None,
    augments: list[str] | None = None,
    mistakes: list[str] | None = None,
    notes: str = "",
) -> str:
    """게임 결과 기록.

    페르소나가 세션 대화에서 자동 추출한 정보를 저장.
    """
    record = GameRecord(
        date=GameRecord.today(),
        placement=placement,
        deck_used=deck_used,
        items=items or [],
        augments=augments or [],
        mistakes=mistakes or [],
        notes=notes,
    )
    add_game(record)

    return json.dumps({
        "status": "recorded",
        "summary": {
            "date": record.date,
            "placement": record.placement,
            "deck": record.deck_used,
            "mistakes_count": len(record.mistakes),
        },
    }, ensure_ascii=False, indent=2)
