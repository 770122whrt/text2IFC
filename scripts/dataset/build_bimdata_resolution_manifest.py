"""Build final file-level BIMData R&D provenance resolution records."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "dataset/manifests/candidates/bimdata-rd-source-evidence.jsonl"
RECONCILIATION = ROOT / "dataset/manifests/candidates/bimdata-rd-package-reconciliation.jsonl"
URL_PROBE = ROOT / "dataset/manifests/candidates/bimdata-rd-url-probe.jsonl"
OUTPUT = ROOT / "dataset/manifests/candidates/bimdata-rd-resolution.jsonl"


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    evidence = read_jsonl(EVIDENCE)
    reconciliation = {
        str(row.get("upstream_path")): row for row in read_jsonl(RECONCILIATION)
    }
    probes = {str(row.get("url")): row for row in read_jsonl(URL_PROBE)}
    rows: list[dict] = []

    for row in evidence:
        path = str(row.get("upstream_path"))
        rec = reconciliation.get(path)
        url_states = [
            {
                "url": url,
                "status": probes.get(str(url), {}).get("status", "not_probed"),
                "http_status": probes.get(str(url), {}).get("http_status"),
                "final_url": probes.get(str(url), {}).get("final_url"),
            }
            for url in row.get("source_urls") or []
        ]
        probe_statuses = {item["status"] for item in url_states}
        reconciliation_status = rec.get("reconciliation_status") if rec else None

        if reconciliation_status == "package_scanned_unique_size_match":
            resolution_status = "direct_package_unique_member_candidate"
        elif reconciliation_status == "package_scanned_ambiguous_size_match":
            resolution_status = "direct_package_ambiguous_member_candidates"
        elif reconciliation_status == "package_scanned_no_size_match":
            resolution_status = "direct_package_index_mismatch"
        elif row.get("evidence_level") == "index_only_unresolved":
            resolution_status = "index_only_unresolved"
        elif "direct_file_or_archive" in probe_statuses:
            resolution_status = "direct_source_live_pending_scan"
        elif "live_landing_page" in probe_statuses:
            resolution_status = "landing_page_only_no_direct_artifact"
        elif url_states and probe_statuses <= {"dead_or_unreachable", "not_probed"}:
            resolution_status = "source_link_dead_or_unreachable"
        else:
            resolution_status = "source_resolution_pending"

        reported_size_mb = row.get("reported_size_mb")
        under_10_reported = reported_size_mb is not None and float(reported_size_mb) < 10.0
        if resolution_status == "direct_package_unique_member_candidate":
            action = "use_verified_package_member_then_sha_scan"
        elif resolution_status == "direct_package_ambiguous_member_candidates":
            action = "resolve_member_by_name_family_or_sha"
        elif resolution_status == "direct_package_index_mismatch":
            action = "do_not_admit_from_index_without_new_source_evidence"
        elif resolution_status == "direct_source_live_pending_scan":
            action = "fetch_direct_source_if_within_target_size"
        elif resolution_status in {
            "landing_page_only_no_direct_artifact",
            "source_link_dead_or_unreachable",
            "index_only_unresolved",
        }:
            action = "defer_until_alternate_upstream_or_existing_mirror_is_verified"
        else:
            action = "manual_source_resolution"

        rows.append(
            {
                "schema_version": "text2ifc/bimdata-resolution/1.0",
                "source_id": "bimdata-rd-index",
                "upstream_path": path,
                "reported_size_mb": reported_size_mb,
                "reported_under_10mib": under_10_reported,
                "canonical_source": row.get("canonical_source"),
                "source_classification": row.get("source_classification"),
                "license": row.get("license"),
                "research_use": row.get("research_use"),
                "training_use": row.get("training_use"),
                "redistribution": row.get("redistribution"),
                "evidence_level": row.get("evidence_level"),
                "resolution_status": resolution_status,
                "recommended_action": action,
                "source_urls": url_states,
                "package_reconciliation": rec,
                "notes": [
                    "BIMData R&D remains discovery-only; upstream evidence controls admission.",
                    "Reported size is index metadata and is not authoritative until source artifact verification.",
                    "Exact identity requires SHA256 equality; size/name reconciliation alone is not exact deduplication."
                ],
            }
        )

    rows.sort(key=lambda item: str(item.get("upstream_path")).casefold())
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    statuses: dict[str, int] = {}
    under10: dict[str, int] = {}
    for row in rows:
        status = row["resolution_status"]
        statuses[status] = statuses.get(status, 0) + 1
        if row["reported_under_10mib"]:
            under10[status] = under10.get(status, 0) + 1
    print(json.dumps({"records": len(rows), "resolution": statuses, "reported_under_10mib": under10}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
