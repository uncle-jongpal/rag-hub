"""RAPTOR - 청크 클러스터링 + LLM 요약으로 트리 인덱싱 (깊이 3단계).

원논문(Sarthi et al., 2024)은 GMM 기반 soft clustering + UMAP 차원 축소를 사용합니다.
본 구현은 단순화를 위해 KMeans + 원본 임베딩을 그대로 씁니다.

깊이 구성:
- L0 (leaf) - 원본 청크 임베딩
- L1 (mid) - leaf 클러스터 요약 임베딩
- L2 (root) - L1 클러스터 요약 임베딩 (전체 코퍼스 글로벌 요약)
"""

from __future__ import annotations

import logging

import numpy as np
from sklearn.cluster import KMeans

from common.base import BaseRAG, RetrievalResult
from common.chunkers import semantic_chunk
from common.embeddings import EmbeddingModel
from common.llm import GenerationLLM
from common.vector_store import QdrantStore

logger = logging.getLogger(__name__)


SUMMARY_SYSTEM = "당신은 여러 단락의 핵심을 합쳐 요약하는 도우미입니다."

SUMMARY_USER = (
    "다음 단락들의 공통 주제와 핵심 내용을 3-4문장으로 요약하세요. "
    "원문 표현을 가능한 한 유지하고, 구체적 명사/수치는 보존하세요.\n\n"
    "단락들:\n{passages}\n\n요약:"
)


def _kmeans_cluster(vectors: np.ndarray, n_clusters: int) -> list[list[int]]:
    if len(vectors) <= n_clusters:
        return [[i] for i in range(len(vectors))]
    km = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
    labels = km.fit_predict(vectors)
    groups: dict[int, list[int]] = {}
    for i, lab in enumerate(labels):
        groups.setdefault(int(lab), []).append(i)
    return list(groups.values())


class RaptorRAG(BaseRAG):
    name = "11-raptor"

    def __init__(
        self,
        collection: str = "raptor_rag",
        n_mid_clusters: int = 6,
        n_root_clusters: int = 2,
    ):
        self.embedder = EmbeddingModel()
        self.store = QdrantStore(collection, dim=self.embedder.dim)
        self.llm = GenerationLLM()
        self.n_mid = n_mid_clusters
        self.n_root = n_root_clusters

    def _summarize(self, passages: list[str]) -> str:
        joined = "\n\n---\n\n".join(passages)
        return self.llm.raw(
            system=SUMMARY_SYSTEM,
            user=SUMMARY_USER.format(passages=joined[:4000]),
            temperature=0.2,
        )

    def build_index(self, documents: list[dict]) -> None:
        self.store.recreate()

        # L0: leaf chunks
        leaves: list[str] = []
        leaf_payloads: list[dict] = []
        for doc in documents:
            for chunk in semantic_chunk(doc["text"]):
                leaves.append(chunk)
                leaf_payloads.append(
                    {"text": chunk, "level": 0, "doc_id": doc.get("id")}
                )
        leaf_vecs = self.embedder.encode(leaves)
        self.store.upsert(leaf_vecs, leaf_payloads)
        logger.info("L0 leaf 색인 완료: %d", len(leaves))

        # L1: mid clusters
        mid_summaries: list[str] = []
        mid_payloads: list[dict] = []
        groups = _kmeans_cluster(leaf_vecs, self.n_mid)
        for gi, group in enumerate(groups):
            summary = self._summarize([leaves[i] for i in group])
            mid_summaries.append(summary)
            mid_payloads.append(
                {
                    "text": summary,
                    "level": 1,
                    "cluster_id": gi,
                    "leaf_indices": group,
                    "raw_chunks": [leaves[i] for i in group[:4]],
                }
            )
        if mid_summaries:
            mid_vecs = self.embedder.encode(mid_summaries)
            self.store.upsert(mid_vecs, mid_payloads)
        logger.info("L1 mid 색인 완료: %d", len(mid_summaries))

        # L2: root clusters
        if len(mid_summaries) >= 2:
            root_groups = _kmeans_cluster(mid_vecs, min(self.n_root, len(mid_summaries)))
            root_summaries: list[str] = []
            root_payloads: list[dict] = []
            for gi, group in enumerate(root_groups):
                summary = self._summarize([mid_summaries[i] for i in group])
                root_summaries.append(summary)
                root_payloads.append(
                    {
                        "text": summary,
                        "level": 2,
                        "cluster_id": gi,
                        "mid_indices": group,
                    }
                )
            if root_summaries:
                root_vecs = self.embedder.encode(root_summaries)
                self.store.upsert(root_vecs, root_payloads)
            logger.info("L2 root 색인 완료: %d", len(root_summaries))

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        q_vec = self.embedder.encode_one(query)
        hits = self.store.search(q_vec, top_k=top_k * 2)
        # 모든 레벨 결과를 섞어 가져오되 점수 순으로 top_k
        hits = sorted(hits, key=lambda h: h.score, reverse=True)[:top_k]
        return [RetrievalResult(text=h.payload["text"], score=h.score, metadata=h.payload) for h in hits]

    def generate(self, query: str, top_k: int = 5) -> dict:
        results = self.retrieve(query, top_k=top_k)
        contexts = [r.text for r in results]
        answer = self.llm.generate(query, contexts) if contexts else "검색 결과가 없습니다."
        return {"answer": answer, "contexts": contexts, "raw_results": results}


if __name__ == "__main__":
    from data.sample.loader import load_all

    logging.basicConfig(level=logging.INFO)
    rag = RaptorRAG()
    rag.build_index(load_all())
    out = rag.generate("RAG 분야에서 검색 기법은 어떻게 발전해왔습니까?")
    print("\n[답변]\n", out["answer"])
