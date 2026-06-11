"""IFC PSD registry API skeleton for the RED phase."""

from __future__ import annotations


class PsdParseError(ValueError):
    pass


def build_property_registry(archive_path):
    return {"counts": {}, "property_sets": {}}
