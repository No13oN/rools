import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_lds.py"


def load_module():
    spec = importlib.util.spec_from_file_location("validate_lds", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class LdsValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module()
        dep_errors = cls.mod.dependency_check()
        cls.tiktoken_missing = any("tiktoken" in e for e in dep_errors)

    def _require_tiktoken(self):
        if self.tiktoken_missing:
            self.skipTest("tiktoken is not available in local environment")

    def test_dependency_contract_for_tiktoken(self):
        dep_errors = self.mod.dependency_check()
        if self.tiktoken_missing:
            self.assertTrue(any("tiktoken" in e for e in dep_errors))
        else:
            self.assertFalse(any("tiktoken" in e for e in dep_errors))

    def test_good_fixture_passes(self):
        self._require_tiktoken()
        schema = self.mod.load_json(ROOT / "contracts/schemas/lds-frontmatter.schema.json")
        required = schema.get("required", [])
        good = ROOT / "tests/fixtures/good/good_doc.md"
        errors = self.mod.validate_markdown_file(good, required)
        self.assertEqual(errors, [])

    def test_bad_fixture_missing_frontmatter_fails(self):
        self._require_tiktoken()
        schema = self.mod.load_json(ROOT / "contracts/schemas/lds-frontmatter.schema.json")
        required = schema.get("required", [])
        bad = ROOT / "tests/fixtures/bad/bad_missing_frontmatter.md"
        errors = self.mod.validate_markdown_file(bad, required)
        self.assertTrue(any("frontmatter missing" in e for e in errors))

    def test_bad_fixture_heading_skip_fails(self):
        self._require_tiktoken()
        schema = self.mod.load_json(ROOT / "contracts/schemas/lds-frontmatter.schema.json")
        required = schema.get("required", [])
        bad = ROOT / "tests/fixtures/bad/bad_heading_skip.md"
        errors = self.mod.validate_markdown_file(bad, required)
        self.assertTrue(any("heading skip detected" in e for e in errors))

    def test_bad_fixture_untagged_code_fails(self):
        self._require_tiktoken()
        schema = self.mod.load_json(ROOT / "contracts/schemas/lds-frontmatter.schema.json")
        required = schema.get("required", [])
        bad = ROOT / "tests/fixtures/bad/bad_untagged_code.md"
        errors = self.mod.validate_markdown_file(bad, required)
        self.assertTrue(any("missing language tag" in e for e in errors))

    def test_bad_fixture_empty_alt_fails(self):
        self._require_tiktoken()
        schema = self.mod.load_json(ROOT / "contracts/schemas/lds-frontmatter.schema.json")
        required = schema.get("required", [])
        bad = ROOT / "tests/fixtures/bad/bad_empty_alt.md"
        errors = self.mod.validate_markdown_file(bad, required)
        self.assertTrue(any("empty alt text" in e for e in errors))

    def test_anti_drift_passes(self):
        errors = self.mod.validate_drift()
        self.assertEqual(errors, [])

    def test_governance_contracts_pass(self):
        errors = self.mod.validate_governance_contracts()
        self.assertEqual(errors, [])

    def test_runtime_contracts_pass(self):
        errors = self.mod.validate_runtime_contracts()
        self.assertEqual(errors, [])

    def test_contract_manifest_pass(self):
        errors = self.mod.validate_contract_manifest()
        self.assertEqual(errors, [])

    def test_protected_manifest_pass(self):
        errors = self.mod.validate_protected_manifest()
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
