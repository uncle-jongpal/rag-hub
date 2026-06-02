"""Reranking RAG - 임베딩 1차 검색 후 cross-encoder로 재정렬."""

from __future__ import annotations

import logging

from common.base import BaseRAG, RetrievalResult
from common.chunkers import semantic_chunk
from common.config import settings
from common.embeddings import EmbeddingModel
from common.llm import GenerationLLM
from common.vector_store import QdrantStore

logger = logging.getLogger(__name__)


class Reranker:
    """BGE-reranker-v2-m3 cross-encoder."""

    def __init__(self, model_name: str | None = None):
        from sentence_transformers import CrossEncoder

        self.model_name = model_name or settings.reranker_model
        logger.info("Reranker 로드: %s", self.model_name)
        self.model = CrossEncoder(self.model_name)

    def rerank(self, query: str, candidates: list[str]) -> list[float]:
        pairs = [[query, c] for c in candidates]
        scores = self.model.predict(pairs)
        return scores.tolist()


class RerankingRAG(BaseRAG):
    name = "03-reranking"

    def __init__(self, collection: str = "reranking_rag", first_stage_n: int = 30):
        self.embedder = EmbeddingModel()
        self.store = QdrantStore(collection, dim=self.embedder.dim)
        self.reranker = Reranker()
        self.llm = GenerationLLM()
        self.first_stage_n = first_stage_n

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
        logger.info("Reranking 인덱스 구축: %d 청크", len(chunks))

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        q_vec = self.embedder.encode_one(query)
        first = self.store.search(q_vec, top_k=self.first_stage_n)
        if not first:
            return []
        texts = [h.payload["text"] for h in first]
        scores = self.reranker.rerank(query, texts)
        ranked = sorted(zip(first, scores, strict=True), key=lambda x: x[1], reverse=True)[:top_k]
        return [
            RetrievalResult(text=h.payload["text"], score=float(s), metadata=h.payload) for h, s in ranked
        ]

    def generate(self, query: str, top_k: int = 5) -> dict:
        results = self.retrieve(query, top_k=top_k)
        contexts = [r.text for r in results]
        answer = self.llm.generate(query, contexts)
        return {"answer": answer, "contexts": contexts, "raw_results": results}


if __name__ == "__main__":
    from data.sample.loader import load_all

    logging.basicConfig(level=logging.INFO)
    rag = RerankingRAG()
    rag.build_index(load_all())
    out = rag.generate("BGE-reranker는 무엇이고 언제 사용합니까?")
    print("\n[답변]\n", out["answer"])
