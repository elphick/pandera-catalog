"""
Catalog View Reader
===================

This example shows how to query the generated SQL views through
``CatalogViewReader`` and work with the returned pandas ``DataFrame`` objects.
"""
import pandas as pd
# %%
# Setup
# -----
import pandera.pandas as pa

from pandera_catalog import CatalogViewReader, PanderaCatalog, SqlCatalogBackend

# %%
# Create a SQL-backed catalog
# ---------------------------
backend = SqlCatalogBackend("sqlite:///catalog.db")
catalog = PanderaCatalog(backend=backend)

catalog.register(
    "sales",
    pa.DataFrameSchema(
        {
            "id": pa.Column(int),
            "value": pa.Column(float, pa.Check.greater_than(0)),
        }
    ),
    tags=["finance"],
    overwrite=True  # for repeated runs of the example
)
catalog.register_projection(
    "sales_reporting",
    [{"schema": "sales", "kind": "columns", "names": ["id", "value"]}],
    overwrite=True  # for repeated runs of the example
)

# %%
# Query the generated views
# -------------------------
reader = CatalogViewReader(catalog)
schema_catalog: pd.DataFrame = reader.read_schema_catalog()
projection_steps: pd.DataFrame = reader.read_projection_steps()
schema_columns: pd.DataFrame = reader.read_schema_columns()

# %%
schema_catalog

# %%
projection_steps

#%%
schema_columns


