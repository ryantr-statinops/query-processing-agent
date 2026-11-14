"""Import boundaries exercised in a fresh interpreter without business data."""
import subprocess
import sys
import tempfile
import unittest


class PackageImportTests(unittest.TestCase):
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
