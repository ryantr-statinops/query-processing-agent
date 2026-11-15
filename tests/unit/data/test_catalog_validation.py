"""Catalog validation failures remain active under optimized Python."""

import subprocess
import sys
import unittest

from datamate.data.catalog_audit.validate import CatalogValidationError, require


class CatalogValidationTests(unittest.TestCase):
    def test_failed_invariant_has_a_specific_message(self):
        with self.assertRaisesRegex(CatalogValidationError, "sentinel"):
            require(False, "sentinel")

    def test_invariant_check_is_not_removed_by_optimization(self):
        result = subprocess.run(
            [
                sys.executable,
                "-O",
                "-c",
                "from datamate.data.catalog_audit.validate import require; require(False, 'sentinel')",
            ],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("sentinel", result.stderr)


if __name__ == "__main__":
    unittest.main()
