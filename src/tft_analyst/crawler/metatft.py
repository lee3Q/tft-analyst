"""metatft.com 크롤러 — API 조사 후 구현 예정."""

from __future__ import annotations

from ..data.models import Deck


async def crawl_metatft(patch: str | None = None) -> list[Deck]:
    """metatft.com에서 메타 덱 데이터 크롤링.

    TODO: API 엔드포인트 확인 후 구현
    - 내부 API 우선 시도
    - 실패 시 Playwright 헤드리스 브라우저
    """
    raise NotImplementedError(
        "metatft.com 크롤러 미구현. API 엔드포인트 조사 필요."
    )
