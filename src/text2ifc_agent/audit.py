"""Evidence-linked semantic audit subordinate to deterministic gates."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


REQUIRED_EVIDENCE = (
    "input",
    "design_brief",
    "candidate",
    "validation",
    "geometry",
    "raw_response",
)


def build_audit_report(
    *,
    deterministic_gates: Mapping[str, bool],
    intent_coverage: Mapping[str, str],
    mismatches: Sequence[Mapping[str, Any]],
    unsupported_facts: Sequence[Mapping[str, Any] | str],
    evidence: Mapping[str, str],
    narrative_recommendation: str | None = None,
) -> dict[str, Any]:
    """Build an audit report without allowing narrative to override gates."""
    failed_gates = sorted(
        name for name, passed in deterministic_gates.items() if passed is not True
    )
    missing_evidence = [name for name in REQUIRED_EVIDENCE if not evidence.get(name)]
    diagnostics = [
        {
            "code": "MISSING_EVIDENCE",
            "path": f"/evidence/{name}",
            "message": f"Required audit evidence path {name!r} is missing.",
        }
        for name in missing_evidence
    ]
    mismatch_records = [dict(item) for item in mismatches]
    blocking = bool(failed_gates or missing_evidence or mismatch_records)
    if failed_gates or missing_evidence:
        recommendation = "reject"
    elif mismatch_records or unsupported_facts:
        recommendation = "revise"
    else:
        recommendation = "accept"
    return {
        "deterministic_status": "failed" if failed_gates else "passed",
        "deterministic_gates": dict(deterministic_gates),
        "failed_gates": failed_gates,
        "intent_coverage": dict(intent_coverage),
        "mismatches": mismatch_records,
        "unsupported_facts": list(unsupported_facts),
        "evidence": dict(evidence),
        "diagnostics": diagnostics,
        "narrative_recommendation": narrative_recommendation,
        "recommendation": recommendation,
        "blocking": blocking,
    }
