#!/usr/bin/env python3
"""Validate deterministic offline tokenizer mirror and strict no-network loading."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

try:
    from jsonschema import FormatChecker, validate as jsonschema_validate  # type: ignore
except Exception:  # pragma: no cover
    FormatChecker = None
    jsonschema_validate = None

try:
    import tiktoken  # type: ignore
except Exception:  # pragma: no cover
    tiktoken = None


ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def sha256_of_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def validate_contract(contract: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if jsonschema_validate is None or FormatChecker is None:
        return ["jsonschema dependency missing"]
    try:
        jsonschema_validate(instance=contract, schema=schema, format_checker=FormatChecker())
    except Exception as exc:
        errors.append(f"tokenizer mirror contract schema validation failed ({exc})")
    return errors


def validate_mirror_files(contract: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    for enc in contract.get("encodings", []):
        rel = enc.get("cache_file")
        expected_hash = enc.get("expected_sha256")
        name = enc.get("name", "<unknown>")
        if not isinstance(rel, str):
            errors.append(f"encoding {name}: missing cache_file")
            continue
        path = ROOT / rel
        if not path.exists():
            errors.append(f"encoding {name}: cache file missing ({rel})")
            continue
        if not isinstance(expected_hash, str):
            errors.append(f"encoding {name}: missing expected_sha256")
            continue
        actual = sha256_of_file(path)
        if actual != expected_hash:
            errors.append(
                f"encoding {name}: cache hash mismatch ({actual} != {expected_hash})"
            )
    return errors


def validate_offline_loading(contract: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if tiktoken is None:
        return ["tiktoken dependency missing"]

    cache_dir = contract.get("cache_dir")
    env_var = contract.get("cache_env_var", "TIKTOKEN_CACHE_DIR")
    if not isinstance(cache_dir, str):
        return ["tokenizer mirror contract missing cache_dir"]

    os.environ[env_var] = str((ROOT / cache_dir).resolve())

    try:
        import tiktoken.load as tkload  # type: ignore
    except Exception as exc:
        return [f"failed to import tiktoken.load ({exc})"]

    original_read_file = tkload.read_file

    def _blocked_read_file(blobpath: str) -> bytes:
        raise RuntimeError(f"network access disabled during strict tokenizer check ({blobpath})")

    tkload.read_file = _blocked_read_file
    try:
        for enc in contract.get("encodings", []):
            name = enc.get("name")
            if not isinstance(name, str):
                errors.append("encoding entry missing name")
                continue
            try:
                tiktoken.get_encoding(name)
            except Exception as exc:
                errors.append(f"offline tokenizer load failed for {name} ({exc})")
    finally:
        tkload.read_file = original_read_file

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate LDS offline tokenizer mirror.")
    parser.add_argument(
        "--contract",
        default="contracts/token/lds-tokenizer-mirror.json",
        help="Tokenizer mirror contract path (relative to LDS root).",
    )
    parser.add_argument(
        "--schema",
        default="contracts/token/lds-tokenizer-mirror.schema.json",
        help="Tokenizer mirror schema path (relative to LDS root).",
    )
    parser.add_argument("--strict", action="store_true", help="Return non-zero on failures.")
    args = parser.parse_args()

    contract_path = ROOT / args.contract
    schema_path = ROOT / args.schema

    errors: List[str] = []
    if not contract_path.exists():
        errors.append(f"missing contract: {contract_path}")
    if not schema_path.exists():
        errors.append(f"missing schema: {schema_path}")

    contract: Dict[str, Any] = {}
    schema: Dict[str, Any] = {}
    if not errors:
        contract = load_json(contract_path)
        schema = load_json(schema_path)
        errors.extend(validate_contract(contract, schema))

    if not errors:
        errors.extend(validate_mirror_files(contract))

    if not errors:
        errors.extend(validate_offline_loading(contract))

    if errors:
        print("Offline tokenizer gate: FAIL")
        for err in errors:
            print(f"- {err}")
        return 1 if args.strict else 0

    print("Offline tokenizer gate: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
