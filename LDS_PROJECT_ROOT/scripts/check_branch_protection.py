#!/usr/bin/env python3
"""Check GitHub branch protection and emit release report."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]


def write_report(path: Path, status: str, summary: str, details: Dict[str, Any]) -> None:
    report = {
        "artifact_id": "branch_protection_report",
        "generated_on": date.today().isoformat(),
        "status": status,
        "summary": summary,
    }
    report.update(details)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


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


def read_enabled(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, dict):
        return bool(value.get("enabled", False))
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Check branch protection and write report.")
    parser.add_argument("--repo", help="Repository in owner/name format. If omitted, inferred.")
    parser.add_argument("--branch", default="main", help="Branch name (default: main).")
    parser.add_argument(
        "--report",
        default="reports/release/branch_protection_report.json",
        help="Output report path relative to LDS root.",
    )
    parser.add_argument(
        "--required-context",
        action="append",
        default=["validate"],
        help="Required status check context. Can be passed multiple times.",
    )
    parser.add_argument("--strict", action="store_true", help="Fail on warn conditions.")
    args = parser.parse_args()

    report_path = ROOT / args.report

    if shutil.which("gh") is None:
        msg = "gh CLI is not installed"
        write_report(report_path, "warn", msg, {"repo": None, "branch": args.branch})
        print("Branch protection check: FAIL")
        print(f"- {msg}")
        return 1 if args.strict else 0

    repo = args.repo or infer_repo()
    if not repo:
        msg = "unable to infer GitHub repo"
        write_report(report_path, "warn", msg, {"repo": None, "branch": args.branch})
        print("Branch protection check: FAIL")
        print(f"- {msg}")
        return 1 if args.strict else 0

    proc = run(
        [
            "gh",
            "api",
            "-H",
            "Accept: application/vnd.github+json",
            f"repos/{repo}/branches/{args.branch}/protection",
        ]
    )

    if proc.returncode != 0:
        msg = (proc.stderr or proc.stdout).strip()
        write_report(
            report_path,
            "warn",
            "branch protection is not configured or inaccessible",
            {"repo": repo, "branch": args.branch, "error": msg},
        )
        print("Branch protection check: FAIL")
        print(f"- {msg}")
        return 1 if args.strict else 0

    data = json.loads(proc.stdout)
    required_status = data.get("required_status_checks", {}) or {}
    strict_checks = bool(required_status.get("strict", False))
    contexts = required_status.get("contexts", []) or []
    enforce_admins = read_enabled(data.get("enforce_admins", {}))
    pr_reviews = data.get("required_pull_request_reviews", {}) or {}
    approving_count = int(pr_reviews.get("required_approving_review_count") or 0)
    dismiss_stale_reviews = bool(pr_reviews.get("dismiss_stale_reviews", False))
    linear_history = read_enabled(data.get("required_linear_history", {}))
    allow_force_pushes = read_enabled(data.get("allow_force_pushes", {}))
    allow_deletions = read_enabled(data.get("allow_deletions", {}))
    conversation_resolution = read_enabled(data.get("required_conversation_resolution", {}))

    status = "pass"
    summary = "Branch protection is active and validated."
    errors: List[str] = []

    required_contexts = list(dict.fromkeys(args.required_context))
    for context in required_contexts:
        if context not in contexts:
            errors.append(f"missing required status check context: {context}")
    if not strict_checks:
        errors.append("required status checks strict mode is disabled")
    if not enforce_admins:
        errors.append("enforce_admins is disabled")
    if approving_count < 1:
        errors.append("required_approving_review_count must be >= 1")
    if not dismiss_stale_reviews:
        errors.append("dismiss_stale_reviews is disabled")
    if not linear_history:
        errors.append("required_linear_history is disabled")
    if allow_force_pushes:
        errors.append("allow_force_pushes must be disabled")
    if allow_deletions:
        errors.append("allow_deletions must be disabled")
    if not conversation_resolution:
        errors.append("required_conversation_resolution is disabled")

    if errors:
        status = "fail" if args.strict else "warn"
        summary = "Branch protection is present but does not satisfy LDS policy."

    details = {
        "repo": repo,
        "branch": args.branch,
        "required_status_checks_strict": strict_checks,
        "contexts": contexts,
        "enforce_admins": enforce_admins,
        "required_approving_review_count": approving_count,
        "dismiss_stale_reviews": dismiss_stale_reviews,
        "required_linear_history": linear_history,
        "allow_force_pushes": allow_force_pushes,
        "allow_deletions": allow_deletions,
        "required_conversation_resolution": conversation_resolution,
        "required_contexts": required_contexts,
        "errors": errors,
    }
    write_report(report_path, status, summary, details)

    if errors:
        print("Branch protection check: FAIL")
        for err in errors:
            print(f"- {err}")
        return 1 if args.strict else 0

    print("Branch protection check: PASS")
    print(f"- repo: {repo}")
    print(f"- branch: {args.branch}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
