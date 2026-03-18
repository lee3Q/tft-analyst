# TFT Analyst

개인용 TFT 분석가 도구. Claude Code MCP 서버 + 스킬.

## 구조

```
src/tft_analyst/
├── server.py          # MCP 서버 (FastMCP)
├── tools/             # 7+1개 도구 (crawl, get_meta, recommend, record_game, get_stats, quiz, add_buildup, list_buildups)
├── data/
│   ├── models.py      # Deck, Buildup, GameRecord 데이터클래스
│   └── store.py       # JSON 파일 기반 저장소
└── crawler/
    ├── cli.py         # tft-crawl CLI
    ├── lolchess.py    # lolchess.gg 크롤러 (구현 예정)
    └── metatft.py     # metatft.com 크롤러 (구현 예정)

skill/tft.md           # /tft 스킬 정의 (페르소나 + 플로우)
data/                  # 로컬 데이터 (decks.json, buildups.json, games.json)
```

## 실행

```bash
# MCP 서버
uv run tft-analyst

# 크롤링
uv run tft-crawl [lolchess|metatft|all] --patch 14.5
```

## 개발 규칙

- Python 3.11+, type hints 사용
- 데이터는 로컬 JSON 파일 (data/ 디렉토리)
- LLM은 크롤링 데이터 정제에만 사용, 서비스 로직은 규칙 기반
- 한국어 전용
