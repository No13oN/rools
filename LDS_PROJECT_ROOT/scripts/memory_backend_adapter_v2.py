#!/usr/bin/env python3
"""LDS memory backend adapter v2 (SQLite production backend)."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sqlite3
import sys
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List

ROOT = Path(__file__).resolve().parents[1]
LOG = logging.getLogger("memory_backend_adapter_v2")


class MemoryBackendAdapterV2:
    """SQLite backend with transactional append/query/compact/evict operations."""

    SCHEMA_VERSION = "2.0.0"

    def __init__(self, policy_path: Path, db_path: Path) -> None:
        self.policy_path = policy_path
        self.db_path = db_path
        self.policy = self._load_json(policy_path)
        self.memory_classes = self.policy.get("memory_classes", {})
        self.requires_provenance = bool(
            self.policy.get("merge_policy", {}).get("requires_provenance", True)
        )

        if not isinstance(self.memory_classes, dict) or not self.memory_classes:
            raise ValueError("memory policy is invalid: memory_classes must be non-empty object")

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self._configure_sqlite()
        self._initialize_schema()

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            LOG.exception("failed to close sqlite connection")

    def __del__(self) -> None:  # pragma: no cover
        try:
            self.close()
        except Exception:
            pass

    @staticmethod
    def _load_json(path: Path) -> Dict[str, Any]:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _sha256(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @staticmethod
    def _safe_date(value: Any) -> date | None:
        if not isinstance(value, str):
            return None
        try:
            return date.fromisoformat(value[:10])
        except Exception:
            return None

    @staticmethod
    def _now_utc() -> datetime:
        return datetime.now(timezone.utc)

    def _configure_sqlite(self) -> None:
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.execute("PRAGMA busy_timeout=5000")

    def _initialize_schema(self) -> None:
        with self._tx():
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memory_records (
                    record_id TEXT PRIMARY KEY,
                    memory_class TEXT NOT NULL,
                    canonical_hash TEXT NOT NULL,
                    content TEXT NOT NULL,
                    evidence_score REAL NOT NULL,
                    tags_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_on TEXT NOT NULL,
                    provenance_json TEXT NOT NULL,
                    tombstone INTEGER NOT NULL DEFAULT 0,
                    tombstone_reason TEXT,
                    tombstoned_on TEXT,
                    compacted_into TEXT,
                    compliance_hold INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_memory_records_class_live "
                "ON memory_records(memory_class, tombstone, expires_on)"
            )
            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_memory_records_hash_live "
                "ON memory_records(memory_class, canonical_hash, tombstone)"
            )
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS backend_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            self._upsert_meta("schema_version", self.SCHEMA_VERSION)

    def _upsert_meta(self, key: str, value: str) -> None:
        self.conn.execute(
            """
            INSERT INTO backend_meta(key, value, updated_at)
            VALUES(?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value=excluded.value,
                updated_at=excluded.updated_at
            """,
            (key, value, self._now_utc().isoformat().replace("+00:00", "Z")),
        )

    @contextmanager
    def _tx(self) -> Iterator[None]:
        try:
            self.conn.execute("BEGIN")
            yield
            self.conn.commit()
        except sqlite3.DatabaseError as exc:
            self.conn.rollback()
            raise RuntimeError(f"sqlite transaction failed ({exc})") from exc

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

    def _build_record(
        self,
        memory_class: str,
        raw_record: Dict[str, Any],
        provenance: Dict[str, Any],
    ) -> Dict[str, Any]:
        content = str(raw_record.get("content", "")).strip()
        if not content:
            raise ValueError("record.content must be non-empty")

        now = self._now_utc()
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

    def _canonical_exists(self, memory_class: str, canonical_hash: str) -> bool:
        row = self.conn.execute(
            """
            SELECT 1
            FROM memory_records
            WHERE memory_class = ?
              AND canonical_hash = ?
              AND tombstone = 0
            LIMIT 1
            """,
            (memory_class, canonical_hash),
        ).fetchone()
        return row is not None

    def _row_to_record(self, row: sqlite3.Row) -> Dict[str, Any]:
        tags_raw = row["tags_json"]
        provenance_raw = row["provenance_json"]
        try:
            tags = json.loads(tags_raw)
        except Exception:
            tags = []
        try:
            provenance = json.loads(provenance_raw)
        except Exception:
            provenance = {}
        if not isinstance(tags, list):
            tags = []
        if not isinstance(provenance, dict):
            provenance = {}

        return {
            "record_id": row["record_id"],
            "memory_class": row["memory_class"],
            "canonical_hash": row["canonical_hash"],
            "content": row["content"],
            "evidence_score": float(row["evidence_score"]),
            "tags": [str(tag) for tag in tags],
            "created_at": row["created_at"],
            "expires_on": row["expires_on"],
            "provenance": provenance,
            "tombstone": bool(row["tombstone"]),
            "tombstone_reason": row["tombstone_reason"],
            "tombstoned_on": row["tombstoned_on"],
            "compacted_into": row["compacted_into"],
            "compliance_hold": bool(row["compliance_hold"]),
        }

    def _load_records(self, memory_class: str) -> List[Dict[str, Any]]:
        self._validate_memory_class(memory_class)
        rows = self.conn.execute(
            "SELECT * FROM memory_records WHERE memory_class = ? ORDER BY created_at ASC",
            (memory_class,),
        ).fetchall()
        return [self._row_to_record(row) for row in rows]

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

        accepted: List[str] = []

        with self._tx():
            for raw in records:
                if not isinstance(raw, dict):
                    raise ValueError("append records must be objects")

                built = self._build_record(memory_class, raw, provenance)
                if self._canonical_exists(memory_class, built["canonical_hash"]):
                    continue

                self.conn.execute(
                    """
                    INSERT INTO memory_records(
                        record_id,
                        memory_class,
                        canonical_hash,
                        content,
                        evidence_score,
                        tags_json,
                        created_at,
                        expires_on,
                        provenance_json,
                        tombstone,
                        compliance_hold
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0)
                    """,
                    (
                        built["record_id"],
                        built["memory_class"],
                        built["canonical_hash"],
                        built["content"],
                        built["evidence_score"],
                        json.dumps(built["tags"], ensure_ascii=True),
                        built["created_at"],
                        built["expires_on"],
                        json.dumps(built["provenance"], ensure_ascii=True),
                    ),
                )
                accepted.append(built["record_id"])

        return {
            "accepted_count": len(accepted),
            "record_ids": accepted,
        }

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

        filter_obj = filters or {}
        min_evidence = float(filter_obj.get("min_evidence_score", 0.0))
        required_tags_raw = filter_obj.get("required_tags", [])
        required_tags = set(str(tag) for tag in required_tags_raw) if isinstance(required_tags_raw, list) else set()

        placeholders = ", ".join("?" for _ in classes)
        today = date.today().isoformat()

        rows = self.conn.execute(
            f"""
            SELECT *
            FROM memory_records
            WHERE tombstone = 0
              AND memory_class IN ({placeholders})
              AND expires_on >= ?
            """,
            [*classes, today],
        ).fetchall()

        scored: List[Dict[str, Any]] = []
        tokens = text.split()

        for row in rows:
            rec = self._row_to_record(row)
            evidence = float(rec["evidence_score"])
            if evidence < min_evidence:
                continue

            tags = set(rec.get("tags", []))
            if required_tags and not required_tags.issubset(tags):
                continue

            content = str(rec.get("content", "")).lower()
            token_hits = sum(content.count(tok) for tok in tokens)
            if token_hits <= 0:
                continue

            score = float(token_hits) + evidence
            scored.append(
                {
                    "record_id": rec["record_id"],
                    "score": round(score, 4),
                    "evidence": {
                        "memory_class": rec["memory_class"],
                        "content": rec["content"],
                        "provenance": rec.get("provenance", {}),
                    },
                }
            )

        scored.sort(key=lambda item: item["score"], reverse=True)
        top = max(1, int(top_k))

        return {
            "results": scored[:top],
            "trace_id": self._sha256(f"{self._now_utc().isoformat()}:{query}")[:16],
            "filters": filter_obj,
        }

    def compact(self, memory_class: str, before_date: str, max_tokens: int) -> Dict[str, Any]:
        self._validate_memory_class(memory_class)

        try:
            cutoff = date.fromisoformat(before_date)
        except Exception as exc:
            raise ValueError(f"before_date must be YYYY-MM-DD ({exc})") from exc

        rows = self.conn.execute(
            """
            SELECT *
            FROM memory_records
            WHERE memory_class = ?
              AND tombstone = 0
              AND substr(created_at, 1, 10) <= ?
            ORDER BY created_at ASC
            """,
            (memory_class, cutoff.isoformat()),
        ).fetchall()

        eligible = [self._row_to_record(row) for row in rows]
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
            with self._tx():
                for rec in eligible:
                    self.conn.execute(
                        """
                        UPDATE memory_records
                        SET compacted_into = ?
                        WHERE record_id = ?
                          AND tombstone = 0
                        """,
                        (summary_id, rec["record_id"]),
                    )

        return {
            "compacted_count": len(eligible),
            "summary_ids": summary_ids,
        }

    def evict(self, memory_class: str, selector: str, reason_code: str) -> Dict[str, Any]:
        self._validate_memory_class(memory_class)
        selector_norm = selector.strip().lower()
        if selector_norm not in {"expired", "all"}:
            raise ValueError("selector must be one of: expired, all")
        if not reason_code.strip():
            raise ValueError("reason_code must be non-empty")

        today = date.today().isoformat()
        where = "memory_class = ? AND tombstone = 0"
        params: List[Any] = [memory_class]
        if selector_norm == "expired":
            where += " AND expires_on < ?"
            params.append(today)

        rows = self.conn.execute(
            f"SELECT record_id FROM memory_records WHERE {where}", params
        ).fetchall()
        target_ids = [str(row["record_id"]) for row in rows]

        if not target_ids:
            return {"evicted_count": 0, "tombstones": []}

        with self._tx():
            for record_id in target_ids:
                self.conn.execute(
                    """
                    UPDATE memory_records
                    SET tombstone = 1,
                        tombstone_reason = ?,
                        tombstoned_on = ?
                    WHERE record_id = ?
                    """,
                    (reason_code, today, record_id),
                )

        return {
            "evicted_count": len(target_ids),
            "tombstones": target_ids,
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
    parser = argparse.ArgumentParser(description="LDS memory backend adapter v2 (SQLite).")
    parser.add_argument(
        "--policy",
        default="contracts/memory/lds-memory-policy.json",
        help="Memory policy JSON path (relative to LDS root).",
    )
    parser.add_argument(
        "--db-path",
        default="reports/handoff/memory_store/lds_memory.sqlite3",
        help="SQLite database path for memory backend.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
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
    p_query.add_argument("--filters", default="{}", help="JSON object with optional filters")

    p_compact = sub.add_parser("compact", help="Compact old records")
    p_compact.add_argument("--memory-class", required=True)
    p_compact.add_argument("--before-date", required=True, help="YYYY-MM-DD")
    p_compact.add_argument("--max-tokens", type=int, default=256)

    p_evict = sub.add_parser("evict", help="Evict records")
    p_evict.add_argument("--memory-class", required=True)
    p_evict.add_argument("--selector", required=True, choices=["expired", "all"])
    p_evict.add_argument("--reason-code", required=True)

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s %(message)s",
    )

    adapter: MemoryBackendAdapterV2 | None = None
    try:
        adapter = MemoryBackendAdapterV2(ROOT / args.policy, ROOT / args.db_path)

        if args.cmd == "append":
            records = load_records_from_args(args.records_file, args.record)
            provenance = parse_json_value(args.provenance, "--provenance")
            out = adapter.append(args.memory_class, records, provenance)
        elif args.cmd == "query":
            classes = args.memory_class if args.memory_class else None
            filters = parse_json_value(args.filters, "--filters")
            out = adapter.query(args.query, classes, args.top_k, filters=filters)
        elif args.cmd == "compact":
            out = adapter.compact(args.memory_class, args.before_date, args.max_tokens)
        elif args.cmd == "evict":
            out = adapter.evict(args.memory_class, args.selector, args.reason_code)
        else:
            raise ValueError(f"unsupported command: {args.cmd}")
    except Exception as exc:
        LOG.exception("memory backend v2 command failed")
        print(json.dumps({"status": "fail", "error": str(exc)}, indent=2))
        return 1
    finally:
        if adapter is not None:
            adapter.close()

    print(json.dumps({"status": "pass", "result": out}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
