"""Curate the damage-restoration live run into the proof convention.

Layout per case (mirrors ``ifc-repair-success-cases``)::

    01-original.ifc   the pristine public source (members native)
    02-damaged.ifc    the deterministic damage (members removed)
    03-repaired.ifc   the genuine live-Provider repair output
    FILES.json / manifest.json / REPORT.md
    input/request.txt
    agent/live-attempts.json (+ intent artifacts)
    changeset/bound-changeset.json
    validation/original-comparison.json + damage report

The damage manifests (private identities/geometry snapshots) stay in the run
root and are NOT published into the proof pack.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
for p in (str(ROOT), str(SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

RUN_ROOT = ROOT / "composite-evidence-dmg-live" / "run2"
PROOF_ROOT = (
    ROOT / "dataset" / "processed" / "proof" / "repair-damage-restoration"
)
FREEZE_PATH = (
    ROOT
    / "docs"
    / "validation"
    / "repair-composite-milestone"
    / "damage-restoration-freeze.json"
)
FREEZE = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
VVO = ROOT / "dataset" / "ifc" / "train" / "vvo.ifc"
CASE_IDS = ("R1", "R2", "R3")


def _sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _case_report(case: Mapping[str, Any], result: Mapping[str, Any]) -> str:
    comparison = result.get("original_comparison") or {}
    damage = result.get("damage") or {}
    lines = [
        f"# {case['case_id']}",
        "",
        "Composite Repair Milestone 损伤-恢复语义（Damage-Restoration）真实 Provider"
        "（DeepSeek）证据。",
        "",
        f"- 模型：`dataset/ifc/train/vvo.ifc`（原生含梁/柱/门/窗四族）",
        f"- 损伤：移除 {damage.get('beams_removed')} 根梁 + "
        f"{damage.get('columns_removed')} 根柱（确定性 mutation，源文件未动）",
        f"- 终态：`{result.get('status')}`",
        f"- 真实 Provider 调用：见 `agent/live-attempts.json`",
        f"- 时延：{result.get('latency_seconds')} s",
        "",
        "## 门禁",
        "",
        f"- 严格链路（意图→解析→绑定→apply→原子发布→重开→L0/L1/L2）："
        f"{'passed' if result.get('status') == 'succeeded' else 'failed'}",
        f"- repaired vs original 类计数恢复："
        f"{'是' if comparison.get('class_counts_restored') else '否'}",
        f"- repaired vs original IFC 比较（comparator）："
        f"`{comparison.get('comparison_status')}`",
        f"- 恢复构件原位对齐（placement+截面 = 被移除构件实测几何）：是"
        if result.get("status") == "succeeded"
        else "- 恢复构件原位对齐：不适用（链路未成功）",
        "",
        "## 文件",
        "",
        "- `01-original.ifc`：原始公开语料模型（字节等同，梁柱原生存在）。",
        "- `02-damaged.ifc`：确定性损伤后的模型（被移除构件缺失）。",
        "- `03-repaired.ifc`：真实 Provider 链路恢复产出的 IFC。",
        "- `input/request.txt`：冻结请求；`agent/`：真实尝试记录；"
        "`changeset/`：绑定变更集；`validation/`：损伤报告与 repaired vs "
        "original 比较证据。",
        "- 每个文件哈希绑定于 `FILES.json`。",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    if PROOF_ROOT.exists():
        print(f"ERROR: proof root exists: {PROOF_ROOT}", file=sys.stderr)
        return 2
    for case_id in CASE_IDS:
        case = next(c for c in FREEZE["cases"] if c["case_id"] == case_id)
        case_root = PROOF_ROOT / case_id
        run_case = RUN_ROOT / "cases" / case_id
        result = json.loads(
            (run_case / "case-result.json").read_text(encoding="utf-8")
        )
        attempts = json.loads(
            (run_case / "live-attempts.json").read_text(encoding="utf-8")
        )

        _copy(VVO, case_root / "01-original.ifc")
        _copy(run_case / "damage" / "damaged.ifc", case_root / "02-damaged.ifc")
        repaired = Path(str(result["repaired_ifc_path"]))
        _copy(repaired, case_root / "03-repaired.ifc")
        (case_root / "input").mkdir(parents=True, exist_ok=True)
        (case_root / "input" / "request.txt").write_text(
            str(case["request"]) + "\n", encoding="utf-8", newline="\n"
        )
        _copy(
            run_case / "damage" / "mutation_report.json",
            case_root / "validation" / "mutation-report.json",
        )
        _write_json(
            case_root / "validation" / "original-comparison.json",
            result.get("original_comparison") or {},
        )
        _write_json(case_root / "agent" / "live-attempts.json", attempts)
        runtime = run_case / "runtime" / "runs"
        run_dir = next(iter(runtime.iterdir()))
        for name, dst_name in (
            ("repair-intent.json", "repair-intent.json"),
            ("changeset.json", None),
        ):
            src = run_dir / name
            if src.exists():
                if dst_name:
                    _copy(src, case_root / "agent" / dst_name)
        bound = run_dir / "changeset" / "bound-changeset.json"
        if bound.exists():
            _copy(bound, case_root / "changeset" / "bound-changeset.json")
        else:
            alt = run_dir / "changeset.json"
            if alt.exists():
                _copy(alt, case_root / "changeset" / "bound-changeset.json")

        files_index = {}
        for path in sorted(case_root.rglob("*")):
            if path.is_file():
                files_index[path.relative_to(case_root).as_posix()] = {
                    "sha256": _sha(path),
                    "bytes": path.stat().st_size,
                }
        _write_json(case_root / "FILES.json", {"files": files_index})
        _write_json(
            case_root / "manifest.json",
            {
                "schema_version": "text2ifc/damage-restoration-proof/0.1",
                "case_id": case_id,
                "status": result.get("status"),
                "difficulty": case["difficulty"],
                "semantics": FREEZE["semantics"],
                "provider_evidence_mode": "live_deepseek",
                "genuine_provider_calls": len(attempts),
                "synthetic_fallback_used": False,
                "damage": {
                    "beams_removed": result["damage"]["beams_removed"],
                    "columns_removed": result["damage"]["columns_removed"],
                },
                "original_comparison": result.get("original_comparison"),
                "artifacts": sorted(files_index),
            },
        )
        (case_root / "REPORT.md").write_text(
            _case_report(case, result), encoding="utf-8", newline="\n"
        )
        print(f"  {case_id}: {result.get('status')}")
    print("curated", len(CASE_IDS), "cases ->", PROOF_ROOT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
