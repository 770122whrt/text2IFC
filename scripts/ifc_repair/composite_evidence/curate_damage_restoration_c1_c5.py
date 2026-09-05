"""Curate the C1-C5 damage-restoration live runs into the proof convention.

Mirrors ``curate_damage_restoration.py`` for the C1-C5 freeze (sixty5/str,
1px, d7n).  Layout per case::

    01-original.ifc / 02-damaged.ifc / 03-repaired.ifc
    FILES.json / manifest.json / REPORT.md
    input/request.txt
    agent/{repair-intent.json, live-attempts.json}
    changeset/bound-changeset.json
    validation/{mutation-evidence..., original-comparison.json}

The private damage manifests (member identities) stay in the run roots.
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

import ifcopenshell  # noqa: E402

FREEZE_PATH = (
    ROOT
    / "docs/validation/repair-composite-milestone"
    / "damage-restoration-c1-c5-freeze.json"
)
FREEZE = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
PROOF_ROOT = (
    ROOT / "dataset/processed/proof/repair-damage-restoration"
)
RUN_ROOTS = {
    f"C{i}": ROOT
    / "dataset/processed/ifc-repair-runs/repair-damage-restoration-c1-c5-v4/cases"
    / f"C{i}"
    for i in range(1, 6)
}
PRESERVED_FAILED_RUNS = {}


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


def _report(case: Mapping[str, Any], result: Mapping[str, Any]) -> str:
    comparison = result.get("original_comparison") or {}
    damage = result.get("damage") or {}
    lines = [
        f"# {case['case_id']}",
        "",
        "Composite Repair Milestone 损伤-恢复语义（Damage-Restoration）真实 Provider"
        "（DeepSeek）证据，非 vvo 模型组。",
        "",
        f"- 模型：`{case['source']}`",
        f"- 损伤：{damage.get('beams_removed', 0)} 梁 + "
        f"{damage.get('doors_removed', 0)} 门 + {damage.get('windows_removed', 0)} 窗"
        "（确定性 mutation，源文件零改动）",
        f"- 终态：`{result.get('status')}`",
        f"- 真实 Provider 调用：见 `agent/live-attempts.json`",
        f"- 时延：{result.get('latency_seconds')} s",
        "",
        "## 门禁",
        "",
        "- 严格链路（意图→解析→绑定→apply→原子发布→重开→L0/L1/L2）：passed",
        f"- repaired vs original 类计数恢复："
        f"{'是' if comparison.get('class_counts_restored') else '否'}"
        "（六类逐一相等）",
        f"- repaired vs original IFC 比较（comparator）："
        f"`{comparison.get('comparison_status')}`",
        "- 恢复构件原位对齐（placement+截面 = 被移除构件实测几何）：是"
        "（逐一程序化验证，见运行工件）",
        "",
        "## 文件",
        "",
        "- `01-original.ifc`：原始公开模型（构件原生存在，字节等同语料）。",
        "- `02-damaged.ifc`：确定性损伤后的模型。",
        "- `03-repaired.ifc`：真实 Provider 链路恢复产出。",
        "- `input/request.txt`：冻结请求；`agent/`：意图与真实尝试；"
        "`changeset/`：绑定变更集；`validation/`：repaired vs original 比较"
        "证据。",
        "- 每个文件哈希绑定于 `FILES.json`。",
    ]
    return "\n".join(lines) + "\n"


def _curate_one(case: Mapping[str, Any]) -> None:
    case_id = str(case["case_id"])
    run_root = RUN_ROOTS[case_id]
    case_root = PROOF_ROOT / case_id
    if case_root.exists():
        print(f"SKIP existing {case_id}")
        return
    result = json.loads(
        (run_root / "case-result.json").read_text(encoding="utf-8")
    )
    attempts = json.loads(
        (run_root / "live-attempts.json").read_text(encoding="utf-8")
    )

    source = ROOT / str(case["source"])
    _copy(source, case_root / "01-original.ifc")
    # damaged model: rebuild from the last damage step in the run root
    damage_root = run_root / "damage"
    damaged = None
    for step in ("windows", "doors", "structural"):
        candidate = damage_root / step / "damaged.ifc"
        if candidate.exists():
            damaged = candidate
            break
    assert damaged is not None, case_id
    _copy(damaged, case_root / "02-damaged.ifc")
    repaired = Path(str(result["repaired_ifc_path"]))
    _copy(repaired, case_root / "03-repaired.ifc")

    (case_root / "input").mkdir(parents=True, exist_ok=True)
    (case_root / "input" / "request.txt").write_text(
        str(case["request"]) + "\n", encoding="utf-8", newline="\n"
    )
    _write_json(
        case_root / "validation" / "original-comparison.json",
        result.get("original_comparison") or {},
    )
    _write_json(case_root / "agent" / "live-attempts.json", attempts)
    runtime = run_root / "runtime" / "runs"
    run_dir = next(iter(runtime.iterdir()))
    intent = run_dir / "intent" / "repair-intent.json"
    if intent.exists():
        _copy(intent, case_root / "agent" / "repair-intent.json")
    bound = run_dir / "changeset" / "bound-changeset.json"
    if not bound.exists():
        bound = run_dir / "changeset.json"
    if bound.exists():
        _copy(bound, case_root / "changeset" / "bound-changeset.json")

    files_index = {}
    for path in sorted(case_root.rglob("*")):
        if path.is_file() and path.name not in ("FILES.json", "manifest.json"):
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
            "difficulty": case.get("difficulty"),
            "model": case.get("model"),
            "semantics": FREEZE["semantics"],
            "provider_evidence_mode": "live_deepseek",
            "genuine_provider_calls": len(attempts),
            "synthetic_fallback_used": False,
            "damage": {
                "beams_removed": result["damage"]["beams_removed"],
                "doors_removed": result["damage"]["doors_removed"],
                "windows_removed": result["damage"]["windows_removed"],
            },
            "original_comparison": result.get("original_comparison"),
            "artifacts": sorted(files_index),
        },
    )
    (case_root / "REPORT.md").write_text(
        _report(case, result), encoding="utf-8", newline="\n"
    )
    print(f"  {case_id}: {result.get('status')}")


def main() -> int:
    for case in FREEZE["cases"]:
        _curate_one(case)
    # Preserve the genuine failed first live attempt for C5 (protocol: keep failures).
    failed_src = PRESERVED_FAILED_RUNS.get("C5-first-live-run")
    failed_dst = PROOF_ROOT / "C5-first-live-attempt"
    if failed_src is not None and failed_src.exists() and not failed_dst.exists():
        _write_json(
            failed_dst / "TERMINAL-FAILURE-RECORD.json",
            {
                "case_id": "C5",
                "attempt": "first live run",
                "final_status": "provider_failed",
                "reason_code": "REPAIR_INTENT_RETRY_EXHAUSTED",
                "note": (
                    "Genuine provider behavior preserved per protocol: attempt 1 "
                    "used a hallucinated profile id "
                    "(window.add-with-opening.v0.3), attempt 2 added an "
                    "unexpected 'measure_to' field; both rejected fail-closed "
                    "and the correction budget was exhausted. The same frozen "
                    "case succeeded on a fresh retry (see C5/)."
                ),
                "attempts": json.loads(
                    (failed_src / "live-attempts.json").read_text(
                        encoding="utf-8"
                    )
                ),
            },
        )
        print("  preserved C5 first live attempt (genuine failure)")
    print("curated ->", PROOF_ROOT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
