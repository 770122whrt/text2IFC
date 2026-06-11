"""Check official local sources and generated IFC2X3 registry drift."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from text2ifc_knowledge.registry import check_registry_files  # noqa: E402
from text2ifc_knowledge.sources import (  # noqa: E402
    load_source_manifest,
    verify_source_file,
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    source_manifest_path = (
        ROOT / "schemas" / "ifc" / "IFC2X3_TC1.sources.json"
    )
    source_manifest = load_source_manifest(source_manifest_path)
    express_source = source_manifest.source("ifc2x3-tc1-express")
    verify_source_file(ROOT / express_source.local_path, express_source)

    generated_root = ROOT / "schemas" / "ifc" / "generated" / "IFC2X3"
    registry_manifest = json.loads(
        (generated_root / "registry-manifest.json").read_text(encoding="utf-8")
    )
    actual_source_manifest_hash = _sha256_file(source_manifest_path)
    if registry_manifest.get("source_manifest_sha256") != actual_source_manifest_hash:
        raise SystemExit("source manifest changed; regenerate the IFC2X3 registry")

    checked = check_registry_files(ROOT)
    print(
        "IFC2X3 registry verified: "
        + ", ".join(f"{name}={digest}" for name, digest in sorted(checked.items()))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
