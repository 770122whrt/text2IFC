"""Historical entry point; implementation moved to scripts/ifc_repair/offline."""
from __future__ import annotations

import sys
from pathlib import Path
from importlib import import_module

_ROOT = Path(__file__).resolve().parents[2]
for _path in (str(_ROOT), str(_ROOT / "src")):
    if _path not in sys.path:
        sys.path.insert(0, _path)

_implementation = import_module("scripts.ifc_repair.offline.run_phase11_public_triplet_repair")


def __getattr__(name: str):
    return getattr(_implementation, name)


if __name__ == "__main__":
    raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
