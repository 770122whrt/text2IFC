"""Reconcile BIMData index rows against IFC members observed in scanned packages."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "dataset/manifests/candidates/bimdata-rd-source-evidence.jsonl"
DURAARK_LEDGER = ROOT / "dataset/manifests/acquisition-duraark-bimdata-overlap.jsonl"
PACKAGE_EVIDENCE = ROOT / "dataset/manifests/candidates/bimdata-rd-package-evidence.jsonl"
OUTPUT = ROOT / "dataset/manifests/candidates/bimdata-rd-package-reconciliation.jsonl"
MIB = 1024 * 1024


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    evidence = read_jsonl(EVIDENCE)
    ledger = read_jsonl(DURAARK_LEDGER)
    packages = read_jsonl(PACKAGE_EVIDENCE)
    members: dict[str, list[dict]] = {}
    for row in ledger:
        if row.get("package_url"):
            members.setdefault(str(row["package_url"]), []).append(
                {
                    "member_name": row.get("member_name"),
                    "size_bytes": row.get("size_bytes"),
                    "sha256": row.get("sha256"),
                    "canonical_path": row.get("canonical_path"),
                }
            )
    for row in packages:
        url = str(row.get("package_url"))
        for member in row.get("ifc_members") or []:
            members.setdefault(url, []).append(
                {
                    "member_name": member.get("member_name"),
                    "size_bytes": member.get("size_bytes"),
                    "sha256": None,
                    "canonical_path": None,
                }
            )

    rows: list[dict] = []
    for row in evidence:
        if row.get("evidence_level") != "direct_source_package_scanned":
            continue
        reported_mb = row.get("reported_size_mb")
        reported_bytes = float(reported_mb) * MIB if reported_mb is not None else None
        matches: list[dict] = []
        all_members: list[dict] = []
        for url in row.get("direct_scanned_package_urls") or []:
            for member in members.get(str(url), []):
                member_record = dict(member)
                member_record["package_url"] = url
                all_members.append(member_record)
                actual = member.get("size_bytes")
                if reported_bytes and actual:
                    relative_error = abs(float(actual) - reported_bytes) / reported_bytes
                    absolute_error = abs(float(actual) - reported_bytes)
                    if relative_error <= 0.20 or absolute_error <= 0.5 * MIB:
                        candidate = dict(member_record)
                        candidate["reported_size_relative_error"] = relative_error
                        matches.append(candidate)
        matches.sort(
            key=lambda item: (
                float(item.get("reported_size_relative_error") or 0),
                str(item.get("member_name")),
            )
        )
        if len(matches) == 1:
            reconciliation_status = "package_scanned_unique_size_match"
        elif len(matches) > 1:
            reconciliation_status = "package_scanned_ambiguous_size_match"
        else:
            reconciliation_status = "package_scanned_no_size_match"
        rows.append(
            {
                "schema_version": "text2ifc/bimdata-package-reconciliation/1.0",
                "source_id": "bimdata-rd-index",
                "upstream_path": row.get("upstream_path"),
                "reported_size_mb": reported_mb,
                "canonical_source": row.get("canonical_source"),
                "reconciliation_status": reconciliation_status,
                "candidate_member_matches": matches,
                "scanned_package_ifc_member_count": len(all_members),
                "notes": [
                    "Size reconciliation is evidence for source resolution, not proof of file identity.",
                    "Only SHA256 equality may establish exact file identity.",
                ],
            }
        )

    rows.sort(key=lambda item: str(item.get("upstream_path")).casefold())
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    counts: dict[str, int] = {}
    for row in rows:
        status = row["reconciliation_status"]
        counts[status] = counts.get(status, 0) + 1
    print(json.dumps({"records": len(rows), "status": counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
