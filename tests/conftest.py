"""Root conftest for pandera-catalog tests.

Marker conventions (also registered in pyproject.toml):
- integration  : tests that cross module boundaries (e.g., catalog + YAML I/O)
- slow         : expensive tests excluded from the default fast lane

Default fast lane (excludes slow)::

    pytest -m "not slow"

Include integration tests::

    pytest -m "integration"
"""
from __future__ import annotations

import pytest
import pandera.pandas as pa


@pytest.fixture()
def simple_schema() -> pa.DataFrameSchema:
    """A minimal Pandera DataFrameSchema for use in tests."""
    return pa.DataFrameSchema(
        columns={
            "id": pa.Column(int, nullable=False),
            "value": pa.Column(float, pa.Check.greater_than(0)),
        }
    )


@pytest.fixture()
def tagged_schema() -> pa.DataFrameSchema:
    """A schema with string columns, for tagged registration tests."""
    return pa.DataFrameSchema(
        columns={
            "name": pa.Column(str),
            "category": pa.Column(str),
        }
    )
