"""Offline vLLM planner adapter for generating candidate SQL queries."""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import time
from collections.abc import Mapping
from typing import Any

SYSTEM_PROMPT = (
    "You are a precise data assistant. Answer the question by proposing a read-only SQL query against the provided schema.\n"
    "You must respond ONLY with a single valid JSON object containing exactly:\n"
    "- \"sql\": A valid read-only SQL SELECT statement.\n"
    "- \"type\": The expected answer type, one of: [\"number\", \"percent\", \"string\", \"date\", \"boolean\", \"list\", \"table\", \"unanswerable\"].\n"
    "Important rules for DataFusion SQL:\n"
    "- Many columns in CSV/Excel are strings. For numeric aggregations or calculations (SUM, AVG, +, -, etc.), always use TRY_CAST(col AS DOUBLE) or CAST(col AS DOUBLE).\n"
    "- For scalar queries (number, percent, string, date, boolean), always return exactly 1 row and 1 column. Use COALESCE(..., 0) for aggregations so scalar queries never return NULL.\n"
    "- Avoid syntax errors, do not use multiple statements.\n"
    "Do not output explanation, markdown code fence, or text outside the JSON."
)

PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "sql": {"type": "string"},
        "type": {
            "type": "string",
            "enum": [
                "number",
                "percent",
                "string",
                "date",
                "boolean",
                "list",
                "table",
                "unanswerable",
            ],
        },
    },
    "required": ["sql", "type"],
}


def _resolve_tokenizer_path(model_path: str) -> str | None:
    env_path = os.environ.get("DATAMATE_TOKENIZER_PATH")
    if env_path and os.path.exists(env_path):
        return env_path
    p = pathlib.Path(model_path)
    model_dir = p.parent if p.is_file() else p
    candidates = [
        model_dir / "tokenizer",
        model_dir,
        pathlib.Path("/models/qwen3.5-9b-tokenizer"),
        pathlib.Path("models/qwen3.5-9b-tokenizer"),
    ]
    for cand in candidates:
        if cand.is_dir() and (
            (cand / "tokenizer.json").is_file() or (cand / "tokenizer_config.json").is_file()
        ):
            return str(cand)
    return env_path


class _HttpEngineOutput:
    def __init__(self, text: str) -> None:
        self.text = text


class _HttpEngineResult:
    def __init__(self, text: str) -> None:
        self.outputs = [_HttpEngineOutput(text)]


class _HttpEngine:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def generate(self, prompts: list[str], sampling_params: Any = None) -> list[_HttpEngineResult]:
        import json
        import os
        import urllib.request

        max_tokens = int(os.environ.get("DATAMATE_MAX_TOKENS", "160"))
        results: list[_HttpEngineResult] = []
        for prompt in prompts:
            payload = {
                "prompt": prompt,
                "n_predict": max_tokens,
                "temperature": 0.0,
                "stop": ["<|im_end|>", "<|endoftext|>", "\n}\n", "}\n"],
            }
            req = urllib.request.Request(
                f"{self.base_url}/completion",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    resp_payload = json.loads(resp.read().decode("utf-8"))
                    results.append(_HttpEngineResult(resp_payload.get("content", "")))
            except Exception:
                results.append(_HttpEngineResult("{}"))
        return results


class VllmPlanner:
    """Load an offline model once with vLLM and generate structured candidate plans."""

    def __init__(
        self,
        model_path: str | pathlib.Path,
        *,
        gpu_memory_utilization: float | None = None,
        max_model_len: int | None = None,
        tensor_parallel_size: int = 1,
        enforce_eager: bool | None = None,
    ) -> None:
        self.model_path = str(model_path)
        self.gpu_memory_utilization = (
            gpu_memory_utilization
            if gpu_memory_utilization is not None
            else float(os.environ.get("DATAMATE_GPU_MEMORY_UTILIZATION", "0.80"))
        )
        self.max_model_len = (
            max_model_len
            if max_model_len is not None
            else int(os.environ.get("DATAMATE_CONTEXT_SIZE", "4096"))
        )
        self.tensor_parallel_size = tensor_parallel_size
        self.enforce_eager = (
            enforce_eager
            if enforce_eager is not None
            else (os.environ.get("DATAMATE_ENFORCE_EAGER", "true").lower() in {"1", "true", "yes"})
        )
        self._llm = None
        self._sampling_params = None
        self._init_error: Exception | None = None
        self.model_load_ms: float | None = None

    def get_config_hash(self) -> str:
        """Return deterministic SHA-256 digest of prompt template and engine settings."""
        content = (
            f"v2:{self.model_path}:{self.gpu_memory_utilization}:{self.max_model_len}:"
            f"{self.enforce_eager}:{self.tensor_parallel_size}:{SYSTEM_PROMPT}"
        )
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]

    def _ensure_engine(self) -> Any:
        if self._llm is not None:
            return self._llm

        endpoint = os.environ.get("DATAMATE_INFERENCE_URL")
        if endpoint:
            self._llm = _HttpEngine(endpoint)
            return self._llm

        if self._init_error is not None:
            raise RuntimeError(
                f"vLLM engine initialization previously failed: {self._init_error}"
            ) from self._init_error

        try:
            from vllm import LLM, SamplingParams
        except ImportError as exc:
            self._init_error = exc
            raise RuntimeError(
                "vLLM is not installed. vLLM is an offline Linux dependency for model inference."
            ) from exc

        kwargs: dict[str, Any] = {
            "model": self.model_path,
            "gpu_memory_utilization": self.gpu_memory_utilization,
            "max_model_len": self.max_model_len,
            "tensor_parallel_size": self.tensor_parallel_size,
            "enforce_eager": self.enforce_eager,
        }
        if self.model_path.endswith(".gguf") or (
            os.path.isfile(self.model_path) and ".gguf" in self.model_path.lower()
        ):
            tokenizer_path = _resolve_tokenizer_path(self.model_path)
            if tokenizer_path and os.path.isdir(tokenizer_path):
                kwargs["tokenizer"] = tokenizer_path
            elif tokenizer_path:
                kwargs["tokenizer"] = tokenizer_path
            else:
                kwargs["tokenizer"] = "Qwen/Qwen3.5-9B"

        load_start = time.perf_counter()
        try:
            self._llm = LLM(**kwargs)
        except Exception as exc:
            err_str = str(exc).lower()
            if ("out of memory" in err_str or "cuda out of memory" in err_str) and self.gpu_memory_utilization > 0.70:
                kwargs["gpu_memory_utilization"] = max(0.70, round(self.gpu_memory_utilization - 0.08, 2))
                kwargs["enforce_eager"] = True
                try:
                    self._llm = LLM(**kwargs)
                except Exception as retry_exc:
                    self._init_error = retry_exc
                    raise retry_exc
            else:
                self._init_error = exc
                raise exc

        self.model_load_ms = round((time.perf_counter() - load_start) * 1000, 1)

        # Configure sampling parameters with structured JSON output if supported
        try:
            self._sampling_params = SamplingParams(
                temperature=0.0,
                max_tokens=512,
                stop=["```\n", "<|im_end|>", "\n\n\n"],
                guided_json=json.dumps(PLAN_SCHEMA),
            )
        except (TypeError, ValueError):
            self._sampling_params = SamplingParams(
                temperature=0.0,
                max_tokens=512,
                stop=["```\n", "<|im_end|>", "\n\n\n"],
            )
        return self._llm

    def warmup(self) -> float:
        """Pre-initialize model and run a warmup prompt outside timed evaluation loop."""
        start = time.perf_counter()
        llm = self._ensure_engine()
        if self.model_load_ms is None:
            self.model_load_ms = round((time.perf_counter() - start) * 1000, 1)
        try:
            warmup_prompt = (
                "<|im_start|>system\nYou are a precise data assistant.<|im_end|>\n"
                "<|im_start|>user\nPing<|im_end|>\n"
                "<|im_start|>assistant\n<think>\n\n</think>\n{\"sql\":\"SELECT 1\",\"type\":\"number\"}"
            )
            llm.generate([warmup_prompt], self._sampling_params)
        except Exception:
            pass
        return self.model_load_ms

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

        schema_limit = int(os.environ.get("DATAMATE_SCHEMA_LIMIT", "2200"))
        bounded_schema = schema[:schema_limit]
        rules_section = f"\nRelevant Rules:\n{rules[:1200]}\n" if rules else ""
        calendar_section = f"\nCalendar context:\n{calendar[:400]}\n" if calendar else ""

        # Qwen3.5 thinking is disabled by providing closing </think> in assistant header
        return (
            f"<|im_start|>system\n"
            f"{SYSTEM_PROMPT}\n"
            f"<|im_end|>\n"
            f"<|im_start|>user\n"
            f"Business: {business_id}\n"
            f"As-of date: {as_of_date}\n"
            f"Question: {question}\n\n"
            f"Schema:\n{bounded_schema}\n"
            f"{rules_section}"
            f"{calendar_section}"
            f"Candidate attempt: {index + 1}\n"
            f"Output JSON plan:\n"
            f"<|im_end|>\n"
            f"<|im_start|>assistant\n<think>\n\n</think>\n"
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
