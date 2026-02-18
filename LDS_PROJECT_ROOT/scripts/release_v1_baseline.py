#!/usr/bin/env python3
"""Create LDS release baseline evidence and optional git tag report."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]


def resolve_path(raw: str) -> Path:
    path = Path(raw)
    if path.is_absolute():
        return path
    return ROOT / path


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def sha256_of_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def run(cmd: List[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, check=False)


def collect_gate_snapshot(reports_dir: Path, required_artifacts: List[str]) -> Tuple[Dict[str, str], List[str]]:
    snapshot: Dict[str, str] = {}
    errors: List[str] = []

    for artifact in required_artifacts:
        path = reports_dir / f"{artifact}.json"
        key = f"{artifact}.json"
        if not path.exists():
            snapshot[key] = "missing"
            errors.append(f"missing required artifact: {key}")
            continue

        try:
            payload = load_json(path)
            status = str(payload.get("status", "unknown"))
        except Exception as exc:
            snapshot[key] = "invalid"
            errors.append(f"invalid artifact JSON: {key} ({exc})")
            continue

        snapshot[key] = status
        if status == "fail":
            errors.append(f"required artifact status fail: {key}")

    return snapshot, errors


def build_freeze_report(reports_dir: Path) -> Tuple[Dict[str, Any], List[str]]:
    gate = load_json(ROOT / "contracts/rules/lds-publish-gate.json")
    policy = load_json(ROOT / "contracts/policy/lds-policy.json")
    contract_manifest_path = ROOT / "contracts/governance/lds-contract-manifest.json"
    protected_manifest_path = ROOT / "contracts/governance/lds-protected-manifest.json"
    tokenizer_contract = load_json(ROOT / "contracts/token/lds-tokenizer-mirror.json")

    required_artifacts = gate.get("required_artifacts", [])
    snapshot, errors = collect_gate_snapshot(reports_dir, required_artifacts)

    mirror_assets = tokenizer_contract.get("encodings", [])
    first_asset = mirror_assets[0].get("cache_file") if mirror_assets else None
    if not isinstance(first_asset, str):
        errors.append("tokenizer mirror contract missing encodings[0].cache_file")
        tokenizer_hash = ""
    else:
        tokenizer_path = ROOT / first_asset
        if not tokenizer_path.exists():
            errors.append(f"tokenizer mirror asset missing: {first_asset}")
            tokenizer_hash = ""
        else:
            tokenizer_hash = sha256_of_file(tokenizer_path)

    status = "pass" if not errors else "warn"
    summary = (
        "Production baseline frozen for vendor-neutral LDS core."
        if status == "pass"
        else "Baseline generated with warnings. Resolve issues before strict release."
    )

    report = {
        "artifact_id": "freeze_report",
        "generated_on": date.today().isoformat(),
        "status": status,
        "summary": summary,
        "baseline": {
            "standard_version": gate.get("version"),
            "policy_version": policy.get("version"),
            "publish_gate_version": gate.get("version"),
            "contract_manifest_sha256": sha256_of_file(contract_manifest_path),
            "protected_manifest_sha256": sha256_of_file(protected_manifest_path),
            "tokenizer_mirror_asset_sha256": tokenizer_hash,
        },
        "gate_snapshot": snapshot,
        "warnings": errors,
    }
    return report, errors


def build_tag_report(status: str, summary: str, details: Dict[str, Any]) -> Dict[str, Any]:
    payload = {
        "artifact_id": "release_tag_report",
        "generated_on": date.today().isoformat(),
        "status": status,
        "summary": summary,
    }
    payload.update(details)
    return payload


def handle_tag(tag: str, message: str, allow_dirty: bool, create_tag: bool) -> Tuple[Dict[str, Any], int]:
    if not create_tag:
        report = build_tag_report(
            "warn",
            "Tag creation skipped (--create-tag not set).",
            {"tag": tag, "created": False},
        )
        return report, 0

    inside = run(["git", "rev-parse", "--is-inside-work-tree"])
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        report = build_tag_report(
            "warn",
            "Git repository not detected; tag was not created.",
            {"tag": tag, "created": False},
        )
        return report, 0

    if not allow_dirty:
        dirty = run(["git", "status", "--porcelain"])
        if dirty.returncode != 0:
            report = build_tag_report(
                "fail",
                "Failed to inspect git status.",
                {"tag": tag, "created": False, "error": (dirty.stderr or dirty.stdout).strip()},
            )
            return report, 1
        if dirty.stdout.strip():
            report = build_tag_report(
                "fail",
                "Working tree is dirty; refusing to create release tag.",
                {"tag": tag, "created": False},
            )
            return report, 1

    exists = run(["git", "tag", "--list", tag])
    if exists.returncode == 0 and exists.stdout.strip() == tag:
        report = build_tag_report(
            "warn",
            "Tag already exists; no new tag created.",
            {"tag": tag, "created": False},
        )
        return report, 0

    create = run(["git", "tag", "-a", tag, "-m", message])
    if create.returncode != 0:
        report = build_tag_report(
            "fail",
            "Git tag creation failed.",
            {"tag": tag, "created": False, "error": (create.stderr or create.stdout).strip()},
        )
        return report, 1

    report = build_tag_report(
        "pass",
        "Release tag created.",
        {"tag": tag, "created": True},
    )
    return report, 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate LDS release v1 baseline and optional tag.")
    parser.add_argument(
        "--reports-dir",
        default="reports/release",
        help="Directory containing release artifacts.",
    )
    parser.add_argument(
        "--freeze-report",
        default="reports/release/freeze_report.json",
        help="Output path for freeze report.",
    )
    parser.add_argument(
        "--tag-report",
        default="reports/release/release_tag_report.json",
        help="Output path for tag report.",
    )
    parser.add_argument("--create-tag", action="store_true", help="Create annotated git tag.")
    parser.add_argument("--tag", default="lds-v1.0.0", help="Tag name.")
    parser.add_argument(
        "--tag-message",
        default="LDS v1 release baseline",
        help="Annotated tag message.",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Allow tag creation on dirty working tree.",
    )
    parser.add_argument("--strict", action="store_true", help="Return non-zero if warnings/errors exist.")
    args = parser.parse_args()

    reports_dir = resolve_path(args.reports_dir)
    freeze_report_path = resolve_path(args.freeze_report)
    tag_report_path = resolve_path(args.tag_report)

    freeze_report, freeze_errors = build_freeze_report(reports_dir)
    write_json(freeze_report_path, freeze_report)

    tag_report, tag_rc = handle_tag(
        tag=args.tag,
        message=args.tag_message,
        allow_dirty=args.allow_dirty,
        create_tag=args.create_tag,
    )
    write_json(tag_report_path, tag_report)

    print("Release baseline: PASS" if not freeze_errors else "Release baseline: WARN")
    print(f"- freeze report: {freeze_report_path}")
    print(f"- tag report: {tag_report_path}")

    if args.strict and (freeze_errors or tag_rc != 0):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
