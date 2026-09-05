"""Classify discovered small IFC2X3 candidates by semantic meaningfulness using IfcOpenShell."""

from __future__ import annotations

import concurrent.futures
import json
import ssl
import tempfile
import urllib.request
from pathlib import Path

import certifi
import ifcopenshell

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / ".tmp/dataset-acquisition/ifc2x3-small-github-candidates.jsonl"
OUTPUT = ROOT / ".tmp/dataset-acquisition/ifc2x3-small-github-classified.jsonl"
REPORT = ROOT / "docs/reports/ifc2x3-small-model-meaningfulness.md"
USER_AGENT = "text2ifc-dataset-classifier/1.0"

KEY_CLASSES = (
    "IfcWall",
    "IfcSlab",
    "IfcDoor",
    "IfcWindow",
    "IfcOpeningElement",
    "IfcBeam",
    "IfcColumn",
    "IfcStair",
    "IfcRoof",
    "IfcSpace",
    "IfcFlowTerminal",
    "IfcFlowSegment",
    "IfcFlowFitting",
)


def _download(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    ctx = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(req, timeout=120, context=ctx) as response:
        return response.read()


def _count(model, ifc_class: str) -> int:
    try:
        return len(model.by_type(ifc_class))
    except RuntimeError:
        return 0


def _classify(metrics: dict) -> tuple[str, list[str]]:
    element_count = metrics["element_count"]
    product_count = metrics["product_count"]
    spatial_anchor_count = metrics["site_count"] + metrics["building_count"] + metrics["storey_count"]
    containment_count = metrics["containment_rel_count"]
    key_diversity = metrics["key_class_diversity"]
    project_count = metrics["project_count"]

    reasons: list[str] = []
    if project_count == 0:
        reasons.append("missing_ifc_project")
    if spatial_anchor_count == 0:
        reasons.append("missing_spatial_anchor")
    if containment_count == 0:
        reasons.append("missing_spatial_containment")

    if element_count == 0:
        return "metadata_or_empty", reasons + ["no_ifc_elements"]
    if element_count <= 2:
        return "single_component", reasons + [f"element_count={element_count}"]
    if element_count < 10:
        return "fragment_fixture", reasons + [f"element_count={element_count}"]

    if project_count >= 1 and spatial_anchor_count >= 1 and containment_count >= 1:
        if key_diversity >= 3 or element_count >= 25:
            return "meaningful_model", reasons
        if key_diversity >= 1 and (element_count >= 10 or product_count >= 15):
            return "discipline_model", reasons

    return "fragment_fixture", reasons + [
        f"element_count={element_count}",
        f"key_class_diversity={key_diversity}",
    ]


def _analyze(row: dict) -> dict:
    if row.get("schema") != "IFC2X3" or row.get("status") not in {"new_candidate", "exact_duplicate_local"}:
        return {**row, "meaningfulness": "not_applicable"}

    try:
        data = _download(str(row["raw_url"]))
        with tempfile.TemporaryDirectory(prefix="ifc2x3-small-classify-") as temp_dir:
            path = Path(temp_dir) / "candidate.ifc"
            path.write_bytes(data)
            model = ifcopenshell.open(str(path))
            schema = str(model.schema).upper()
            if schema != "IFC2X3":
                return {**row, "meaningfulness": "invalid", "classification_error": f"schema={schema}"}

            entity_count = sum(1 for _ in model)
            counts = {name: _count(model, name) for name in KEY_CLASSES}
            metrics = {
                "entity_count": entity_count,
                "project_count": _count(model, "IfcProject"),
                "site_count": _count(model, "IfcSite"),
                "building_count": _count(model, "IfcBuilding"),
                "storey_count": _count(model, "IfcBuildingStorey"),
                "space_count": _count(model, "IfcSpace"),
                "product_count": _count(model, "IfcProduct"),
                "element_count": _count(model, "IfcElement"),
                "containment_rel_count": _count(model, "IfcRelContainedInSpatialStructure"),
                "aggregate_rel_count": _count(model, "IfcRelAggregates"),
                "key_class_counts": counts,
                "key_class_diversity": sum(value > 0 for value in counts.values()),
            }
            meaningfulness, reasons = _classify(metrics)
            generation_candidate = (
                meaningfulness == "meaningful_model"
                and row["size_bytes"] < 1024 * 1024
                and metrics["building_count"] >= 1
                and metrics["storey_count"] >= 1
                and metrics["element_count"] >= 10
                and metrics["key_class_diversity"] >= 3
            )
            repair_candidate = meaningfulness in {"meaningful_model", "discipline_model"}
            return {
                **row,
                "meaningfulness": meaningfulness,
                "classification_reasons": reasons,
                "metrics": metrics,
                "generation_reference_candidate": generation_candidate,
                "repair_candidate": repair_candidate,
            }
    except Exception as exc:
        return {
            **row,
            "meaningfulness": "invalid",
            "classification_error": f"{type(exc).__name__}:{exc}",
            "generation_reference_candidate": False,
            "repair_candidate": False,
        }


def main() -> int:
    rows = [json.loads(line) for line in INPUT.read_text(encoding="utf-8").splitlines() if line.strip()]
    candidates = [row for row in rows if row.get("schema") == "IFC2X3"]
    analyzed: list[dict] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(_analyze, row) for row in candidates]
        for index, future in enumerate(concurrent.futures.as_completed(futures), start=1):
            analyzed.append(future.result())
            if index % 25 == 0:
                print(f"CLASSIFY {index}/{len(futures)}", flush=True)

    analyzed.sort(key=lambda row: (row.get("meaningfulness", ""), row.get("size_bytes", 0), row["repo"], row["path"].casefold()))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for row in analyzed), encoding="utf-8")

    counts: dict[str, int] = {}
    for row in analyzed:
        key = str(row.get("meaningfulness"))
        counts[key] = counts.get(key, 0) + 1
    meaningful = [row for row in analyzed if row.get("meaningfulness") in {"meaningful_model", "discipline_model"} and row.get("status") == "new_candidate"]
    generation = [row for row in meaningful if row.get("generation_reference_candidate")]

    lines = [
        "# IFC2X3 Small Candidate Meaningfulness Review",
        "",
        "> Automated IfcOpenShell screening. This is a discovery/admission aid, not a substitute for source/license review.",
        "",
        "## Gate",
        "",
        "- `single_component`: 1–2 `IfcElement` objects.",
        "- `fragment_fixture`: too few elements or missing project/spatial/containment structure.",
        "- `discipline_model`: spatially structured model with at least 10 elements, useful even if category diversity is narrow.",
        "- `meaningful_model`: spatially structured model with at least 10 elements and either >=3 key element classes or >=25 elements.",
        "- Generation reference recommendation additionally requires `<1 MiB`, building + storey, >=10 elements, and >=3 key classes.",
        "",
        "## Summary",
        "",
    ]
    for key in sorted(counts):
        lines.append(f"- `{key}`: **{counts[key]}**")
    lines += [
        f"- New meaningful/discipline candidates: **{len(meaningful)}**",
        f"- New `<1 MiB` Generation reference candidates: **{len(generation)}**",
        "- Machine-readable classification: `dataset/manifests/acquisitions/ifc2x3-small-github-classified.jsonl`",
        "",
        "## Recommended candidates",
        "",
        "| Size (MiB) | Use | Type | Elements | Storeys | Key classes | Repository | Path |",
        "| ---: | --- | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for row in sorted(meaningful, key=lambda item: (not item.get("generation_reference_candidate"), item["size_bytes"], item["repo"], item["path"].casefold())):
        metrics = row["metrics"]
        usage = "generation+repair" if row.get("generation_reference_candidate") else "repair"
        lines.append(
            f"| {row['size_mib']:.3f} | {usage} | `{row['meaningfulness']}` | {metrics['element_count']} | {metrics['storey_count']} | {metrics['key_class_diversity']} | `{row['repo']}` | `{row['path']}` |"
        )
    lines.append("")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({"classified": len(analyzed), "counts": counts, "new_meaningful_or_discipline": len(meaningful), "new_generation_reference": len(generation)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
