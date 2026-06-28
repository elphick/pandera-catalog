Catalog Basics
==============

A :class:`~pandera_catalog.catalog.PanderaCatalog` is the central in-memory
registry for Pandera schemas.

Registering schemas
-------------------

Use :meth:`~pandera_catalog.catalog.PanderaCatalog.register` to add schemas.
Each schema name must be unique unless ``overwrite=True`` is used.

.. code-block:: python

   catalog.register(
       "sales_data",
       schema,
       description="Schema for the daily sales feed",
       tags=["finance", "production"],
   )

Looking up schemas
------------------

Use :meth:`~pandera_catalog.catalog.PanderaCatalog.get` for the schema, or
:meth:`~pandera_catalog.catalog.PanderaCatalog.get_entry` for metadata too.

.. code-block:: python

   schema = catalog.get("sales_data")
   entry = catalog.get_entry("sales_data")
   print(entry.description)

Listing schemas
---------------

:meth:`~pandera_catalog.catalog.PanderaCatalog.list` returns sorted schema
names.

.. code-block:: python

   print(catalog.list())
   # ['my_schema', 'sales_data']

Using a SQL backend
-------------------

To persist entries and expose tabular SQL views, pass a
:class:`~pandera_catalog.backend.SqlCatalogBackend` into the catalog:

.. code-block:: python

   from pandera_catalog import PanderaCatalog, SqlCatalogBackend
   from sqlalchemy import create_engine

   engine = create_engine("postgresql+psycopg://user:pass@host/dbname")
   backend = SqlCatalogBackend(engine=engine)
   catalog = PanderaCatalog(backend=backend)

The backend creates normalized tables plus views including
``v_schema_catalog``, ``v_schema_columns``, ``v_schema_checks``,
``v_projection_steps``, and ``v_metadata_lookup``. Projected schemas are
materialized into schema/column/check views with ``is_projected`` and
``source_projection_name`` markers.

If you do not already have an engine, you can still pass a URL string and let
the backend create one for you.
