from importlib import metadata

from .backend import SqlCatalogBackend
from .catalog import PanderaCatalog
from .schemas import load_schema_from_yaml
from .reader import CatalogViewReader
from .types import SchemaEntry, SchemaProjectionEntry, SchemaProjectionStep

try:
    __version__ = metadata.version("pandera_catalog")
except metadata.PackageNotFoundError:
    __version__ = "0.0.0.dev0"

__all__ = [
    "PanderaCatalog",
    "SqlCatalogBackend",
    "CatalogViewReader",
    "load_schema_from_yaml",
    "SchemaEntry",
    "SchemaProjectionEntry",
    "SchemaProjectionStep",
    "__version__",
]
