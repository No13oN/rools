import importlib.util
import tempfile
from datetime import date, timedelta
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "memory_backend_adapter_v2.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class MemoryBackendAdapterV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(SCRIPT, "memory_backend_adapter_v2")

    def make_adapter(self):
        tmp = tempfile.TemporaryDirectory()
        db_path = Path(tmp.name) / "lds_memory.sqlite3"
        adapter = self.mod.MemoryBackendAdapterV2(
            ROOT / "contracts/memory/lds-memory-policy.json",
            db_path,
        )
        return tmp, adapter, db_path

    def test_append_query_deduplicate_and_persist(self):
        tmp, adapter, db_path = self.make_adapter()
        self.addCleanup(tmp.cleanup)

        first = adapter.append(
            "short_term",
            [{"content": "Order execution latency spike", "evidence_score": 0.9}],
            {"source": "unit-test", "trace_id": "v2-t1"},
        )
        self.assertEqual(first["accepted_count"], 1)
        adapter.close()

        adapter2 = self.mod.MemoryBackendAdapterV2(
            ROOT / "contracts/memory/lds-memory-policy.json",
            db_path,
        )
        self.addCleanup(adapter2.close)

        second = adapter2.append(
            "short_term",
            [{"content": "  order execution latency spike  ", "evidence_score": 0.8}],
            {"source": "unit-test", "trace_id": "v2-t2"},
        )
        self.assertEqual(second["accepted_count"], 0, "duplicate content must be deduplicated")

        query = adapter2.query("execution latency", ["short_term"], top_k=3, filters={})
        self.assertGreaterEqual(len(query["results"]), 1)
        self.assertIn("latency", query["results"][0]["evidence"]["content"].lower())

    def test_evict_expired_records(self):
        tmp, adapter, _ = self.make_adapter()
        self.addCleanup(tmp.cleanup)
        self.addCleanup(adapter.close)

        inserted = adapter.append(
            "short_term",
            [{"content": "Temporary signal", "evidence_score": 0.4}],
            {"source": "unit-test", "trace_id": "v2-e1"},
        )
        self.assertEqual(inserted["accepted_count"], 1)

        record_id = inserted["record_ids"][0]
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        adapter.conn.execute(
            "UPDATE memory_records SET expires_on = ? WHERE record_id = ?",
            (yesterday, record_id),
        )
        adapter.conn.commit()

        evicted = adapter.evict("short_term", "expired", "ttl_expired")
        self.assertEqual(evicted["evicted_count"], 1)

        rows = adapter._load_records("short_term")
        self.assertTrue(rows[0]["tombstone"])
        self.assertEqual(rows[0]["tombstone_reason"], "ttl_expired")

    def test_compact_old_records_creates_summary(self):
        tmp, adapter, _ = self.make_adapter()
        self.addCleanup(tmp.cleanup)
        self.addCleanup(adapter.close)

        adapter.append(
            "episodic",
            [
                {"content": "Alpha strategy failed due to slippage", "evidence_score": 0.8},
                {"content": "Need stricter risk cap for overnight positions", "evidence_score": 0.7},
            ],
            {"source": "unit-test", "trace_id": "v2-c1"},
        )

        adapter.conn.execute(
            "UPDATE memory_records SET created_at = '2020-01-10T10:00:00Z' WHERE memory_class = 'episodic'"
        )
        adapter.conn.commit()

        compacted = adapter.compact("episodic", "2020-12-31", max_tokens=12)
        self.assertEqual(compacted["compacted_count"], 2)
        self.assertGreaterEqual(len(compacted["summary_ids"]), 1)

        rows = adapter._load_records("episodic")
        self.assertTrue(any(rec.get("compacted_into") for rec in rows))


if __name__ == "__main__":
    unittest.main()
