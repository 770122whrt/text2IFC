"""Curate one accepted Phase 11 live UAT into immutable public Proof."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from scripts.ifc_repair.audit_door_repair_triplet import audit_case  # noqa: E402


SOURCE_IFC = (
    ROOT
    / "dataset/external/bim-whale-ifc-samples/LargeBuilding/IFC/LargeBuilding.ifc"
)
DEFAULT_COLLECTION = ROOT / "dataset/processed/proof/ifc-repair-success-cases"
DEFAULT_LIVE_PROOF = ROOT / "dataset/processed/proof/phase11-live-uat"
SUCCESS_CASES = {
    "complete-door": "largebuilding-live-deepseek-complete-door",
    "incomplete-then-feedback": (
        "largebuilding-live-deepseek-clarified-door"
    ),
}


def _read(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON_OBJECT_REQUIRED:{path}")
    return payload


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (
        value
        if isinstance(value, str)
        else json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
    )
    path.write_text(payload.rstrip() + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _hash_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _copy(source: Path, destination: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def _run_root(case_root: Path, run_id: str) -> Path:
    root = (case_root / "runtime" / "runs" / run_id).resolve()
    if not root.is_dir():
        raise FileNotFoundError(root)
    return root


def _artifact(run_root: Path, relative: str) -> Path:
    path = (run_root / relative).resolve()
    try:
        path.relative_to(run_root)
    except ValueError as error:
        raise ValueError(f"ARTIFACT_OUTSIDE_RUN:{relative}") from error
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def _final_context(run_root: Path, source_request_hash: str) -> dict[str, Any]:
    matches = []
    for path in sorted(run_root.glob("api-context*.json")):
        value = _read(path)
        intent = value.get("intent")
        if (
            isinstance(intent, Mapping)
            and intent.get("source_request_hash") == source_request_hash
        ):
            matches.append(value)
    if len(matches) != 1:
        raise ValueError("FINAL_API_CONTEXT_NOT_UNIQUE")
    return matches[0]


def _source_manifest(
    *, case_id: str, case: Mapping[str, Any], mutation: Mapping[str, Any]
) -> dict[str, Any]:
    return {
        "schema_version": "text2ifc/phase11-live-proof-source/0.1",
        "case_id": case_id,
        "status": "passed",
        "operation_count": 1,
        "provider": "deepseek-openai-compatible",
        "model": "deepseek-v4-flash",
        "provider_evidence_mode": "live",
        "synthetic_fallback_used": False,
        "public_targeting": {"guid_free": False, "name_free": False},
        "damage": {
            "mutation_type": mutation.get("mutation_type"),
            "damage_scope": mutation.get("damage_scope"),
            "removed_doors": list(mutation.get("removed_doors", ())),
        },
        "live_contract": {
            "provider_attempts": dict(case["provider_attempts"]),
            "strict_reopen_verification": dict(
                case["strict_reopen_verification"]
            ),
            "contract_pass": case.get("contract_pass"),
        },
    }


def _production_boundary(
    *, damaged: Path, request: str, changeset: Mapping[str, Any]
) -> dict[str, Any]:
    canonical = json.dumps(
        changeset,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return {
        "schema_version": "text2ifc/production-input-boundary/0.2",
        "ifc_inputs": ["damaged_ifc_path"],
        "request_inputs": ["public_request_bundle"],
        "original_ifc_supplied": False,
        "mutation_manifest_supplied": False,
        "deleted_object_ids_supplied": False,
        "private_comparator_available_during_repair": False,
        "damaged_ifc_sha256": _sha256(damaged),
        "request_sha256": _hash_text(request),
        "changeset_canonical_sha256": _hash_text(canonical),
    }


def _provider_attempts(run_root: Path) -> dict[str, Any]:
    stage1 = []
    for path in sorted(run_root.rglob("attempt-*.json")):
        if "intent" not in path.relative_to(run_root).parts:
            continue
        stage1.append(
            {
                "path": path.relative_to(run_root).as_posix(),
                "record": _read(path),
            }
        )
    stage2 = []
    for path in sorted(
        run_root.rglob("changeset/attempt-*/provider-metadata.json")
    ):
        stage2.append(
            {
                "path": path.relative_to(run_root).as_posix(),
                "record": _read(path),
            }
        )
    return {
        "schema_version": "text2ifc/phase11-live-provider-evidence/0.1",
        "stage1": stage1,
        "stage2": stage2,
        "secrets_redacted": True,
    }


def _files(case_root: Path, roles: Mapping[str, str]) -> dict[str, Any]:
    entries = []
    for relative, role in sorted(roles.items()):
        path = case_root / relative
        entries.append(
            {
                "path": relative,
                "role": role,
                "size_bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
        )
    return {
        "schema_version": "text2ifc/ifc-repair-proof-files/0.2",
        "case_id": case_root.name,
        "files": entries,
    }


def _curate_success_case(
    *, source_root: Path, result: Mapping[str, Any], case: Mapping[str, Any],
    proof_case_id: str, collection_root: Path,
) -> dict[str, Any]:
    final = case["final"]
    if (
        case.get("contract_pass") is not True
        or final.get("status") != "succeeded"
        or final.get("successful_artifact_publishable") is not True
        or case.get("strict_reopen_verification", {}).get("status") != "passed"
    ):
        raise ValueError(f"LIVE_CASE_NOT_STRICTLY_ACCEPTED:{case.get('case_id')}")
    source_case = source_root / str(case["case_id"])
    run_root = _run_root(source_case, str(final["run_id"]))
    destination = (
        collection_root / "door" / "surviving-opening" / proof_case_id
    )
    if destination.exists():
        raise FileExistsError(destination)
    destination.mkdir(parents=True)

    changeset_path = run_root / "changeset" / "bound-changeset.json"
    changeset = _read(changeset_path)
    context = _final_context(
        run_root, str(changeset["source_request_hash"])
    )
    request = str(context["repair_text"])
    evidence_path = _artifact(
        run_root,
        str(final["artifacts"]["manifest"]),
    ).parent / "terminal" / "evidence.json"
    application = _read(evidence_path).get("evidence", {}).get("application")
    if not isinstance(application, Mapping):
        raise ValueError("LIVE_APPLICATION_EVIDENCE_MISSING")
    mutation = _read(source_case / "fixture" / "mutation_report.json")

    roles = {
        "01-original.ifc": "original_ground_truth",
        "02-damaged.ifc": "repair_input_ifc",
        "03-repaired.ifc": "published_repair_output",
        "input/request.txt": "user_request",
        "agent/repair-intent.json": "stage1_repair_intent",
        "agent/target-resolution.json": "deterministic_target_resolution",
        "changeset/bound-changeset.json": "bound_changeset",
        "validation/application.json": "application_result",
        "validation/production-evaluation.json": "production_evaluation",
        "validation/source-run-manifest.json": "source_run_manifest",
        "validation/production-boundary.json": "production_input_boundary",
        "validation/strict-reopen-verification.json": (
            "independent_live_reopen_verification"
        ),
        "provider-evidence/live-case-result.json": "live_provider_case_result",
        "provider-evidence/provider-attempts.json": "live_provider_attempts",
        "provider-evidence/prompt-profile-selection.json": (
            "prompt_profile_evidence"
        ),
    }
    _copy(SOURCE_IFC, destination / "01-original.ifc")
    _copy(source_case / "fixture" / "damaged.ifc", destination / "02-damaged.ifc")
    _copy(
        _artifact(run_root, str(final["artifacts"]["successful_ifc"])),
        destination / "03-repaired.ifc",
    )
    _write(destination / "input/request.txt", request)
    _write(destination / "agent/repair-intent.json", context["intent"])
    _copy(run_root / "resolution.json", destination / "agent/target-resolution.json")
    _copy(changeset_path, destination / "changeset/bound-changeset.json")
    _write(destination / "validation/application.json", application)
    _copy(
        _artifact(run_root, str(final["artifacts"]["evaluation"])),
        destination / "validation/production-evaluation.json",
    )
    _write(
        destination / "validation/source-run-manifest.json",
        _source_manifest(case_id=proof_case_id, case=case, mutation=mutation),
    )
    _write(
        destination / "validation/production-boundary.json",
        _production_boundary(
            damaged=destination / "02-damaged.ifc",
            request=request,
            changeset=changeset,
        ),
    )
    _copy(
        source_case / "strict-reopen-verification.json",
        destination / "validation/strict-reopen-verification.json",
    )
    _write(destination / "provider-evidence/live-case-result.json", case)
    _write(
        destination / "provider-evidence/provider-attempts.json",
        _provider_attempts(run_root),
    )
    _copy(
        run_root / "changeset" / "prompt-profile-selection.json",
        destination / "provider-evidence/prompt-profile-selection.json",
    )
    for path in sorted((run_root / "changeset").glob("semantic-manifest-*.json")):
        relative = f"agent/{path.name}"
        _copy(path, destination / relative)
        roles[relative] = "semantic_manifest"

    audit = audit_case(destination, write=False)
    release = audit["release_decision"]
    if (
        release.get("publishable") is not True
        or release.get("l0_pass") is not True
        or release.get("l1_pass") is not True
        or release.get("l2_pass") is not True
        or release.get("blocking_findings")
    ):
        raise ValueError(f"LIVE_CURATED_AUDIT_FAILED:{proof_case_id}")
    _write(destination / "validation/three-way-audit.json", audit)
    _write(destination / "validation/release-decision.json", release)
    roles["validation/three-way-audit.json"] = "three_way_l0_l1_l2_audit"
    roles["validation/release-decision.json"] = "l0_l1_l2_release_decision"

    _write(
        destination / "REPORT.md",
        (
            f"# {proof_case_id}\n\n"
            "真实 DeepSeek Door 修复成功案例。生产修复仅使用 damaged IFC 与"
            "公开请求；original IFC 只在修复完成后用于独立三方审计。\n\n"
            f"- Provider attempts: Stage 1 = {case['provider_attempts']['stage1']}, "
            f"Stage 2 = {case['provider_attempts']['stage2']}。\n"
            "- synthetic fallback: false。\n"
            "- published IFC 已独立重开为 IFC2X3。\n"
            "- production application/preservation/L1/L2 与独立 L0/L1/L2 全部通过。\n"
        ),
    )
    _write(destination / "FILES.json", _files(destination, roles))
    return {
        "case_id": proof_case_id,
        "operation_family": "door",
        "case_kind": "live_surviving_opening",
        "operation_types": ["fill_existing_opening_with_door"],
        "operation_count": 1,
        "provider": str(result["provider"]),
        "model": str(result["model"]),
        "provider_evidence_mode": "live",
        "status": "accepted",
        "report": f"door/surviving-opening/{proof_case_id}/REPORT.md",
        "files": f"door/surviving-opening/{proof_case_id}/FILES.json",
        "original_ifc": f"door/surviving-opening/{proof_case_id}/01-original.ifc",
        "damaged_ifc": f"door/surviving-opening/{proof_case_id}/02-damaged.ifc",
        "repaired_ifc": f"door/surviving-opening/{proof_case_id}/03-repaired.ifc",
    }


def _curate_overall_record(
    *, source_root: Path, result: Mapping[str, Any], proof_root: Path
) -> Path:
    destination = proof_root / source_root.name
    if destination.exists():
        raise FileExistsError(destination)
    destination.mkdir(parents=True)
    roles = {"live-uat-result.json": "live_uat_result"}
    _copy(source_root / "live-uat-result.json", destination / "live-uat-result.json")
    unsupported = next(
        item
        for item in result["cases"]
        if item["case_id"] == "unsupported-complex-door"
    )
    source_case = source_root / "unsupported-complex-door"
    run_root = _run_root(source_case, str(unsupported["final"]["run_id"]))
    for relative, source in {
        "unsupported/case-result.json": source_case / "case-result.json",
        "unsupported/repair-intent.json": run_root / "intent" / "repair-intent.json",
        "unsupported/state.json": run_root / "state.json",
    }.items():
        _copy(source, destination / relative)
        roles[relative] = "unsupported_live_evidence"
    _write(
        destination / "unsupported/provider-attempts.json",
        _provider_attempts(run_root),
    )
    roles["unsupported/provider-attempts.json"] = "unsupported_provider_attempts"
    _write(
        destination / "README.md",
        (
            "# Phase 11 real DeepSeek UAT\n\n"
            "三案均通过严格合同；两个成功案已分别纳入 success-case collection，"
            "unsupported 案在 Stage 2 前以 `DOOR_OPERATION_TYPE_UNSUPPORTED` 终止。\n"
        ),
    )
    roles["README.md"] = "human_readable_report"
    _write(destination / "FILES.json", _files(destination, roles))
    return destination


def curate(
    source_root: Path,
    collection_root: Path = DEFAULT_COLLECTION,
    live_proof_root: Path = DEFAULT_LIVE_PROOF,
) -> dict[str, Any]:
    result = _read(source_root / "live-uat-result.json")
    if (
        result.get("status") != "passed"
        or result.get("synthetic_fallback_used") is not False
    ):
        raise ValueError("LIVE_UAT_NOT_ACCEPTED")
    by_id = {str(item["case_id"]): item for item in result["cases"]}
    entries = [
        _curate_success_case(
            source_root=source_root,
            result=result,
            case=by_id[source_id],
            proof_case_id=proof_case_id,
            collection_root=collection_root,
        )
        for source_id, proof_case_id in SUCCESS_CASES.items()
    ]
    collection = _read(collection_root / "manifest.json")
    existing = {str(item["case_id"]) for item in collection["cases"]}
    duplicates = existing & {item["case_id"] for item in entries}
    if duplicates:
        raise ValueError(f"LIVE_PROOF_CASE_ALREADY_EXISTS:{sorted(duplicates)[0]}")
    collection["cases"] = [*collection["cases"], *entries]
    collection["case_count"] = len(collection["cases"])
    collection["operation_families"] = sorted(
        {str(item["operation_family"]) for item in collection["cases"]}
    )
    collection["generated_at"] = "2026-07-31"
    _write(collection_root / "manifest.json", collection)
    overall = _curate_overall_record(
        source_root=source_root,
        result=result,
        proof_root=live_proof_root,
    )
    return {
        "schema_version": "text2ifc/phase11-live-proof-curation/0.1",
        "status": "passed",
        "success_case_count": len(entries),
        "success_cases": [item["case_id"] for item in entries],
        "overall_proof": overall.as_posix(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_root", type=Path)
    parser.add_argument("--collection-root", type=Path, default=DEFAULT_COLLECTION)
    parser.add_argument("--live-proof-root", type=Path, default=DEFAULT_LIVE_PROOF)
    args = parser.parse_args(argv)
    result = curate(
        args.source_root.resolve(),
        args.collection_root.resolve(),
        args.live_proof_root.resolve(),
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
