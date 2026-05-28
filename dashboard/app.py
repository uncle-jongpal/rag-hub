"""RAG Hub 대시보드 (Streamlit).

실행:
    uv run streamlit run dashboard/app.py

V3 범위
1. 기법 비교 - 13개 기법의 RAGAS 4종 메트릭 차트
2. 질문별 결과 보기 - 질문 선택 → 기법별 답변/컨텍스트 나란히
3. 인터랙티브 검색 데모 - 사용자 질문 입력 → 단일 기법 실행
4. 비용/지연 추적 - 저장된 results JSON의 usage 통계 시각화
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dashboard.components.compare import render_compare  # noqa: E402
from dashboard.components.cost import render_cost  # noqa: E402
from dashboard.components.demo import render_demo  # noqa: E402
from dashboard.components.questions import render_questions  # noqa: E402

st.set_page_config(
    page_title="RAG Hub",
    page_icon=":mag:",
    layout="wide",
)

st.title("RAG Hub - 기법 비교 대시보드")
st.caption("13개 RAG 기법의 RAGAS 평가 결과를 비교하고 인터랙티브 검색 데모를 실행합니다.")

page = st.sidebar.radio(
    "페이지",
    ["1. 기법 비교", "2. 질문별 결과", "3. 인터랙티브 검색", "4. 비용/지연 추적"],
    index=0,
)

st.sidebar.divider()
st.sidebar.markdown("출처 - docs/references.md")
st.sidebar.markdown("저장된 결과 - evaluation/results/")

if page.startswith("1"):
    render_compare()
elif page.startswith("2"):
    render_questions()
elif page.startswith("3"):
    render_demo()
elif page.startswith("4"):
    render_cost()
