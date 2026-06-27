Catalog View Reader
===================

Use :class:`~pandera_catalog.reader.CatalogViewReader` to query the generated
SQL views and return pandas DataFrames.

.. code-block:: python

   import pandera.pandas as pa

   from pandera_catalog import CatalogViewReader, PanderaCatalog, SqlCatalogBackend

   backend = SqlCatalogBackend("sqlite:///catalog.db")
   catalog = PanderaCatalog(backend=backend)

   catalog.register(
       "sales",
       pa.DataFrameSchema({"id": pa.Column(int), "value": pa.Column(float)}),
   )

   reader = CatalogViewReader(catalog)
   schema_catalog = reader.read_schema_catalog()
   schema_columns = reader.read_schema_columns()

   print(schema_catalog.head())
   print(schema_columns.head())

The reader exposes the following generated views:

- ``v_schema_catalog``
- ``v_schema_columns``
- ``v_schema_checks``
- ``v_projection_steps``
- ``v_metadata_lookup``

If the catalog is not configured with a SQL backend, the reader raises a clear
runtime error instead of returning partial results.
