"""Shared type aliases, dataclasses, and protocol helpers for pandera-catalog."""
from __future__ import annotations

from dataclasses import dataclass, field
import pandera.pandas as pa


@dataclass
class SchemaEntry:
    """A catalog entry wrapping a Pandera schema with metadata.

    Attributes
    ----------
    name:
        Unique name of the schema within the catalog.
    schema:
        The Pandera :class:`~pandera.DataFrameSchema` instance.
    description:
        Optional human-readable description.
    tags:
        Optional list of string tags for categorisation or filtering.
    """

    name: str
    schema: pa.DataFrameSchema
    description: str | None = None
    tags: list[str] = field(default_factory=list)

    def __repr__(self) -> str:
        tag_str = f", tags={self.tags!r}" if self.tags else ""
        desc_str = f", description={self.description!r}" if self.description else ""
        return f"SchemaEntry(name={self.name!r}{desc_str}{tag_str})"


@dataclass
class SchemaProjectionEntry:
    """A named projection built from ordered schema selection steps."""

    name: str
    steps: list["SchemaProjectionStep"]
    description: str | None = None

    def __repr__(self) -> str:
        desc_str = f", description={self.description!r}" if self.description else ""
        return (
            f"SchemaProjectionEntry(name={self.name!r}, steps={self.steps!r}{desc_str})"
        )


@dataclass
class SchemaProjectionStep:
    """A single schema projection step."""

    schema: str
    kind: str
    names: list[str]


__all__ = ["SchemaEntry", "SchemaProjectionEntry", "SchemaProjectionStep"]
