"""Private development definitions and filesystem boundary checks."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any


PUBLIC_FILES = frozenset({"model.ifc", "request.txt"})
PACKAGE_VERSION = "repair-comparison-development/0.1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_path(path: Path) -> Path:
    """Reject links before resolving them, including Windows junction parents."""
    absolute = path.absolute()
    for entry in (absolute, *absolute.parents):
        if entry.is_symlink() or entry.is_junction():
            raise ValueError(f"LINK_PATH_NOT_ALLOWED: {entry}")
    if absolute.is_file() and absolute.stat().st_nlink != 1:
        raise ValueError(f"HARDLINK_NOT_ALLOWED: {absolute}")
    return absolute.resolve()


def relative_path(text: str) -> str:
    if not isinstance(text, str) or not text or "\\" in text or ":" in text:
        raise ValueError("INVALID_RELATIVE_PATH")
    path = PurePosixPath(text)
    if path.is_absolute() or any(part in {".", ".."} for part in text.split("/")):
        raise ValueError("INVALID_RELATIVE_PATH")
    return path.as_posix()


def damage_profile(products: dict[str, int]) -> dict[str, Any]:
    """Describe primary repair targets; supporting openings are not supplied."""
    if not products or any(type(count) is not int or count < 1 for count in products.values()):
        raise ValueError("INVALID_DAMAGE_PROFILE")
    count = sum(products.values())
    return {"level": f"S{min(count, 3)}", "target_count": count,
            "composition": "single" if count == 1 else "same_type" if len(products) == 1 else "mixed",
            "targets": dict(products)}


def validate_definition(data: dict[str, Any]) -> None:
    try:
        if set(data) != {"case_id", "source", "damage", "request", "task", "clarification"}:
            raise ValueError("INVALID_DEFINITION_FIELDS")
        if not re.fullmatch(r"case-\d{3}", data["case_id"]):
            raise ValueError("CASE_ID_MUST_BE_NEUTRAL")
        source = data["source"]
        if not relative_path(source["path"]).lower().endswith(".ifc"):
            raise ValueError("SOURCE_MUST_BE_IFC")
        if not re.fullmatch(r"[0-9a-f]{64}", source["sha256"]):
            raise ValueError("INVALID_SOURCE_HASH")
        for key in ("asset_id", "scene_family", "rights", "approved_use"):
            if not isinstance(source[key], str) or not source[key].strip():
                raise ValueError(f"MISSING_SOURCE_{key}")
        for path in source.get("attribution_files", []):
            relative_path(path)
        damage = data["damage"]
        if damage["kind"] not in {"window", "door"}:
            raise ValueError("UNSUPPORTED_DAMAGE")
        ids = [damage["target_guid"]]
        if damage["kind"] == "window":
            ids += [damage["opening_guid"], damage["wall_guid"]]
        elif type(damage["preserve_opening"]) is not bool:
            raise ValueError("PRESERVE_OPENING_MUST_BE_BOOLEAN")
        if any(not re.fullmatch(r"[0-3][A-Za-z0-9_$]{21}", item) for item in ids):
            raise ValueError("INVALID_DAMAGE_GUID")
        request = data["request"]
        if not isinstance(request["text"], str) or not request["text"].strip() or not request["basis"]:
            raise ValueError("PUBLIC_REQUEST_AND_BASIS_REQUIRED")
        private_ids = [damage["target_guid"]]
        if damage["kind"] == "window":
            private_ids.append(damage["opening_guid"])
        if any(identity in request["text"] for identity in private_ids):
            raise ValueError("DELETED_ID_IN_PUBLIC_REQUEST")
        if re.search(r"(?<![A-Za-z0-9_$])[0-3][A-Za-z0-9_$]{21}(?![A-Za-z0-9_$])", request["text"]):
            raise ValueError("GUID_IN_PUBLIC_REQUEST")
        if re.search(r"(?<![A-Za-z0-9_])(?:IfcOpenShell|ChangeSet|run_python|Python|STEP)(?![A-Za-z0-9_])", request["text"], re.IGNORECASE):
            raise ValueError("METHOD_HINT_IN_PUBLIC_REQUEST")
        task = data["task"]
        for key in ("summary", "required_products", "required_relations", "acceptance", "preservation", "allowed_alternatives", "matching", "tolerances"):
            if not task[key]:
                raise ValueError(f"MISSING_TASK_{key}")
        if any(type(n) is not int or n < 1 for n in task["required_products"].values()):
            raise ValueError("INVALID_PRODUCT_DENOMINATOR")
        target_class = {"window": "IfcWindow", "door": "IfcDoor"}[damage["kind"]]
        if task["required_products"] != {target_class: 1}:
            raise ValueError("SINGLE_TARGET_PREPARATION_REQUIRES_ONE_PRODUCT")
        relations = task["required_relations"]
        if len({row["id"] for row in relations}) != len(relations):
            raise ValueError("DUPLICATE_RELATION_REQUIREMENT")
        # These recipes remove a single occurrence; each supported relation kind
        # has at most one target membership edge. Different labels cannot add edges.
        if len({row["ifc_class"] for row in relations}) != len(relations):
            raise ValueError("DUPLICATE_RELATION_EDGE")
        for row in relations:
            if not row["basis"] or not row["ifc_class"].startswith("IfcRel"):
                raise ValueError("INVALID_RELATION_REQUIREMENT")
        facts = data["clarification"]["required_user_facts"]
        if len({fact["fact_id"] for fact in facts}) != len(facts):
            raise ValueError("DUPLICATE_USER_FACT")
        for fact in facts:
            for key in ("fact_id", "why_required", "why_not_in_d", "allowed_answers", "answer", "answer_basis", "reply_scope"):
                if not fact[key]:
                    raise ValueError(f"MISSING_CLARIFICATION_{key}")
            if len(set(fact["allowed_answers"])) < 2 or fact["answer"] not in fact["allowed_answers"]:
                raise ValueError("CLARIFICATION_NEEDS_TWO_COMPATIBLE_CHOICES")
    except (KeyError, TypeError, AttributeError) as error:
        raise ValueError(f"INVALID_DEVELOPMENT_DEFINITION: {error}") from error
