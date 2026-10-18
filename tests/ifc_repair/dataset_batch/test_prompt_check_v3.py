from __future__ import annotations

import json
import math

import ifcopenshell
import ifcopenshell.guid
import ifcopenshell.util.unit
import numpy as np
import pytest
from ifcopenshell.api.root.remove_product import remove_product

from scripts.ifc_repair.dataset_batch.prompt_check_v3 import audit_prompt, parse_public_request


HEADER = "请按以下要求修复模型。世界坐标用米，尺寸和相对距离用毫米；公开数值最多三位小数。"
NAME_HEADER = "请按以下要求修复模型。尺寸和相对距离用毫米；公开数值最多三位小数。"
FOOTER = "除以上补建、洞口关系及指定实例属性外，其余构件、楼层、尺寸、位置、类型和材料保持原样。"
WORLD_HOST = "宿主墙未扣洞口的整体范围为（9.85，20，3）至（10，28，6）米。"
NAME_HOST = "宿主墙「Host wall」，长度正向大致朝北，厚度正向大致朝西。"
COPY_OPENING = "洞口复制参照构件所填洞口，保持与新构件相同的相对位置和朝向；在宿主墙上建立洞口并建立门窗填充关系。"


def request(*rows):
    header = NAME_HEADER if any("宿主墙「" in row for row in rows) else HEADER
    return "\n".join((header, *rows, FOOTER)) + "\n"


def peer_row(kind="门", mode="world", *, preserve=False):
    cls, noun, name, xyz = {
        "门": ("IfcDoor", "扇", "IfcDoor-2", "10，21，3"),
        "窗": ("IfcWindow", "扇", "IfcWindow-4", "10，25，4"),
        "梁": ("IfcBeam", "根", "IfcBeam-6", "8，20，5.7"),
        "柱": ("IfcColumn", "根", "IfcColumn-8", "8，20，3"),
    }[kind]
    peer_xyz = {"门": "10，23，3", "窗": "10，26.5，4", "梁": "6，20，5.7", "柱": "8，24，3"}[kind]
    row = f"1. 补建一{noun}{kind}：归属楼层「Level A」。"
    if kind in {"门", "窗"}:
        row += WORLD_HOST if mode == "world" else NAME_HOST
    if mode == "world":
        row += f"放置基点世界坐标为（{xyz}）米。完整形状复制参照：现存{cls}世界基点（{peer_xyz}）米。"
    else:
        distance, height = (1000, 0) if kind == "门" else (5000, 1000)
        row += f"放置基点距墙长度起端{distance}毫米，距墙厚度负向侧0毫米，高出墙底{height}毫米。完整形状复制参照：楼层「Level A」的现存{cls}「{name}」。"
    row += "朝向与参照相同。"
    if kind in {"门", "窗"}:
        if preserve:
            locator = f"世界基点（{xyz}）米" if mode == "world" else "距墙长度起端1000毫米，距墙厚度负向侧0毫米，高出墙底0毫米"
            row += f"保留现有洞口：{locator}；将新构件填入并建立门窗填充关系。"
        else:
            row += COPY_OPENING
    return row


def make_case(scene_factory, tmp_path, kind="门", *, preserve=False, configure=None, millimetres=True):
    path = scene_factory(tmp_path / "source.ifc", rotated=True, millimetres=millimetres, shared_property=False)
    reference = ifcopenshell.open(str(path))
    if configure:
        configure(reference)
    target = reference.by_type({"门": "IfcDoor", "窗": "IfcWindow", "梁": "IfcBeam", "柱": "IfcColumn"}[kind])[0]
    damaged = ifcopenshell.file.from_string(reference.to_string())
    row = {"guid": target.GlobalId, "ifc_class": target.is_a(), "storey": {"guid": reference.by_type("IfcBuildingStorey")[0].GlobalId}}
    if kind in {"门", "窗"}:
        opening = target.FillsVoids[0].RelatingOpeningElement
        row.update(opening_guid=opening.GlobalId, preserve_opening=preserve)
        if not preserve:
            remove_product(damaged, product=damaged.by_guid(opening.GlobalId))
    remove_product(damaged, product=damaged.by_guid(target.GlobalId))
    return reference, damaged, {"deletions": [row], "property_changes": []}


def assert_failure(case, mode, text, fragment):
    report = audit_prompt(*case, mode, text)
    assert not report["passed"], report
    assert any(fragment in error for error in report["errors"]), report
    json.dumps(report, allow_nan=False)


@pytest.mark.parametrize("kind,mode", [(kind, "world") for kind in ("门", "窗", "梁", "柱")] + [("门", "host_wall"), ("窗", "host_wall")])
@pytest.mark.parametrize("millimetres", [False, True])
def test_peer_shape_and_opening_requests_resolve_publicly(scene_factory, tmp_path, kind, mode, millimetres):
    case = make_case(scene_factory, tmp_path, kind, millimetres=millimetres)
    text = request(peer_row(kind, mode))
    public = parse_public_request(case[1], mode, text)
    assert public["passed"], public["errors"]
    report = audit_prompt(*case, mode, text)
    assert report["passed"], report
    assert report["checker_version"] == "text2ifc/dataset-prompt-check/1.2"
    assert report["request_profile"] == "text2ifc/dataset-request/1.3"
    assert report["checks"]["target_meshes"] == 1
    assert report["checks"]["openings"] == int(kind in {"门", "窗"})
    json.dumps(report, allow_nan=False)


@pytest.mark.parametrize("mode", ["world", "host_wall"])
def test_retained_opening_resolves_actual_void_and_identity(scene_factory, tmp_path, mode):
    case = make_case(scene_factory, tmp_path, preserve=True)
    text = request(peer_row(mode=mode, preserve=True))
    assert audit_prompt(*case, mode, text)["passed"]
    opening = case[1].by_guid(case[2]["deletions"][0]["opening_guid"])
    remove_product(case[1], product=opening)
    assert_failure(case, mode, text, "retained_opening_not_unique_or_absent")


@pytest.mark.parametrize("corruption,fragment", [
    ("coordinate", "placement_or_axes_mismatch"),
    ("peer_absent", "public_peer_not_unique_or_absent"),
    ("shape_missing", "complete_geometry_not_described"),
    ("void_missing", "void_relationship_missing"),
    ("fill_missing", "fill_relationship_missing"),
    ("mixed", "mixed_locator_modes"),
    ("four_decimals", "numeric_precision_exceeded"),
    ("polygon", "unsupported_geometry_description"),
    ("step", "step_identity_leak"),
])
def test_invalid_actual_text_is_rejected(scene_factory, tmp_path, corruption, fragment):
    case = make_case(scene_factory, tmp_path)
    text = request(peer_row())
    if corruption == "coordinate":
        text = text.replace("放置基点世界坐标为（10，21，3）", "放置基点世界坐标为（10，21.002，3）")
    elif corruption == "peer_absent":
        text = text.replace("现存IfcDoor世界基点（10，23，3）", "现存IfcDoor世界基点（10，29，3）")
    elif corruption == "shape_missing":
        text = text.replace("完整形状复制参照：现存IfcDoor世界基点（10，23，3）米。", "")
    elif corruption == "void_missing":
        text = text.replace("在宿主墙上建立洞口并", "")
    elif corruption == "fill_missing":
        text = text.replace("并建立门窗填充关系", "")
    elif corruption == "mixed":
        text = text.replace(WORLD_HOST, NAME_HOST)
    elif corruption == "four_decimals":
        text = text.replace("（10，21，3）", "（10，21.0001，3）", 1)
    elif corruption == "polygon":
        text = text.replace("朝向与参照相同。", "朝向与参照相同。几何实体1采用闭合多边形。")
    else:
        text = text.replace("朝向与参照相同。", "朝向与参照相同。STEP #123。")
    assert_failure(case, "world", text, fragment)


@pytest.mark.parametrize("mode", ["world", "host_wall"])
def test_ambiguous_public_peer_never_uses_private_identity(scene_factory, tmp_path, mode):
    case = make_case(scene_factory, tmp_path)
    damaged = case[1]
    peer = damaged.by_type("IfcDoor")[0]
    duplicate = damaged.create_entity("IfcDoor", GlobalId=ifcopenshell.guid.new(), OwnerHistory=peer.OwnerHistory, Name=peer.Name, ObjectPlacement=peer.ObjectPlacement, Representation=peer.Representation)
    containment = peer.ContainedInStructure[0]
    containment.RelatedElements = (*containment.RelatedElements, duplicate)
    assert_failure(case, mode, request(peer_row(mode=mode)), "public_peer_not_unique_or_absent")


def test_world_rounding_cell_ambiguity_and_bad_peer_coordinate(scene_factory, tmp_path):
    case = make_case(scene_factory, tmp_path)
    peer = case[1].by_type("IfcDoor")[0]
    duplicate = case[1].create_entity("IfcDoor", GlobalId=ifcopenshell.guid.new(), OwnerHistory=peer.OwnerHistory, Name="Other", ObjectPlacement=peer.ObjectPlacement, Representation=peer.Representation)
    # Public resolution cannot recover uniqueness from unprinted extra digits.
    containment = peer.ContainedInStructure[0]
    containment.RelatedElements = (*containment.RelatedElements, duplicate)
    assert_failure(case, "world", request(peer_row()), "public_peer_not_unique_or_absent")
    remove_product(case[1], product=duplicate)
    text = request(peer_row()).replace("世界基点（10，23，3）", "世界基点（10，23.001，3）")
    assert_failure(case, "world", text, "public_peer_not_unique_or_absent")


def test_failed_public_parse_does_not_read_reference_or_manifest(scene_factory, tmp_path):
    case = make_case(scene_factory, tmp_path)
    class PrivateSentinel:
        def __getattr__(self, name):
            pytest.fail(f"private phase reached after public failure: {name}")
    report = audit_prompt(PrivateSentinel(), case[1], PrivateSentinel(), "world", request(peer_row()).replace("现存IfcDoor世界基点（10，23，3）", "现存IfcDoor世界基点（99，99，99）"))
    assert not report["passed"]
    assert not report["private_comparison_performed"]


@pytest.mark.parametrize("mode", ["world", "host_wall"])
def test_wrong_wall_bounds_or_named_direction_is_rejected(scene_factory, tmp_path, mode):
    case = make_case(scene_factory, tmp_path)
    row = peer_row(mode=mode)
    row = row.replace("（10，28，6）", "（10，28.002，6）") if mode == "world" else row.replace("大致朝北", "大致朝南")
    assert_failure(case, mode, request(row), "wall_not_unique_or_absent" if mode == "world" else "wall_direction_mismatch")


def _nonmatching_beam_peer(model):
    unit = ifcopenshell.util.unit.calculate_unit_scale(model)
    solid = model.by_type("IfcBeam")[1].Representation.Representations[0].Items[0]
    solid.SweptArea.XDim = 5 / unit
    solid.SweptArea.Position.Location.Coordinates = (2.5 / unit, 0.1 / unit)


BASIC_BEAM = '1. 补建一根梁：归属楼层「Level A」。放置基点世界坐标为（8，20，5.7）米。形状为单一长方体，沿自身三个轴方向的尺寸为（4000，200，300）毫米；基点距对应负向面的距离为（0，0，0）毫米。朝向相对项目坐标系，按高、厚、宽轴依次旋转90度、0度、0度。'


def test_basic_box_requires_actual_box_and_no_available_peer(scene_factory, tmp_path):
    case = make_case(scene_factory, tmp_path, "梁", configure=_nonmatching_beam_peer)
    report = audit_prompt(*case, "world", request(BASIC_BEAM))
    assert report["passed"], report
    assert_failure(case, "world", request(BASIC_BEAM.replace("（4000，200，300）", "（4000，210，300）")), "target_geometry_mismatch")
    other = tmp_path / "other"
    other.mkdir()
    with_peer = make_case(scene_factory, other, "梁")
    assert_failure(with_peer, "world", request(BASIC_BEAM), "basic_shape_surviving_peer_available")


@pytest.mark.parametrize("delta,passed", [("90.000", True), ("90.001", False)])
def test_angle_rounding_tolerance_is_explicit(scene_factory, tmp_path, delta, passed):
    case = make_case(scene_factory, tmp_path, "梁", configure=_nonmatching_beam_peer)
    report = audit_prompt(*case, "world", request(BASIC_BEAM.replace("旋转90度", f"旋转{delta}度")))
    assert report["passed"] is passed, report
    assert report["numeric_tolerances"]["angle_component_deg"] == 0.0005


@pytest.mark.parametrize("mode", ["world", "host_wall"])
def test_property_target_path_type_and_untruncated_string(scene_factory, tmp_path, mode):
    path = scene_factory(tmp_path / "properties.ifc", rotated=True, millimetres=True, shared_property=False)
    reference = ifcopenshell.open(str(path))
    target = reference.by_type("IfcDoor")[0]
    prop = target.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[0]
    prop.NominalValue = reference.createIfcLabel("R-1.23456789")
    damaged = ifcopenshell.file.from_string(reference.to_string())
    damaged.by_guid(target.GlobalId).IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[0].NominalValue = damaged.createIfcLabel("damaged")
    change = {"guid": target.GlobalId, "pset_name": "Pset_DoorCommon", "property_name": "IsExternal", "value_type": "IfcLabel", "before": "R-1.23456789", "after": "damaged"}
    case = (reference, damaged, {"deletions": [], "property_changes": [change]})
    host = WORLD_HOST if mode == "world" else NAME_HOST
    position = "放置基点世界坐标为（10，21，3）米。" if mode == "world" else "放置基点距墙长度起端1000毫米，距墙厚度负向侧0毫米，高出墙底0毫米。"
    row = f'属性更改1：现有IfcDoor，归属楼层「Level A」。{host}{position}将实例属性「Pset_DoorCommon.IsExternal」改为"R-1.23456789"，保留其原属性类型。'
    report = audit_prompt(*case, mode, request(row))
    assert report["passed"], report
    assert_failure(case, mode, request(row.replace("R-1.23456789", "R-1.234")), "property_restoration_value_mismatch")
    damaged.by_guid(target.GlobalId).IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[0].NominalValue = damaged.createIfcIdentifier("damaged")
    assert_failure(case, mode, request(row), "property_type_mismatch")


def test_actual_renderer_output_is_checked_without_regenerating_it(scene_factory, tmp_path, monkeypatch):
    from scripts.ifc_repair.dataset_batch import prompts_v3
    case = make_case(scene_factory, tmp_path)
    inventory = prompts_v3.prepare_inventory(tmp_path / "source.ifc")
    target = next(row for row in inventory["targets"]["door"] if row["guid"] == case[2]["deletions"][0]["guid"])
    recipe = {"deletions": [{**target, "preserve_opening": False}], "property_changes": []}
    rendered = prompts_v3.render_prompts(prompts_v3.prepare_recipe(recipe))
    monkeypatch.setattr(prompts_v3, "render_prompts", lambda *_: pytest.fail("checker regenerated public text"))
    monkeypatch.setattr(prompts_v3, "prepare_recipe", lambda *_: pytest.fail("checker used private shape recipe"))
    for mode, text in rendered.items():
        assert text is not None
        report = audit_prompt(*case, mode, text)
        assert report["passed"], report


def test_name_rounding_is_checked_in_the_wall_axes(scene_factory, tmp_path):
    def configure(model):
        unit = ifcopenshell.util.unit.calculate_unit_scale(model)
        model.by_type("IfcBuildingStorey")[0].ObjectPlacement.RelativePlacement.RefDirection.DirectionRatios = (math.cos(math.pi / 6), math.sin(math.pi / 6), 0.0)
        door = model.by_type("IfcDoor")[0]
        for entity in (door, door.FillsVoids[0].RelatingOpeningElement):
            point = entity.ObjectPlacement.RelativePlacement.Location
            point.Coordinates = tuple(value + delta / unit for value, delta in zip(point.Coordinates, (0.0000004, 0.0000004, 0)))
    case = make_case(scene_factory, tmp_path, configure=configure)
    row = peer_row(mode="host_wall").replace(NAME_HOST, "宿主墙「Host wall」，长度正向大致朝东北，厚度正向大致朝西北。")
    report = audit_prompt(*case, "host_wall", request(row))
    assert report["passed"], report


def test_box_certificate_rejects_extra_geometry_with_the_same_bbox(scene_factory, tmp_path):
    def configure(model):
        _nonmatching_beam_peer(model)
        body = model.by_type("IfcBeam")[0].Representation.Representations[0]
        body.Items = (*body.Items, body.Items[0])
    case = make_case(scene_factory, tmp_path, "梁", configure=configure)
    assert_failure(case, "world", request(BASIC_BEAM), "target_geometry_mismatch")


@pytest.mark.parametrize("scale,passed", [(1.0, True), (2.0, False)])
def test_basic_box_mapping_accepts_only_a_single_rigid_path(scene_factory, tmp_path, scale, passed):
    def configure(model):
        _nonmatching_beam_peer(model)
        body = model.by_type("IfcBeam")[0].Representation.Representations[0]
        point = model.createIfcCartesianPoint((0.0, 0.0, 0.0))
        origin = model.createIfcAxis2Placement3D(point, None, None)
        source_body = model.createIfcShapeRepresentation(body.ContextOfItems, "Body", "SweptSolid", list(body.Items))
        source = model.createIfcRepresentationMap(origin, source_body)
        transform = model.createIfcCartesianTransformationOperator3D(None, None, point, scale, None)
        body.Items = [model.createIfcMappedItem(source, transform)]
        body.RepresentationType = "MappedRepresentation"
    case = make_case(scene_factory, tmp_path, "梁", configure=configure)
    row = BASIC_BEAM if scale == 1 else BASIC_BEAM.replace("（4000，200，300）", "（8000，400，600）")
    report = audit_prompt(*case, "world", request(row))
    assert report["passed"] is passed, report


def test_relative_peer_angles_and_opening_placement_are_verified(scene_factory, tmp_path):
    yaw, pitch, roll = np.radians([10, 20, 30])
    rz = np.array([[math.cos(yaw), -math.sin(yaw), 0], [math.sin(yaw), math.cos(yaw), 0], [0, 0, 1]])
    ry = np.array([[math.cos(pitch), 0, math.sin(pitch)], [0, 1, 0], [-math.sin(pitch), 0, math.cos(pitch)]])
    rx = np.array([[1, 0, 0], [0, math.cos(roll), -math.sin(roll)], [0, math.sin(roll), math.cos(roll)]])
    rotation = rz @ ry @ rx
    def configure(model):
        door = model.by_type("IfcDoor")[0]
        for entity in (door, door.FillsVoids[0].RelatingOpeningElement):
            axis = entity.ObjectPlacement.RelativePlacement
            axis.Axis.DirectionRatios = tuple(float(value) for value in rotation[:, 2])
            axis.RefDirection.DirectionRatios = tuple(float(value) for value in rotation[:, 0])
    case = make_case(scene_factory, tmp_path, configure=configure)
    row = peer_row().replace("朝向与参照相同。", "朝向相对参照，按自身高、厚、宽轴依次旋转10度、20度、30度。")
    assert audit_prompt(*case, "world", request(row))["passed"]
    assert_failure(case, "world", request(row.replace("旋转10度", "旋转10.001度")), "placement_or_axes_mismatch")


def test_complex_peer_without_installation_anchor_is_rejected_even_with_the_same_bbox(scene_factory, tmp_path):
    case = make_case(scene_factory, tmp_path)
    body = case[1].by_type("IfcDoor")[0].Representation.Representations[0]
    body.Items = (*body.Items, body.Items[0])
    assert_failure(case, "world", request(peer_row()), "public_reference_not_authorable")


@pytest.mark.parametrize("kind", ["门", "窗"])
def test_unmapped_peer_mesh_alone_does_not_establish_installation_authorability(scene_factory, tmp_path, kind):
    def configure(model):
        cls = "IfcDoor" if kind == "门" else "IfcWindow"
        unit = ifcopenshell.util.unit.calculate_unit_scale(model)
        for entity in model.by_type(cls):
            shape = ifcopenshell.geom.create_shape(ifcopenshell.geom.settings(), entity)
            vertices = np.asarray(shape.geometry.verts).reshape(-1, 3) / unit
            triangles = np.asarray(shape.geometry.faces).reshape(-1, 3)
            points = [model.createIfcCartesianPoint(tuple(float(value) for value in vertex)) for vertex in vertices]
            faces = [model.createIfcFace([model.createIfcFaceOuterBound(model.createIfcPolyLoop([points[int(index)] for index in triangle]), True)]) for triangle in triangles]
            body = entity.Representation.Representations[0]
            body.Items = [model.createIfcFacetedBrep(model.createIfcClosedShell(faces))]
            body.RepresentationType = "Brep"
    case = make_case(scene_factory, tmp_path, kind, configure=configure)
    report = audit_prompt(*case, "world", request(peer_row(kind)))
    assert not report["passed"], report
    assert any("public_reference_not_authorable" in error for error in report["errors"]), report
    assert report["reference_authorability"]["failed"] == 1
    assert not report["private_comparison_performed"]


@pytest.mark.parametrize("mode", ["world", "host_wall"])
def test_independent_basic_opening_has_its_own_placement_shape_and_axes(scene_factory, tmp_path, mode):
    def configure(model):
        unit = ifcopenshell.util.unit.calculate_unit_scale(model)
        peer_opening = model.by_type("IfcDoor")[1].FillsVoids[0].RelatingOpeningElement
        rectangle = peer_opening.Representation.Representations[0].Items[0].SweptArea
        rectangle.XDim = 1.2 / unit
        rectangle.Position.Location.Coordinates = (0.6 / unit, 0.075 / unit)
    case = make_case(scene_factory, tmp_path, configure=configure)
    position = "洞口放置基点世界坐标为（10，21，3）米。" if mode == "world" else "洞口放置基点距墙长度起端1000毫米，距墙厚度负向侧0毫米，高出墙底0毫米。"
    basis, yaw = ("项目坐标系", 90) if mode == "world" else ("宿主墙", 0)
    opening = f"洞口规格：{position}洞口形状为单一长方体，沿自身三个轴方向的尺寸为（900，150，2100）毫米；基点距对应负向面的距离为（0，0，0）毫米。洞口朝向相对{basis}，按高、厚、宽轴依次旋转{yaw}度、0度、0度。在宿主墙上建立洞口并建立门窗填充关系。"
    row = peer_row(mode=mode).replace(COPY_OPENING, opening)
    report = audit_prompt(*case, mode, request(row))
    assert report["passed"], report
    bad = row.replace("（900，150，2100）", "（900，160，2100）")
    assert_failure(case, mode, request(bad), "opening_geometry_mismatch")
    other = tmp_path / "matching"
    other.mkdir()
    matching_case = make_case(scene_factory, other)
    assert_failure(matching_case, mode, request(row), "basic_opening_copy_available")


def test_float_property_value_obeys_public_precision_without_rounding_private_facts(scene_factory, tmp_path):
    path = scene_factory(tmp_path / "numeric-property.ifc", rotated=True, shared_property=False)
    reference = ifcopenshell.open(str(path))
    target = reference.by_type("IfcDoor")[0]
    target.IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[0].NominalValue = reference.createIfcReal(1.23456789)
    damaged = ifcopenshell.file.from_string(reference.to_string())
    damaged.by_guid(target.GlobalId).IsDefinedBy[0].RelatingPropertyDefinition.HasProperties[0].NominalValue = damaged.createIfcReal(9.87)
    change = {"guid": target.GlobalId, "pset_name": "Pset_DoorCommon", "property_name": "IsExternal", "value_type": "IfcReal", "before": 1.23456789, "after": 9.87}
    case = (reference, damaged, {"deletions": [], "property_changes": [change]})
    row = f'属性更改1：现有IfcDoor，归属楼层「Level A」。{WORLD_HOST}放置基点世界坐标为（10，21，3）米。将实例属性「Pset_DoorCommon.IsExternal」改为1.235，保留其原属性类型。'
    assert audit_prompt(*case, "world", request(row))["passed"]
    assert_failure(case, "world", request(row.replace("改为1.235", "改为1.236")), "property_restoration_value_mismatch")
    assert_failure(case, "world", request(row.replace("改为1.235", "改为1.2345")), "numeric_precision_exceeded")
