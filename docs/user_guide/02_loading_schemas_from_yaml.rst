Loading Schemas from YAML
=========================

Pandera supports serialising schemas to YAML.
:func:`~pandera_catalog.schemas.load_schema_from_yaml` loads a schema from YAML
and returns a :class:`pandera.DataFrameSchema`.

.. code-block:: python

   from pathlib import Path
   from pandera_catalog.schemas import load_schema_from_yaml

   schema = load_schema_from_yaml(Path("schemas/my_schema.yaml"))
   catalog.register("my_schema", schema)
