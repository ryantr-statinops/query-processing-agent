"""Offline vLLM planner adapter for generating candidate SQL queries."""

from __future__ import annotations

import os
import pathlib
from collections.abc import Mapping
from typing import Any


class VllmPlanner:
    """Load an offline model once with vLLM and generate structured candidate plans."""

    def __init__(
        self,
        model_path: str | pathlib.Path,
        *,
        gpu_memory_utilization: float | None = None,
        max_model_len: int | None = None,
        tensor_parallel_size: int = 1,
        enforce_eager: bool = False,
    ) -> None:
        self.model_path = str(model_path)
        self.gpu_memory_utilization = (
            gpu_memory_utilization
            if gpu_memory_utilization is not None
            else float(os.environ.get("DATAMATE_GPU_MEMORY_UTILIZATION", "0.85"))
        )
        self.max_model_len = (
            max_model_len
            if max_model_len is not None
            else int(os.environ.get("DATAMATE_CONTEXT_SIZE", "3072"))
        )
        self.tensor_parallel_size = tensor_parallel_size
        self.enforce_eager = enforce_eager
        self._llm = None
        self._sampling_params = None

    def _ensure_engine(self) -> Any:
        if self._llm is not None:
            return self._llm

        try:
            from vllm import LLM, SamplingParams
        except ImportError as exc:
            raise RuntimeError(
                "vLLM is not installed. vLLM is an offline Linux dependency for model inference."
            ) from exc

        kwargs: dict[str, Any] = {
            "model": self.model_path,
            "gpu_memory_utilization": self.gpu_memory_utilization,
            "max_model_len": self.max_model_len,
            "tensor_parallel_size": self.tensor_parallel_size,
            "enforce_eager": self.enforce_eager,
            "trust_remote_code": True,
        }
        if self.model_path.endswith(".gguf") or (
            os.path.isfile(self.model_path) and ".gguf" in self.model_path.lower()
        ):
            tokenizer_path = os.environ.get("DATAMATE_TOKENIZER_PATH") or os.path.dirname(self.model_path)
            if tokenizer_path and os.path.isdir(tokenizer_path):
                kwargs["tokenizer"] = tokenizer_path

        self._llm = LLM(**kwargs)
        self._sampling_params = SamplingParams(
            temperature=0.0,
            max_tokens=512,
            stop=["```\n", "\n\n\n"],
        )
        return self._llm

    def build_prompt(
        self,
        request: Mapping[str, Any],
        schema: str,
        index: int = 0,
        rules: str = "",
        calendar: str = "",
    ) -> str:
        question = request.get("question", "")
        as_of_date = request.get("as_of_date", "")
        business_id = request.get("business_id", "")

        rules_section = f"\nRelevant Rules:\n{rules[:1500]}\n" if rules else ""
        calendar_section = f"\nCalendar context:\n{calendar[:500]}\n" if calendar else ""

        return (
            f"<|im_start|>system\n"
            f"You are a precise data assistant. Answer the question by proposing a read-only SQL query against the provided schema.\n"
            f"You must respond ONLY with a valid JSON object containing:\n"
            f"- \"sql\": A valid read-only SQL SELECT statement.\n"
            f"- \"type\": The expected answer type, one of: [\"number\", \"percent\", \"string\", \"date\", \"boolean\", \"list\", \"table\", \"unanswerable\"].\n"
            f"Do not include explanation or text outside the JSON.\n"
            f"<|im_end|>\n"
            f"<|im_start|>user\n"
            f"Business: {business_id}\n"
            f"As-of date: {as_of_date}\n"
            f"Question: {question}\n\n"
            f"Schema:\n{schema}\n"
            f"{rules_section}"
            f"{calendar_section}"
            f"Candidate attempt: {index + 1}\n"
            f"Output JSON plan:\n"
            f"<|im_end|>\n"
            f"<|im_start|>assistant\n"
        )

    def generate_one(
        self,
        request: Mapping[str, Any],
        schema: str,
        index: int = 0,
        rules: str = "",
        calendar: str = "",
    ) -> str:
        llm = self._ensure_engine()
        prompt = self.build_prompt(request, schema, index, rules, calendar)
        outputs = llm.generate([prompt], self._sampling_params)
        if not outputs or not outputs[0].outputs:
            return "{}"
        return outputs[0].outputs[0].text
