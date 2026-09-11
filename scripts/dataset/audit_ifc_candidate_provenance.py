"""Audit that every IFC candidate resolves to source-level provenance evidence."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POOL = ROOT / "dataset/manifests/candidates/ifc-candidate-pool.jsonl"
REGISTRY = ROOT / "dataset/manifests/candidates/source-registry.json"
BIMDATA_EVIDENCE = ROOT / "dataset/manifests/candidates/bimdata-rd-source-evidence.jsonl"
BIMDATA_RESOLUTION = ROOT / "dataset/manifests/candidates/bimdata-rd-resolution.jsonl"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    pool = read_jsonl(POOL)
    registry_payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    registry = {row["source_id"]: row for row in registry_payload["sources"]}
    bimdata = read_jsonl(BIMDATA_EVIDENCE)
    bimdata_paths = {str(row.get("upstream_path")) for row in bimdata}
    bimdata_resolution = read_jsonl(BIMDATA_RESOLUTION)
    bimdata_resolution_paths = {str(row.get("upstream_path")) for row in bimdata_resolution}

    missing_registry: list[dict] = []
    missing_bimdata_evidence: list[dict] = []
    missing_bimdata_resolution: list[dict] = []
    invalid_registry: list[dict] = []
    for source_id, row in registry.items():
        required = (
            "canonical_source",
            "classification",
            "license",
            "model_rights_status",
            "research_use",
            "training_use",
            "redistribution",
            "evidence",
        )
        missing = [field for field in required if not row.get(field)]
        if missing:
            invalid_registry.append({"source_id": source_id, "missing": missing})

    for row in pool:
        source_id = str(row.get("source_id") or "")
        if source_id not in registry:
            missing_registry.append(
                {
                    "source_id": source_id,
                    "upstream_path": row.get("upstream_path"),
                }
            )
        if source_id == "bimdata-rd-index" and str(row.get("upstream_path")) not in bimdata_paths:
            missing_bimdata_evidence.append(
                {
                    "upstream_path": row.get("upstream_path"),
                }
            )
        if source_id == "bimdata-rd-index" and str(row.get("upstream_path")) not in bimdata_resolution_paths:
            missing_bimdata_resolution.append(
                {
                    "upstream_path": row.get("upstream_path"),
                }
            )

    result = {
        "candidate_records": len(pool),
        "registry_sources": len(registry),
        "bimdata_evidence_records": len(bimdata),
        "bimdata_resolution_records": len(bimdata_resolution),
        "missing_registry": missing_registry,
        "missing_bimdata_evidence": missing_bimdata_evidence,
        "missing_bimdata_resolution": missing_bimdata_resolution,
        "invalid_registry": invalid_registry,
        "valid": not missing_registry and not missing_bimdata_evidence and not missing_bimdata_resolution and not invalid_registry,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
