"""Build and verify the authorized BIMNet IFC2X3 extraction audit."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / ".deps" / "python312"))

from text2ifc_extractor import extract_ifc2x3  # noqa: E402
from text2ifc_extractor.inventory import verify_inventory  # noqa: E402


MANIFEST_PATH = ROOT / "dataset" / "manifests" / "bimnet-ifc2x3.jsonl"
OUTPUT_DIR = ROOT / "dataset" / "processed" / "bim-json-2.0"
AUDIT_PATH = OUTPUT_DIR / "extraction-audit.json"
FAMILIES_PATH = OUTPUT_DIR / "scene-families.json"
EXPECTED_FILE_COUNT = 25
APPROVED_USES = [
    "local-extraction",
    "dataset-construction",
    "baseline-evaluation",
    "local-model-training",
]
AUTHORIZATION = {
    "basis": "user-confirmed Matterport3D/BIMNet authorization",
    "confirmed_at": "2026-06-11",
    "redistribution_inferred": False,
    "scope": APPROVED_USES,
}


def _source_paths() -> list[Path]:
    paths = sorted((ROOT / "dataset" / "ifc").glob("*/*.ifc"))
    if len(paths) != EXPECTED_FILE_COUNT:
        raise ValueError(
            f"expected {EXPECTED_FILE_COUNT} BIMNet IFC files, found {len(paths)}"
        )
    return paths


def _scene_family(path: Path) -> str:
    return path.stem.split("_", 1)[0]


def _file_id(path: Path) -> str:
    return f"bimnet-ifc2x3-{path.stem}"


def _relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _upstream_path(path: Path) -> str:
    return path.relative_to(ROOT / "dataset").as_posix()


def _empty_inventory() -> dict[str, dict[str, int]]:
    return {
        category: {"source": 0, "represented": 0, "reported": 0}
        for category in (
            "entities",
            "relationships",
            "properties",
            "representations",
            "materials",
            "types",
            "connections",
        )
    }


def _add_inventory(
    target: dict[str, dict[str, int]],
    source: dict[str, dict[str, int]],
) -> None:
    verify_inventory(source)
    if set(target) != set(source):
        raise ValueError("extraction inventory categories drifted")
    for category, record in source.items():
        for field in ("source", "represented", "reported"):
            target[category][field] += record[field]


def _extract_summary(path_value: str) -> dict[str, Any]:
    result = extract_ifc2x3(path_value)
    payload = result.draft or result.document
    if payload is None:
        raise ValueError(f"extractor returned no output for {path_value}")
    losses = result.losses
    missing_facts = (
        result.draft.get("missing_facts", [])
        if result.draft is not None
        else []
    )
    return {
        "source_sha256": result.source_sha256,
        "ifc_schema": payload["provenance"]["ifc_schema"],
        "status": "draft" if result.draft is not None else "formal",
        "inventory": result.inventory,
        "loss_count": len(losses),
        "loss_counts": dict(
            sorted(Counter(item["kind"] for item in losses).items())
        ),
        "missing_fact_count": len(missing_facts),
    }


def build_outputs() -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    manifest: list[dict[str, Any]] = []
    files: list[dict[str, Any]] = []
    aggregate_inventory = _empty_inventory()
    aggregate_losses: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    family_files: dict[str, list[str]] = defaultdict(list)

    paths = _source_paths()
    with ProcessPoolExecutor(max_workers=min(6, len(paths))) as executor:
        summaries = executor.map(
            _extract_summary, (str(path) for path in paths)
        )

    for path, summary in zip(paths, summaries, strict=True):
        if summary["ifc_schema"] != "IFC2X3":
            raise ValueError(f"unexpected schema for {_relative(path)}")

        file_id = _file_id(path)
        family = _scene_family(path)
        manifest.append(
            {
                "id": file_id,
                "source_repository": "LydJason/BIMNet",
                "source_revision": None,
                "source_path": _upstream_path(path),
                "retrieved_at": None,
                "license": "user-authorized-local-use",
                "local_path": _relative(path),
                "sha256": summary["source_sha256"],
                "declared_schema": "IFC2X3",
                "validation": "ifcopenshell-opened-and-audited",
                "approved_uses": APPROVED_USES,
                "training_eligible": True,
                "scene_family": family,
                "authorization": AUTHORIZATION,
            }
        )
        family_files[family].append(file_id)

        loss_counts = Counter(summary["loss_counts"])
        aggregate_losses.update(loss_counts)
        status = summary["status"]
        status_counts[status] += 1
        _add_inventory(aggregate_inventory, summary["inventory"])
        files.append(
            {
                "id": file_id,
                "local_path": _relative(path),
                "scene_family": family,
                "sha256": summary["source_sha256"],
                "status": status,
                "inventory": summary["inventory"],
                "loss_count": summary["loss_count"],
                "loss_counts": dict(sorted(loss_counts.items())),
                "missing_fact_count": summary["missing_fact_count"],
            }
        )

    verify_inventory(aggregate_inventory)
    manifest.sort(key=lambda item: item["id"])
    files.sort(key=lambda item: item["id"])
    audit = {
        "schema_version": "text2ifc/extraction-audit-v1",
        "source_manifest": _relative(MANIFEST_PATH),
        "file_count": len(files),
        "files": files,
        "aggregate": {
            "inventory": aggregate_inventory,
            "loss_count": sum(aggregate_losses.values()),
            "loss_counts": dict(sorted(aggregate_losses.items())),
            "status_counts": dict(sorted(status_counts.items())),
        },
    }
    families = {
        "schema_version": "text2ifc/scene-families-v1",
        "source_manifest": _relative(MANIFEST_PATH),
        "split_assignment": None,
        "families": [
            {
                "scene_family": family,
                "file_ids": sorted(file_ids),
            }
            for family, file_ids in sorted(family_files.items())
        ],
    }
    return manifest, audit, families


def _render_json(payload: Any) -> str:
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
        + "\n"
    )


def _render_manifest(records: list[dict[str, Any]]) -> str:
    return "".join(
        json.dumps(
            record,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
        for record in records
    )


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _render_outputs() -> dict[Path, str]:
    manifest, audit, families = build_outputs()
    return {
        MANIFEST_PATH: _render_manifest(manifest),
        AUDIT_PATH: _render_json(audit),
        FAMILIES_PATH: _render_json(families),
    }


def write_outputs() -> None:
    for path, content in _render_outputs().items():
        _atomic_write(path, content)


def check_outputs() -> None:
    for path, expected in _render_outputs().items():
        if not path.is_file():
            raise ValueError(f"missing generated audit output: {_relative(path)}")
        actual = path.read_text(encoding="utf-8")
        if actual != expected:
            raise ValueError(f"generated audit drift: {_relative(path)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true")
    action.add_argument("--check-accounting", action="store_true")
    arguments = parser.parse_args()
    try:
        if arguments.write:
            write_outputs()
        else:
            check_outputs()
    except (OSError, RuntimeError, ValueError) as exc:
        print(
            json.dumps(
                {
                    "error": {
                        "code": "BIMNET_AUDIT_ERROR",
                        "message": f"{type(exc).__name__}: {exc}",
                    }
                },
                sort_keys=True,
            )
        )
        return 2
    print(
        json.dumps(
            {
                "file_count": EXPECTED_FILE_COUNT,
                "mode": "write" if arguments.write else "check",
                "status": "ok",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
