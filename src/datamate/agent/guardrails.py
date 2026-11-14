"""Compatibility facade for the inference-contract guardrails.

Implementation lives in focused modules within datamate.agent. Existing callers
can keep importing this module; exported classes are the original class objects.
"""

from .requests import (
    find_reference_leakage,
    validate_no_reference_leakage,
    validate_request,
)
from .sql import (
    SqlPlanProbe,
    SqlToken,
    tokenize_sql,
    validate_sql_static,
)
from .budgets import (
    BudgetLedger,
    check_context_budget,
    estimate_tokens,
)
from .tools import (
    validate_tool_call,
)
from .entities import (
    normalise_text,
    resolve_entity,
)
from .answers import (
    build_diagnostic_record,
    build_submission_record,
    build_typed_answer,
    map_outcome,
    validate_internal_result,
    validate_typed_answer,
)
from .evidence import (
    verify_evidence,
)
from ._shared import (
    ANSWER_TYPES,
    CONCRETE_ANSWER_TYPES,
    CONTRACT_VERSION,
    EXECUTION_STATUSES,
    FORBIDDEN_REFERENCE_KEYS,
    GuardrailError,
    MAX_QUESTION_CHARS,
    MAX_RESULT_ROWS,
    MAX_SAMPLE_ROWS,
    MAX_SQL_CHARS,
    REASON_CODES,
    REASON_OUTCOMES,
    TOOL_ERROR_CODES,
    TOOL_NAMES,
    build_error,
)

__all__ = ['ANSWER_TYPES', 'BudgetLedger', 'CONCRETE_ANSWER_TYPES', 'CONTRACT_VERSION', 'EXECUTION_STATUSES', 'FORBIDDEN_REFERENCE_KEYS', 'GuardrailError', 'MAX_QUESTION_CHARS', 'MAX_RESULT_ROWS', 'MAX_SAMPLE_ROWS', 'MAX_SQL_CHARS', 'REASON_CODES', 'REASON_OUTCOMES', 'SqlPlanProbe', 'SqlToken', 'TOOL_ERROR_CODES', 'TOOL_NAMES', 'build_diagnostic_record', 'build_error', 'build_submission_record', 'build_typed_answer', 'check_context_budget', 'estimate_tokens', 'find_reference_leakage', 'map_outcome', 'normalise_text', 'resolve_entity', 'tokenize_sql', 'validate_internal_result', 'validate_no_reference_leakage', 'validate_request', 'validate_sql_static', 'validate_tool_call', 'validate_typed_answer', 'verify_evidence']
