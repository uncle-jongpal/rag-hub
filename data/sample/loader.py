"""샘플 데이터 로더 - jsonl 파일을 한 곳에서 읽어옴."""

import json
from pathlib import Path

SAMPLE_DIR = Path(__file__).parent


def load_korean() -> list[dict]:
    return _load(SAMPLE_DIR / "korean_docs.jsonl")


def load_english() -> list[dict]:
    return _load(SAMPLE_DIR / "english_docs.jsonl")


def load_all() -> list[dict]:
    """한/영 합본. 평가 베이스로 사용."""
    return load_korean() + load_english()


def _load(path: Path) -> list[dict]:
    out: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(json.loads(line))
    return out
