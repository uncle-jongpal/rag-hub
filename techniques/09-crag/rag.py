"""CRAG (Corrective RAG) - 검색 결과 신뢰도 평가 후 보정/재검색 분기.

원논문(Yan et al., 2024)은 retrieval evaluator를 학습시켜 confident/ambiguous/incorrect 3단계로 분류합니다.
본 구현은 단순화를 위해 평가자를 프롬프트 기반으로 두고 fallback은 Multi-query 재검색으로 갈음합니다.
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


EVAL_SYSTEM = "당신은 검색된 컨텍스트가 질문에 답하기에 충분한지 평가하는 판정관입니다."

EVAL_USER = (
    "다음 컨텍스트가 질문에 답할 충분한 정보를 담고 있는지 한 단어로 평가하세요.\n"
    "- correct : 직접적 근거가 명확히 들어 있음\n"
    "- ambiguous : 부분적/간접적 근거만 있음\n"
    "- incorrect : 무관하거나 정보 부족\n\n"
    "질문: {query}\n\n컨텍스트:\n{context}\n\n평가:"
)

REWRITE_SYSTEM = "당신은 검색 회수율을 높이기 위해 질문을 더 검색 친화적으로 다시 쓰는 도우미입니다."

REWRITE_USER = (
    "다음 질문을 핵심 키워드 중심으로 다시 작성하세요. 짧게, 한 줄로.\n\n질문: {query}\n\n재작성:"
)


class CragRAG(BaseRAG):
    name = "09-crag"

    def __init__(self, collection: str = "crag_rag"):
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
        logger.info("CRAG 인덱스 구축: %d 청크", len(chunks))

    def _evaluate(self, query: str, contexts: list[str]) -> str:
        joined = "\n\n".join(f"({i + 1}) {c}" for i, c in enumerate(contexts))
        ans = self.llm.raw(
            system=EVAL_SYSTEM,
            user=EVAL_USER.format(query=query, context=joined),
            temperature=0.0,
        )
        ans_low = ans.lower()
        for label in ("correct", "ambiguous", "incorrect"):
            if re.search(rf"\b{label}\b", ans_low):
                return label
        return "ambiguous"

    def _rewrite(self, query: str) -> str:
        return self.llm.raw(
            system=REWRITE_SYSTEM,
            user=REWRITE_USER.format(query=query),
            temperature=0.3,
        ).strip().splitlines()[0]

    def _search(self, query: str, top_k: int) -> list[RetrievalResult]:
        q_vec = self.embedder.encode_one(query)
        hits = self.store.search(q_vec, top_k=top_k)
        return [RetrievalResult(text=h.payload["text"], score=h.score, metadata=h.payload) for h in hits]

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        first = self._search(query, top_k=top_k)
        verdict = self._evaluate(query, [r.text for r in first])
        logger.info("CRAG 평가: %s", verdict)

        if verdict == "correct":
            return first
        if verdict == "incorrect":
            rewritten = self._rewrite(query)
            return self._search(rewritten, top_k=top_k)
        # ambiguous - 원 질문 + 재작성 질문 결과를 합쳐 다양성 확보
        rewritten = self._rewrite(query)
        second = self._search(rewritten, top_k=top_k)
        seen: set[str] = set()
        merged: list[RetrievalResult] = []
        for r in first + second:
            if r.text in seen:
                continue
            seen.add(r.text)
            merged.append(r)
            if len(merged) >= top_k:
                break
        return merged

    def generate(self, query: str, top_k: int = 5) -> dict:
        results = self.retrieve(query, top_k=top_k)
        contexts = [r.text for r in results]
        answer = self.llm.generate(query, contexts) if contexts else "주어진 자료로는 답할 수 없습니다."
        return {"answer": answer, "contexts": contexts, "raw_results": results}


if __name__ == "__main__":
    from data.sample.loader import load_all

    logging.basicConfig(level=logging.INFO)
    rag = CragRAG()
    rag.build_index(load_all())
    out = rag.generate("Self-RAG의 reflection token 종류는?")
    print("\n[답변]\n", out["answer"])
