"""HyDE (Hypothetical Document Embeddings) - LLM이 만든 가설 답변으로 검색."""

from __future__ import annotations

import logging

from common.base import BaseRAG, RetrievalResult
from common.chunkers import semantic_chunk
from common.embeddings import EmbeddingModel
from common.llm import GenerationLLM
from common.vector_store import QdrantStore

logger = logging.getLogger(__name__)


HYDE_SYSTEM = (
    "당신은 정보 검색을 돕기 위해 가상의 답변을 생성합니다. "
    "정확성보다 답변의 어휘/문체가 실제 문서 본문과 유사하도록 작성하세요. "
    "한국어 질문에는 한국어로, 영어 질문에는 영어로 작성하세요."
)

HYDE_USER_TMPL = "다음 질문에 대한 가상의 짧은 단락(3-5문장) 답변을 작성하세요.\n\n질문: {query}\n\n답변:"


class HydeRAG(BaseRAG):
    name = "04-hyde"

    def __init__(self, collection: str = "hyde_rag"):
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
        logger.info("HyDE 인덱스 구축: %d 청크", len(chunks))

    def _hypothetical(self, query: str) -> str:
        return self.llm.raw(
            system=HYDE_SYSTEM,
            user=HYDE_USER_TMPL.format(query=query),
            temperature=0.5,
        )

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        hypo = self._hypothetical(query)
        logger.debug("가설 답변: %s", hypo[:100])
        q_vec = self.embedder.encode_one(hypo)
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
    rag = HydeRAG()
    rag.build_index(load_all())
    out = rag.generate("프롬프트 캐싱이 비용 절감에 어떻게 도움이 됩니까?")
    print("\n[답변]\n", out["answer"])
