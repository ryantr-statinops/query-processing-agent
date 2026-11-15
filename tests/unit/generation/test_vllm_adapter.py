"""Unit tests for offline vLLM planner adapter."""

from __future__ import annotations

import pathlib
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from datamate.application.candidates import CandidatePipeline
from datamate.data.catalog import BusinessCatalog
from datamate.generation.local_gguf import parse_candidate_json
from datamate.generation.vllm_adapter import VllmPlanner


class VllmPlannerTests(unittest.TestCase):
    def test_vllm_planner_lazy_instantiation_does_not_require_vllm(self):
        planner = VllmPlanner("models/dummy_model.gguf")
        self.assertEqual(planner.model_path, "models/dummy_model.gguf")
        self.assertIsNone(planner._llm)

    def test_vllm_planner_build_prompt_structure(self):
        planner = VllmPlanner("models/dummy_model.gguf")
        prompt = planner.build_prompt(
            request={
                "id": "q_001",
                "business_id": "biz_101",
                "question": "Tháng trước bán được bao nhiêu ly?",
                "as_of_date": "2026-03-04",
            },
            schema="CREATE TABLE sales (item TEXT, qty INT);",
            index=0,
            rules="Rule 1: Revenue excludes cancelled orders.",
            calendar="2026-03-04,Wed",
        )
        self.assertIn("Tháng trước bán được bao nhiêu ly?", prompt)
        self.assertIn("2026-03-04", prompt)
        self.assertIn("biz_101", prompt)
        self.assertIn("CREATE TABLE sales", prompt)
        self.assertIn("Rule 1:", prompt)
        self.assertIn("Candidate attempt: 1", prompt)
        self.assertIn('"sql": A valid read-only SQL SELECT statement.', prompt)

    def test_vllm_planner_ensure_engine_fails_gracefully_without_vllm(self):
        planner = VllmPlanner("models/dummy_model.gguf")
        with patch.dict("sys.modules", {"vllm": None}):
            with self.assertRaises(RuntimeError) as caught:
                planner._ensure_engine()
            self.assertIn("vLLM is not installed", str(caught.exception))

    def test_vllm_planner_generates_and_parses_with_mock_engine(self):
        planner = VllmPlanner("models/dummy_model.gguf")

        mock_llm = MagicMock()
        mock_output = MagicMock()
        mock_output.outputs = [MagicMock(text='{"sql": "SELECT SUM(total) AS value FROM orders", "type": "number"}')]
        mock_llm.generate.return_value = [mock_output]

        planner._llm = mock_llm
        planner._sampling_params = MagicMock()

        raw = planner.generate_one(
            request={"question": "Tổng tiền", "business_id": "biz_test", "as_of_date": "2026-01-01"},
            schema="CREATE TABLE orders (total INT);",
        )
        parsed = parse_candidate_json(raw)
        self.assertEqual(parsed["type"], "number")
        self.assertEqual(parsed["sql"], "SELECT SUM(total) AS value FROM orders")

    def test_vllm_planner_integrates_with_candidate_pipeline(self):
        planner = VllmPlanner("models/dummy_model.gguf")

        mock_llm = MagicMock()
        mock_output = MagicMock()
        mock_output.outputs = [MagicMock(text='{"sql": "SELECT SUM(amount) AS value FROM sales", "type": "number"}')]
        mock_llm.generate.return_value = [mock_output]

        planner._llm = mock_llm
        planner._sampling_params = MagicMock()

        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            biz_dir = root / "data" / "biz_001"
            biz_dir.mkdir(parents=True)
            (biz_dir / "sales.csv").write_text("amount\n10\n15\n", encoding="utf-8")
            catalog = BusinessCatalog(biz_dir)

            pipeline = CandidatePipeline(root, planner, count=1)
            candidates = pipeline.generate(
                {
                    "id": "q_test",
                    "business_id": "biz_001",
                    "question": "Tính tổng doanh số",
                    "as_of_date": "2026-01-01",
                },
                catalog=catalog,
            )
            self.assertEqual(len(candidates), 1)
            self.assertTrue(candidates[0]["result"].ok)
            self.assertEqual(candidates[0]["answer"], {"type": "number", "answer": 25})
