Developer Testing Guide
=======================

This page describes how we use pytest markers and how to run the test suite.

Marker conventions
------------------

Use the following markers consistently:

- ``@pytest.mark.integration``
  For tests that exercise multiple layers together (e.g., catalog registration
  combined with YAML schema loading).

- ``@pytest.mark.slow``
  For expensive tests that are valuable but too costly for the default fast lane.

Keep unit tests (fast, deterministic, no external dependencies) unmarked.

Example usage::

   import pytest

   @pytest.mark.integration
   def test_catalog_register_from_yaml(...):
       ...

   @pytest.mark.slow
   def test_large_catalog_performance(...):
       ...

How to run subsets
------------------

Default fast lane::

   pytest -m "not slow"

Include integration tests::

   pytest -m "integration"

Run everything::

   pytest

Using ``uv``
------------

Run tests via ``uv``::

   uv run pytest

Run with coverage::

   uv run pytest --cov=pandera_catalog --cov-report=term-missing

Build the docs::

   uv run sphinx-build docs docs/_build/html
