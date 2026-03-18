"""크롤러 CLI — 패치마다 수동 실행."""

from __future__ import annotations

import argparse
import asyncio
import sys


def main():
    parser = argparse.ArgumentParser(description="TFT 공략 크롤러")
    parser.add_argument(
        "source",
        nargs="?",
        default="all",
        choices=["lolchess", "metatft", "all"],
        help="크롤링 대상 (기본: all)",
    )
    parser.add_argument("--patch", help="패치 버전 (예: 14.5)")
    args = parser.parse_args()

    print(f"크롤링 시작: source={args.source}, patch={args.patch or 'auto'}")
    asyncio.run(run_crawl(args.source, args.patch))


async def run_crawl(source: str, patch: str | None = None):
    """크롤링 실행."""
    from .lolchess import crawl_lolchess
    from .metatft import crawl_metatft
    from ..data.store import save_decks

    all_decks = []

    if source in ("lolchess", "all"):
        print("  → lolchess.gg 크롤링 중...")
        try:
            decks = await crawl_lolchess(patch)
            all_decks.extend(decks)
            print(f"    lolchess.gg: {len(decks)}개 덱 수집")
        except Exception as e:
            print(f"    lolchess.gg 실패: {e}", file=sys.stderr)

    if source in ("metatft", "all"):
        print("  → metatft.com 크롤링 중...")
        try:
            decks = await crawl_metatft(patch)
            all_decks.extend(decks)
            print(f"    metatft.com: {len(decks)}개 덱 수집")
        except Exception as e:
            print(f"    metatft.com 실패: {e}", file=sys.stderr)

    if all_decks:
        save_decks(all_decks)
        print(f"\n총 {len(all_decks)}개 덱 저장 완료.")
    else:
        print("\n수집된 덱이 없습니다.", file=sys.stderr)


if __name__ == "__main__":
    main()
