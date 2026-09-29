"""Development package boundaries, using real IFC files and no Provider."""

from __future__ import annotations

import copy
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys

import ifcopenshell
import pytest


ROOT = Path(__file__).resolve().parents[3]


def package_api():
    path = ROOT / "scripts/ifc_repair/repair_comparison/prepare.py"
    assert path.is_file(), "Development package preparation entry point is missing"
    return importlib.import_module("scripts.ifc_repair.repair_comparison.prepare")


@pytest.fixture
def sample(tmp_path):
    """Small schema-valid IFC2X3 fixture with real extruded geometry."""
    model = ifcopenshell.file(schema="IFC2X3")
    wall = model.create_entity("IfcWall", GlobalId=ifcopenshell.guid.new(), Name="wall")
    opening = model.create_entity("IfcOpeningElement", GlobalId=ifcopenshell.guid.new())
    door = model.create_entity("IfcDoor", GlobalId=ifcopenshell.guid.new(), OverallWidth=0.9, OverallHeight=2.1)
    origin = model.create_entity("IfcAxis2Placement3D", Location=model.create_entity("IfcCartesianPoint", Coordinates=(0., 0., 0.)))
    context = model.create_entity("IfcGeometricRepresentationContext", ContextType="Model", CoordinateSpaceDimension=3, Precision=1e-5, WorldCoordinateSystem=origin)
    for entity, width, depth, height in ((wall, 4., .2, 3.), (opening, .9, .2, 2.1), (door, .9, .05, 2.1)):
        position = model.create_entity("IfcAxis2Placement2D", Location=model.create_entity("IfcCartesianPoint", Coordinates=(0., 0.)))
        profile = model.create_entity("IfcRectangleProfileDef", ProfileType="AREA", Position=position, XDim=width, YDim=depth)
        solid = model.create_entity("IfcExtrudedAreaSolid", SweptArea=profile, Position=origin, ExtrudedDirection=model.create_entity("IfcDirection", DirectionRatios=(0., 0., 1.)), Depth=height)
        shape = model.create_entity("IfcShapeRepresentation", ContextOfItems=context, RepresentationIdentifier="Body", RepresentationType="SweptSolid", Items=[solid])
        entity.Representation = model.create_entity("IfcProductDefinitionShape", Representations=[shape])
        entity.ObjectPlacement = model.create_entity("IfcLocalPlacement", RelativePlacement=origin)
    model.create_entity("IfcRelVoidsElement", GlobalId=ifcopenshell.guid.new(), RelatingBuildingElement=wall, RelatedOpeningElement=opening)
    model.create_entity("IfcRelFillsElement", GlobalId=ifcopenshell.guid.new(), RelatingOpeningElement=opening, RelatedBuildingElement=door)
    person = model.create_entity("IfcPerson", FamilyName="Fixture")
    organisation = model.create_entity("IfcOrganization", Name="Development tests")
    user = model.create_entity("IfcPersonAndOrganization", ThePerson=person, TheOrganization=organisation)
    application = model.create_entity("IfcApplication", ApplicationDeveloper=organisation, Version="1", ApplicationFullName="Development fixture", ApplicationIdentifier="fixture")
    history = model.create_entity("IfcOwnerHistory", OwningUser=user, OwningApplication=application, ChangeAction="ADDED", CreationDate=1)
    units = model.create_entity("IfcUnitAssignment", Units=[model.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE")])
    model.create_entity("IfcProject", GlobalId=ifcopenshell.guid.new(), Name="Development fixture", RepresentationContexts=[context], UnitsInContext=units)
    for entity in model.by_type("IfcRoot"):
        entity.OwnerHistory = history
    source = tmp_path / "source.ifc"
    model.write(str(source))
    definition = {
        "case_id": "case-001",
        "source": {"path": "source.ifc", "sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "asset_id": "unit-fixture", "scene_family": "unit-family", "rights": "test fixture", "approved_use": "research-evaluation"},
        "damage": {"kind": "door", "target_guid": door.GlobalId, "preserve_opening": True},
        "request": {"text": "请给墙上唯一的空门洞补一扇门，其他地方保持原样。", "basis": ["Pre-authored development intent; the unique surviving opening is public."]},
        "task": {"summary": "补一扇门", "reference_guids": [wall.GlobalId, opening.GlobalId], "required_products": {"IfcDoor": 1}, "required_relations": [{"id": "fill", "ifc_class": "IfcRelFillsElement", "basis": "one door fills the retained opening"}], "acceptance": ["Door fills the public opening."], "preservation": ["No other product deletion."], "allowed_alternatives": ["New GlobalId is allowed."], "matching": "Match a new door at the retained public opening.", "tolerances": {"status": "pending_human_review", "length_mm": 1.0}},
        "clarification": {"required_user_facts": [], "out_of_card_policy": "pending_user_decision"},
    }
    return tmp_path, source, definition


def build(sample):
    root, source, definition = sample
    api = package_api()
    output = root / "package"
    api.prepare_case(definition, repository_root=root, output_dir=output)
    return api, source, definition, output


def test_visual_meshes_use_world_positions_and_detect_reference_movement(sample):
    from scripts.ifc_repair.repair_comparison.viewer import collect_meshes, compare_meshes
    _, source, definition = sample
    before = collect_meshes(source)
    target = definition['damage']['target_guid']
    assert before['meshes'][target]['vertices']
    assert before['meshes'][target]['faces']
    assert compare_meshes(before, before, [target])[0]['unchanged'] is True
    changed = copy.deepcopy(before)
    changed['meshes'][target]['vertices'][0] += 1.0
    assert compare_meshes(before, changed, [target])[0]['unchanged'] is False
    del changed['meshes'][target]
    assert compare_meshes(before, changed, [target])[0]['unchanged'] is False


def test_viewer_is_private_actual_mesh_and_safe_to_embed(sample):
    from scripts.ifc_repair.repair_comparison.viewer import write_viewer
    _, _, definition, output = build(sample)
    definition = copy.deepcopy(definition)
    definition['task']['summary'] = '</script><script>alert(1)</script>'
    audit = write_viewer(output, definition)
    html = (output / 'VIEW.html').read_text(encoding='utf-8')
    assert '</script><script>alert(1)</script>' not in html
    assert '"vertices":' in html and '"faces":' in html
    assert audit['removed_target_absent_in_d'] is True
    assert audit['reference_geometry_unchanged'] is True
    assert not (output / 'public/VIEW.html').exists()


def test_package_is_real_damage_with_pending_review_and_separate_public_copy(sample):
    api, source, definition, output = build(sample)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == definition["source"]["sha256"]
    assert (output / "private/reference.ifc").read_bytes() == source.read_bytes()
    assert (output / "private/mutation/damaged.ifc").read_bytes() == (output / "public/model.ifc").read_bytes()
    assert not os.path.samefile(output / "private/mutation/damaged.ifc", output / "public/model.ifc")
    assert sorted(p.name for p in (output / "public").iterdir()) == ["model.ifc", "request.txt"]
    assert definition["damage"]["target_guid"] not in (output / "public/model.ifc").read_text(encoding="utf-8")
    model = ifcopenshell.open(str(output / "public/model.ifc"))
    assert not model.by_type("IfcDoor")
    assert len(model.by_type("IfcOpeningElement")) == 1
    task = json.loads((output / "private/task.json").read_text(encoding="utf-8"))
    assert task["review"]["status"] == "pending_human_review"
    assert task["purpose"] == "development_only"
    assert task["formal_eligible"] is False
    assert task["required_relation_count"] == 1
    report = api.check_package(output)
    assert report["valid"] is True
    assert report["human_accepted"] is False
    checks = json.loads((output / "private/checks.json").read_text(encoding="utf-8"))
    assert checks["source_validation"]["diagnostic_count"] == 0
    assert checks["source_validation"]["express_rules"] is True
    assert checks["source_validation"]["passed"] is True
    assert "pending_human_review" in (output / "REVIEW.md").read_text(encoding="utf-8")
    assert not list(output.rglob("repaired.ifc"))


def test_native_invalid_d_is_rejected_even_without_new_diagnostics(sample):
    root, source, definition = sample
    model = ifcopenshell.open(str(source))
    wall = model.by_type("IfcWall")[0]
    original = wall.to_string()
    invalid = original.replace(f",#{wall.OwnerHistory.id()},", ",$,", 1)
    contents = source.read_text(encoding="utf-8")
    assert original in contents and original != invalid
    source.write_text(contents.replace(original, invalid, 1), encoding="utf-8")
    definition["source"]["sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="DAMAGE_PREPARATION_CHECK_FAILED"):
        package_api().prepare_case(definition, repository_root=root, output_dir=root / "invalid-ifc")
    checks = json.loads((root / "invalid-ifc/private/checks.json").read_text(encoding="utf-8"))
    assert checks["checks"]["no_new_native_diagnostics"] is True
    assert checks["checks"]["damaged_native_validation_passed"] is False


def test_validator_report_is_bound_to_frozen_d(sample):
    _, _, _, output = build(sample)
    report = json.loads((output / "private/damaged-ifc-validation.json").read_text(encoding="utf-8"))
    assert report["passed"] is True
    assert report["express_rules"] is True
    assert report["diagnostic_count"] == 0
    assert report["ifc_sha256"] == hashlib.sha256((output / "public/model.ifc").read_bytes()).hexdigest()
    assert "PASS" in (output / "IFC-VALIDATION.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("products,level,composition", [({"IfcWindow": 1}, "S1", "single"), ({"IfcWindow": 2}, "S2", "same_type"), ({"IfcWindow": 1, "IfcDoor": 1}, "S2", "mixed"), ({"IfcWindow": 2, "IfcDoor": 1}, "S3", "mixed")])
def test_damage_profile_counts_targets_not_supporting_openings(products, level, composition):
    contracts = importlib.import_module("scripts.ifc_repair.repair_comparison.contracts")
    profile = contracts.damage_profile(products)
    assert profile == {"level": level, "target_count": sum(products.values()), "composition": composition, "targets": products}


def test_exports_are_whitelisted_independent_and_writable(sample):
    api, _, _, output = build(sample)
    a = output.parent / "A"
    b = output.parent / "B"
    api.export_public(output, a)
    api.export_public(output, b)
    assert sorted(p.name for p in a.iterdir()) == ["model.ifc", "request.txt"]
    pristine = (b / "model.ifc").read_bytes()
    with (a / "model.ifc").open("ab") as handle:
        handle.write(b"\n/* direct editing allowed */\n")
    assert (b / "model.ifc").read_bytes() == pristine
    assert (output / "private/mutation/damaged.ifc").read_bytes() == pristine
    assert api.check_package(output)["valid"] is True
    with pytest.raises(FileExistsError):
        api.export_public(output, a)


@pytest.mark.parametrize("relative", ["public/request.txt", "public/model.ifc", "private/reference.ifc", "private/task.json", "private/mutation/damaged.ifc"])
def test_tampering_blocks_check_and_export(sample, relative):
    api, _, _, output = build(sample)
    with (output / relative).open("ab") as handle:
        handle.write(b"changed")
    assert api.check_package(output)["valid"] is False
    with pytest.raises(ValueError, match="PACKAGE_CHECK_FAILED"):
        api.export_public(output, output.parent / "export")


def test_extra_private_file_in_public_directory_blocks_export(sample):
    api, _, _, output = build(sample)
    (output / "public/answer.json").write_text('{"secret":"canary"}', encoding="utf-8")
    assert api.check_package(output)["valid"] is False
    with pytest.raises(ValueError, match="PACKAGE_CHECK_FAILED"):
        api.export_public(output, output.parent / "export")


def test_hardlinked_public_input_is_rejected(sample):
    api, _, _, output = build(sample)
    os.link(output / "public/model.ifc", output.parent / "shared.ifc")
    assert api.check_package(output)["valid"] is False


def test_review_notes_do_not_require_a_hash_inventory(sample):
    api, _, _, output = build(sample)
    (output / "REVIEW.md").write_text("Human annotation", encoding="utf-8")
    (output / "notes.txt").write_text("development note", encoding="utf-8")
    assert api.check_package(output)["valid"] is True
    assert not (output / "integrity.json").exists()


def test_pending_package_can_refresh_in_place_but_accepted_cannot(sample):
    api, source, definition, output = build(sample)
    definition["request"]["text"] = "给墙中央的空门洞补一扇宽900毫米、高2100毫米的门。"
    api.prepare_case(definition, repository_root=source.parent, output_dir=output)
    assert definition["request"]["text"] in (output / "public/request.txt").read_text(encoding="utf-8")
    assert api.check_package(output)["valid"]
    task_path = output / "private/task.json"
    task = json.loads(task_path.read_text(encoding="utf-8"))
    task["review"]["status"] = "accepted"
    task_path.write_text(json.dumps(task), encoding="utf-8")
    with pytest.raises(ValueError, match="ONLY_PENDING_DEVELOPMENT"):
        api.prepare_case(definition, repository_root=source.parent, output_dir=output)


@pytest.mark.skipif(os.name != "nt", reason="Windows inherited ACL regression")
def test_mutation_directory_uses_normal_inherited_permissions(sample):
    _, _, _, output = build(sample)
    path = str(output / "private/mutation").replace("'", "''")
    result = subprocess.run(["pwsh", "-NoProfile", "-Command", f"(Get-Acl -LiteralPath '{path}').AreAccessRulesProtected"], capture_output=True, text=True, timeout=20)
    assert result.returncode == 0
    assert result.stdout.strip() == "False"


def test_export_cannot_be_nested_with_private_material(sample):
    api, _, _, output = build(sample)
    with pytest.raises(ValueError, match="EXPORT_MUST_BE_OUTSIDE_PRIVATE_PACKAGE"):
        api.export_public(output, output / "another-public-view")


def test_relation_denominator_requires_a_real_damaged_edge(sample):
    root, _, definition = sample
    definition["task"]["required_relations"].append({"id": "type", "ifc_class": "IfcRelDefinesByType", "basis": "claimed type edge, but fixture has none"})
    with pytest.raises(ValueError, match="DAMAGE_PREPARATION_CHECK_FAILED"):
        package_api().prepare_case(definition, repository_root=root, output_dir=root / "bad-edge")
    checks = json.loads((root / "bad-edge/private/checks.json").read_text(encoding="utf-8"))
    assert checks["checks"]["required_relation_edges_verified"] is False


@pytest.mark.parametrize("damage", ["wall_thickness", "missing_geometry"])
def test_inspection_blocks_host_damage_and_missing_post_damage_geometry(sample, damage):
    api, _, definition, output = build(sample)
    damaged = output / "private/mutation/damaged.ifc"
    model = ifcopenshell.open(str(damaged))
    wall = model.by_type("IfcWall")[0]
    if damage == "wall_thickness":
        wall.Representation.Representations[0].Items[0].SweptArea.YDim = .4
    else:
        wall.Representation = None
    model.write(str(damaged))
    checks = api.inspect_damage(output / "private/reference.ifc", damaged, definition)
    assert checks["checks"]["no_unexpected_modified_products"] is False
    if damage == "missing_geometry":
        assert checks["checks"]["required_geometry_available"] is False


def test_preparation_refuses_unowned_directory_and_stale_source(sample):
    api, source, definition, output = build(sample)
    unknown = source.parent / "unowned"
    unknown.mkdir()
    with pytest.raises(ValueError, match="ONLY_PENDING_DEVELOPMENT"):
        api.prepare_case(definition, repository_root=source.parent, output_dir=unknown)
    definition["source"]["sha256"] = "0" * 64
    next_output = output.parent / "stale"
    with pytest.raises(ValueError, match="SOURCE_IFC_FINGERPRINT_MISMATCH"):
        api.prepare_case(definition, repository_root=source.parent, output_dir=next_output)
    assert not next_output.exists()


@pytest.mark.parametrize("change", ["accepted", "leak", "no_answer", "traversal", "empty_relations", "wrong_product_count", "duplicate_edge", "surviving_guid", "method_hint"])
def test_invalid_contracts_fail_before_writing(sample, change):
    root, _, original = sample
    definition = copy.deepcopy(original)
    if change == "accepted":
        definition["review"] = {"status": "accepted"}
    elif change == "leak":
        definition["request"]["text"] += definition["damage"]["target_guid"]
    elif change == "no_answer":
        definition["clarification"]["required_user_facts"] = [{"fact_id": "swing", "why_required": "two options", "why_not_in_d": "not encoded"}]
    elif change == "traversal":
        definition["source"]["path"] = "../source.ifc"
    elif change == "wrong_product_count":
        definition["task"]["required_products"] = {"IfcDoor": 2}
    elif change == "duplicate_edge":
        definition["task"]["required_relations"].append({"id": "second-fill", "ifc_class": "IfcRelFillsElement", "basis": "counting the same member edge twice"})
    elif change == "surviving_guid":
        definition["request"]["text"] += definition["task"]["reference_guids"][0]
    elif change == "method_hint":
        definition["request"]["text"] += "请使用IfcOpenShell脚本。"
    else:
        definition["task"]["required_relations"] = []
    with pytest.raises(ValueError):
        package_api().prepare_case(definition, repository_root=root, output_dir=root / "invalid")
    assert not (root / "invalid").exists()


def test_clarification_card_is_private_and_unapproved(sample):
    root, _, definition = sample
    definition["clarification"]["required_user_facts"] = [{"fact_id": "swing", "why_required": "two compatible choices", "why_not_in_d": "opening does not encode preference", "allowed_answers": ["left", "right"], "answer": "left", "answer_basis": "proposed user preference, requires review", "reply_scope": "only when asked about door swing"}]
    api, _, _, output = build(sample)
    card = json.loads((output / "private/answer-card.json").read_text(encoding="utf-8"))
    assert card["status"] == "pending_human_review"
    assert card["required_user_facts"][0]["answer"] == "left"
    assert "swing" not in (output / "public/request.txt").read_text(encoding="utf-8")
    assert api.check_package(output)["valid"] is True


def test_cli_does_not_overwrite_an_unowned_batch(sample):
    root, _, definition = sample
    definitions = root / 'definitions.json'
    definitions.write_text(json.dumps({'cases': [definition]}), encoding='utf-8')
    output = root / 'unowned'
    output.mkdir()
    (output / 'README.md').write_text('Existing user notes', encoding='utf-8')
    result = subprocess.run([sys.executable, str(ROOT / 'scripts/ifc_repair/repair_comparison/prepare.py'), 'prepare', '--definitions', str(definitions), '--repository-root', str(root), '--output', str(output)], capture_output=True, text=True, encoding='utf-8', timeout=30)
    assert result.returncode != 0
    assert (output / 'README.md').read_text(encoding='utf-8') == 'Existing user notes'
    assert not (output / 'case-001').exists()


def test_cli_prepares_then_checks_without_network(sample):
    root, _, definition = sample
    package_api()
    definitions = root / "definitions.json"
    definitions.write_text(json.dumps({"cases": [definition]}), encoding="utf-8")
    script = ROOT / "scripts/ifc_repair/repair_comparison/prepare.py"
    result = subprocess.run([sys.executable, str(script), "prepare", "--definitions", str(definitions), "--repository-root", str(root), "--output", str(root / "batch")], cwd=root, capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    checked = subprocess.run([sys.executable, str(script), "check", str(root / "batch/case-001")], cwd=root, capture_output=True, text=True, encoding="utf-8", timeout=30)
    assert checked.returncode == 0, checked.stdout + checked.stderr
    assert json.loads(checked.stdout)["human_accepted"] is False
