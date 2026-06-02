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
        # ragas 0.3.x 가 기대하는 컬럼명 (user_input/response/retrieved_contexts/reference).
        # 옛 이름(question/answer/contexts/ground_truth)을 같이 넣어두면 일부 메트릭이 자동 매핑 못해 NaN.
        out.append(
            {
                "user_input": q["question"],
                "reference": q["ground_truth"],
                "response": result["answer"],
                "retrieved_contexts": result["contexts"],
            }
        )
        logger.info("질문 처리: %s", q["id"])
    return out


def _compute_answer_relevancy(records: list[dict]) -> list[float]:
    """답변 적합성 자체 계산 - BGE-M3 로 질문/답변 임베딩 코사인 유사도.

    RAGAS 의 answer_relevancy 메트릭은 미스트랄 무료 티어 분당 한도에 부딪혀 NaN 처리됨.
    LLM 호출 없이 임베딩만으로 계산하면 무료 티어에 영향 없이 0~1 점수 산출 가능.
    원 RAGAS 메트릭과 정확히 같진 않지만 "질문과 답변이 의미적으로 가까운지"를 측정한다는 의도는 동일.
    """
    if not records:
        return []
    from common.embeddings import EmbeddingModel

    embedder = EmbeddingModel()
    questions = [r.get("user_input", "") for r in records]
    answers = [r.get("response", "") for r in records]
    q_vecs = embedder.encode(questions)
    a_vecs = embedder.encode(answers)
    scores = (q_vecs * a_vecs).sum(axis=1).tolist()
    return [max(0.0, min(1.0, float(s))) for s in scores]


def evaluate_with_ragas(records: list[dict]) -> dict:
    from datasets import Dataset
    from ragas import evaluate
    from ragas.llms import LangchainLLMWrapper
    from ragas.metrics import (
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

    # 평가용 임베딩 - 미스트랄/앤트로픽 사용 시 ragas 가 기본으로 OpenAIEmbeddings 시도해서 실패.
    # ragas 자체 HuggingFaceEmbeddings (0.3.x 의 권장 방식) 사용.
    eval_embeddings = None
    if settings.llm_provider in ("mistral", "anthropic"):
        from ragas.embeddings import HuggingFaceEmbeddings as RagasHFEmbeddings

        eval_embeddings = RagasHFEmbeddings(model=settings.embedding_model)

    # 미스트랄 무료 티어 분당 한도(1 req/sec 수준) 대응 - 동시 1개 호출 + 재시도 충분히
    from ragas.run_config import RunConfig

    run_config = RunConfig(max_workers=1, max_retries=10, timeout=180)

    ds = Dataset.from_list(records)
    # RAGAS 평가에서는 답변 적합성을 제외하고 3개만 사용. 답변 적합성은 별도로 자체 계산.
    metrics = [faithfulness, context_precision, context_recall]

    for m in metrics:
        if eval_llm is not None and hasattr(m, "llm") and getattr(m, "llm", None) is None:
            m.llm = eval_llm
        if eval_embeddings is not None and hasattr(m, "embeddings") and getattr(m, "embeddings", None) is None:
            m.embeddings = eval_embeddings

    kwargs = {"run_config": run_config}
    if eval_llm is not None:
        kwargs["llm"] = eval_llm
    if eval_embeddings is not None:
        kwargs["embeddings"] = eval_embeddings
    result = evaluate(ds, metrics=metrics, **kwargs)

    import math

    def _mean(v):
        if isinstance(v, (int, float)):
            return float(v)
        if hasattr(v, "__iter__"):
            vals = [x for x in v if isinstance(x, (int, float)) and not math.isnan(x)]
            return float(sum(vals) / len(vals)) if vals else 0.0
        return 0.0

    # 답변 적합성을 BGE-M3 자체 계산으로 추가 (RAGAS 메트릭 우회)
    logger.info("답변 적합성 자체 계산 시작 (BGE-M3 질문/답변 임베딩 유사도)")
    ar_scores = _compute_answer_relevancy(records)

    by_question = result.to_pandas().to_dict(orient="records")
    for row, score in zip(by_question, ar_scores, strict=False):
        row["answer_relevancy"] = score

    summary = {m.name: _mean(result[m.name]) for m in metrics}
    summary["answer_relevancy"] = float(sum(ar_scores) / len(ar_scores)) if ar_scores else 0.0

    return {
        "summary": summary,
        "by_question": by_question,
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
