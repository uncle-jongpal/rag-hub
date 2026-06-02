"""Qdrant 벡터 DB 래퍼 - 컬렉션 생성/색인/검색을 단순화."""

import logging
import uuid
from dataclasses import dataclass

import numpy as np

from common.config import settings

logger = logging.getLogger(__name__)


@dataclass
class HitResult:
    id: str
    score: float
    payload: dict


class QdrantStore:
    def __init__(self, collection: str, dim: int):
        from qdrant_client import QdrantClient

        # check_compatibility=False - 클라이언트/서버 마이너 버전 차이 경고 무시 (도커 이미지 1.12.x 사용)
        self.client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key or None,
            check_compatibility=False,
        )
        self.collection = collection
        self.dim = dim

    def recreate(self) -> None:
        """기존 컬렉션 삭제 후 재생성. PoC/평가 반복 시 유용."""
        from qdrant_client.http import models as qm

        self.client.delete_collection(self.collection, timeout=30)
        self.client.create_collection(
            collection_name=self.collection,
            vectors_config=qm.VectorParams(size=self.dim, distance=qm.Distance.COSINE),
        )
        logger.info("컬렉션 재생성: %s (dim=%d)", self.collection, self.dim)

    def ensure(self) -> None:
        from qdrant_client.http import models as qm

        existing = [c.name for c in self.client.get_collections().collections]
        if self.collection not in existing:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=qm.VectorParams(size=self.dim, distance=qm.Distance.COSINE),
            )
            logger.info("컬렉션 생성: %s", self.collection)

    def upsert(self, vectors: np.ndarray, payloads: list[dict]) -> None:
        from qdrant_client.http import models as qm

        if len(vectors) != len(payloads):
            raise ValueError("vector/payload 길이 불일치")
        points = [
            qm.PointStruct(id=str(uuid.uuid4()), vector=vec.tolist(), payload=pl)
            for vec, pl in zip(vectors, payloads, strict=True)
        ]
        self.client.upsert(collection_name=self.collection, points=points)

    def search(self, query_vec: np.ndarray, top_k: int = 5) -> list[HitResult]:
        # qdrant-client 1.18+ 에서 search 메서드가 제거되고 query_points 로 통일됨
        result = self.client.query_points(
            collection_name=self.collection,
            query=query_vec.tolist(),
            limit=top_k,
            with_payload=True,
        )
        hits = result.points
        return [HitResult(id=str(h.id), score=h.score, payload=h.payload or {}) for h in hits]
