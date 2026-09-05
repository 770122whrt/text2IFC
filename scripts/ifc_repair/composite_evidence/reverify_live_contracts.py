"""Re-verify the live run's proof contracts offline (zero new Provider calls).

The genuine DeepSeek execution recorded every attempt, changeset, and
application under
``dataset/processed/ifc-repair-runs/repair-composite-milestone/cases/``.
The first execution marked C1's contract failed only because the proof
contract then bound predicates by the FROZEN operation_id, while the live
Provider authors its own ids (``op_beam_add`` etc.).  The contract resolver
now binds by frozen geometry/target/property; this script re-runs the
contract verification against the RECORDED live artifacts and writes the
updated per-case contract results.

No Provider transport is touched; this is deterministic post-processing of
genuine recorded evidence.
"""

from __future__ import annotations

import glob
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import ifcopenshell  # noqa: E402

from scripts.ifc_repair.composite_evidence.composite_proof import (  # noqa: E402
    CompositeProofError,
    verify_composite_case,
)
from scripts.ifc_repair.composite_evidence.offline_driver import load_freeze  # noqa: E402
from scripts.ifc_repair.composite_evidence.preservation import (  # noqa: E402
    CompositePreservationError,
    verify_exact_composed_delta,
    verify_no_unrelated_mutation,
)

RUN_ROOT = ROOT / "dataset" / "processed" / "ifc-repair-runs" / "repair-composite-milestone"
FREEZE = load_freeze()


def _read(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def reverify_case(case: dict) -> dict:
    case_id = str(case["case_id"])
    case_dir = RUN_ROOT / "cases" / case_id
    case_result_path = case_dir / "case-result.json"
    case_result = _read(case_result_path)
    final = case_result.get("final", {})

    source = ROOT / str(FREEZE["models"][case["model_id"]]["path"])
    negative = case.get("expected_terminal_class") == "UNSUPPORTED_ATOMIC_GUARD"

    attempts = case_result.get("attempts", [])

    if negative:
        proof_payload = {
            "case_id": case_id,
            "status": "not_run",
        }
        try:
            guard = verify_composite_case(
                case=case,
                changeset={},
                application={},
                source_model=None,
                repaired_model=None,
                source_path=source,
                repaired_path=None,
                live_attempt_evidence=attempts,
            )
            proof_payload = {
                "case_id": case_id,
                "composite_proof": guard,
                "negative_guard": {
                    "status": final.get("status"),
                    "reason_code": final.get("reason_code"),
                    "zero_mutation": final.get("source_sha256_before")
                    == final.get("source_sha256_after"),
                    "stage2_attempts": sum(
                        1 for a in attempts if a.get("stage") == "stage2"
                    ),
                },
                "status": "passed",
            }
        except CompositeProofError as error:
            proof_payload["proof_error"] = str(error)
            proof_payload["status"] = "failed"
        return proof_payload

    # Positive case: only meaningful when the production chain succeeded.
    if final.get("status") != "succeeded":
        return {
            "case_id": case_id,
            "status": "not_applicable_production_chain_did_not_succeed",
            "final_status": final.get("status"),
            "final_reason": final.get("reason_code"),
        }

    runtime = case_dir / "runtime"
    run_id = str(final.get("run_id"))
    run_root = runtime / "runs" / run_id
    changeset_path = run_root / "changeset" / "bound-changeset.json"
    if not changeset_path.is_file():
        changeset_path = run_root / "changeset.json"
    changeset = _read(changeset_path)
    evidence_path = None
    for path in glob.glob(
        str(run_root / ".terminal-bundles" / "*" / "terminal" / "evidence.json"),
        recursive=True,
    ):
        evidence_path = path
        break
    application = _read(evidence_path)["evidence"]["application"]
    repaired_path = Path(str(final["artifacts"]["successful_ifc"]))
    if not repaired_path.is_absolute():
        repaired_path = run_root / repaired_path

    payload = {"case_id": case_id, "status": "not_run"}
    try:
        proof = verify_composite_case(
            case=case,
            changeset=changeset,
            application=application,
            source_model=ifcopenshell.open(str(source)),
            repaired_model=ifcopenshell.open(str(repaired_path)),
            source_path=source,
            repaired_path=repaired_path,
            live_attempt_evidence=attempts,
        )
        preservation_exact = verify_exact_composed_delta(
            case=case,
            application=application,
            source_model=ifcopenshell.open(str(source)),
            repaired_model=ifcopenshell.open(str(repaired_path)),
        )
        preservation_comparator = verify_no_unrelated_mutation(
            case=case,
            application=application,
            source_path=source,
            repaired_path=repaired_path,
        )
        payload.update(
            {
                "composite_proof": proof,
                "preservation_exact_delta": preservation_exact,
                "preservation_comparator": preservation_comparator,
                "repaired_ifc_path": str(repaired_path),
                "changeset_path": str(changeset_path),
                "status": "passed",
            }
        )
    except (CompositeProofError, CompositePreservationError) as error:
        payload["status"] = "failed"
        payload["proof_error"] = str(error)
    return payload


def main() -> int:
    results = []
    for case in FREEZE["cases"]:
        case_id = str(case["case_id"])
        payload = reverify_case(case)
        # Write the updated contract back into the case result.
        case_result_path = RUN_ROOT / "cases" / case_id / "case-result.json"
        case_result = _read(case_result_path)
        case_result["contract"] = payload
        case_result["contract_reverified_offline_utc"] = (
            __import__("datetime")
            .datetime.now(__import__("datetime").timezone.utc)
            .isoformat()
        )
        case_result["status"] = (
            "passed"
            if payload.get("status") == "passed"
            and case_result.get("live_evidence_pass")
            and case_result.get("execution_error") is None
            else case_result["status"]
        )
        case_result_path.write_text(
            json.dumps(case_result, ensure_ascii=False, indent=2, default=str)
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        results.append(payload)
        print(f"{case_id}: contract={payload.get('status')}")
    out = RUN_ROOT / "contract-reverification.json"
    out.write_text(
        json.dumps(results, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
