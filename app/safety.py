import re
from dataclasses import dataclass

from app.catalog import ALLOWED_COLUMNS, ALLOWED_TABLES


class SQLSafetyError(ValueError):
    """Raised when a generated query violates the read-only SQL policy."""


@dataclass(frozen=True)
class ValidatedSQL:
    sql: str
    tables: tuple[str, ...]
    validator: str


FORBIDDEN_FUNCTIONS = {
    "load_extension", "readfile", "writefile", "fts3_tokenizer", "eval",
}
FORBIDDEN_TOKENS = re.compile(
    r"\b(insert|update|delete|replace|create|alter|drop|attach|detach|pragma|vacuum|"
    r"reindex|analyze|grant|revoke|truncate|call|execute|begin|commit|rollback)\b",
    re.IGNORECASE,
)
TABLE_PATTERN = re.compile(r"\b(?:from|join)\s+([a-zA-Z_][\w]*)", re.IGNORECASE)


def _fallback_validate(sql: str) -> tuple[str, ...]:
    """Conservative fallback used only when SQLGlot isn't installed.

    Execution is still protected by SQLite's read-only URI and authorizer. This
    fallback intentionally supports a smaller subset than the SQLGlot path.
    """
    text = sql.strip()
    if text.endswith(";"):
        text = text[:-1].rstrip()
    if ";" in text or "--" in text or "/*" in text or "*/" in text:
        raise SQLSafetyError("Multiple statements and SQL comments are not allowed.")
    if not re.match(r"^(select|with)\b", text, re.IGNORECASE):
        raise SQLSafetyError("Only SELECT queries and read-only CTEs are allowed.")
    if FORBIDDEN_TOKENS.search(text):
        raise SQLSafetyError("The query contains a forbidden SQL operation.")
    if re.search(r"\binto\b", text, re.IGNORECASE):
        raise SQLSafetyError("SELECT INTO is not allowed.")
    for function in FORBIDDEN_FUNCTIONS:
        if re.search(rf"\b{re.escape(function)}\s*\(", text, re.IGNORECASE):
            raise SQLSafetyError(f"The SQL function '{function}' is not allowed.")
    tables = tuple(sorted({name.lower() for name in TABLE_PATTERN.findall(text)}))
    if not tables:
        raise SQLSafetyError("The query must read from an approved analytics table.")
    unknown = set(tables) - ALLOWED_TABLES
    if unknown:
        raise SQLSafetyError(f"Tables are not available to this copilot: {', '.join(sorted(unknown))}.")
    return tables


def _sqlglot_validate(sql: str) -> tuple[str, ...]:
    import sqlglot
    from sqlglot import exp
    from sqlglot.errors import ParseError

    try:
        trees = [tree for tree in sqlglot.parse(sql, read="sqlite") if tree is not None]
    except ParseError as exc:
        raise SQLSafetyError(f"SQL could not be parsed: {exc}") from exc
    if len(trees) != 1:
        raise SQLSafetyError("Exactly one SQL statement is allowed.")
    tree = trees[0]
    if tree.key not in {"select", "union", "intersect", "except"}:
        raise SQLSafetyError("Only SELECT queries and read-only CTEs are allowed.")
    if any(select.args.get("into") for select in tree.find_all(exp.Select)):
        raise SQLSafetyError("SELECT INTO is not allowed.")

    cte_columns: dict[str, set[str]] = {}
    cte_names = set()
    for cte in tree.find_all(exp.CTE):
        cte_name = cte.alias_or_name.lower() if cte.alias_or_name else ""
        if cte_name:
            cte_names.add(cte_name)
            output_columns: set[str] = set()
            for select in cte.this.find_all(exp.Select):
                for projection in select.expressions:
                    output_name = projection.alias_or_name
                    if output_name:
                        output_columns.add(output_name.lower())
            cte_columns[cte_name] = output_columns

    tables = set()
    alias_to_table: dict[str, str] = {}
    alias_to_derived_columns: dict[str, set[str]] = {}
    for table in tree.find_all(exp.Table):
        name = table.name.lower()
        if table.db or table.catalog:
            raise SQLSafetyError("Schema-qualified or attached-database references are not allowed.")
        if name in cte_names:
            alias_to_derived_columns[(table.alias or table.name).lower()] = cte_columns.get(name, set())
            continue
        if name not in ALLOWED_TABLES:
            raise SQLSafetyError(f"Table '{name}' is not available to this copilot.")
        tables.add(name)
        alias_to_table[(table.alias or table.name).lower()] = name

    for subquery in tree.find_all(exp.Subquery):
        alias = subquery.alias
        if alias:
            output_columns: set[str] = set()
            for select in subquery.this.find_all(exp.Select):
                for projection in select.expressions:
                    output_name = projection.alias_or_name
                    if output_name:
                        output_columns.add(output_name.lower())
            alias_to_derived_columns[alias.lower()] = output_columns

    if not tables:
        raise SQLSafetyError("The query must read from an approved analytics table.")

    select_aliases = {
        projection.alias.lower()
        for select in tree.find_all(exp.Select)
        for projection in select.expressions
        if getattr(projection, "alias", None)
    }

    for column in tree.find_all(exp.Column):
        name = column.name.lower()
        if name == "*":
            continue
        if column.table:
            qualifier = column.table.lower()
            if qualifier in alias_to_derived_columns:
                if name not in alias_to_derived_columns[qualifier]:
                    raise SQLSafetyError(f"Column '{name}' does not exist in derived source '{qualifier}'.")
                continue
            source = alias_to_table.get(qualifier, qualifier)
            if source not in ALLOWED_COLUMNS:
                raise SQLSafetyError(f"Column qualifier '{column.table}' is not an approved table alias.")
            if name not in ALLOWED_COLUMNS[source]:
                raise SQLSafetyError(f"Column '{name}' does not exist in approved table '{source}'.")
        else:
            # ORDER BY / GROUP BY may reference a projection alias.
            if name in select_aliases:
                continue
            # Require the unqualified field to exist in at least one source table.
            if not any(name in ALLOWED_COLUMNS[table] for table in tables):
                raise SQLSafetyError(f"Column '{name}' is not available in the selected tables.")

    for function in tree.find_all(exp.Func):
        function_name = (getattr(function, "name", "") or function.sql_name()).lower()
        if function_name in FORBIDDEN_FUNCTIONS:
            raise SQLSafetyError(f"The SQL function '{function_name}' is not allowed.")
    return tuple(sorted(tables))


def validate_sql(sql: str) -> ValidatedSQL:
    if not isinstance(sql, str) or not sql.strip():
        raise SQLSafetyError("SQL is required.")
    if len(sql) > 10000:
        raise SQLSafetyError("SQL exceeds the maximum allowed length.")
    if "--" in sql or "/*" in sql or "*/" in sql:
        raise SQLSafetyError("SQL comments are not allowed.")

    try:
        import sqlglot  # noqa: F401
    except ImportError:
        tables = _fallback_validate(sql)
        return ValidatedSQL(sql=sql.strip().rstrip(";"), tables=tables, validator="sqlite-authorizer-fallback")

    tables = _sqlglot_validate(sql)
    return ValidatedSQL(sql=sql.strip().rstrip(";"), tables=tables, validator="sqlglot-ast")
