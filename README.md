<h1 style="display: inline-flex; align-items: center; gap: 0.4rem; margin: 0;">
  <img src="https://raw.githubusercontent.com/elphick/pandera-catalog/main/docs/_static/branding/pandera-catalog.svg" alt="pandera-catalog logo" width="72" style="display: block; margin-top: 20px;" />
  <span>pandera-catalog</span>
</h1>

[![Run Tests](https://github.com/elphick/pandera-catalog/actions/workflows/build_and_test.yml/badge.svg?branch=main)](https://github.com/elphick/pandera-catalog/actions/workflows/build_and_test.yml)
[![PyPI](https://img.shields.io/pypi/v/pandera-catalog?logo=python&logoColor=white)](https://pypi.org/project/pandera-catalog/)
![Coverage](https://raw.githubusercontent.com/elphick/pandera-catalog/main/docs/_static/badges/coverage.svg)
[![Python Versions](https://img.shields.io/pypi/pyversions/pandera-catalog)](https://pypi.org/project/pandera-catalog/)
[![License](https://img.shields.io/github/license/elphick/pandera-catalog?cacheSeconds=86400)](https://pypi.org/project/pandera-catalog/)
[![Open Issues](https://img.shields.io/github/issues/elphick/pandera-catalog?cacheSeconds=86400)](https://github.com/elphick/pandera-catalog/issues)

## Overview

`pandera-catalog` is a Python package that provides a database-backed catalog for registering, looking up, and
managing [Pandera](https://pandera.readthedocs.io/) schemas. It is designed to grow into a SQLAlchemy-connected
(SQLite initially) registry of schema entries, validation rules, and schema metadata — keeping schemas
organized, discoverable, and version-aware.

## Installation

Install the base package:

```bash
pip install pandera-catalog
```

Or with `uv`:

```bash
uv add pandera-catalog
```

Install optional extras for schema validation helpers using Pydantic:

```bash
pip install "pandera-catalog[schema]"
```

## Quick Usage

```python
import pandera.pandas as pa
from pandera_catalog import PanderaCatalog

# Create a catalog
catalog = PanderaCatalog()

# Define a schema
schema = pa.DataFrameSchema(
    columns={
        "id": pa.Column(int),
        "value": pa.Column(float, pa.Check.greater_than(0)),
    }
)

# Register the schema
catalog.register("my_schema", schema)

# Look up the schema
retrieved = catalog.get("my_schema")
print(retrieved)

# List all registered schemas
print(catalog.list())
```

## Loading schemas from YAML

```python
from pathlib import Path
from pandera_catalog import PanderaCatalog
from pandera_catalog.schemas import load_schema_from_yaml

catalog = PanderaCatalog()
schema = load_schema_from_yaml(Path("schemas/my_schema.yaml"))
catalog.register("my_schema", schema)
```

See the [documentation](https://elphick.github.io/pandera-catalog/) and
[examples](examples/) for more detail.
