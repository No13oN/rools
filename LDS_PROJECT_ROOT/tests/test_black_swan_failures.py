import copy
import importlib.util
import json
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOKENIZER_SCRIPT = ROOT / "scripts" / "validate_tokenizer_offline.py"
SEMANTIC_SCRIPT = ROOT / "scripts" / "eval_semantic_gate.py"
ARTIFACT_SCRIPT = ROOT / "scripts" / "validate_release_artifacts.py"
POLICY_SCRIPT = ROOT / "scripts" / "eval_policy_gate.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class BlackSwanFailureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tokenizer = load_module(TOKENIZER_SCRIPT, "validate_tokenizer_offline")
        cls.semantic = load_module(SEMANTIC_SCRIPT, "eval_semantic_gate")
        cls.artifacts = load_module(ARTIFACT_SCRIPT, "validate_release_artifacts")
        cls.policy = load_module(POLICY_SCRIPT, "eval_policy_gate")

    def test_black_swan_tokenizer_hash_corruption_detected(self):
        contract = self.tokenizer.load_json(ROOT / "contracts/token/lds-tokenizer-mirror.json")
        corrupted = copy.deepcopy(contract)
        corrupted["encodings"][0]["expected_sha256"] = "0" * 64
        errors = self.tokenizer.validate_mirror_files(corrupted)
        self.assertTrue(any("cache hash mismatch" in err for err in errors), msg=str(errors))

    def test_black_swan_semantic_critical_hallucination_blocks_release(self):
        scorecard = self.semantic.load_json(ROOT / "reports/release/semantic_scorecard.json")
        thresholds = self.semantic.load_json(ROOT / "contracts/evaluation/lds-eval-thresholds.json")
        gate = self.semantic.load_json(ROOT / "contracts/rules/lds-publish-gate.json")

        broken = copy.deepcopy(scorecard)
        broken["weighted_score"] = 70
        broken["critical_hallucination"]["factual"] = True

        errors = self.semantic.validate_semantic_gate(broken, thresholds, gate)
        self.assertTrue(any("weighted_score below threshold" in err for err in errors), msg=str(errors))
        self.assertTrue(any("critical hallucination" in err for err in errors), msg=str(errors))

    def test_black_swan_missing_release_artifact_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing_path = Path(tmp) / "not-existing.json"
            errors = self.artifacts.validate_artifact_file(missing_path, "static_report")
            self.assertTrue(any("missing artifact file" in err for err in errors), msg=str(errors))

    def test_black_swan_policy_deny_parse_detected(self):
        sample = {
            "result": [
                {
                    "expressions": [
                        {"value": ["deny: stale waiver", "deny: missing governance field"]}
                    ]
                }
            ]
        }
        denies = self.policy.parse_opa_deny(json.dumps(sample))
        self.assertEqual(len(denies), 2)
        self.assertIn("deny: stale waiver", denies)
        self.assertIn("deny: missing governance field", denies)


if __name__ == "__main__":
    unittest.main()
