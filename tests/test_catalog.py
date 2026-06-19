"""Tests for PanderaCatalog."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pandera
import pandera.pandas as pa
import pytest
import yaml

from pandera_catalog import PanderaCatalog
from pandera_catalog.schemas import load_schema_from_yaml, load_schema_from_dict
from pandera_catalog.types import SchemaEntry


# ---------------------------------------------------------------------------
# Catalog initialisation
# ---------------------------------------------------------------------------


class TestCatalogInit:
    def test_empty_on_creation(self):
        catalog = PanderaCatalog()
        assert len(catalog) == 0
        assert catalog.list() == []

    def test_repr(self):
        catalog = PanderaCatalog()
        assert "PanderaCatalog" in repr(catalog)


# ---------------------------------------------------------------------------
# Schema registration
# ---------------------------------------------------------------------------


class TestRegister:
    def test_register_and_get(self, simple_schema):
        catalog = PanderaCatalog()
        catalog.register("my_schema", simple_schema)
        assert "my_schema" in catalog
        retrieved = catalog.get("my_schema")
        assert isinstance(retrieved, pa.DataFrameSchema)

    def test_register_with_metadata(self, simple_schema):
        catalog = PanderaCatalog()
        catalog.register(
            "annotated",
            simple_schema,
            description="A simple test schema",
            tags=["test", "demo"],
        )
        entry = catalog.get_entry("annotated")
        assert isinstance(entry, SchemaEntry)
        assert entry.description == "A simple test schema"
        assert "test" in entry.tags

    def test_duplicate_raises_key_error(self, simple_schema):
        catalog = PanderaCatalog()
        catalog.register("dupe", simple_schema)
        with pytest.raises(KeyError, match="already registered"):
            catalog.register("dupe", simple_schema)

    def test_overwrite_allowed(self, simple_schema, tagged_schema):
        catalog = PanderaCatalog()
        catalog.register("s", simple_schema)
        catalog.register("s", tagged_schema, overwrite=True)
        # Should now hold the new schema without error
        assert "s" in catalog

    def test_list_returns_sorted_names(self, simple_schema, tagged_schema):
        catalog = PanderaCatalog()
        catalog.register("zebra", simple_schema)
        catalog.register("alpha", tagged_schema)
        assert catalog.list() == ["alpha", "zebra"]

    def test_len(self, simple_schema, tagged_schema):
        catalog = PanderaCatalog()
        catalog.register("a", simple_schema)
        catalog.register("b", tagged_schema)
        assert len(catalog) == 2


# ---------------------------------------------------------------------------
# Schema removal
# ---------------------------------------------------------------------------


class TestRemove:
    def test_remove_existing(self, simple_schema):
        catalog = PanderaCatalog()
        catalog.register("to_remove", simple_schema)
        catalog.remove("to_remove")
        assert "to_remove" not in catalog

    def test_remove_missing_raises(self):
        catalog = PanderaCatalog()
        with pytest.raises(KeyError, match="not registered"):
            catalog.remove("nonexistent")


# ---------------------------------------------------------------------------
# Get / get_entry error paths
# ---------------------------------------------------------------------------


class TestGet:
    def test_get_missing_raises(self):
        catalog = PanderaCatalog()
        with pytest.raises(KeyError, match="not registered"):
            catalog.get("missing")

    def test_get_entry_missing_raises(self):
        catalog = PanderaCatalog()
        with pytest.raises(KeyError, match="not registered"):
            catalog.get_entry("missing")


# ---------------------------------------------------------------------------
# Schema loading helpers
# ---------------------------------------------------------------------------


class TestLoadSchemaFromYaml:
    def test_load_roundtrip(self, simple_schema, tmp_path):
        yaml_path = tmp_path / "schema.yaml"
        yaml_path.write_text(simple_schema.to_yaml())

        loaded = load_schema_from_yaml(yaml_path)
        assert isinstance(loaded, pa.DataFrameSchema)
        assert "id" in loaded.columns
        assert "value" in loaded.columns

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_schema_from_yaml(tmp_path / "does_not_exist.yaml")

    @pytest.mark.integration
    def test_catalog_register_from_yaml(self, simple_schema, tmp_path):
        yaml_path = tmp_path / "schema.yaml"
        yaml_path.write_text(simple_schema.to_yaml())

        catalog = PanderaCatalog()
        schema = load_schema_from_yaml(yaml_path)
        catalog.register("from_yaml", schema)

        assert "from_yaml" in catalog


class TestLoadSchemaFromDict:
    def test_load_from_dict(self):
        definition = {
            "schema_type": "DataFrameSchema",
            "version": pandera.__version__,
            "columns": {
                "score": {
                    "title": None,
                    "description": None,
                    "dtype": "float64",
                    "nullable": False,
                    "checks": None,
                    "unique": False,
                    "coerce": False,
                    "required": True,
                    "regex": False,
                }
            },
            "checks": None,
            "index": None,
            "dtype": None,
            "coerce": False,
            "strict": False,
            "name": None,
            "ordered": False,
            "unique": None,
            "report_duplicates": "all",
            "unique_column_names": False,
            "add_missing_columns": False,
            "title": None,
            "description": None,
        }
        schema = load_schema_from_dict(definition)
        assert isinstance(schema, pa.DataFrameSchema)
