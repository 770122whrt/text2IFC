"""Compatibility entry point; implementation lives in text2ifc_proof."""
from __future__ import annotations

import sys
from pathlib import Path
from importlib import import_module

ROOT = Path(__file__).resolve().parents[2]
for _path in (str(ROOT), str(ROOT / "src")):
    if _path not in sys.path:
        sys.path.insert(0, _path)

_implementation = import_module("text2ifc_proof.audit_door_repair_triplet")


def __getattr__(name: str):
    return getattr(_implementation, name)


if __name__ == "__main__":
    raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
