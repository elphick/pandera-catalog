"""Schema loading helpers for pandera-catalog.

This module provides utilities for loading Pandera schemas from YAML files
and from plain Python dictionaries.
"""
from __future__ import annotations

from pathlib import Path
from typing import Union

import pandera.pandas as pa
import yaml


def load_schema_from_yaml(path: Union[str, Path]) -> pa.DataFrameSchema:
    """Load a Pandera :class:`~pandera.DataFrameSchema` from a YAML file.

    The YAML file must follow the format produced by
    :meth:`pandera.DataFrameSchema.to_yaml`.

    Parameters
    ----------
    path:
        Path to the ``.yaml`` (or ``.yml``) schema definition file.

    Returns
    -------
    pandera.DataFrameSchema

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    ValueError
        If the file cannot be parsed as a Pandera schema.

    Examples
    --------
    >>> from pathlib import Path
    >>> from pandera_catalog.schemas import load_schema_from_yaml
    >>> schema = load_schema_from_yaml(Path("schemas/my_schema.yaml"))
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")
    return pa.DataFrameSchema.from_yaml(path)


def load_schema_from_dict(definition: dict) -> pa.DataFrameSchema:
    """Build a Pandera :class:`~pandera.DataFrameSchema` from a dictionary.

    The dictionary must follow the same structure as Pandera's YAML
    serialisation format.

    Parameters
    ----------
    definition:
        Mapping that describes the schema (columns, checks, etc.).

    Returns
    -------
    pandera.DataFrameSchema

    Examples
    --------
    >>> from pandera_catalog.schemas import load_schema_from_dict
    >>> defn = {"columns": {"value": {"dtype": "float64"}}}
    >>> schema = load_schema_from_dict(defn)
    """
    yaml_str = yaml.dump(definition)
    return pa.DataFrameSchema.from_yaml(yaml_str)


__all__ = [
    "load_schema_from_yaml",
    "load_schema_from_dict",
]
