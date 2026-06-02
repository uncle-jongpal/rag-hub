"""Hybrid Search - BM25(Kiwi 형태소) + Dense(BGE-M3) 결합, RRF 융합."""

from __future__ import annotations

import logging

from rank_bm25 import BM25Okapi

from common.base import BaseRAG, RetrievalResult
from common.chunkers import semantic_chunk
from common.embeddings import EmbeddingModel
from common.korean_tokenizer import tokenize_mixed
from common.llm import GenerationLLM
from common.vector_store import QdrantStore

logger = logging.getLogger(__name__)


def reciprocal_rank_fusion(
    rankings: list[list[int]],
    k: int = 60,
) -> list[tuple[int, float]]:
    """여러 검색기의 순위를 RRF로 합산.

    rankings: 각 검색기가 반환한 인덱스 리스트 (순위 순)
    반환: [(idx, score), ...] 점수 내림차순
    """
    scores: dict[int, float] = {}
    for ranking in rankings:
        for rank, idx in enumerate(ranking):
            scores[idx] = scores.get(idx, 0.0) + 1.0 / (k + rank + 1)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


class HybridRAG(BaseRAG):
    name = "02-hybrid-search"

    def __init__(self, collection: str = "hybrid_rag", rrf_k: int = 60):
        self.embedder = EmbeddingModel()
        self.store = QdrantStore(collection, dim=self.embedder.dim)
        self.llm = GenerationLLM()
        self.rrf_k = rrf_k

        self._chunks: list[str] = []
        self._payloads: list[dict] = []
        self._bm25: BM25Okapi | None = None

    def build_index(self, documents: list[dict]) -> None:
        self.store.recreate()
        self._chunks = []
        self._payloads = []

        for doc in documents:
            for chunk in semantic_chunk(doc["text"]):
                self._chunks.append(chunk)
                self._payloads.append({"text": chunk, "doc_id": doc.get("id"), "title": doc.get("title", "")})

        vectors = self.embedder.encode(self._chunks)
        self.store.upsert(vectors, self._payloads)

        tokenized = [tokenize_mixed(c) for c in self._chunks]
        self._bm25 = BM25Okapi(tokenized)
        logger.info("Hybrid 인덱스 구축: %d 청크 (Dense + BM25)", len(self._chunks))

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        if self._bm25 is None:
            raise RuntimeError("build_index 를 먼저 호출하세요")

        candidate_n = max(top_k * 4, 20)

        q_vec = self.embedder.encode_one(query)
        dense_hits = self.store.search(q_vec, top_k=candidate_n)
        dense_rank = [self._find_chunk_idx(h.payload["text"]) for h in dense_hits]
        dense_rank = [i for i in dense_rank if i >= 0]

        q_tokens = tokenize_mixed(query)
        bm25_scores = self._bm25.get_scores(q_tokens)
        bm25_rank = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:candidate_n]

        fused = reciprocal_rank_fusion([dense_rank, bm25_rank], k=self.rrf_k)[:top_k]

        results: list[RetrievalResult] = []
        for idx, score in fused:
            results.append(RetrievalResult(text=self._chunks[idx], score=score, metadata=self._payloads[idx]))
        return results

    def _find_chunk_idx(self, text: str) -> int:
        try:
            return self._chunks.index(text)
        except ValueError:
            return -1

    def generate(self, query: str, top_k: int = 5) -> dict:
        results = self.retrieve(query, top_k=top_k)
        contexts = [r.text for r in results]
        answer = self.llm.generate(query, contexts)
        return {"answer": answer, "contexts": contexts, "raw_results": results}


if __name__ == "__main__":
    from data.sample.loader import load_all

    logging.basicConfig(level=logging.INFO)
    rag = HybridRAG()
    rag.build_index(load_all())
    out = rag.generate("RRF는 어떻게 동작합니까?")
    print("\n[답변]\n", out["answer"])
