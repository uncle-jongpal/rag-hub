"""Self-RAG (단순화 버전) - LLM이 검색 필요 여부와 결과 유용성을 자가 평가.

원논문(Asai et al., 2023)은 reflection token을 별도 fine-tune으로 학습합니다.
본 구현은 GPT-4 같은 generalist 모델에 동일한 의사결정을 프롬프트로 시키는 버전입니다.
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


NEED_RETRIEVAL_SYSTEM = (
    "당신은 사용자 질문이 외부 문서 검색을 필요로 하는지 판단하는 분류기입니다. "
    "단순 산수, 일반 상식, 메타 질문(예: 너는 누구야)은 검색이 불필요합니다. "
    "사실 조회, 도메인 지식, 최신 정보는 검색이 필요합니다."
)

NEED_RETRIEVAL_USER = (
    "다음 질문에 답하기 위해 외부 문서 검색이 필요합니까? "
    "yes 또는 no 만 출력하세요.\n\n질문: {query}\n\n답:"
)

GRADE_SYSTEM = "당신은 검색된 단락이 질문에 유용한지 판단하는 평가자입니다."

GRADE_USER = (
    "질문에 답하기 위해 아래 단락이 직접적인 근거가 될 수 있습니까? "
    "relevant 또는 irrelevant 만 출력하세요.\n\n"
    "질문: {query}\n\n단락: {chunk}\n\n판단:"
)


class SelfRAG(BaseRAG):
    name = "08-self-rag"

    def __init__(self, collection: str = "self_rag"):
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
        logger.info("Self-RAG 인덱스 구축: %d 청크", len(chunks))

    def _needs_retrieval(self, query: str) -> bool:
        ans = self.llm.raw(
            system=NEED_RETRIEVAL_SYSTEM,
            user=NEED_RETRIEVAL_USER.format(query=query),
            temperature=0.0,
        )
        return bool(re.search(r"\byes\b", ans.lower()))

    def _grade(self, query: str, chunk: str) -> bool:
        ans = self.llm.raw(
            system=GRADE_SYSTEM,
            user=GRADE_USER.format(query=query, chunk=chunk),
            temperature=0.0,
        )
        return "relevant" in ans.lower() and "irrelevant" not in ans.lower()

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        if not self._needs_retrieval(query):
            logger.info("검색 불필요 판정: %s", query[:40])
            return []
        q_vec = self.embedder.encode_one(query)
        hits = self.store.search(q_vec, top_k=top_k * 2)
        filtered: list[RetrievalResult] = []
        for h in hits:
            if self._grade(query, h.payload["text"]):
                filtered.append(
                    RetrievalResult(text=h.payload["text"], score=h.score, metadata=h.payload)
                )
            if len(filtered) >= top_k:
                break
        return filtered

    def generate(self, query: str, top_k: int = 5) -> dict:
        results = self.retrieve(query, top_k=top_k)
        contexts = [r.text for r in results]
        if not contexts:
            answer = self.llm.raw(
                system="당신은 일반 지식 어시스턴트입니다. 한국어 질문은 한국어로, 영어 질문은 영어로 답하세요.",
                user=query,
                temperature=0.1,
            )
        else:
            answer = self.llm.generate(query, contexts)
        return {"answer": answer, "contexts": contexts, "raw_results": results}


if __name__ == "__main__":
    from data.sample.loader import load_all

    logging.basicConfig(level=logging.INFO)
    rag = SelfRAG()
    rag.build_index(load_all())
    for q in ["BGE-M3는 누가 만든 모델입니까?", "2 + 2는?"]:
        print(f"\n>>> {q}")
        out = rag.generate(q)
        print("답변:", out["answer"][:200])
        print("컨텍스트 수:", len(out["contexts"]))
