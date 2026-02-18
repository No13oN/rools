#!/usr/bin/env python3
"""Validate release artifact presence and minimal schema."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_artifact_file(path: Path, artifact_name: str) -> List[str]:
    errors: List[str] = []
    if not path.exists():
        return [f"missing artifact file: {path}"]

    try:
        data = load_json(path)
    except Exception as exc:
        return [f"invalid JSON in artifact {path}: {exc}"]

    required = ["artifact_id", "generated_on", "status", "summary"]
    for field in required:
        if field not in data:
            errors.append(f"artifact {artifact_name} missing field: {field}")

    if errors:
        return errors

    if data["artifact_id"] != artifact_name:
        errors.append(f"artifact_id mismatch for {artifact_name}: {data['artifact_id']}")

    try:
        generated = date.fromisoformat(data["generated_on"])
        if generated > date.today():
            errors.append(f"artifact {artifact_name} has future generated_on date")
    except Exception:
        errors.append(f"artifact {artifact_name} has invalid generated_on date")

    if data["status"] not in {"pass", "warn", "fail"}:
        errors.append(f"artifact {artifact_name} has invalid status: {data['status']}")

    if data["status"] == "fail":
        errors.append(f"artifact {artifact_name} status is fail")

    if not str(data["summary"]).strip():
        errors.append(f"artifact {artifact_name} summary is empty")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate LDS release artifacts.")
    parser.add_argument(
        "--artifacts-dir",
        default="reports/release",
        help="Directory with release artifacts (relative to LDS root).",
    )
    parser.add_argument(
        "--publish-gate",
        default="contracts/rules/lds-publish-gate.json",
        help="Publish gate contract path.",
    )
    parser.add_argument("--strict", action="store_true", help="Return non-zero exit on failures.")
    args = parser.parse_args()

    gate = load_json(ROOT / args.publish_gate)
    required_artifacts = gate.get("required_artifacts", [])
    artifacts_dir = ROOT / args.artifacts_dir

    errors: List[str] = []
    for artifact in required_artifacts:
        artifact_path = artifacts_dir / f"{artifact}.json"
        errors.extend(validate_artifact_file(artifact_path, artifact))

    if errors:
        print("Release artifacts: FAIL")
        for err in errors:
            print(f"- {err}")
        return 1 if args.strict else 0

    print("Release artifacts: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
