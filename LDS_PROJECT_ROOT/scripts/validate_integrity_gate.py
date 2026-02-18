#!/usr/bin/env python3
"""Validate LDS integrity gate only (contract and protected manifests)."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_lds.py"


def load_validator_module():
    spec = importlib.util.spec_from_file_location("validate_lds", VALIDATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description="Run LDS integrity gate checks.")
    parser.add_argument("--strict", action="store_true", help="Return non-zero on failures.")
    args = parser.parse_args()

    mod = load_validator_module()
    errors: List[str] = []
    errors.extend(mod.validate_contract_manifest())
    errors.extend(mod.validate_protected_manifest())

    if errors:
        print("Integrity gate: FAIL")
        for err in errors:
            print(f"- {err}")
        return 1 if args.strict else 0

    print("Integrity gate: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
