"""평가 결과 JSON 로더 - 모든 페이지에서 공용."""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

RESULTS_DIR = Path(__file__).resolve().parent.parent.parent / "evaluation" / "results"


@st.cache_data(ttl=60)
def list_results() -> list[dict]:
    items: list[dict] = []
    for p in sorted(RESULTS_DIR.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        # 파일명: <technique>-YYYYMMDD-HHMMSS.json
        stem = p.stem
        parts = stem.rsplit("-", 2)
        if len(parts) < 3:
            continue
        technique = parts[0]
        items.append({"path": str(p), "technique": technique, "data": data, "stem": stem})
    return items


@st.cache_data(ttl=60)
def latest_by_technique() -> dict[str, dict]:
    """기법별 가장 최신 결과 1개씩."""
    by_tech: dict[str, dict] = {}
    for item in list_results():
        cur = by_tech.get(item["technique"])
        if cur is None or item["stem"] > cur["stem"]:
            by_tech[item["technique"]] = item
    return by_tech


METRIC_NAMES = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]


def empty_state(message: str = "평가 결과가 없습니다. ragas_eval.py 를 먼저 실행하세요."):
    st.info(message)
