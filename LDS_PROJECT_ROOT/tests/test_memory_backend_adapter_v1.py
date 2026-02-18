import importlib.util
import tempfile
from datetime import date, timedelta
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "memory_backend_adapter_v1.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class MemoryBackendAdapterV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(SCRIPT, "memory_backend_adapter_v1")

    def make_adapter(self):
        tmp = tempfile.TemporaryDirectory()
        adapter = self.mod.MemoryBackendAdapterV1(
            ROOT / "contracts/memory/lds-memory-policy.json",
            Path(tmp.name),
        )
        return tmp, adapter

    def test_append_query_and_deduplicate(self):
        tmp, adapter = self.make_adapter()
        self.addCleanup(tmp.cleanup)

        first = adapter.append(
            "short_term",
            [{"content": "Order execution latency spike", "evidence_score": 0.9}],
            {"source": "unit-test", "trace_id": "t-1"},
        )
        self.assertEqual(first["accepted_count"], 1)

        second = adapter.append(
            "short_term",
            [{"content": "  order execution latency spike  ", "evidence_score": 0.8}],
            {"source": "unit-test", "trace_id": "t-2"},
        )
        self.assertEqual(second["accepted_count"], 0, "duplicate content must be deduplicated")

        query = adapter.query("execution latency", ["short_term"], top_k=3, filters={})
        self.assertGreaterEqual(len(query["results"]), 1)
        self.assertIn("latency", query["results"][0]["evidence"]["content"].lower())

    def test_evict_expired_records(self):
        tmp, adapter = self.make_adapter()
        self.addCleanup(tmp.cleanup)

        adapter.append(
            "short_term",
            [{"content": "Temporary signal", "evidence_score": 0.4}],
            {"source": "unit-test", "trace_id": "e-1"},
        )

        records = adapter._load_records("short_term")
        records[0]["expires_on"] = (date.today() - timedelta(days=1)).isoformat()
        adapter._write_records("short_term", records)

        evicted = adapter.evict("short_term", "expired", "ttl_expired")
        self.assertEqual(evicted["evicted_count"], 1)

        after = adapter._load_records("short_term")
        self.assertTrue(after[0]["tombstone"])
        self.assertEqual(after[0]["tombstone_reason"], "ttl_expired")

    def test_compact_old_records_creates_summary(self):
        tmp, adapter = self.make_adapter()
        self.addCleanup(tmp.cleanup)

        adapter.append(
            "episodic",
            [
                {"content": "Alpha strategy failed due to slippage", "evidence_score": 0.8},
                {"content": "Need stricter risk cap for overnight positions", "evidence_score": 0.7},
            ],
            {"source": "unit-test", "trace_id": "c-1"},
        )

        records = adapter._load_records("episodic")
        for rec in records:
            rec["created_at"] = "2020-01-10T10:00:00Z"
        adapter._write_records("episodic", records)

        compacted = adapter.compact("episodic", "2020-12-31", max_tokens=12)
        self.assertEqual(compacted["compacted_count"], 2)
        self.assertGreaterEqual(len(compacted["summary_ids"]), 1)

        after = adapter._load_records("episodic")
        self.assertTrue(any("compacted_into" in rec for rec in after))


if __name__ == "__main__":
    unittest.main()
