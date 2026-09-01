from __future__ import annotations

import gc
from pathlib import Path
import weakref

from text2ifc_ifc_repair import api as api_module


def test_source_schema_probe_does_not_retain_open_model(
    monkeypatch,
    tmp_path: Path,
) -> None:
    released_model: list[weakref.ReferenceType[object]] = []

    class _Model:
        schema = "IFC2X3"

    def open_model(_path: str) -> _Model:
        model = _Model()
        released_model.append(weakref.ref(model))
        return model

    monkeypatch.setattr(api_module.ifcopenshell, "open", open_model)

    assert api_module._source_ifc_schema(tmp_path / "source.ifc") == "IFC2X3"
    gc.collect()

    assert released_model[0]() is None