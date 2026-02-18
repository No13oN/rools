import importlib.util
import json
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CHECK_SCRIPT = ROOT / "scripts" / "check_branch_protection.py"
APPLY_SCRIPT = ROOT / "scripts" / "apply_branch_protection.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class BranchProtectionToolsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.check = load_module(CHECK_SCRIPT, "check_branch_protection")
        cls.apply = load_module(APPLY_SCRIPT, "apply_branch_protection")

    def test_validate_policy_accepts_current_policy(self):
        policy = json.loads((ROOT / ".github/branch-protection.json").read_text(encoding="utf-8"))
        errors = self.apply.validate_policy(policy)
        self.assertEqual(errors, [])

    def test_validate_policy_rejects_weak_policy(self):
        policy = json.loads((ROOT / ".github/branch-protection.json").read_text(encoding="utf-8"))
        policy["enforce_admins"] = False
        policy["allow_force_pushes"] = True
        policy["required_pull_request_reviews"]["required_approving_review_count"] = 0
        errors = self.apply.validate_policy(policy)
        self.assertTrue(any("enforce_admins" in err for err in errors))
        self.assertTrue(any("allow_force_pushes" in err for err in errors))
        self.assertTrue(any("required_approving_review_count" in err for err in errors))

    def test_read_enabled_supports_bool_and_dict(self):
        self.assertTrue(self.check.read_enabled(True))
        self.assertTrue(self.check.read_enabled({"enabled": True}))
        self.assertFalse(self.check.read_enabled({"enabled": False}))
        self.assertFalse(self.check.read_enabled(None))

    def test_write_report_creates_valid_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "branch_protection_report.json"
            self.check.write_report(
                target,
                "warn",
                "test summary",
                {"repo": "owner/repo", "branch": "main", "errors": ["x"]},
            )
            data = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(data["artifact_id"], "branch_protection_report")
            self.assertEqual(data["status"], "warn")
            self.assertEqual(data["repo"], "owner/repo")


if __name__ == "__main__":
    unittest.main()
