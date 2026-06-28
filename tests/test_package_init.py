from __future__ import annotations

import importlib

import pandera_catalog


def test_version_fallback(monkeypatch):
    def boom(_name: str) -> str:
        raise pandera_catalog.metadata.PackageNotFoundError

    monkeypatch.setattr(pandera_catalog.metadata, "version", boom)
    module = importlib.reload(pandera_catalog)

    assert module.__version__ == "0.0.0.dev0"
