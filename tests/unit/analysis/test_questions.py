"""Question-analysis commands remain import-safe and preserve their classifiers."""

import subprocess
import sys
import unittest

from analysis.questions import classify_intent, normalize_time_marker_text
from tests.support import REPO_ROOT


class QuestionAnalysisTests(unittest.TestCase):
    def test_import_does_not_load_data_or_print(self):
        result = subprocess.run(
            [sys.executable, "-c", "import analysis.questions"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_classifier_handles_question_and_customer_groups_separately(self):
        self.assertEqual(classify_intent("Doanh thu nhóm hải sản tháng này"), "doanh_thu")
        self.assertEqual(classify_intent("Khách nào mua nhiều nhất"), "top_khach")

    def test_time_marker_normalization_preserves_legacy_mapping(self):
        self.assertEqual(normalize_time_marker_text("tuần trước"), "tuần truớc")


if __name__ == "__main__":
    unittest.main()
