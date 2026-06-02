"""페이지 3 - 인터랙티브 검색 데모. 사용자가 직접 질문 입력."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import streamlit as st

from dashboard.components.labels import technique_card, technique_ko

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
    st.caption("기법을 직접 골라 질문을 입력하고, 검색된 컨텍스트 + 답변 + 토큰 사용량을 한 번에 확인합니다.")

    with st.expander("이 페이지 가이드", expanded=False):
        st.markdown("이 페이지는 실시간으로 한 기법을 돌려보는 페이지입니다. 평가 결과가 없어도 동작합니다.")
        st.markdown("사용 흐름")
        st.markdown("1. 기법 선택 - 옆에 그 기법의 의미가 표시됨")
        st.markdown("1. top_k 선택 - 검색 결과 몇 개를 LLM 에 전달할지")
        st.markdown("1. 질문 입력 후 실행 - 답변/컨텍스트/사용 토큰이 화면에 표시")
        st.warning("최초 실행 시 임베딩 모델 로드와 인덱싱에 30초-2분 정도 걸립니다. 두 번째부터는 캐시되어 빠릅니다.")

    col_t, col_k = st.columns([3, 1])
    with col_t:
        technique = st.selectbox(
            "기법 선택",
            list(TECHNIQUE_REGISTRY),
            format_func=technique_ko,
        )
    with col_k:
        top_k = st.number_input("top_k (검색 결과 수)", min_value=1, max_value=15, value=5)

    with st.expander(f"선택한 기법 설명 - {technique_ko(technique)}", expanded=True):
        st.markdown(technique_card(technique))

    query = st.text_input("질문 입력", placeholder="예) BGE-M3 임베딩 모델의 특징은?")

    if not query:
        return

    if st.button("실행"):
        from common.usage import get_tracker

        with st.spinner("인덱스 로드 + 검색 + LLM 답변 생성 중..."):
            tracker = get_tracker()
            tracker.reset()
            rag = _load_rag(technique)
            result = rag.generate(query, top_k=int(top_k))
            usage = tracker.snapshot()

        st.subheader("답변")
        st.write(result.get("answer", ""))

        st.subheader("사용된 컨텍스트")
        st.caption("LLM 이 답변을 만들 때 참고한 청크들입니다. 답변이 이 안에서 나왔는지 검증하실 수 있습니다.")
        for i, c in enumerate(result.get("contexts", []), 1):
            with st.expander(f"({i}) 청크 보기"):
                st.write(c)

        st.subheader("토큰/비용 (이번 호출 분만)")
        st.caption("미스트랄 무료 티어 사용 중이면 청구 비용은 0 입니다. 표시되는 추정 비용은 유료 단가 환산값으로, 가격 테이블에서 0 으로 설정된 경우 0 으로 표시됩니다.")
        totals = usage.get("totals", {})
        st.markdown(f"1. 호출 수 : {totals.get('calls', 0)}")
        st.markdown(f"1. 입력 토큰 : {totals.get('input_tokens', 0)}")
        st.markdown(f"1. 출력 토큰 : {totals.get('output_tokens', 0)}")
        st.markdown(f"1. 추정 비용 : ${totals.get('cost_usd', 0.0):.5f}")
        st.markdown(f"1. LLM 호출 시간 합계 : {totals.get('elapsed_seconds', 0.0):.2f}초")
