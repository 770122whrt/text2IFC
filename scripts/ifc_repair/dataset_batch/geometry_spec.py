"""Complete supported extrusion specifications and surviving-instance references."""
from __future__ import annotations

import hashlib
import json

import ifcopenshell.util.placement
import numpy as np


PROFILES = {
    "IfcRectangleProfileDef": ("矩形截面", ("XDim", "YDim")),
    "IfcRectangleHollowProfileDef": ("矩形空心截面", ("XDim", "YDim", "WallThickness", "InnerFilletRadius", "OuterFilletRadius")),
    "IfcCircleProfileDef": ("圆形截面", ("Radius",)),
    "IfcCircleHollowProfileDef": ("圆形空心截面", ("Radius", "WallThickness")),
    "IfcEllipseProfileDef": ("椭圆截面", ("SemiAxis1", "SemiAxis2")),
    "IfcIShapeProfileDef": ("工字形截面", ("OverallWidth", "OverallDepth", "WebThickness", "FlangeThickness", "FilletRadius")),
    "IfcUShapeProfileDef": ("槽形截面", ("Depth", "FlangeWidth", "WebThickness", "FlangeThickness", "FilletRadius", "EdgeRadius", "FlangeSlope")),
    "IfcLShapeProfileDef": ("角形截面", ("Depth", "Width", "Thickness", "FilletRadius", "EdgeRadius", "LegSlope")),
    "IfcTShapeProfileDef": ("T形截面", ("Depth", "FlangeWidth", "WebThickness", "FlangeThickness", "FilletRadius", "FlangeEdgeRadius", "WebEdgeRadius", "WebSlope", "FlangeSlope")),
    "IfcCShapeProfileDef": ("C形截面", ("Depth", "Width", "WallThickness", "Girth", "InternalFilletRadius")),
    "IfcZShapeProfileDef": ("Z形截面", ("Depth", "FlangeWidth", "WebThickness", "FlangeThickness", "FilletRadius", "EdgeRadius")),
}


def mesh_fingerprint(shape):
    vertices = np.asarray(shape.geometry.verts, dtype=float).reshape(-1, 3)
    faces = np.asarray(shape.geometry.faces, dtype=np.int64)
    return hashlib.sha256(np.round(vertices, 10).astype("<f8").tobytes() + faces.astype("<i8").tobytes()).hexdigest()


def _placement(value, unit):
    matrix = np.array(ifcopenshell.util.placement.get_axis2placement(value), dtype=float) if value else np.eye(4)
    matrix[:3, 3] *= unit
    return matrix


def _profile(profile, unit):
    kind = profile.is_a()
    if profile.ProfileType != "AREA":
        raise ValueError("NON_AREA_PROFILE")
    if kind in PROFILES:
        label, fields = PROFILES[kind]
        dimensions, angles = {}, {}
        for name in fields:
            value = getattr(profile, name, None)
            if value is not None:
                (angles if name.endswith("Slope") else dimensions)[name] = float(value) * (1 if name.endswith("Slope") else unit)
        return {"kind": kind, "label": label, "dimensions_m": dimensions, "angles_radians": angles, "frame_m": _placement(profile.Position, unit).tolist()}
    if kind in {"IfcArbitraryClosedProfileDef", "IfcArbitraryProfileDefWithVoids"}:
        curves = [profile.OuterCurve, *getattr(profile, "InnerCurves", ())]
        if any(not curve.is_a("IfcPolyline") for curve in curves):
            raise ValueError("NON_POLYLINE_PROFILE")
        polygons = [[[float(v) * unit for v in point.Coordinates] for point in curve.Points] for curve in curves]
        if any(polygon[0] != polygon[-1] for polygon in polygons):
            raise ValueError("OPEN_POLYGON_PROFILE")
        return {"kind": kind, "label": "闭合多边形截面", "polygons_m": polygons, "frame_m": np.eye(4).tolist()}
    raise ValueError("UNSUPPORTED_PROFILE:" + kind)


def body_spec(product, unit):
    """Return all Body items or None; never describe an arbitrary body as a box."""
    components = []
    if getattr(product, "HasOpenings", ()):
        return None

    def walk(item, transform):
        if item.is_a("IfcMappedItem"):
            if not np.allclose(_placement(item.MappingSource.MappingOrigin, unit), np.eye(4), atol=1e-10):
                raise ValueError("NONTRIVIAL_MAPPING_ORIGIN")
            mapping = ifcopenshell.util.placement.get_mappeditem_transformation(item)
            if mapping is None:
                raise ValueError("UNSUPPORTED_MAPPING")
            mapping = np.asarray(mapping, dtype=float)
            mapping[:3, 3] *= unit
            # A scaled mapping cannot be represented by an orthonormal frame.
            if np.linalg.det(mapping[:3, :3]) <= 0 or not np.allclose(mapping[:3, :3].T @ mapping[:3, :3], np.eye(3), atol=1e-10):
                raise ValueError("SCALED_MAPPING")
            for child in item.MappingSource.MappedRepresentation.Items:
                walk(child, transform @ mapping)
        elif item.is_a("IfcExtrudedAreaSolid"):
            frame = transform @ _placement(item.Position, unit)
            direction = np.array(item.ExtrudedDirection.DirectionRatios, dtype=float)
            direction /= np.linalg.norm(direction)
            components.append({"profile": _profile(item.SweptArea, unit), "frame_product_m": frame.tolist(), "extrusion_direction": direction.tolist(), "depth_m": float(item.Depth) * unit})
        else:
            raise ValueError("UNSUPPORTED_BODY_ITEM:" + item.is_a())

    try:
        bodies = [rep for rep in product.Representation.Representations if rep.RepresentationIdentifier == "Body"]
        if not bodies:
            return None
        for rep in bodies:
            for item in rep.Items:
                walk(item, np.eye(4))
        return {"method": "complete_extrusions", "components": components} if components else None
    except (ValueError, AttributeError, TypeError):
        return None


def describe_body(spec, xyz):
    def number(value):
        return f"{value:.6f}".rstrip("0").rstrip(".")

    if spec.get("method") == "surviving_instance":
        peer = spec["peer"]
        axes = peer["axes_world"]
        return f"几何形状逐项复制模型中仍存在的{peer['ifc_class']}「{peer['name']}」，参考实例的世界基点为{xyz(peer['origin_world_m'])}米，世界X/Y/Z轴分别为{xyz(axes[0])}、{xyz(axes[1])}、{xyz(axes[2])}；复制其自身局部几何，再按本条指定原点和轴放置。"
    rows = []
    for index, part in enumerate(spec["components"], 1):
        profile = part["profile"]
        fields = []
        for key, value in profile.get("dimensions_m", {}).items():
            fields.append(("半径" if key == "Radius" else key + "=") + number(value * 1000) + "毫米")
        fields.extend(key + "=" + number(value) + "弧度" for key, value in profile.get("angles_radians", {}).items())
        if "polygons_m" in profile:
            fields.append("外轮廓及内孔依次为" + json.dumps([[[v * 1000 for v in point] for point in polygon] for polygon in profile["polygons_m"]], ensure_ascii=False) + "毫米；各轮廓按给定顺序闭合")
        frame = np.asarray(part["frame_product_m"])
        pframe = np.asarray(profile["frame_m"])
        rows.append(f"几何实体{index}采用{profile['label']}（{profile['kind']}），" + "，".join(fields) + f"。实体坐标原点在构件自身坐标中为{xyz(frame[:3, 3] * 1000)}毫米，X/Y/Z轴分别为{xyz(frame[:3, 0])}、{xyz(frame[:3, 1])}、{xyz(frame[:3, 2])}；截面原点在实体坐标中为{xyz(pframe[:3, 3] * 1000)}毫米，X/Y轴分别为{xyz(pframe[:3, 0])}、{xyz(pframe[:3, 1])}；沿实体坐标方向{xyz(part['extrusion_direction'])}拉伸{number(part['depth_m'] * 1000)}毫米。")
    return "".join(rows)
