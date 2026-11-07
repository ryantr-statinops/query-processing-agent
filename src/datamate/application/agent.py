"""Question-level agent orchestration for DataMate inference."""

from __future__ import annotations

import os
import pathlib
from typing import Any

from datamate.application.candidates import CandidatePipeline
from datamate.data.catalog import BusinessCatalog
from datamate.generation.local_gguf import LocalSQLGenerator
from datamate.ranking.policy import CandidateBandit
from datamate.ranking.reranker import FeatureReranker


class DataMateAgent:
    def __init__(
        self,
        data_root: pathlib.Path,
        model_path: pathlib.Path | None,
        count: int,
        reranker: FeatureReranker | None,
        policy: CandidateBandit | None,
    ):
        self.data_root = data_root
        self.count = max(1, min(3, count))
        self.reranker = reranker
        self.policy = policy
        self.catalogs: dict[str, BusinessCatalog] = {}
        self.generator = None
        if model_path and model_path.is_file():
            self.generator = LocalSQLGenerator(
                model_path,
                context_size=int(os.environ.get("DATAMATE_CONTEXT_SIZE", "3072")),
                seed=int(os.environ.get("DATAMATE_SEED", "2026")),
            )
        self.candidate_pipeline = CandidatePipeline(data_root, self.generator, self.count)

    def _catalog(self, business_id: str) -> BusinessCatalog:
        if business_id not in self.catalogs:
            self.catalogs[business_id] = BusinessCatalog(self.data_root / "data" / business_id)
        return self.catalogs[business_id]

    def _candidates(self, question: dict[str, Any], catalog: BusinessCatalog) -> list[dict[str, Any]]:
        def stop_after_candidate(candidates: list[dict[str, Any]]) -> bool:
            ordered = self.reranker.rerank(candidates) if self.reranker else candidates
            action = self.policy.choose(ordered, can_generate_more=len(candidates) < self.count)
            return action != "generate_more"

        candidates = self.candidate_pipeline.generate(
            question,
            catalog,
            stop_after_candidate if self.policy else None,
        )
        return self.reranker.rerank(candidates) if self.reranker and candidates else candidates

    def answer(self, question: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        business_id = str(question.get("business_id", ""))
        trace: dict[str, Any] = {"code": [], "output": []}
        try:
            catalog = self._catalog(business_id)
            candidates = self._candidates(question, catalog)
            for item in candidates:
                trace["code"].append(item.get("sql", ""))
                result = dict(item.get("result", {}))
                rows = result.get("rows", []) or []
                result["row_count"] = len(rows)
                result["truncated_for_log"] = len(rows) > 20
                result["rows"] = rows[:20]
                trace["output"].append(result)
            selected = next((candidate for candidate in candidates if candidate.get("answer") is not None), None)
            if selected is None:
                answer = {"id": question["id"], "type": "abstain"}
            else:
                answer = {"id": question["id"], **selected["answer"]}
            trace["candidate_count"] = len(candidates)
            trace["selected_candidate"] = selected.get("index") if selected else None
            return answer, trace
        except Exception as error:
            trace["error"] = f"{type(error).__name__}: {error}"[:500]
            return {"id": question["id"], "type": "abstain"}, trace

    def close(self) -> None:
        for catalog in self.catalogs.values():
            catalog.close()
