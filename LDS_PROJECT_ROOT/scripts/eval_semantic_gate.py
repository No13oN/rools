#!/usr/bin/env python3
"""Evaluate semantic gate scorecard against LDS thresholds."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_semantic_gate(
    scorecard: Dict[str, Any],
    thresholds: Dict[str, Any],
    publish_gate: Dict[str, Any],
) -> List[str]:
    errors: List[str] = []

    required_scorecard = [
        "weighted_score",
        "class_scores",
        "critical_hallucination",
        "retrieval_precision",
        "retrieval_recall",
        "citation_faithfulness",
        "hallucination_rate",
        "p95_latency_ms",
    ]
    for key in required_scorecard:
        if key not in scorecard:
            errors.append(f"semantic scorecard missing required field: {key}")

    if errors:
        return errors

    sem_gate = publish_gate["semantic_gate"]
    weighted_min = sem_gate["weighted_score_min"]
    if scorecard["weighted_score"] < weighted_min:
        errors.append(
            f"weighted_score below threshold: {scorecard['weighted_score']} < {weighted_min}"
        )

    class_scores = scorecard["class_scores"]
    for cls, cls_min in sem_gate["class_thresholds"].items():
        value = class_scores.get(cls)
        if value is None:
            errors.append(f"class score missing: {cls}")
            continue
        if value < cls_min:
            errors.append(f"class score below threshold for {cls}: {value} < {cls_min}")

    critical = scorecard["critical_hallucination"]
    for cls in sem_gate.get("block_on_critical_hallucination", []):
        value = critical.get(cls, 0)
        if isinstance(value, bool):
            triggered = value
        elif isinstance(value, (int, float)):
            triggered = value > 0
        else:
            errors.append(f"critical_hallucination invalid value type for {cls}")
            continue
        if triggered:
            errors.append(f"critical hallucination present in blocked class: {cls}")

    t = thresholds["thresholds"]
    if scorecard["retrieval_precision"] < t["retrieval_precision_min"]:
        errors.append(
            f"retrieval_precision below threshold: {scorecard['retrieval_precision']} < {t['retrieval_precision_min']}"
        )
    if scorecard["retrieval_recall"] < t["retrieval_recall_min"]:
        errors.append(
            f"retrieval_recall below threshold: {scorecard['retrieval_recall']} < {t['retrieval_recall_min']}"
        )
    if scorecard["citation_faithfulness"] < t["citation_faithfulness_min"]:
        errors.append(
            f"citation_faithfulness below threshold: {scorecard['citation_faithfulness']} < {t['citation_faithfulness_min']}"
        )
    if scorecard["hallucination_rate"] > t["hallucination_rate_max"]:
        errors.append(
            f"hallucination_rate above threshold: {scorecard['hallucination_rate']} > {t['hallucination_rate_max']}"
        )
    if scorecard["p95_latency_ms"] > t["p95_latency_ms_max"]:
        errors.append(
            f"p95_latency_ms above threshold: {scorecard['p95_latency_ms']} > {t['p95_latency_ms_max']}"
        )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate LDS semantic gate scorecard.")
    parser.add_argument(
        "--scorecard",
        default="reports/release/semantic_scorecard.json",
        help="Path to semantic scorecard JSON (relative to LDS root).",
    )
    parser.add_argument(
        "--thresholds",
        default="contracts/evaluation/lds-eval-thresholds.json",
        help="Path to evaluation thresholds contract JSON.",
    )
    parser.add_argument(
        "--publish-gate",
        default="contracts/rules/lds-publish-gate.json",
        help="Path to publish gate JSON.",
    )
    parser.add_argument("--strict", action="store_true", help="Return non-zero exit on failures.")
    args = parser.parse_args()

    scorecard_path = ROOT / args.scorecard
    thresholds_path = ROOT / args.thresholds
    gate_path = ROOT / args.publish_gate

    if not scorecard_path.exists():
        print("Semantic gate: FAIL")
        print(f"- missing scorecard: {scorecard_path}")
        return 1 if args.strict else 0

    scorecard = load_json(scorecard_path)
    thresholds = load_json(thresholds_path)
    gate = load_json(gate_path)

    errors = validate_semantic_gate(scorecard, thresholds, gate)
    if errors:
        print("Semantic gate: FAIL")
        for err in errors:
            print(f"- {err}")
        return 1 if args.strict else 0

    print("Semantic gate: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
