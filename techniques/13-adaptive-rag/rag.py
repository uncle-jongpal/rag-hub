"""Adaptive RAG - 질문 난이도/유형을 먼저 분류해 다른 검색 전략으로 분기.

원논문(Jeong et al., 2024)은 분류기를 fine-tune하지만 본 구현은 LLM 프롬프트 기반 단순 분류입니다.

분기 정책
- simple : 검색 불필요 (산수, 상식). LLM 직접 답변
- single-hop : 1회 검색으로 답이 나옴. Naive RAG
- multi-hop : 다단계 추론 필요. Multi-query 방식 검색
"""

from __future__ import annotations

import logging
import re

from common.base import BaseRAG, RetrievalResult
from common.chunkers import semantic_chunk
from common.embeddings import EmbeddingModel
from common.llm import GenerationLLM
from common.vector_store import QdrantStore

logger = logging.getLogger(__name__)


CLASSIFY_SYSTEM = "당신은 질문 복잡도를 simple/single-hop/multi-hop 세 단계로 분류하는 분류기입니다."

CLASSIFY_USER = (
    "다음 질문의 복잡도를 한 단어로 분류하세요.\n"
    "- simple : 외부 지식 검색이 불필요한 단순 질문 (산수, 일반 상식, 메타)\n"
    "- single-hop : 한 번의 검색으로 답이 나오는 사실 질문\n"
    "- multi-hop : 여러 문서를 종합하거나 단계적 추론이 필요한 질문\n\n"
    "질문: {query}\n\n분류:"
)

EXPAND_SYSTEM = "질문을 의미는 유지한 채 3개의 변형으로 다시 쓰세요."

EXPAND_USER = (
    "다음 질문을 검색 회수율을 높이도록 표현/관점이 다른 3개 변형으로 다시 작성하세요. "
    "한 줄에 하나씩 번호 없이 출력하세요.\n\n질문: {query}\n\n변형:"
)


class AdaptiveRAG(BaseRAG):
    name = "13-adaptive-rag"

    def __init__(self, collection: str = "adaptive_rag"):
        self.embedder = EmbeddingModel()
        self.store = QdrantStore(collection, dim=self.embedder.dim)
        self.llm = GenerationLLM()

    def build_index(self, documents: list[dict]) -> None:
        self.store.recreate()
        chunks: list[str] = []
        payloads: list[dict] = []
        for doc in documents:
            for chunk in semantic_chunk(doc["text"]):
                chunks.append(chunk)
                payloads.append({"text": chunk, "doc_id": doc.get("id"), "title": doc.get("title", "")})
        vectors = self.embedder.encode(chunks)
        self.store.upsert(vectors, payloads)
        logger.info("Adaptive RAG 인덱스 구축: %d 청크", len(chunks))

    def _classify(self, query: str) -> str:
        raw = self.llm.raw(
            system=CLASSIFY_SYSTEM,
            user=CLASSIFY_USER.format(query=query),
            temperature=0.0,
        ).lower()
        for label in ("multi-hop", "single-hop", "simple"):
            if label in raw:
                return label
        return "single-hop"

    def _expand(self, query: str) -> list[str]:
        raw = self.llm.raw(
            system=EXPAND_SYSTEM,
            user=EXPAND_USER.format(query=query),
            temperature=0.4,
        )
        return [re.sub(r"^[\d\-\.\)\s]+", "", line).strip() for line in raw.splitlines() if line.strip()]

    def _search_single(self, query: str, top_k: int) -> list[RetrievalResult]:
        q_vec = self.embedder.encode_one(query)
        hits = self.store.search(q_vec, top_k=top_k)
        return [RetrievalResult(text=h.payload["text"], score=h.score, metadata=h.payload) for h in hits]

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        label = self._classify(query)
        logger.info("Adaptive 분류: %s", label)
        if label == "simple":
            return []
        if label == "single-hop":
            return self._search_single(query, top_k=top_k)
        # multi-hop : 원 질문 + 변형 3개로 검색 후 dedup
        queries = [query] + self._expand(query)[:3]
        seen: set[str] = set()
        merged: list[RetrievalResult] = []
        for q in queries:
            for r in self._search_single(q, top_k=top_k):
                if r.text in seen:
                    continue
                seen.add(r.text)
                merged.append(r)
        return merged[: top_k * 2]

    def generate(self, query: str, top_k: int = 5) -> dict:
        results = self.retrieve(query, top_k=top_k)
        contexts = [r.text for r in results]
        if not contexts:
            answer = self.llm.raw(
                system="당신은 일반 지식 어시스턴트입니다. 한국어 질문은 한국어로 답하세요.",
                user=query,
                temperature=0.1,
            )
        else:
            answer = self.llm.generate(query, contexts)
        return {"answer": answer, "contexts": contexts, "raw_results": results}


if __name__ == "__main__":
    from data.sample.loader import load_all

    logging.basicConfig(level=logging.INFO)
    rag = AdaptiveRAG()
    rag.build_index(load_all())
    for q in [
        "2 + 3은?",
        "BGE-M3는 누가 공개했나요?",
        "Self-RAG와 CRAG는 어떤 점이 다르고 각각 어떤 경우에 더 적합합니까?",
    ]:
        print(f"\n>>> {q}")
        out = rag.generate(q)
        print("답:", out["answer"][:200])
