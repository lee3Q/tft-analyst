"""TFT Analyst 데이터 모델."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass
class Deck:
    """완성 덱 데이터."""

    name: str
    core_champions: list[str]
    recommended_items: dict[str, list[str]]  # champion -> items
    avg_placement: float
    first_rate: float  # 1등 비율 (0~1)
    difficulty: str  # 상/중/하
    synergy_tags: list[str]
    recommended_augments: list[str]
    emblem_synergies: list[str]
    source: str = ""  # 데이터 출처
    patch: str = ""  # 패치 버전


@dataclass
class Buildup:
    """초반 빌드업 데이터."""

    name: str
    champions: list[str]
    tier: str  # S/A/B/C
    strong_against: list[str]
    weak_against: list[str]
    item_matchups: dict[str, str]  # item_key -> 상성 설명
    transition_decks: list[str]  # 전환 가능 완성 덱 이름


@dataclass
class GameRecord:
    """게임 결과 기록."""

    date: str  # YYYY-MM-DD
    placement: int
    deck_used: str
    items: list[str] = field(default_factory=list)
    augments: list[str] = field(default_factory=list)
    mistakes: list[str] = field(default_factory=list)
    notes: str = ""

    @staticmethod
    def today() -> str:
        return date.today().isoformat()
