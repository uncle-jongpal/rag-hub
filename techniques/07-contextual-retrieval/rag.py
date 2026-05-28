"""Contextual Retrieval (Anthropic, 2024.09) - 각 청크에 문서 컨텍스트 1-2문장을 prepend."""

from __future__ import annotations

import logging

from common.base import BaseRAG, RetrievalResult
from common.chunkers import semantic_chunk
from common.embeddings import EmbeddingModel
from common.llm import GenerationLLM
from common.vector_store import QdrantStore

logger = logging.getLogger(__name__)


CONTEXT_SYSTEM = (
    "당신은 청크가 어떤 문서의 어느 부분인지 한두 문장으로 요약해 "
    "검색 시점에 맥락이 드러나도록 돕는 어시스턴트입니다."
)

CONTEXT_USER_TMPL = (
    "[전체 문서 시작]\n{doc}\n[전체 문서 끝]\n\n"
    "위 문서에서 다음 청크가 어떤 맥락에 속하는지 한두 문장으로 짧게 설명하세요. "
    "청크 자체를 반복하지 말고 위치/주제만 짚으세요.\n\n"
    "[청크]\n{chunk}\n\n"
    "[맥락 설명]"
)


class ContextualRetrievalRAG(BaseRAG):
    name = "07-contextual-retrieval"

    def __init__(self, collection: str = "contextual_rag", context_llm_provider: str = "openai"):
        self.embedder = EmbeddingModel()
        self.store = QdrantStore(collection, dim=self.embedder.dim)
        self.llm = GenerationLLM()
        self.context_llm = GenerationLLM(provider=context_llm_provider)

    def _contextualize(self, doc_text: str, chunk: str) -> str:
        return self.context_llm.raw(
            system=CONTEXT_SYSTEM,
            user=CONTEXT_USER_TMPL.format(doc=doc_text[:4000], chunk=chunk),
            temperature=0.2,
        )

    def build_index(self, documents: list[dict]) -> None:
        self.store.recreate()
        contextual_texts: list[str] = []
        payloads: list[dict] = []

        for doc in documents:
            doc_text = doc["text"]
            for chunk in semantic_chunk(doc_text):
                ctx = self._contextualize(doc_text, chunk)
                augmented = f"[문서 맥락] {ctx}\n[내용] {chunk}"
                contextual_texts.append(augmented)
                payloads.append(
                    {
                        "text": augmented,
                        "raw_chunk": chunk,
                        "context_blurb": ctx,
                        "doc_id": doc.get("id"),
                        "title": doc.get("title", ""),
                    }
                )

        vectors = self.embedder.encode(contextual_texts)
        self.store.upsert(vectors, payloads)
        logger.info("Contextual Retrieval 인덱스 구축: %d 청크", len(contextual_texts))

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        q_vec = self.embedder.encode_one(query)
        hits = self.store.search(q_vec, top_k=top_k)
        return [
            RetrievalResult(text=h.payload["raw_chunk"], score=h.score, metadata=h.payload) for h in hits
        ]

    def generate(self, query: str, top_k: int = 5) -> dict:
        results = self.retrieve(query, top_k=top_k)
        contexts = [r.text for r in results]
        answer = self.llm.generate(query, contexts)
        return {"answer": answer, "contexts": contexts, "raw_results": results}


if __name__ == "__main__":
    from data.sample.loader import load_all

    logging.basicConfig(level=logging.INFO)
    rag = ContextualRetrievalRAG()
    rag.build_index(load_all())
    out = rag.generate("Contextual Retrieval이 검색 실패율을 얼마나 줄이나요?")
    print("\n[답변]\n", out["answer"])
