Schema Lifecycle
================

Removing schemas
----------------

Use :meth:`~pandera_catalog.catalog.PanderaCatalog.remove` to unregister a
schema by name.

.. code-block:: python

   catalog.remove("my_schema")
