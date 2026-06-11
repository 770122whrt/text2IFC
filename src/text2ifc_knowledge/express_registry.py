"""Generate deterministic declaration metadata from IFC EXPRESS."""

from __future__ import annotations

import gc
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any


def _name(declaration) -> str:
    return declaration.name()


def _supertype_chain(entity) -> list[str]:
    chain: list[str] = []
    current = entity.supertype()
    while current is not None:
        chain.append(_name(current))
        current = current.supertype()
    return chain


def _attribute_record(attribute, *, derived: bool) -> dict[str, Any]:
    return {
        "name": attribute.name(),
        "optional": bool(attribute.optional()),
        "derived": derived,
        "type": str(attribute.type_of_attribute()),
    }


def _entity_record(entity) -> dict[str, Any]:
    all_attributes = list(entity.all_attributes())
    derived_flags = list(entity.derived())
    attributes = [
        _attribute_record(attribute, derived=bool(derived_flags[index]))
        for index, attribute in enumerate(all_attributes)
    ]
    direct_attributes = list(entity.attributes())
    direct_offset = len(all_attributes) - len(direct_attributes)
    declared_attributes = [
        _attribute_record(
            attribute,
            derived=bool(derived_flags[direct_offset + index]),
        )
        for index, attribute in enumerate(direct_attributes)
    ]
    inverses = []
    for inverse in entity.all_inverse_attributes():
        inverses.append(
            {
                "name": inverse.name(),
                "entity": _name(inverse.entity_reference()),
                "attribute": inverse.attribute_reference().name(),
                "aggregation": inverse.type_of_aggregation_string(),
                "lower_bound": inverse.bound1(),
                "upper_bound": inverse.bound2(),
            }
        )
    supertype = entity.supertype()
    return {
        "kind": "entity",
        "abstract": bool(entity.is_abstract()),
        "supertype": _name(supertype) if supertype is not None else None,
        "supertypes": _supertype_chain(entity),
        "subtypes": sorted(_name(item) for item in entity.subtypes()),
        "declared_attributes": declared_attributes,
        "attributes": attributes,
        "inverse_attributes": inverses,
    }


def _declaration_record(declaration) -> dict[str, Any]:
    entity = declaration.as_entity()
    if entity is not None:
        return _entity_record(entity)

    select = declaration.as_select_type()
    if select is not None:
        return {
            "kind": "select",
            "items": [_name(item) for item in select.select_list()],
        }

    enumeration = declaration.as_enumeration_type()
    if enumeration is not None:
        return {
            "kind": "enumeration",
            "items": list(enumeration.enumeration_items()),
        }

    type_declaration = declaration.as_type_declaration()
    if type_declaration is not None:
        return {
            "kind": "type",
            "declared_type": str(type_declaration.declared_type()),
        }

    raise TypeError(f"unsupported IFC declaration: {declaration!r}")


def _build_from_schema(schema) -> dict[str, Any]:
    declarations = {
        _name(declaration): _declaration_record(declaration)
        for declaration in sorted(schema.declarations(), key=_name)
    }
    entity_count = sum(
        record["kind"] == "entity" for record in declarations.values()
    )
    return {
        "schema": schema.name(),
        "counts": {
            "declarations": len(declarations),
            "entities": entity_count,
        },
        "declarations": declarations,
    }


def _build_from_express_worker(express_path: str | Path) -> dict[str, Any]:
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".json",
            delete=False,
        ) as output:
            temporary = Path(output.name)
        environment = os.environ.copy()
        environment["PYTHONPATH"] = os.pathsep.join(
            str(path) for path in sys.path if path
        )
        completed = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "--worker",
                str(Path(express_path).resolve()),
                str(temporary),
            ],
            capture_output=True,
            text=True,
            env=environment,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                "IFC EXPRESS worker failed"
                + (f": {completed.stderr.strip()}" if completed.stderr else "")
            )
        with temporary.open("r", encoding="utf-8") as stream:
            return json.load(stream)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def build_declaration_registry(
    express_path: str | Path,
    *,
    schema=None,
) -> dict[str, Any]:
    if schema is not None:
        return _build_from_schema(schema)
    return _build_from_express_worker(express_path)


def _worker_main(express_path: str, output_path: str) -> None:
    import ifcopenshell.express

    # Keep all late-bound SWIG wrappers alive until the hard process exit.
    gc.disable()
    schema = ifcopenshell.express.parse(express_path).schema
    registry = _build_from_schema(schema)
    with Path(output_path).open("w", encoding="utf-8") as output:
        json.dump(registry, output, ensure_ascii=True, sort_keys=True)
        output.flush()
        os.fsync(output.fileno())
    # IfcOpenShell 0.8.5 corrupts the Windows heap while destroying a
    # late-bound EXPRESS schema. The worker has no remaining state to flush.
    os._exit(0)


if __name__ == "__main__":
    if len(sys.argv) != 4 or sys.argv[1] != "--worker":
        raise SystemExit("usage: express_registry.py --worker INPUT.exp OUTPUT.json")
    _worker_main(sys.argv[2], sys.argv[3])
