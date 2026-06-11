"""research-rag 백엔드 API.

기존 8501 대시보드의 인터랙티브 데모 로직(dashboard/components/demo.py)을 그대로
떼어내, 정적 프론트엔드(8502)가 호출할 수 있는 REST 엔드포인트로 노출한다.
새 RAG 로직은 없으며 techniques/ + common/ 코드를 재사용한다.
"""

from __future__ import annotations

import importlib.util
import logging
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("research-rag-api")

ROOT = Path(__file__).resolve().parent.parent

# 8501 데모와 동일한 레지스트리. 폴더명에 하이픈이 있어 동적 로드한다.
TECHNIQUE_REGISTRY: dict[str, tuple[str, str]] = {
    "01-naive": ("01-naive", "NaiveRAG"),
    "02-hybrid-search": ("02-hybrid-search", "HybridRAG"),
    "03-reranking": ("03-reranking", "RerankingRAG"),
    "04-hyde": ("04-hyde", "HydeRAG"),
    "05-multi-query": ("05-multi-query", "MultiQueryRAG"),
    "06-parent-child": ("06-parent-child", "ParentChildRAG"),
    "07-contextual-retrieval": ("07-contextual-retrieval", "ContextualRetrievalRAG"),
    "08-self-rag": ("08-self-rag", "SelfRAG"),
    "09-crag": ("09-crag", "CragRAG"),
    "10-graphrag": ("10-graphrag", "GraphRAG"),
    "11-raptor": ("11-raptor", "RaptorRAG"),
    "12-agentic-rag": ("12-agentic-rag", "AgenticRAG"),
    "13-adaptive-rag": ("13-adaptive-rag", "AdaptiveRAG"),
}

# 기법별 인스턴스 캐시. 최초 1회 인덱스를 구축하고 이후 재사용한다(8501과 동일).
_RAG_CACHE: dict[str, object] = {}


def _load_rag(technique_id: str):
    if technique_id in _RAG_CACHE:
        return _RAG_CACHE[technique_id]
    folder, class_name = TECHNIQUE_REGISTRY[technique_id]
    rag_path = ROOT / "techniques" / folder / "rag.py"
    spec = importlib.util.spec_from_file_location(f"rag_{technique_id}", rag_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rag = getattr(module, class_name)()

    from data.sample.loader import load_all

    logger.info("인덱스 구축 시작: %s", technique_id)
    rag.build_index(load_all())
    logger.info("인덱스 구축 완료: %s", technique_id)

    _RAG_CACHE[technique_id] = rag
    return rag


app = FastAPI(title="research-rag API", version="1.0")


class QueryIn(BaseModel):
    technique: str
    query: str
    top_k: int = 5


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "techniques": list(TECHNIQUE_REGISTRY)}


@app.get("/api/techniques")
def techniques() -> dict:
    return {"order": list(TECHNIQUE_REGISTRY)}


@app.post("/api/query")
def query(body: QueryIn) -> dict:
    if body.technique not in TECHNIQUE_REGISTRY:
        return {"error": f"알 수 없는 기법: {body.technique}"}
    if not body.query.strip():
        return {"error": "질문이 비어 있습니다."}

    from common.usage import get_tracker

    tracker = get_tracker()
    tracker.reset()
    rag = _load_rag(body.technique)
    result = rag.generate(body.query, top_k=int(body.top_k))
    totals = tracker.snapshot().get("totals", {})

    return {
        "technique": body.technique,
        "query": body.query,
        "answer": result.get("answer", ""),
        "contexts": result.get("contexts", []),
        "usage": {
            "calls": totals.get("calls", 0),
            "input_tokens": totals.get("input_tokens", 0),
            "output_tokens": totals.get("output_tokens", 0),
            "cost_usd": totals.get("cost_usd", 0.0),
            "elapsed_seconds": totals.get("elapsed_seconds", 0.0),
        },
    }
