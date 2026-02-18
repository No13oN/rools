#!/usr/bin/env python3
"""LDS validator: static checks + schema validation + anti-drift guards."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None

try:
    from jsonschema import FormatChecker, validate as jsonschema_validate  # type: ignore
except Exception:  # pragma: no cover
    FormatChecker = None
    jsonschema_validate = None

try:
    import tiktoken  # type: ignore
    _TIKTOKEN_IMPORT_ERROR = None
except Exception as exc:  # pragma: no cover
    tiktoken = None
    _TIKTOKEN_IMPORT_ERROR = exc


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PATHS = [
    "docs/standards/lds-spec.md",
    "docs/standards/lds-execution-card.md",
    "docs/standards/lds-standards-profile.md",
    "docs/governance/lds-glossary.md",
    "docs/governance/lds-changelog.md",
    "docs/governance/lds-waivers.md",
    "docs/governance/lds-ownership.yaml",
    "docs/governance/lds-canonical-tier0.md",
    "docs/governance/lds-governance-raci.md",
    "docs/governance/lds-readiness-audit.md",
    "contracts/schemas/lds-frontmatter.schema.json",
    "contracts/rules/lds-ruleset.json",
    "contracts/rules/lds-ruleset.schema.json",
    "contracts/rules/lds-publish-gate.json",
    "contracts/rules/lds-publish-gate.schema.json",
    "contracts/rules/lds-publish-gate.yaml",
    "contracts/governance/lds-waivers.yaml",
    "contracts/governance/lds-waivers.schema.json",
    "contracts/governance/lds-contract-manifest.schema.json",
    "contracts/governance/lds-contract-manifest.json",
    "contracts/governance/lds-protected-manifest.json",
    "contracts/governance/lds-protected-manifest.schema.json",
    "contracts/policy/lds-policy.json",
    "contracts/policy/lds-policy.schema.json",
    "contracts/memory/lds-memory-policy.json",
    "contracts/memory/lds-memory-policy.schema.json",
    "contracts/retrieval/lds-retrieval-policy.json",
    "contracts/retrieval/lds-retrieval-policy.schema.json",
    "contracts/token/lds-token-budget.json",
    "contracts/token/lds-token-budget.schema.json",
    "contracts/token/lds-tokenizer-mirror.json",
    "contracts/token/lds-tokenizer-mirror.schema.json",
    "contracts/evaluation/lds-eval-thresholds.json",
    "contracts/evaluation/lds-eval-thresholds.schema.json",
    "contracts/evaluation/lds-handoff-acceptance.json",
    "contracts/evaluation/lds-handoff-acceptance.schema.json",
    "contracts/memory/lds-memory-api.json",
    "contracts/memory/lds-memory-api.schema.json",
    "policies/opa/lds_gate.rego",
    "scripts/eval_semantic_gate.py",
    "scripts/validate_release_artifacts.py",
    "scripts/validate_tokenizer_offline.py",
    "scripts/build_policy_input.py",
    "scripts/eval_policy_gate.py",
    "scripts/validate_integrity_gate.py",
    "scripts/eval_handoff_acceptance.py",
]

_ENCODING = None
_STRICT_MODE = False


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
        raise ValueError(f"YAML root must be object/dict, got {type(data)}")
    return data


def file_exists_check() -> List[str]:
    errors: List[str] = []
    for rel in REQUIRED_PATHS:
        if not (ROOT / rel).exists():
            errors.append(f"missing required file: {rel}")
    return errors


def ci_workflow_check() -> List[str]:
    errors: List[str] = []
    candidates = [
        ROOT / ".github/workflows/lds-validate.yml",
        ROOT.parent / ".github/workflows/lds-validate.yml",
    ]
    if not any(p.exists() for p in candidates):
        errors.append(
            "missing CI workflow: expected `.github/workflows/lds-validate.yml` in project root or parent root"
        )
    return errors


def validate_tokenizer_mirror_runtime(strict: bool = False) -> List[str]:
    errors: List[str] = []

    contract_path = ROOT / "contracts/token/lds-tokenizer-mirror.json"
    if not contract_path.exists():
        return ["tokenizer mirror contract missing: contracts/token/lds-tokenizer-mirror.json"]

    try:
        contract = load_json(contract_path)
    except Exception as exc:
        return [f"tokenizer mirror contract invalid JSON ({exc})"]

    cache_dir_rel = contract.get("cache_dir")
    env_var = contract.get("cache_env_var", "TIKTOKEN_CACHE_DIR")
    encodings = contract.get("encodings", [])

    if not isinstance(cache_dir_rel, str):
        errors.append("tokenizer mirror contract missing cache_dir")
        return errors
    if not isinstance(encodings, list) or not encodings:
        errors.append("tokenizer mirror contract encodings must be non-empty list")
        return errors

    for enc in encodings:
        name = enc.get("name", "<unknown>")
        file_rel = enc.get("cache_file")
        expected_hash = enc.get("expected_sha256")

        if not isinstance(file_rel, str):
            errors.append(f"tokenizer mirror entry missing cache_file: {name}")
            continue
        if not isinstance(expected_hash, str):
            errors.append(f"tokenizer mirror entry missing expected_sha256: {name}")
            continue

        path = ROOT / file_rel
        if not path.exists():
            errors.append(f"tokenizer mirror file missing: {file_rel}")
            continue

        actual = sha256_of_file(path)
        if actual != expected_hash:
            errors.append(
                f"tokenizer mirror hash mismatch for {name}: {actual} != {expected_hash}"
            )

    if strict and not errors:
        cache_dir_abs = (ROOT / cache_dir_rel).resolve()
        os.environ[str(env_var)] = str(cache_dir_abs)

        try:
            import tiktoken.load as tkload  # type: ignore
        except Exception as exc:
            errors.append(f"tokenizer mirror runtime: failed to import tiktoken.load ({exc})")
            return errors

        original_read_file = tkload.read_file

        def _blocked_read_file(blobpath: str) -> bytes:
            raise RuntimeError(
                f"network access disabled during strict tokenizer check ({blobpath})"
            )

        tkload.read_file = _blocked_read_file
        try:
            for enc in encodings:
                name = enc.get("name")
                if not isinstance(name, str):
                    errors.append("tokenizer mirror entry missing name")
                    continue
                try:
                    tiktoken.get_encoding(name)
                except Exception as exc:
                    errors.append(f"offline tokenizer load failed for {name} ({exc})")
        finally:
            tkload.read_file = original_read_file

    return errors


def dependency_check(strict: bool = False) -> List[str]:
    errors: List[str] = []
    if yaml is None:
        errors.append("dependency missing: pyyaml")
    if jsonschema_validate is None or FormatChecker is None:
        errors.append("dependency missing: jsonschema")
    if tiktoken is None:
        details = f" ({_TIKTOKEN_IMPORT_ERROR})" if _TIKTOKEN_IMPORT_ERROR else ""
        errors.append(f"dependency missing: tiktoken{details}")
        return errors

    errors.extend(validate_tokenizer_mirror_runtime(strict=strict))

    return errors


def extract_frontmatter(md_text: str) -> Tuple[Dict[str, Any], List[str]]:
    errors: List[str] = []
    lines = md_text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, ["frontmatter missing"]

    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break
    if end_idx is None:
        return {}, ["frontmatter opening found but closing delimiter missing"]

    block = "\n".join(lines[1:end_idx])

    if yaml is not None:
        try:
            data = yaml.safe_load(block)  # type: ignore
            if data is None:
                data = {}
            if not isinstance(data, dict):
                return {}, ["frontmatter is not a YAML mapping/object"]
            return data, errors
        except Exception as exc:
            return {}, [f"frontmatter YAML parse failed: {exc}"]

    meta: Dict[str, Any] = {}
    for raw in lines[1:end_idx]:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip().strip(chr(34)).strip(chr(39))
    return meta, errors


def heading_skip_errors(md_text: str) -> List[str]:
    levels = [len(m.group(1)) for m in re.finditer(r"^(#{1,6})\s+\S", md_text, re.MULTILINE)]
    errors: List[str] = []
    for prev, curr in zip(levels, levels[1:]):
        if curr > prev + 1:
            errors.append(f"heading skip detected: H{prev} -> H{curr}")
    return errors


def code_fence_errors(md_text: str) -> List[str]:
    lines = md_text.splitlines()
    errors: List[str] = []
    open_len = None

    fence_re = re.compile(r"^(`{3,})(.*)$")
    for idx, line in enumerate(lines, 1):
        m = fence_re.match(line.rstrip())
        if not m:
            continue

        ticks = m.group(1)
        tail = m.group(2).strip()

        if open_len is None:
            if not tail:
                errors.append(f"line {idx}: opening code fence missing language tag")
            open_len = len(ticks)
        else:
            if len(ticks) == open_len and not tail:
                open_len = None

    if open_len is not None:
        errors.append("unclosed code fence block")
    return errors


def alt_text_errors(md_text: str) -> List[str]:
    errors: List[str] = []
    for m in re.finditer(r"!\[([^\]]*)\]\(([^)]+)\)", md_text):
        alt = m.group(1).strip()
        target = m.group(2).strip()
        if target and not alt:
            errors.append("image detected with empty alt text")
    return errors


def estimate_tokens(md_text: str) -> int:
    global _ENCODING
    if tiktoken is None:
        raise RuntimeError("tiktoken is required for token counting")
    if _ENCODING is None:
        try:
            _ENCODING = tiktoken.get_encoding("cl100k_base")
        except Exception as exc:
            if _STRICT_MODE:
                raise RuntimeError(f"exact tokenization unavailable in strict mode ({exc})")
            # Non-strict mode can still use deterministic approximation.
            _ENCODING = "__fallback__"
    if _ENCODING == "__fallback__":
        return max(len(md_text) // 4, len(md_text.split()))
    return len(_ENCODING.encode(md_text))


def rule_id_set_from_text(text: str) -> Set[str]:
    return set(re.findall(r"LDS-MUST-\d{3}", text))


def validate_json_against_schema(json_path: Path, schema_path: Path) -> List[str]:
    errors: List[str] = []
    instance = load_json(json_path)
    schema = load_json(schema_path)

    if jsonschema_validate is None or FormatChecker is None:
        errors.append(
            f"jsonschema dependency missing; cannot validate {json_path} against {schema_path}"
        )
        return errors

    try:
        jsonschema_validate(instance=instance, schema=schema, format_checker=FormatChecker())
    except Exception as exc:
        errors.append(f"{json_path}: schema validation failed ({exc})")
    return errors


def validate_yaml_data_against_schema(data: Dict[str, Any], schema_path: Path, context: str) -> List[str]:
    errors: List[str] = []
    if jsonschema_validate is None or FormatChecker is None:
        errors.append(f"jsonschema dependency missing; cannot validate YAML context `{context}`")
        return errors
    schema = load_json(schema_path)
    try:
        jsonschema_validate(instance=data, schema=schema, format_checker=FormatChecker())
    except Exception as exc:
        errors.append(f"{context}: schema validation failed ({exc})")
    return errors


def validate_frontmatter_schema(meta: Dict[str, Any], schema: Dict[str, Any], path: Path) -> List[str]:
    errors: List[str] = []
    if jsonschema_validate is None or FormatChecker is None:
        required = schema.get("required", [])
        for field in required:
            if field not in meta:
                errors.append(f"{path}: missing frontmatter field `{field}`")
        return errors

    try:
        jsonschema_validate(instance=meta, schema=schema, format_checker=FormatChecker())
    except Exception as exc:
        errors.append(f"{path}: frontmatter schema validation failed ({exc})")
    return errors


def parse_iso_date(value: str, context: str) -> Tuple[date | None, List[str]]:
    try:
        return date.fromisoformat(value), []
    except Exception:
        return None, [f"{context}: invalid ISO date `{value}`"]


def resolve_manifest_path(path_str: str) -> Tuple[Path | None, List[str]]:
    errors: List[str] = []
    abs_path = (ROOT / path_str).resolve()
    allowed_roots = [ROOT.resolve(), ROOT.parent.resolve()]
    if not any(abs_path == r or str(abs_path).startswith(str(r) + "/") for r in allowed_roots):
        errors.append(f"protected-manifest path escapes allowed roots: {path_str}")
        return None, errors
    return abs_path, errors


def sha256_of_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def load_waiver_registry() -> Tuple[Dict[str, Any], List[str]]:
    errors: List[str] = []
    waivers_path = ROOT / "contracts/governance/lds-waivers.yaml"
    waivers_schema = ROOT / "contracts/governance/lds-waivers.schema.json"

    waivers_doc = load_yaml(waivers_path)
    errors.extend(validate_yaml_data_against_schema(waivers_doc, waivers_schema, str(waivers_path)))

    today = date.today()
    for waiver in waivers_doc.get("waivers", []):
        status = waiver.get("status")
        expires_on = waiver.get("expires_on")
        waiver_id = waiver.get("waiver_id", "<unknown>")

        if isinstance(expires_on, str):
            exp_date, dt_errors = parse_iso_date(expires_on, f"waiver {waiver_id}")
            errors.extend(dt_errors)
            if exp_date is not None and status == "active" and exp_date < today:
                errors.append(f"waiver expired but still active: {waiver_id}")
        else:
            errors.append(f"waiver {waiver_id}: missing or invalid expires_on")

    return waivers_doc, errors


def has_active_hash_waiver(waivers_doc: Dict[str, Any], scope_path: str) -> bool:
    today = date.today()
    for waiver in waivers_doc.get("waivers", []):
        if waiver.get("status") != "active":
            continue
        if waiver.get("waiver_type") != "tier0_hash_override":
            continue
        if waiver.get("scope_path") != scope_path:
            continue
        expires_on = waiver.get("expires_on")
        if not isinstance(expires_on, str):
            continue
        waiver_id = waiver.get("waiver_id", "<unknown>")
        exp_date, _ = parse_iso_date(expires_on, f"waiver {waiver_id}")
        if exp_date is None:
            continue
        if exp_date >= today:
            return True
    return False


def validate_protected_manifest() -> List[str]:
    errors: List[str] = []
    manifest_path = ROOT / "contracts/governance/lds-protected-manifest.json"
    manifest_schema = ROOT / "contracts/governance/lds-protected-manifest.schema.json"

    errors.extend(validate_json_against_schema(manifest_path, manifest_schema))
    if errors:
        return errors

    manifest = load_json(manifest_path)
    waivers_doc, waiver_errors = load_waiver_registry()
    errors.extend(waiver_errors)

    entries = manifest.get("entries", [])
    seen_paths: Set[str] = set()

    for entry in entries:
        rel_path = entry.get("path")
        if not isinstance(rel_path, str):
            errors.append("protected-manifest entry missing string `path`")
            continue

        if rel_path in seen_paths:
            errors.append(f"protected-manifest duplicate path: {rel_path}")
            continue
        seen_paths.add(rel_path)

        resolved, resolve_errors = resolve_manifest_path(rel_path)
        errors.extend(resolve_errors)
        if resolved is None:
            continue

        if not resolved.exists():
            errors.append(f"protected-manifest file missing: {rel_path}")
            continue

        expected = entry.get("sha256")
        if not isinstance(expected, str):
            errors.append(f"protected-manifest entry missing sha256: {rel_path}")
            continue

        actual = sha256_of_file(resolved)
        if actual != expected:
            waiver_allowed = bool(entry.get("waiver_allowed", False))
            if waiver_allowed and has_active_hash_waiver(waivers_doc, rel_path):
                continue
            errors.append(f"protected-manifest hash mismatch: {rel_path}")

    return errors


def validate_governance_contracts() -> List[str]:
    errors: List[str] = []

    waivers_doc, waiver_errors = load_waiver_registry()
    errors.extend(waiver_errors)

    raci_text = (ROOT / "docs/governance/lds-governance-raci.md").read_text(encoding="utf-8")
    if "RACI Matrix" not in raci_text:
        errors.append("governance RACI document missing `RACI Matrix` section")

    tier0_text = (ROOT / "docs/governance/lds-canonical-tier0.md").read_text(encoding="utf-8")
    if "Tier-0 Paths" not in tier0_text:
        errors.append("canonical Tier-0 document missing `Tier-0 Paths` section")

    if "waivers" not in waivers_doc:
        errors.append("waiver registry missing `waivers` list")

    return errors


def validate_runtime_contracts() -> List[str]:
    errors: List[str] = []

    pairs = [
        (
            ROOT / "contracts/rules/lds-ruleset.json",
            ROOT / "contracts/rules/lds-ruleset.schema.json",
        ),
        (
            ROOT / "contracts/memory/lds-memory-policy.json",
            ROOT / "contracts/memory/lds-memory-policy.schema.json",
        ),
        (
            ROOT / "contracts/memory/lds-memory-api.json",
            ROOT / "contracts/memory/lds-memory-api.schema.json",
        ),
        (
            ROOT / "contracts/retrieval/lds-retrieval-policy.json",
            ROOT / "contracts/retrieval/lds-retrieval-policy.schema.json",
        ),
        (
            ROOT / "contracts/token/lds-token-budget.json",
            ROOT / "contracts/token/lds-token-budget.schema.json",
        ),
        (
            ROOT / "contracts/token/lds-tokenizer-mirror.json",
            ROOT / "contracts/token/lds-tokenizer-mirror.schema.json",
        ),
        (
            ROOT / "contracts/evaluation/lds-eval-thresholds.json",
            ROOT / "contracts/evaluation/lds-eval-thresholds.schema.json",
        ),
        (
            ROOT / "contracts/evaluation/lds-handoff-acceptance.json",
            ROOT / "contracts/evaluation/lds-handoff-acceptance.schema.json",
        ),
    ]
    for instance, schema in pairs:
        errors.extend(validate_json_against_schema(instance, schema))

    retrieval = load_json(ROOT / "contracts/retrieval/lds-retrieval-policy.json")
    denylist = set(retrieval.get("denylist_globs", []))
    for required_glob in ("legacy/**", "tests/fixtures/**"):
        if required_glob not in denylist:
            errors.append(f"retrieval denylist missing required glob: {required_glob}")

    token_budget = load_json(ROOT / "contracts/token/lds-token-budget.json")
    doc_limits = token_budget.get("document_limits", {})
    max_doc = doc_limits.get("max_tokens_per_doc")
    if isinstance(max_doc, int) and max_doc > 10000:
        errors.append("token budget violation: max_tokens_per_doc > 10000")

    eval_cfg = load_json(ROOT / "contracts/evaluation/lds-eval-thresholds.json")
    thresholds = eval_cfg.get("thresholds", {})
    hallucination_max = thresholds.get("hallucination_rate_max")
    if isinstance(hallucination_max, (int, float)) and hallucination_max > 0.05:
        errors.append("evaluation contract violation: hallucination_rate_max > 0.05")

    return errors


def list_contract_files_for_manifest() -> Set[str]:
    files: Set[str] = set()
    excluded = {
        "contracts/governance/lds-contract-manifest.json",
        "contracts/governance/lds-protected-manifest.json",
    }

    for path in (ROOT / "contracts").rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel in excluded:
            # Excluded to avoid recursive checksum dependency between manifests.
            continue
        if rel.endswith(".json") or rel.endswith(".yaml") or rel.endswith(".yml"):
            files.add(rel)

    return files


def validate_contract_manifest() -> List[str]:
    errors: List[str] = []
    manifest_rel = "contracts/governance/lds-contract-manifest.json"
    manifest_path = ROOT / manifest_rel
    manifest_schema = ROOT / "contracts/governance/lds-contract-manifest.schema.json"

    errors.extend(validate_json_against_schema(manifest_path, manifest_schema))
    if errors:
        return errors

    manifest = load_json(manifest_path)
    entries = manifest.get("entries", [])

    contracts_root = (ROOT / "contracts").resolve()
    seen_paths: Set[str] = set()
    listed_paths: Set[str] = set()

    for entry in entries:
        rel_path = entry.get("path")
        if not isinstance(rel_path, str):
            errors.append("contract-manifest entry missing string `path`")
            continue

        if rel_path in seen_paths:
            errors.append(f"contract-manifest duplicate path: {rel_path}")
            continue
        seen_paths.add(rel_path)
        listed_paths.add(rel_path)

        resolved, resolve_errors = resolve_manifest_path(rel_path)
        errors.extend(resolve_errors)
        if resolved is None:
            continue

        if not (resolved == contracts_root or str(resolved).startswith(str(contracts_root) + "/")):
            errors.append(f"contract-manifest path outside contracts root: {rel_path}")
            continue

        if not resolved.exists():
            errors.append(f"contract-manifest file missing: {rel_path}")
            continue

        expected = entry.get("sha256")
        if not isinstance(expected, str):
            errors.append(f"contract-manifest entry missing sha256: {rel_path}")
        else:
            actual = sha256_of_file(resolved)
            if actual != expected:
                errors.append(f"contract-manifest hash mismatch: {rel_path}")

        kind = entry.get("kind")
        fmt = entry.get("format")
        schema_rel = entry.get("schema_path")

        if kind == "schema":
            if fmt != "json":
                errors.append(f"contract-manifest schema entry must be json: {rel_path}")
            if not rel_path.endswith(".schema.json"):
                errors.append(f"contract-manifest schema entry must end with .schema.json: {rel_path}")
            continue

        if kind != "instance":
            errors.append(f"contract-manifest unknown kind for {rel_path}: {kind}")
            continue

        if rel_path.endswith(".schema.json"):
            errors.append(f"contract-manifest instance cannot be a schema file: {rel_path}")

        if not isinstance(schema_rel, str):
            errors.append(f"contract-manifest instance missing schema_path: {rel_path}")
            continue

        schema_abs = ROOT / schema_rel
        if not schema_abs.exists():
            errors.append(f"contract-manifest schema_path missing: {schema_rel}")
            continue

        if fmt == "json":
            errors.extend(validate_json_against_schema(resolved, schema_abs))
        elif fmt == "yaml":
            try:
                data = load_yaml(resolved)
            except Exception as exc:
                errors.append(f"{rel_path}: YAML parse failed ({exc})")
                continue
            errors.extend(validate_yaml_data_against_schema(data, schema_abs, rel_path))
        else:
            errors.append(f"contract-manifest unsupported format `{fmt}` for {rel_path}")

    expected_files = list_contract_files_for_manifest()
    for rel in sorted(expected_files - listed_paths):
        errors.append(f"contract-manifest missing file: {rel}")
    for rel in sorted(listed_paths - expected_files):
        errors.append(f"contract-manifest unexpected file: {rel}")

    return errors


def validate_drift() -> List[str]:
    errors: List[str] = []

    ruleset = load_json(ROOT / "contracts/rules/lds-ruleset.json")
    policy = load_json(ROOT / "contracts/policy/lds-policy.json")
    gate_json = load_json(ROOT / "contracts/rules/lds-publish-gate.json")

    ruleset_ids = {r["id"] for r in ruleset.get("rules", [])}
    policy_ids = {r["id"] for r in policy.get("must_rules", [])}

    spec_text = (ROOT / "docs/standards/lds-spec.md").read_text(encoding="utf-8")
    card_text = (ROOT / "docs/standards/lds-execution-card.md").read_text(encoding="utf-8")
    spec_ids = rule_id_set_from_text(spec_text)
    card_ids = rule_id_set_from_text(card_text)

    if ruleset_ids != policy_ids:
        errors.append("anti-drift: ruleset IDs != policy IDs")
    if ruleset_ids != spec_ids:
        errors.append("anti-drift: ruleset IDs != spec IDs")
    if ruleset_ids != card_ids:
        errors.append("anti-drift: ruleset IDs != execution-card IDs")

    policy_gate = policy.get("publish_gate", {})
    policy_static = set(policy_gate.get("static", {}).get("required_checks", []))
    gate_static = set(gate_json.get("static_gate", {}).get("required", []))
    if policy_static != gate_static:
        errors.append("anti-drift: static gate checks differ between policy and gate.json")

    policy_semantic = policy_gate.get("semantic", {})
    gate_semantic = gate_json.get("semantic_gate", {})
    if policy_semantic.get("weighted_score_min") != gate_semantic.get("weighted_score_min"):
        errors.append("anti-drift: weighted_score_min mismatch")
    if policy_semantic.get("class_thresholds") != gate_semantic.get("class_thresholds"):
        errors.append("anti-drift: semantic class thresholds mismatch")
    if set(policy_semantic.get("block_on_critical_hallucination", [])) != set(
        gate_semantic.get("block_on_critical_hallucination", [])
    ):
        errors.append("anti-drift: critical hallucination block classes mismatch")

    policy_gov = set(policy_gate.get("governance", {}).get("required_checks", []))
    gate_gov = set(gate_json.get("governance_gate", {}).get("required", []))
    if policy_gov != gate_gov:
        errors.append("anti-drift: governance gate checks mismatch")

    if set(policy.get("required_artifacts", [])) != set(gate_json.get("required_artifacts", [])):
        errors.append("anti-drift: required artifacts mismatch between policy and gate.json")

    try:
        gate_yaml = load_yaml(ROOT / "contracts/rules/lds-publish-gate.yaml")
        y_static = set(gate_yaml.get("static_gate", {}).get("required", []))
        j_static = set(gate_json.get("static_gate", {}).get("required", []))
        if y_static != j_static:
            errors.append("anti-drift: static gate mismatch between gate.yaml and gate.json")

        y_sem = gate_yaml.get("semantic_gate", {})
        j_sem = gate_json.get("semantic_gate", {})
        if y_sem.get("weighted_score_min") != j_sem.get("weighted_score_min"):
            errors.append("anti-drift: weighted_score_min mismatch between gate.yaml and gate.json")
        if y_sem.get("class_thresholds") != j_sem.get("class_thresholds"):
            errors.append("anti-drift: class_thresholds mismatch between gate.yaml and gate.json")
        if set(y_sem.get("block_on_critical_hallucination", [])) != set(
            j_sem.get("block_on_critical_hallucination", [])
        ):
            errors.append("anti-drift: hallucination block classes mismatch between gate.yaml and gate.json")

        y_gov = set(gate_yaml.get("governance_gate", {}).get("required", []))
        j_gov = set(gate_json.get("governance_gate", {}).get("required", []))
        if y_gov != j_gov:
            errors.append("anti-drift: governance gate mismatch between gate.yaml and gate.json")

        if set(gate_yaml.get("required_artifacts", [])) != set(gate_json.get("required_artifacts", [])):
            errors.append("anti-drift: required_artifacts mismatch between gate.yaml and gate.json")
    except Exception as exc:
        errors.append(f"anti-drift: failed to parse gate.yaml ({exc})")

    return errors


def validate_markdown_file(path: Path, required_fields: List[str]) -> List[str]:
    errors: List[str] = []
    text = path.read_text(encoding="utf-8")

    meta, fm_errors = extract_frontmatter(text)
    errors.extend([f"{path}: {err}" for err in fm_errors])
    if not fm_errors:
        missing = [f for f in required_fields if f not in meta]
        for field in missing:
            errors.append(f"{path}: missing frontmatter field `{field}`")

        schema = load_json(ROOT / "contracts/schemas/lds-frontmatter.schema.json")
        errors.extend(validate_frontmatter_schema(meta, schema, path))

    for err in heading_skip_errors(text):
        errors.append(f"{path}: {err}")
    for err in code_fence_errors(text):
        errors.append(f"{path}: {err}")
    for err in alt_text_errors(text):
        errors.append(f"{path}: {err}")

    try:
        token_count = estimate_tokens(text)
    except Exception as exc:
        errors.append(f"{path}: token counting failed ({exc})")
        return errors

    if token_count > 10000:
        errors.append(f"{path}: token count exceeds 10,000")
    return errors


def validate_fixtures() -> List[str]:
    errors: List[str] = []
    schema = load_json(ROOT / "contracts/schemas/lds-frontmatter.schema.json")
    required_fields = schema.get("required", [])

    good_path = ROOT / "tests/fixtures/good/good_doc.md"
    bad_paths = [
        ROOT / "tests/fixtures/bad/bad_missing_frontmatter.md",
        ROOT / "tests/fixtures/bad/bad_heading_skip.md",
        ROOT / "tests/fixtures/bad/bad_untagged_code.md",
        ROOT / "tests/fixtures/bad/bad_empty_alt.md",
    ]

    good_errors = validate_markdown_file(good_path, required_fields)
    if good_errors:
        errors.append("good fixture failed validation")
        errors.extend(good_errors)

    for bad in bad_paths:
        bad_errors = validate_markdown_file(bad, required_fields)
        if not bad_errors:
            errors.append(f"bad fixture unexpectedly passed: {bad}")
    return errors


def run_all(strict: bool = False, include_integrity: bool = True) -> Tuple[bool, List[str]]:
    global _STRICT_MODE
    _STRICT_MODE = strict

    errors: List[str] = []

    errors.extend(file_exists_check())
    errors.extend(ci_workflow_check())
    errors.extend(dependency_check(strict=strict))

    if not errors:
        schema = load_json(ROOT / "contracts/schemas/lds-frontmatter.schema.json")
        required_fields = schema.get("required", [])

        md_files = [
            ROOT / "docs/standards/lds-spec.md",
            ROOT / "docs/standards/lds-execution-card.md",
            ROOT / "docs/standards/lds-standards-profile.md",
            ROOT / "docs/governance/lds-glossary.md",
            ROOT / "docs/governance/lds-changelog.md",
            ROOT / "docs/governance/lds-waivers.md",
            ROOT / "docs/governance/lds-canonical-tier0.md",
            ROOT / "docs/governance/lds-governance-raci.md",
            ROOT / "docs/governance/lds-readiness-audit.md",
        ]
        for md in md_files:
            errors.extend(validate_markdown_file(md, required_fields))

        ownership = (ROOT / "docs/governance/lds-ownership.yaml").read_text(encoding="utf-8")
        for marker in (
            "spec_owner",
            "contract_owner",
            "governance_owner",
            "validation_owner",
        ):
            if marker not in ownership:
                errors.append(f"ownership map missing block: {marker}")

        for rel in (
            "contracts/rules/lds-ruleset.json",
            "contracts/rules/lds-ruleset.schema.json",
            "contracts/rules/lds-publish-gate.json",
            "contracts/rules/lds-publish-gate.schema.json",
            "contracts/policy/lds-policy.json",
            "contracts/policy/lds-policy.schema.json",
            "contracts/schemas/lds-frontmatter.schema.json",
            "contracts/governance/lds-contract-manifest.json",
            "contracts/governance/lds-contract-manifest.schema.json",
            "contracts/governance/lds-protected-manifest.json",
            "contracts/governance/lds-protected-manifest.schema.json",
            "contracts/governance/lds-waivers.schema.json",
            "contracts/memory/lds-memory-policy.json",
            "contracts/memory/lds-memory-policy.schema.json",
            "contracts/memory/lds-memory-api.json",
            "contracts/memory/lds-memory-api.schema.json",
            "contracts/retrieval/lds-retrieval-policy.json",
            "contracts/retrieval/lds-retrieval-policy.schema.json",
            "contracts/token/lds-token-budget.json",
            "contracts/token/lds-token-budget.schema.json",
            "contracts/token/lds-tokenizer-mirror.json",
            "contracts/token/lds-tokenizer-mirror.schema.json",
            "contracts/evaluation/lds-eval-thresholds.json",
            "contracts/evaluation/lds-eval-thresholds.schema.json",
            "contracts/evaluation/lds-handoff-acceptance.json",
            "contracts/evaluation/lds-handoff-acceptance.schema.json",
        ):
            try:
                load_json(ROOT / rel)
            except Exception as exc:
                errors.append(f"{rel}: invalid JSON ({exc})")

        errors.extend(
            validate_json_against_schema(
                ROOT / "contracts/rules/lds-publish-gate.json",
                ROOT / "contracts/rules/lds-publish-gate.schema.json",
            )
        )
        errors.extend(
            validate_json_against_schema(
                ROOT / "contracts/policy/lds-policy.json",
                ROOT / "contracts/policy/lds-policy.schema.json",
            )
        )

        errors.extend(validate_drift())
        errors.extend(validate_governance_contracts())
        errors.extend(validate_runtime_contracts())
        if include_integrity:
            errors.extend(validate_contract_manifest())
            errors.extend(validate_protected_manifest())
        errors.extend(validate_fixtures())

    if strict and errors:
        return False, errors
    return (len(errors) == 0), errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate LDS project structure, schemas, and anti-drift checks."
    )
    parser.add_argument("--strict", action="store_true", help="Fail with non-zero exit code if any errors exist.")
    parser.add_argument("--skip-integrity", action="store_true", help="Skip contract/protected manifest integrity checks.")
    args = parser.parse_args()

    ok, errors = run_all(strict=args.strict, include_integrity=not args.skip_integrity)
    if ok:
        print("LDS validation: PASS")
        return 0

    print("LDS validation: FAIL")
    for err in errors:
        print(f"- {err}")
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
