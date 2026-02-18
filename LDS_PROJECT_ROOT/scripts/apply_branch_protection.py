#!/usr/bin/env python3
"""Apply GitHub branch protection from repository policy file."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def run(cmd: List[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, check=False)


def infer_repo() -> str | None:
    proc = run(["git", "remote", "get-url", "origin"])
    if proc.returncode == 0:
        url = proc.stdout.strip()
        if url.endswith(".git"):
            url = url[:-4]
        if "github.com:" in url:
            return url.split("github.com:", 1)[1]
        if "github.com/" in url:
            return url.split("github.com/", 1)[1]

    proc = run(["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"])
    if proc.returncode == 0:
        return proc.stdout.strip() or None
    return None


def validate_policy(policy: Dict[str, Any]) -> List[str]:
    errors: List[str] = []

    required_status = policy.get("required_status_checks")
    if not isinstance(required_status, dict):
        errors.append("policy missing object: required_status_checks")
    else:
        contexts = required_status.get("contexts")
        if not isinstance(contexts, list) or not contexts:
            errors.append("policy required_status_checks.contexts must be non-empty list")
        if not bool(required_status.get("strict", False)):
            errors.append("policy required_status_checks.strict must be true")

    if not bool(policy.get("enforce_admins", False)):
        errors.append("policy enforce_admins must be true")

    pr_reviews = policy.get("required_pull_request_reviews")
    if not isinstance(pr_reviews, dict):
        errors.append("policy missing object: required_pull_request_reviews")
    else:
        count = int(pr_reviews.get("required_approving_review_count") or 0)
        if count < 1:
            errors.append("policy required_approving_review_count must be >= 1")

    for key in ("allow_force_pushes", "allow_deletions"):
        if bool(policy.get(key, False)):
            errors.append(f"policy {key} must be false")

    if not bool(policy.get("required_linear_history", False)):
        errors.append("policy required_linear_history must be true")

    if not bool(policy.get("required_conversation_resolution", False)):
        errors.append("policy required_conversation_resolution must be true")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply branch protection on GitHub.")
    parser.add_argument("--repo", help="Repository in owner/name format. If omitted, inferred.")
    parser.add_argument("--branch", default="main", help="Branch name (default: main).")
    parser.add_argument(
        "--policy",
        default=".github/branch-protection.json",
        help="Branch protection policy JSON (relative to LDS root).",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print command without applying.")
    args = parser.parse_args()

    if shutil.which("gh") is None:
        print("Branch protection: FAIL")
        print("- gh CLI is not installed")
        return 1

    repo = args.repo or infer_repo()
    if not repo:
        print("Branch protection: FAIL")
        print("- unable to infer GitHub repo; pass --repo owner/name")
        return 1

    policy_path = ROOT / args.policy
    if not policy_path.exists():
        print("Branch protection: FAIL")
        print(f"- policy file missing: {policy_path}")
        return 1

    policy = load_json(policy_path)
    policy_errors = validate_policy(policy)
    if policy_errors:
        print("Branch protection: FAIL")
        for err in policy_errors:
            print(f"- {err}")
        return 1

    body = json.dumps(policy)

    cmd = [
        "gh",
        "api",
        "--method",
        "PUT",
        f"repos/{repo}/branches/{args.branch}/protection",
        "-H",
        "Accept: application/vnd.github+json",
        "--input",
        "-",
    ]

    if args.dry_run:
        print("Branch protection: DRY-RUN")
        print(f"- repo: {repo}")
        print(f"- branch: {args.branch}")
        print(f"- policy: {policy_path}")
        print("- command:")
        print("  " + " ".join(cmd))
        return 0

    proc = subprocess.run(cmd, input=body, text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        print("Branch protection: FAIL")
        print(f"- repo: {repo}")
        print(f"- branch: {args.branch}")
        err = (proc.stderr or proc.stdout).strip()
        print(f"- {err}")
        return 1

    print("Branch protection: PASS")
    print(f"- repo: {repo}")
    print(f"- branch: {args.branch}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
