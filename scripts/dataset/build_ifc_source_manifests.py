"""Generate deterministic canonical Source IFC manifests."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from text2ifc_dataset.source_manifests import (
    build_file_records,
    build_source_payload,
    manifest_summary,
    render_json,
    render_jsonl,
    validate_records,
)
from text2ifc_text.splits import atomic_write_text


SOURCES_PATH = ROOT / "dataset" / "manifests" / "ifc-sources.json"
FILES_PATH = ROOT / "dataset" / "manifests" / "ifc-files.jsonl"
SUMMARY_PATH = ROOT / "dataset" / "manifests" / "ifc-source-summary.json"


def _bimnet_compatibility_projection(root: Path, records: list[dict]) -> str:
    """Generate the legacy BIMNet projection from canonical records.

    The existing manifest supplies historical source metadata while canonical file
    path/hash/schema come from the generated source inventory. This keeps old
    consumers stable during the migration without making the legacy manifest an
    independent authority.
    """

    manifest = root / "dataset" / "manifests" / "bimnet-ifc2x3.jsonl"
    prior: dict[str, dict] = {}
    if manifest.is_file():
        prior = {
            item["id"]: item
            for line in manifest.read_text(encoding="utf-8").splitlines()
            if line.strip()
            for item in [json.loads(line)]
        }

    projected: list[dict] = []
    for record in records:
        if record.get("source_id") != "bimnet":
            continue
        item = dict(prior.get(record["id"], {}))
        item.update(
            {
                "id": record["id"],
                "local_path": record["local_path"],
                "sha256": record["sha256"],
                "declared_schema": "IFC2X3",
                "scene_family": record["source_family"],
                "license": "user-authorized-local-use",
                "approved_uses": [
                    "local-extraction",
                    "dataset-construction",
                    "baseline-evaluation",
                    "local-model-training",
                ],
                "training_eligible": True,
                "validation": "ifcopenshell-opened-and-audited",
            }
        )
        projected.append(item)
    return render_jsonl(sorted(projected, key=lambda item: item["id"]))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--no-probe", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    sources = build_source_payload(root)
    records = build_file_records(root, probe=not args.no_probe)
    validate_records(records, root)
    summary = manifest_summary(records)

    rendered = {
        root / "dataset" / "manifests" / "ifc-sources.json": render_json(sources),
        root / "dataset" / "manifests" / "ifc-files.jsonl": render_jsonl(records),
        root / "dataset" / "manifests" / "ifc-source-summary.json": render_json(summary),
        root / "dataset" / "manifests" / "bimnet-ifc2x3.jsonl": _bimnet_compatibility_projection(root, records),
    }

    if args.check:
        drift = [
            path.relative_to(root).as_posix()
            for path, text in rendered.items()
            if not path.is_file() or path.read_text(encoding="utf-8") != text
        ]
        if drift:
            raise SystemExit("IFC_SOURCE_MANIFEST_DRIFT:" + ",".join(drift))
        return 0

    if args.write:
        for path, text in rendered.items():
            atomic_write_text(path, text)
        return 0

    print(render_json({"sources": sources, "summary": summary}), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
