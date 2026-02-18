import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "release_v1_baseline.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ReleaseV1BaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(SCRIPT, "release_v1_baseline")

    def test_collect_gate_snapshot_detects_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            reports_dir = Path(tmp)
            snapshot, errors = self.mod.collect_gate_snapshot(reports_dir, ["static_report"])
            self.assertEqual(snapshot["static_report.json"], "missing")
            self.assertTrue(any("missing required artifact" in err for err in errors))

    def test_cli_generates_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            freeze_path = Path(tmp) / "freeze_report.json"
            tag_path = Path(tmp) / "release_tag_report.json"

            proc = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(SCRIPT),
                    "--reports-dir",
                    "reports/release",
                    "--freeze-report",
                    str(freeze_path),
                    "--tag-report",
                    str(tag_path),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, msg=proc.stdout + proc.stderr)
            self.assertTrue(freeze_path.exists())
            self.assertTrue(tag_path.exists())

            freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
            tag = json.loads(tag_path.read_text(encoding="utf-8"))
            self.assertEqual(freeze["artifact_id"], "freeze_report")
            self.assertEqual(tag["artifact_id"], "release_tag_report")


if __name__ == "__main__":
    unittest.main()
