from __future__ import annotations

from pathlib import Path

import pandera.pandas as pa
import pytest

from pandera_catalog import CatalogViewReader, PanderaCatalog, SqlCatalogBackend


def _sqlite_url(path: Path) -> str:
    return f"sqlite:///{path.as_posix()}"


def test_reader_returns_dataframes_for_views(tmp_path):
    backend = SqlCatalogBackend(url=_sqlite_url(tmp_path / "catalog.sqlite"))
    catalog = PanderaCatalog(backend=backend)
    catalog.register(
        "base",
        pa.DataFrameSchema(
            {
                "id": pa.Column(int),
                "value": pa.Column(float, pa.Check.greater_than(0)),
            }
        ),
        tags=["core"],
    )
    catalog.register_projection(
        "projection",
        [{"schema": "base", "kind": "columns", "names": ["value"]}],
    )

    reader = CatalogViewReader(catalog)
    schema_catalog = reader.read_schema_catalog()
    schema_columns = reader.read_schema_columns()
    schema_checks = reader.read_schema_checks()
    projection_steps = reader.read_projection_steps()
    metadata_lookup = reader.read_metadata_lookup()

    assert "schema_name" in schema_catalog.columns
    assert "is_projected" in schema_catalog.columns
    assert schema_catalog.shape[0] == 2
    assert set(schema_columns["schema_name"]) == {"base", "projection"}
    assert "source_projection_name" in schema_columns.columns
    assert schema_checks.shape[0] >= 1
    assert projection_steps.shape[0] == 1
    assert metadata_lookup.empty


def test_reader_requires_sql_backend():
    catalog = PanderaCatalog()
    reader = CatalogViewReader(catalog)
    with pytest.raises(RuntimeError, match="requires a PanderaCatalog configured with a SQL backend"):
        reader.read_schema_catalog()


def test_reader_rejects_unknown_view(tmp_path):
    backend = SqlCatalogBackend(url=_sqlite_url(tmp_path / "catalog.sqlite"))
    catalog = PanderaCatalog(backend=backend)
    reader = CatalogViewReader(catalog)

    with pytest.raises(KeyError, match="Unknown catalog view"):
        reader.read_view("v_not_real")
