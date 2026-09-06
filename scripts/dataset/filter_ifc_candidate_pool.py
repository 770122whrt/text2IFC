"""Uniformly classify the discovery candidate pool without mutating canonical data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MIB = 1024 * 1024


def classify(row: dict) -> dict:
    out = dict(row)
    status = str(row.get("candidate_status") or row.get("status") or "discovered")
    size = int(row.get("size_bytes") or 0)
    schema = str(row.get("schema") or "").upper()
    metrics = row.get("metrics") or {}

    out["retention_decision"] = "pending"
    out["strict_quality_pass"] = None
    out["decision_reason"] = None

    if status in {"excluded_size_exception", "excluded_over_10mib_current_target"}:
        out["retention_decision"] = "exclude"
        out["decision_reason"] = "size_exception"
        return out
    if status in {"existing_canonical", "existing_benchmark_reference"}:
        out["retention_decision"] = "existing_reference"
        out["decision_reason"] = status
        return out
    if status == "index_only":
        out["retention_decision"] = "pending_fetch"
        out["decision_reason"] = "index_only"
        return out
    if row.get("http_status") not in (None, 200):
        out["retention_decision"] = "exclude"
        out["decision_reason"] = "fetch_failed"
        return out
    if size and size >= 10 * MIB:
        out["retention_decision"] = "exclude"
        out["decision_reason"] = "over_10mib"
        return out
    if row.get("local_exact_duplicate") or row.get("batch_exact_duplicate"):
        out["retention_decision"] = "exclude"
        out["decision_reason"] = "exact_duplicate"
        return out
    if status in {"parse_error", "error"} and not schema:
        out["retention_decision"] = "exclude"
        out["decision_reason"] = "parse_error"
        return out
    if schema and schema != "IFC2X3":
        out["retention_decision"] = "exclude"
        out["decision_reason"] = "not_ifc2x3"
        return out
    if metrics:
        elements = int(metrics.get("element_count") or 0)
        if elements <= 1:
            out["retention_decision"] = "exclude"
            out["decision_reason"] = "single_component"
            return out
        out["retention_decision"] = "retain_candidate"
        out["decision_reason"] = "ifc2x3_non_single_component"
        out["strict_quality_pass"] = bool(
            int(metrics.get("project_count") or 0) >= 1
            and int(metrics.get("building_count") or 0) >= 1
            and int(metrics.get("storey_count") or 0) >= 1
            and int(metrics.get("containment_rel_count") or 0) >= 1
            and elements >= 10
            and int(metrics.get("key_class_diversity") or 0) >= 2
        )
        return out

    out["retention_decision"] = "pending_scan"
    out["decision_reason"] = "metadata_only"
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default="dataset/manifests/candidates/ifc-candidate-pool.jsonl",
    )
    parser.add_argument(
        "--output",
        default="dataset/manifests/candidates/ifc-candidate-screen.jsonl",
    )
    args = parser.parse_args()
    source = ROOT / args.input
    rows = [
        json.loads(line)
        for line in source.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    screened = [classify(row) for row in rows]
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in screened),
        encoding="utf-8",
    )
    decisions: dict[str, int] = {}
    reasons: dict[str, int] = {}
    strict_pass = 0
    strict_fail = 0
    for row in screened:
        d = str(row["retention_decision"])
        r = str(row["decision_reason"])
        decisions[d] = decisions.get(d, 0) + 1
        reasons[r] = reasons.get(r, 0) + 1
        if row["strict_quality_pass"] is True:
            strict_pass += 1
        elif row["strict_quality_pass"] is False:
            strict_fail += 1
    print(
        json.dumps(
            {
                "records": len(screened),
                "decisions": decisions,
                "reasons": reasons,
                "strict_quality_pass": strict_pass,
                "strict_quality_fail": strict_fail,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
