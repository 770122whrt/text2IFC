"""Deterministic, hash-addressed context selection for Design Brief calls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BIM_JSON_SCHEMA_PATH = PROJECT_ROOT / "schemas" / "bim-json" / "2.0" / "schema.json"
CAPABILITY_PATH = PROJECT_ROOT / "schemas" / "ifc" / "capabilities" / "IFC2X3.json"
REGISTRY_MANIFEST_PATH = (
    PROJECT_ROOT / "schemas" / "ifc" / "generated" / "IFC2X3" / "registry-manifest.json"
)
FEW_SHOT_PATH = (
    PROJECT_ROOT / "prompts" / "agent" / "few-shots" / "design-brief-v2.json"
)

_ENTITY_TERMS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("IfcSpace", ("房间", "空间", "室内")),
    ("IfcWall", ("墙", "墙体")),
    ("IfcDoor", ("门", "门洞")),
    ("IfcWindow", ("窗", "窗户")),
    ("IfcWindowStyle", ("窗型", "开启机构", "WindowStyle")),
    ("IfcOpeningElement", ("洞口", "开洞")),
    ("IfcBuildingStorey", ("楼层", "层高", "单层", "多层")),
    ("IfcSlab", ("楼板", "地板", "板")),
    ("IfcRoof", ("屋顶", "屋面")),
    ("IfcBeam", ("梁",)),
    ("IfcColumn", ("柱",)),
    ("IfcStair", ("楼梯",)),
    ("IfcRailing", ("栏杆", "扶手")),
    ("IfcCurtainWall", ("幕墙",)),
    ("IfcCovering", ("天花", "吊顶", "饰面")),
)

_COMMON_SCHEMA_FRAGMENTS = (
    ("schema:bim-json-v2:root", "/"),
    ("schema:bim-json-v2:entity", "/$defs/entity"),
    ("schema:bim-json-v2:attributes", "/$defs/attributes"),
    ("schema:bim-json-v2:representation", "/$defs/representation"),
    ("schema:bim-json-v2:profile", "/$defs/profile"),
    ("schema:bim-json-v2:object-placement", "/$defs/objectPlacement"),
    ("schema:bim-json-v2:relationship", "/$defs/relationship"),
)


def select_design_brief_context(
    *,
    user_request: str,
    conversation: list[dict[str, Any]],
    max_few_shots: int = 3,
) -> dict[str, Any]:
    """Select request-relevant evidence without deciding which facts are required."""
    request_text = user_request + "\n" + "\n".join(
        str(turn.get("content", ""))
        for turn in conversation
        if isinstance(turn, dict)
    )
    evidence: list[dict[str, Any]] = []
    for evidence_id, pointer in _COMMON_SCHEMA_FRAGMENTS:
        evidence.append(
            _evidence_record(
                evidence_id=evidence_id,
                kind="bim_json_schema",
                source_path=BIM_JSON_SCHEMA_PATH,
                json_pointer=pointer,
            )
        )

    selected_classes = _select_ifc_classes(request_text)
    for ifc_class in selected_classes:
        evidence.append(
            _evidence_record(
                evidence_id=f"capability:IFC2X3:{ifc_class}",
                kind="ifc_generation_capability",
                source_path=CAPABILITY_PATH,
                json_pointer=f"/entities/{ifc_class}",
            )
        )
    evidence.append(
        _evidence_record(
            evidence_id="registry:IFC2X3:manifest",
            kind="ifc_registry_manifest",
            source_path=REGISTRY_MANIFEST_PATH,
            json_pointer="/",
        )
    )

    few_shots = _select_few_shots(request_text, max_few_shots=max_few_shots)
    return {
        "schema_version": "text2ifc/design-brief-context/1.0",
        "request_sha256": "sha256:"
        + hashlib.sha256(user_request.encode("utf-8")).hexdigest(),
        "selected_ifc_classes": selected_classes,
        "evidence": evidence,
        "few_shots": few_shots,
    }


def _select_ifc_classes(text: str) -> list[str]:
    selected = [
        ifc_class
        for ifc_class, terms in _ENTITY_TERMS
        if any(term in text for term in terms)
    ]
    if "IfcDoor" in selected or "IfcWindow" in selected:
        selected.extend(
            ["IfcOpeningElement", "IfcRelVoidsElement", "IfcRelFillsElement"]
        )
    return list(dict.fromkeys(selected))


def _select_few_shots(text: str, *, max_few_shots: int) -> list[dict[str, Any]]:
    payload = _load_json(FEW_SHOT_PATH)
    candidates = []
    for index, record in enumerate(payload.get("few_shots", [])):
        if not isinstance(record, dict):
            continue
        terms = [str(term) for term in record.get("selection_terms", [])]
        score = sum(1 for term in terms if term in text)
        candidates.append((score, -index, record))
    candidates.sort(reverse=True, key=lambda item: (item[0], item[1]))
    selected = [record for score, _, record in candidates if score > 0][
        : max(0, max_few_shots)
    ]
    if not selected and candidates and max_few_shots > 0:
        selected = [candidates[0][2]]
    return json.loads(json.dumps(selected, ensure_ascii=False))


def _evidence_record(
    *,
    evidence_id: str,
    kind: str,
    source_path: Path,
    json_pointer: str,
) -> dict[str, Any]:
    payload = _load_json(source_path)
    return {
        "evidence_id": evidence_id,
        "kind": kind,
        "source_path": source_path.relative_to(PROJECT_ROOT).as_posix(),
        "source_sha256": "sha256:" + hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "json_pointer": json_pointer,
        "content": _resolve_json_pointer(payload, json_pointer),
    }


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _resolve_json_pointer(payload: Any, pointer: str) -> Any:
    if pointer in {"", "/"}:
        return payload
    current = payload
    for raw_token in pointer.lstrip("/").split("/"):
        token = raw_token.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, dict) or token not in current:
            raise ValueError(f"JSON pointer {pointer!r} does not exist")
        current = current[token]
    return current
