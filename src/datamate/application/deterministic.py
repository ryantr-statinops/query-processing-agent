"""Composition root for supported offline, rule-based question handlers."""

from datetime import date
from pathlib import Path

from datamate.application.evidence import InsufficientEvidence
from datamate.application.periods import resolve_period
from datamate.application.plans import QuestionPlan, Unresolved
from datamate.application.purchases import answer_purchase_total
from datamate.application.routing import select_plan
from datamate.data.sources import SourceCatalog
from datamate.ranking.intents import IntentIndex

_DESCRIPTIONS = (
    ("purchase_total", "tổng tiền tổng giá trị số tiền các phiếu nhập hàng trong kỳ"),
)


class DeterministicAgent:
    """Cache each business source catalog and abstain outside implemented rules."""

    def __init__(self, data_root: Path):
        self.data_root = data_root
        self.index = IntentIndex(_DESCRIPTIONS)
        self.catalogs: dict[str, SourceCatalog] = {}

    def _catalog(self, business_id: str) -> SourceCatalog:
        if not business_id or Path(business_id).name != business_id:
            raise ValueError("invalid_business_id")
        if business_id not in self.catalogs:
            directory = self.data_root / "data" / business_id
            if not directory.is_dir():
                raise FileNotFoundError("business_data_not_found")
            self.catalogs[business_id] = SourceCatalog(directory)
        return self.catalogs[business_id]

    def answer(self, question: dict) -> tuple[dict, dict]:
        question_id = question.get("id")
        if not isinstance(question_id, str):
            raise ValueError("question_id_required")
        trace = {"code": [], "output": [], "pipeline": "deterministic"}
        try:
            text = question.get("question")
            if not isinstance(text, str):
                raise ValueError("question_text_required")
            as_of = date.fromisoformat(question["as_of_date"])
            parsers = {"purchase_total": lambda normalized: (
                QuestionPlan("purchase_total", "number", period)
                if (period := resolve_period(normalized, as_of)) is not None else None
            )}
            plan, match = select_plan(text, self.index, parsers)
            if isinstance(plan, Unresolved) or match is None:
                return {"id": question_id, "type": "abstain"}, trace
            # The handler validates the period and required source columns before calculation.
            result = answer_purchase_total(self._catalog(str(question.get("business_id", ""))), text,
                                           as_of)
            return {"id": question_id, **result}, trace
        except InsufficientEvidence as error:
            trace["error"] = f"{type(error).__name__}: {error}"[:500]
            return {"id": question_id, "type": "unanswerable", "reason": str(error)}, trace
        except (OSError, ValueError, TypeError, KeyError) as error:
            trace["error"] = f"{type(error).__name__}: {error}"[:500]
            return {"id": question_id, "type": "abstain"}, trace
