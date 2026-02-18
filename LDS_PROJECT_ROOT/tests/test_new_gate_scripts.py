import json
import shutil
import subprocess
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class NewGateScriptsTests(unittest.TestCase):
    def run_cmd(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_offline_tokenizer_gate_strict_passes(self):
        proc = self.run_cmd("scripts/validate_tokenizer_offline.py", "--strict")
        self.assertEqual(proc.returncode, 0, msg=proc.stdout + proc.stderr)

    def test_handoff_acceptance_gate_strict_passes(self):
        proc = self.run_cmd("scripts/eval_handoff_acceptance.py", "--strict")
        self.assertEqual(proc.returncode, 0, msg=proc.stdout + proc.stderr)

    def test_policy_gate_non_strict_writes_report(self):
        build = self.run_cmd("scripts/build_policy_input.py")
        self.assertEqual(build.returncode, 0, msg=build.stdout + build.stderr)

        proc = self.run_cmd("scripts/eval_policy_gate.py")
        self.assertEqual(proc.returncode, 0, msg=proc.stdout + proc.stderr)

        report_path = ROOT / "reports/release/policy_report.json"
        self.assertTrue(report_path.exists(), msg="policy_report.json missing")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertIn(report.get("status"), {"pass", "warn"})

    def test_policy_gate_strict_passes_when_opa_installed(self):
        if shutil.which("opa") is None:
            self.skipTest("opa binary is not available")

        build = self.run_cmd("scripts/build_policy_input.py")
        self.assertEqual(build.returncode, 0, msg=build.stdout + build.stderr)

        proc = self.run_cmd("scripts/eval_policy_gate.py", "--strict")
        self.assertEqual(proc.returncode, 0, msg=proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
