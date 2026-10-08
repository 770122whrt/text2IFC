"""Independently compare candidate source meshes with their repair rectangles.

Axis/Body disagreement, extra nonrectangular parts and cutbacks cannot be
accepted solely because the production index found one rectangular extrusion.
Source IFCs remain read-only. Reports are private preparation evidence.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

REPO = Path(__file__).absolute().parents[2]
sys.path[:0] = [str(REPO), str(REPO / "src")]

import ifcopenshell
import ifcopenshell.geom
import numpy as np


def mesh_agreement(entity, member: dict, scale: float) -> dict:
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    shape = ifcopenshell.geom.create_shape(settings, entity)
    vertices = np.array(shape.geometry.verts, dtype=float).reshape(-1, 3) * 1000.0
    faces = np.array(shape.geometry.faces, dtype=int).reshape(-1, 3)
    matrix = np.array(member["storey_world_matrix_project_units"], dtype=float)
    storey_mm = (vertices - matrix[:3, 3] * scale) @ matrix[:3, :3]
    frame = member["frame"]
    start = np.array(frame["axis_start_mm"])
    axis = np.array(frame["axis_direction"])
    section = frame["section"]
    if member["family"] == "beam":
        width_direction, other_direction = frame["profile_x_direction"], frame["profile_y_direction"]
        width, other = section["width_mm"], section["height_mm"]
    else:
        width_direction, other_direction = frame["profile_x_direction"], frame["profile_y_direction"]
        width, other = section["width_mm"], section["depth_mm"]
    basis = np.array([axis, width_direction, other_direction], dtype=float)
    local = (storey_mm - start) @ basis.T
    length = float(frame["axis_extent_mm"])
    expected_bounds = np.array([[0.0, length], [-width / 2, width / 2], [-other / 2, other / 2]])
    actual_bounds = np.array([[local[:, i].min(), local[:, i].max()] for i in range(3)])
    bounds_error = float(np.max(np.abs(actual_bounds - expected_bounds)))
    all_plane_errors = np.stack([np.abs(local[:, i]-expected_bounds[i, j]) for i in range(3) for j in range(2)], axis=1)
    surface_error = float(all_plane_errors.min(axis=1).max())
    triangle = local[faces]
    actual_volume = abs(float(np.einsum("ij,ij->i", triangle[:, 0], np.cross(triangle[:, 1], triangle[:, 2])).sum() / 6.0))
    expected_volume = length * width * other
    volume_relative_error = abs(actual_volume - expected_volume) / expected_volume
    passed = bounds_error <= 0.05 and surface_error <= 0.05 and volume_relative_error <= 0.00001
    return {"rectangular_mesh_matches_authored_axis_section": passed,
            "bounds_max_error_mm": bounds_error, "vertices_surface_max_error_mm": surface_error,
            "actual_volume_mm3": actual_volume, "expected_volume_mm3": expected_volume,
            "volume_relative_error": volume_relative_error, "vertices": len(vertices), "triangles": len(faces),
            "actual_bounds_in_request_frame_mm": actual_bounds.tolist(), "expected_bounds_in_request_frame_mm": expected_bounds.tolist(),
            "tolerances": {"bounds_mm": 0.05, "surface_mm": 0.05, "relative_volume": 0.00001},
            "volume_is_supporting_check_only": True, "independent_of_provider": True}


def main() -> int:
    report = json.loads((REPO / ".tmp/repair-comparison-formal-expansion/next_ten_source_audit.json").read_text(encoding="utf-8"))
    rows = []
    settings = ifcopenshell.geom.settings()
    for candidate in report["rows"]:
        if candidate["status"] != "eligible":
            continue
        path = REPO / candidate["source_path"]
        before = hashlib.sha256(path.read_bytes()).hexdigest()
        model = ifcopenshell.open(path)
        result = {k: candidate[k] for k in ("asset_id", "source_path", "license", "source_id", "counts", "actual_sha256", "registry_line")}
        result["members"] = {}
        for family, eligibility in candidate["eligibility"].items():
            checks = []
            for member in eligibility["eligible"]:
                try:
                    check = mesh_agreement(model.by_guid(member["global_id"]), member, candidate["project_unit_to_mm"])
                except Exception as error:
                    check = {"rectangular_mesh_matches_authored_axis_section": False, "error": f"{type(error).__name__}: {error}"}
                checks.append({"global_id": member["global_id"], "name": member["name"], "storey_name": member["storey_name"],
                               "axis_world_m": member["axis_world_m"], "parameters_storey_local_mm": member["parameters_storey_local_mm"], **check})
            result["members"][family] = checks
        result["source_unchanged"] = hashlib.sha256(path.read_bytes()).hexdigest() == before
        rows.append(result)
        print(json.dumps({"asset_id": result["asset_id"], "mesh_verified": {k: sum(m["rectangular_mesh_matches_authored_axis_section"] for m in v)
                           for k, v in result["members"].items()}}, ensure_ascii=True), flush=True)
    output = {"schema_version": "next-ten-structural-mesh-screen/0.1", "timestamp": datetime.now(timezone.utc).isoformat(),
              "input": ".tmp/repair-comparison-formal-expansion/next_ten_source_audit.json", "rows": rows,
              "sources_unchanged": all(r["source_unchanged"] for r in rows), "model_calls": 0,
              "evidence_class": "independent_actual_source_mesh_preparation", "native_schema_express_rerun": False}
    target = REPO / ".tmp/repair-comparison-formal-expansion/next_ten_mesh_audit.json"
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"output": str(target), "models": len(rows), "source_unchanged": output["sources_unchanged"]}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
