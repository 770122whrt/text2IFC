"""Classify BIMData R&D file candidates by provenance and evidence strength.

BIMData R&D is treated as a discovery index, not as license authority.  Each
file-level candidate records the upstream URL(s), the canonical source family
that those URLs point to, whether the upstream package has actually been
acquired/scanned, and the conservative rights state used by the dataset.
"""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / ".tmp/dataset-acquisition/bimdata-rd-file-candidates.jsonl"
DURAARK_LEDGER = ROOT / "dataset/manifests/acquisition-duraark-bimdata-overlap.jsonl"
PACKAGE_EVIDENCE = ROOT / "dataset/manifests/candidates/bimdata-rd-package-evidence.jsonl"
OUTPUT = ROOT / "dataset/manifests/candidates/bimdata-rd-source-evidence.jsonl"


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def classify_url(url: str) -> dict:
    host = urlparse(url).netloc.lower()
    lower = url.lower()
    if "tib.eu" in host and "/duraark/" in lower:
        return {
            "canonical_source": "DURAARK/TIB BuildingData",
            "source_classification": "public_research",
            "license": "source-open-data-model-rights-review-required",
            "research_use": "review_required",
            "training_use": "review_required",
            "redistribution": "review_required",
        }
    if "bimcollab.com" in host:
        return {
            "canonical_source": "BIMcollab Example Project",
            "source_classification": "public_example",
            "license": "review-required",
            "research_use": "review_required",
            "training_use": "review_required",
            "redistribution": "review_required",
        }
    if "openifcmodel.cs.auckland.ac.nz" in host:
        return {
            "canonical_source": "Open IFC Model Repository (University of Auckland)",
            "source_classification": "public_model_repository",
            "license": "upstream-model-rights-review-required",
            "research_use": "review_required",
            "training_use": "review_required",
            "redistribution": "review_required",
        }
    if "portal.nibs.org" in host:
        return {
            "canonical_source": "NIBS public BIM example source",
            "source_classification": "public_example",
            "license": "model-rights-review-required",
            "research_use": "review_required",
            "training_use": "review_required",
            "redistribution": "review_required",
        }
    if "dropbox.com" in host:
        return {
            "canonical_source": "author-hosted Dropbox model",
            "source_classification": "public_link",
            "license": "unresolved",
            "research_use": "review_required",
            "training_use": "review_required",
            "redistribution": "review_required",
        }
    if "cgcad.thss.tsinghua.edu.cn" in host:
        return {
            "canonical_source": "Tsinghua CGCAD IFCCompressor research source",
            "source_classification": "public_research",
            "license": "model-rights-review-required",
            "research_use": "review_required",
            "training_use": "review_required",
            "redistribution": "review_required",
        }
    return {
        "canonical_source": host or "unresolved",
        "source_classification": "public_link" if host else "unresolved",
        "license": "unresolved",
        "research_use": "review_required",
        "training_use": "review_required",
        "redistribution": "review_required",
    }


def main() -> int:
    candidates = read_jsonl(INPUT)
    ledger = read_jsonl(DURAARK_LEDGER)
    package_evidence = read_jsonl(PACKAGE_EVIDENCE)
    package_urls = {str(row.get("package_url")): row for row in ledger if row.get("package_url")}
    for row in package_evidence:
        if row.get("package_url"):
            package_urls.setdefault(str(row["package_url"]), row)
    package_members: dict[str, list[dict]] = {}
    for row in ledger:
        package_members.setdefault(str(row.get("package_url")), []).append(row)
    for row in package_evidence:
        package_members.setdefault(str(row.get("package_url")), []).extend(row.get("ifc_members") or [])

    rows: list[dict] = []
    for candidate in candidates:
        urls = [str(url) for url in candidate.get("source_urls") or [] if url]
        classifications = [classify_url(url) for url in urls]
        primary = classifications[0] if classifications else classify_url("")
        direct_scanned_urls = [url for url in urls if url in package_urls]
        if direct_scanned_urls:
            evidence_level = "direct_source_package_scanned"
            retrieval_status = "source_package_scanned"
        elif urls:
            evidence_level = "source_url_indexed"
            retrieval_status = "pending_or_dead_link"
        else:
            evidence_level = "index_only_unresolved"
            retrieval_status = "unresolved"
        row = {
            "schema_version": "text2ifc/candidate-source-evidence/1.0",
            "source_id": "bimdata-rd-index",
            "discovered_via": "bimdata-rd-index",
            "upstream_path": candidate.get("upstream_path"),
            "reported_size_mb": candidate.get("reported_size_mb"),
            "reported_size_is_index_metadata": True,
            "source_urls": urls,
            "canonical_source": primary["canonical_source"],
            "source_classification": primary["source_classification"],
            "license": primary["license"],
            "research_use": primary["research_use"],
            "training_use": primary["training_use"],
            "redistribution": primary["redistribution"],
            "evidence_level": evidence_level,
            "retrieval_status": retrieval_status,
            "direct_scanned_package_urls": direct_scanned_urls,
            "direct_scanned_package_member_count": sum(
                len(package_members.get(url, [])) for url in direct_scanned_urls
            ),
            "notes": [
                "BIMData R&D is discovery-only and is not treated as independent model-license authority.",
                "Reported size/name metadata must be verified against the original package or file before admission.",
            ],
        }
        rows.append(row)

    rows.sort(key=lambda row: (str(row["upstream_path"]).casefold(), str(row["canonical_source"])))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    counts: dict[str, int] = {}
    rights: dict[str, int] = {}
    sources: dict[str, int] = {}
    for row in rows:
        counts[row["evidence_level"]] = counts.get(row["evidence_level"], 0) + 1
        rights[row["license"]] = rights.get(row["license"], 0) + 1
        sources[row["canonical_source"]] = sources.get(row["canonical_source"], 0) + 1
    print(json.dumps({"records": len(rows), "evidence": counts, "rights": rights, "canonical_sources": sources}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
