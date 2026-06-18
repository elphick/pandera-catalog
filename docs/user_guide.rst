User Guide
==========

The purpose of this guide is to walk the user through how to use the package.
It is complemented by the examples.

.. note::

   This is a work in progress and not all features are documented yet.
   Please check back later for updates.

Creating a Catalog
------------------

A :class:`~pandera_catalog.catalog.PanderaCatalog` is the central object.
It acts as an in-memory registry for Pandera schemas — keyed by a unique
name — and is designed to grow into a SQLAlchemy-backed persistent store.

.. code-block:: python

   import pandera.pandas as pa
   from pandera_catalog import PanderaCatalog

   catalog = PanderaCatalog()

   schema = pa.DataFrameSchema(
       columns={"value": pa.Column(float, pa.Check.greater_than(0))}
   )
   catalog.register("my_schema", schema)

Registering schemas
-------------------

Use :meth:`~pandera_catalog.catalog.PanderaCatalog.register` to add a schema
to the catalog.  Each schema must have a unique name within the catalog.
Optional ``description`` and ``tags`` metadata can be attached:

.. code-block:: python

   catalog.register(
       "sales_data",
       schema,
       description="Schema for the daily sales feed",
       tags=["finance", "production"],
   )

Looking up schemas
------------------

Use :meth:`~pandera_catalog.catalog.PanderaCatalog.get` to retrieve a schema
by name, or :meth:`~pandera_catalog.catalog.PanderaCatalog.get_entry` to
retrieve the full :class:`~pandera_catalog.types.SchemaEntry` record
(including metadata):

.. code-block:: python

   schema = catalog.get("sales_data")
   entry = catalog.get_entry("sales_data")
   print(entry.description)

Listing schemas
---------------

:meth:`~pandera_catalog.catalog.PanderaCatalog.list` returns a sorted list of
all registered schema names:

.. code-block:: python

   print(catalog.list())
   # ['my_schema', 'sales_data']

Loading schemas from YAML
--------------------------

Pandera supports serialising schemas to YAML.
:func:`~pandera_catalog.schemas.load_schema_from_yaml` loads a schema from
such a file and returns a standard :class:`pandera.DataFrameSchema`:

.. code-block:: python

   from pathlib import Path
   from pandera_catalog.schemas import load_schema_from_yaml

   schema = load_schema_from_yaml(Path("schemas/my_schema.yaml"))
   catalog.register("my_schema", schema)

Removing schemas
----------------

Use :meth:`~pandera_catalog.catalog.PanderaCatalog.remove` to unregister a
schema:

.. code-block:: python

   catalog.remove("my_schema")
