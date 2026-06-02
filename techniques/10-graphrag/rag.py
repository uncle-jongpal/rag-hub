"""GraphRAG (미니멀 버전) - 엔티티/관계 추출 + 커뮤니티 요약 1단계.

원논문(Microsoft, 2024)은 Leiden 알고리즘 기반 계층적 커뮤니티 탐지를 사용합니다.
본 구현은 학습 목적으로 다음을 단순화합니다.

1. 엔티티 추출 - LLM에 청크별 엔티티 + 관계 추출 요청
2. 그래프 빌드 - networkx 없이 dict 기반 간단 그래프
3. 커뮤니티 - 연결 컴포넌트 단위 (Leiden 미사용)
4. 요약 - 컴포넌트당 LLM 요약 1회
5. 검색 - 질문 임베딩 vs 컴포넌트 요약 임베딩 매칭
"""

from __future__ import annotations

import json
import logging
import re
from collections import defaultdict

from common.base import BaseRAG, RetrievalResult
from common.chunkers import semantic_chunk
from common.embeddings import EmbeddingModel
from common.llm import GenerationLLM
from common.vector_store import QdrantStore

logger = logging.getLogger(__name__)


EXTRACT_SYSTEM = "당신은 텍스트에서 핵심 엔티티와 관계를 JSON으로 추출하는 도우미입니다."

EXTRACT_USER = (
    "다음 텍스트에서 주요 엔티티(인물/조직/기술/개념)와 그들 사이 관계를 추출하세요. "
    "JSON으로만 출력하세요. 형식:\n"
    '{{"entities": ["A", "B", ...], "relations": [["A", "관계", "B"], ...]}}\n\n'
    "텍스트:\n{text}\n\nJSON:"
)

SUMMARY_SYSTEM = "당신은 엔티티/관계 묶음을 자연어로 요약하는 도우미입니다."

SUMMARY_USER = (
    "다음 엔티티와 관계들이 이루는 주제를 2-3문장으로 요약하세요.\n\n"
    "엔티티: {entities}\n관계: {relations}\n\n요약:"
)


def _extract_json(raw: str) -> dict:
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return {"entities": [], "relations": []}
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return {"entities": [], "relations": []}


class GraphRAG(BaseRAG):
    name = "10-graphrag"

    def __init__(self, collection: str = "graph_rag"):
        self.embedder = EmbeddingModel()
        self.store = QdrantStore(collection, dim=self.embedder.dim)
        self.llm = GenerationLLM()
        self._communities: list[dict] = []

    def _extract(self, text: str) -> dict:
        raw = self.llm.raw(
            system=EXTRACT_SYSTEM,
            user=EXTRACT_USER.format(text=text[:1500]),
            temperature=0.0,
        )
        return _extract_json(raw)

    def _build_communities(self, items: list[dict]) -> list[dict]:
        """연결 컴포넌트 단위로 커뮤니티 생성. networkx 없이 BFS."""
        adj: dict[str, set[str]] = defaultdict(set)
        entity_to_chunks: dict[str, set[int]] = defaultdict(set)

        for idx, item in enumerate(items):
            for ent in item.get("entities", []) or []:
                if not isinstance(ent, str) or not ent:
                    continue
                entity_to_chunks[ent].add(idx)
            for rel in item.get("relations", []) or []:
                if not isinstance(rel, (list, tuple)) or len(rel) < 3:
                    continue
                a, _rel, b = rel[0], rel[1], rel[2]
                if not isinstance(a, str) or not isinstance(b, str) or not a or not b:
                    continue
                adj[a].add(b)
                adj[b].add(a)

        seen: set[str] = set()
        components: list[set[str]] = []
        for ent in adj:
            if ent in seen:
                continue
            queue = [ent]
            comp: set[str] = set()
            while queue:
                cur = queue.pop()
                if cur in seen:
                    continue
                seen.add(cur)
                comp.add(cur)
                queue.extend(adj[cur] - seen)
            components.append(comp)

        for ent in entity_to_chunks:
            if ent not in seen:
                components.append({ent})
                seen.add(ent)

        communities: list[dict] = []
        for comp_idx, comp in enumerate(components):
            related_relations: list[list[str]] = []
            related_chunks: set[int] = set()
            for item in items:
                if any(e in comp for e in item["entities"]):
                    related_chunks.add(item["chunk_idx"])
                for a, rel, b in item["relations"]:
                    if a in comp or b in comp:
                        related_relations.append([a, rel, b])

            # 정렬 키에 None 이 섞이는 경우 가드 (LLM 추출 결과가 가끔 None 포함)
            entities_clean = sorted(e for e in comp if isinstance(e, str))
            chunk_indices_clean = sorted(i for i in related_chunks if isinstance(i, int))
            communities.append(
                {
                    "id": comp_idx,
                    "entities": entities_clean,
                    "relations": related_relations[:30],
                    "chunk_indices": chunk_indices_clean,
                }
            )
        return communities

    def build_index(self, documents: list[dict]) -> None:
        self.store.recreate()
        all_chunks: list[str] = []
        chunk_payloads: list[dict] = []
        items: list[dict] = []

        for doc in documents:
            for chunk in semantic_chunk(doc["text"]):
                idx = len(all_chunks)
                all_chunks.append(chunk)
                chunk_payloads.append({"text": chunk, "doc_id": doc.get("id")})
                ext = self._extract(chunk)
                ext["chunk_idx"] = idx
                items.append(ext)

        self._communities = self._build_communities(items)
        logger.info(
            "GraphRAG: %d 청크, %d 커뮤니티 생성",
            len(all_chunks),
            len(self._communities),
        )

        community_texts: list[str] = []
        community_payloads: list[dict] = []
        for c in self._communities:
            summary = self.llm.raw(
                system=SUMMARY_SYSTEM,
                user=SUMMARY_USER.format(entities=c["entities"], relations=c["relations"]),
                temperature=0.2,
            )
            text = f"[커뮤니티 #{c['id']}] {summary}\n관련 엔티티: {', '.join(c['entities'][:10])}"
            community_texts.append(text)
            community_payloads.append(
                {
                    "text": text,
                    "community_id": c["id"],
                    "chunk_indices": c["chunk_indices"],
                    "raw_chunks": [all_chunks[i] for i in c["chunk_indices"][:5]],
                }
            )

        if community_texts:
            vectors = self.embedder.encode(community_texts)
            self.store.upsert(vectors, community_payloads)

        self._all_chunks = all_chunks

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        q_vec = self.embedder.encode_one(query)
        hits = self.store.search(q_vec, top_k=min(top_k, 5))
        results: list[RetrievalResult] = []
        for h in hits:
            summary = h.payload["text"]
            raw = "\n\n".join(h.payload.get("raw_chunks", []))
            combined = f"{summary}\n\n[관련 단락]\n{raw}"
            results.append(
                RetrievalResult(text=combined, score=h.score, metadata=h.payload)
            )
        return results

    def generate(self, query: str, top_k: int = 5) -> dict:
        results = self.retrieve(query, top_k=top_k)
        contexts = [r.text for r in results]
        answer = self.llm.generate(query, contexts) if contexts else "관련 커뮤니티를 찾지 못했습니다."
        return {"answer": answer, "contexts": contexts, "raw_results": results}


if __name__ == "__main__":
    from data.sample.loader import load_all

    logging.basicConfig(level=logging.INFO)
    rag = GraphRAG()
    rag.build_index(load_all())
    out = rag.generate("이 자료에 등장하는 주요 RAG 기법들을 한 단락으로 요약해주세요.")
    print("\n[답변]\n", out["answer"])
