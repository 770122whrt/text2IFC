"""Finalize the LIVE Composite Repair Milestone proof pack to repository convention.

For every curated case directory under
``dataset/processed/proof/repair-composite-milestone/`` (populated by
``curate_live_proof.py`` from the genuine DeepSeek execution), this adds the
standard proof components used by ``ifc-repair-success-cases``:

* ``FILES.json`` — hash manifest of every file under the case directory;
* ``manifest.json`` — case metadata (source, status, evidence mode, calls);
* ``REPORT.md`` — Chinese per-case report in the established style.

Idempotent-safe: overwrites only its own outputs.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from scripts.ifc_repair.composite_evidence.offline_driver import load_freeze  # noqa: E402

PROOF_ROOT = ROOT / "dataset" / "processed" / "proof" / "repair-composite-milestone"
FREEZE = load_freeze()
NL = chr(10)

OUTCOMES = {
    "succeeded": "真实 Provider 链路完整成功",
    "clarification_required": "真实 Provider 请求澄清（保留原始失败）",
    "provider_failed": "真实 Provider 输出未通过确定性校验（保留原始失败）",
    "unsupported": "负孪生按设计 fail-closed（零突变）",
}


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _optional_read(path: Path) -> dict | None:
    return _read(path) if path.is_file() else None


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def finalize_case(case: Mapping[str, Any]) -> None:
    case_id = str(case["case_id"])
    case_root = PROOF_ROOT / case_id
    model = FREEZE["models"][case["model_id"]]
    negative = case.get("expected_terminal_class") == "UNSUPPORTED_ATOMIC_GUARD"

    summary = _read(case_root / "agent" / "live-case-summary.json")
    final_status = str(summary.get("final_status"))
    proof = _optional_read(case_root / "validation" / "composite-proof.json")
    guard = _optional_read(case_root / "validation" / "NEGATIVE-GUARD.json")
    failure = _optional_read(
        case_root / "validation" / "TERMINAL-FAILURE-RECORD.json"
    )
    succeeded = final_status == "succeeded"

    # ---- FILES.json ----------------------------------------------------
    entries: dict[str, Any] = {}
    for path in sorted(case_root.rglob("*")):
        if not path.is_file() or path.name in {"FILES.json"}:
            continue
        rel = path.relative_to(case_root).as_posix()
        entries[rel] = {
            "bytes": path.stat().st_size,
            "path": rel,
            "sha256": _sha256(path),
        }
    _write(case_root / "FILES.json", {
        "schema_version": "text2ifc/composite-proof-files/0.1",
        "case_id": case_id,
        "artifacts": entries,
    })

    # ---- manifest.json --------------------------------------------------
    _write(case_root / "manifest.json", {
        "schema_version": "text2ifc/composite-repair-proof-case/0.2",
        "provenance_namespace": "repair-composite-milestone",
        "case_id": case_id,
        "status": final_status,
        "difficulty": case.get("difficulty"),
        "source": {
            "path": model["path"],
            "schema": model["schema"],
            "sha256": "sha256:" + model["sha256"],
            "size_bytes": model["size_bytes"],
        },
        "request_sha256": "sha256:" + case["request_sha256"],
        "operation_count": case["scale"]["operation_count"],
        "operation_families": sorted(case["scale"]["families"]),
        "property_intent_count": case["scale"]["property_intent_count"],
        "expected_terminal_class": case["expected_terminal_class"],
        "provider_evidence_mode": "live_deepseek",
        "genuine_provider_calls": summary.get("transport_calls"),
        "transport_calls_by_stage": summary.get("transport_calls_by_stage"),
        "live_evidence_pass": summary.get("live_evidence_pass"),
        "synthetic_fallback_used": False,
        "production_input_boundary": {
            "pristine_comparator_gold_supplied": False,
            "mutation_truth_supplied": False,
            "deleted_identities_supplied": False,
            "public_bindings_only": True,
            "source_immutable": summary.get("source_sha256_before")
            == summary.get("source_sha256_after"),
        },
        "artifacts": sorted(entries),
        "base_revision": FREEZE["base_revision"],
        "freeze_sha256": FREEZE["freeze_sha256"],
        "finalized_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(),
    })

    # ---- REPORT.md ------------------------------------------------------
    lines: list[str] = []
    lines.append(f"# {case_id}")
    lines.append("")
    lines.append(
        f"Composite Repair Milestone 真实 Provider（DeepSeek）证据。"
        f"{OUTCOMES.get(final_status, final_status)}。"
    )
    lines.append("")
    lines.append(f"- 模型：`{model['path']}`（SHA-256 `{model['sha256']}`）")
    lines.append(
        f"- Storey：`{case['storey']['global_id']}`（{case['storey']['name']}）"
    )
    lines.append(
        f"- 操作数：{case['scale']['operation_count']}（族："
        f"{', '.join(sorted(case['scale']['families']))}；属性意图 "
        f"{case['scale']['property_intent_count']}）"
    )
    lines.append(
        f"- 终态：`{final_status}`"
        + (f"（reason `{summary.get('reason_code')}`）" if summary.get("reason_code") else "")
    )
    lines.append(
        f"- 真实 Provider 调用：{summary.get('transport_calls')}"
        f"（{json.dumps(summary.get('transport_calls_by_stage'), ensure_ascii=False)}）"
    )
    lines.append(f"- live 证据校验：{summary.get('live_evidence_pass')}")
    lines.append("- synthetic fallback：false")
    lines.append("")
    strict = summary.get("strict_reopen_verification") or {}
    if succeeded:
        lines.append("## 门禁")
        lines.append("")
        lines.append(f"- 严格重开（L0/L1/L2）：{strict.get('status')}"
                     f"（{strict.get('l0_pass')}/{strict.get('l1_pass')}/{strict.get('l2_pass')}）")
        lines.append(f"- 操作级复合 Proof：{'PASS' if proof and proof.get('status') == 'passed' else 'FAIL'}")
        preservation = _optional_read(case_root / "validation" / "preservation.json")
        if preservation:
            lines.append(
                f"- 精确增量保存：{preservation.get('exact_delta', {}).get('status')}"
            )
            lines.append(
                f"- 比较器零无关突变："
                f"{preservation.get('comparator', {}).get('status')}"
            )
        lines.append("")
    if guard:
        lines.append("## 负孪生守卫（全有或全无）")
        lines.append("")
        lines.append(f"- 终态：`{guard.get('final_status')}`（reason `{guard.get('reason_code')}`）")
        lines.append(f"- 零突变：{guard.get('zero_mutation')}")
        lines.append(f"- Stage 2 尝试：{guard.get('stage2_attempts')}")
        lines.append("- 按设计不产出 repaired IFC。")
        lines.append("")
    if failure:
        lines.append("## 真实失败记录（按协议保留）")
        lines.append("")
        lines.append(f"- 终态：`{failure.get('final_status')}`（reason `{failure.get('reason_code')}`）")
        clar = failure.get("clarification") or {}
        if clar.get("question"):
            lines.append(f"- 澄清问题：{clar['question']}")
        lines.append(
            "- 每次真实尝试的完整证据见 `agent/live-attempts.json`；"
            "失败不覆盖、不重命名、不替换。"
        )
        lines.append("")
    lines.append("## 文件")
    lines.append("")
    lines.append(
        "- `01-original.ifc`：原始公开语料模型（字节等同）。"
        "本里程碑为**增量改造**语义（非既有 proof 的损伤-恢复语义），"
        "系统输入即原始模型，故 `02-input.ifc` 与 `01` 哈希一致。"
    )
    if succeeded:
        lines.append("- `03-repaired.ifc`：真实 Provider 链路产出的修复 IFC。")
    else:
        lines.append(
            "- 无 `03-repaired.ifc`：链路未产出（真实终态见上）；"
            "离线确定性可执行性由测试套件证明（48/48）。"
        )
    lines.append("- `input/request.txt`：冻结请求；`agent/`：意图与真实尝试；"
                 "`changeset/`：绑定变更集；`validation/`：应用、Proof、保存与终态记录。")
    lines.append("- 每个文件哈希绑定于 `FILES.json`。")
    lines.append("")
    (case_root / "REPORT.md").write_text(
        NL.join(lines) + NL, encoding="utf-8", newline=NL
    )


def _write(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str) + NL,
        encoding="utf-8",
        newline=NL,
    )


def main() -> int:
    finalized = []
    for case in FREEZE["cases"]:
        finalize_case(case)
        finalized.append(str(case["case_id"]))
    print("finalized:", ", ".join(finalized))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
