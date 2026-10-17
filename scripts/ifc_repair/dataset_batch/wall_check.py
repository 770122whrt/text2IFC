"""Read-only, fail-closed checks of walls affected by opening deletion.

The expected wall is computed from a separately opened reference by removing
only the recorded void relationships in memory. Mesh equivalence alone cannot
prove closure: a Body may already contain a baked hole. Interior probes therefore
also have to establish original uncut wall material, an empty original opening,
and the required damaged-wall occupancy. This is a finite geometric check, not a
proof of every point in a curved or complex opening volume.
"""
from __future__ import annotations

import hashlib
import itertools
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.placement
import ifcopenshell.util.unit
import numpy as np

_MESH_TOLERANCE_M = 1e-7
_POINT_TOLERANCE_M = 5e-7
_MIN_PROBES = 3
_SCOPE = (
    "Read-only evaluation of reference-bound walls in manifest.deletions; "
    "world mesh, closed/oriented surface and volume, exact void membership, "
    "retained opening geometry, and finite interior occupancy probes. "
    "No Provider call, IFC write, whole-model preservation or complete-volume proof. "
    "Unconfirmed or ambiguous applicable geometry fails closed."
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _find(model, guid):
    try:
        return model.by_guid(guid)
    except (RuntimeError, TypeError):
        return None


def _error(errors, code, *, wall_guid=None, opening_guid=None, detail=None):
    row = {"code": code}
    for key, value in (("wall_guid", wall_guid), ("opening_guid", opening_guid), ("detail", detail)):
        if value is not None:
            row[key] = value
    errors.append(row)


@dataclass
class _Mesh:
    vertices: np.ndarray
    faces: np.ndarray
    fingerprint: str
    closed: bool
    oriented: bool
    volume: float

    def summary(self):
        return {
            "closed": self.closed,
            "consistently_oriented": self.oriented,
            "vertex_count": len(self.vertices),
            "triangle_count": len(self.faces),
            "volume_m3": round(self.volume, 12),
            "normalized_mesh_sha256": self.fingerprint,
        }


def _mesh(product, *, uncut=False) -> _Mesh:
    if product is None:
        raise ValueError("product missing")
    settings = ifcopenshell.geom.settings()
    settings.set("use-world-coords", True)
    settings.set("weld-vertices", True)
    settings.set("disable-opening-subtractions", uncut)
    shape = ifcopenshell.geom.create_shape(settings, product)
    vertices = np.asarray(shape.geometry.verts, dtype=float).reshape(-1, 3)
    faces = np.asarray(shape.geometry.faces, dtype=np.int64).reshape(-1, 3)
    if not len(vertices) or not len(faces) or not np.isfinite(vertices).all():
        raise ValueError("empty or nonfinite mesh")
    if faces.min() < 0 or faces.max() >= len(vertices):
        raise ValueError("invalid mesh indices")
    scaled = vertices / _MESH_TOLERANCE_M
    if np.max(np.abs(scaled)) >= np.iinfo(np.int64).max / 2:
        raise ValueError("coordinates exceed normalization range")
    quantized = np.rint(scaled).astype(np.int64)
    keys = [tuple(int(value) for value in vertex) for vertex in quantized]
    triangles = []
    edges = Counter()
    directions = Counter()
    degenerate = False
    for face in faces:
        triangle = tuple(keys[int(index)] for index in face)
        triangles.append(tuple(sorted(triangle)))
        if len(set(triangle)) < 3:
            degenerate = True
        for a, b in zip(triangle, triangle[1:] + triangle[:1]):
            edge = tuple(sorted((a, b)))
            edges[edge] += 1
            directions[edge] += 1 if a < b else -1
    fingerprint = hashlib.sha256(np.asarray(sorted(triangles), dtype=np.int64).tobytes()).hexdigest()
    closed = bool(edges) and not degenerate and all(count == 2 for count in edges.values())
    oriented = closed and all(count == 0 for count in directions.values())
    # Translate near the mesh before summing to avoid cancellation at large
    # georeferenced coordinates. Consistent winding is checked separately.
    centred = vertices - vertices.mean(axis=0)
    a, b, c = (centred[faces[:, index]] for index in range(3))
    volume = abs(float(np.sum(np.einsum("ij,ij->i", a, np.cross(b, c))) / 6.0))
    if not np.isfinite(volume):
        raise ValueError("nonfinite mesh volume")
    return _Mesh(vertices, faces, fingerprint, closed, oriented, volume)


def _usable(mesh: _Mesh) -> bool:
    return mesh.closed and mesh.oriented and mesh.volume > _MESH_TOLERANCE_M ** 3


def _inside(mesh: _Mesh, point: np.ndarray) -> bool | None:
    """Three independent ray directions; boundary/disagreement is unconfirmed."""
    if not _usable(mesh):
        return None
    tolerance = _POINT_TOLERANCE_M
    if np.any(point < mesh.vertices.min(axis=0) - tolerance) or np.any(point > mesh.vertices.max(axis=0) + tolerance):
        return False
    triangles = mesh.vertices[mesh.faces]
    a, e1, e2 = triangles[:, 0], triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0]
    normal = np.cross(e1, e2)
    lengths = np.linalg.norm(normal, axis=1)
    if np.any(lengths < _MESH_TOLERANCE_M ** 2):
        return None
    delta = point - a
    near = np.abs(np.einsum("ij,ij->i", delta, normal)) / lengths <= tolerance
    if np.any(near):
        d00 = np.einsum("ij,ij->i", e1[near], e1[near])
        d01 = np.einsum("ij,ij->i", e1[near], e2[near])
        d11 = np.einsum("ij,ij->i", e2[near], e2[near])
        d20 = np.einsum("ij,ij->i", delta[near], e1[near])
        d21 = np.einsum("ij,ij->i", delta[near], e2[near])
        denominator = d00 * d11 - d01 * d01
        if np.any(denominator <= 0):
            return None
        u, v = (d11 * d20 - d01 * d21) / denominator, (d00 * d21 - d01 * d20) / denominator
        if np.any((u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9)):
            return None
    answers = []
    for vector in ((1.0, 0.371391, 0.193793), (-0.217439, 1.0, 0.413321), (0.179318, -0.263811, 1.0)):
        direction = np.asarray(vector) / np.linalg.norm(vector)
        h = np.cross(direction, e2)
        determinant = np.einsum("ij,ij->i", e1, h)
        valid = np.abs(determinant) > lengths * 1e-10
        if not np.any(valid):
            answers.append(False)
            continue
        q = np.cross(delta[valid], e1[valid])
        u = np.einsum("ij,ij->i", delta[valid], h[valid]) / determinant[valid]
        v = q @ direction / determinant[valid]
        distance = np.einsum("ij,ij->i", e2[valid], q) / determinant[valid]
        hits = (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9) & (distance > tolerance)
        if np.any(hits & ((u <= 1e-8) | (v <= 1e-8) | (u + v >= 1 - 1e-8))):
            continue  # This ray touched a triangulation edge; use other rays.
        distances = np.sort(distance[hits])
        unique = 0 if not len(distances) else 1 + int(np.sum(np.diff(distances) > tolerance))
        answers.append(bool(unique % 2))
    return answers[0] if len(answers) >= 2 and len(set(answers)) == 1 else None


def _probe_points(opening, opening_mesh, uncut_mesh):
    frame = np.asarray(ifcopenshell.util.placement.get_local_placement(opening.ObjectPlacement), dtype=float)
    frame[:3, 3] *= ifcopenshell.util.unit.calculate_unit_scale(opening.file)
    if not np.isfinite(frame).all() or abs(np.linalg.det(frame[:3, :3])) < 1e-12:
        raise ValueError("opening placement unavailable")
    inverse = np.linalg.inv(frame)

    def local(vertices):
        return vertices @ inverse[:3, :3].T + inverse[:3, 3]

    hole, wall = local(opening_mesh.vertices), local(uncut_mesh.vertices)
    low = np.maximum(hole.min(axis=0), wall.min(axis=0))
    high = np.minimum(hole.max(axis=0), wall.max(axis=0))
    if np.any(high - low <= _POINT_TOLERANCE_M * 4):
        return []
    # Use the placement frame, so thin rotated walls and metre/mm projects
    # receive the same interior grid. All selected points must be confirmed;
    # points outside the uncut wall are never silently discarded.
    return [frame[:3, :3] @ (low + (high - low) * np.asarray(fractions)) + frame[:3, 3]
            for fractions in itertools.product((0.25, 0.5, 0.75), repeat=3)]


def _void_map(wall):
    result = {}
    for relation in wall.HasOpenings:
        guid = str(relation.RelatedOpeningElement.GlobalId)
        if guid in result:
            raise ValueError("duplicate void relationship for opening")
        result[guid] = str(relation.GlobalId)
    return result


def _retained_opening(reference, damaged, guid, wall_guid, relation_guid):
    before, after = _find(reference, guid), _find(damaged, guid)
    record = {"opening_guid": guid, "present_after": after is not None, "void_relationship_preserved": False, "geometry_preserved": False, "passed": False}
    if before is None or after is None or not after.is_a("IfcOpeningElement"):
        return record
    relations = list(after.VoidsElements)
    record["void_relationship_preserved"] = len(relations) == 1 and str(relations[0].GlobalId) == relation_guid and str(relations[0].RelatingBuildingElement.GlobalId) == wall_guid
    try:
        a, b = _mesh(before), _mesh(after)
        record["geometry_preserved"] = a.fingerprint == b.fingerprint
    except Exception as exc:
        record["geometry_error"] = f"{type(exc).__name__}: {exc}"
    record["passed"] = record["void_relationship_preserved"] and record["geometry_preserved"]
    return record


def _check_wall(reference, damaged, expected, wall_guid, targets, errors):
    start = len(errors)
    row = {"wall_guid": wall_guid, "passed": False, "opening_checks": [], "other_openings": [], "other_openings_preserved": False, "mesh_equal_expected": False, "mesh_equal_before": False}
    before_wall, after_wall, expected_wall = (_find(model, wall_guid) for model in (reference, damaged, expected))
    if any(wall is None or not wall.is_a("IfcWall") for wall in (before_wall, after_wall, expected_wall)):
        _error(errors, "WALL_BINDING_UNAVAILABLE", wall_guid=wall_guid)
        return row
    try:
        before_voids, after_voids = _void_map(before_wall), _void_map(after_wall)
    except Exception as exc:
        _error(errors, "VOID_MEMBERSHIP_AMBIGUOUS", wall_guid=wall_guid, detail=f"{type(exc).__name__}: {exc}")
        return row
    removed = {guid for guid, target in targets.items() if not target["preserve_opening"]}
    expected_voids = {guid: relation for guid, relation in before_voids.items() if guid not in removed}
    row["opening_count"] = {"before": len(before_voids), "after": len(after_voids), "expected": len(expected_voids)}
    row["void_membership_matches_expected"] = after_voids == expected_voids
    if after_voids != expected_voids:
        _error(errors, "VOID_MEMBERSHIP_MISMATCH", wall_guid=wall_guid)
    valid_targets = {}
    for guid, target in targets.items():
        opening = _find(reference, guid)
        if opening is None or not opening.is_a("IfcOpeningElement") or guid not in before_voids or len(opening.VoidsElements) != 1:
            _error(errors, "REFERENCE_OPENING_BINDING_UNAVAILABLE", wall_guid=wall_guid, opening_guid=guid)
            row["opening_checks"].append({"opening_guid": guid, "preserve_opening": target["preserve_opening"], "passed": False, "probes": []})
            continue
        filling = _find(reference, target.get("guid")) if target.get("guid") else None
        if target.get("guid") and (filling is None or not any(str(rel.RelatingOpeningElement.GlobalId) == guid for rel in getattr(filling, "FillsVoids", ()))):
            _error(errors, "REFERENCE_FILLING_BINDING_MISMATCH", wall_guid=wall_guid, opening_guid=guid)
        if not target["preserve_opening"]:
            # The expected IFC is exclusively an in-memory counterfactual.
            # No opening, filling, representation or file is edited here.
            expected.remove(expected.by_guid(before_voids[guid]))
        valid_targets[guid] = opening
    try:
        meshes = {"before": _mesh(before_wall), "after": _mesh(after_wall), "expected": _mesh(expected_wall), "uncut": _mesh(before_wall, uncut=True)}
        row["meshes"] = {name: mesh.summary() for name, mesh in meshes.items()}
        row["mesh_equal_expected"] = meshes["after"].fingerprint == meshes["expected"].fingerprint
        row["mesh_equal_before"] = meshes["after"].fingerprint == meshes["before"].fingerprint
        row["volume_increase_m3"] = round(meshes["after"].volume - meshes["before"].volume, 12)
        if not all(_usable(mesh) for mesh in meshes.values()):
            _error(errors, "WALL_SOLID_UNCONFIRMED", wall_guid=wall_guid)
        if not row["mesh_equal_expected"]:
            _error(errors, "WALL_MESH_MISMATCH", wall_guid=wall_guid)
        if not np.isclose(meshes["after"].volume, meshes["expected"].volume, rtol=1e-8, atol=1e-10):
            _error(errors, "WALL_VOLUME_MISMATCH", wall_guid=wall_guid)
    except Exception as exc:
        _error(errors, "WALL_GEOMETRY_UNAVAILABLE", wall_guid=wall_guid, detail=f"{type(exc).__name__}: {exc}")
        return row
    for guid in sorted(set(before_voids) - set(targets)):
        other = _retained_opening(reference, damaged, guid, wall_guid, before_voids[guid])
        row["other_openings"].append(other)
        if not other["passed"]:
            _error(errors, "OTHER_OPENING_NOT_PRESERVED", wall_guid=wall_guid, opening_guid=guid)
    row["other_openings_preserved"] = all(item["passed"] for item in row["other_openings"])
    for guid, opening in valid_targets.items():
        target = targets[guid]
        target_start = len(errors)
        preserve = target["preserve_opening"]
        after_opening = _find(damaged, guid)
        check = {"opening_guid": guid, "preserve_opening": preserve, "present_after": after_opening is not None, "passed": False, "probes": []}
        if preserve:
            check.update(_retained_opening(reference, damaged, guid, wall_guid, before_voids[guid]))
            if not check["passed"]:
                _error(errors, "TARGET_OPENING_NOT_PRESERVED", wall_guid=wall_guid, opening_guid=guid)
        else:
            check["void_relationship_removed"] = _find(damaged, before_voids[guid]) is None
            if after_opening is not None or not check["void_relationship_removed"]:
                _error(errors, "TARGET_OPENING_NOT_REMOVED", wall_guid=wall_guid, opening_guid=guid)
        if target.get("guid") and _find(damaged, target["guid"]) is not None:
            _error(errors, "TARGET_FILLING_NOT_REMOVED", wall_guid=wall_guid, opening_guid=guid)
        try:
            hole = _mesh(opening)
            check["opening_mesh"] = hole.summary()
            if not _usable(hole):
                raise ValueError("opening is not a confirmed closed, oriented solid")
            points = _probe_points(opening, hole, meshes["uncut"])
            check["candidate_count"] = len(points)
            ambiguous = 0
            for point in points:
                opening_inside = _inside(hole, point)
                if opening_inside is False:
                    continue
                if opening_inside is None:
                    ambiguous += 1
                    continue
                check["probes"].append({
                    "world_m": [round(float(value), 9) for value in point],
                    "inside_uncut_wall": _inside(meshes["uncut"], point),
                    "inside_wall_before": _inside(meshes["before"], point),
                    "inside_wall_after": _inside(meshes["after"], point),
                    "inside_wall_expected": _inside(meshes["expected"], point),
                })
            if ambiguous or len(check["probes"]) < _MIN_PROBES:
                _error(errors, "OPENING_INTERIOR_PROBES_UNCONFIRMED", wall_guid=wall_guid, opening_guid=guid)
            if any(probe["inside_uncut_wall"] is not True for probe in check["probes"]):
                _error(errors, "ORIGINAL_UNCUT_WALL_INTERIOR_UNCONFIRMED", wall_guid=wall_guid, opening_guid=guid)
            if any(probe["inside_wall_before"] is not False for probe in check["probes"]):
                _error(errors, "ORIGINAL_OPENING_VOID_UNCONFIRMED", wall_guid=wall_guid, opening_guid=guid)
            desired = not preserve
            check["occupancy_confirmed"] = len(check["probes"]) >= _MIN_PROBES and all(probe["inside_wall_after"] is desired and probe["inside_wall_expected"] is desired for probe in check["probes"])
            if not check["occupancy_confirmed"]:
                _error(errors, "PRESERVED_VOID_UNCONFIRMED" if preserve else "OPENING_CLOSURE_UNCONFIRMED", wall_guid=wall_guid, opening_guid=guid)
        except Exception as exc:
            _error(errors, "OPENING_GEOMETRY_UNAVAILABLE", wall_guid=wall_guid, opening_guid=guid, detail=f"{type(exc).__name__}: {exc}")
        check["passed"] = len(errors) == target_start
        row["opening_checks"].append(check)
    row["passed"] = len(errors) == start
    return row


def check_wall_closure(reference_path, damaged_path, manifest) -> dict:
    """Return JSON-safe geometric evidence; never write either input IFC.

    ``manifest`` is the private evaluation mutation manifest, not a Provider
    input. ``applicable=False`` means no wall opening was requested and must
    not be interpreted as evidence that doors/windows were filled.
    """
    paths = {"reference": Path(reference_path), "damaged": Path(damaged_path)}
    errors = []
    report = {"passed": False, "applicable": False, "walls": [], "errors": errors, "input_sha256": {}, "input_unchanged": False, "ifcopenshell_version": ifcopenshell.version, "mesh_tolerance_m": _MESH_TOLERANCE_M, "minimum_interior_probes": _MIN_PROBES, "scope": _SCOPE}
    try:
        report["input_sha256"] = {name: _sha256(path) for name, path in paths.items()}
        for key, name in (("source_sha256", "reference"), ("damaged_sha256", "damaged")):
            if manifest.get(key) is not None and manifest[key] != report["input_sha256"][name]:
                _error(errors, "INPUT_HASH_BINDING_MISMATCH", detail=key)
        groups = {}
        for target in manifest.get("deletions", []):
            opening_guid = target.get("opening_guid")
            if not opening_guid:
                if target.get("ifc_class") in {"IfcDoor", "IfcWindow"}:
                    report["applicable"] = True
                    _error(errors, "TARGET_OPENING_BINDING_MISSING")
                continue
            report["applicable"] = True
            wall_guid = target.get("host", {}).get("guid")
            preserve = target.get("preserve_opening", True)
            if not wall_guid or not isinstance(preserve, bool):
                _error(errors, "TARGET_WALL_OR_POLICY_BINDING_MISSING", opening_guid=opening_guid)
                continue
            if any(opening_guid in rows for rows in groups.values()):
                _error(errors, "DUPLICATE_OPENING_POLICY", opening_guid=opening_guid)
                continue
            groups.setdefault(wall_guid, {})[opening_guid] = {**target, "preserve_opening": preserve}
        if groups:
            reference = ifcopenshell.open(str(paths["reference"]))
            damaged = ifcopenshell.open(str(paths["damaged"]))
            expected = ifcopenshell.open(str(paths["reference"]))
            if reference.schema != damaged.schema:
                _error(errors, "INPUT_SCHEMA_MISMATCH")
            for wall_guid, targets in sorted(groups.items()):
                report["walls"].append(_check_wall(reference, damaged, expected, wall_guid, targets, errors))
    except Exception as exc:
        _error(errors, "WALL_CHECK_UNAVAILABLE", detail=f"{type(exc).__name__}: {exc}")
    finally:
        if report["input_sha256"]:
            try:
                report["input_unchanged"] = all(_sha256(path) == report["input_sha256"][name] for name, path in paths.items())
            except OSError:
                report["input_unchanged"] = False
            if not report["input_unchanged"]:
                _error(errors, "INPUT_BYTES_CHANGED_DURING_CHECK")
    report["passed"] = report["input_unchanged"] and not errors and all(wall["passed"] for wall in report["walls"])
    return report
