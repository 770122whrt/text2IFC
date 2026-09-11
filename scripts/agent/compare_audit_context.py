"""Read-only comparison of archived wire prompts; never creates a Provider."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from text2ifc_agent.audit_context import render_audit_context, restore_audit_evidence


def compare_case(directory: Path) -> dict:
    names = ("prompt-render-input.json", "prompt-rendered.md", "request.redacted.json", "response-metadata.json")
    source_bytes = {name: (directory / name).read_bytes() for name in names}
    inputs = json.loads(source_bytes["prompt-render-input.json"])
    review = "DESIGN_REVIEW_CONTEXT" in inputs
    baseline, _ = render_audit_context(inputs=inputs, review_enabled=review)
    # Text files can use CRLF; the actual JSON request must match exactly.
    stored_text = source_bytes["prompt-rendered.md"].decode("utf-8").replace("\r\n", "\n")
    request = json.loads(source_bytes["request.redacted.json"])["request"]
    messages = request.get("messages", [])
    if (stored_text != baseline["text"] or len(messages) != 1
            or messages[0].get("role") != "user" or messages[0].get("content") != baseline["text"]):
        raise ValueError("AUDIT_CONTEXT_BASELINE_WIRE_MISMATCH")
    selected, record = render_audit_context(inputs=inputs, review_enabled=review, mode="deduplicated")
    reconstructed = dict(selected["inputs"])
    if record["effective_mode"] == "deduplicated":
        reconstructed.update(restore_audit_evidence(reconstructed.pop("AUDIT_EVIDENCE_CONTEXT")))
    if json.dumps(reconstructed, sort_keys=True) != json.dumps(baseline["inputs"], sort_keys=True):
        raise ValueError("AUDIT_CONTEXT_TRANSMITTED_INPUT_MISMATCH")
    source_hashes = {name: hashlib.sha256(data).hexdigest() for name, data in source_bytes.items()}
    if any((directory / name).read_bytes() != data for name, data in source_bytes.items()):
        raise ValueError("AUDIT_CONTEXT_SOURCE_CHANGED_DURING_COMPARISON")
    metadata = json.loads(source_bytes["response-metadata.json"])
    return {
        "audit_dir": directory.as_posix(), "source_sha256": source_hashes,
        "baseline_matches_actual_message": True, "all_transmitted_values_preserved": True,
        "baseline_response_id": metadata.get("response_id"), "baseline_usage": metadata.get("usage"),
        "candidate_usage": None, "model_quality_comparison": "not_run",
        "comparison": record,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-dir", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists; preserve the previous comparison")
    rows = [compare_case(path) for path in args.audit_dir]
    result = {
        "schema_version": "text2ifc/audit-context-comparison/1.0",
        "evidence_class": "offline_projection_of_frozen_live_inputs",
        "provider_calls": 0,
        "measurement_scope": "single_user_message_text_including_reference_instructions_not_transport_overhead",
        "estimator": "existing_ASCII_CJK_heuristic_not_actual_tokenizer_or_guaranteed_upper_bound",
        "cases": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as target:
        json.dump(result, target, ensure_ascii=False, indent=2, allow_nan=False)
        target.write("\n")
    for row in rows:
        record = row["comparison"]
        before, after = record["baseline"], record["selected"]
        print(f"{row['audit_dir']}: {before['utf8_bytes']} -> {after['utf8_bytes']} bytes; {record['effective_mode']}")


if __name__ == "__main__":
    main()
