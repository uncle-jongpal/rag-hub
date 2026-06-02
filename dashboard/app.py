"""RAG Frame 대시보드 (Streamlit).

실행:
    streamlit run dashboard/app.py
또는 도커:
    docker compose up -d dashboard

페이지 구성
1. 기법 비교 - 메트릭별 차트 + 기법 한국어 설명
2. 질문별 결과 - 같은 질문에 대한 기법별 답변 비교
3. 인터랙티브 검색 - 직접 질문 입력 + 단일 기법 실행
4. 비용/지연 추적 - LLM 호출 비용/시간 시각화
5. 가이드 - 메트릭/기법/결과 해석법 학습 페이지
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
from dashboard.components.guide import render_guide  # noqa: E402
from dashboard.components.questions import render_questions  # noqa: E402

st.set_page_config(
    page_title="RAG Frame - 기법 비교 대시보드",
    page_icon=":mag:",
    layout="wide",
)

st.title("RAG Frame - 기법 비교 대시보드")
st.caption("13개 RAG 기법을 같은 데이터셋에서 정량 비교하고, 직접 질문을 입력해 결과를 확인합니다.")

st.sidebar.markdown("페이지 이동")
page = st.sidebar.radio(
    "메뉴",
    [
        "1. 기법 비교",
        "2. 질문별 결과",
        "3. 인터랙티브 검색",
        "4. 비용 / 지연 추적",
        "5. 가이드 (메트릭/기법 설명)",
    ],
    index=0,
    label_visibility="collapsed",
)

st.sidebar.divider()
st.sidebar.markdown("처음 보시는 분 - 먼저 5번 가이드 페이지를 한 번 읽고 1번으로 돌아오시면 점수 해석이 쉽습니다.")
st.sidebar.divider()
st.sidebar.markdown("참고")
st.sidebar.markdown("1. 원논문/구현 출처 - docs/references.md")
st.sidebar.markdown("1. 저장된 평가 결과 - evaluation/results/")
st.sidebar.markdown("1. 미스트랄 무료 티어 사용 중이면 비용 표시는 모두 0 입니다")

if page.startswith("1"):
    render_compare()
elif page.startswith("2"):
    render_questions()
elif page.startswith("3"):
    render_demo()
elif page.startswith("4"):
    render_cost()
elif page.startswith("5"):
    render_guide()
