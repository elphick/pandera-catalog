"""
Basic Catalog Usage
===================

This example demonstrates how to create a :class:`~pandera_catalog.PanderaCatalog`,
register Pandera schemas with optional metadata, and then look them up.
"""

# %%
# Setup
# -----
# Import the catalog and pandera.

import pandera.pandas as pa
from pandera_catalog import PanderaCatalog

# %%
# Create a catalog
# ----------------

catalog = PanderaCatalog()
print(f"Empty catalog: {catalog}")

# %%
# Define schemas
# --------------

sales_schema = pa.DataFrameSchema(
    columns={
        "date": pa.Column(str, nullable=False),
        "product_id": pa.Column(int, nullable=False),
        "quantity": pa.Column(int, pa.Check.greater_than(0)),
        "revenue": pa.Column(float, pa.Check.greater_than_or_equal_to(0.0)),
    },
    name="sales",
)

inventory_schema = pa.DataFrameSchema(
    columns={
        "product_id": pa.Column(int, nullable=False),
        "stock_level": pa.Column(int, pa.Check.greater_than_or_equal_to(0)),
    },
    name="inventory",
)

# %%
# Register schemas
# ----------------
# You can attach an optional description and tags to each entry.

catalog.register(
    "sales",
    sales_schema,
    description="Daily sales transactions",
    tags=["finance", "production"],
)
catalog.register(
    "inventory",
    inventory_schema,
    description="Current warehouse stock levels",
    tags=["operations"],
)

print(f"Registered schemas: {catalog.list()}")

# %%
# Look up a schema
# ----------------

retrieved = catalog.get("sales")
print(f"Retrieved: {type(retrieved).__name__}")

# %%
# Inspect a full catalog entry
# ----------------------------

entry = catalog.get_entry("sales")
print(f"Entry name: {entry.name}")
print(f"Description: {entry.description}")
print(f"Tags: {entry.tags}")

# %%
# Validate a DataFrame
# --------------------
# Once you have the schema you can validate a DataFrame as usual.

import pandas as pd

df = pd.DataFrame(
    {
        "date": ["2024-01-01", "2024-01-02"],
        "product_id": [1, 2],
        "quantity": [10, 5],
        "revenue": [99.9, 49.5],
    }
)

validated_df = catalog.get("sales").validate(df)
print(validated_df)

# %%
# Remove a schema
# ---------------

catalog.remove("inventory")
print(f"After removal: {catalog.list()}")
