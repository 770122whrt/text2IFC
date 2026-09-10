"""Bound, operator-authored design decisions; never an engineering pass gate."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


CONTEXT_VERSION = "text2ifc/design-review-context/1.0"


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _local_file(root: Path, relative: Any) -> Path:
    if not _text(relative):
        raise ValueError("DESIGN_REVIEW_EVIDENCE_PATH")
    path = Path(relative)
    if path.is_absolute() or path.drive or ".." in path.parts:
        raise ValueError("DESIGN_REVIEW_EVIDENCE_PATH")
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root.resolve()) or not resolved.is_file():
        raise ValueError("DESIGN_REVIEW_EVIDENCE_PATH")
    return resolved


def load_design_review_context(root: Path, conversation_path: Path) -> dict[str, Any] | None:
    """Read a review context authored by the caller, not inferred from Agent output.

    Exact quote binding proves provenance, not the meaning of arbitrary language.
    The caller must have authority for each declared revise/retain decision.
    """
    path = root / "design-review-context.json"
    if not path.exists():
        return None
    try:
        context = json.loads(path.read_text(encoding="utf-8"))
        turns = json.loads(conversation_path.read_text(encoding="utf-8"))
        if not isinstance(context, dict) or context.get("schema_version") != CONTEXT_VERSION:
            raise ValueError("DESIGN_REVIEW_VERSION")
        if context.get("conversation_sha256") != hashlib.sha256(conversation_path.read_bytes()).hexdigest():
            raise ValueError("DESIGN_REVIEW_STALE_CONVERSATION")
        concerns = context.get("concerns")
        if not isinstance(concerns, list) or not concerns:
            raise ValueError("DESIGN_REVIEW_CONCERNS_REQUIRED")
        if not isinstance(turns, list):
            raise ValueError("DESIGN_REVIEW_CONVERSATION")
        seen: set[str] = set()
        for row in concerns:
            if not isinstance(row, dict) or not all(_text(row.get(k)) for k in (
                "id", "description", "location", "decision_turn_id", "decision_quote"
            )):
                raise ValueError("DESIGN_REVIEW_INVALID_CONCERN")
            if row["id"] in seen:
                raise ValueError("DESIGN_REVIEW_DUPLICATE_CONCERN")
            seen.add(row["id"])
            if row.get("decision") not in ("revise", "retain"):
                raise ValueError("DESIGN_REVIEW_DECISION_REQUIRED")
            matches = [t for t in turns if isinstance(t, dict) and t.get("turn_id") == row["decision_turn_id"]]
            if len(matches) != 1 or matches[0].get("role") != "user" or matches[0].get("content") != row["decision_quote"]:
                raise ValueError("DESIGN_REVIEW_UNBOUND_USER_DECISION")
            evidence = _local_file(root, row.get("evidence_path"))
            if row.get("evidence_sha256") != hashlib.sha256(evidence.read_bytes()).hexdigest():
                raise ValueError("DESIGN_REVIEW_STALE_EVIDENCE")
        return context
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("DESIGN_REVIEW_UNREADABLE_CONTEXT") from error


def validate_design_review_output(payload: dict[str, Any], context: dict[str, Any], root: Path) -> list[dict[str, str]]:
    """Require each known concern in v3. User acknowledgement never clears it."""
    def fail(reason: str) -> list[dict[str, str]]:
        return [{"code": "DESIGN_REVIEW_OUTPUT_INVALID", "path": "/design_review", "message": reason}]

    if payload.get("schema_version") != "text2ifc/audit/3.0":
        return fail("This bound review requires Audit 3.0; downgrade is forbidden.")
    review = payload.get("design_review")
    if not isinstance(review, dict) or review.get("scope") != "limited_review_not_code_compliance":
        return fail("A limited design review is not a building-code compliance certificate.")
    limits = review.get("limitations")
    if not isinstance(limits, list) or not limits or not all(_text(v) for v in limits):
        return fail("Review limitations must be explicit.")
    rows = review.get("concerns")
    if not isinstance(rows, list):
        return fail("Known concerns must be retained as a list.")
    known = {row["id"]: row for row in context["concerns"]}
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict) or not _text(row.get("id")) or not _text(row.get("description")):
            return fail("Invalid review concern.")
        identity = row["id"]
        if identity in seen or identity not in known:
            return fail("Duplicate or unoffered review concern; additional findings belong in findings.")
        seen.add(identity)
        status = row.get("status")
        # No 'resolved' claim until an independent current-IFC check is bound.
        allowed = ("retained_known_issue",) if known[identity]["decision"] == "retain" else ("not_verified", "unresolved")
        if status not in allowed:
            return fail("Acknowledgement or a requested revision does not prove a defect resolved.")
        if status == "unresolved" and payload.get("blocking") is not True:
            return fail("An unresolved requested revision must remain blocking.")
        paths = row.get("evidence_paths")
        if not isinstance(paths, list) or not paths:
            return fail("Each concern needs existing local evidence.")
        try:
            for relative in paths:
                _local_file(root, relative)
        except ValueError:
            return fail("Concern evidence must stay inside the current case and exist.")
    if seen != set(known):
        return fail("Known design concerns were omitted.")
    return []


def design_review_report_lines(root: Path) -> list[str]:
    """Expose the model's bounded assessment without changing machine authority."""
    path = root / "audit/audit-report.json"
    if not path.is_file():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != "text2ifc/audit/3.0":
        return []
    review = payload.get("design_review")
    return [
        "", "## 合理性问题与用户决定", "",
        "以下为 Audit 的有限审查记录，技术／请求符合性通过不代表合理性或规范通过。",
        "用户保留的已知问题仍然存在；要求修改也不等于已经独立验证修改成功。",
        "[用户决定与参考证据](design-review-context.json) · [Audit 校验](audit/validation.json)",
        "", "```json", json.dumps(review, ensure_ascii=False, indent=2), "```", "",
    ]
