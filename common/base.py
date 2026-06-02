"""모든 RAG 기법이 구현해야 할 공통 인터페이스."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class RetrievalResult:
    text: str
    score: float
    metadata: dict


class BaseRAG(ABC):
    name: str = "base"

    @abstractmethod
    def build_index(self, documents: list[dict]) -> None:
        """문서 리스트를 받아 인덱스를 구축한다.

        documents: [{"id": str, "text": str, "metadata": dict}, ...]
        """
        ...

    @abstractmethod
    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        """질문에 대해 관련 문서를 top_k개 반환."""
        ...

    @abstractmethod
    def generate(self, query: str, top_k: int = 5) -> dict:
        """retrieve + LLM 호출까지 한 번에. 답변 + 사용된 컨텍스트 반환.

        반환 형식: {"answer": str, "contexts": list[str], "raw_results": list[RetrievalResult]}
        """
        ...
