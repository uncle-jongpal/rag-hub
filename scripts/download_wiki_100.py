"""V4 평가용 한국어 위키 100문서 일괄 다운로드.

토픽 리스트는 data/wiki/topics.txt 에 있고, 다양한 도메인(기술/과학/문화/역사/사회/예술)을
의도적으로 골고루 포함. 다운로드 결과는 data/wiki/korean_wiki_100.jsonl.

사용:
    python scripts/download_wiki_100.py
또는 컨테이너 안에서:
    docker compose exec dashboard python scripts/download_wiki_100.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import wikipediaapi


def load_topics(path: Path) -> list[str]:
    topics: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        topics.append(line)
    return topics


def fetch(topic: str, wiki) -> dict | None:
    page = wiki.page(topic)
    if not page.exists():
        return None
    # summary 가 너무 짧으면 본문 일부 사용. 너무 길면 잘라서 사용 (인덱싱 시간/메모리 관리)
    text = page.summary if len(page.summary) >= 600 else page.text
    text = text[:6000]
    return {
        "id": f"ko-wiki-{page.pageid}",
        "title": page.title,
        "text": text,
    }


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    topics_path = root / "data" / "wiki" / "topics.txt"
    out_path = root / "data" / "wiki" / "korean_wiki_100.jsonl"

    topics = load_topics(topics_path)
    print(f"토픽 수: {len(topics)}")

    wiki = wikipediaapi.Wikipedia(
        user_agent="rag-frame/0.4 (https://github.com/uncle-jongpal/rag-hub)",
        language="ko",
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    success = 0
    missing: list[str] = []
    with out_path.open("w", encoding="utf-8") as f:
        for i, topic in enumerate(topics, 1):
            doc = fetch(topic, wiki)
            if doc is None:
                missing.append(topic)
                print(f"  [{i:3d}] - {topic} : 페이지 없음 (skip)")
            else:
                f.write(json.dumps(doc, ensure_ascii=False) + "\n")
                success += 1
                tlen = len(doc["text"])
                print(f"  [{i:3d}] + {doc['title']} ({tlen}자)")
            time.sleep(0.2)  # API 부담 줄이기

    print()
    print(f"성공 {success} / 전체 {len(topics)}")
    print(f"실패 토픽({len(missing)}): {missing}")
    print(f"저장: {out_path}")


if __name__ == "__main__":
    main()
