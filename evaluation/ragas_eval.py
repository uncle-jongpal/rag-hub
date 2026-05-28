"""기법별 RAGAS 평가 하네스.

사용:
    uv run python evaluation/ragas_eval.py --technique 01-naive
    uv run python evaluation/ragas_eval.py --technique 02-hybrid-search --top-k 5

평가 LLM 비용이 크므로 질문 수와 top_k를 작게 두는 것을 권장합니다.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import logging
from datetime import datetime
from pathlib import Path

from common.config import settings
from common.usage import get_tracker
from data.sample.loader import load_all

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "evaluation" / "results"

# 기법 ID → (폴더명, 클래스명). 폴더가 숫자로 시작해 일반 import가 안 되므로 파일 경로로 동적 로드.
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


def load_questions() -> list[dict]:
    path = ROOT / "evaluation" / "questions.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_rag(technique_id: str):
    folder, class_name = TECHNIQUE_REGISTRY[technique_id]
    rag_path = ROOT / "techniques" / folder / "rag.py"
    spec = importlib.util.spec_from_file_location(f"rag_{technique_id}", rag_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"모듈 로드 실패: {rag_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, class_name)()


def run_inference(rag, questions: list[dict], top_k: int) -> list[dict]:
    out: list[dict] = []
    for q in questions:
        result = rag.generate(q["question"], top_k=top_k)
        out.append(
            {
                "question": q["question"],
                "ground_truth": q["ground_truth"],
                "answer": result["answer"],
                "contexts": result["contexts"],
            }
        )
        logger.info("질문 처리: %s", q["id"])
    return out


def evaluate_with_ragas(records: list[dict]) -> dict:
    from datasets import Dataset
    from ragas import evaluate
    from ragas.llms import LangchainLLMWrapper
    from ragas.metrics import (
        answer_relevancy,
        context_precision,
        context_recall,
        faithfulness,
    )

    # 평가용 LLM 선택 - llm_provider 에 따라 분기. 미스트랄이면 ChatMistralAI 사용
    eval_llm = None
    if settings.llm_provider == "mistral":
        from langchain_mistralai import ChatMistralAI

        eval_llm = LangchainLLMWrapper(
            ChatMistralAI(
                model=settings.eval_llm_model,
                api_key=settings.mistral_api_key,
                temperature=0.0,
            )
        )
    elif settings.llm_provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        eval_llm = LangchainLLMWrapper(
            ChatAnthropic(
                model=settings.eval_llm_model,
                api_key=settings.anthropic_api_key,
                temperature=0.0,
            )
        )
    # openai 는 RAGAS 디폴트로 OPENAI_API_KEY 환경변수에서 자동 인식

    ds = Dataset.from_list(records)
    metrics = [faithfulness, answer_relevancy, context_precision, context_recall]
    if eval_llm is not None:
        result = evaluate(ds, metrics=metrics, llm=eval_llm)
    else:
        result = evaluate(ds, metrics=metrics)
    return {
        "summary": {m.name: float(result[m.name]) for m in metrics},
        "by_question": result.to_pandas().to_dict(orient="records"),
    }


def write_markdown(technique_id: str, scores: dict, out_path: Path) -> None:
    lines = [
        f"# RAGAS 평가 결과 - {technique_id}",
        "",
        f"실행 시각 : {datetime.now().isoformat(timespec='seconds')}",
        f"생성 LLM : {settings.gen_llm_model}",
        f"평가 LLM : {settings.eval_llm_model}",
        "",
        "## 평균 점수",
        "",
    ]
    for k, v in scores["summary"].items():
        lines.append(f"1. {k} : {v:.3f}")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--technique", required=True, choices=list(TECHNIQUE_REGISTRY))
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--limit", type=int, default=0, help="질문 수 제한 (0=전체)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    questions = load_questions()
    if args.limit > 0:
        questions = questions[: args.limit]

    tracker = get_tracker()
    tracker.reset()

    logger.info("기법 로드: %s", args.technique)
    rag = load_rag(args.technique)
    rag.build_index(load_all())
    indexing_usage = tracker.snapshot()

    tracker.reset()
    logger.info("추론 실행 (질문 %d개)", len(questions))
    records = run_inference(rag, questions, top_k=args.top_k)
    inference_usage = tracker.snapshot()

    logger.info("RAGAS 평가 실행")
    scores = evaluate_with_ragas(records)

    scores["usage"] = {
        "indexing": indexing_usage,
        "inference": inference_usage,
    }
    scores["meta"] = {
        "technique": args.technique,
        "top_k": args.top_k,
        "n_questions": len(questions),
        "gen_llm_model": settings.gen_llm_model,
        "eval_llm_model": settings.eval_llm_model,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    base = RESULTS_DIR / f"{args.technique}-{stamp}"
    (base.with_suffix(".json")).write_text(json.dumps(scores, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(args.technique, scores, base.with_suffix(".md"))

    print("\n=== 평균 점수 ===")
    for k, v in scores["summary"].items():
        print(f"  {k}: {v:.3f}")
    print("\n=== 토큰/비용 (인덱싱 + 추론) ===")
    total_cost = indexing_usage["totals"]["cost_usd"] + inference_usage["totals"]["cost_usd"]
    total_time = indexing_usage["totals"]["elapsed_seconds"] + inference_usage["totals"]["elapsed_seconds"]
    print(f"  비용 합계: ${total_cost:.4f}")
    print(f"  LLM 호출 시간 합계: {total_time:.1f}초")
    print(f"\n결과 저장: {base.with_suffix('.json').name}, {base.with_suffix('.md').name}")


if __name__ == "__main__":
    main()
