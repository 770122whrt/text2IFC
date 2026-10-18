"""Curate only the completed, model-free 020 after-answer support material."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
from copy import deepcopy

REPO = Path(__file__).resolve().parents[2]
BASE = REPO / ".tmp/repair-comparison-formal-expansion"
PACKAGE = BASE / "next-ten-packages/formal-020"
ROOT = PACKAGE / "private/offline-support/window-property-after-answer"


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(path: Path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")


def sha(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


result = read(ROOT / "result.json")
receipt = read(BASE / "next_ten_020_mixed_after_prefix_fix.receipt.json")
if not result["passed"] or receipt["exit_code"] != 0 or result["provider_calls"] != 0:
    raise ValueError("ONLY_COMPLETED_PASSED_OFFLINE_SUPPORT_CAN_BE_CURATED")
import ifcopenshell


def property_snapshot(entity):
    definitions = list(getattr(entity, "HasPropertySets", ()) or ())
    definitions += [relationship.RelatingPropertyDefinition
                    for relationship in getattr(entity, "IsDefinedBy", ())
                    if relationship.is_a("IfcRelDefinesByProperties")]
    snapshots = []
    for definition in definitions:
        if definition.is_a("IfcPropertySet"):
            properties = [item.get_info(recursive=True, include_identifier=False)
                          for item in definition.HasProperties]
            snapshots.append({"set_name": definition.Name, "description": definition.Description,
                              "properties": sorted(properties, key=lambda item: json.dumps(item, sort_keys=True))})
        else:
            snapshots.append({"other_property_definition": definition.get_info(recursive=True, include_identifier=False)})
    return sorted(snapshots, key=lambda item: json.dumps(item, sort_keys=True))


# Independent, post-publication check of all existing instance and Type
# property values. Target Pset GUID allowlists alone do not verify its siblings.
damaged_model = ifcopenshell.open(ROOT / "damaged.ifc")
repaired_model = ifcopenshell.open(ROOT / "repaired.ifc")
door_id = read(ROOT / "public-selection.json")["door_id"]
differences, target_value_count, object_count = [], 0, 0
for entity in [*damaged_model.by_type("IfcObject"), *damaged_model.by_type("IfcTypeObject")]:
    before = property_snapshot(entity)
    expected = deepcopy(before)
    if str(entity.GlobalId) == door_id:
        for definition in expected:
            if definition.get("set_name") != "Pset_DoorCommon":
                continue
            for item in definition["properties"]:
                if item.get("Name") != "IsExternal":
                    continue
                if item["NominalValue"] != {"type": "IfcBoolean", "wrappedValue": False} or item["Unit"] is not None:
                    raise ValueError("SUPPLEMENTAL_D_PROPERTY_BASELINE_NOT_EXPECTED_FALSE_BOOLEAN")
                item["NominalValue"]["wrappedValue"] = True
                target_value_count += 1
    after = property_snapshot(repaired_model.by_guid(str(entity.GlobalId)))
    if expected != after:
        differences.append({"guid": str(entity.GlobalId), "class": entity.is_a(), "name": entity.Name,
                            "expected": expected, "actual": after})
    object_count += 1
property_preservation = {
    "scope": "post-publication public D vs R only; all original IfcObject and IfcTypeObject property definitions",
    "objects_checked": object_count, "expected_existing_property_changes": 1,
    "actual_expected_target_property_matches": target_value_count,
    "only_allowed_delta": "target occurrence Pset_DoorCommon.IsExternal IfcBoolean false -> true, Unit stays None",
    "target_pset_other_properties_also_checked": True,
    "all_other_instance_and_type_properties_checked": True,
    "differences": differences, "provider_calls": 0,
    "passed": not differences and target_value_count == 1,
}
write(ROOT / "existing-property-preservation.json", property_preservation)
shutil.copy2(Path(__file__), ROOT / "curation-and-property-check-source.py")
if not property_preservation["passed"]:
    raise ValueError("SUPPLEMENTAL_EXISTING_PROPERTY_PRESERVATION_FAILED")
for source, target in (
    (BASE / "next_ten_020_mixed_after_prefix_fix.log", ROOT / "run.log"),
    (BASE / "next_ten_020_mixed_after_prefix_fix.receipt.json", ROOT / "run-receipt.json"),
):
    if target.exists():
        raise FileExistsError(target)
    shutil.copy2(source, target)

readiness = {
    "schema_version": "repair-comparison-candidate-pipeline-readiness/0.2",
    "case": "020",
    "evidence": "private/offline-support/window-property-after-answer/result.json",
    "whole_mixed_bound_task_after_prewritten_answer_passed": True,
    "operation_types": result["operation_types"],
    "one_atomic_changeset": True,
    "public_D_only_target_selection": True,
    "initial_request_requires_clarification": True,
    "required_user_facts": ["window_opening_bottom"],
    "initial_public_request_used_verbatim": True,
    "simulated_answer_source": "prewritten answer-card; explicitly simulated, not an observed model question or human reply",
    "exact_standard_property_resolver_manifest_binder_used": True,
    "bound_contract": "text2ifc/ifc-repair-changeset/0.5",
    "production_apply_reopen_evaluation_passed": True,
    "independent_actual_R_geometry_and_typed_boolean_passed": True,
    "independent_all_existing_instance_and_type_properties_preserved": True,
    "existing_property_objects_checked": object_count,
    "source_D_geometry_baseline_reused_after_publication_only": True,
    "source_G_first_parsed_after_publication": True,
    "source_preservation_and_second_operation_atomic_rollback_passed": True,
    "R_native_schema_express_diagnostics": result["repaired_native_diagnostics"],
    "initial_natural_clarification_or_resume_tested": False,
    "natural_property_retrieval_tested": False,
    "full_B_experiment_runtime_verified": False,
    "four_arm_admission": False,
    "provider_calls": 0,
    "human_review_status": "pending_human_review",
    "human_viewed": False,
    "review_acceptance_inherited": False,
    "budget_provider_calls_allowed": False,
    "not_stage_or_formal_admission": True,
    "negative_evidence": [
        "private/offline-support/window-property-after-answer/failed-helper-binding/README.md",
        "private/offline-support/window-property-after-answer/failed-helper-index-prefix/README.md",
    ],
    "negative_evidence_classification": "temporary probe input assembly and canonical fingerprint comparison bugs; no production/schema/IFC change, not model scores",
}
write(PACKAGE / "private/pipeline-readiness.json", readiness)
task_path = PACKAGE / "private/task.json"
task = read(task_path)
if task["review"]["status"] != "pending_human_review" or task["budget"]["provider_calls_allowed"]:
    raise ValueError("CANDIDATE_REVIEW_OR_BUDGET_STATUS_CHANGED")
task["pipeline_readiness"]["bound_window_property_after_answer"] = {
    "passed": True,
    "whole_mixed_task_tested": True,
    "evidence": "private/offline-support/window-property-after-answer/result.json",
    "answer_role": "explicitly simulated prewritten height answer; no observed clarification dialogue",
    "provider_calls": 0,
    "formal_admission": False,
}
write(task_path, task)

(PACKAGE / "PIPELINE-CHECK.md").write_text(
    "# formal-020 离线链路核对\n\n"
    "**待用户审阅、未冻结；本题没有付费模型调用。**\n\n"
    "初始公开请求缺窗洞下沿标高。把预写的 0.6 米答复明确作为离线假回答后，补窗和门外门标记恢复已在同一原子 ChangeSet 中通过现有产品解析、清单绑定、应用、重开与生产评价。输入只含公开 D、原公开请求和该模拟答复；目标身份来自 D 中的实际几何。G 首次解析在产物发布后。\n\n"
    "修复后实际网格核对了窗洞位置和尺寸、同规格参照外观、唯一 0 米楼层归属、门的唯一 IfcBoolean(true)，并确认其余构件几何和原有墙/门正向属性保全。R 的 schema＋EXPRESS 为 0 诊断。明确注入第二项操作失败时不发布半个结果，D 保持不变。制题时已有 D 网格只在发布后的评价侧复用。\n\n"
    "[整题答后执行证据](private/offline-support/window-property-after-answer/README.md) · "
    "[结果](private/offline-support/window-property-after-answer/result.json) · "
    "[运行日志](private/offline-support/window-property-after-answer/run.log) · "
    "[回滚检查](private/offline-support/window-property-after-answer/injected-atomic-rollback.json) · "
    "[全部原有属性保全](private/offline-support/window-property-after-answer/existing-property-preservation.json) · "
    "[就绪状态](private/pipeline-readiness.json)。\n\n"
    "此前单独属性探针仍保留在 [实例属性操作证据](private/offline-support/instance-property/README.md)。"
    "两次组合脚本失败也原样保留：[混合版本选择错误](private/offline-support/window-property-after-answer/failed-helper-binding/README.md)、"
    "[指纹前缀比较错误](private/offline-support/window-property-after-answer/failed-helper-index-prefix/README.md)。两者来自临时检查脚本，修正遵照已有产品契约；未修改生产、schema 或 IFC，也不计为模型成绩。\n\n"
    "本题证据只证明事实明确后的执行可行性；没有测试模型自然提问、真人回复、自然属性检索或完整 B 实验执行器。四组准入和扩展评分尚未冻结。通用真实 B 属性 Runtime 的假 Provider 证据见仓库 dataset/processed/experiments/repair-comparison/development/structural-property-readiness/README.md；它也不等于本题模型成功。浏览器桥接不可用，没有 WebGL 或 usBIM 实际显示验收。\n",
    encoding="utf-8",
)
review_path = PACKAGE / "REVIEW.md"
review = review_path.read_text(encoding="utf-8")
anchor = "完整自然语言属性检索、四组执行与新题评分准入仍待完成；不能把上述绑定探针记为模型成功。\n"
addition = (
    "\n补窗＋属性整题也已在预写高度答复明确后完成离线原子执行、重开和生产评价；独立检查确认新窗实际参照外观、位置尺寸、唯一 0 米楼层归属以及门的唯一 IfcBoolean(true)。R 的 schema＋EXPRESS 为 0 诊断；第二项操作注入失败时整题回滚、不发布部分结果。"
    "这没有生成模型问题或记录真人回答，只证明答复后的执行可行性。\n"
    "[组合执行检查](PIPELINE-CHECK.md) · [自包含执行证据](private/offline-support/window-property-after-answer/README.md)。\n"
)
if anchor not in review or addition in review:
    raise ValueError("REVIEW_ANCHOR_MISSING_OR_ALREADY_UPDATED")
review_path.write_text(review.replace(anchor, anchor+addition), encoding="utf-8")

readme_path = ROOT / "README.md"
readme_path.write_text(readme_path.read_text(encoding="utf-8")+
    "\n[主结果](result.json) · [实际几何和属性核验](independent-public-requirements.json) · "
    "[R 原生格式检查](native-validation.json) · [注入失败回滚](injected-atomic-rollback.json) · "
    "[全部原有属性保全](existing-property-preservation.json) · "
    "[原始日志](run.log) · [进程收据](run-receipt.json) · [材料索引](evidence-index.json)。\n\n"
    "所有必要输入、清单、绑定产物、应用/评价、实际 D 网格基线和 R 已随本目录保留。"
    "源 G 沿本题的 ../../reference.ifc 仅供发布后评价，完整 role/fingerprint 见记录；机器日志中的绝对路径是原运行定位，不是唯一材料入口。\n\n"
    "临时 helper 的 [版本选择失败](failed-helper-binding/README.md) 和 [指纹前缀比较失败](failed-helper-index-prefix/README.md) 均保留原源码/错误/log/receipt。"
    "修正没有改变生产契约；这些记录不是模型成绩。\n",
    encoding="utf-8",
)
files = [{"path": str(path.relative_to(ROOT)).replace("\\", "/"), "sha256": sha(path), "bytes": path.stat().st_size}
         for path in sorted(ROOT.rglob("*")) if path.is_file() and path.name != "evidence-index.json"]
write(ROOT / "evidence-index.json", {
    "schema_version": "repair-comparison-offline-support-index/0.1",
    "case": "020", "passed": True, "provider_calls": 0,
    "role": "self-contained developer bound execution after explicitly simulated prewritten answer",
    "primary_result": "result.json", "files": files,
    "G_post_evaluation_relative": "../../reference.ifc",
    "G_not_in_resolve_bind_apply_inputs": True,
    "not_model_performance_or_formal_admission": True,
})
print(json.dumps({"case": "020", "curated": True, "files": len(files), "passed": True, "provider_calls": 0}))
