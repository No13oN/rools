#!/usr/bin/env python3
"""Build OPA input document from LDS contracts and release artifacts."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any, Dict

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None


ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_yaml(path: Path) -> Dict[str, Any]:
    if yaml is None:
        raise RuntimeError("pyyaml is not available")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)  # type: ignore
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError("YAML root must be mapping")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Build OPA policy input for LDS gates.")
    parser.add_argument(
        "--output",
        default="reports/release/policy_input.json",
        help="Output file path relative to LDS root.",
    )
    parser.add_argument(
        "--publish-gate",
        default="contracts/rules/lds-publish-gate.json",
        help="Publish gate contract path relative to LDS root.",
    )
    parser.add_argument(
        "--policy",
        default="contracts/policy/lds-policy.json",
        help="Policy contract path relative to LDS root.",
    )
    parser.add_argument(
        "--thresholds",
        default="contracts/evaluation/lds-eval-thresholds.json",
        help="Threshold contract path relative to LDS root.",
    )
    parser.add_argument(
        "--waivers",
        default="contracts/governance/lds-waivers.yaml",
        help="Waiver registry path relative to LDS root.",
    )
    parser.add_argument(
        "--artifacts-dir",
        default="reports/release",
        help="Artifacts directory relative to LDS root.",
    )
    args = parser.parse_args()

    gate = load_json(ROOT / args.publish_gate)
    policy = load_json(ROOT / args.policy)
    thresholds = load_json(ROOT / args.thresholds)
    waivers_doc = load_yaml(ROOT / args.waivers)

    artifacts: Dict[str, Any] = {}
    missing = []
    deferred_artifacts = {"policy_report", "handoff_report"}
    artifacts_dir = ROOT / args.artifacts_dir

    for artifact_name in gate.get("required_artifacts", []):
        if artifact_name in deferred_artifacts:
            continue
        path = artifacts_dir / f"{artifact_name}.json"
        if not path.exists():
            missing.append(artifact_name)
            continue
        artifacts[artifact_name] = load_json(path)

    active_waivers = []
    today = date.today()
    for item in waivers_doc.get("waivers", []):
        if item.get("status") != "active":
            continue
        expires = item.get("expires_on")
        expired = False
        if isinstance(expires, str):
            try:
                expired = date.fromisoformat(expires) < today
            except Exception:
                expired = True
        else:
            expired = True

        active_waivers.append(
            {
                "waiver_id": item.get("waiver_id", "<unknown>"),
                "waiver_type": item.get("waiver_type", "<unknown>"),
                "scope_path": item.get("scope_path", "<unknown>"),
                "expires_on": expires,
                "expired": expired,
            }
        )

    policy_input = {
        "generated_on": today.isoformat(),
        "policy": {
            "version": policy.get("version"),
            "publish_gate": policy.get("publish_gate", {}),
            "required_artifacts": gate.get("required_artifacts", []),
            "deferred_artifacts": sorted(deferred_artifacts),
        },
        "thresholds": thresholds.get("thresholds", {}),
        "artifacts": artifacts,
        "missing_artifacts": missing,
        "waivers": {
            "active": active_waivers,
            "expired_active_count": sum(1 for w in active_waivers if w.get("expired")),
        },
    }

    output_path = ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(policy_input, indent=2) + "\n", encoding="utf-8")

    print(f"Policy input: WROTE {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
