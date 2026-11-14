"""Import boundaries exercised in a fresh interpreter without business data."""
import subprocess
import sys
import tempfile
import unittest


class PackageImportTests(unittest.TestCase):
    def test_catalog_imports_do_not_run_an_audit(self):
        code = """
from datamate.data.catalog_audit import build, review, validate
assert review.base is build
assert validate.review is review
"""
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, "-c", code], cwd=directory,
                capture_output=True, text=True,
            )
            from pathlib import Path
            self.assertEqual(list(Path(directory).iterdir()), [])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_guardrail_facade_preserves_identity_and_lazy_datafusion(self):
        code = """
import sys
from datamate.agent import guardrails, sql, tools, answers
from datamate.agent._shared import GuardrailError
assert guardrails.GuardrailError is GuardrailError
assert sql.GuardrailError is tools.GuardrailError is answers.GuardrailError
assert guardrails.SqlPlanProbe is sql.SqlPlanProbe
assert guardrails.validate_tool_call is tools.validate_tool_call
assert 'datafusion' not in sys.modules
"""
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, "-c", code], cwd=directory,
                capture_output=True, text=True,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_tracing_package_imports_do_not_run_audit(self):
        code = """
import sys
from datamate.evaluation.tracing import (
    INVENTORY_LOT_BALANCE_SQL, answers_match, validate_records,
)
assert 'sqlite3' not in sys.modules
assert answers_match('number', 3, 3)
assert 'WITH valid_receipts' in INVENTORY_LOT_BALANCE_SQL
assert callable(validate_records)
"""
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, "-c", code], cwd=directory,
                capture_output=True, text=True,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
