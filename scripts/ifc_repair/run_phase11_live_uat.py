"""Real, no-fallback DeepSeek UAT for Phase 11 Door routing."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import ifcopenshell


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from scripts.ifc_repair.validate_success_cases import (  # noqa: E402
    audit_repaired_operations,
)
from text2ifc_agent.openai_compat import load_openai_compatible_config  # noqa: E402
from text2ifc_ifc_repair.api import RepairAPI  # noqa: E402
from text2ifc_ifc_repair.mutation import remove_door  # noqa: E402


SOURCE = (
    ROOT
    / "dataset/external/bim-whale-ifc-samples/LargeBuilding/IFC/LargeBuilding.ifc"
)
DOOR_ID = "2cXV28XOjE6f6irgi0COhu"
OPENING_ID = "2cXV28XOjE6f6irhW0COhu"
WALL_ID = "2cXV28XOjE6f6irgi0COfF"
TYPE_ID = "2cXV28XOjE6f6irhu0COgZ"
TYPE_NAME = "M_Single-Flush:Inside Door"
DEFAULT_OUTPUT = ROOT / "dataset/processed/ifc-repair/phase11-live-uat"
TOKEN_GUARD = 65_536
COMPLETE_REQUEST = (
    f"在已有洞口 {OPENING_ID} 中安装一扇门。明确复用现有 DoorStyle “{TYPE_NAME}”"
    f"（GlobalId {TYPE_ID}）。保留 damaged IFC 中可确定的洞口、墙和楼层关系，"
    "不要猜测未提供的材料或五金。"
)
INCOMPLETE_REQUEST = (
    f"在已有洞口 {OPENING_ID} 中安装一扇门。保留 damaged IFC 中可确定的"
    "洞口、墙和楼层关系；门的开启方式和 DoorStyle 尚未说明。"
)
CLARIFICATION_DETAIL = (
    f"明确复用现有 DoorStyle “{TYPE_NAME}”（GlobalId {TYPE_ID}）。"
)
UNSUPPORTED_REQUEST = (
    f"在墙 {WALL_ID} 上新开洞并生成一扇 OperationType 为 REVOLVING 的旋转门；"
    "要求复杂门框、五金、上亮和两片不同开启轨迹。"
)
def _environment(path: Path) -> dict[str, str]:
    values = dict(os.environ)
    if path.is_file():
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _config(environment: dict[str, str]) -> dict[str, Any]:
    value = load_openai_compatible_config(environment)
    ready = (
        bool(value.get("configured"))
        and value.get("max_input_tokens") == TOKEN_GUARD
        and value.get("max_completion_tokens") == TOKEN_GUARD
    )
    return {
        "status": "ready" if ready else "not_configured",
        "provider": value.get("provider"),
        "model": value.get("model"),
        "max_input_tokens": value.get("max_input_tokens"),
        "max_completion_tokens": value.get("max_completion_tokens"),
        "secret_redacted": True,
    }


def _attempts(root: Path) -> dict[str, int]:
    return {
        "stage1": len(
            [item for item in root.rglob("attempt-*.json") if "intent" in item.parts]
        ),
        "stage2": len(
            list(root.rglob("changeset/attempt-*/provider-metadata.json"))
        ),
    }


def _summary(result: Any) -> dict[str, Any]:
    return {
        "status": result.status,
        "reason_code": result.reason_code,
        "run_id": result.run_id,
        "state_version": result.state_version,
        "complete_repair_success": result.complete_repair_success,
        "successful_artifact_publishable": result.successful_artifact_publishable,
        "artifacts": dict(result.artifacts),
    }


def _contract_pass(
    *,
    final: dict[str, Any],
    attempts: dict[str, int],
    expectation: dict[str, Any],
    feedback_expected: bool,
    feedback_applied: bool,
    strict_verification: Mapping[str, Any],
) -> bool:
    published = bool(
        final.get("complete_repair_success")
        and final.get("successful_artifact_publishable")
    )
    checks = [
        str(final.get("status")) == str(expectation["status"]),
        published is bool(expectation["publish"]),
        attempts.get("stage2") == expectation.get("stage2_attempts"),
        (not feedback_expected or feedback_applied),
    ]
    if expectation["publish"]:
        checks.extend(
            (
                strict_verification.get("status") == "passed",
                strict_verification.get("l0_pass") is True,
                strict_verification.get("l1_pass") is True,
                strict_verification.get("l2_pass") is True,
            )
        )
    else:
        checks.append(strict_verification.get("status") == "not_applicable")
    if "reason_code" in expectation:
        checks.append(final.get("reason_code") == expectation["reason_code"])
    return all(checks)


def _strict_reopen_verification(
    runtime: Path,
    final: Mapping[str, Any],
) -> dict[str, Any]:
    """Reopen a published IFC and recompute L0/L1/L2 from run artifacts."""

    if not final.get("successful_artifact_publishable"):
        return {
            "status": "not_applicable",
            "l0_pass": None,
            "l1_pass": None,
            "l2_pass": None,
        }
    try:
        run_id = str(final["run_id"])
        run_root = (runtime / "runs" / run_id).resolve()
        artifacts = final.get("artifacts")
        if not isinstance(artifacts, Mapping):
            raise ValueError("missing result artifacts")
        required = ("manifest", "evaluation", "successful_ifc")
        missing = [name for name in required if not artifacts.get(name)]
        if missing:
            raise ValueError(f"missing published artifacts: {','.join(missing)}")

        manifest_path = _run_artifact_path(run_root, str(artifacts["manifest"]))
        evaluation_path = _run_artifact_path(
            run_root, str(artifacts["evaluation"])
        )
        repaired_path = _run_artifact_path(
            run_root, str(artifacts["successful_ifc"])
        )
        manifest = _read_json(manifest_path)
        _verify_published_manifest(run_root, manifest)
        evaluation = _read_json(evaluation_path)
        changeset_path = run_root / "changeset" / "bound-changeset.json"
        if not changeset_path.is_file():
            changeset_path = run_root / "changeset.json"
        changeset = _read_json(changeset_path)
        evidence_path = manifest_path.parent / "terminal" / "evidence.json"
        evidence = _read_json(evidence_path).get("evidence")
        if not isinstance(evidence, Mapping):
            raise ValueError("terminal evidence payload is missing")
        application = evidence.get("application")
        if not isinstance(application, Mapping):
            raise ValueError("terminal application evidence is missing")

        repaired = ifcopenshell.open(str(repaired_path))
        operations = changeset.get("operations")
        if not isinstance(operations, list) or not operations:
            raise ValueError("bound ChangeSet operations are missing")
        _verify_l0(
            run_root=run_root,
            changeset=changeset,
            application=application,
            evaluation=evaluation,
            repaired_schema=str(repaired.schema),
            operation_count=len(operations),
        )
        recomputed = audit_repaired_operations(
            changeset=changeset,
            application=application,
            repaired_model=repaired,
        )
        l1_pass = recomputed["l1_operation_count"] == len(operations)
        l2_pass = recomputed["l2_operation_count"] == len(operations)
        if not l1_pass or not l2_pass:
            raise ValueError("independent operation count mismatch")
        return {
            "status": "passed",
            "l0_pass": True,
            "l1_pass": l1_pass,
            "l2_pass": l2_pass,
            "operation_count": len(operations),
            "reopened_schema": str(repaired.schema),
            "successful_ifc_sha256": "sha256:" + _sha256(repaired_path),
            "changeset": changeset_path.relative_to(run_root).as_posix(),
            "application_evidence": evidence_path.relative_to(run_root).as_posix(),
            "evaluation": evaluation_path.relative_to(run_root).as_posix(),
        }
    except Exception as error:
        return {
            "status": "failed",
            "l0_pass": False,
            "l1_pass": False,
            "l2_pass": False,
            "reason": f"{type(error).__name__}: {error}"[:512],
        }


def _verify_l0(
    *,
    run_root: Path,
    changeset: Mapping[str, Any],
    application: Mapping[str, Any],
    evaluation: Mapping[str, Any],
    repaired_schema: str,
    operation_count: int,
) -> None:
    state = _read_json(run_root / "state.json")
    source = state.get("source")
    if not isinstance(source, Mapping):
        raise ValueError("run state source binding is missing")
    if repaired_schema != "IFC2X3":
        raise ValueError(f"repaired schema is {repaired_schema}")
    if changeset.get("binding_status") != "bound":
        raise ValueError("ChangeSet is not bound")
    if changeset.get("base_model_fingerprint") != source.get("sha256"):
        raise ValueError("ChangeSet base fingerprint does not match run source")
    if application.get("valid") is not True or application.get("published") is not True:
        raise ValueError("application evidence is not a valid publication")
    applied = application.get("operations")
    if not isinstance(applied, list) or len(applied) != operation_count:
        raise ValueError("application operation count mismatch")
    if evaluation.get("status") != "passed":
        raise ValueError("public evaluation status is not passed")
    if evaluation.get("complete_repair_success") is not True:
        raise ValueError("public evaluation complete flag is false")
    if evaluation.get("successful_artifact_publishable") is not True:
        raise ValueError("public evaluation publishable flag is false")
    for gate in ("application", "preservation"):
        value = evaluation.get(gate)
        if not isinstance(value, Mapping) or value.get("status") != "passed":
            raise ValueError(f"public evaluation {gate} gate is not passed")
    evaluated = evaluation.get("operations")
    if not isinstance(evaluated, list) or len(evaluated) != operation_count:
        raise ValueError("public evaluation operation count mismatch")
    for operation in evaluated:
        levels = {
            str(item.get("level")): str(item.get("status"))
            for item in operation.get("levels", ())
            if isinstance(item, Mapping)
        }
        if levels.get("L1") != "passed" or levels.get("L2") != "passed":
            raise ValueError(
                f"saved evaluation failed for {operation.get('operation_id')}"
            )


def _run_artifact_path(run_root: Path, relative: str) -> Path:
    path = (run_root / relative).resolve()
    try:
        path.relative_to(run_root)
    except ValueError as error:
        raise ValueError(f"artifact escapes run root: {relative}") from error
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def _verify_published_manifest(
    run_root: Path, manifest: Mapping[str, Any]
) -> None:
    entries = manifest.get("artifacts")
    if not isinstance(entries, list) or not entries:
        raise ValueError("published manifest is empty")
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise ValueError("published manifest entry is invalid")
        path = _run_artifact_path(run_root, str(entry.get("path")))
        if path.stat().st_size != int(entry.get("size_bytes", -1)):
            raise ValueError(f"published artifact size mismatch: {path.name}")
        if _sha256(path) != str(entry.get("sha256")):
            raise ValueError(f"published artifact hash mismatch: {path.name}")


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root is not an object: {path}")
    return payload


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact_hashes(root: Path) -> dict[str, str]:
    result = {}
    for path in sorted(root.rglob("*.json")):
        if any(token in path.name.lower() for token in ("secret", "env")):
            continue
        result[path.relative_to(root).as_posix()] = (
            "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
        )
    return result


def _run_case(
    root: Path,
    environment: dict[str, str],
    *,
    case_id: str,
    request: str,
    feedback: str | None,
    expectation: dict[str, Any],
) -> dict[str, Any]:
    case_dir = root / case_id
    case_dir.mkdir(parents=True)
    fixture = case_dir / "fixture"
    remove_door(
        source_path=SOURCE,
        output_dir=fixture,
        door_global_id=DOOR_ID,
        preserve_opening=True,
    )
    runtime = case_dir / "runtime"
    try:
        api = RepairAPI.from_environment(runtime, environment)
        initial = api.start(fixture / "damaged.ifc", request)
        clarification = initial.clarification
        clarification_payload = (
            None
            if clarification is None
            else {
                "clarification_id": clarification.clarification_id,
                "reason_code": clarification.reason_code,
                "question": clarification.question,
                "answer_modes": list(clarification.answer_modes),
            }
        )
        final = initial
        feedback_applied = False
        if feedback is not None and clarification is not None:
            final = api.continue_with_answer(
                initial.run_id,
                {"kind": "add_detail", "detail": feedback},
                clarification_id=clarification.clarification_id,
                expected_state_version=initial.state_version,
            )
            feedback_applied = True
        attempts = _attempts(runtime)
        final_summary = _summary(final)
        strict_verification = _strict_reopen_verification(
            runtime, final_summary
        )
        (case_dir / "strict-reopen-verification.json").write_text(
            json.dumps(
                strict_verification,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        contract_pass = _contract_pass(
            final=final_summary,
            attempts=attempts,
            expectation=expectation,
            feedback_expected=feedback is not None,
            feedback_applied=feedback_applied,
            strict_verification=strict_verification,
        )
        payload = {
            "case_id": case_id,
            "status": "passed" if contract_pass else "failed",
            "request_sha256": "sha256:"
            + hashlib.sha256(request.encode("utf-8")).hexdigest(),
            "feedback_sha256": (
                None
                if feedback is None
                else "sha256:"
                + hashlib.sha256(feedback.encode("utf-8")).hexdigest()
            ),
            "initial": _summary(initial),
            "clarification": clarification_payload,
            "feedback_applied": feedback_applied,
            "final": final_summary,
            "provider_attempts": attempts,
            "strict_reopen_verification": strict_verification,
            "synthetic_fallback_used": False,
            "contract_pass": contract_pass,
            "artifact_hashes": _artifact_hashes(runtime),
        }
    except Exception as error:
        payload = {
            "case_id": case_id,
            "status": "provider_failed",
            "reason_code": str(getattr(error, "code", type(error).__name__))[:160],
            "provider_attempts": _attempts(runtime),
            "synthetic_fallback_used": False,
            "contract_pass": False,
            "artifact_hashes": _artifact_hashes(runtime),
        }
    (case_dir / "case-result.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-config", action="store_true")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    if args.check_config == args.live:
        parser.error("choose exactly one of --check-config or --live")
    environment = _environment(args.env_file)
    config = _config(environment)
    if args.check_config:
        print(json.dumps(config, ensure_ascii=False, sort_keys=True))
        return 0 if config["status"] == "ready" else 2
    if config["status"] != "ready":
        print(json.dumps(config, ensure_ascii=False, sort_keys=True))
        return 2
    run_dir = args.output_root / datetime.now(timezone.utc).strftime(
        "uat-%Y%m%dT%H%M%S%fZ"
    )
    run_dir.mkdir(parents=True)
    cases = [
        _run_case(
            run_dir,
            environment,
            case_id="complete-door",
            request=COMPLETE_REQUEST,
            feedback=None,
            expectation={
                "status": "succeeded",
                "publish": True,
                "stage2_attempts": 1,
            },
        ),
        _run_case(
            run_dir,
            environment,
            case_id="incomplete-then-feedback",
            request=INCOMPLETE_REQUEST,
            feedback=CLARIFICATION_DETAIL,
            expectation={
                "status": "succeeded",
                "publish": True,
                "stage2_attempts": 1,
            },
        ),
        _run_case(
            run_dir,
            environment,
            case_id="unsupported-complex-door",
            request=UNSUPPORTED_REQUEST,
            feedback=None,
            expectation={
                "status": "unsupported",
                "reason_code": "DOOR_OPERATION_TYPE_UNSUPPORTED",
                "publish": False,
                "stage2_attempts": 0,
            },
        ),
    ]
    passed = all(item["contract_pass"] for item in cases)
    result = {
        "schema_version": "text2ifc/phase11-live-uat/0.1",
        "status": "passed" if passed else "failed",
        "provider": config["provider"],
        "model": config["model"],
        "token_guard": {
            "max_input_tokens": TOKEN_GUARD,
            "max_completion_tokens": TOKEN_GUARD,
        },
        "cases": cases,
        "synthetic_fallback_used": False,
    }
    (run_dir / "live-uat-result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "cases": [
                    {
                        "case_id": item["case_id"],
                        "status": item["status"],
                        "provider_attempts": item["provider_attempts"],
                        "contract_pass": item["contract_pass"],
                    }
                    for item in cases
                ],
                "result": str(run_dir / "live-uat-result.json"),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
