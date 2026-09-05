"""Build a deterministic technical certification slice for canonical IFC2X3 sources."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from text2ifc_dataset.source_manifests import render_jsonl
from text2ifc_text.splits import atomic_write_text

FILES_PATH = ROOT / "dataset/manifests/ifc-files.jsonl"
OUTPUT_PATH = ROOT / "dataset/manifests/ifc2x3-certified.jsonl"
CERTIFICATION_PROFILE = "text2ifc/ifc2x3-technical-certification/1.0"


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def build_records() -> list[dict]:
    records = _read_jsonl(FILES_PATH)
    certified: list[dict] = []
    seen_sha: set[str] = set()
    for record in records:
        if record.get("declared_schema") != "IFC2X3":
            continue
        sha256 = str(record.get("sha256", ""))
        if len(sha256) != 64:
            raise RuntimeError(f"INVALID_SHA:{record.get('id')}")
        if sha256 in seen_sha:
            raise RuntimeError(f"DUPLICATE_CANONICAL_SHA:{sha256}")
        seen_sha.add(sha256)

        path = ROOT / str(record["local_path"])
        if not path.is_file():
            raise RuntimeError(f"MISSING_FILE:{record['local_path']}")
        validation = record.get("validation") or {}
        gates = {
            "schema_ifc2x3": True,
            "canonical_sha_unique": True,
            "file_exists": True,
            "ifcopenshell_parse": validation.get("ifcopenshell_parse") is True,
            "entity_traversal": validation.get("entity_traversal") is True,
            "roundtrip_write": validation.get("roundtrip_write") is True,
            "roundtrip_reopen": validation.get("roundtrip_reopen") is True,
        }
        if not all(gates.values()):
            continue

        certified.append(
            {
                "schema_version": CERTIFICATION_PROFILE,
                "certification": "IFC2X3_CERTIFIED",
                "id": record["id"],
                "source_id": record["source_id"],
                "source_family": record.get("source_family"),
                "local_path": record["local_path"],
                "sha256": sha256,
                "size_bytes": record.get("size_bytes"),
                "entity_count": record.get("entity_count"),
                "entity_counts": record.get("entity_counts", {}),
                "gates": gates,
                "research_use": (
                    "authorized" if record.get("source_id") == "bimnet" else "source_policy"
                ),
                "training_use": record.get("training_use"),
                "redistribution": record.get("redistribution"),
                "permission_note": "Technical certification does not grant training or redistribution rights.",
            }
        )
    return sorted(certified, key=lambda item: item["id"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    records = build_records()
    rendered = render_jsonl(records)
    if args.check:
        if not OUTPUT_PATH.is_file() or OUTPUT_PATH.read_text(encoding="utf-8") != rendered:
            raise SystemExit("IFC2X3_CERTIFIED_MANIFEST_DRIFT")
    elif args.write:
        atomic_write_text(OUTPUT_PATH, rendered)
    else:
        print(rendered, end="")

    by_source: dict[str, int] = {}
    for record in records:
        by_source[record["source_id"]] = by_source.get(record["source_id"], 0) + 1
    print(json.dumps({"certified_count": len(records), "by_source": dict(sorted(by_source.items()))}, indent=2, sort_keys=True), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
