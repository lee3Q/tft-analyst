"""로컬 JSON 파일 기반 데이터 저장소."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .models import Buildup, Deck, GameRecord

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"


def _ensure_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _read_json(filename: str) -> list[dict]:
    path = DATA_DIR / filename
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(filename: str, data: list[dict]) -> None:
    _ensure_dir()
    path = DATA_DIR / filename
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# --- Decks ---

def load_decks() -> list[Deck]:
    return [Deck(**d) for d in _read_json("decks.json")]


def save_decks(decks: list[Deck]) -> None:
    _write_json("decks.json", [asdict(d) for d in decks])


# --- Buildups ---

def load_buildups() -> list[Buildup]:
    return [Buildup(**b) for b in _read_json("buildups.json")]


def save_buildups(buildups: list[Buildup]) -> None:
    _write_json("buildups.json", [asdict(b) for b in buildups])


def add_buildup(buildup: Buildup) -> None:
    buildups = load_buildups()
    # 같은 이름이면 덮어쓰기
    buildups = [b for b in buildups if b.name != buildup.name]
    buildups.append(buildup)
    save_buildups(buildups)


# --- Game Records ---

def load_games() -> list[GameRecord]:
    return [GameRecord(**g) for g in _read_json("games.json")]


def save_games(games: list[GameRecord]) -> None:
    _write_json("games.json", [asdict(g) for g in games])


def add_game(record: GameRecord) -> None:
    games = load_games()
    games.append(record)
    save_games(games)


# --- Stats ---

def get_stats() -> dict:
    """누적 통계 계산."""
    games = load_games()
    if not games:
        return {"total_games": 0, "message": "기록된 게임이 없습니다."}

    total = len(games)
    avg_placement = sum(g.placement for g in games) / total
    top4_rate = sum(1 for g in games if g.placement <= 4) / total
    first_rate = sum(1 for g in games if g.placement == 1) / total

    # 덱별 통계
    deck_stats: dict[str, dict] = {}
    for g in games:
        if g.deck_used not in deck_stats:
            deck_stats[g.deck_used] = {"games": 0, "total_placement": 0, "firsts": 0}
        ds = deck_stats[g.deck_used]
        ds["games"] += 1
        ds["total_placement"] += g.placement
        ds["firsts"] += 1 if g.placement == 1 else 0

    deck_summary = []
    for name, ds in sorted(deck_stats.items(), key=lambda x: x[1]["total_placement"] / x[1]["games"]):
        deck_summary.append({
            "deck": name,
            "games": ds["games"],
            "avg_placement": round(ds["total_placement"] / ds["games"], 2),
            "first_rate": round(ds["firsts"] / ds["games"], 2),
        })

    # 자주 하는 실수
    all_mistakes: dict[str, int] = {}
    for g in games:
        for m in g.mistakes:
            all_mistakes[m] = all_mistakes.get(m, 0) + 1
    top_mistakes = sorted(all_mistakes.items(), key=lambda x: -x[1])[:5]

    return {
        "total_games": total,
        "avg_placement": round(avg_placement, 2),
        "top4_rate": round(top4_rate, 2),
        "first_rate": round(first_rate, 2),
        "deck_stats": deck_summary,
        "frequent_mistakes": [{"mistake": m, "count": c} for m, c in top_mistakes],
    }
