"""IFC2X3 solid authoring for the four frozen Generation filling templates."""
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import ifcopenshell.util.element
import ifcopenshell.util.unit
from ifcopenshell.api.geometry import assign_representation, add_shape_aspect
from ifcopenshell.api.pset import add_pset, edit_pset
from ifcopenshell.api.root import create_entity
from ifcopenshell.api.type import assign_type
from text2ifc_contract.basic_filling import resolve_basic_filling


def _box(file, x0, x1, y0, y1, z0, z1, scale):
    profile = file.create_entity("IfcRectangleProfileDef", ProfileType="AREA", Position=file.createIfcAxis2Placement2D(file.createIfcCartesianPoint((0., 0.)), None), XDim=(x1-x0)*scale, YDim=(y1-y0)*scale)
    position = file.createIfcAxis2Placement3D(file.createIfcCartesianPoint(((x0+x1)/2*scale, (y0+y1)/2*scale, z0*scale)), None, None)
    return file.createIfcExtrudedAreaSolid(profile, position, file.createIfcDirection((0., 0., 1.)), (z1-z0)*scale)


def add_basic_filling_geometry(ifc_file: Any, product: Any, representation: Mapping[str, Any], body_context: Any) -> None:
    resolved = resolve_basic_filling(representation, product.is_a())
    scale = .001 / ifcopenshell.util.unit.calculate_unit_scale(ifc_file)
    width, height = float(resolved["width"]), float(resolved["height"])
    p = resolved["parameters"]
    frame, depth, panel = (float(p[key]) for key in ("frame_width", "frame_depth", "panel_thickness"))
    left, right = -width/2, width/2
    door = product.is_a("IfcDoor")
    strips = [(left,left+frame,-depth/2,depth/2,0,height), (right-frame,right,-depth/2,depth/2,0,height), (left+frame,right-frame,-depth/2,depth/2,height-frame,height)]
    if not door:
        strips.append((left+frame,right-frame,-depth/2,depth/2,0,frame))
    clear = [(left+frame,right-frame)]
    if resolved["template_id"] == "window-double-vertical":
        middle = left + width * p["split_ratio"]
        strips.append((middle-frame/2,middle+frame/2,-depth/2,depth/2,frame,height-frame))
        clear = [(left+frame,middle-frame/2), (middle+frame/2,right-frame)]
    frame_items = [_box(ifc_file, *bounds, scale) for bounds in strips]
    panel_items = [_box(ifc_file, a,b,-panel/2,panel/2,0 if door else frame,height-frame,scale) for a,b in clear]
    shape = ifc_file.create_entity("IfcShapeRepresentation", ContextOfItems=body_context, RepresentationIdentifier="Body", RepresentationType="SweptSolid", Items=frame_items+panel_items)
    assign_representation(ifc_file, product=product, representation=shape)
    for role, items in (("Lining" if door else "Framing", frame_items), ("Panel" if door else "Glazing", panel_items)):
        add_shape_aspect(ifc_file, name=role, items=items, representation=shape, part_of_product=product.Representation)
    product.OverallWidth = width * scale
    product.OverallHeight = height * scale
    provenance = add_pset(ifc_file, product=product, name="Pset_text2IFCBasicFilling")
    edit_pset(ifc_file, pset=provenance, properties={"TemplateId": resolved["template_id"], "TemplateVersion": resolved["template_version"], "ParametersJson": json.dumps(p, sort_keys=True), "ParameterSourcesJson": json.dumps(resolved["parameter_sources"], sort_keys=True)})


def ensure_basic_filling_styles(ifc_file: Any, records: Mapping[str, Any], entities: Mapping[str, Any]) -> None:
    """Record handedness without changing or merging an explicitly requested Type."""
    for entity_id, record in records.items():
        rep = record.get("attributes", {}).get("Representation", {})
        if rep.get("kind") != "basic_filling" or record["ifc_class"] != "IfcDoor":
            continue
        product = entities[entity_id]
        operation = "SINGLE_SWING_LEFT" if rep["template_id"] == "door-left" else "SINGLE_SWING_RIGHT"
        existing = ifcopenshell.util.element.get_type(product)
        if existing is not None:
            if not existing.is_a("IfcDoorStyle") or existing.OperationType != operation:
                raise ValueError("Explicit DoorStyle conflicts with basic filling handedness.")
            continue
        style = create_entity(ifc_file, ifc_class="IfcDoorStyle", name=f"text2IFC construction attachment {entity_id}")
        style.OperationType = operation
        style.ConstructionType = "NOTDEFINED"
        style.ParameterTakesPrecedence = False
        style.Sizeable = True
        assign_type(ifc_file, related_objects=[product], relating_type=style, should_map_representations=False)


def verify_basic_filling(model: Any, document: Mapping[str, Any], *, verify_placement: bool = True) -> tuple:
    """Read actual reopened part meshes, not the authoring metadata's assertions."""
    import numpy as np
    import ifcopenshell.geom
    import ifcopenshell.util.placement
    from text2ifc_contract.placement import world_transform_for
    from .verification import IfcValidationIssue

    issues = []
    products = {}
    for product in model.by_type("IfcProduct"):
        identity = ifcopenshell.util.element.get_psets(product, should_inherit=False).get("Pset_text2IFCIdentity", {}).get("BimJsonId")
        products.setdefault(identity, []).append(product)
    settings = ifcopenshell.geom.settings()
    for record in document.get("entities", []):
        rep = record.get("attributes", {}).get("Representation", {})
        if rep.get("kind") != "basic_filling":
            continue
        def fail(message):
            issues.append(IfcValidationIssue("IFC_BASIC_FILLING_MISMATCH", record["id"], "Representation", message))
        matches = products.get(record["id"], [])
        if len(matches) != 1:
            fail("Missing or duplicate generated filling identity.")
            continue
        product = matches[0]
        resolved = resolve_basic_filling(rep, record["ifc_class"])
        p = resolved["parameters"]
        w, h, f, d, t = (float(n)/1000 for n in (rep["width"],rep["height"],p["frame_width"],p["frame_depth"],p["panel_thickness"]))
        door = record["ifc_class"] == "IfcDoor"
        unit_scale = ifcopenshell.util.unit.calculate_unit_scale(model)
        if product.OverallWidth is None or product.OverallHeight is None or not np.allclose([product.OverallWidth * unit_scale, product.OverallHeight * unit_scale], [w,h], atol=1e-8, rtol=0):
            fail("Reopened nominal dimensions differ from the frozen input.")
        if verify_placement and product.ObjectPlacement is None:
            fail("Reopened filling has no placement.")
        elif verify_placement:
            actual_placement = ifcopenshell.util.placement.get_local_placement(product.ObjectPlacement)
            expected_placement = np.array(world_transform_for(document, record["id"]), dtype=float)
            actual_placement[:3,3] *= unit_scale
            expected_placement[:3,3] *= .001
            if not np.allclose(actual_placement, expected_placement, atol=1e-8, rtol=0):
                fail("Reopened placement differs from the frozen input.")
        if door:
            style = ifcopenshell.util.element.get_type(product)
            operation = "SINGLE_SWING_LEFT" if rep["template_id"] == "door-left" else "SINGLE_SWING_RIGHT"
            if style is None or not style.is_a("IfcDoorStyle") or style.OperationType != operation:
                fail("Reopened DoorStyle hand differs from the frozen input.")
        # Expected occupied boxes are calculated here from frozen dimensions,
        # independently of the compiler's geometry entities and metadata.
        frame_boxes = [(-w/2,-w/2+f,-d/2,d/2,0,h), (w/2-f,w/2,-d/2,d/2,0,h), (-w/2+f,w/2-f,-d/2,d/2,h-f,h)]
        if not door:
            frame_boxes.append((-w/2+f,w/2-f,-d/2,d/2,0,f))
        intervals = [(-w/2+f,w/2-f)]
        if rep["template_id"] == "window-double-vertical":
            middle = -w/2+w*p["split_ratio"]
            frame_boxes.append((middle-f/2,middle+f/2,-d/2,d/2,f,h-f))
            intervals = [(-w/2+f,middle-f/2),(middle+f/2,w/2-f)]
        expected = {"Lining" if door else "Framing": frame_boxes, "Panel" if door else "Glazing": [(a,b,-t/2,t/2,0 if door else f,h-f) for a,b in intervals]}
        try:
            actual_roles = {}
            for aspect in product.Representation.HasShapeAspects:
                actual_roles.setdefault(aspect.Name, []).extend(item for shape in aspect.ShapeRepresentations for item in shape.Items)
            if set(actual_roles) != set(expected):
                fail("Missing or unexpected part roles.")
            body_items = [item.id() for shape in product.Representation.Representations if shape.RepresentationIdentifier == "Body" for item in shape.Items]
            aspect_items = [item.id() for items in actual_roles.values() for item in items]
            if sorted(body_items) != sorted(aspect_items):
                fail("Body items and part role membership differ.")
            for role, boxes in expected.items():
                actual_boxes = []
                for item in actual_roles.get(role, []):
                    shape = ifcopenshell.geom.create_shape(settings, item)
                    mesh = getattr(shape, "geometry", shape)
                    vertices = np.array(mesh.verts).reshape(-1,3)
                    faces = np.array(mesh.faces).reshape(-1,3)
                    lo, hi = vertices.min(axis=0), vertices.max(axis=0)
                    actual_boxes.append((lo[0],hi[0],lo[1],hi[1],lo[2],hi[2]))
                    triangles = vertices[faces]
                    volume = abs(np.einsum("ij,ij->i", triangles[:,0], np.cross(triangles[:,1], triangles[:,2])).sum()/6)
                    if not np.isclose(volume, np.prod(hi-lo), atol=1e-10, rtol=1e-7):
                        fail(f"{role} part is not a closed rectangular occupied volume.")
                if len(actual_boxes) != len(boxes) or not np.allclose(sorted(actual_boxes), sorted(boxes), atol=1e-7, rtol=0):
                    fail(f"{role} mesh dimensions, placement or clear aperture do not match the frozen parameters.")
            metadata = ifcopenshell.util.element.get_psets(product, should_inherit=False).get("Pset_text2IFCBasicFilling", {})
            if metadata.get("TemplateId") != rep["template_id"] or metadata.get("TemplateVersion") != rep["template_version"] or json.loads(metadata.get("ParametersJson", "null")) != p or json.loads(metadata.get("ParameterSourcesJson", "null")) != resolved["parameter_sources"]:
                fail("Template parameter provenance does not match the frozen input.")
        except (AttributeError, TypeError, ValueError, RuntimeError):
            fail("Filling part geometry or metadata could not be independently read.")
    return tuple(issues)
