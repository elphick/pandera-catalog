"""View DDL generation for SQL-backed catalog projections."""

from __future__ import annotations


VIEW_DEFINITIONS: dict[str, str] = {
    "v_schema_catalog": """
SELECT
    s.schema_name,
    s.description,
    s.tags_json,
    0 AS is_projected,
    NULL AS source_projection_name
FROM catalog_schemas AS s
UNION ALL
SELECT
    p.projection_name AS schema_name,
    p.description,
    '[]' AS tags_json,
    1 AS is_projected,
    p.projection_name AS source_projection_name
FROM catalog_projections AS p
""".strip(),
    "v_schema_columns": """
SELECT
    c.schema_name,
    c.column_name,
    c.ordinal,
    c.dtype,
    c.nullable,
    c.required,
    c.unique_value,
    c.coerce,
    c.regex,
    c.checks_json,
    0 AS is_projected,
    NULL AS source_projection_name,
    c.source_schema_name,
    c.source_column_name
FROM catalog_schema_columns AS c
UNION ALL
SELECT
    p.projection_name AS schema_name,
    p.column_name,
    p.ordinal,
    p.dtype,
    p.nullable,
    p.required,
    p.unique_value,
    p.coerce,
    p.regex,
    p.checks_json,
    1 AS is_projected,
    p.projection_name AS source_projection_name,
    p.source_schema_name,
    p.source_column_name
FROM catalog_projection_columns AS p
""".strip(),
    "v_schema_checks": """
SELECT
    c.schema_name,
    c.column_name,
    c.scope,
    c.check_order,
    c.name,
    c.statistics_json,
    c.payload_json,
    0 AS is_projected,
    NULL AS source_projection_name,
    c.source_schema_name,
    c.source_column_name
FROM catalog_schema_checks AS c
UNION ALL
SELECT
    p.projection_name AS schema_name,
    p.column_name,
    p.scope,
    p.check_order,
    p.name,
    p.statistics_json,
    p.payload_json,
    1 AS is_projected,
    p.projection_name AS source_projection_name,
    p.source_schema_name,
    p.source_column_name
FROM catalog_projection_checks AS p
""".strip(),
    "v_projection_steps": """
SELECT
    projection_name,
    step_index,
    kind,
    source_schema_name,
    name_ordinal,
    selected_name
FROM catalog_projection_steps
""".strip(),
    "v_metadata_lookup": """
SELECT
    schema_name,
    meta_key,
    lookup_key,
    lookup_value_json,
    value_type
FROM catalog_metadata_lookup
""".strip(),
}


def drop_view_sql(dialect_name: str, view_name: str) -> str:
    """Return dialect-appropriate SQL to drop a view when it exists."""
    if dialect_name.startswith("mssql"):
        return (
            f"IF OBJECT_ID(N'{view_name}', N'V') IS NOT NULL "
            f"DROP VIEW {view_name};"
        )
    return f"DROP VIEW IF EXISTS {view_name};"


def create_view_sql(view_name: str, query_sql: str) -> str:
    """Return SQL to create a view."""
    return f"CREATE VIEW {view_name} AS {query_sql};"


def get_view_ddl(dialect_name: str) -> list[tuple[str, str]]:
    """Return ordered (drop, create) SQL statements for all views."""
    statements: list[tuple[str, str]] = []
    for view_name, select_sql in VIEW_DEFINITIONS.items():
        statements.append(
            (drop_view_sql(dialect_name, view_name), create_view_sql(view_name, select_sql))
        )
    return statements
