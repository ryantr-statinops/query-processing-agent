"""Sql helpers for the inference contract. Source data and labels are never loaded on import."""

from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence
from ._shared import (
    GuardrailError,
    MAX_SQL_CHARS,
    _FORBIDDEN_KEYWORDS,
    _FROM_TERMINATORS,
    _IDENT_START,
    _OPERATORS,
    _UNSAFE_TABLE_FUNCTIONS,
)


@dataclass(frozen=True)
class SqlToken:
    kind: str
    value: str
    position: int
    line: int


def tokenize_sql(sql: str) -> list[SqlToken]:
    """Tokenise SQL without executing or normalising it.

    Comments are dropped. Single-quoted strings and double-quoted/backticked
    identifiers are opaque tokens, so keyword checks cannot be fooled by text
    inside them.
    """

    if not isinstance(sql, str):
        raise GuardrailError("sql_parse_error", "SQL must be a string", stage="validation")
    if len(sql) > MAX_SQL_CHARS:
        raise GuardrailError(
            "sql_parse_error",
            "SQL exceeds the maximum length",
            stage="validation",
            detail={"max_chars": MAX_SQL_CHARS},
        )

    tokens: list[SqlToken] = []
    index = 0
    line = 1
    length = len(sql)

    while index < length:
        char = sql[index]

        if char in " \t\r":
            index += 1
            continue
        if char == "\n":
            line += 1
            index += 1
            continue

        if char == "-" and index + 1 < length and sql[index + 1] == "-":
            index += 2
            while index < length and sql[index] != "\n":
                index += 1
            continue

        if char == "/" and index + 1 < length and sql[index + 1] == "*":
            start_line = line
            index += 2
            closed = False
            while index + 1 < length:
                if sql[index] == "*" and sql[index + 1] == "/":
                    index += 2
                    closed = True
                    break
                if sql[index] == "\n":
                    line += 1
                index += 1
            if not closed:
                raise GuardrailError(
                    "sql_parse_error",
                    "unterminated block comment",
                    stage="validation",
                    detail={"line": start_line},
                )
            continue

        if char == "'":
            start = index
            start_line = line
            index += 1
            value: list[str] = []
            closed = False
            while index < length:
                if sql[index] == "'":
                    if index + 1 < length and sql[index + 1] == "'":
                        value.append("'")
                        index += 2
                        continue
                    index += 1
                    closed = True
                    break
                if sql[index] == "\n":
                    line += 1
                value.append(sql[index])
                index += 1
            if not closed:
                raise GuardrailError(
                    "sql_parse_error",
                    "unterminated string literal",
                    stage="validation",
                    detail={"line": start_line},
                )
            tokens.append(SqlToken("string", "".join(value), start, start_line))
            continue

        if char in {'"', "`"}:
            quote = char
            start = index
            start_line = line
            index += 1
            value = []
            closed = False
            while index < length:
                if sql[index] == quote:
                    if quote == '"' and index + 1 < length and sql[index + 1] == '"':
                        value.append('"')
                        index += 2
                        continue
                    index += 1
                    closed = True
                    break
                if sql[index] == "\n":
                    line += 1
                value.append(sql[index])
                index += 1
            if not closed:
                raise GuardrailError(
                    "sql_parse_error",
                    "unterminated quoted identifier",
                    stage="validation",
                    detail={"line": start_line},
                )
            tokens.append(SqlToken("quoted_ident", "".join(value), start, start_line))
            continue

        if char == "$":
            if index + 1 < length and sql[index + 1].isdigit():
                start = index
                index += 1
                while index < length and sql[index].isdigit():
                    index += 1
                tokens.append(SqlToken("param", sql[start:index], start, line))
                continue
            raise GuardrailError(
                "sql_parse_error",
                "dollar-quoted strings and $ parameters are not supported",
                stage="validation",
                detail={"line": line},
            )

        if char == "?":
            tokens.append(SqlToken("param", "?", index, line))
            index += 1
            continue

        if char.isdigit() or (char == "." and index + 1 < length and sql[index + 1].isdigit()):
            start = index
            if char == ".":
                index += 1
                while index < length and sql[index].isdigit():
                    index += 1
            else:
                while index < length and sql[index].isdigit():
                    index += 1
                if index < length and sql[index] == ".":
                    index += 1
                    while index < length and sql[index].isdigit():
                        index += 1
            if index < length and sql[index] in "eE":
                probe = index + 1
                if probe < length and sql[probe] in "+-":
                    probe += 1
                if probe < length and sql[probe].isdigit():
                    index = probe
                    while index < length and sql[index].isdigit():
                        index += 1
            tokens.append(SqlToken("number", sql[start:index], start, line))
            continue

        if _IDENT_START.match(char):
            start = index
            while index < length and (sql[index] == "_" or sql[index].isalnum()):
                index += 1
            tokens.append(SqlToken("word", sql[start:index], start, line))
            continue

        operator = next((op for op in _OPERATORS if sql.startswith(op, index)), None)
        if operator:
            tokens.append(SqlToken("operator", operator, index, line))
            index += len(operator)
            continue

        if char in "(),;.[]{}":
            tokens.append(SqlToken("punct", char, index, line))
            index += 1
            continue

        if char in "+-*/%=<>!~&|^@#:":
            tokens.append(SqlToken("operator", char, index, line))
            index += 1
            continue

        raise GuardrailError(
            "sql_parse_error",
            f"unsupported character in SQL: {char!r}",
            stage="validation",
            detail={"line": line, "position": index},
        )

    return tokens


def _split_statements(tokens: Sequence[SqlToken]) -> list[list[SqlToken]]:
    statements: list[list[SqlToken]] = []
    current: list[SqlToken] = []
    for token in tokens:
        if token.kind == "punct" and token.value == ";":
            if current:
                statements.append(current)
                current = []
            continue
        current.append(token)
    if current:
        statements.append(current)
    return statements


def _paren_depths(tokens: Sequence[SqlToken]) -> list[int]:
    depths: list[int] = []
    depth = 0
    for token in tokens:
        depths.append(depth)
        if token.kind == "punct" and token.value == "(":
            depth += 1
        elif token.kind == "punct" and token.value == ")":
            depth = max(0, depth - 1)
    return depths


def _next_is_open_paren(tokens: Sequence[SqlToken], index: int) -> bool:
    return index + 1 < len(tokens) and tokens[index + 1].kind == "punct" and tokens[index + 1].value == "("


def _skip_parens(tokens: Sequence[SqlToken], index: int) -> int:
    if index >= len(tokens) or tokens[index].value != "(":
        raise GuardrailError("sql_parse_error", "expected '('", stage="validation")
    depth = 0
    while index < len(tokens):
        token = tokens[index]
        if token.kind == "punct" and token.value == "(":
            depth += 1
        elif token.kind == "punct" and token.value == ")":
            depth -= 1
            if depth == 0:
                return index + 1
        index += 1
    raise GuardrailError("sql_parse_error", "unbalanced parentheses", stage="validation")


def _collect_ctes(tokens: Sequence[SqlToken]) -> tuple[list[str], list[str]]:
    first_word = next(
        (index for index, token in enumerate(tokens) if token.kind == "word"),
        None,
    )
    if first_word is None or tokens[first_word].value.casefold() != "with":
        return [], []

    names: list[str] = []
    aliases: list[str] = []
    index = first_word + 1
    if index < len(tokens) and tokens[index].kind == "word" and tokens[index].value.casefold() == "recursive":
        index += 1

    while index < len(tokens):
        if tokens[index].kind not in ("word", "quoted_ident"):
            break
        name = tokens[index].value
        index += 1
        if index < len(tokens) and tokens[index].value == "(":
            close = _skip_parens(tokens, index)
            aliases.extend(
                token.value
                for token in tokens[index + 1 : close - 1]
                if token.kind in ("word", "quoted_ident")
            )
            index = close
        if index >= len(tokens) or tokens[index].value.casefold() != "as":
            raise GuardrailError(
                "sql_parse_error",
                "CTE is missing AS",
                stage="validation",
                detail={"cte": name},
            )
        index += 1
        while index < len(tokens) and tokens[index].kind == "word" and tokens[index].value.casefold() in {
            "materialized",
            "not",
        }:
            index += 1
        if index >= len(tokens) or tokens[index].value != "(":
            raise GuardrailError(
                "sql_parse_error",
                "CTE body must be parenthesised",
                stage="validation",
                detail={"cte": name},
            )
        index = _skip_parens(tokens, index)
        names.append(name.casefold())
        if index < len(tokens) and tokens[index].kind == "punct" and tokens[index].value == ",":
            index += 1
            continue
        break
    return names, aliases


def _collect_aliases(tokens: Sequence[SqlToken]) -> set[str]:
    aliases: set[str] = set()
    for index, token in enumerate(tokens[:-1]):
        if token.kind == "word" and token.value.casefold() == "as":
            following = tokens[index + 1]
            if following.kind in ("word", "quoted_ident"):
                aliases.add(following.value.casefold())
    return aliases


def _check_statement_form(tokens: Sequence[SqlToken]) -> None:
    index = 0
    while index < len(tokens) and tokens[index].kind == "punct" and tokens[index].value == "(":
        index += 1
    if index >= len(tokens):
        raise GuardrailError("sql_parse_error", "empty SQL statement", stage="validation")
    token = tokens[index]
    if token.kind != "word":
        raise GuardrailError(
            "sql_parse_error",
            "SQL must start with SELECT or WITH",
            stage="validation",
            detail={"token": token.value},
        )
    keyword = token.value.casefold()
    if keyword in {"select", "with"}:
        return
    if keyword in _FORBIDDEN_KEYWORDS:
        raise GuardrailError(
            "forbidden_statement",
            f"statement type is not allowed: {token.value}",
            stage="validation",
            detail={"keyword": token.value},
        )
    raise GuardrailError(
        "sql_parse_error",
        "SQL must start with SELECT or WITH",
        stage="validation",
        detail={"token": token.value},
    )


def _parse_table_ref(
    tokens: Sequence[SqlToken],
    index: int,
    ctes: set[str],
) -> tuple[str | None, int]:
    """Return a physical table name (or None for a CTE/subquery) and next index."""

    if index >= len(tokens):
        raise GuardrailError("sql_parse_error", "FROM/JOIN is missing a relation", stage="validation")

    token = tokens[index]
    if token.kind == "punct" and token.value == "(":
        return None, index

    if token.kind == "word" and token.value.casefold() == "lateral":
        raise GuardrailError(
            "forbidden_table_reference",
            "LATERAL table references are not allowed",
            stage="validation",
        )

    if token.kind not in ("word", "quoted_ident"):
        raise GuardrailError(
            "sql_parse_error",
            "expected a table name after FROM/JOIN",
            stage="validation",
            detail={"token": token.value},
        )

    name = token.value
    if _next_is_open_paren(tokens, index):
        raise GuardrailError(
            "forbidden_function",
            f"table-valued functions are not allowed: {name}",
            stage="validation",
            detail={"function": name},
        )

    if index + 1 < len(tokens) and tokens[index + 1].kind == "punct" and tokens[index + 1].value == ".":
        raise GuardrailError(
            "forbidden_table_reference",
            "schema-qualified table references are not allowed",
            stage="validation",
            detail={"table": name},
        )

    if name.casefold() in ctes:
        return None, index
    return name, index


def _scan_table_references(
    tokens: Sequence[SqlToken],
    depths: Sequence[int],
    ctes: set[str],
) -> list[str]:
    tables: list[str] = []
    in_from = False

    for index, token in enumerate(tokens):
        if token.kind == "word":
            keyword = token.value.casefold()
            if keyword == "from" and depths[index] == 0:
                table, _ = _parse_table_ref(tokens, index + 1, ctes)
                if table is not None:
                    tables.append(table)
                in_from = True
                continue
            if keyword == "join":
                table, _ = _parse_table_ref(tokens, index + 1, ctes)
                if table is not None:
                    tables.append(table)
                in_from = False
                continue
            if keyword in _FROM_TERMINATORS and depths[index] == 0:
                in_from = False
                continue
        elif token.kind == "punct" and token.value == "," and depths[index] == 0 and in_from:
            table, _ = _parse_table_ref(tokens, index + 1, ctes)
            if table is not None:
                tables.append(table)

    return tables


def _check_quoted_columns(
    tokens: Sequence[SqlToken],
    tables: Sequence[str],
    ctes: Sequence[str],
    aliases: set[str],
    allowed_columns: Iterable[str],
) -> None:
    allowed = {str(column).casefold() for column in allowed_columns}
    table_names = {table.casefold() for table in tables} | set(ctes)
    column_context_keywords = {
        "select",
        "where",
        "and",
        "or",
        "on",
        "by",
        "having",
        "group",
        "order",
        "distinct",
        "case",
        "when",
        "then",
        "else",
        "returning",
    }

    for index, token in enumerate(tokens):
        if token.kind != "quoted_ident":
            continue
        name = token.value.casefold()
        if name in table_names or name in aliases:
            continue
        previous = tokens[index - 1] if index else None
        following = tokens[index + 1] if index + 1 < len(tokens) else None
        if previous is not None and previous.kind == "word" and previous.value.casefold() == "as":
            continue
        if (
            previous is not None
            and previous.kind == "word"
            and previous.value.casefold() in {"from", "join"}
        ):
            continue
        if following is not None and following.kind == "punct" and following.value == ".":
            continue
        in_column_position = (
            previous is not None
            and (
                previous.kind == "operator"
                or (previous.kind == "punct" and previous.value in {"(", ",", "."})
                or (
                    previous.kind == "word"
                    and previous.value.casefold() in column_context_keywords
                )
            )
        )
        if not in_column_position:
            continue
        if name not in allowed:
            raise GuardrailError(
                "unknown_column",
                f"unknown column: {token.value}",
                stage="validation",
                detail={"column": token.value},
            )


def validate_sql_static(
    sql: str,
    allowed_tables: Iterable[str],
    allowed_columns: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Validate SQL structure without a database planner.

    This is a strong first gate, not a replacement for logical-plan validation:
    nested subquery relations and unquoted columns are resolved by
    :class:`SqlPlanProbe`.
    """

    tokens = tokenize_sql(sql)
    statements = _split_statements(tokens)
    if len(statements) != 1:
        raise GuardrailError(
            "multiple_statements",
            "exactly one SQL statement is allowed",
            stage="validation",
            detail={"statement_count": len(statements)},
        )
    tokens = statements[0]

    _check_statement_form(tokens)
    depths = _paren_depths(tokens)

    for index, token in enumerate(tokens):
        if token.kind == "param":
            raise GuardrailError(
                "forbidden_statement",
                "SQL parameters are not allowed",
                stage="validation",
            )
        if token.kind == "word":
            keyword = token.value.casefold()
            if keyword in _FORBIDDEN_KEYWORDS:
                raise GuardrailError(
                    "forbidden_statement",
                    f"keyword is not allowed in read-only SQL: {token.value}",
                    stage="validation",
                    detail={"keyword": token.value},
                )
            if keyword in _UNSAFE_TABLE_FUNCTIONS and _next_is_open_paren(tokens, index):
                raise GuardrailError(
                    "forbidden_function",
                    f"table-valued functions are not allowed: {token.value}",
                    stage="validation",
                    detail={"function": token.value},
                )

    ctes, cte_aliases = _collect_ctes(tokens)
    tables = _scan_table_references(tokens, depths, set(ctes))

    allowed = {str(table).casefold() for table in allowed_tables}
    for table in tables:
        if table.casefold() not in allowed:
            raise GuardrailError(
                "unknown_table",
                f"table is not in the verified allow-list: {table}",
                stage="validation",
                detail={"table": table},
            )

    aliases = _collect_aliases(tokens) | {alias.casefold() for alias in cte_aliases}
    if allowed_columns is not None:
        _check_quoted_columns(tokens, tables, ctes, aliases, allowed_columns)

    return {
        "ok": True,
        "statement_type": "select",
        "tables": list(dict.fromkeys(tables)),
        "ctes": list(dict.fromkeys(ctes)),
        "plan_checked": False,
        "columns_checked": allowed_columns is not None,
        "warnings": [],
    }


def _normalise_sql_type(type_name: Any) -> str:
    text = str(type_name or "VARCHAR").upper()
    if "TIMESTAMP" in text or "DATETIME" in text:
        return "TIMESTAMP"
    if "DATE" in text:
        return "DATE"
    if "BOOL" in text:
        return "BOOLEAN"
    if "INT" in text:
        return "BIGINT"
    if any(part in text for part in ("DOUBLE", "FLOAT", "REAL", "DECIMAL", "NUMERIC")):
        return "DOUBLE"
    return "VARCHAR"


def _normalise_schema(schema: Mapping[str, Any]) -> dict[str, dict[str, str]]:
    normalised: dict[str, dict[str, str]] = {}
    for table, spec in schema.items():
        raw_columns: Any = spec.get("columns", spec) if isinstance(spec, Mapping) else spec
        columns: dict[str, str] = {}
        if isinstance(raw_columns, Mapping):
            for column, meta in raw_columns.items():
                if isinstance(meta, Mapping):
                    type_name = meta.get("type") or meta.get("data_type") or "VARCHAR"
                else:
                    type_name = meta
                columns[str(column)] = _normalise_sql_type(type_name)
        elif isinstance(raw_columns, Sequence) and not isinstance(raw_columns, (str, bytes)):
            for column in raw_columns:
                columns[str(column)] = "VARCHAR"
        else:
            raise GuardrailError(
                "catalog_unavailable",
                "schema columns must be a mapping or a sequence",
                detail={"table": str(table)},
            )
        normalised[str(table)] = columns
    return normalised


def _quote_ident(name: str) -> str:
    return '"' + str(name).replace('"', '""') + '"'


def _collect_table_scans(plan: Any) -> list[str]:
    scans: list[str] = []

    def visit(node: Any, depth: int = 0) -> None:
        if depth > 100:  # defensive bound; logical plans are acyclic trees
            return
        try:
            text = node.display()
        except Exception:
            text = ""
        first_line = text.splitlines()[0] if text else ""
        if first_line.lstrip().startswith("TableScan:"):
            name = first_line.split("TableScan:", 1)[1].strip()
            for marker in (" projection=", " filters=", " fetch=", " order_by=", " limit="):
                name = name.split(marker, 1)[0].strip()
            name = name.strip('"`')
            scans.append(name)
        try:
            children = node.inputs()
        except Exception:
            children = []
        for child in children:
            visit(child, depth + 1)

    visit(plan)
    return scans


def _classify_datafusion_error(exc: Exception) -> GuardrailError:
    text = str(exc)
    lowered = text.casefold()

    if "single sql statement" in lowered:
        code = "multiple_statements"
    elif "dml not supported" in lowered or "ddl not supported" in lowered:
        code = "forbidden_statement"
    elif "table function" in lowered and "not found" in lowered:
        code = "forbidden_function"
    elif "table '" in lowered and "not found" in lowered:
        code = "unknown_table"
    elif "no field named" in lowered or ("column" in lowered and "not found" in lowered):
        code = "unknown_column"
    elif "parsererror" in lowered or "sql error" in lowered:
        code = "sql_parse_error"
    elif "not implemented" in lowered:
        code = "forbidden_statement"
    else:
        code = "sql_parse_error"

    detail: dict[str, Any] = {"planner_message": text[:500]}
    table_match = re.search(r"table '([^']+)' not found", text)
    if table_match:
        detail["table"] = table_match.group(1)
    field_match = re.search(r"No field named ([^.\s]+)", text)
    if field_match:
        detail["column"] = field_match.group(1).strip('"')

    return GuardrailError(code, text.splitlines()[0][:300], stage="validation", detail=detail)


class SqlPlanProbe:
    """Validate SQL through DataFusion's logical planner without collecting rows.

    Tables are registered as empty typed relations built from the verified
    catalog. Planning therefore resolves table and column names exactly as the
    read-only executor will, while no business data is read.
    """

    def __init__(self, schema: Mapping[str, Any]) -> None:
        self.schema = _normalise_schema(schema)
        self._datafusion: Any = None
        self._module_loaded = False
        self._context: Any = None
        self._signature: tuple[Any, ...] | None = None

    @property
    def available(self) -> bool:
        return self._load_datafusion() is not None

    def _load_datafusion(self) -> Any:
        if not self._module_loaded:
            self._module_loaded = True
            try:  # pragma: no cover - exercised when DataFusion is installed
                import datafusion

                self._datafusion = datafusion
            except Exception:
                self._datafusion = None
        return self._datafusion

    def _build_context(self) -> Any:
        module = self._load_datafusion()
        if module is None:
            raise GuardrailError(
                "catalog_unavailable",
                "DataFusion is not installed; logical-plan validation is unavailable",
                stage="validation",
            )
        signature = tuple(
            (table, tuple(sorted(columns.items()))) for table, columns in sorted(self.schema.items())
        )
        if self._context is not None and signature == self._signature:
            return self._context

        context = module.SessionContext()
        for table, columns in self.schema.items():
            if not columns:
                raise GuardrailError(
                    "catalog_unavailable",
                    "table has no columns in the verified schema",
                    detail={"table": table},
                )
            definitions = ", ".join(
                f"{_quote_ident(column)} {type_name}" for column, type_name in columns.items()
            )
            context.sql(f"CREATE TABLE IF NOT EXISTS {_quote_ident(table)} ({definitions})")
        self._context = context
        self._signature = signature
        return context

    def _options(self) -> Any:
        module = self._load_datafusion()
        options = module.SQLOptions()
        return (
            options.with_allow_ddl(False)
            .with_allow_dml(False)
            .with_allow_statements(False)
        )

    def validate(
        self,
        sql: str,
        allowed_tables: Iterable[str] | None = None,
        allowed_columns: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        allowed = list(allowed_tables) if allowed_tables is not None else list(self.schema)
        static = validate_sql_static(sql, allowed, allowed_columns)

        if not self.available:
            static["warnings"].append("datafusion_unavailable")
            return static

        context = self._build_context()
        try:
            frame = context.sql_with_options(sql, self._options())
        except Exception as exc:
            raise _classify_datafusion_error(exc) from exc

        try:
            plan = frame.logical_plan()
            scans = _collect_table_scans(plan)
        except Exception as exc:  # pragma: no cover - defensive planner boundary
            raise GuardrailError(
                "internal_error",
                f"could not inspect logical plan: {exc}",
                stage="validation",
            ) from exc

        if not scans:
            raise GuardrailError(
                "no_source_table",
                "query must read from a verified business table",
                stage="validation",
            )

        allowed_lookup = {str(table).casefold() for table in allowed}
        for scan in scans:
            if "(" in scan:
                raise GuardrailError(
                    "forbidden_function",
                    f"table-valued functions are not allowed: {scan}",
                    stage="validation",
                    detail={"function": scan},
                )
            if "." in scan:
                raise GuardrailError(
                    "forbidden_table_reference",
                    "schema-qualified table references are not allowed",
                    stage="validation",
                    detail={"table": scan},
                )
            if scan.casefold() not in allowed_lookup:
                raise GuardrailError(
                    "unknown_table",
                    f"table is not in the verified allow-list: {scan}",
                    stage="validation",
                    detail={"table": scan},
                )

        static.update(
            {
                "tables": list(dict.fromkeys(scans)),
                "plan_checked": True,
                "columns_checked": True,
            }
        )
        return static
