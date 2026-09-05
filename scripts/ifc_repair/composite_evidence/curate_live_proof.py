"""Curate the genuine live-run evidence into the repository proof convention.

Reads the recorded genuine DeepSeek execution under
``dataset/processed/ifc-repair-runs/repair-composite-milestone/`` (12 real
Provider calls; every attempt, changeset, and application preserved) and
assembles the public proof collection under
``dataset/processed/proof/repair-composite-milestone/`` following the
established convention of ``ifc-repair-success-cases`` (numbered IFC files,
input/agent/changeset/validation subdirectories, FILES.json, REPORT.md).

Composite-milestone semantics note: this milestone is an ADDITION/RENOVATION
milestone, not a damage-restoration benchmark — the system input is the
pristine public corpus model, so ``02-input.ifc`` is byte-identical to
``01-original.ifc`` (there is no manufactured damage).  The README documents
this mapping explicitly.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from scripts.ifc_repair.composite_evidence.offline_driver import load_freeze  # noqa: E402

RUN_ROOT = ROOT / "dataset" / "processed" / "ifc-repair-runs" / "repair-composite-milestone"
PROOF_ROOT = ROOT / "dataset" / "processed" / "proof" / "repair-composite-milestone"
FREEZE = load_freeze()
NL = chr(10)


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _read(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str) + NL,
        encoding="utf-8",
        newline=NL,
    )


def _terminal_bundle(run_root: Path) -> Path | None:
    for path in sorted((run_root / ".terminal-bundles").glob("*")):
        if (path / "terminal" / "evidence.json").is_file():
            return path
    return None


def curate_case(case: Mapping[str, Any]) -> dict[str, Any]:
    case_id = str(case["case_id"])
    case_dir = PROOF_ROOT / case_id
    if case_dir.exists():
        shutil.rmtree(case_dir)
    for sub in ("input", "agent", "changeset", "validation"):
        (case_dir / sub).mkdir(parents=True)

    model = FREEZE["models"][case["model_id"]]
    source = ROOT / str(model["path"])
    negative = case.get("expected_terminal_class") == "UNSUPPORTED_ATOMIC_GUARD"

    # 01-original / 02-input: addition semantics — input IS the pristine model.
    shutil.copy2(source, case_dir / "01-original.ifc")
    shutil.copy2(source, case_dir / "02-input.ifc")
    (case_dir / "input" / "request.txt").write_text(
        str(case["request"]) + NL, encoding="utf-8", newline=NL
    )

    run_dir = RUN_ROOT / "cases" / case_id
    case_result = _read(run_dir / "case-result.json")
    final = case_result.get("final", {})
    run_root = run_dir / "runtime" / "runs" / str(final.get("run_id"))
    succeeded = final.get("status") == "succeeded"

    # agent artifacts: the Provider-authored intent + live attempt evidence
    intent_path = run_root / "intent" / "repair-intent.json"
    if intent_path.is_file():
        shutil.copy2(intent_path, case_dir / "agent" / "repair-intent.json")
    _write_json(
        case_dir / "agent" / "live-attempts.json",
        {
            "schema_version": "text2ifc/composite-live-attempts/0.1",
            "case_id": case_id,
            "attempt_count": len(case_result.get("attempts", [])),
            "attempts": case_result.get("attempts", []),
        },
    )
    _write_json(
        case_dir / "agent" / "live-case-summary.json",
        {
            "case_id": case_id,
            "final_status": final.get("status"),
            "reason_code": final.get("reason_code"),
            "transport_calls": case_result.get("transport_calls"),
            "transport_calls_by_stage": case_result.get("transport_calls_by_stage"),
            "live_evidence_pass": case_result.get("live_evidence_pass"),
            "latency_seconds": final.get("latency_seconds"),
            "strict_reopen_verification": final.get("strict_reopen_verification"),
            "source_sha256_before": final.get("source_sha256_before"),
            "source_sha256_after": final.get("source_sha256_after"),
        },
    )

    # changeset (only exists when Stage 2 ran and bound)
    bound = run_root / "changeset" / "bound-changeset.json"
    if bound.is_file():
        shutil.copy2(bound, case_dir / "changeset" / "bound-changeset.json")

    # 03-repaired + validation artifacts for succeeded cases
    if succeeded:
        bundle = _terminal_bundle(run_root)
        repaired = bundle / "successful" / "repaired.ifc"
        shutil.copy2(repaired, case_dir / "03-repaired.ifc")
        evidence = _read(bundle / "terminal" / "evidence.json")["evidence"]
        _write_json(
            case_dir / "validation" / "application.json",
            evidence["application"],
        )
    elif negative:
        _write_json(
            case_dir / "validation" / "NEGATIVE-GUARD.json",
            {
                "case_id": case_id,
                "terminal_class": "UNSUPPORTED_ATOMIC_GUARD",
                "final_status": final.get("status"),
                "reason_code": final.get("reason_code"),
                "zero_mutation": final.get("source_sha256_before")
                == final.get("source_sha256_after"),
                "stage2_attempts": sum(
                    1
                    for a in case_result.get("attempts", [])
                    if a.get("stage") == "stage2"
                ),
                "repaired_ifc_produced": False,
            },
        )
    else:
        _write_json(
            case_dir / "validation" / "TERMINAL-FAILURE-RECORD.json",
            {
                "case_id": case_id,
                "final_status": final.get("status"),
                "reason_code": final.get("reason_code"),
                "genuine_provider_outcome": True,
                "clarification": final.get("clarification"),
                "transport_calls_by_stage": case_result.get(
                    "transport_calls_by_stage"
                ),
                "repaired_ifc_produced": False,
                "note": (
                    "Genuine live-Provider outcome preserved per protocol; "
                    "the failure modes and attempt evidence are recorded in "
                    "agent/live-attempts.json."
                ),
            },
        )

    # composite proof / preservation from the offline re-verification
    contract = case_result.get("contract", {})
    if contract.get("composite_proof"):
        _write_json(
            case_dir / "validation" / "composite-proof.json",
            contract["composite_proof"],
        )
    if contract.get("preservation_exact_delta"):
        _write_json(
            case_dir / "validation" / "preservation.json",
            {
                "exact_delta": contract["preservation_exact_delta"],
                "comparator": contract.get("preservation_comparator"),
            },
        )

    return {
        "case_id": case_id,
        "final_status": final.get("status"),
        "reason_code": final.get("reason_code"),
        "succeeded": succeeded,
        "negative": negative,
    }


def main() -> int:
    results = [curate_case(case) for case in FREEZE["cases"]]
    for item in results:
        print(
            f"  {item['case_id']}: {item['final_status']}"
            f" ({item['reason_code']})"
        )
    _write_json(
        PROOF_ROOT / "live-curation-summary.json",
        {
            "curated_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(),
            "run_root": str(RUN_ROOT.relative_to(ROOT)),
            "results": results,
        },
    )
    print("curated", len(results), "cases ->", PROOF_ROOT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
