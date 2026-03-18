"""metatft.com 크롤러 — api-hc.metatft.com API 사용."""

from __future__ import annotations

import httpx

from ..data.models import Deck

API_BASE = "https://api-hc.metatft.com"
DATA_BASE = "https://data.metatft.com"
HEADERS = {
    "User-Agent": "tft-analyst/0.1",
    "Origin": "https://metatft.com",
    "Referer": "https://metatft.com/",
}


async def crawl_metatft(patch: str | None = None) -> list[Deck]:
    """metatft.com에서 메타 덱 데이터 수집.

    소스:
    1. /tft-comps-api/latest_cluster_info — 컴프 클러스터 목록
    2. /tft-comps-api/comp_options — 클러스터별 변형 + 통계
    3. /tft-comps-api/comp_builds — 챔피언별 아이템 빌드
    4. /tft-comps-api/comp_augments — 증강 추천
    """
    async with httpx.AsyncClient(headers=HEADERS, timeout=30) as client:
        clusters = await _fetch_clusters(client)
        options = await _fetch_comp_options(client)
        builds = await _fetch_comp_builds(client)
        augments = await _fetch_comp_augments(client)

    return _build_decks(clusters, options, builds, augments, patch)


async def _fetch_clusters(client: httpx.AsyncClient) -> dict:
    """컴프 클러스터 목록."""
    resp = await client.get(f"{API_BASE}/tft-comps-api/latest_cluster_info")
    resp.raise_for_status()
    return resp.json()


async def _fetch_comp_options(client: httpx.AsyncClient) -> dict:
    """클러스터별 유닛 조합 변형 + 통계."""
    resp = await client.get(f"{API_BASE}/tft-comps-api/comp_options")
    resp.raise_for_status()
    return resp.json()


async def _fetch_comp_builds(client: httpx.AsyncClient) -> dict:
    """챔피언별 아이템 빌드."""
    resp = await client.get(f"{API_BASE}/tft-comps-api/comp_builds")
    resp.raise_for_status()
    return resp.json()


async def _fetch_comp_augments(client: httpx.AsyncClient) -> dict:
    """컴프별 증강 추천."""
    try:
        resp = await client.get(f"{API_BASE}/tft-comps-api/comp_augments")
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return {}


def _build_decks(
    clusters: dict,
    options: dict,
    builds: dict,
    augments: dict,
    patch: str | None,
) -> list[Deck]:
    """API 응답을 Deck 리스트로 변환."""
    decks: list[Deck] = []

    cluster_info = clusters.get("cluster_info", {})
    cluster_details = cluster_info.get("cluster_details", {})
    cluster_list = cluster_details.get("clusters", [])
    tft_set = clusters.get("tft_set", "")

    options_data = options.get("results", {}).get("options", {})
    builds_data = builds.get("results", {})

    for cluster in cluster_list:
        cluster_id = str(cluster.get("Cluster", ""))

        # 챔피언 추출 (TFT16_Neeko → Neeko)
        units_str = cluster.get("units_string", "")
        champions = _parse_units(units_str)
        if not champions:
            continue

        # 시너지 추출
        traits_str = cluster.get("traits_string", "")
        synergies = _parse_traits(traits_str)

        # 이름 생성
        name_data = cluster.get("name", [])
        name_str = cluster.get("name_string", "")
        deck_name = _generate_name(name_data, name_str, champions)

        # 통계: 레벨 8 기준 가장 좋은 변형
        avg_placement, plays = _best_option_stats(options_data.get(cluster_id, {}))

        # 아이템 빌드
        items_map = _parse_builds(builds_data.get(cluster_id, {}))

        # 증강
        augment_list = _parse_augments(augments, cluster_id)

        first_rate = 0.0
        if plays > 0:
            # metatft는 1등 비율을 직접 제공하지 않으므로 avg_placement로 추정
            # avg 3.0 이하 → ~20%, 4.0 → ~12%, 5.0 → ~8%
            first_rate = max(0.0, 0.30 - avg_placement * 0.05) if avg_placement > 0 else 0.0

        decks.append(Deck(
            name=deck_name,
            core_champions=champions,
            recommended_items=items_map,
            avg_placement=round(avg_placement, 2),
            first_rate=round(first_rate, 4),
            difficulty=_estimate_difficulty(len(champions)),
            synergy_tags=synergies,
            recommended_augments=augment_list[:5],
            emblem_synergies=[],
            source="metatft",
            patch=patch or tft_set,
        ))

    # 평균 순위순 정렬
    decks.sort(key=lambda d: d.avg_placement if d.avg_placement > 0 else 99)
    return decks


def _parse_units(units_str: str) -> list[str]:
    """'TFT16_Neeko, TFT16_Taric' → ['Neeko', 'Taric']"""
    if not units_str:
        return []
    return [u.strip().split("_")[-1] for u in units_str.split(",") if u.strip()]


def _parse_traits(traits_str: str) -> list[str]:
    """'TFT16_Defender_1, TFT16_Demacia_1' → ['Defender', 'Demacia']"""
    if not traits_str:
        return []
    tags = set()
    for t in traits_str.split(","):
        parts = t.strip().split("_")
        if len(parts) >= 2:
            tags.add(parts[-2])  # TFT16_Defender_1 → Defender
    return sorted(tags)


def _generate_name(name_data: list, name_str: str, champions: list[str]) -> str:
    """덱 이름 생성."""
    if name_data:
        parts = []
        for entry in name_data[:2]:
            raw = entry.get("name", "")
            clean = raw.split("_")[-1] if "_" in raw else raw
            parts.append(clean)
        if parts:
            return " ".join(parts)

    if champions:
        return " ".join(champions[:2]) + " 덱"
    return "Unknown"


def _best_option_stats(options: dict) -> tuple[float, int]:
    """레벨 8 기준 가장 좋은 변형의 통계 반환."""
    # 레벨 8 → 9 → 10 순으로 시도
    for level in ("8", "9", "10"):
        variants = options.get(level, [])
        if not variants:
            continue
        # count 가장 많은 변형 기준
        best = max(variants, key=lambda v: v.get("count", 0))
        return best.get("avg", 0.0), best.get("count", 0)
    return 0.0, 0


def _parse_builds(builds_data: dict) -> dict[str, list[str]]:
    """챔피언별 추천 아이템."""
    items_map: dict[str, list[str]] = {}
    build_list = builds_data.get("builds", [])

    for build in build_list:
        unit = build.get("unit", "")
        champ_name = unit.split("_")[-1] if "_" in unit else unit
        item_names = [i.split("_")[-1] if "_" in i else i for i in build.get("buildName", [])]

        # 가장 좋은 빌드만 (avg 기준)
        if champ_name not in items_map:
            items_map[champ_name] = item_names

    return items_map


def _parse_augments(augments: dict, cluster_id: str) -> list[str]:
    """컴프별 추천 증강."""
    if not augments:
        return []
    results = augments.get("results", {})
    cluster_augs = results.get(cluster_id, {})
    aug_list = cluster_augs.get("augments", [])
    return [a.get("augment", "").split("_")[-1] for a in aug_list[:5] if a.get("augment")]


def _estimate_difficulty(champ_count: int) -> str:
    if champ_count >= 9:
        return "상"
    elif champ_count >= 7:
        return "중"
    else:
        return "하"
