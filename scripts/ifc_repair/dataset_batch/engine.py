"""Deterministic isolated mutations of source copies, with complete audit files."""
from __future__ import annotations

import hashlib
import itertools
import json
import math
import os
import random
import tempfile
import time
import uuid
from pathlib import Path

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.guid
import ifcopenshell.util.element
import ifcopenshell.util.placement
import ifcopenshell.util.unit
import numpy as np
from ifcopenshell.api.root.remove_product import remove_product

from text2ifc_ifc_repair.mutation import _canonicalize_structural_relationship_sets, _restore_owner_history, _snapshot_owner_history

from .prompts import render_prompts
from .geometry_spec import body_spec, mesh_fingerprint
from .geometry_deletion import guard_geometry
from .validation import native_validate, product_state, sha256, verify_case

CLASSES = {"door": "IfcDoor", "window": "IfcWindow", "beam": "IfcBeam", "column": "IfcColumn"}
FAMILIES = {"door": ("door",), "window": ("window",), "door_window": ("door", "window"), "beam": ("beam",), "column": ("column",), "beam_column": ("beam", "column"), "door_window_beam_column": tuple(CLASSES)}
VALUE_TYPES = {"IfcBoolean", "IfcLogical", "IfcLabel", "IfcText", "IfcIdentifier", "IfcInteger", "IfcReal", "IfcLengthMeasure", "IfcPositiveLengthMeasure", "IfcAreaMeasure", "IfcVolumeMeasure"}


def write_json(path: Path, value: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _matrix(placement, unit):
    value = np.array(ifcopenshell.util.placement.get_local_placement(placement), dtype=float) if placement else np.eye(4)
    value[:3, 3] *= unit
    return value


def _geometry(product, storey, host, unit):
    settings = ifcopenshell.geom.settings()
    # Default mesh vertices are in product-local metres; transform exactly once.
    shape = ifcopenshell.geom.create_shape(settings, product)
    vertices = np.array(shape.geometry.verts, dtype=float).reshape(-1, 3)
    if not len(vertices) or not np.isfinite(vertices).all():
        raise ValueError("GEOMETRY_UNAVAILABLE")
    matrix = _matrix(product.ObjectPlacement, unit)
    storey_matrix = _matrix(storey.ObjectPlacement, unit) if storey else np.eye(4)
    local = np.linalg.inv(storey_matrix) @ matrix
    result = {"origin_world_m": matrix[:3, 3].tolist(), "origin_storey_m": local[:3, 3].tolist(), "axes_world": matrix[:3, :3].T.tolist(), "axes_storey": local[:3, :3].T.tolist(), "bounds_local_m": [vertices.min(axis=0).tolist(), vertices.max(axis=0).tolist()], "dimensions_local_m": (vertices.max(axis=0) - vertices.min(axis=0)).tolist(), "storey_frame_world_m": storey_matrix.tolist(), "body_spec": body_spec(product, unit), "mesh_fingerprint": mesh_fingerprint(shape)}
    if host:
        relative = np.linalg.inv(_matrix(host.ObjectPlacement, unit)) @ matrix
        result.update(origin_host_m=relative[:3, 3].tolist(), axes_host=relative[:3, :3].T.tolist(), host_frame_world_m=_matrix(host.ObjectPlacement, unit).tolist())
    return result


def _snapshot(product, unit):
    storeys = {rel.RelatingStructure.GlobalId: rel.RelatingStructure for rel in getattr(product, "ContainedInStructure", ()) if rel.RelatingStructure.is_a("IfcBuildingStorey")}
    if not storeys:
        storey = ifcopenshell.util.element.get_container(product, ifc_class="IfcBuildingStorey")
    else:
        storey = next(iter(storeys.values())) if len(storeys) == 1 else None
    if storey is None:
        raise ValueError("UNIQUE_STOREY_UNAVAILABLE")
    fillings = list(getattr(product, "FillsVoids", ()) or ())
    opening = fillings[0].RelatingOpeningElement if len(fillings) == 1 else None
    voids = list(getattr(opening, "VoidsElements", ()) or ()) if opening else []
    host = voids[0].RelatingBuildingElement if len(voids) == 1 else None
    if host is not None and not host.is_a("IfcWall"):
        host = None
    kind = ifcopenshell.util.element.get_type(product)
    model = product.file
    storey_unique = bool(storey.Name) and sum(other.Name == storey.Name and np.allclose(_matrix(other.ObjectPlacement, unit), _matrix(storey.ObjectPlacement, unit), atol=1e-10, rtol=0) for other in model.by_type("IfcBuildingStorey")) == 1
    host_unique = bool(host.Name) and sum(other.Name == host.Name and np.allclose(_matrix(other.ObjectPlacement, unit), _matrix(host.ObjectPlacement, unit), atol=1e-10, rtol=0) for other in model.by_type("IfcWall")) == 1 if host else False
    return {"guid": str(product.GlobalId), "step_id": product.id(), "ifc_class": product.is_a(), "name": product.Name, "tag": getattr(product, "Tag", None), "storey": {"guid": str(storey.GlobalId), "name": storey.Name, "name_frame_unique": storey_unique, "elevation_project_units": storey.Elevation}, "host": {"guid": str(host.GlobalId), "name": host.Name, "name_frame_unique": host_unique} if host else {}, "opening_guid": str(opening.GlobalId) if opening else None, "opening": {"guid": str(opening.GlobalId), "name": opening.Name, "ifc_class": opening.is_a(), "geometry": _geometry(opening, storey, host, unit)} if opening and host else None, "type_guid": str(kind.GlobalId) if kind else None, "type_name": kind.Name if kind else None, "geometry": _geometry(product, storey, host, unit)}


def inventory_model(path: Path) -> dict:
    model = ifcopenshell.open(str(path))
    if model.schema != "IFC2X3":
        raise ValueError("UNSUPPORTED_IFC_SCHEMA")
    unit = ifcopenshell.util.unit.calculate_unit_scale(model)
    result = {"schema": model.schema, "unit_to_m": unit, "targets": {family: [] for family in CLASSES}, "properties": [], "excluded_targets": [], "product_count": len(model.by_type("IfcProduct")), "class_counts": {family: len(model.by_type(cls)) for family, cls in CLASSES.items()}}
    snapshots = {}
    products = sorted([*itertools.chain.from_iterable(model.by_type(cls) for cls in CLASSES.values()), *model.by_type("IfcWall")], key=lambda p: str(p.GlobalId))
    for product in products:
        try:
            snapshot = _snapshot(product, unit)
            if not snapshot["storey"]["name_frame_unique"]:
                raise ValueError("AMBIGUOUS_OR_UNNAMED_STOREY_FRAME")
            snapshots[product.GlobalId] = snapshot
            family = next((key for key, cls in CLASSES.items() if product.is_a(cls)), None)
            if family and (family not in {"door", "window"} or snapshot["host"]):
                result["targets"][family].append(snapshot)
        except Exception as exc:
            result["excluded_targets"].append({"guid": str(product.GlobalId), "class": product.is_a(), "reason": f"{type(exc).__name__}: {exc}"})
            continue
        for rel in getattr(product, "IsDefinedBy", ()):
            if not rel.is_a("IfcRelDefinesByProperties") or not rel.RelatingPropertyDefinition.is_a("IfcPropertySet"):
                continue
            pset = rel.RelatingPropertyDefinition
            for prop in pset.HasProperties:
                if not prop.is_a("IfcPropertySingleValue") or prop.NominalValue is None or prop.NominalValue.is_a() not in VALUE_TYPES:
                    continue
                value = prop.NominalValue.wrappedValue
                if not isinstance(value, (bool, int, float, str)) or (isinstance(value, float) and not math.isfinite(value)):
                    continue
                result["properties"].append({**snapshot, "pset_name": str(pset.Name), "property_name": str(prop.Name), "value_type": prop.NominalValue.is_a(), "before": value})
    groups = {}
    public_identity_counts = {}
    for snapshot in snapshots.values():
        key = (snapshot["name"], tuple(snapshot["geometry"]["origin_world_m"]))
        public_identity_counts[key] = public_identity_counts.get(key, 0) + 1
    for snapshot in snapshots.values():
        if snapshot["name"]:
            groups.setdefault((snapshot["ifc_class"], snapshot["geometry"]["mesh_fingerprint"]), []).append(snapshot)
    for rows in result["targets"].values():
        for target in rows:
            peers = groups.get((target["ifc_class"], target["geometry"]["mesh_fingerprint"]), [])
            target["geometry"]["peers"] = [{"guid": p["guid"], "name": p["name"], "ifc_class": p["ifc_class"], "origin_world_m": p["geometry"]["origin_world_m"], "axes_world": p["geometry"]["axes_world"]} for p in peers if p["guid"] != target["guid"] and public_identity_counts[(p["name"], tuple(p["geometry"]["origin_world_m"]))] == 1]
            if not target["geometry"]["body_spec"] and not target["geometry"]["peers"]:
                result["excluded_targets"].append({"guid": target["guid"], "class": target["ifc_class"], "reason": "no complete parametric body or unambiguous named equal-geometry peer"})
        rows[:] = [target for target in rows if target["geometry"]["body_spec"] or target["geometry"]["peers"]]
    result["properties"].sort(key=lambda row: (row["guid"], row["pset_name"], row["property_name"]))
    property_identity_counts = {}
    for snapshot in snapshots.values():
        key = (snapshot["ifc_class"], snapshot["name"], tuple(snapshot["geometry"]["origin_world_m"]))
        property_identity_counts[key] = property_identity_counts.get(key, 0) + 1
    result["properties"] = [row for row in result["properties"] if property_identity_counts[(row["ifc_class"], row["name"], tuple(row["geometry"]["origin_world_m"]))] == 1]
    # Opening geometry is its own requirement, never inferred from door/window bounds.
    openings = {row["opening"]["guid"]: row["opening"] for row in snapshots.values() if row.get("opening")}
    for opening in openings.values():
        opening["geometry"]["peers"] = [{"guid": peer["guid"], "name": peer["name"], "ifc_class": peer["ifc_class"], "origin_world_m": peer["geometry"]["origin_world_m"], "axes_world": peer["geometry"]["axes_world"]} for peer in openings.values() if peer["guid"] != opening["guid"] and peer["name"] and peer["geometry"]["mesh_fingerprint"] == opening["geometry"]["mesh_fingerprint"] and sum(other.Name == peer["name"] and np.allclose(_matrix(other.ObjectPlacement, unit)[:3, 3], peer["geometry"]["origin_world_m"], atol=1e-10, rtol=0) for other in model.by_type("IfcOpeningElement")) == 1]
    result["inventory_version"] = 3
    result["geometry_scope"] = "native geometry of deletion/property candidates and their wall hosts; complete supported extrusions or a surviving equal-geometry named reference for deletion prompts"
    return result


def _wrong_value(prop, variant):
    value = prop["before"]
    if prop["value_type"] == "IfcLogical" and value == "UNKNOWN":
        return bool(variant % 2)
    if isinstance(value, bool):
        return not value
    if isinstance(value, str):
        return f"{value} [damage-{variant:02d}]"
    if isinstance(value, int):
        return value + variant + 1
    changed = value * (1 + (variant + 1) / 10) if value else float(variant + 1)
    return changed


def build_recipes(inventory: dict, *, count=25, seed=42) -> list[dict]:
    if not 1 <= count <= 30:
        raise ValueError("CASE_COUNT_MUST_BE_BETWEEN_1_AND_30")
    randomizer = random.Random(seed)
    targets = inventory["targets"]
    available = [(name, families) for name, families in FAMILIES.items() if all(targets.get(f) for f in families)]
    properties = inventory["properties"]
    result, seen = [], set()

    def add(family, severity, deleted, changed):
        if len(deleted) > 30:
            return
        identities = {x["guid"] for x in deleted}
        identities.update(x["opening_guid"] for x in deleted if x.get("opening_guid") and not x.get("preserve_opening", True))
        resolved = []
        for target in deleted:
            geometry = dict(target["geometry"])
            if not geometry.get("body_spec"):
                peer = next((p for p in geometry.get("peers", []) if p["guid"] not in identities), None)
                if peer is None:
                    return
                geometry["body_spec"] = {"method": "surviving_instance", "peer": peer}
            opening = target.get("opening")
            if opening and not target.get("preserve_opening", True):
                opening_geometry = dict(opening["geometry"])
                if not opening_geometry.get("body_spec"):
                    peer = next((p for p in opening_geometry.get("peers", []) if p["guid"] not in identities), None)
                    if peer is None:
                        return
                    opening_geometry["body_spec"] = {"method": "surviving_instance", "peer": peer}
                opening = {**opening, "geometry": opening_geometry}
            resolved.append({**target, "geometry": geometry, "opening": opening})
        deleted = resolved
        key = json.dumps({"delete": sorted((x["guid"], x.get("preserve_opening", True)) for x in deleted), "change": sorted((x["guid"], x["pset_name"], x["property_name"], str(x["after"])) for x in changed)}, sort_keys=True)
        if key in seen or not (deleted or changed):
            return
        seen.add(key)
        result.append({"family": family, "severity": severity, "deletions": deleted, "property_changes": changed})

    # Coverage is scheduled before random combinations; absent families are skipped.
    for cycle in range(90):
        severity = ("light", "medium", "heavy")[cycle % 3]
        for family, families in available:
            deleted = []
            for f in families:
                population = targets[f]
                n = 1 if severity == "light" else min(len(population), 3) if severity == "medium" else min(len(population), max(4, math.ceil(len(population) * 0.3)), 30 // len(families))
                for target in randomizer.sample(population, n):
                    deleted.append({**target, "preserve_opening": bool(target.get("opening_guid")) and (f == "door" and cycle % 2 == 0)})
            add(family, severity, deleted, [])
        if properties:
            prop = properties[cycle % len(properties)]
            add("attribute", severity, [], [{**prop, "after": _wrong_value(prop, cycle)}])
        if cycle >= 1 and available and properties:
            family, families = available[cycle % len(available)]
            deleted = [{**randomizer.choice(targets[f]), "preserve_opening": False} for f in families]
            eligible = [p for p in properties if p["guid"] not in {d["guid"] for d in deleted}]
            if eligible:
                prop = randomizer.choice(eligible)
                add(family + "_attribute", severity, deleted, [{**prop, "after": _wrong_value(prop, cycle)}])
        if cycle == 2 and targets.get("window"):
            deleted = [{**target, "preserve_opening": False} for target in targets["window"]]
            doors = [p for p in properties if p["ifc_class"] == "IfcDoor"]
            if doors:
                prop = randomizer.choice(doors)
                add("all_windows_door_attribute", "heavy", deleted, [{**prop, "after": _wrong_value(prop, cycle)}])
        # Finish a complete cycle, then allocate room for compound cases.
        if len(result) >= count + 5:
            break
    if len(result) > count:
        mandatory = []
        for name in [*(name for name, _ in available), "attribute", "all_windows_door_attribute"]:
            item = next((r for r in result if r["family"] == name), None)
            if item:
                mandatory.append(item)
        compound = next((r for r in result if r["deletions"] and r["property_changes"]), None)
        if compound and compound not in mandatory:
            mandatory.append(compound)
        mandatory = mandatory[:count]
        candidates = [r for r in result if r not in mandatory]
        result = mandatory + candidates[:count - len(mandatory)]
    return result[:count]


def _change_property(model, change, namespace):
    element = model.by_guid(change["guid"])
    matches = [(rel, rel.RelatingPropertyDefinition, prop) for rel in element.IsDefinedBy if rel.is_a("IfcRelDefinesByProperties") and rel.RelatingPropertyDefinition.is_a("IfcPropertySet") and rel.RelatingPropertyDefinition.Name == change["pset_name"] for prop in rel.RelatingPropertyDefinition.HasProperties if prop.is_a("IfcPropertySingleValue") and prop.Name == change["property_name"]]
    if len(matches) != 1:
        raise ValueError("PROPERTY_BINDING_AMBIGUOUS")
    rel, pset, prop = matches[0]
    if prop.NominalValue is None or prop.NominalValue.is_a() != change["value_type"] or prop.NominalValue.wrappedValue != change["before"]:
        raise ValueError("PROPERTY_BEFORE_VALUE_MISMATCH")
    shared = len(rel.RelatedObjects) > 1 or any(other != rel for other in model.get_inverse(pset))
    if shared:
        copied = [ifcopenshell.util.element.copy(model, item) for item in pset.HasProperties]
        new_pset = model.createIfcPropertySet(ifcopenshell.guid.compress(uuid.uuid5(namespace, "pset:" + change["guid"] + change["pset_name"]).hex), pset.OwnerHistory, pset.Name, pset.Description, copied)
        if len(rel.RelatedObjects) > 1:
            rel.RelatedObjects = tuple(p for p in rel.RelatedObjects if p != element)
            model.createIfcRelDefinesByProperties(ifcopenshell.guid.compress(uuid.uuid5(namespace, "rel:" + change["guid"] + change["pset_name"]).hex), rel.OwnerHistory, None, None, [element], new_pset)
        else:
            rel.RelatingPropertyDefinition = new_pset
        pset = new_pset
        prop = next(p for p in copied if p.Name == change["property_name"])
    elif len(model.get_inverse(prop)) > 1:
        old = prop
        prop = ifcopenshell.util.element.copy(model, old)
        pset.HasProperties = tuple(prop if p == old else p for p in pset.HasProperties)
    prop.NominalValue = model.create_entity(change["value_type"], change["after"])


def _remove_product_with_relationship_cleanup(model, product):
    """Complete the API's removal without deleting unrelated/shared objects.

    file.remove clears references, but an unhandled relationship can then have
    a missing required endpoint or an aggregate below its EXPRESS lower bound.
    Only fields that referenced this product are candidates for this cleanup.
    """
    schema = ifcopenshell.ifcopenshell_wrapper.schema_by_name(model.schema)
    product_id = product.id()

    def references(value):
        if isinstance(value, ifcopenshell.entity_instance):
            return value.id() == product_id
        if isinstance(value, (tuple, list)):
            return any(references(member) for member in value)
        return False

    affected = []
    for relation in model.get_inverse(product):
        if relation.is_a("IfcRelationship"):
            attributes = schema.declaration_by_name(relation.is_a()).all_attributes()
            fields = [(i, attr) for i, attr in enumerate(attributes) if references(relation[i])]
            affected.append((relation.id(), fields))
    with guard_geometry(model, product):
        remove_product(model, product=product)
    for relation_id, fields in affected:
        try:
            relation = model.by_id(relation_id)
        except RuntimeError:
            continue  # The API already removed this relationship.
        for index, attribute in fields:
            value = relation[index]
            aggregate = attribute.type_of_attribute().as_aggregation_type()
            invalid = value is None and not attribute.optional()
            if value is not None and aggregate is not None:
                invalid = len(value) < aggregate.bound1()
            if invalid:
                # Shallow removal preserves coverings, actors, shared types,
                # materials, containers and history still used elsewhere.
                model.remove(relation)
                break


def apply_recipe(source_path: Path, recipe: dict, output: Path, *, inventory=None, baseline_state=None, prompt_profile="text2ifc/dataset-request/1.1") -> dict:
    if prompt_profile not in {"text2ifc/dataset-request/1.1", "text2ifc/dataset-request/1.2", "text2ifc/dataset-request/1.3"}:
        raise ValueError("UNSUPPORTED_DATASET_REQUEST_PROFILE")
    source_path, output = Path(source_path).resolve(), Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    if source_path.is_relative_to(output):
        raise ValueError("SOURCE_INSIDE_OUTPUT")
    started = time.monotonic()
    source_hash = sha256(source_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".building-", dir=output.parent))
    public, private = stage / "public", stage / "private"
    public.mkdir(); private.mkdir()
    model = ifcopenshell.open(str(source_path))
    if model.schema != "IFC2X3":
        raise ValueError("UNSUPPORTED_IFC_SCHEMA")
    if baseline_state is None:
        baseline_state = product_state(model)
    histories = _snapshot_owner_history(model)
    touched_relations = set()
    removed_relationships = {}
    for target in recipe["deletions"]:
        element = model.by_guid(target["guid"])
        entities = [element]
        if target.get("opening_guid") and not target.get("preserve_opening", True):
            entities.append(model.by_guid(target["opening_guid"]))
        for entity in entities:
            for relation in model.get_inverse(entity):
                if relation.is_a("IfcRelationship"):
                    touched_relations.add(relation.id())
                    removed_relationships[relation.GlobalId] = {"guid": str(relation.GlobalId), "class": relation.is_a()}
        _remove_product_with_relationship_cleanup(model, element)
        if len(entities) > 1:
            _remove_product_with_relationship_cleanup(model, entities[1])
    namespace = uuid.uuid5(uuid.NAMESPACE_URL, source_hash + json.dumps(recipe, sort_keys=True, ensure_ascii=False))
    for change in recipe["property_changes"]:
        _change_property(model, change, namespace)
    _restore_owner_history(model, histories)
    _canonicalize_structural_relationship_sets(model, touched_relations)
    damaged = public / "model.ifc"
    model.write(str(damaged))
    reopened = ifcopenshell.open(str(damaged))
    manifest = {"schema_version": "text2ifc/ifc-repair-dataset-mutation/1.1", "prompt_profile": "text2ifc/dataset-request/1.1", "source_sha256": source_hash, "damaged_sha256": sha256(damaged), "family": recipe["family"], "severity": recipe["severity"], "deletions": recipe["deletions"], "property_changes": recipe["property_changes"], "affected_relationships": list(removed_relationships.values()), "human_review": {"status": "pending_human_review", "human_viewed": False}, "reference_role": "preassigned synthetic task reference; private evaluation only; never production input"}
    manifest["prompt_profile"] = prompt_profile
    if prompt_profile in {"text2ifc/dataset-request/1.2", "text2ifc/dataset-request/1.3"}:
        manifest["schema_version"] = "text2ifc/ifc-repair-dataset-mutation/" + prompt_profile.rsplit('/', 1)[1]
    validation = native_validate(reopened)
    preservation = verify_case(source_path, reopened, manifest, baseline_state=baseline_state)
    if prompt_profile == "text2ifc/dataset-request/1.3":
        from .prompts_v3 import render_prompts as render_v3
        prompts = render_v3(manifest)
    elif prompt_profile == "text2ifc/dataset-request/1.2":
        from .prompts_v2 import render_prompts as render_v2
        prompts = render_v2(manifest)
    else:
        prompts = render_prompts(manifest)
    for name, text in prompts.items():
        if text is not None:
            (public / f"request-{name}.txt").write_text(text, encoding="utf-8")
    applicable = {name: {"applicable": text is not None, "reason": None if text is not None else "missing valid wall host or unique named storey", "sha256": sha256(public / f"request-{name}.txt") if text is not None else None} for name, text in prompts.items()}
    deleted_identities = {identity for row in recipe["deletions"] for identity in (row["guid"], row.get("opening_guid")) if identity}
    leakage = any(identity in text for identity in deleted_identities for text in prompts.values() if text)
    unchanged = sha256(source_path) == source_hash
    required_prompts = ("world", "storey_local") if prompt_profile == "text2ifc/dataset-request/1.1" else ("world",)
    passed = validation["passed"] and preservation["passed"] and unchanged and not leakage and all(prompts[name] is not None for name in required_prompts)
    result = {"schema_version": "text2ifc/ifc-repair-dataset-case/1.0", "status": "passed" if passed else "failed", "family": recipe["family"], "severity": recipe["severity"], "source_sha256": source_hash, "damaged_sha256": manifest["damaged_sha256"], "deleted_counts": {f: sum(t["ifc_class"] == cls for t in recipe["deletions"]) for f, cls in CLASSES.items()}, "property_changes": len(recipe["property_changes"]), "source_unchanged": unchanged, "private_identity_leakage": leakage, "machine_validated": passed, "human_reviewed": False, "prompt_templates": applicable, "elapsed_seconds": round(time.monotonic() - started, 3)}
    write_json(private / "mutation.json", manifest)
    write_json(private / "recipe.json", recipe)
    write_json(private / "validation.json", validation)
    write_json(private / "preservation.json", preservation)
    write_json(stage / "case.json", result)
    seal_case(stage)
    os.replace(stage, output)
    return result


def seal_case(folder: Path):
    case = json.loads((folder / "case.json").read_text(encoding="utf-8"))
    paths = ["case.json", "public/model.ifc", "private/mutation.json", "private/recipe.json", "private/validation.json", "private/preservation.json"]
    paths.extend(f"public/request-{name}.txt" for name, meta in case["prompt_templates"].items() if meta["applicable"])
    paths.extend(case.get("additional_evidence", []))
    write_json(folder / "private/seal.json", {"schema_version": "text2ifc/ifc-repair-dataset-seal/1.0", "sha256": {name: sha256(folder / name) for name in paths}})


def verify_seal(folder: Path) -> bool:
    try:
        seal = json.loads((folder / "private/seal.json").read_text(encoding="utf-8"))
        hashes = seal["sha256"]
        required = {"case.json", "public/model.ifc", "private/mutation.json", "private/recipe.json", "private/validation.json", "private/preservation.json"}
        case = json.loads((folder / "case.json").read_text(encoding="utf-8"))
        required.update(f"public/request-{name}.txt" for name, meta in case["prompt_templates"].items() if meta["applicable"])
        required.update(case.get("additional_evidence", []))
        return set(hashes) == required and all(sha256(folder / name) == value for name, value in hashes.items())
    except (OSError, ValueError, KeyError):
        return False
