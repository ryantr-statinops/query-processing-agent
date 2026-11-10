"""Composition root for supported offline, rule-based question handlers."""

from datetime import date
from pathlib import Path

from datamate.application.evidence import InsufficientEvidence
from datamate.application.periods import resolve_period
from datamate.application.plans import QuestionPlan, Unresolved
from datamate.application.purchases import answer_purchase_total
from datamate.application.retail_answers import (answer_order_count, answer_product_revenue,
                                                 answer_revenue, answer_revenue_by_group)
from datamate.application.routing import select_plan
from datamate.data.sources import SourceCatalog
from datamate.ranking.intents import IntentIndex

_DESCRIPTIONS = (
    ("purchase_total", "tổng tiền tổng giá trị số tiền các phiếu nhập hàng trong kỳ"),
    ("sales_count", "đếm số đơn hàng hóa đơn bán ra trong kỳ có bao nhiêu đơn"),
    ("sales_revenue", "doanh thu tiền bán tổng thành tiền các dòng hàng trong kỳ"),
    ("sales_product_revenue", "doanh thu tiền bán thành tiền của một sản phẩm mặt hàng trong kỳ"),
    ("sales_group_revenue", "doanh thu theo nhóm khách kênh bán hình thức thanh toán trong kỳ"),
)


def _purchase_plan(text: str, as_of: date) -> QuestionPlan | None:
    if not any(term in text for term in ("nhập hàng", "phiếu nhập", "nhập đầu kỳ")):
        return None
    if any(term in text for term in ("nhà cung cấp", "ncc", "xếp hạng", "nào nhiều nhất", "nhập nhiều nhất")):
        return None
    if not any(term in text for term in ("tổng", "bao nhiêu tiền", "hết bao nhiêu", "giá trị")):
        return None
    period = resolve_period(text, as_of)
    return QuestionPlan("purchase_total", "number", period) if period is not None else None


def _sales_count_plan(text: str, as_of: date) -> QuestionPlan | None:
    if any(term in text for term in ("nhập hàng", "phiếu nhập", "nhà cung cấp")):
        return None
    if not any(term in text for term in ("bao nhiêu đơn", "số đơn", "đếm đơn", "đếm số hóa đơn")):
        return None
    if any(term in text for term in ("hủy", "huỷ", "trả hàng", "tỷ lệ", "phần trăm")):
        return None
    if any(term in text for term in ("mặt hàng", "sản phẩm", "khách", "nhân viên", "theo ", "doanh thu",
                                     "ca ", "ca sáng", "ca chiều", "trở lên", "ít nhất", "nhiều hơn",
                                     "lớn hơn", "≥", ">", "so với", "chênh", "tăng", "giảm", "%")):
        return None
    period = resolve_period(text, as_of)
    return QuestionPlan("sales_count", "number", period) if period is not None else None


def _sales_revenue_plan(text: str, as_of: date) -> QuestionPlan | None:
    if not any(term in text for term in ("doanh thu", "tiền bán", "tổng tiền hàng")):
        return None
    if any(term in text for term in ("theo ", "so với", "từng tháng", "lần lượt", "tiền mặt", "chuyển khoản",
                                     "bình quân", "trung bình", "cao nhất", "thấp nhất", "tỷ lệ", "phần trăm",
                                     "tỉ lệ", "%", "chiếm", "mỗi loại", "liên tục", "chênh", "tăng", "giảm",
                                     "hơn hay kém", "nhóm", "khách", "mặt hàng", "sản phẩm", "món", "thuốc",
                                     "hoạt chất", "kê đơn", "không kê đơn", "tên hàng", "đơn bán", "các đơn",
                                     "cod", "ví điện tử", "quầy", "điện thoại", "trả bằng", "ca ", "nhân viên",
                                     "trở lên", "ít nhất", "nhiều hơn", "lớn hơn", "≥", ">")):
        return None
    if "của" in text and not any(term in text for term in ("của cửa hàng", "của shop")):
        return None
    if any(term in text for term in ("nhập hàng", "phiếu nhập")):
        return None
    period = resolve_period(text, as_of)
    return QuestionPlan("sales_revenue", "number", period) if period is not None else None


def _sales_product_revenue_plan(text: str, as_of: date) -> QuestionPlan | None:
    if not any(term in text for term in ("doanh thu", "tiền bán", "tổng tiền hàng")):
        return None
    if "của" not in text or any(term in text for term in ("của cửa hàng", "của shop")):
        return None
    if any(term in text for term in ("theo ", "so với", "tỷ lệ", "tỉ lệ", "phần trăm", "%", "chiếm",
                                     "nhóm", "khách", "tiền mặt", "chuyển khoản", "cod", "ví điện tử",
                                     "quầy", "điện thoại", "ca ", "nhân viên", "cao nhất", "thấp nhất")):
        return None
    if any(term in text for term in ("nhập hàng", "phiếu nhập")):
        return None
    period = resolve_period(text, as_of)
    return QuestionPlan("sales_product_revenue", "number", period) if period is not None else None


def _sales_group_revenue_plan(text: str, as_of: date) -> QuestionPlan | None:
    if not any(term in text for term in ("doanh thu", "tiền bán", "tổng tiền hàng")) or "theo " not in text:
        return None
    if any(term in text for term in ("so với", "từng tháng", "liên tục", "cao nhất", "thấp nhất", "nhập hàng")):
        return None
    if "nhóm khách" in text:
        group = "customer_group"
    elif any(term in text for term in ("hình thức thanh toán", "phương thức thanh toán")):
        group = "payment_method"
    elif any(term in text for term in ("kênh bán", "kênh")):
        group = "channel"
    else:
        return None
    period = resolve_period(text, as_of)
    return QuestionPlan("sales_group_revenue", "table", period, entity=group) if period is not None else None


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
            parsers = {"purchase_total": lambda normalized: _purchase_plan(normalized, as_of),
                       "sales_count": lambda normalized: _sales_count_plan(normalized, as_of),
                       "sales_revenue": lambda normalized: _sales_revenue_plan(normalized, as_of),
                       "sales_product_revenue": lambda normalized: _sales_product_revenue_plan(normalized, as_of),
                       "sales_group_revenue": lambda normalized: _sales_group_revenue_plan(normalized, as_of)}
            plan, match = select_plan(text, self.index, parsers)
            if isinstance(plan, Unresolved) or match is None or plan.period is None:
                return {"id": question_id, "type": "abstain"}, trace
            catalog = self._catalog(str(question.get("business_id", "")))
            if plan.intent == "purchase_total":
                result = answer_purchase_total(catalog, text, as_of)
            elif plan.intent == "sales_count":
                result = answer_order_count(catalog, plan.period)
            elif plan.intent == "sales_product_revenue":
                result = answer_product_revenue(catalog, text, plan.period)
            elif plan.intent == "sales_group_revenue":
                result = answer_revenue_by_group(catalog, plan.period, plan.entity)
            else:
                result = answer_revenue(catalog, plan.period)
            return {"id": question_id, **result}, trace
        except InsufficientEvidence as error:
            trace["error"] = f"{type(error).__name__}: {error}"[:500]
            return {"id": question_id, "type": "unanswerable", "reason": str(error)}, trace
        except (OSError, ValueError, TypeError, KeyError) as error:
            trace["error"] = f"{type(error).__name__}: {error}"[:500]
            return {"id": question_id, "type": "abstain"}, trace
