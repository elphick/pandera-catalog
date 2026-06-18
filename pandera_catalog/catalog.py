"""Core catalog abstraction for pandera-catalog.

The :class:`PanderaCatalog` class is the primary entry-point for registering,
looking up, listing, and removing Pandera schema entries.
"""
from __future__ import annotations

from typing import Optional

import pandera.pandas as pa

from .types import SchemaEntry


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

    def __init__(self) -> None:
        self._store: dict[str, SchemaEntry] = {}

    # ------------------------------------------------------------------
    # Mutating operations
    # ------------------------------------------------------------------

    def register(
        self,
        name: str,
        schema: pa.DataFrameSchema,
        *,
        description: Optional[str] = None,
        tags: Optional[list[str]] = None,
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

    def list(self) -> list[str]:
        """Return a sorted list of all registered schema names.

        Returns
        -------
        list[str]
        """
        return sorted(self._store.keys())

    def __len__(self) -> int:
        return len(self._store)

    def __contains__(self, name: object) -> bool:
        return name in self._store

    def __repr__(self) -> str:
        names = self.list()
        return f"PanderaCatalog({names!r})"
