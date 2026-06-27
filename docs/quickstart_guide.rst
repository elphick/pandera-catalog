Quickstart Guide
================

Use this page to get productive quickly. For detailed, topic-based guidance,
see :doc:`user_guide/index`.

Create and register your first schema
-------------------------------------

.. code-block:: python

   import pandera.pandas as pa
   from pandera_catalog import PanderaCatalog

   catalog = PanderaCatalog()
   schema = pa.DataFrameSchema(columns={"value": pa.Column(float)})
   catalog.register("my_schema", schema)

   print(catalog.list())
   # ['my_schema']

Next steps
----------

1. Read :doc:`user_guide/00_catalog_basics` for core catalog operations.
2. Read :doc:`user_guide/01_schema_projections` for projection composition.
3. Explore runnable examples in :doc:`auto_examples/index`.
