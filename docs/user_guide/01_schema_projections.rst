Schema Projections
==================

A **Schema Projection** defines a named exported schema from ordered steps.
Each step uses ``schema``, ``kind``, and ``names``.

Registering a projection
------------------------

Use :meth:`~pandera_catalog.catalog.PanderaCatalog.register_projection` to
register a projection, then
:meth:`~pandera_catalog.catalog.PanderaCatalog.export_projection` to materialise
the projected :class:`pandera.DataFrameSchema`.

.. code-block:: python

   catalog.register_projection(
       "reporting_projection",
       steps=[
           {
               "schema": "sensor_readings",
               "kind": "columns",
               "names": ["site", "sensor_id", "temperature"],
           }
       ],
       description="Columns used by reporting consumers",
   )

   projected = catalog.export_projection("reporting_projection")
   print(list(projected.columns.keys()))
   # ['site', 'sensor_id', 'temperature']

Validation behavior
-------------------

- Unknown step kinds raise :class:`ValueError`.
- Unknown columns raise :class:`ValueError`.
- Duplicate projected columns across steps raise :class:`ValueError`.
- Missing schema references or duplicate projection names raise :class:`KeyError`.
- ``kind: group`` is reserved for future support and currently raises
  :class:`NotImplementedError` during registration.
