#!/usr/bin/env python3
"""Evaluate multi-agent handoff consistency against LDS acceptance contract."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def extract_step_ids(plan: Dict[str, Any]) -> List[str]:
    steps = plan.get("steps", [])
    step_ids: List[str] = []
    for item in steps:
        sid = item.get("step_id")
        if isinstance(sid, str) and sid:
            step_ids.append(sid)
    return step_ids


def pair_divergence(ids_a: List[str], ids_b: List[str]) -> Tuple[float, int, float, float]:
    set_a = set(ids_a)
    set_b = set(ids_b)
    union = set_a | set_b
    inter = set_a & set_b

    if not union:
        return 100.0, 0, 100.0, 100.0

    set_div = (1.0 - (len(inter) / len(union))) * 100.0

    common = [sid for sid in ids_a if sid in set_b]
    if not common:
        order_div = 100.0
    else:
        idx_a = {sid: i for i, sid in enumerate(ids_a)}
        idx_b = {sid: i for i, sid in enumerate(ids_b)}
        mismatches = 0
        for sid in common:
            if idx_a[sid] != idx_b[sid]:
                mismatches += 1
        order_div = (mismatches / len(common)) * 100.0

    combined = max(set_div, order_div)
    return combined, len(inter), set_div, order_div


def write_report(path: Path, status: str, summary: str, details: Dict[str, Any]) -> None:
    report = {
        "artifact_id": "handoff_report",
        "generated_on": date.today().isoformat(),
        "status": status,
        "summary": summary,
    }
    report.update(details)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate LDS multi-agent handoff consistency.")
    parser.add_argument(
        "--config",
        default="contracts/evaluation/lds-handoff-acceptance.json",
        help="Handoff acceptance config path relative to LDS root.",
    )
    parser.add_argument(
        "--plans-dir",
        default="reports/handoff",
        help="Directory with agent handoff plans relative to LDS root.",
    )
    parser.add_argument(
        "--report",
        default="reports/release/handoff_report.json",
        help="Output report path relative to LDS root.",
    )
    parser.add_argument("--strict", action="store_true", help="Return non-zero on failures.")
    args = parser.parse_args()

    cfg = load_json(ROOT / args.config)
    plans_dir = ROOT / args.plans_dir

    required_agents = cfg.get("required_agents", [])
    max_divergence = float(cfg.get("max_divergence_percent", 10))
    min_shared_steps = int(cfg.get("min_shared_steps", 1))

    errors: List[str] = []
    plans: Dict[str, Dict[str, Any]] = {}

    for agent in required_agents:
        plan_path = plans_dir / f"{agent}.json"
        if not plan_path.exists():
            errors.append(f"missing handoff plan: {plan_path}")
            continue
        plans[agent] = load_json(plan_path)

    comparisons: List[Dict[str, Any]] = []
    agents = list(plans.keys())
    worst = 0.0

    for i in range(len(agents)):
        for j in range(i + 1, len(agents)):
            a = agents[i]
            b = agents[j]
            ids_a = extract_step_ids(plans[a])
            ids_b = extract_step_ids(plans[b])

            divergence, shared, set_div, order_div = pair_divergence(ids_a, ids_b)
            worst = max(worst, divergence)

            comparisons.append(
                {
                    "pair": [a, b],
                    "divergence_percent": round(divergence, 3),
                    "set_divergence_percent": round(set_div, 3),
                    "order_divergence_percent": round(order_div, 3),
                    "shared_steps": shared,
                }
            )

            if shared < min_shared_steps:
                errors.append(
                    f"pair {a}/{b}: shared_steps below minimum ({shared} < {min_shared_steps})"
                )
            if divergence > max_divergence:
                errors.append(
                    f"pair {a}/{b}: divergence above threshold ({divergence:.3f} > {max_divergence:.3f})"
                )

    report_path = ROOT / args.report
    details = {
        "required_agents": required_agents,
        "max_divergence_percent": max_divergence,
        "worst_divergence_percent": round(worst, 3),
        "comparisons": comparisons,
    }

    if errors:
        write_report(report_path, "fail", "Handoff acceptance failed.", {**details, "errors": errors})
        print("Handoff acceptance: FAIL")
        for err in errors:
            print(f"- {err}")
        return 1 if args.strict else 0

    write_report(report_path, "pass", "Handoff acceptance passed.", details)
    print("Handoff acceptance: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
