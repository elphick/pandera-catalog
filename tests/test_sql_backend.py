from __future__ import annotations

from pathlib import Path

import pandera.pandas as pa
from sqlalchemy import create_engine, text

from pandera_catalog import PanderaCatalog, SqlCatalogBackend
from pandera_catalog.backend.views import get_view_ddl


def _sqlite_url(path: Path) -> str:
    return f"sqlite:///{path.as_posix()}"


def test_backend_round_trip_loads_schemas_and_projections(tmp_path):
    db_path = tmp_path / "catalog.sqlite"
    backend = SqlCatalogBackend(url=_sqlite_url(db_path))
    catalog = PanderaCatalog(backend=backend)
    source_schema = pa.DataFrameSchema(
        {
            "id": pa.Column(int),
            "value": pa.Column(float, pa.Check.greater_than(0)),
        }
    )
    catalog.register("source", source_schema, description="source schema", tags=["core"])
    catalog.register_projection(
        "reporting",
        steps=[{"schema": "source", "kind": "columns", "names": ["value", "id"]}],
    )

    reloaded = PanderaCatalog(backend=SqlCatalogBackend(url=_sqlite_url(db_path)))
    assert reloaded.list() == ["source"]
    assert reloaded.list_projections() == ["reporting"]
    projected = reloaded.export_projection("reporting")
    assert list(projected.columns.keys()) == ["value", "id"]


def test_backend_accepts_engine(tmp_path):
    engine = create_engine(_sqlite_url(tmp_path / "engine.sqlite"), future=True)
    backend = SqlCatalogBackend(engine=engine)
    catalog = PanderaCatalog(backend=backend)
    catalog.register(
        "source",
        pa.DataFrameSchema({"id": pa.Column(int)}),
    )

    with backend.engine.connect() as conn:
        rows = conn.execute(text("SELECT schema_name FROM v_schema_catalog")).fetchall()

    assert rows == [("source",)]


def test_views_include_materialized_projection_rows(tmp_path):
    db_path = tmp_path / "catalog.sqlite"
    backend = SqlCatalogBackend(url=_sqlite_url(db_path))
    catalog = PanderaCatalog(backend=backend)
    schema = pa.DataFrameSchema(
        {
            "id": pa.Column(int),
            "value": pa.Column(float, pa.Check.greater_than(0)),
        }
    )
    catalog.register("base", schema)
    catalog.register_projection(
        "reporting",
        steps=[{"schema": "base", "kind": "columns", "names": ["value"]}],
    )

    with backend.engine.connect() as conn:
        schema_rows = conn.execute(
            text(
                "SELECT schema_name, is_projected FROM v_schema_catalog "
                "WHERE schema_name IN ('base', 'reporting') ORDER BY schema_name"
            )
        ).all()
        column_rows = conn.execute(
            text(
                "SELECT schema_name, column_name, is_projected, source_projection_name "
                "FROM v_schema_columns WHERE schema_name = 'reporting'"
            )
        ).all()
        check_rows = conn.execute(
            text(
                "SELECT schema_name, column_name, is_projected FROM v_schema_checks "
                "WHERE schema_name = 'reporting'"
            )
        ).all()

    assert schema_rows == [("base", 0), ("reporting", 1)]
    assert column_rows == [("reporting", "value", 1, "reporting")]
    assert check_rows == [("reporting", "value", 1)]


def test_view_ddl_supports_mssql_and_postgres():
    mssql_ddl = get_view_ddl("mssql")
    postgres_ddl = get_view_ddl("postgresql")

    assert "OBJECT_ID" in mssql_ddl[0][0]
    assert "DROP VIEW IF EXISTS" in postgres_ddl[0][0]
    assert len(mssql_ddl) == len(postgres_ddl) >= 5


def test_backend_internal_helpers_and_cleanup(tmp_path):
    backend = SqlCatalogBackend(url=_sqlite_url(tmp_path / "catalog.sqlite"))
    catalog = PanderaCatalog(backend=backend)
    with backend.engine.begin() as conn:
        conn.execute(
            backend.schemas.insert().values(
                schema_name="manual",
                description="manual schema",
                tags_json="[]",
                schema_yaml="schema_type: dataframe\ncolumns: {}\nmetadata:\n  owner:\n    team: analytics\n  source: manual\nchecks:\n  - name: frame_check\n    statistics: 1\n",
            )
        )
        backend._insert_schema_flat_rows(
            conn,
            "manual",
            {
                "columns": {
                    "value": {
                        "dtype": "float64",
                        "nullable": False,
                        "required": True,
                        "unique": False,
                        "coerce": False,
                        "regex": False,
                        "checks": [
                            {"name": "positive", "statistics": 0},
                            {"greater_than": 0},
                        ],
                    }
                },
                "checks": [
                    {"name": "frame_check", "statistics": 1},
                    {"less_than": 10},
                ],
                "metadata": {"owner": {"team": "analytics"}, "source": "manual"},
            },
        )

    catalog.register(
        "base",
        pa.DataFrameSchema(
            {
                "value": pa.Column(float, pa.Check.greater_than(0)),
            },
            checks=[pa.Check.greater_than_or_equal_to(0)],
        ),
    )
    catalog.register_projection(
        "projection",
        [{"schema": "base", "kind": "columns", "names": ["value"]}],
    )

    assert backend._normalise_checks(None) == []
    assert backend._normalise_checks(["x"]) == ["x"]
    assert backend._parse_check_payload({"name": "custom", "statistics": 1}, 1)[0] == "custom"
    assert backend._parse_check_payload({"greater_than": 0}, 2)[0] == "greater_than"
    assert backend._optional_bool(True) is True
    assert backend._optional_bool(0) is False
    assert backend._optional_text(None) is None

    with backend.engine.connect() as conn:
        metadata_rows = conn.execute(
            text("SELECT * FROM v_metadata_lookup WHERE schema_name = 'manual'")
        ).all()
        schema_checks = conn.execute(
            text("SELECT * FROM v_schema_checks WHERE schema_name = 'manual'")
        ).all()

    assert metadata_rows
    assert schema_checks

    catalog.remove_projection("projection")
    catalog.remove("base")

    with backend.engine.connect() as conn:
        rows = conn.execute(
            text("SELECT schema_name FROM v_schema_catalog ORDER BY schema_name")
        ).fetchall()

    assert rows == [("manual",)]
