"""
Loading a Schema from YAML
===========================

This example shows how to serialise a Pandera schema to YAML, then reload it
via :func:`~pandera_catalog.schemas.load_schema_from_yaml` and register it in
a :class:`~pandera_catalog.PanderaCatalog`.
"""

# %%
# Setup
# -----

from pathlib import Path
import tempfile

import pandera.pandas as pa
from pandera_catalog import PanderaCatalog
from pandera_catalog.schemas import load_schema_from_yaml

# %%
# Define and serialise a schema to YAML
# --------------------------------------
# Pandera has built-in YAML serialisation via ``.to_yaml()``.

schema = pa.DataFrameSchema(
    columns={
        "sensor_id": pa.Column(str, nullable=False),
        "temperature": pa.Column(
            float,
            checks=[
                pa.Check.greater_than(-50.0),
                pa.Check.less_than(100.0),
            ],
        ),
        "humidity": pa.Column(
            float,
            checks=pa.Check.in_range(0.0, 100.0),
            nullable=True,
        ),
    },
    name="sensor_readings",
)

# Write the schema to a temporary YAML file.
with tempfile.TemporaryDirectory() as tmp_dir:
    yaml_path = Path(tmp_dir) / "sensor_readings.yaml"
    yaml_path.write_text(schema.to_yaml())

    print("--- YAML content ---")
    print(yaml_path.read_text())

    # %%
    # Load the schema back from YAML
    # --------------------------------

    loaded_schema = load_schema_from_yaml(yaml_path)
    print(f"Loaded schema type: {type(loaded_schema).__name__}")
    print(f"Columns: {list(loaded_schema.columns.keys())}")

    # %%
    # Register in the catalog
    # ------------------------

    catalog = PanderaCatalog()
    catalog.register("sensor_readings", loaded_schema, tags=["iot", "sensors"])

    print(f"Catalog contents: {catalog.list()}")
    entry = catalog.get_entry("sensor_readings")
    print(f"Tags: {entry.tags}")

# %%
# Validate data with the loaded schema
# -------------------------------------

import pandas as pd

df = pd.DataFrame(
    {
        "sensor_id": ["S001", "S002"],
        "temperature": [22.5, 18.3],
        "humidity": [55.0, None],
    }
)

validated = catalog.get("sensor_readings").validate(df)
print(validated)
