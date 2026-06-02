"""Multi-query Retrieval - 질문을 여러 표현으로 확장 후 결과를 RRF로 통합."""

from __future__ import annotations

import logging
import re

from common.base import BaseRAG, RetrievalResult
from common.chunkers import semantic_chunk
from common.embeddings import EmbeddingModel
from common.llm import GenerationLLM
from common.vector_store import QdrantStore

logger = logging.getLogger(__name__)


MULTI_QUERY_SYSTEM = (
    "당신은 사용자 질문을 다양한 표현으로 다시 작성해 검색 회수율을 높이는 도우미입니다."
)

MULTI_QUERY_USER_TMPL = (
    "다음 질문을 의미는 유지한 채 표현/관점을 다르게 4개의 짧은 질문으로 다시 작성하세요.\n"
    "한 줄에 하나씩, 번호 없이 출력하세요.\n\n"
    "원 질문: {query}\n\n변형:"
)


def _rrf(rankings: list[list[int]], k: int = 60) -> list[tuple[int, float]]:
    scores: dict[int, float] = {}
    for ranking in rankings:
        for rank, idx in enumerate(ranking):
            scores[idx] = scores.get(idx, 0.0) + 1.0 / (k + rank + 1)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


class MultiQueryRAG(BaseRAG):
    name = "05-multi-query"

    def __init__(self, collection: str = "multiquery_rag", n_queries: int = 4):
        self.embedder = EmbeddingModel()
        self.store = QdrantStore(collection, dim=self.embedder.dim)
        self.llm = GenerationLLM()
        self.n_queries = n_queries

        self._chunks: list[str] = []
        self._payloads: list[dict] = []
        self._text_to_idx: dict[str, int] = {}

    def build_index(self, documents: list[dict]) -> None:
        self.store.recreate()
        self._chunks = []
        self._payloads = []
        for doc in documents:
            for chunk in semantic_chunk(doc["text"]):
                self._chunks.append(chunk)
                self._payloads.append({"text": chunk, "doc_id": doc.get("id"), "title": doc.get("title", "")})
        self._text_to_idx = {c: i for i, c in enumerate(self._chunks)}
        vectors = self.embedder.encode(self._chunks)
        self.store.upsert(vectors, self._payloads)
        logger.info("Multi-query 인덱스 구축: %d 청크", len(self._chunks))

    def _expand_queries(self, query: str) -> list[str]:
        raw = self.llm.raw(
            system=MULTI_QUERY_SYSTEM,
            user=MULTI_QUERY_USER_TMPL.format(query=query),
            temperature=0.4,
        )
        lines = [re.sub(r"^[\d\-\.\)\s]+", "", line).strip() for line in raw.splitlines()]
        variants = [line for line in lines if line]
        return [query] + variants[: self.n_queries]

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        queries = self._expand_queries(query)
        logger.debug("확장 질문: %s", queries)
        all_rankings: list[list[int]] = []
        for q in queries:
            q_vec = self.embedder.encode_one(q)
            hits = self.store.search(q_vec, top_k=top_k * 3)
            ranking = [self._text_to_idx.get(h.payload["text"], -1) for h in hits]
            ranking = [i for i in ranking if i >= 0]
            all_rankings.append(ranking)

        fused = _rrf(all_rankings)[:top_k]
        return [
            RetrievalResult(text=self._chunks[i], score=s, metadata=self._payloads[i]) for i, s in fused
        ]

    def generate(self, query: str, top_k: int = 5) -> dict:
        results = self.retrieve(query, top_k=top_k)
        contexts = [r.text for r in results]
        answer = self.llm.generate(query, contexts)
        return {"answer": answer, "contexts": contexts, "raw_results": results}


if __name__ == "__main__":
    from data.sample.loader import load_all

    logging.basicConfig(level=logging.INFO)
    rag = MultiQueryRAG()
    rag.build_index(load_all())
    out = rag.generate("한국어 검색에서 형태소 분석은 왜 필요합니까?")
    print("\n[답변]\n", out["answer"])
