"""designsite/data/rag_data.js 를 평가 결과 JSON 에서 빌드.

evaluation/results/*.json 에서 기법별 최신 1 개를 골라
시안이 기대하는 모양으로 변환한 뒤 window.RAG_DATA 글로벌로
주입되는 한 줄 JS 파일로 저장.

키 변환
- user_input → q
- response → answer
- retrieved_contexts → contexts
- usage.indexing → usage.indexing.totals (calls/input_tokens/output_tokens/elapsed_seconds/cost_usd)
- 메트릭 4 개 (faithfulness/answer_relevancy/context_precision/context_recall) 는 그대로
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "evaluation" / "results"
OUT = ROOT / "designsite" / "data" / "rag_data.js"

ORDER = [
    "01-naive",
    "02-hybrid-search",
    "03-reranking",
    "04-hyde",
    "05-multi-query",
    "06-parent-child",
    "07-contextual-retrieval",
    "08-self-rag",
    "09-crag",
    "10-graphrag",
    "11-raptor",
    "12-agentic-rag",
    "13-adaptive-rag",
]

USAGE_FIELDS = ["calls", "input_tokens", "output_tokens", "elapsed_seconds", "cost_usd"]


def latest_json(tech: str) -> Path | None:
    files = sorted(RESULTS.glob(f"{tech}-*.json"))
    return files[-1] if files else None


def usage_block(raw: dict) -> dict:
    out = {}
    for phase in ("indexing", "inference"):
        totals = raw.get(phase, {}).get("totals", {})
        out[phase] = {k: totals.get(k, 0) for k in USAGE_FIELDS}
    return out


def by_question(rows: list[dict]) -> list[dict]:
    converted = []
    for r in rows:
        converted.append({
            "q": r.get("user_input", ""),
            "answer": r.get("response", ""),
            "reference": r.get("reference", ""),
            "contexts": r.get("retrieved_contexts", []),
            "faithfulness": r.get("faithfulness"),
            "answer_relevancy": r.get("answer_relevancy"),
            "context_precision": r.get("context_precision"),
            "context_recall": r.get("context_recall"),
        })
    return converted


def main() -> None:
    techniques = {}
    picked = {}
    for tech in ORDER:
        path = latest_json(tech)
        if path is None:
            print(f"[skip] {tech}: 결과 파일 없음")
            continue
        raw = json.loads(path.read_text(encoding="utf-8"))
        techniques[tech] = {
            "summary": raw.get("summary", {}),
            "usage": usage_block(raw.get("usage", {})),
            "by_question": by_question(raw.get("by_question", [])),
        }
        picked[tech] = path.name

    payload = {"order": [t for t in ORDER if t in techniques], "techniques": techniques}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        "window.RAG_DATA = " + json.dumps(payload, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )

    n_q = sum(len(t["by_question"]) for t in techniques.values())
    print(f"기법 {len(techniques)} / 질문 합계 {n_q}")
    for tech, name in picked.items():
        print(f"  {tech} ← {name}")
    print(f"\n→ {OUT} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
