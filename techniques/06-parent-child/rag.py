"""Parent-Child Chunking - 자식 청크로 검색, 부모 청크로 컨텍스트 확장."""

from __future__ import annotations

import logging

from common.base import BaseRAG, RetrievalResult
from common.chunkers import parent_child_chunk
from common.embeddings import EmbeddingModel
from common.llm import GenerationLLM
from common.vector_store import QdrantStore

logger = logging.getLogger(__name__)


class ParentChildRAG(BaseRAG):
    name = "06-parent-child"

    def __init__(self, collection: str = "parent_child_rag"):
        self.embedder = EmbeddingModel()
        self.store = QdrantStore(collection, dim=self.embedder.dim)
        self.llm = GenerationLLM()
        self._parents: list[str] = []

    def build_index(self, documents: list[dict]) -> None:
        self.store.recreate()
        self._parents = []

        child_texts: list[str] = []
        payloads: list[dict] = []

        for doc in documents:
            for parent, children in parent_child_chunk(doc["text"]):
                parent_idx = len(self._parents)
                self._parents.append(parent)
                for child in children:
                    child_texts.append(child)
                    payloads.append(
                        {
                            "text": child,
                            "parent_idx": parent_idx,
                            "doc_id": doc.get("id"),
                            "title": doc.get("title", ""),
                        }
                    )

        vectors = self.embedder.encode(child_texts)
        self.store.upsert(vectors, payloads)
        logger.info(
            "Parent-child 인덱스 구축: %d 부모, %d 자식",
            len(self._parents),
            len(child_texts),
        )

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        q_vec = self.embedder.encode_one(query)
        hits = self.store.search(q_vec, top_k=top_k * 3)

        seen_parents: set[int] = set()
        results: list[RetrievalResult] = []
        for h in hits:
            parent_idx = h.payload.get("parent_idx", -1)
            if parent_idx in seen_parents or parent_idx < 0:
                continue
            seen_parents.add(parent_idx)
            parent_text = self._parents[parent_idx]
            metadata = {**h.payload, "child_text": h.payload["text"]}
            results.append(RetrievalResult(text=parent_text, score=h.score, metadata=metadata))
            if len(results) >= top_k:
                break
        return results

    def generate(self, query: str, top_k: int = 5) -> dict:
        results = self.retrieve(query, top_k=top_k)
        contexts = [r.text for r in results]
        answer = self.llm.generate(query, contexts)
        return {"answer": answer, "contexts": contexts, "raw_results": results}


if __name__ == "__main__":
    from data.sample.loader import load_all

    logging.basicConfig(level=logging.INFO)
    rag = ParentChildRAG()
    rag.build_index(load_all())
    out = rag.generate("Qdrant 벡터 DB는 어떤 점에서 PoC에 적합합니까?")
    print("\n[답변]\n", out["answer"])
