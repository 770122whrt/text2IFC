import json
import re
from pathlib import Path


def test_multistorey_diagnosis_summary_classifies_cases(tmp_path):
    from text2ifc_agent.multistorey_diagnosis import build_multistorey_diagnosis_summary

    root = tmp_path / "diagnosis"
    _write_case(
        root,
        "two-storey",
        final_status="blocked",
        route="regenerate_json",
        issues=[
            {
                "owner": "generator",
                "issue_type": "missing_vertical_connection",
                "suggested_route": "regenerate_json",
            }
        ],
    )
    _write_case(
        root,
        "three-storey",
        final_status="blocked",
        route="blocked_as_unsupported",
        issues=[
            {
                "owner": "compiler",
                "issue_type": "compiler_unsupported_feature",
                "suggested_route": "blocked_as_unsupported",
            }
        ],
    )

    summary = build_multistorey_diagnosis_summary(root)

    assert summary["schema_version"] == "text2ifc/phase6.4-multistorey-diagnosis/1.0"
    assert summary["case_count"] == 2
    assert summary["accepted_ifc_count"] == 0
    cases = {case["case_id"]: case for case in summary["cases"]}
    assert cases["two-storey"]["diagnosis_class"] == "route_loop_fixable"
    assert cases["three-storey"]["diagnosis_class"] == "system_capability_gap"
    assert "compiler_unsupported_feature" in summary["capability_gap_issue_types"]
    assert (root / "multistorey-diagnosis-summary.json").is_file()
    assert (root / "multistorey-diagnosis-report.md").is_file()


def test_two_storey_diagnosis_prompt_includes_roof_slab_thickness():
    from scripts.agent import run_phase6_4_multistorey_diagnosis

    prompt = run_phase6_4_multistorey_diagnosis._cases()["two-storey-residential"]

    assert "屋面板厚度 150 mm" in prompt
    assert "CONTROL_LAYOUT_V2" in prompt
    assert "以下坐标是精确控制事实" in prompt
    assert "所有门窗必须使用本楼层的宿主墙" in prompt
    assert "生成宽 1000 的直跑 IfcStair" in prompt


def test_two_storey_diagnosis_prompt_removes_corridor_width_conflict_and_requires_stair_void():
    from scripts.agent import run_phase6_4_multistorey_diagnosis

    prompt = run_phase6_4_multistorey_diagnosis._cases()["two-storey-residential"]

    assert "CONTROL_LAYOUT_V2" in prompt
    assert "storey-2.corridor: x=4000..6000, y=0..8000" in prompt
    assert "二层走廊矩形范围作为控制边界" not in prompt
    assert "二层楼板在 stair-opening 范围必须生成可通行洞口" in prompt


def test_two_storey_diagnosis_prompt_fixes_slab_datum_and_stair_envelope():
    from scripts.agent import run_phase6_4_multistorey_diagnosis

    prompt = run_phase6_4_multistorey_diagnosis._cases()["two-storey-residential"]

    assert "首层地板顶面标高为 Z=0" in prompt
    assert "楼梯水平投影长度为 3900 mm" in prompt
    assert "x=500..1500、y=4050..7950" in prompt
    assert "沿 +Y 方向上升" in prompt


def test_two_storey_control_prompt_has_a_non_overlapping_coordinate_contract():
    from scripts.agent import run_phase6_4_multistorey_diagnosis

    prompt = run_phase6_4_multistorey_diagnosis._cases()["two-storey-residential"]

    assert "CONTROL_LAYOUT_V2" in prompt
    rectangles = _control_rectangles(prompt)
    assert rectangles
    for storey, records in rectangles.items():
        for index, (left_name, left) in enumerate(records):
            for right_name, right in records[index + 1 :]:
                overlap_x = min(left[1], right[1]) - max(left[0], right[0])
                overlap_y = min(left[3], right[3]) - max(left[2], right[2])
                assert not (overlap_x > 0 and overlap_y > 0), (
                    f"{storey}: {left_name} overlaps {right_name}"
                )
    assert "door-living-corridor: host=storey-1-wall-living-corridor" in prompt
    assert "segment=x=4000,y=0..4000, center=(4000,2000)" in prompt
    assert "stair-opening: x=0..2000, y=4000..8000" in prompt


def _control_rectangles(prompt: str) -> dict[str, list[tuple[str, tuple[int, int, int, int]]]]:
    records: dict[str, list[tuple[str, tuple[int, int, int, int]]]] = {}
    pattern = re.compile(
        r"(storey-[12])\.([a-z0-9_-]+): x=(\d+)\.\.(\d+), y=(\d+)\.\.(\d+)"
    )
    for storey, name, x_min, x_max, y_min, y_max in pattern.findall(prompt):
        records.setdefault(storey, []).append(
            (name, (int(x_min), int(x_max), int(y_min), int(y_max)))
        )
    return records


def _write_case(root: Path, case_id: str, *, final_status: str, route: str, issues: list[dict]) -> None:
    case_dir = root / case_id
    _write_json(
        case_dir / "case-result.json",
        {
            "case_id": case_id,
            "final_status": final_status,
            "route": route,
            "output_type": "none",
            "blocking_issue_count": len(issues),
        },
    )
    _write_json(case_dir / "issues.json", {"issues": issues})
    _write_json(case_dir / "route-decision.json", {"route": route, "final_status": final_status})
    (case_dir / "report.md").write_text("# report\n", encoding="utf-8")


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
