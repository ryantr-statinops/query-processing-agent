"""Local GGUF generator adapter backed by the Rust-native mistral.rs engine."""

from __future__ import annotations

import json
import os
import pathlib
import re
from typing import Any


TEMPERATURES = (0.0, 0.0, 0.0)


class LocalSQLGenerator:
    def __init__(self, model_path: pathlib.Path, context_size: int = 3072, seed: int = 2026):
        model_path = model_path.resolve()
        if not model_path.is_file():
            raise FileNotFoundError(f"Local GGUF model not found: {model_path}")
        try:
            from mistralrs import Runner, Which
        except ImportError as error:
            raise RuntimeError("Install the uv project dependencies to load mistralrs") from error

        self.model_path = model_path
        self.seed = seed
        self.context_size = max(1024, min(context_size, 8192))
        runner_options: dict[str, Any] = {
            "which": Which.GGUF(
                quantized_model_id=str(model_path.parent),
                quantized_filename=model_path.name,
                tok_model_id=str(model_path.parent / "mistralrs_runtime"),
            ),
            "max_seqs": 1,
            "prefix_cache_n": 0,
        }
        runtime_seed = os.environ.get("DATAMATE_RUNTIME_SEED")
        if runtime_seed:
            runner_options["seed"] = int(runtime_seed)
        memory_goal = os.environ.get("DATAMATE_MEMORY_GOAL", "").strip()
        if memory_goal and memory_goal.lower() != "none":
            runner_options.update(memory_goal=memory_goal, paged_attn=True)
        self.runner = Runner(**runner_options)

    def generate_one(
        self,
        question: dict[str, Any],
        schema: str,
        index: int,
        rules: str = "",
        calendar: str = "",
    ) -> dict[str, Any]:
        from mistralrs import ChatCompletionRequest

        index = max(0, min(index, len(TEMPERATURES) - 1))
        system = (
            "Translate the Vietnamese business-data question into one read-only Apache DataFusion SQL SELECT query. "
            "Use only the supplied schema. Never write or modify data. Return JSON only with keys sql and type. "
            "type must be number, percent, string, date, boolean, list, table, or unanswerable. "
            "Use as_of_date, calendar, and business rules when relevant. Do not invent columns."
        )
        strategies = (
            "Start from the simplest direct aggregation that matches the requested measure.",
            "Independently check row granularity, join duplication, and whether distinct entities are needed.",
            "Independently check date boundaries, filters, units, and whether the requested result is ranked or tabular.",
        )
        lead = (
            f"QUESTION: {question.get('question', '')}\nAS_OF_DATE: {question.get('as_of_date', '')}\n"
            f"BUSINESS_ID: {question.get('business_id', '')}\nCANDIDATE APPROACH: {strategies[index]}\n"
        )
        rules_context = f"\nBUSINESS RULES:\n{rules[:2500]}\n"
        calendar_context = f"CALENDAR REFERENCE:\n{calendar[:900]}\n"
        ending = (
            "Return one JSON object. For a table, SQL should return the requested columns. "
            "If the available tables cannot answer the question, return type=unanswerable and sql empty."
        )
        schema_text = schema
        rules_text = rules_context
        calendar_text = calendar_context

        def make_user() -> str:
            return lead + "SCHEMA AND SAMPLE VALUES:\n" + schema_text + "\n" + rules_text + calendar_text + ending

        # Reserve room for the answer tokens and chat template. Tokenize through the loaded Rust engine,
        # then trim lower-priority context while retaining the question and output contract.
        prompt_budget = max(256, self.context_size - 384 - 96)
        tokenizer = getattr(self.runner, "tokenize_text", None)
        if tokenizer is not None:
            while len(tokenizer(system + "\n" + make_user(), add_special_tokens=True, enable_thinking=False)) > prompt_budget:
                if len(schema_text) > 700:
                    schema_text = schema_text[: int(len(schema_text) * 0.8)]
                elif len(rules_text) > 160:
                    rules_text = rules_text[: int(len(rules_text) * 0.8)]
                elif len(calendar_text) > 100:
                    calendar_text = calendar_text[: int(len(calendar_text) * 0.8)]
                else:
                    break
        else:
            schema_text = schema_text[: self.context_size * 2]
        user = make_user()
        response = self.runner.send_chat_completion_request(
            ChatCompletionRequest(
                model="default",
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                temperature=TEMPERATURES[index],
                max_tokens=384,
                reasoning_effort="off",
                truncate_sequence=True,
            )
        )
        message = response.choices[0].message
        content = message.content or ""
        parsed = parse_candidate_json(content)
        return {
            "index": index,
            "raw": content,
            "sql": str(parsed.get("sql", "")),
            "type": str(parsed.get("type", "")).lower(),
            "thinking": getattr(message, "reasoning_content", None),
        }


def parse_candidate_json(text: str) -> dict[str, Any]:
    cleaned = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", text.strip(), flags=re.I)
    try:
        value = json.loads(cleaned)
        return value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.S)
        if not match:
            return {}
        try:
            value = json.loads(match.group(0))
            return value if isinstance(value, dict) else {}
        except json.JSONDecodeError:
            return {}
