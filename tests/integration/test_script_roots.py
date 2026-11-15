"""Tracing commands resolve repository inputs independently of the CWD."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts import trace_full_dataset, verify_phase_criteria
from tests.support import REPO_ROOT


class ScriptRootTests(unittest.TestCase):
    def test_tracing_scripts_anchor_paths_at_repository_root(self):
        self.assertEqual(trace_full_dataset.ROOT, REPO_ROOT)
        self.assertEqual(verify_phase_criteria.ROOT, REPO_ROOT)

    def test_physical_source_resolution_works_outside_repository(self):
        expected = REPO_ROOT / "configs" / "representative_questions.json"
        with tempfile.TemporaryDirectory() as directory:
            original = Path.cwd()
            try:
                os.chdir(directory)
                resolved = Path(
                    verify_phase_criteria.resolve_physical_source(
                        "configs/representative_questions.json"
                    )
                )
            finally:
                os.chdir(original)
        self.assertEqual(resolved, expected)
        self.assertTrue(resolved.is_file())

    def test_generator_validation_survives_optimized_python(self):
        result = subprocess.run(
            [
                sys.executable,
                "-O",
                "-c",
                "from scripts.trace_full_dataset import require; require(False, 'sentinel')",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("sentinel", result.stderr)


if __name__ == "__main__":
    unittest.main()
