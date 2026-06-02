"""Naive RAG - 단순 임베딩 + top-k 검색 베이스라인."""

from __future__ import annotations

import logging

from common.base import BaseRAG, RetrievalResult
from common.chunkers import semantic_chunk
from common.embeddings import EmbeddingModel
from common.llm import GenerationLLM
from common.vector_store import QdrantStore

logger = logging.getLogger(__name__)


class NaiveRAG(BaseRAG):
    name = "01-naive"

    def __init__(self, collection: str = "naive_rag"):
        self.embedder = EmbeddingModel()
        self.store = QdrantStore(collection, dim=self.embedder.dim)
        self.llm = GenerationLLM()

    def build_index(self, documents: list[dict]) -> None:
        self.store.recreate()
        chunk_texts: list[str] = []
        payloads: list[dict] = []
        for doc in documents:
            for chunk in semantic_chunk(doc["text"]):
                chunk_texts.append(chunk)
                payloads.append({"text": chunk, "doc_id": doc.get("id"), "title": doc.get("title", "")})

        vectors = self.embedder.encode(chunk_texts)
        self.store.upsert(vectors, payloads)
        logger.info("Naive 인덱스 구축 완료: %d 청크", len(chunk_texts))

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        q_vec = self.embedder.encode_one(query)
        hits = self.store.search(q_vec, top_k=top_k)
        return [RetrievalResult(text=h.payload["text"], score=h.score, metadata=h.payload) for h in hits]

    def generate(self, query: str, top_k: int = 5) -> dict:
        results = self.retrieve(query, top_k=top_k)
        contexts = [r.text for r in results]
        answer = self.llm.generate(query, contexts)
        return {"answer": answer, "contexts": contexts, "raw_results": results}


if __name__ == "__main__":
    from data.sample.loader import load_all

    logging.basicConfig(level=logging.INFO)
    rag = NaiveRAG()
    rag.build_index(load_all())
    out = rag.generate("BGE-M3 임베딩 모델의 특징은?")
    print("\n[답변]\n", out["answer"])
    print("\n[컨텍스트]\n")
    for i, c in enumerate(out["contexts"], 1):
        print(f"({i}) {c[:120]}...")
