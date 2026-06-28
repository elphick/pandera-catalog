"""SQLAlchemy Core backend for persisting catalog state and generated views."""

from __future__ import annotations

import json
from collections import defaultdict

import pandera.pandas as pa
from sqlalchemy import Boolean, Column, Integer, MetaData, String, Table, Text, create_engine, delete, insert, select, text
from sqlalchemy.engine import Connection, Engine
import yaml

from pandera_catalog.types import SchemaEntry, SchemaProjectionEntry, SchemaProjectionStep

from .views import get_view_ddl

_COLUMN_BASE_KEYS = {
    "title",
    "description",
    "dtype",
    "nullable",
    "checks",
    "unique",
    "coerce",
    "required",
    "regex",
}

_SCHEMA_BASE_KEYS = {
    "schema_type",
    "version",
    "columns",
    "checks",
    "index",
    "dtype",
    "coerce",
    "strict",
    "name",
    "ordered",
    "unique",
    "report_duplicates",
    "unique_column_names",
    "add_missing_columns",
    "title",
    "description",
    "metadata",
}


class SqlCatalogBackend:
    """Persist catalog schemas/projections and maintain tabular views."""

    def __init__(
        self,
        engine: Engine | None = None,
        url: str = "sqlite:///:memory:",
    ) -> None:
        if engine is not None and url != "sqlite:///:memory:":
            raise ValueError("Pass either engine or url, not both.")
        self.engine: Engine = engine if engine is not None else create_engine(url, future=True)
        self.metadata = MetaData()
        self.schemas = Table(
            "catalog_schemas",
            self.metadata,
            Column("schema_name", String(255), primary_key=True),
            Column("description", Text, nullable=True),
            Column("tags_json", Text, nullable=False),
            Column("schema_yaml", Text, nullable=False),
        )
        self.schema_columns = Table(
            "catalog_schema_columns",
            self.metadata,
            Column("schema_name", String(255), nullable=False),
            Column("column_name", String(255), nullable=False),
            Column("ordinal", Integer, nullable=False),
            Column("dtype", String(255), nullable=True),
            Column("nullable", Boolean, nullable=True),
            Column("required", Boolean, nullable=True),
            Column("unique_value", Boolean, nullable=True),
            Column("coerce", Boolean, nullable=True),
            Column("regex", Boolean, nullable=True),
            Column("checks_json", Text, nullable=True),
            Column("source_schema_name", String(255), nullable=False),
            Column("source_column_name", String(255), nullable=False),
        )
        self.schema_checks = Table(
            "catalog_schema_checks",
            self.metadata,
            Column("schema_name", String(255), nullable=False),
            Column("column_name", String(255), nullable=True),
            Column("scope", String(32), nullable=False),
            Column("check_order", Integer, nullable=False),
            Column("name", String(255), nullable=False),
            Column("statistics_json", Text, nullable=True),
            Column("payload_json", Text, nullable=False),
            Column("source_schema_name", String(255), nullable=False),
            Column("source_column_name", String(255), nullable=True),
        )
        self.metadata_lookup = Table(
            "catalog_metadata_lookup",
            self.metadata,
            Column("schema_name", String(255), nullable=False),
            Column("meta_key", String(255), nullable=False),
            Column("lookup_key", String(255), nullable=True),
            Column("lookup_value_json", Text, nullable=False),
            Column("value_type", String(64), nullable=False),
        )
        self.projections = Table(
            "catalog_projections",
            self.metadata,
            Column("projection_name", String(255), primary_key=True),
            Column("description", Text, nullable=True),
        )
        self.projection_steps = Table(
            "catalog_projection_steps",
            self.metadata,
            Column("projection_name", String(255), nullable=False),
            Column("step_index", Integer, nullable=False),
            Column("kind", String(64), nullable=False),
            Column("source_schema_name", String(255), nullable=False),
            Column("name_ordinal", Integer, nullable=False),
            Column("selected_name", String(255), nullable=False),
        )
        self.projection_columns = Table(
            "catalog_projection_columns",
            self.metadata,
            Column("projection_name", String(255), nullable=False),
            Column("column_name", String(255), nullable=False),
            Column("ordinal", Integer, nullable=False),
            Column("dtype", String(255), nullable=True),
            Column("nullable", Boolean, nullable=True),
            Column("required", Boolean, nullable=True),
            Column("unique_value", Boolean, nullable=True),
            Column("coerce", Boolean, nullable=True),
            Column("regex", Boolean, nullable=True),
            Column("checks_json", Text, nullable=True),
            Column("source_schema_name", String(255), nullable=False),
            Column("source_column_name", String(255), nullable=False),
        )
        self.projection_checks = Table(
            "catalog_projection_checks",
            self.metadata,
            Column("projection_name", String(255), nullable=False),
            Column("column_name", String(255), nullable=True),
            Column("scope", String(32), nullable=False),
            Column("check_order", Integer, nullable=False),
            Column("name", String(255), nullable=False),
            Column("statistics_json", Text, nullable=True),
            Column("payload_json", Text, nullable=False),
            Column("source_schema_name", String(255), nullable=False),
            Column("source_column_name", String(255), nullable=True),
        )

    def initialize(self) -> None:
        """Create backend tables and tabular views."""
        self.metadata.create_all(self.engine)
        self._create_views()

    def _create_views(self) -> None:
        dialect_name = self.engine.dialect.name
        with self.engine.begin() as conn:
            for drop_sql, create_sql in get_view_ddl(dialect_name):
                conn.execute(text(drop_sql))
                conn.execute(text(create_sql))

    def load_schemas(self) -> list[SchemaEntry]:
        """Return persisted schema entries."""
        entries: list[SchemaEntry] = []
        with self.engine.connect() as conn:
            rows = conn.execute(
                select(
                    self.schemas.c.schema_name,
                    self.schemas.c.description,
                    self.schemas.c.tags_json,
                    self.schemas.c.schema_yaml,
                )
            ).all()
        for row in rows:
            entries.append(
                SchemaEntry(
                    name=row.schema_name,
                    schema=pa.DataFrameSchema.from_yaml(row.schema_yaml),
                    description=row.description,
                    tags=list(json.loads(row.tags_json)),
                )
            )
        return entries

    def load_projections(self) -> list[SchemaProjectionEntry]:
        """Return persisted projection entries."""
        with self.engine.connect() as conn:
            projection_rows = conn.execute(
                select(self.projections.c.projection_name, self.projections.c.description)
            ).all()
            step_rows = conn.execute(
                select(
                    self.projection_steps.c.projection_name,
                    self.projection_steps.c.step_index,
                    self.projection_steps.c.kind,
                    self.projection_steps.c.source_schema_name,
                    self.projection_steps.c.name_ordinal,
                    self.projection_steps.c.selected_name,
                ).order_by(
                    self.projection_steps.c.projection_name,
                    self.projection_steps.c.step_index,
                    self.projection_steps.c.name_ordinal,
                )
            ).all()

        descriptions = {row.projection_name: row.description for row in projection_rows}
        grouped: dict[str, dict[int, dict[str, object]]] = defaultdict(dict)
        for row in step_rows:
            projection_steps = grouped[row.projection_name]
            step_payload = projection_steps.setdefault(
                row.step_index,
                {
                    "schema": row.source_schema_name,
                    "kind": row.kind,
                    "names": [],
                },
            )
            names = step_payload["names"]
            assert isinstance(names, list)
            names.append(row.selected_name)

        result: list[SchemaProjectionEntry] = []
        for projection_name, step_map in grouped.items():
            ordered_steps: list[SchemaProjectionStep] = []
            for step_index in sorted(step_map):
                payload = step_map[step_index]
                ordered_steps.append(
                    SchemaProjectionStep(
                        schema=str(payload["schema"]),
                        kind=str(payload["kind"]),
                        names=list(payload["names"]),
                    )
                )
            result.append(
                SchemaProjectionEntry(
                    name=projection_name,
                    steps=ordered_steps,
                    description=descriptions.get(projection_name),
                )
            )
        return result

    def upsert_schema(self, entry: SchemaEntry) -> None:
        """Insert or replace a schema entry and its flattened rows."""
        schema_yaml = entry.schema.to_yaml()
        definition = yaml.safe_load(schema_yaml) or {}
        with self.engine.begin() as conn:
            self._delete_schema_rows(conn, entry.name)
            conn.execute(
                insert(self.schemas).values(
                    schema_name=entry.name,
                    description=entry.description,
                    tags_json=json.dumps(entry.tags),
                    schema_yaml=schema_yaml,
                )
            )
            self._insert_schema_flat_rows(conn, entry.name, definition)

    def remove_schema(self, schema_name: str) -> None:
        """Delete a persisted schema and its flattened rows."""
        with self.engine.begin() as conn:
            self._delete_schema_rows(conn, schema_name)

    def upsert_projection(
        self,
        entry: SchemaProjectionEntry,
        resolved_columns: list[tuple[str, str]],
    ) -> None:
        """Insert or replace a projection and materialized projection rows."""
        with self.engine.begin() as conn:
            self._delete_projection_rows(conn, entry.name)
            conn.execute(
                insert(self.projections).values(
                    projection_name=entry.name,
                    description=entry.description,
                )
            )
            for step_index, step in enumerate(entry.steps, start=1):
                for name_ordinal, selected_name in enumerate(step.names, start=1):
                    conn.execute(
                        insert(self.projection_steps).values(
                            projection_name=entry.name,
                            step_index=step_index,
                            kind=step.kind,
                            source_schema_name=step.schema,
                            name_ordinal=name_ordinal,
                            selected_name=selected_name,
                        )
                    )

            for ordinal, (source_schema_name, source_column_name) in enumerate(
                resolved_columns, start=1
            ):
                source_column = conn.execute(
                    select(
                        self.schema_columns.c.dtype,
                        self.schema_columns.c.nullable,
                        self.schema_columns.c.required,
                        self.schema_columns.c.unique_value,
                        self.schema_columns.c.coerce,
                        self.schema_columns.c.regex,
                        self.schema_columns.c.checks_json,
                    ).where(
                        self.schema_columns.c.schema_name == source_schema_name,
                        self.schema_columns.c.column_name == source_column_name,
                    )
                ).first()
                if source_column is None:
                    continue
                conn.execute(
                    insert(self.projection_columns).values(
                        projection_name=entry.name,
                        column_name=source_column_name,
                        ordinal=ordinal,
                        dtype=source_column.dtype,
                        nullable=source_column.nullable,
                        required=source_column.required,
                        unique_value=source_column.unique_value,
                        coerce=source_column.coerce,
                        regex=source_column.regex,
                        checks_json=source_column.checks_json,
                        source_schema_name=source_schema_name,
                        source_column_name=source_column_name,
                    )
                )
                source_checks = conn.execute(
                    select(
                        self.schema_checks.c.column_name,
                        self.schema_checks.c.scope,
                        self.schema_checks.c.check_order,
                        self.schema_checks.c.name,
                        self.schema_checks.c.statistics_json,
                        self.schema_checks.c.payload_json,
                    ).where(
                        self.schema_checks.c.schema_name == source_schema_name,
                        self.schema_checks.c.column_name == source_column_name,
                        self.schema_checks.c.scope == "column",
                    )
                ).all()
                for check_row in source_checks:
                    conn.execute(
                        insert(self.projection_checks).values(
                            projection_name=entry.name,
                            column_name=check_row.column_name,
                            scope=check_row.scope,
                            check_order=check_row.check_order,
                            name=check_row.name,
                            statistics_json=check_row.statistics_json,
                            payload_json=check_row.payload_json,
                            source_schema_name=source_schema_name,
                            source_column_name=source_column_name,
                        )
                    )

    def remove_projection(self, projection_name: str) -> None:
        """Delete a persisted projection and materialized rows."""
        with self.engine.begin() as conn:
            self._delete_projection_rows(conn, projection_name)

    def _delete_schema_rows(self, conn: Connection, schema_name: str) -> None:
        conn.execute(delete(self.schema_checks).where(self.schema_checks.c.schema_name == schema_name))
        conn.execute(delete(self.schema_columns).where(self.schema_columns.c.schema_name == schema_name))
        conn.execute(delete(self.metadata_lookup).where(self.metadata_lookup.c.schema_name == schema_name))
        conn.execute(delete(self.schemas).where(self.schemas.c.schema_name == schema_name))

    def _delete_projection_rows(self, conn: Connection, projection_name: str) -> None:
        conn.execute(
            delete(self.projection_checks).where(
                self.projection_checks.c.projection_name == projection_name
            )
        )
        conn.execute(
            delete(self.projection_columns).where(
                self.projection_columns.c.projection_name == projection_name
            )
        )
        conn.execute(
            delete(self.projection_steps).where(
                self.projection_steps.c.projection_name == projection_name
            )
        )
        conn.execute(
            delete(self.projections).where(self.projections.c.projection_name == projection_name)
        )

    def _insert_schema_flat_rows(
        self, conn: Connection, schema_name: str, definition: dict[str, object]
    ) -> None:
        columns = definition.get("columns") or {}
        if isinstance(columns, dict):
            for ordinal, (column_name, payload) in enumerate(columns.items(), start=1):
                column_payload = payload if isinstance(payload, dict) else {}
                checks = self._normalise_checks(column_payload.get("checks"))
                if not checks:
                    checks = [
                        {key: value}
                        for key, value in column_payload.items()
                        if key not in _COLUMN_BASE_KEYS
                    ]
                conn.execute(
                    insert(self.schema_columns).values(
                        schema_name=schema_name,
                        column_name=column_name,
                        ordinal=ordinal,
                        dtype=self._optional_text(column_payload.get("dtype")),
                        nullable=self._optional_bool(column_payload.get("nullable")),
                        required=self._optional_bool(column_payload.get("required")),
                        unique_value=self._optional_bool(column_payload.get("unique")),
                        coerce=self._optional_bool(column_payload.get("coerce")),
                        regex=self._optional_bool(column_payload.get("regex")),
                        checks_json=json.dumps(checks),
                        source_schema_name=schema_name,
                        source_column_name=column_name,
                    )
                )
                for check_order, check_payload in enumerate(checks, start=1):
                    name, statistics_json, payload_json = self._parse_check_payload(
                        check_payload, check_order
                    )
                    conn.execute(
                        insert(self.schema_checks).values(
                            schema_name=schema_name,
                            column_name=column_name,
                            scope="column",
                            check_order=check_order,
                            name=name,
                            statistics_json=statistics_json,
                            payload_json=payload_json,
                            source_schema_name=schema_name,
                            source_column_name=column_name,
                        )
                    )

        dataframe_checks = self._normalise_checks(definition.get("checks"))
        if not dataframe_checks:
            dataframe_checks = [
                {key: value}
                for key, value in definition.items()
                if key not in _SCHEMA_BASE_KEYS
            ]
        for check_order, check_payload in enumerate(dataframe_checks, start=1):
            name, statistics_json, payload_json = self._parse_check_payload(
                check_payload, check_order
            )
            conn.execute(
                insert(self.schema_checks).values(
                    schema_name=schema_name,
                    column_name=None,
                    scope="dataframe",
                    check_order=check_order,
                    name=name,
                    statistics_json=statistics_json,
                    payload_json=payload_json,
                    source_schema_name=schema_name,
                    source_column_name=None,
                )
            )

        metadata_payload = definition.get("metadata")
        if isinstance(metadata_payload, dict):
            for meta_key, lookup_value in metadata_payload.items():
                if isinstance(lookup_value, dict):
                    for lookup_key, nested_value in lookup_value.items():
                        conn.execute(
                            insert(self.metadata_lookup).values(
                                schema_name=schema_name,
                                meta_key=str(meta_key),
                                lookup_key=str(lookup_key),
                                lookup_value_json=json.dumps(nested_value),
                                value_type=type(nested_value).__name__,
                            )
                        )
                else:
                    conn.execute(
                        insert(self.metadata_lookup).values(
                            schema_name=schema_name,
                            meta_key=str(meta_key),
                            lookup_key=None,
                            lookup_value_json=json.dumps(lookup_value),
                            value_type=type(lookup_value).__name__,
                        )
                    )

    @staticmethod
    def _normalise_checks(payload: object) -> list[object]:
        if payload is None:
            return []
        if isinstance(payload, list):
            return payload
        return [payload]

    @staticmethod
    def _parse_check_payload(payload: object, check_order: int) -> tuple[str, str | None, str]:
        check_name = f"check_{check_order}"
        statistics: object | None = None
        if isinstance(payload, dict):
            if "name" in payload and isinstance(payload["name"], str):
                check_name = payload["name"]
                statistics = payload.get("statistics")
            elif len(payload) == 1:
                key = next(iter(payload.keys()))
                check_name = str(key)
                value = payload[key]
                statistics = value
            else:
                statistics = payload.get("statistics")
        payload_json = json.dumps(payload)
        statistics_json = json.dumps(statistics) if statistics is not None else None
        return check_name, statistics_json, payload_json

    @staticmethod
    def _optional_bool(value: object) -> bool | None:
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        return bool(value)

    @staticmethod
    def _optional_text(value: object) -> str | None:
        if value is None:
            return None
        return str(value)
