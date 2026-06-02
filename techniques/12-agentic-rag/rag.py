"""Agentic RAG (ReAct 스타일) - LLM이 search/calc 도구를 선택해 호출.

ReAct 패턴: Thought → Action → Observation 반복 후 Final Answer.
본 구현은 OpenAI function calling이 아닌 텍스트 파싱 기반 단순 ReAct 루프입니다.
실 운영에서는 function calling API 사용을 권장합니다.
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


REACT_SYSTEM = """당신은 도구를 사용해 사용자 질문에 답하는 어시스턴트입니다.

사용 가능한 도구
- search(query): 지식 베이스 검색. 핵심 키워드를 query로 넘기세요
- calc(expression): 산수 계산. 예: calc("3 + 4 * 2")
- final(answer): 최종 답변

응답 형식 (반드시 한 행씩 분리)
Thought: 무엇을 할지 한 문장으로 생각
Action: 도구이름
Action Input: 입력값

다음 차례 메시지로 Observation이 주어지면 다시 Thought → Action 으로 반복.
충분한 정보가 모이면 Action: final, Action Input: 최종답변.
최대 4회까지 도구 호출 가능합니다.
"""


def _parse_action(text: str) -> tuple[str, str] | None:
    action_match = re.search(r"Action\s*:\s*(\w+)", text)
    input_match = re.search(r"Action Input\s*:\s*(.+?)(?:\n|$)", text, re.DOTALL)
    if not action_match:
        return None
    action = action_match.group(1).strip().lower()
    arg = (input_match.group(1).strip() if input_match else "").strip("\"' ")
    return action, arg


def _calc(expr: str) -> str:
    try:
        if not re.fullmatch(r"[\d\s+\-*/().]+", expr):
            return "오류: 허용되지 않은 문자가 포함되어 있습니다."
        return str(eval(expr))  # noqa: S307 - 정규식으로 입력 제한, 학습 데모용
    except Exception as e:  # noqa: BLE001
        return f"오류: {e}"


class AgenticRAG(BaseRAG):
    name = "12-agentic-rag"

    def __init__(self, collection: str = "agentic_rag", max_steps: int = 4):
        self.embedder = EmbeddingModel()
        self.store = QdrantStore(collection, dim=self.embedder.dim)
        self.llm = GenerationLLM()
        self.max_steps = max_steps

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
        logger.info("Agentic RAG 인덱스 구축: %d 청크", len(chunks))

    def _tool_search(self, query: str, top_k: int = 4) -> list[str]:
        q_vec = self.embedder.encode_one(query)
        hits = self.store.search(q_vec, top_k=top_k)
        return [h.payload["text"] for h in hits]

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        """ReAct 루프 내부에서 사용된 검색 결과들을 누적해 반환."""
        # generate에서 contexts를 채우므로 여기서는 단순 1회 검색만 수행
        q_vec = self.embedder.encode_one(query)
        hits = self.store.search(q_vec, top_k=top_k)
        return [RetrievalResult(text=h.payload["text"], score=h.score, metadata=h.payload) for h in hits]

    def generate(self, query: str, top_k: int = 5) -> dict:
        scratch = [f"Question: {query}"]
        used_contexts: list[str] = []
        final_answer = ""

        for step in range(self.max_steps):
            prompt = "\n".join(scratch) + "\n"
            response = self.llm.raw(system=REACT_SYSTEM, user=prompt, temperature=0.1)
            parsed = _parse_action(response)
            if not parsed:
                final_answer = response.strip()
                break
            action, arg = parsed
            logger.info("Step %d: %s(%s)", step + 1, action, arg[:40])

            if action == "final":
                final_answer = arg
                break

            if action == "search":
                results = self._tool_search(arg, top_k=top_k)
                used_contexts.extend(results)
                observation = "\n---\n".join(results) if results else "검색 결과 없음"
            elif action == "calc":
                observation = _calc(arg)
            else:
                observation = f"알 수 없는 도구: {action}"

            scratch.append(response.strip())
            scratch.append(f"Observation: {observation}")
        else:
            # max_steps 도달
            final_answer = self.llm.generate(query, used_contexts) if used_contexts else "단계 한도에 도달했습니다."

        return {
            "answer": final_answer,
            "contexts": list(dict.fromkeys(used_contexts)),
            "raw_results": [],
        }


if __name__ == "__main__":
    from data.sample.loader import load_all

    logging.basicConfig(level=logging.INFO)
    rag = AgenticRAG()
    rag.build_index(load_all())
    out = rag.generate("RAPTOR는 어떤 클러스터링 방식을 쓰며, 깊이 3 트리에 노드가 최대 몇 개 생기는가?")
    print("\n[답변]\n", out["answer"])
