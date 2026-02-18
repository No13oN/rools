#!/usr/bin/env python3
"""Evaluate LDS policy gate with OPA/Rego."""

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


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_policy_report(path: Path, status: str, summary: str, denies: List[str]) -> None:
    report = {
        "artifact_id": "policy_report",
        "generated_on": date.today().isoformat(),
        "status": status,
        "summary": summary,
        "deny_count": len(denies),
        "denies": denies,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def parse_opa_deny(stdout: str) -> List[str]:
    data = json.loads(stdout)
    denies: List[str] = []
    for result in data.get("result", []):
        for expr in result.get("expressions", []):
            value = expr.get("value", [])
            if isinstance(value, list):
                for item in value:
                    denies.append(str(item))
    return denies


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate LDS policy gate using OPA/Rego.")
    parser.add_argument(
        "--input",
        default="reports/release/policy_input.json",
        help="OPA input JSON path relative to LDS root.",
    )
    parser.add_argument(
        "--rego",
        default="policies/opa/lds_gate.rego",
        help="Rego policy file path relative to LDS root.",
    )
    parser.add_argument(
        "--query",
        default="data.lds.gate.deny",
        help="OPA query expression.",
    )
    parser.add_argument(
        "--report",
        default="reports/release/policy_report.json",
        help="Policy report output path relative to LDS root.",
    )
    parser.add_argument("--strict", action="store_true", help="Return non-zero on failures.")
    args = parser.parse_args()

    input_path = ROOT / args.input
    rego_path = ROOT / args.rego
    report_path = ROOT / args.report

    if not input_path.exists():
        msg = f"policy input missing: {input_path}"
        status = "fail" if args.strict else "warn"
        write_policy_report(report_path, status, msg, [msg])
        print("Policy gate: FAIL")
        print(f"- {msg}")
        return 1 if args.strict else 0

    if not rego_path.exists():
        msg = f"rego policy missing: {rego_path}"
        status = "fail" if args.strict else "warn"
        write_policy_report(report_path, status, msg, [msg])
        print("Policy gate: FAIL")
        print(f"- {msg}")
        return 1 if args.strict else 0

    opa_bin = shutil.which("opa")
    if opa_bin is None:
        msg = "opa binary is not available"
        status = "fail" if args.strict else "warn"
        write_policy_report(report_path, status, msg, [msg])
        print("Policy gate: FAIL")
        print(f"- {msg}")
        return 1 if args.strict else 0

    cmd = [
        opa_bin,
        "eval",
        "--format=json",
        "--data",
        str(rego_path),
        "--input",
        str(input_path),
        args.query,
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        msg = f"opa eval failed: {proc.stderr.strip() or proc.stdout.strip()}"
        status = "fail" if args.strict else "warn"
        write_policy_report(report_path, status, msg, [msg])
        print("Policy gate: FAIL")
        print(f"- {msg}")
        return 1 if args.strict else 0

    try:
        denies = parse_opa_deny(proc.stdout)
    except Exception as exc:
        msg = f"failed to parse opa output ({exc})"
        status = "fail" if args.strict else "warn"
        write_policy_report(report_path, status, msg, [msg])
        print("Policy gate: FAIL")
        print(f"- {msg}")
        return 1 if args.strict else 0

    if denies:
        write_policy_report(report_path, "fail", "Policy denies detected.", denies)
        print("Policy gate: FAIL")
        for deny in denies:
            print(f"- {deny}")
        return 1 if args.strict else 0

    write_policy_report(report_path, "pass", "OPA policy gate passed.", [])
    print("Policy gate: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
