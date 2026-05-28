"""샘플 외 추가 데이터 다운로드 - 한국어/영어 위키 본문 일부.

기본 샘플(`data/sample/*.jsonl`)은 깃에 포함되어 있어 다운로드 없이도 동작합니다.
이 스크립트는 더 큰 벤치마크가 필요할 때 위키피디아에서 문서를 추가로 가져옵니다.

사용 예:
    uv run python scripts/download_data.py --lang ko --topics "검색 증강 생성,BM25" --out data/cache/ko_extra.jsonl
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def fetch_wiki(topic: str, lang: str) -> dict | None:
    import wikipediaapi

    wiki = wikipediaapi.Wikipedia(
        user_agent="rag-hub/0.1 (https://example.com)",
        language=lang,
    )
    page = wiki.page(topic)
    if not page.exists():
        return None
    return {
        "id": f"{lang}-wiki-{page.pageid}",
        "title": page.title,
        "text": page.summary if len(page.summary) > 200 else page.text[:2000],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", default="ko", choices=["ko", "en"])
    parser.add_argument("--topics", required=True, help="콤마 구분")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    topics = [t.strip() for t in args.topics.split(",") if t.strip()]
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as f:
        for t in topics:
            doc = fetch_wiki(t, args.lang)
            if doc:
                f.write(json.dumps(doc, ensure_ascii=False) + "\n")
                print(f"  + {doc['title']}")
            else:
                print(f"  - {t} (페이지 없음)")

    print(f"저장 완료: {out_path}")


if __name__ == "__main__":
    main()
