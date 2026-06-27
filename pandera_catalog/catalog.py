"""Core catalog abstraction for pandera-catalog.

The :class:`PanderaCatalog` class is the primary entry-point for registering,
looking up, listing, and removing Pandera schema entries.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

import pandera.pandas as pa

from .types import SchemaEntry, SchemaProjectionEntry, SchemaProjectionStep

if TYPE_CHECKING:
    from .backend import SqlCatalogBackend


class PanderaCatalog:
    """A registry for Pandera schemas.

    Schemas are stored in memory by name.  A future version will persist
    entries to a SQLAlchemy-backed database (SQLite by default).

    Examples
    --------
    >>> from pandera_catalog import PanderaCatalog
    >>> import pandera.pandas as pa
    >>> catalog = PanderaCatalog()
    >>> schema = pa.DataFrameSchema({"value": pa.Column(float)})
    >>> catalog.register("my_schema", schema)
    >>> catalog.get("my_schema")
    <Schema DataFrameSchema(columns={'value': ...}, ...)>
    """

    def __init__(self, *, backend: SqlCatalogBackend | None = None) -> None:
        self._store: dict[str, SchemaEntry] = {}
        self._projections: dict[str, SchemaProjectionEntry] = {}
        self._backend = backend
        if self._backend is not None:
            self._backend.initialize()
            for entry in self._backend.load_schemas():
                self._store[entry.name] = entry
            for projection_entry in self._backend.load_projections():
                self._projections[projection_entry.name] = projection_entry

    # ------------------------------------------------------------------
    # Mutating operations
    # ------------------------------------------------------------------

    def register(
        self,
        name: str,
        schema: pa.DataFrameSchema,
        *,
        description: str | None = None,
        tags: list[str] | None = None,
        overwrite: bool = False,
    ) -> None:
        """Register a Pandera schema under *name*.

        Parameters
        ----------
        name:
            Unique identifier for the schema within this catalog.
        schema:
            A :class:`pandera.DataFrameSchema` instance.
        description:
            Optional human-readable description of the schema.
        tags:
            Optional list of string tags for categorisation.
        overwrite:
            When ``True``, silently replace any existing entry with the same
            name.  When ``False`` (default), raise :class:`KeyError` if the
            name is already registered.

        Raises
        ------
        KeyError
            If *name* is already registered and *overwrite* is ``False``.
        """
        if name in self._store and not overwrite:
            raise KeyError(
                f"Schema '{name}' is already registered.  "
                "Pass overwrite=True to replace it."
            )
        self._store[name] = SchemaEntry(
            name=name,
            schema=schema,
            description=description,
            tags=list(tags or []),
        )
        if self._backend is not None:
            self._backend.upsert_schema(self._store[name])

    def register_projection(
        self,
        name: str,
        steps: list[SchemaProjectionStep | Mapping[str, object]],
        *,
        description: str | None = None,
        overwrite: bool = False,
    ) -> None:
        """Register a named projection from ordered step definitions.

        Parameters
        ----------
        name:
            Unique projection name within this catalog.
        steps:
            Ordered list of projection steps. Each step must include
            ``schema``, ``kind``, and ``names``.
        description:
            Optional human-readable description of the projection.
        overwrite:
            When ``True``, replace any existing projection with the same name.

        Raises
        ------
        KeyError
            If any step schema is not registered, or if *name* already exists
            and *overwrite* is ``False``.
        ValueError
            If *steps* are invalid, include duplicates, include unknown columns,
            or include an unknown step kind.
        NotImplementedError
            If a ``kind: group`` step is provided.
        """
        if name in self._projections and not overwrite:
            raise KeyError(
                f"Projection '{name}' is already registered.  "
                "Pass overwrite=True to replace it."
            )

        resolved_steps = self._normalise_projection_steps(steps)
        resolved_columns = self._resolve_projection_columns(resolved_steps)
        duplicate_columns = self._find_duplicate_columns(
            [column for _, column in resolved_columns]
        )
        if duplicate_columns:
            raise ValueError(
                f"Projection columns contain duplicates across steps: "
                f"{duplicate_columns!r}."
            )

        self._projections[name] = SchemaProjectionEntry(
            name=name,
            steps=resolved_steps,
            description=description,
        )
        if self._backend is not None:
            self._backend.upsert_projection(self._projections[name], resolved_columns)

    def remove(self, name: str) -> None:
        """Remove the schema registered under *name*.

        Parameters
        ----------
        name:
            Name of the schema to remove.

        Raises
        ------
        KeyError
            If *name* is not registered.
        """
        if name not in self._store:
            raise KeyError(f"Schema '{name}' is not registered.")
        del self._store[name]
        if self._backend is not None:
            self._backend.remove_schema(name)

    def remove_projection(self, name: str) -> None:
        """Remove the projection registered under *name*."""
        if name not in self._projections:
            raise KeyError(f"Projection '{name}' is not registered.")
        del self._projections[name]
        if self._backend is not None:
            self._backend.remove_projection(name)

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def get(self, name: str) -> pa.DataFrameSchema:
        """Return the schema registered under *name*.

        Parameters
        ----------
        name:
            Name of the schema to retrieve.

        Returns
        -------
        pandera.DataFrameSchema

        Raises
        ------
        KeyError
            If *name* is not registered.
        """
        if name not in self._store:
            raise KeyError(f"Schema '{name}' is not registered.")
        return self._store[name].schema

    def get_entry(self, name: str) -> SchemaEntry:
        """Return the full :class:`~pandera_catalog.types.SchemaEntry` for *name*.

        Parameters
        ----------
        name:
            Name of the schema entry to retrieve.

        Returns
        -------
        SchemaEntry

        Raises
        ------
        KeyError
            If *name* is not registered.
        """
        if name not in self._store:
            raise KeyError(f"Schema '{name}' is not registered.")
        return self._store[name]

    def get_projection_entry(self, name: str) -> SchemaProjectionEntry:
        """Return the full projection entry registered under *name*."""
        if name not in self._projections:
            raise KeyError(f"Projection '{name}' is not registered.")
        return self._projections[name]

    def export_projection(self, name: str) -> pa.DataFrameSchema:
        """Materialise and return the schema defined by projection *name*."""
        projection = self.get_projection_entry(name)
        resolved_columns = self._resolve_projection_columns(projection.steps)
        columns: dict[str, pa.Column] = {}
        for schema_name, column_name in resolved_columns:
            source_schema = self.get(schema_name)
            columns[column_name] = source_schema.columns[column_name]
        return pa.DataFrameSchema(columns=columns, name=projection.name)

    def list(self) -> list[str]:
        """Return a sorted list of all registered schema names.

        Returns
        -------
        list[str]
        """
        return sorted(self._store.keys())

    def list_projections(self) -> list[str]:
        """Return a sorted list of all registered projection names."""
        return sorted(self._projections.keys())

    def __len__(self) -> int:
        return len(self._store)

    def __contains__(self, name: object) -> bool:
        return name in self._store

    def __repr__(self) -> str:
        names = self.list()
        projections = self.list_projections()
        return f"PanderaCatalog(schemas={names!r}, projections={projections!r})"

    @property
    def backend(self) -> SqlCatalogBackend | None:
        """Return the configured SQL backend, if any."""
        return self._backend

    @staticmethod
    def _find_duplicate_columns(columns: list[str]) -> list[str]:
        seen: set[str] = set()
        duplicates: list[str] = []
        for column in columns:
            if column in seen and column not in duplicates:
                duplicates.append(column)
            seen.add(column)
        return duplicates

    def _normalise_projection_steps(
        self, steps: list[SchemaProjectionStep | Mapping[str, object]]
    ) -> list[SchemaProjectionStep]:
        if not steps:
            raise ValueError("Projection steps cannot be empty.")

        normalised_steps: list[SchemaProjectionStep] = []
        for step in steps:
            if isinstance(step, SchemaProjectionStep):
                normalised = step
            elif isinstance(step, Mapping):
                normalised = SchemaProjectionStep(
                    schema=self._require_string(step, "schema"),
                    kind=self._require_string(step, "kind"),
                    names=self._require_string_list(step, "names"),
                )
            else:
                raise ValueError("Projection steps must be mappings or SchemaProjectionStep.")

            if normalised.kind not in {"columns", "group"}:
                raise ValueError(f"Unknown projection step kind: {normalised.kind!r}.")

            if normalised.kind == "group":
                raise NotImplementedError("Projection step kind 'group' is not implemented.")

            if normalised.schema not in self._store:
                raise KeyError(f"Schema '{normalised.schema}' is not registered.")

            if not normalised.names:
                raise ValueError("Projection step names cannot be empty.")

            normalised_steps.append(normalised)

        return normalised_steps

    def _resolve_projection_columns(
        self, steps: list[SchemaProjectionStep]
    ) -> list[tuple[str, str]]:
        resolved: list[tuple[str, str]] = []
        for step in steps:
            source_columns = set(self._store[step.schema].schema.columns.keys())
            unknown_columns = [name for name in step.names if name not in source_columns]
            if unknown_columns:
                raise ValueError(
                    f"Projection columns not found in source schema '{step.schema}': "
                    f"{unknown_columns!r}."
                )
            resolved.extend((step.schema, name) for name in step.names)
        return resolved

    @staticmethod
    def _require_string(step: Mapping[str, object], key: str) -> str:
        value = step.get(key)
        if not isinstance(value, str) or not value:
            raise ValueError(f"Projection step '{key}' must be a non-empty string.")
        return value

    @staticmethod
    def _require_string_list(step: Mapping[str, object], key: str) -> list[str]:
        value = step.get(key)
        if not isinstance(value, list) or not all(
            isinstance(item, str) and item for item in value
        ):
            raise ValueError(
                f"Projection step '{key}' must be a list of non-empty strings."
            )
        return list(value)
