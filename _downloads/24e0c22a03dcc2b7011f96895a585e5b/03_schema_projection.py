"""
Schema Projection (Explicit Columns)
====================================

This example shows how to register a Schema Projection from ordered steps, then
export that projection as a Pandera ``DataFrameSchema``.
"""

# %%
# Setup
# -----
import pandera.pandas as pa

from pandera_catalog import PanderaCatalog

# %%
# Register canonical source schemas
# ---------------------------------
catalog = PanderaCatalog()
sensor_schema = pa.DataFrameSchema(
    columns={
        "sensor_id": pa.Column(str, nullable=False),
        "temperature": pa.Column(float),
        "humidity": pa.Column(float, nullable=True),
        "site": pa.Column(str),
    },
    name="sensor_readings",
)
catalog.register("sensor_readings", sensor_schema)
site_schema = pa.DataFrameSchema(
    columns={
        "country": pa.Column(str),
        "site": pa.Column(str, nullable=False),
    },
    name="site_metadata",
)
catalog.register("site_metadata", site_schema)

# %%
# Register a projection with ordered steps
# ----------------------------------------
catalog.register_projection(
    name="reporting_projection",
    steps=[
        {"schema": "site_metadata", "kind": "columns", "names": ["country"]},
        {"schema": "sensor_readings", "kind": "columns", "names": ["site", "sensor_id"]},
        {"schema": "sensor_readings", "kind": "columns", "names": ["temperature"]},
    ],
    description="Columns used by the reporting export",
)
print("Projection names:", catalog.list_projections())
print("Projection entry:", catalog.get_projection_entry("reporting_projection"))

# %%
# Export the projected schema
# ---------------------------
projected_schema = catalog.export_projection("reporting_projection")
print("Exported columns:", list(projected_schema.columns.keys()))
