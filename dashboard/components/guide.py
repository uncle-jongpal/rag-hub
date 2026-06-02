"""페이지 5 - 가이드. 메트릭/기법/결과 해석 한 곳에서 학습."""

from __future__ import annotations

import streamlit as st

from dashboard.components.data import METRIC_NAMES
from dashboard.components.labels import METRICS, TECHNIQUES, technique_card


def render_guide() -> None:
    st.header("5. 가이드 - 메트릭과 기법 이해하기")
    st.caption("처음 보시는 분도 읽으면서 따라갈 수 있는 학습 페이지입니다.")

    st.markdown("---")
    st.subheader("이 레포는 무엇을 하는가")
    st.markdown(
        "이 대시보드는 RAG (Retrieval-Augmented Generation) 기법 13가지를 같은 데이터 위에서 비교 평가하는 도구입니다. "
        "RAG 는 대형 언어 모델이 외부 지식 베이스를 참조하여 답을 만드는 방식이고, 그 안에서 다양한 검색/청크/평가 전략이 발전해왔습니다."
    )
    st.markdown(
        "각 기법은 같은 인터페이스(build_index → retrieve → generate)로 동작하므로, 동일한 질문 셋에 대해 점수를 측정해 비교할 수 있습니다."
    )

    st.markdown("---")
    st.subheader("RAGAS 메트릭 네 가지")
    st.markdown("RAGAS 는 LLM 을 평가자로 활용해 RAG 시스템의 품질을 정량화하는 프레임워크입니다. 본 레포에서는 네 가지 핵심 메트릭을 사용합니다.")
    for name in METRIC_NAMES:
        m = METRICS[name]
        with st.expander(f"{m['ko']} ({name})", expanded=False):
            st.markdown(m["desc"])
            st.markdown(_metric_extra(name))

    st.markdown("---")
    st.subheader("결과 해석 가이드")
    st.markdown("1. 모든 점수가 동시에 높은 게 가장 좋지만, 트레이드오프가 있습니다")
    st.markdown("2. 충실도가 낮다 → 환각 발생. 검색 결과는 좋은데 답을 만들 때 LLM 이 자료를 무시하고 있음. 프롬프트 강화 또는 더 작은 모델 사용 검토")
    st.markdown("3. 답변 적합성이 낮다 → 답이 질문 핵심을 빗나감. 더 큰 LLM 또는 질문 처리(HyDE, Multi-query) 적용 검토")
    st.markdown("4. 검색 정확도가 낮다 → 검색에 무관한 청크가 많이 들어옴. Reranking 추가, 청크 크기 조정 검토")
    st.markdown("5. 검색 완전성이 낮다 → 정답에 필요한 정보가 검색에 빠짐. Hybrid Search, Multi-query, 청크 오버랩 늘리기")
    st.markdown("6. NaN 으로 표시된다 → 평가 LLM 호출 실패 또는 한도 초과로 측정 못 한 항목. 재실행 시 천천히 (max_workers 작게)")

    st.markdown("---")
    st.subheader("기법 13가지 한눈 보기")
    st.caption("각 기법의 한 줄 요약과 어떤 상황에 잘 맞는지 정리했습니다. 자세한 내용은 기법명 클릭.")
    for tid in TECHNIQUES:
        with st.expander(f"{tid} · {TECHNIQUES[tid]['ko']}", expanded=False):
            st.markdown(technique_card(tid))

    st.markdown("---")
    st.subheader("실제 운영 시작 추천 순서")
    st.markdown("1. 단순 임베딩 검색 (01) 으로 베이스라인 점수 확보 - 빠르게 동작 확인")
    st.markdown("2. 하이브리드 검색 (02) 추가 - 한국어 환경에서 큰 효과, 운영 표준")
    st.markdown("3. 재정렬 (03) 추가 - 검색 정확도가 답 품질의 병목이면 적용")
    st.markdown("4. 문맥 보강 검색 (07) - 청크 단독으로 모호한 도메인 (법률/메뉴얼/사내 문서)")
    st.markdown("5. 가설 답변 (04) 또는 다중 질문 (05) - 사용자 질문이 짧거나 모호할 때")
    st.markdown("6. 자가 평가 (08) / 교정 (09) - 환각 통제, 검색 실패 회복")
    st.markdown("7. 그래프 (10) / 트리 (11) - 요약형/전체 조망 질문이 많을 때")
    st.markdown("8. 에이전트 (12) / 적응형 (13) - 다단계 추론, 질문 다양성이 큰 환경")

    st.markdown("---")
    st.subheader("이 대시보드의 한계 + 참고")
    st.markdown("1. 본 평가는 데모셋(한 30 + 영 30) 기준입니다. 도메인 데이터로 재평가하지 않으면 운영 의사결정에 그대로 쓰기 어렵습니다")
    st.markdown("2. 일부 기법(GraphRAG, RAPTOR, Self-RAG, CRAG, Adaptive) 은 원논문의 단순화 버전 구현입니다. 풀스펙은 더 무겁고 정확합니다")
    st.markdown("3. 미스트랄 무료 티어를 사용하면 분당 호출 한도로 평가에 시간이 걸립니다. 한 기법당 약 12분 (질문 3개 기준) 예상")
    st.markdown("4. 자세한 원논문 / 공식 구현은 docs/references.md 에 통합 정리되어 있습니다")


def _metric_extra(name: str) -> str:
    extras = {
        "faithfulness": "계산 방식 - 답변을 문장 단위로 쪼개고, 각 문장이 컨텍스트에 의해 지지되는지 LLM 으로 판정합니다. 컨텍스트 밖 정보가 많을수록 점수가 떨어집니다.",
        "answer_relevancy": "계산 방식 - 답변으로부터 가상의 질문 N개를 생성하고, 그 질문들과 원 질문의 임베딩 유사도를 평균냅니다. 임베딩이 필요해서 실패할 수 있습니다 (본 레포는 BGE-M3 사용).",
        "context_precision": "계산 방식 - 검색된 컨텍스트 중 정답에 직접적으로 기여한 청크의 비율. 컨텍스트 순위까지 반영합니다 (앞순위에 정답이 있으면 점수가 높음).",
        "context_recall": "계산 방식 - 정답 텍스트의 각 주장(claim)이 검색된 컨텍스트에 의해 지지되는지 본 비율. 정답 라벨이 필요한 메트릭입니다.",
    }
    return extras.get(name, "")
