import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SEMANTIC_SCRIPT = ROOT / "scripts" / "eval_semantic_gate.py"
ARTIFACT_SCRIPT = ROOT / "scripts" / "validate_release_artifacts.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ReleaseGateToolsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.semantic = load_module(SEMANTIC_SCRIPT, "eval_semantic_gate")
        cls.artifacts = load_module(ARTIFACT_SCRIPT, "validate_release_artifacts")

    def test_semantic_gate_passes_with_current_scorecard(self):
        scorecard = self.semantic.load_json(ROOT / "reports/release/semantic_scorecard.json")
        thresholds = self.semantic.load_json(ROOT / "contracts/evaluation/lds-eval-thresholds.json")
        gate = self.semantic.load_json(ROOT / "contracts/rules/lds-publish-gate.json")
        errors = self.semantic.validate_semantic_gate(scorecard, thresholds, gate)
        self.assertEqual(errors, [])

    def test_release_artifacts_exist_and_valid(self):
        gate = self.artifacts.load_json(ROOT / "contracts/rules/lds-publish-gate.json")
        required = gate.get("required_artifacts", [])
        for artifact_name in required:
            path = ROOT / "reports/release" / f"{artifact_name}.json"
            errors = self.artifacts.validate_artifact_file(path, artifact_name)
            self.assertEqual(errors, [], msg=f"Artifact {artifact_name} failed: {errors}")


if __name__ == "__main__":
    unittest.main()
