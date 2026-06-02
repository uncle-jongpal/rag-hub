"""LLM 토큰/비용 추적 - 호출 횟수, 입출력 토큰, 추정 비용을 누적."""

from __future__ import annotations

import threading
import time
from dataclasses import asdict, dataclass, field

# 모델별 1M 토큰당 USD 단가 (2026-05 기준, 입력/출력 분리)
PRICE_TABLE: dict[str, tuple[float, float]] = {
    "gpt-4o": (2.5, 10.0),
    "gpt-4o-mini": (0.15, 0.6),
    "gpt-4.1": (3.0, 12.0),
    "gpt-4.1-mini": (0.4, 1.6),
    "claude-opus-4-7": (15.0, 75.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-haiku-4-5": (1.0, 5.0),
    # 미스트랄 - 사용자분이 La Plateforme 무료(Experiment) 티어 운영, 결제 카드 미등록.
    # 무료 한도 안이면 청구 0. 추정 비용 표시를 0으로 통일해 대시보드/결과 JSON에 0 표시.
    "mistral-large-latest": (0.0, 0.0),
    "mistral-medium-latest": (0.0, 0.0),
    "mistral-small-latest": (0.0, 0.0),
    "mistral-tiny": (0.0, 0.0),
    "open-mistral-7b": (0.0, 0.0),
    "open-mixtral-8x7b": (0.0, 0.0),
}


@dataclass
class UsageRecord:
    model: str
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    elapsed_seconds: float = 0.0


def estimate_cost(model: str, in_tok: int, out_tok: int) -> float:
    if model not in PRICE_TABLE:
        return 0.0
    in_price, out_price = PRICE_TABLE[model]
    return in_tok / 1_000_000 * in_price + out_tok / 1_000_000 * out_price


class UsageTracker:
    """프로세스 단위 누적 카운터. thread-safe."""

    def __init__(self):
        self._lock = threading.Lock()
        self._records: dict[str, UsageRecord] = {}

    def record(self, model: str, in_tok: int, out_tok: int, elapsed: float) -> None:
        with self._lock:
            rec = self._records.setdefault(model, UsageRecord(model=model))
            rec.calls += 1
            rec.input_tokens += in_tok
            rec.output_tokens += out_tok
            rec.cost_usd += estimate_cost(model, in_tok, out_tok)
            rec.elapsed_seconds += elapsed

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "by_model": {k: asdict(v) for k, v in self._records.items()},
                "totals": {
                    "calls": sum(r.calls for r in self._records.values()),
                    "input_tokens": sum(r.input_tokens for r in self._records.values()),
                    "output_tokens": sum(r.output_tokens for r in self._records.values()),
                    "cost_usd": round(sum(r.cost_usd for r in self._records.values()), 5),
                    "elapsed_seconds": round(sum(r.elapsed_seconds for r in self._records.values()), 3),
                },
            }

    def reset(self) -> None:
        with self._lock:
            self._records.clear()


_TRACKER = UsageTracker()


def get_tracker() -> UsageTracker:
    return _TRACKER


def stopwatch():
    """간단 타이머 컨텍스트 - with stopwatch() as t: ... ; t.elapsed."""

    class _SW:
        def __enter__(self):
            self._start = time.monotonic()
            return self

        def __exit__(self, *_):
            self.elapsed = time.monotonic() - self._start

    return _SW()
