"""Allowlisted projection from private mutation truth to public repair input."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


PUBLIC_SPEC_SCHEMA_VERSION = "text2ifc/ifc-repair-spec/0.1"
BATCH_PUBLIC_SPEC_SCHEMA_VERSION = "text2ifc/ifc-repair-spec/0.2"


def project_public_repair_spec(
    private_manifest: Mapping[str, Any],
    *,
    request_id: str,
) -> dict[str, Any]:
    """Build a public specification without copying private source fields."""

    if private_manifest.get("mutation_type") != "remove_window_and_opening":
        raise ValueError("UNSUPPORTED_MUTATION_TYPE")
    target = private_manifest["target"]
    wall = target["wall"]
    opening = target["opening"]
    window = target["window"]
    return {
        "schema_version": PUBLIC_SPEC_SCHEMA_VERSION,
        "request_id": request_id,
        "requested_operation_type": "add_window_with_opening_to_wall",
        "storey": {"name": str(wall["storey"])},
        "target": {
            "ifc_class": "IfcWall",
            "description": str(wall["name"]),
            "local_reference": {
                "reference": str(wall["local_reference"]),
                "meaning": "宿主墙 Axis 表示的第一个点，沿 Axis 正方向测量",
                "opening_center_offset_mm": float(
                    opening["geometric_center_offset_mm"]
                ),
            },
        },
        "opening": {
            "width_mm": float(window["width_mm"]),
            "height_mm": float(window["height_mm"]),
            "sill_height_mm": float(opening["sill_height_mm"]),
        },
        "window": {"fit_opening": True},
        "preservation_requirements": [
            "保持宿主墙的身份、放置、材质、类型和属性不变",
            "保持楼层、空间布局和其他构件不变",
        ],
    }


def render_repair_request(public_spec: Mapping[str, Any]) -> str:
    """Render the human repair request exclusively from the public spec."""

    storey = public_spec["storey"]["name"]
    target = public_spec["target"]
    reference = target["local_reference"]
    opening = public_spec["opening"]
    return (
        f"请在 {storey} 的墙“{target['description']}”上新增一扇窗户及其墙洞。"
        f"位置以 {reference['reference']}（{reference['meaning']}）为基准，"
        f"洞口中心偏移 {reference['opening_center_offset_mm']:g} mm。"
        f"洞口宽 {opening['width_mm']:g} mm、高 {opening['height_mm']:g} mm，"
        f"窗台高 {opening['sill_height_mm']:g} mm。"
        "窗户应完整填充洞口。"
        + "；".join(public_spec["preservation_requirements"])
        + "。\n"
    )


def project_public_batch_repair_spec(
    private_manifest: Mapping[str, Any],
    *,
    request_id: str,
) -> dict[str, Any]:
    """Project a private batch fixture into ordered, bounded public operations."""

    if private_manifest.get("mutation_type") != "remove_windows_and_openings_batch":
        raise ValueError("UNSUPPORTED_MUTATION_TYPE")
    targets = private_manifest.get("targets")
    if not isinstance(targets, list) or not 1 <= len(targets) <= 16:
        raise ValueError("BATCH_TARGET_COUNT_INVALID")
    operations: list[dict[str, Any]] = []
    for target in targets:
        wall = target["wall"]
        opening = target["opening"]
        window = target["window"]
        prototype = target["prototype_evidence"]
        if (
            prototype.get("source") != "damaged_ifc_surviving_type"
            or int(prototype.get("surviving_occurrence_count", 0)) < 1
        ):
            raise ValueError("BATCH_PROTOTYPE_EVIDENCE_INVALID")
        operations.append(
            {
                "operation_id": str(target["target_id"]),
                "requested_operation_type": "add_window_with_opening_to_wall",
                "storey": {"name": str(wall["storey"])},
                "target": {
                    "ifc_class": "IfcWall",
                    "global_id": str(wall["global_id"]),
                    "description": str(wall["name"]),
                    "local_reference": {
                        "reference": str(wall["local_reference"]),
                        "meaning": "宿主墙 Axis 的起点，沿 Axis 正方向测量",
                        "opening_center_offset_mm": float(
                            opening["geometric_center_offset_mm"]
                        ),
                    },
                },
                "opening": {
                    "width_mm": float(window["width_mm"]),
                    "height_mm": float(window["height_mm"]),
                    "sill_height_mm": float(opening["sill_height_mm"]),
                },
                "window": {
                    "fit_opening": True,
                    "prototype": {
                        "ifc_class": str(prototype["ifc_class"]),
                        "global_id": str(prototype["global_id"]),
                        "name": str(prototype["name"]),
                        "evidence": "damaged_ifc_surviving_type",
                    },
                },
            }
        )
    return {
        "schema_version": BATCH_PUBLIC_SPEC_SCHEMA_VERSION,
        "request_id": request_id,
        "transaction": {
            "mode": "all_or_nothing",
            "operation_count": len(operations),
        },
        "operations": operations,
        "preservation_requirements": [
            "保持五面宿主墙的身份、放置、材质、类型和既有属性不变",
            "保持楼层、空间布局和所有非目标构件不变",
            "任何一项不能安全完成时整批失败，不发布部分成功 IFC",
        ],
    }


def render_batch_repair_request(public_spec: Mapping[str, Any]) -> str:
    """Render one readable request for all ordered public batch operations."""

    operations = public_spec.get("operations")
    if not isinstance(operations, list) or not operations:
        raise ValueError("BATCH_OPERATIONS_REQUIRED")
    lines = [
        f"请一次性修复以下共 {len(operations)} 扇窗，并作为一个统一 ChangeSet 原子执行："
    ]
    for index, operation in enumerate(operations, start=1):
        target = operation["target"]
        reference = target["local_reference"]
        opening = operation["opening"]
        prototype = operation["window"]["prototype"]
        lines.append(
            f"{index}. 在 {operation['storey']['name']} 的墙“{target['description']}”"
            f"（GlobalId: {target['global_id']}）上，以"
            f"{reference['reference']} 为基准，沿墙 Axis 正方向"
            f" {reference['opening_center_offset_mm']:g} mm 处设置洞口中心；"
            f"洞口宽 {opening['width_mm']:g} mm、高 {opening['height_mm']:g} mm，"
            f"窗台高 {opening['sill_height_mm']:g} mm；复用损伤 IFC 中仍存在的"
            f"窗型“{prototype['name']}”（GlobalId: {prototype['global_id']}），"
            "窗完整填充洞口。"
        )
    lines.extend(
        [
            "约束：",
            *[
                f"- {requirement}"
                for requirement in public_spec["preservation_requirements"]
            ],
        ]
    )
    return "\n".join(lines) + "\n"
