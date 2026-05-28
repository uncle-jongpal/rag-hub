"""페이지 3 - 인터랙티브 검색 데모. 사용자가 직접 질문 입력."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent

TECHNIQUE_REGISTRY: dict[str, tuple[str, str]] = {
    "01-naive": ("01-naive", "NaiveRAG"),
    "02-hybrid-search": ("02-hybrid-search", "HybridRAG"),
    "03-reranking": ("03-reranking", "RerankingRAG"),
    "04-hyde": ("04-hyde", "HydeRAG"),
    "05-multi-query": ("05-multi-query", "MultiQueryRAG"),
    "06-parent-child": ("06-parent-child", "ParentChildRAG"),
    "07-contextual-retrieval": ("07-contextual-retrieval", "ContextualRetrievalRAG"),
    "08-self-rag": ("08-self-rag", "SelfRAG"),
    "09-crag": ("09-crag", "CragRAG"),
    "10-graphrag": ("10-graphrag", "GraphRAG"),
    "11-raptor": ("11-raptor", "RaptorRAG"),
    "12-agentic-rag": ("12-agentic-rag", "AgenticRAG"),
    "13-adaptive-rag": ("13-adaptive-rag", "AdaptiveRAG"),
}


@st.cache_resource
def _load_rag(technique_id: str):
    folder, class_name = TECHNIQUE_REGISTRY[technique_id]
    rag_path = ROOT / "techniques" / folder / "rag.py"
    spec = importlib.util.spec_from_file_location(f"rag_{technique_id}", rag_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rag = getattr(module, class_name)()
    from data.sample.loader import load_all

    rag.build_index(load_all())
    return rag


def render_demo() -> None:
    st.header("3. 인터랙티브 검색 데모")
    st.caption("기법을 선택하고 직접 질문을 입력해 답변/컨텍스트를 확인합니다.")
    st.warning("최초 실행 시 임베딩 모델 로드 + Qdrant 인덱싱에 30초-2분 정도 소요됩니다. 캐시되어 두 번째부터 빠릅니다.")

    col_t, col_k = st.columns([3, 1])
    with col_t:
        technique = st.selectbox("기법 선택", list(TECHNIQUE_REGISTRY))
    with col_k:
        top_k = st.number_input("top_k", min_value=1, max_value=15, value=5)

    query = st.text_input("질문 입력", placeholder="예: BGE-M3 임베딩 모델의 특징은?")

    if not query:
        return

    if st.button("실행"):
        from common.usage import get_tracker

        with st.spinner("인덱스 로드 + 추론 중..."):
            tracker = get_tracker()
            tracker.reset()
            rag = _load_rag(technique)
            result = rag.generate(query, top_k=int(top_k))
            usage = tracker.snapshot()

        st.subheader("답변")
        st.write(result.get("answer", ""))

        st.subheader("사용된 컨텍스트")
        for i, c in enumerate(result.get("contexts", []), 1):
            with st.expander(f"({i})"):
                st.write(c)

        st.subheader("토큰/비용 (이번 호출만)")
        totals = usage.get("totals", {})
        st.markdown(f"1. 호출 수 : {totals.get('calls', 0)}")
        st.markdown(f"1. 입력 토큰 : {totals.get('input_tokens', 0)}")
        st.markdown(f"1. 출력 토큰 : {totals.get('output_tokens', 0)}")
        st.markdown(f"1. 추정 비용 : ${totals.get('cost_usd', 0.0):.5f}")
        st.markdown(f"1. LLM 호출 시간 합계 : {totals.get('elapsed_seconds', 0.0):.2f}초")
