"""여러 기법의 평가 결과를 하나의 비교 리포트로 합침.

사용:
    uv run python evaluation/compare.py
    uv run python evaluation/compare.py --out evaluation/results/compare.md
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "evaluation" / "results"


def collect_latest() -> dict[str, dict]:
    """기법별 가장 최근 결과 JSON을 한 개씩 수집."""
    latest: dict[str, Path] = {}
    for p in sorted(RESULTS_DIR.glob("*.json")):
        stem = p.stem
        # 파일명 형식: <technique>-YYYYMMDD-HHMMSS
        parts = stem.rsplit("-", 2)
        if len(parts) < 3:
            continue
        technique = parts[0]
        if technique not in latest or p.stat().st_mtime > latest[technique].stat().st_mtime:
            latest[technique] = p
    return {t: json.loads(p.read_text(encoding="utf-8")) for t, p in latest.items()}


def render_markdown(results: dict[str, dict]) -> str:
    metric_names = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]

    lines = ["# 기법 비교 (RAGAS)", "", "줄바꿈 + 콜론 형식으로 메트릭별 점수를 나열합니다.", ""]
    for tech, scores in sorted(results.items()):
        lines.append(f"## {tech}")
        lines.append("")
        summary = scores.get("summary", {})
        for m in metric_names:
            v = summary.get(m)
            lines.append(f"1. {m} : {v:.3f}" if isinstance(v, (int, float)) else f"1. {m} : N/A")
        lines.append("")

    # 메트릭별 순위
    lines.append("## 메트릭별 순위")
    lines.append("")
    for m in metric_names:
        ranked = sorted(
            ((t, s.get("summary", {}).get(m, 0.0)) for t, s in results.items()),
            key=lambda x: x[1],
            reverse=True,
        )
        lines.append(f"### {m}")
        for i, (t, v) in enumerate(ranked, 1):
            lines.append(f"1. {i}위 - {t} : {v:.3f}")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(RESULTS_DIR / "compare.md"))
    args = parser.parse_args()

    results = collect_latest()
    if not results:
        print("평가 결과가 없습니다. ragas_eval.py 를 먼저 실행하세요.")
        return

    md = render_markdown(results)
    Path(args.out).write_text(md, encoding="utf-8")
    print(f"비교 리포트 저장: {args.out} ({len(results)}개 기법)")


if __name__ == "__main__":
    main()
