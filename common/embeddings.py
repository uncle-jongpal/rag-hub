"""임베딩 모델 래퍼 - BGE-M3 기본, OpenAI 임베딩도 지원."""

import logging

import numpy as np

from common.config import settings

logger = logging.getLogger(__name__)


class EmbeddingModel:
    """sentence-transformers 기반 임베딩. BGE-M3 디폴트."""

    def __init__(self, model_name: str | None = None):
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name or settings.embedding_model
        logger.info("임베딩 모델 로드: %s", self.model_name)
        self.model = SentenceTransformer(self.model_name)
        self._dim: int | None = None

    @property
    def dim(self) -> int:
        if self._dim is None:
            # sentence-transformers 5.x 에서 get_sentence_embedding_dimension 이 get_embedding_dimension 으로 개명됨
            getter = getattr(self.model, "get_embedding_dimension", None) or self.model.get_sentence_embedding_dimension
            self._dim = getter()
        return self._dim

    def encode(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        """문서/질문 리스트를 벡터 행렬(N, dim)로 변환. L2 정규화 적용."""
        return self.model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

    def encode_one(self, text: str) -> np.ndarray:
        return self.encode([text])[0]


class OpenAIEmbedding:
    """오픈AI text-embedding-3-small 등을 사용하는 대안 백엔드."""

    def __init__(self, model: str = "text-embedding-3-small"):
        from openai import OpenAI

        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = model
        self._dim = {"text-embedding-3-small": 1536, "text-embedding-3-large": 3072}.get(model, 1536)

    @property
    def dim(self) -> int:
        return self._dim

    def encode(self, texts: list[str], batch_size: int = 100) -> np.ndarray:
        all_vecs: list[list[float]] = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            resp = self.client.embeddings.create(model=self.model, input=batch)
            all_vecs.extend([d.embedding for d in resp.data])
        return np.array(all_vecs)
