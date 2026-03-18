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
class Champion:
    """챔피언 스킬/특성 데이터 (Set 16 기준)."""

    name: str
    cost: int  # 1~5 코스트
    synergies: list[str]  # 시너지 태그
    skill_name: str
    skill_description: str  # 스킬 효과 요약
    skill_range: int  # 스킬 사거리 (칸 수, 0=자기자신)
    skill_target: str  # 타겟 방식: "nearest", "farthest", "lowest_hp", "highest_hp", "aoe", "self", "random", "line" 등
    cc_type: str = ""  # CC 종류: "stun", "knockup", "pull", "slow", "silence", "taunt", "disarm", "" (없음)
    cc_duration: float = 0.0  # CC 지속시간 (초)
    damage_type: str = "physical"  # "physical", "magic", "true"
    attack_range: int = 1  # 기본 공격 사거리 (칸)
    role: str = ""  # "tank", "carry", "support", "assassin" 등

    @property
    def has_cc(self) -> bool:
        return bool(self.cc_type)

    @property
    def is_backline_threat(self) -> bool:
        """뒷라인을 위협하는 챔피언인지."""
        return self.skill_target in ("farthest", "lowest_hp") or self.role == "assassin"


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
