"""Install Plan 07 evidence in the direct, human-readable case layout.

The installer creates a review view only.  It deliberately does not add the
cases to the collection's accepted manifest before the requested human check.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

import ifcopenshell


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE_ROOT = (
    ROOT
    / "dataset/processed/proof/ifc-repair-success-cases-v2-plan07-staging"
)
DEFAULT_COLLECTION_ROOT = (
    ROOT / "dataset/processed/proof/ifc-repair-success-cases"
)
LIVE_BUNDLE = "plan07-live-v2-uat-20260903T095045509630Z"


@dataclass(frozen=True)
class CaseSpec:
    source: str
    destination: str
    evidence_mode: str
    outcome: str
    operation_family: str
    operation_types: tuple[str, ...]
    provider_calls: int = 0


OFFLINE_CASES = (
    CaseSpec(
        "structural/single/phase12-v2-vvo-beam-loadbearing-restoration",
        "structural/single/phase12-v2-vvo-beam-loadbearing-restoration",
        "offline_bound_deterministic",
        "repaired",
        "structural",
        ("add_beam",),
    ),
    CaseSpec(
        "structural/single/phase12-v2-vvo-column-loadbearing-restoration",
        "structural/single/phase12-v2-vvo-column-loadbearing-restoration",
        "offline_bound_deterministic",
        "repaired",
        "structural",
        ("add_column",),
    ),
    CaseSpec(
        "structural/batch/phase12-v2-vvo-beam-column-atomic-restoration",
        "structural/batch/phase12-v2-vvo-beam-column-atomic-restoration",
        "offline_bound_deterministic",
        "repaired",
        "structural",
        ("add_beam", "add_column"),
    ),
    CaseSpec(
        "structural/single/phase12-v2-vvo-beam-material-present-restoration",
        "structural/single/phase12-v2-vvo-beam-material-present-restoration",
        "offline_bound_deterministic",
        "repaired",
        "structural",
        ("add_beam",),
    ),
    CaseSpec(
        "structural/single/phase12-v2-vvo-column-material-absent-restoration",
        "structural/single/phase12-v2-vvo-column-material-absent-restoration",
        "offline_bound_deterministic",
        "repaired",
        "structural",
        ("add_column",),
    ),
    CaseSpec(
        (
            "mixed/door-window-beam-column/"
            "phase12-v2-vvo-door-window-beam-column-atomic-restoration"
        ),
        (
            "mixed/door-window-beam-column/"
            "phase12-v2-vvo-door-window-beam-column-atomic-restoration"
        ),
        "offline_bound_deterministic",
        "repaired",
        "mixed",
        (
            "add_beam",
            "add_column",
            "add_window_with_opening_to_wall",
            "fill_existing_opening_with_door",
        ),
    ),
)

LIVE_CASES = (
    CaseSpec(
        "complete",
        "structural/batch/phase12-plan07-live-beam-column-complete",
        "live",
        "repaired",
        "structural",
        ("add_beam", "add_column"),
        4,
    ),
    CaseSpec(
        "clarification-resume",
        "structural/single/phase12-plan07-live-column-clarification-resume",
        "live",
        "repaired",
        "structural",
        ("add_column",),
        3,
    ),
    CaseSpec(
        "window-semantic-canary",
        "window/single/phase12-plan07-live-window-property-repair",
        "live",
        "repaired",
        "window",
        ("set_occurrence_properties",),
        3,
    ),
    CaseSpec(
        "program-guard",
        "guard/unsupported/phase12-plan07-live-structural-program-guard",
        "live",
        "expected_no_repair",
        "guard",
        (),
        1,
    ),
)
ALL_CASES = (*OFFLINE_CASES, *LIVE_CASES)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        value.rstrip() + "\n", encoding="utf-8", newline="\n"
    )


def _write_json(path: Path, value: Any) -> None:
    _write_text(
        path,
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True),
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _copy(source: Path, destination: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def _offline_destination(relative: str) -> str | None:
    direct = {
        "original.ifc": "01-original.ifc",
        "damaged.ifc": "02-damaged.ifc",
        "repaired.ifc": "03-repaired.ifc",
        "request.txt": "input/request.txt",
        "repair-intent.json": "agent/repair-intent.json",
        "target-resolution.json": "agent/target-resolution.json",
        "semantic-manifest.json": "agent/semantic-manifest.json",
        "semantic-manifests.json": "agent/semantic-manifests.json",
        "production-evidence.json": "agent/production-evidence.json",
        "changeset.json": "changeset/bound-changeset.json",
        "application.json": "validation/application.json",
        "evaluation.json": "validation/production-evaluation.json",
        "comparison.json": "validation/ifc-comparison.json",
        "structural-restoration-audit.json": (
            "validation/structural-restoration-audit.json"
        ),
        "production-boundary.json": "validation/production-boundary.json",
        "manifest.json": "validation/source-run-manifest.json",
        "mutation_report.json": "private-evaluation/mutation-report.json",
        "mutation_manifest.private.json": (
            "private-evaluation/mutation-manifest.json"
        ),
    }
    if relative in direct:
        return direct[relative]
    if relative.startswith("property-resolution/"):
        return "agent/" + relative
    if relative.startswith(".validation-cache/") or relative == "target-index.sqlite":
        return None
    return "validation/source/" + relative


def _files_document(
    case_root: Path, case_id: str, roles: Mapping[str, str]
) -> None:
    entries = []
    for relative, role in sorted(roles.items()):
        path = case_root / relative
        entries.append(
            {
                "path": relative,
                "role": role,
                "sha256": _sha256(path),
                "size_bytes": path.stat().st_size,
            }
        )
    _write_json(
        case_root / "FILES.json",
        {
            "schema_version": "text2ifc/ifc-repair-proof-files/0.2",
            "case_id": case_id,
            "files": entries,
        },
    )


def _offline_report(case_root: Path, spec: CaseSpec) -> str:
    audit = _read_json(
        case_root / "validation/structural-restoration-audit.json"
    )
    evaluation = _read_json(
        case_root / "validation/production-evaluation.json"
    )
    changeset = _read_json(case_root / "changeset/bound-changeset.json")
    operation_count = len(changeset.get("operations", ()))
    return f"""# {Path(spec.destination).name}

## 结论

本案例通过。它是 Plan 07 修正后的离线确定性 operation-engine Proof，不是真实 Provider 调用。

- Evidence mode：offline_bound_deterministic
- Provider calls：0
- Operations：{operation_count}
- Operation types：{', '.join(spec.operation_types)}
- Application：{evaluation.get('application', {}).get('status')}
- Preservation：{evaluation.get('preservation', {}).get('status')}
- Structural restoration：{audit.get('status')}
- Linear tolerance：{audit.get('axis_tolerance_mm', 0.01)} mm
- Orientation tolerance：{audit.get('orientation_tolerance_degrees', 0.1)}°

## 最短检查路径

1. 打开 01-original.ifc、02-damaged.ifc、03-repaired.ifc 对照构件位置。
2. 阅读 input/request.txt。
3. 查看 agent/repair-intent.json 与 agent/target-resolution.json。
4. 查看 changeset/bound-changeset.json。
5. 查看 validation/structural-restoration-audit.json、validation/production-evaluation.json 和 validation/ifc-comparison.json。
6. 通过 [evidence/README.md](evidence/README.md) 回到完整机器权威包。

## 证据边界

三份 IFC 是该冻结损伤案例的合法 original/damaged/repaired 三元组。证据只支持单场景 BIMNet VVO restoration，不声称跨场景或跨数据集能力。完整机器权威仍保留在已提交的 Plan 07 v2 staging collection。
"""


def _copy_offline_case(
    source_root: Path, case_root: Path, spec: CaseSpec
) -> None:
    source = source_root / spec.source
    source_files = _read_json(source / "FILES.json")
    roles: dict[str, str] = {}
    for entry in source_files.get("files", ()):
        relative = str(entry["path"])
        destination = _offline_destination(relative)
        if destination is None:
            continue
        _copy(source / relative, case_root / destination)
        roles[destination] = str(entry["role"])
    report = _offline_report(case_root, spec)
    _write_text(case_root / "REPORT.md", report)
    _write_text(case_root / "validation/AUDIT-REPORT.md", report)
    roles["validation/AUDIT-REPORT.md"] = "human_validation_report"
    _files_document(case_root, Path(spec.destination).name, roles)


def _live_roles(spec: CaseSpec) -> dict[str, tuple[str, str]]:
    common = {
        "original.ifc": (
            "01-original.ifc",
            "physical_fixture_non_private_audit",
        ),
        "damaged.ifc": ("02-damaged.ifc", "repair_input_ifc"),
        "repaired.ifc": (
            "03-repaired.ifc",
            "published_repair_output",
        ),
        "request.txt": ("input/request.txt", "user_request"),
        "clarification-answer.txt": (
            "input/clarification-answer.txt",
            "public_clarification_answer",
        ),
        "repair-intent.json": (
            "agent/repair-intent.json",
            "stage1_repair_intent",
        ),
        "target-resolution.json": (
            "agent/target-resolution.json",
            "deterministic_target_resolution",
        ),
        "provider-draft.json": (
            "agent/provider-draft.json",
            "provider_stage2_draft",
        ),
        "prompt-profile-selection.json": (
            "agent/prompt-profile-selection.json",
            "prompt_profile_selection",
        ),
        "case-result.json": (
            "agent/provider-attempts.json",
            "genuine_provider_attempt_ledger",
        ),
        "changeset.json": (
            "changeset/bound-changeset.json",
            "bound_changeset",
        ),
        "application.json": (
            "validation/application.json",
            "application_result",
        ),
        "evaluation.json": (
            "validation/production-evaluation.json",
            "production_evaluation",
        ),
        "proof-result.json": (
            "validation/evidence-decision.json",
            "independent_evidence_result",
        ),
        "structural-restoration-audit.json": (
            "validation/structural-restoration-audit.json",
            "structural_restoration_audit",
        ),
        "base-damage-manifest.json": (
            "validation/base-damage-source-manifest.json",
            "base_damage_source_manifest",
        ),
        "source-role.json": (
            "private-evaluation/original-role.json",
            "original_role_declaration",
        ),
        "mutation_manifest.private.json": (
            "private-evaluation/mutation-manifest.json",
            "mutation_manifest_private",
        ),
    }
    if spec.outcome == "expected_no_repair":
        allowed = {
            "damaged.ifc",
            "request.txt",
            "case-result.json",
            "proof-result.json",
        }
        return {
            key: value for key, value in common.items() if key in allowed
        }
    return common


def _live_report(case_root: Path, spec: CaseSpec) -> str:
    decision = _read_json(
        case_root / "validation/evidence-decision.json"
    )
    if spec.outcome == "expected_no_repair":
        return f"""# {Path(spec.destination).name}

## 结论

本案例通过，正确结果是不生成 repaired IFC。请求要求系统完成结构分析程序设计，超出 IFC repair operation 合同，因此 Stage 1 后 fail closed。

- Provider/model：deepseek-openai-compatible / deepseek-v4-flash
- Provider calls：1（Stage 1=1，Stage 1.5=0，Stage 2=0）
- Reason：{decision.get('reason_code')}
- Mutation attempted：{decision.get('mutation_attempted')}
- Published outputs：{len(decision.get('published_outputs', ()))}
- Source unchanged：{decision.get('source_unchanged')}

## 最短检查路径

1. 阅读 input/request.txt。
2. 阅读 NO-REPAIR.md。
3. 查看 agent/provider-attempts.json 和 validation/evidence-decision.json。
4. 通过 [evidence/README.md](evidence/README.md) 回到完整机器权威包。

该目录故意没有 03-repaired.ifc。出现 repaired IFC 反而表示 guard 失败。
"""
    source = _read_json(case_root / "agent/provider-attempts.json")
    return f"""# {Path(spec.destination).name}

## 结论

本案例通过。真实 DeepSeek Provider 输出经过确定性解析、绑定、apply、发布并重新打开 repaired IFC。

- Provider/model：deepseek-openai-compatible / deepseek-v4-flash
- Provider calls：{spec.provider_calls}
- Runtime run ID：{source.get('final', {}).get('run_id')}
- Operations：{decision.get('operation_count')}
- Operation types：{', '.join(spec.operation_types)}
- L0/L1/L2：{decision.get('l0_pass')} / {decision.get('l1_pass')} / {decision.get('l2_pass')}
- Evidence validation：{decision.get('evidence_validation_status')}

## 最短检查路径

1. 打开 01-original.ifc、02-damaged.ifc、03-repaired.ifc。
2. 阅读 input/request.txt；澄清案例另有 input/clarification-answer.txt。
3. 查看 agent/repair-intent.json、agent/target-resolution.json 与 agent/provider-attempts.json。
4. 查看 changeset/bound-changeset.json。
5. 查看 validation/evidence-decision.json、validation/production-evaluation.json；结构案例另看 validation/structural-restoration-audit.json。
6. 通过 [evidence/README.md](evidence/README.md) 回到完整机器权威包。

## original 与 IFCCompare 边界

01-original.ifc 的角色是 physical_fixture_non_private_audit：它用于人工结构/物理对照，未发送给 Provider，也不被事后改称 case-specific private Ground Truth。因此本案例不声称 publishable private IFCCompare。当前目录证明 genuine Provider execution 和 case-local L0/L1/L2；Plan 07 是否最终接受等待本次人工检查，R1 不在此目录范围内。
"""


def _copy_live_case(
    source_root: Path, case_root: Path, spec: CaseSpec
) -> None:
    source = source_root / LIVE_BUNDLE / "cases" / spec.source
    roles: dict[str, str] = {}
    for source_name, (destination, role) in _live_roles(spec).items():
        path = source / source_name
        if path.is_file():
            _copy(path, case_root / destination)
            roles[destination] = role
    if spec.outcome == "expected_no_repair":
        _copy(source / "NO-REPAIR.md", case_root / "NO-REPAIR.md")
        roles["NO-REPAIR.md"] = "expected_no_output_explanation"
    report = _live_report(case_root, spec)
    _write_text(case_root / "REPORT.md", report)
    _write_text(case_root / "validation/AUDIT-REPORT.md", report)
    roles["validation/AUDIT-REPORT.md"] = "human_validation_report"
    _files_document(case_root, Path(spec.destination).name, roles)


def _manifest_case(spec: CaseSpec) -> dict[str, Any]:
    case_id = Path(spec.destination).name
    return {
        "case_id": case_id,
        "path": spec.destination,
        "evidence_mode": spec.evidence_mode,
        "outcome": spec.outcome,
        "operation_family": spec.operation_family,
        "operation_types": list(spec.operation_types),
        "provider_calls": spec.provider_calls,
        "human_report": f"{spec.destination}/REPORT.md",
        "files": f"{spec.destination}/FILES.json",
        "accepted_collection_status": "pending_human_review",
    }


def _authority_case_root(source_root: Path, spec: CaseSpec) -> Path:
    if spec.evidence_mode == "live":
        return source_root / LIVE_BUNDLE / "cases" / spec.source
    return source_root / spec.source


def _authority_readme(
    source_root: Path, collection_root: Path, spec: CaseSpec
) -> str:
    case_root = collection_root / spec.destination
    authority_root = _authority_case_root(source_root, spec)
    relative = Path(os.path.relpath(authority_root, case_root)).as_posix()
    return f"""# Machine authority

本目录是便于人工检查的展示视图，不改变证据状态。完整的 Provider、runtime、ChangeSet 和验证材料以原始机器权威包为准。

- [Authoritative source bundle]({relative})
- Evidence mode：{spec.evidence_mode}
- Outcome：{spec.outcome}
- Collection status：pending_human_review

展示视图与机器权威的关系由 FILES.json 记录。该链接只提供追溯路径，不把 pending review 提升为 accepted Proof。
"""


def refresh_plan07_navigation(
    source_root: Path, collection_root: Path
) -> None:
    """Refresh presentation metadata without rewriting machine authority."""

    source_root = source_root.resolve()
    collection_root = collection_root.resolve()
    for spec in ALL_CASES:
        case_root = collection_root / spec.destination
        if not case_root.is_dir():
            raise FileNotFoundError(case_root)
        source_files = _read_json(case_root / "FILES.json").get(
            "files", ()
        )
        roles = {
            str(entry["path"]): str(entry["role"])
            for entry in source_files
            if str(entry["path"]) != "evidence/README.md"
        }
        report = (
            _live_report(case_root, spec)
            if spec.evidence_mode == "live"
            else _offline_report(case_root, spec)
        )
        _write_text(case_root / "REPORT.md", report)
        _write_text(case_root / "validation/AUDIT-REPORT.md", report)
        _write_text(
            case_root / "evidence/README.md",
            _authority_readme(source_root, collection_root, spec),
        )
        roles["validation/AUDIT-REPORT.md"] = "human_validation_report"
        roles["evidence/README.md"] = "machine_authority_navigation"
        _files_document(case_root, Path(spec.destination).name, roles)


def _collection_report() -> str:
    rows = []
    for spec in ALL_CASES:
        case_id = Path(spec.destination).name
        mode = (
            "真实 Provider"
            if spec.evidence_mode == "live"
            else "离线确定性"
        )
        result = (
            "无输出（正确 guard）"
            if spec.outcome == "expected_no_repair"
            else "repaired IFC"
        )
        rows.append(
            f"| [{case_id}]({spec.destination}/REPORT.md) | {mode} | "
            f"{spec.provider_calls} | {result} |"
        )
    return """# Phase 12 Plan 07 Proof — 人工验收入口

本页只汇总修正后的 Plan 07 证据，不包含 Repair Milestone R1。案例目录按既有 door/batch/vvo-five-door-authority-public-repair 的方式组织：IFC 直接位于案例根目录，输入、Agent、ChangeSet、验证和私有评估分别归档。

当前状态：待人工检查。这些目录尚未写入主 manifest.json 的 accepted 列表；检查通过后再完成 Plan 07 最终状态更新。

## 案例矩阵

| 案例 | 证据类型 | Provider calls | 产物 |
|---|---|---:|---|
""" + "\n".join(rows) + """

## 总结

- 离线矩阵：6 个 repaired case，12 个 operation；证明通用 restoration、原子性和保存性路径。
- Genuine run：uat-20260903T095045509630Z，11 次真实调用；3 个 repaired case、1 个 expected no-repair guard。
- 结构几何线性容差：0.01 mm；方向容差：0.1°。
- 旧 offsite Beam/Column 结果已撤下，只作为负向回归 fixture 保留。
- R1 不属于本次人工验收范围，后续单独处理。

## 证据边界

离线与 live 证据明确分开。Live 案例的 01-original.ifc 只承担物理对照角色，不伪装成 case-specific private Ground Truth；因此没有合法私有 truth 的案例不会声称 publishable IFCCompare。
"""


def install(source_root: Path, collection_root: Path) -> dict[str, Any]:
    source_root = source_root.resolve()
    collection_root = collection_root.resolve()
    if not source_root.is_dir() or not collection_root.is_dir():
        raise FileNotFoundError(
            "Plan 07 source or collection root is missing"
        )
    targets = [collection_root / spec.destination for spec in ALL_CASES]
    existing = [path for path in targets if path.exists()]
    for name in ("PLAN07-REPORT.md", "plan07-manifest.json"):
        if (collection_root / name).exists():
            existing.append(collection_root / name)
    if existing:
        raise FileExistsError(
            "Plan 07 review target already exists: "
            + ", ".join(str(path) for path in existing)
        )

    temp = Path(
        tempfile.mkdtemp(prefix=".plan07-install-", dir=collection_root)
    )
    try:
        for spec in OFFLINE_CASES:
            _copy_offline_case(
                source_root, temp / spec.destination, spec
            )
        for spec in LIVE_CASES:
            _copy_live_case(source_root, temp / spec.destination, spec)
        _write_text(temp / "PLAN07-REPORT.md", _collection_report())
        _write_json(
            temp / "plan07-manifest.json",
            {
                "schema_version": (
                    "text2ifc/plan07-human-proof-collection/0.1"
                ),
                "plan": "Phase 12 Plan 07",
                "status": "pending_human_review",
                "r1_included": False,
                "live_run_id": "uat-20260903T095045509630Z",
                "live_provider_calls": 11,
                "cases": [
                    _manifest_case(spec) for spec in ALL_CASES
                ],
            },
        )
        for spec in ALL_CASES:
            destination = collection_root / spec.destination
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(temp / spec.destination), destination)
        shutil.move(
            str(temp / "PLAN07-REPORT.md"),
            collection_root / "PLAN07-REPORT.md",
        )
        shutil.move(
            str(temp / "plan07-manifest.json"),
            collection_root / "plan07-manifest.json",
        )
        refresh_plan07_navigation(source_root, collection_root)
    finally:
        if temp.exists():
            shutil.rmtree(temp)
    return validate_plan07_layout(collection_root)


def validate_plan07_layout(
    collection_root: Path,
    source_root: Path = DEFAULT_SOURCE_ROOT,
) -> dict[str, Any]:
    collection_root = collection_root.resolve()
    source_root = source_root.resolve()
    errors: list[str] = []
    reopened = 0
    repaired = 0
    no_repair = 0
    live_calls = 0
    manifest_path = collection_root / "plan07-manifest.json"
    if not manifest_path.is_file():
        return {
            "status": "failed",
            "errors": ["missing plan07-manifest.json"],
            "case_count": 0,
            "repaired_case_count": 0,
            "no_repair_case_count": 0,
            "live_provider_calls": 0,
            "reopened_ifc_count": 0,
            "accepted_overlap_count": 0,
        }
    manifest = _read_json(manifest_path)
    if manifest.get("status") != "pending_human_review":
        errors.append("plan07 manifest status must remain pending_human_review")
    if manifest.get("r1_included") is not False:
        errors.append("plan07 review manifest must exclude R1")
    cases = manifest.get("cases")
    if not isinstance(cases, list) or len(cases) != 10:
        errors.append("plan07 manifest must contain exactly 10 cases")
        cases = cases if isinstance(cases, list) else []
    accepted_manifest_path = collection_root / "manifest.json"
    accepted_ids: set[str] = set()
    if accepted_manifest_path.is_file():
        accepted_cases = _read_json(accepted_manifest_path).get("cases", ())
        accepted_ids = {
            str(case.get("case_id"))
            for case in accepted_cases
            if isinstance(case, dict)
        }
    review_ids = {
        str(case.get("case_id")) for case in cases if isinstance(case, dict)
    }
    accepted_overlap = accepted_ids & review_ids
    if accepted_overlap:
        errors.append(
            "pending Plan 07 cases overlap accepted manifest: "
            + ", ".join(sorted(accepted_overlap))
        )
    specs = {Path(spec.destination).name: spec for spec in ALL_CASES}
    for case in cases:
        path = collection_root / str(case.get("path"))
        try:
            case_id = str(case.get("case_id"))
            spec = specs.get(case_id)
            if spec is None:
                raise ValueError("case is not in frozen Plan 07 case set")
            if case.get("accepted_collection_status") != "pending_human_review":
                raise ValueError("case status must remain pending_human_review")
            if not (path / "REPORT.md").is_file():
                raise ValueError("REPORT.md missing")
            if not (path / "FILES.json").is_file():
                raise ValueError("FILES.json missing")
            if not (path / "input/request.txt").is_file():
                raise ValueError("input/request.txt missing")
            files = _read_json(path / "FILES.json").get("files", ())
            file_roles = {
                str(entry["path"]): str(entry["role"])
                for entry in files
            }
            for entry in files:
                artifact = path / str(entry["path"])
                if not artifact.is_file():
                    raise ValueError(
                        f"listed artifact missing: {entry['path']}"
                    )
            authority_readme = path / "evidence/README.md"
            if file_roles.get("evidence/README.md") != (
                "machine_authority_navigation"
            ):
                raise ValueError("machine authority navigation is not listed")
            authority_text = authority_readme.read_text(encoding="utf-8")
            match = re.search(
                r"\[Authoritative source bundle\]\(([^)]+)\)",
                authority_text,
            )
            if match is None:
                raise ValueError("machine authority link is missing")
            linked_authority = (path / match.group(1)).resolve()
            expected_authority = _authority_case_root(source_root, spec).resolve()
            if linked_authority != expected_authority or not linked_authority.is_dir():
                raise ValueError("machine authority link does not resolve")
            if "evidence/README.md" not in (path / "REPORT.md").read_text(
                encoding="utf-8"
            ):
                raise ValueError("REPORT.md does not link machine authority")
            if case.get("outcome") == "repaired":
                for name in (
                    "01-original.ifc",
                    "02-damaged.ifc",
                    "03-repaired.ifc",
                ):
                    model = ifcopenshell.open(str(path / name))
                    if model.schema != "IFC2X3":
                        raise ValueError(f"{name} is not IFC2X3")
                    reopened += 1
                if (path / "NO-REPAIR.md").exists():
                    raise ValueError(
                        "repaired case contains NO-REPAIR.md"
                    )
                if case.get("evidence_mode") == "live":
                    role = _read_json(
                        path / "private-evaluation/original-role.json"
                    )
                    if (
                        role.get("original_is_case_specific_property_gold")
                        is not False
                        or role.get("private_evidence_available_during_repair")
                        is not False
                    ):
                        raise ValueError("live original role boundary mismatch")
                elif file_roles.get("01-original.ifc") != (
                    "original_ground_truth"
                ):
                    raise ValueError("offline original role boundary mismatch")
                repaired += 1
            elif case.get("outcome") == "expected_no_repair":
                model = ifcopenshell.open(
                    str(path / "02-damaged.ifc")
                )
                if model.schema != "IFC2X3":
                    raise ValueError(
                        "guard damaged IFC is not IFC2X3"
                    )
                reopened += 1
                if not (path / "NO-REPAIR.md").is_file():
                    raise ValueError("guard is missing NO-REPAIR.md")
                if (path / "03-repaired.ifc").exists():
                    raise ValueError(
                        "guard unexpectedly contains repaired IFC"
                    )
                decision = _read_json(
                    path / "validation/evidence-decision.json"
                )
                if (
                    decision.get("mutation_attempted") is not False
                    or decision.get("source_unchanged") is not True
                    or decision.get("stage2_attempts") != 0
                    or decision.get("published_outputs") != []
                ):
                    raise ValueError(
                        "guard fail-closed evidence mismatch"
                    )
                no_repair += 1
            else:
                raise ValueError("unknown Plan 07 outcome")
            if case.get("evidence_mode") == "live":
                live_calls += int(case.get("provider_calls", 0))
        except Exception as error:
            errors.append(f"{case.get('case_id')}: {error}")
    if not (collection_root / "PLAN07-REPORT.md").is_file():
        errors.append("missing PLAN07-REPORT.md")
    return {
        "status": "passed" if not errors else "failed",
        "errors": errors,
        "case_count": len(cases),
        "repaired_case_count": repaired,
        "no_repair_case_count": no_repair,
        "live_provider_calls": live_calls,
        "reopened_ifc_count": reopened,
        "accepted_overlap_count": len(accepted_overlap),
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-root", type=Path, default=DEFAULT_SOURCE_ROOT
    )
    parser.add_argument(
        "--collection-root", type=Path, default=DEFAULT_COLLECTION_ROOT
    )
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--validate-only", action="store_true")
    action.add_argument("--refresh-navigation", action="store_true")
    args = parser.parse_args(argv)
    if args.refresh_navigation:
        refresh_plan07_navigation(args.source_root, args.collection_root)
        result = validate_plan07_layout(
            args.collection_root, args.source_root
        )
    elif args.validate_only:
        result = validate_plan07_layout(
            args.collection_root, args.source_root
        )
    else:
        result = install(args.source_root, args.collection_root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
