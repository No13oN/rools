#!/usr/bin/env python3
"""LDS memory backend adapter v1 (file-based reference implementation)."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

ROOT = Path(__file__).resolve().parents[1]


class MemoryBackendAdapterV1:
    """Reference backend that implements append/query/compact/evict on JSONL files."""

    def __init__(self, policy_path: Path, store_dir: Path) -> None:
        self.policy_path = policy_path
        self.store_dir = store_dir
        self.policy = self._load_json(policy_path)
        self.memory_classes = self.policy.get("memory_classes", {})
        self.requires_provenance = bool(
            self.policy.get("merge_policy", {}).get("requires_provenance", True)
        )

        if not isinstance(self.memory_classes, dict) or not self.memory_classes:
            raise ValueError("memory policy is invalid: memory_classes must be non-empty object")
        self.store_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _load_json(path: Path) -> Dict[str, Any]:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _sha256(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _class_file(self, memory_class: str) -> Path:
        self._validate_memory_class(memory_class)
        return self.store_dir / f"{memory_class}.jsonl"

    def _validate_memory_class(self, memory_class: str) -> None:
        if memory_class not in self.memory_classes:
            allowed = ", ".join(sorted(self.memory_classes.keys()))
            raise ValueError(f"unknown memory_class '{memory_class}', allowed: {allowed}")

    def _ttl_for_class(self, memory_class: str) -> timedelta:
        config = self.memory_classes[memory_class]
        if "ttl_hours" in config:
            return timedelta(hours=int(config["ttl_hours"]))
        if "ttl_days" in config:
            return timedelta(days=int(config["ttl_days"]))
        return timedelta(days=1)

    def _load_records(self, memory_class: str) -> List[Dict[str, Any]]:
        path = self._class_file(memory_class)
        if not path.exists():
            return []

        records: List[Dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                records.append(json.loads(line))
        return records

    def _write_records(self, memory_class: str, records: Iterable[Dict[str, Any]]) -> None:
        path = self._class_file(memory_class)
        with path.open("w", encoding="utf-8") as f:
            for rec in records:
                f.write(json.dumps(rec, ensure_ascii=True) + "\n")

    def _build_record(
        self,
        memory_class: str,
        raw_record: Dict[str, Any],
        provenance: Dict[str, Any],
    ) -> Dict[str, Any]:
        content = str(raw_record.get("content", "")).strip()
        if not content:
            raise ValueError("record.content must be non-empty")

        now = datetime.now(timezone.utc)
        canonical_content = " ".join(content.lower().split())
        canonical_hash = self._sha256(canonical_content)
        source = str(provenance.get("source", "unknown"))
        entropy = f"{canonical_hash}:{now.isoformat()}:{source}"
        record_id = self._sha256(entropy)[:24]
        ttl = self._ttl_for_class(memory_class)

        evidence_score = raw_record.get("evidence_score", 0.5)
        try:
            evidence_score = float(evidence_score)
        except Exception as exc:
            raise ValueError(f"record.evidence_score must be float-compatible ({exc})") from exc

        tags = raw_record.get("tags", [])
        if tags is None:
            tags = []
        if not isinstance(tags, list):
            raise ValueError("record.tags must be a list when provided")

        return {
            "record_id": record_id,
            "memory_class": memory_class,
            "canonical_hash": canonical_hash,
            "content": content,
            "evidence_score": max(0.0, min(1.0, evidence_score)),
            "tags": [str(tag) for tag in tags],
            "created_at": now.isoformat().replace("+00:00", "Z"),
            "expires_on": (now + ttl).date().isoformat(),
            "provenance": provenance,
            "tombstone": False,
        }

    def append(
        self,
        memory_class: str,
        records: List[Dict[str, Any]],
        provenance: Dict[str, Any] | None,
    ) -> Dict[str, Any]:
        self._validate_memory_class(memory_class)
        provenance = provenance or {}
        if self.requires_provenance and not provenance:
            raise ValueError("provenance is required by memory policy")

        existing = self._load_records(memory_class)
        existing_hashes = {
            str(rec.get("canonical_hash", ""))
            for rec in existing
            if not bool(rec.get("tombstone", False))
        }

        accepted: List[Dict[str, Any]] = []
        for raw in records:
            if not isinstance(raw, dict):
                raise ValueError("append records must be objects")
            built = self._build_record(memory_class, raw, provenance)
            if built["canonical_hash"] in existing_hashes:
                continue
            accepted.append(built)
            existing_hashes.add(built["canonical_hash"])

        if accepted:
            self._write_records(memory_class, [*existing, *accepted])

        return {
            "accepted_count": len(accepted),
            "record_ids": [rec["record_id"] for rec in accepted],
        }

    @staticmethod
    def _safe_date(value: Any) -> date | None:
        if not isinstance(value, str):
            return None
        try:
            return date.fromisoformat(value[:10])
        except Exception:
            return None

    def query(
        self,
        query: str,
        memory_classes: List[str] | None,
        top_k: int,
        filters: Dict[str, Any] | None,
    ) -> Dict[str, Any]:
        text = query.strip().lower()
        if not text:
            raise ValueError("query must be non-empty")

        classes = memory_classes or sorted(self.memory_classes.keys())
        for cls in classes:
            self._validate_memory_class(cls)

        today = date.today()
        scored: List[Dict[str, Any]] = []

        for cls in classes:
            for rec in self._load_records(cls):
                if bool(rec.get("tombstone", False)):
                    continue
                expires = self._safe_date(rec.get("expires_on"))
                if expires is not None and expires < today:
                    continue

                content = str(rec.get("content", "")).lower()
                token_hits = sum(content.count(tok) for tok in text.split())
                if token_hits <= 0:
                    continue

                evidence = float(rec.get("evidence_score", 0.0))
                score = float(token_hits) + evidence
                scored.append(
                    {
                        "record_id": rec.get("record_id"),
                        "score": round(score, 4),
                        "evidence": {
                            "memory_class": rec.get("memory_class"),
                            "content": rec.get("content"),
                            "provenance": rec.get("provenance", {}),
                        },
                    }
                )

        scored.sort(key=lambda item: item["score"], reverse=True)
        top = max(1, int(top_k))

        return {
            "results": scored[:top],
            "trace_id": self._sha256(f"{datetime.now(timezone.utc).isoformat()}:{query}")[:16],
            "filters": filters or {},
        }

    def compact(self, memory_class: str, before_date: str, max_tokens: int) -> Dict[str, Any]:
        self._validate_memory_class(memory_class)

        try:
            cutoff = date.fromisoformat(before_date)
        except Exception as exc:
            raise ValueError(f"before_date must be YYYY-MM-DD ({exc})") from exc

        records = self._load_records(memory_class)
        eligible: List[Dict[str, Any]] = []
        for rec in records:
            if bool(rec.get("tombstone", False)):
                continue
            created = self._safe_date(rec.get("created_at"))
            if created is None:
                continue
            if created <= cutoff:
                eligible.append(rec)

        if not eligible:
            return {"compacted_count": 0, "summary_ids": []}

        text = "\n".join(str(rec.get("content", "")).strip() for rec in eligible).strip()
        words = text.split()
        summary = " ".join(words[: max(1, int(max_tokens))])

        max_evidence = max(float(rec.get("evidence_score", 0.0)) for rec in eligible)
        append_result = self.append(
            memory_class,
            [
                {
                    "content": summary,
                    "evidence_score": max_evidence,
                    "tags": ["compacted-summary"],
                }
            ],
            {"source": "memory-compactor", "reason": "age-based compaction"},
        )

        summary_ids = append_result["record_ids"]
        summary_id = summary_ids[0] if summary_ids else None
        if summary_id:
            for rec in records:
                if rec in eligible:
                    rec["compacted_into"] = summary_id

        self._write_records(memory_class, records)
        return {
            "compacted_count": len(eligible),
            "summary_ids": summary_ids,
        }

    def evict(self, memory_class: str, selector: str, reason_code: str) -> Dict[str, Any]:
        self._validate_memory_class(memory_class)
        selector = selector.strip().lower()
        if selector not in {"expired", "all"}:
            raise ValueError("selector must be one of: expired, all")
        if not reason_code.strip():
            raise ValueError("reason_code must be non-empty")

        today = date.today()
        records = self._load_records(memory_class)
        tombstones: List[str] = []

        for rec in records:
            if bool(rec.get("tombstone", False)):
                continue

            should_evict = selector == "all"
            if selector == "expired":
                expires = self._safe_date(rec.get("expires_on"))
                should_evict = expires is not None and expires < today

            if not should_evict:
                continue

            rec["tombstone"] = True
            rec["tombstone_reason"] = reason_code
            rec["tombstoned_on"] = today.isoformat()
            tombstones.append(str(rec.get("record_id", "")))

        self._write_records(memory_class, records)
        return {
            "evicted_count": len(tombstones),
            "tombstones": tombstones,
        }


def parse_json_value(raw: str, field_name: str) -> Dict[str, Any]:
    try:
        data = json.loads(raw)
    except Exception as exc:
        raise ValueError(f"{field_name} must be valid JSON ({exc})") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return data


def load_records_from_args(records_file: str | None, record_values: List[str]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []

    if records_file:
        path = Path(records_file)
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            records.append(data)
        elif isinstance(data, list):
            for item in data:
                if not isinstance(item, dict):
                    raise ValueError("records file list must contain only objects")
                records.append(item)
        else:
            raise ValueError("records file must be a JSON object or JSON array")

    for raw in record_values:
        records.append(parse_json_value(raw, "--record"))

    if not records:
        raise ValueError("no records provided")

    return records


def main() -> int:
    parser = argparse.ArgumentParser(description="LDS memory backend adapter v1.")
    parser.add_argument(
        "--policy",
        default="contracts/memory/lds-memory-policy.json",
        help="Memory policy JSON path (relative to LDS root).",
    )
    parser.add_argument(
        "--store-dir",
        default="reports/handoff/memory_store",
        help="Storage directory for memory backend.",
    )

    sub = parser.add_subparsers(dest="cmd", required=True)

    p_append = sub.add_parser("append", help="Append records to a memory class")
    p_append.add_argument("--memory-class", required=True)
    p_append.add_argument("--records-file", help="JSON file with object or array of objects")
    p_append.add_argument("--record", action="append", default=[], help="Inline JSON record")
    p_append.add_argument("--provenance", default="{}", help="Provenance JSON object")

    p_query = sub.add_parser("query", help="Query records")
    p_query.add_argument("--query", required=True)
    p_query.add_argument("--memory-class", action="append", default=[])
    p_query.add_argument("--top-k", type=int, default=5)

    p_compact = sub.add_parser("compact", help="Compact old records")
    p_compact.add_argument("--memory-class", required=True)
    p_compact.add_argument("--before-date", required=True, help="YYYY-MM-DD")
    p_compact.add_argument("--max-tokens", type=int, default=256)

    p_evict = sub.add_parser("evict", help="Evict records")
    p_evict.add_argument("--memory-class", required=True)
    p_evict.add_argument("--selector", required=True, choices=["expired", "all"])
    p_evict.add_argument("--reason-code", required=True)

    args = parser.parse_args()

    try:
        adapter = MemoryBackendAdapterV1(ROOT / args.policy, ROOT / args.store_dir)

        if args.cmd == "append":
            records = load_records_from_args(args.records_file, args.record)
            provenance = parse_json_value(args.provenance, "--provenance")
            out = adapter.append(args.memory_class, records, provenance)
        elif args.cmd == "query":
            classes = args.memory_class if args.memory_class else None
            out = adapter.query(args.query, classes, args.top_k, filters={})
        elif args.cmd == "compact":
            out = adapter.compact(args.memory_class, args.before_date, args.max_tokens)
        elif args.cmd == "evict":
            out = adapter.evict(args.memory_class, args.selector, args.reason_code)
        else:
            raise ValueError(f"unsupported command: {args.cmd}")
    except Exception as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}, indent=2))
        return 1

    print(json.dumps({"status": "pass", "result": out}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
