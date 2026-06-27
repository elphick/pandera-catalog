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
