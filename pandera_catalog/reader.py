"""Read generated catalog views as pandas DataFrames."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text

from .catalog import PanderaCatalog


class CatalogViewReader:
    """Query generated SQL views from a catalog backend."""

    _VIEW_NAMES = {
        "schema_catalog": "v_schema_catalog",
        "schema_columns": "v_schema_columns",
        "schema_checks": "v_schema_checks",
        "projection_steps": "v_projection_steps",
        "metadata_lookup": "v_metadata_lookup",
    }

    def __init__(self, catalog: PanderaCatalog) -> None:
        self.catalog = catalog

    def read_view(self, view_name: str) -> pd.DataFrame:
        """Return a DataFrame for a named generated view."""
        backend = self._require_backend()
        if view_name not in self._VIEW_NAMES.values():
            raise KeyError(f"Unknown catalog view: {view_name!r}")

        with backend.engine.connect() as conn:
            return pd.read_sql_query(text(f"SELECT * FROM {view_name}"), conn)

    def read_schema_catalog(self) -> pd.DataFrame:
        return self.read_view(self._VIEW_NAMES["schema_catalog"])

    def read_schema_columns(self) -> pd.DataFrame:
        return self.read_view(self._VIEW_NAMES["schema_columns"])

    def read_schema_checks(self) -> pd.DataFrame:
        return self.read_view(self._VIEW_NAMES["schema_checks"])

    def read_projection_steps(self) -> pd.DataFrame:
        return self.read_view(self._VIEW_NAMES["projection_steps"])

    def read_metadata_lookup(self) -> pd.DataFrame:
        return self.read_view(self._VIEW_NAMES["metadata_lookup"])

    def _require_backend(self):
        backend = self.catalog.backend
        if backend is None:
            raise RuntimeError(
                "CatalogViewReader requires a PanderaCatalog configured with a SQL backend."
            )
        backend.initialize()
        return backend
