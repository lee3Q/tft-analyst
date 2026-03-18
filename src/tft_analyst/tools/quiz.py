"""패치 브리핑 + 빌드업 퀴즈 도구."""

from __future__ import annotations

import json
import random

from ..data.store import load_buildups, load_decks


def quiz() -> str:
    """패치 브리핑 + 빌드업 퀴즈 생성.

    Returns:
        브리핑 내용 + 퀴즈 질문/선택지/정답
    """
    decks = load_decks()
    buildups = load_buildups()

    result: dict = {}

    # 1. 패치 브리핑
    if decks:
        top_decks = sorted(decks, key=lambda d: d.avg_placement)[:3]
        result["briefing"] = {
            "top_meta_decks": [
                {"name": d.name, "avg_placement": d.avg_placement, "synergies": d.synergy_tags}
                for d in top_decks
            ],
            "patch": decks[0].patch if decks[0].patch else "unknown",
        }

    # 2. 퀴즈 생성 (빌드업 기반)
    questions = []

    if buildups:
        questions.extend(_buildup_tier_quiz(buildups))
        questions.extend(_buildup_matchup_quiz(buildups))

    if decks:
        questions.extend(_meta_deck_quiz(decks))

    # 최대 3문제 랜덤 선택
    if questions:
        random.shuffle(questions)
        result["quiz"] = questions[:3]
    else:
        result["quiz"] = []
        result["message"] = "데이터가 부족하여 퀴즈를 생성할 수 없습니다."

    return json.dumps(result, ensure_ascii=False, indent=2)


def _buildup_tier_quiz(buildups: list) -> list[dict]:
    """가장 강한 빌드업 맞추기."""
    questions = []
    s_tier = [b for b in buildups if b.tier == "S"]
    others = [b for b in buildups if b.tier != "S"]

    if s_tier and len(others) >= 2:
        correct = random.choice(s_tier)
        wrong = random.sample(others, min(2, len(others)))
        options = [correct.name] + [w.name for w in wrong]
        random.shuffle(options)

        questions.append({
            "question": "현재 패치에서 가장 강력한 초반 빌드업은?",
            "options": options,
            "answer": correct.name,
            "explanation": f"{correct.name}은(는) 현재 S티어 빌드업입니다.",
        })

    return questions


def _buildup_matchup_quiz(buildups: list) -> list[dict]:
    """빌드업 상성 퀴즈."""
    questions = []

    for b in buildups:
        if b.strong_against and b.weak_against:
            # "X 빌드업에 강한 빌드업은?"
            target = random.choice(b.strong_against) if b.strong_against else None
            if target:
                wrong_pool = [
                    other.name for other in buildups
                    if other.name != b.name and other.name != target
                ]
                if len(wrong_pool) >= 2:
                    wrong = random.sample(wrong_pool, 2)
                    options = [b.name] + wrong
                    random.shuffle(options)

                    questions.append({
                        "question": f"{target} 빌드업에 강한 빌드업은?",
                        "options": options,
                        "answer": b.name,
                        "explanation": f"{b.name}은(는) {target}에 대해 상성 유리합니다.",
                    })
                    break  # 1문제만

    return questions


def _meta_deck_quiz(decks: list) -> list[dict]:
    """메타 덱 관련 퀴즈."""
    questions = []
    if len(decks) >= 3:
        sorted_decks = sorted(decks, key=lambda d: d.avg_placement)
        correct = sorted_decks[0]
        wrong = random.sample(sorted_decks[3:], min(2, len(sorted_decks) - 3)) if len(sorted_decks) > 3 else sorted_decks[1:3]
        options = [correct.name] + [w.name for w in wrong]
        random.shuffle(options)

        questions.append({
            "question": "현재 패치에서 평균 순위가 가장 높은(낮은) 메타 덱은?",
            "options": options,
            "answer": correct.name,
            "explanation": f"{correct.name}의 평균 순위는 {correct.avg_placement}입니다.",
        })

    return questions
