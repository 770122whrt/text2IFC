"""Source-preservation and admission boundaries for the local RVT pipeline."""
import hashlib
import importlib.util
import json
from pathlib import Path
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("rvt_pipeline", ROOT / "dataset/external/RVT/pipeline.py")


@pytest.fixture
def pipeline():
    assert SPEC.origin and Path(SPEC.origin).exists(), "RVT pipeline is not implemented"
    module = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(module)
    return module


def make_bundle(root, name="01_RVT/source/model.rvt", payload=b"rvt-test-bytes", digest=None):
    root.mkdir(parents=True, exist_ok=True)
    archive = root / "models.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr(name, payload)
    row = {"inventory_id": "INV-001", "package_path": name, "filename": "model.rvt",
           "source_name": "source", "sha256": digest or hashlib.sha256(payload).hexdigest(),
           "size_bytes": len(payload)}
    parts = {"part_files": [{"filename": archive.name, "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(), "bytes": archive.stat().st_size}], "total_rvt_entries": 1}
    meta = root / "Text2IFC_RVT86_Handoff_Metadata_20260911.zip"
    with zipfile.ZipFile(meta, "w") as z:
        z.writestr("02_METADATA/RVT_manifest_86_enriched.json", json.dumps([row]))
        z.writestr("02_METADATA/PARTS_MANIFEST.json", json.dumps(parts))
        z.writestr("02_METADATA/RVT_inventory_86_original.json", json.dumps({"unique_rvts": [{**row, "asset_id": "OLD-1"}]}))
        z.writestr("02_METADATA/crosssource_dependency_manifest.json", "[]")
    return row


def test_extract_preserves_bytes_and_old_identity(tmp_path, pipeline):
    row = make_bundle(tmp_path)
    result = pipeline.extract_handoff(tmp_path)
    assert (tmp_path / "extracted" / row["package_path"]).read_bytes() == b"rvt-test-bytes"
    assert result["assets"][0]["legacy_asset_id"] == "OLD-1"
    assert pipeline.extract_handoff(tmp_path) == result


@pytest.mark.parametrize("name", ["../outside.rvt", "01_RVT/../../escape.rvt", "C:/escape.rvt", "01_RVT/file.rvt:stream", "01_RVT/NUL.rvt"])
def test_rejects_unsafe_windows_archive_paths_before_writes(tmp_path, pipeline, name):
    make_bundle(tmp_path, name=name)
    with pytest.raises(ValueError, match="UNSAFE"):
        pipeline.extract_handoff(tmp_path)
    assert not (tmp_path / "extracted").exists()


def test_batch_candidate_requires_all_gates():
    spec = importlib.util.spec_from_file_location("rvt_batch", ROOT / "dataset/external/RVT/batch.py")
    module = importlib.util.module_from_spec(spec)
    import sys
    sys.path.insert(0, str(ROOT / "dataset/external/RVT"))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    attempt = {"conversion_completed": True, "status": "validation_failed"}
    normalization = {"pending": [], "preservation": {"source_unchanged": True, "product_guids_unchanged": True, "unchanged_entities_equal": True}}
    validation = {"technical_candidate": True}
    assert module.candidate_status(attempt, normalization, validation) == "technical_candidate"
    assert module.candidate_status(attempt, {**normalization, "pending": ["uncertain"]}, validation) == "manual_review_required"
    assert module.candidate_status(attempt, normalization, {"technical_candidate": False}) == "validation_failed"
    assert module.candidate_status({**attempt, "status": "source_mutation_detected"}, normalization, validation) == "source_mutation_detected"


def test_hash_mismatch_does_not_extract(tmp_path, pipeline):
    make_bundle(tmp_path, digest="0" * 64)
    with pytest.raises(ValueError, match="HASH"):
        pipeline.extract_handoff(tmp_path)
    assert not (tmp_path / "extracted").exists()


def test_existing_different_file_is_never_overwritten(tmp_path, pipeline):
    row = make_bundle(tmp_path)
    target = tmp_path / "extracted" / row["package_path"]
    target.parent.mkdir(parents=True)
    target.write_bytes(b"user work")
    with pytest.raises(ValueError, match="EXISTING"):
        pipeline.extract_handoff(tmp_path)
    assert target.read_bytes() == b"user work"


def test_empty_ifc_is_not_admitted(tmp_path, pipeline):
    import ifcopenshell
    path = tmp_path / "empty.ifc"
    ifcopenshell.file(schema="IFC2X3").write(path)
    result = pipeline.validate_ifc(path)
    assert result["schema"] == "IFC2X3"
    assert result["technical_candidate"] is False
    assert "NO_BUILDING_BODY" in result["blockers"]


def test_malformed_ifc_is_not_admitted(tmp_path, pipeline):
    path = tmp_path / "bad.ifc"
    path.write_text("not an IFC", encoding="utf-8")
    result = pipeline.validate_ifc(path)
    assert result["technical_candidate"] is False
    assert result["blockers"]


def test_ddc_command_preserves_properties_and_separates_paths(tmp_path, pipeline):
    argv = pipeline.ddc_command(tmp_path / "tool path.exe", tmp_path / "source path.rvt", tmp_path / "result.ifc")
    assert argv[1] == str(tmp_path / "source path.rvt")
    assert argv[argv.index("--mode") + 1] == "custom"
    config = argv[argv.index("--config") + 1]
    assert "FileVersion=ifc2x3" in config
    for flag in ["BimRvPropSets=y", "IfcCommonPropSets=y", "BaseQuantities=y", "MaterialPropSets=y"]:
        assert flag in config


def test_converter_failure_retains_attempt_and_original(tmp_path, pipeline):
    import sys
    source = tmp_path / "input.rvt"
    source.write_bytes(b"source")
    result = pipeline.run_attempt([sys.executable, "-c", "raise SystemExit(7)"], source,
                                  tmp_path / "attempt", expected_sha256=hashlib.sha256(b"source").hexdigest())
    assert result["status"] == "converter_failed"
    assert source.read_bytes() == b"source"
    assert (tmp_path / "attempt/attempt.json").is_file()


def test_exit_zero_without_ifc_is_failure(tmp_path, pipeline):
    import sys
    source = tmp_path / "input.rvt"
    source.write_bytes(b"source")
    result = pipeline.run_attempt([sys.executable, "-c", "pass"], source,
                                  tmp_path / "attempt", expected_sha256=hashlib.sha256(b"source").hexdigest())
    assert result["status"] == "missing_output"


def test_wrong_source_hash_blocks_converter(tmp_path, pipeline):
    source = tmp_path / "input.rvt"
    source.write_bytes(b"changed")
    with pytest.raises(ValueError, match="SOURCE_HASH"):
        pipeline.run_attempt(["not-to-be-executed"], source, tmp_path / "attempt", expected_sha256="0" * 64)
    assert not (tmp_path / "attempt").exists()


def test_curve_representations_are_checked_as_curves(tmp_path, pipeline):
    import ifcopenshell
    f = ifcopenshell.file(schema="IFC2X3")
    point = f.createIfcCartesianPoint((0., 0., 0.))
    axis = f.createIfcAxis2Placement3D(point)
    context = f.createIfcGeometricRepresentationContext(None, "Model", 3, 1e-5, axis, None)
    curve = f.createIfcPolyline([point, f.createIfcCartesianPoint((1., 0., 0.))])
    rep = f.createIfcShapeRepresentation(context, "FootPrint", "Curve3D", [curve])
    shape = f.createIfcProductDefinitionShape(None, None, [rep])
    annotation = f.create_entity("IfcAnnotation", GlobalId=ifcopenshell.guid.new(), Representation=shape)
    path = tmp_path / "curve.ifc"
    f.write(path)
    result = pipeline.validate_ifc(path)
    assert result["geometry"]["checked"] == 1
    assert result["geometry"]["failed"] == 0


def normalizer():
    spec = importlib.util.spec_from_file_location("rvt_normalize", ROOT / "dataset/external/RVT/normalize.py")
    assert Path(spec.origin).exists(), "Normalization is not implemented"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_normalization_only_detaches_exact_typed_duplicates(tmp_path):
    import ifcopenshell
    f = ifcopenshell.file(schema="IFC2X3")
    p1 = f.createIfcPropertySingleValue("A", None, f.createIfcLabel("same"), None)
    p2 = f.createIfcPropertySingleValue("A", None, f.createIfcLabel("same"), None)
    p3 = f.createIfcPropertySingleValue("B", None, f.createIfcText("value"), None)
    p4 = f.createIfcPropertySingleValue("B", None, f.createIfcLabel("value"), None)
    ps = f.createIfcPropertySet(ifcopenshell.guid.new(), f.create_entity("IfcOwnerHistory"), "Test", None, [p1,p2,p3,p4])
    source, target = tmp_path / "source.ifc", tmp_path / "candidate.ifc"
    f.write(source)
    original = source.read_bytes()
    report = normalizer().normalize(source, target, converter_label="test fixture")
    output = ifcopenshell.open(target)
    assert [p.id() for p in output.by_id(ps.id()).HasProperties] == [p1.id(),p3.id(),p4.id()]
    assert output.by_id(p2.id()) is not None
    assert report["pending"] and source.read_bytes() == original


def test_normalization_keeps_product_guid_and_clones_shared_psets(tmp_path):
    import ifcopenshell
    f = ifcopenshell.file(schema="IFC2X3")
    guid = ifcopenshell.guid.new()
    wall = f.create_entity("IfcWall", GlobalId=guid)
    prop = f.createIfcPropertySingleValue("A", None, f.createIfcLabel("value"), None)
    ps = f.createIfcPropertySet(guid, f.create_entity("IfcOwnerHistory"), "Test", None, [prop])
    a = f.create_entity("IfcWallType", GlobalId=ifcopenshell.guid.new(), HasPropertySets=[ps], PredefinedType="STANDARD")
    b = f.create_entity("IfcWallType", GlobalId=ifcopenshell.guid.new(), HasPropertySets=[ps], PredefinedType="STANDARD")
    source, target = tmp_path / "source.ifc", tmp_path / "candidate.ifc"
    f.write(source)
    report = normalizer().normalize(source, target, converter_label="test fixture")
    out = ifcopenshell.open(target)
    assert out.by_id(wall.id()).GlobalId == guid
    assert out.by_id(a.id()).HasPropertySets[0] != out.by_id(b.id()).HasPropertySets[0]
    assert out.by_id(a.id()).HasPropertySets[0].HasProperties == out.by_id(b.id()).HasPropertySets[0].HasProperties
    assert report["preservation"]["unchanged_entities_equal"]


def test_normalization_never_overwrites_source(tmp_path):
    path = tmp_path / "source.ifc"
    path.write_bytes(b"original")
    with pytest.raises(ValueError, match="OVERWRITE"):
        normalizer().normalize(path, path, converter_label="test fixture")
    assert path.read_bytes() == b"original"


@pytest.mark.parametrize("z", [0.0, 1.0])
def test_grid_axis_projection_requires_exact_local_xy_plane(tmp_path, z):
    import ifcopenshell
    f = ifcopenshell.file(schema="IFC2X3")
    origin = f.createIfcCartesianPoint((0.,0.,z))
    line = f.createIfcLine(origin, f.createIfcVector(f.createIfcDirection((1.,0.,0.)), 1.))
    curve = f.createIfcTrimmedCurve(line, [origin], [f.createIfcCartesianPoint((2.,0.,z))], True, "CARTESIAN")
    axis = f.createIfcGridAxis("A", curve, True)
    source, target = tmp_path / "source.ifc", tmp_path / "candidate.ifc"
    f.write(source)
    report = normalizer().normalize(source, target, converter_label="test fixture")
    out = ifcopenshell.open(target)
    assert out.by_id(axis.id()).AxisCurve.Dim == (2 if z == 0 else 3)
    assert out.by_id(curve.id()).to_string() == curve.to_string()
    if z: assert report["pending"]


def test_volume_unit_prefix_is_independent_of_length_prefix(tmp_path):
    import ifcopenshell
    f = ifcopenshell.file(schema="IFC2X3")
    length = f.createIfcSIUnit(None, "LENGTHUNIT", "MILLI", "METRE")
    volume = f.create_entity("IfcSIUnit", UnitType="VOLUMEUNIT")
    f.createIfcUnitAssignment([length, volume])
    source, target = tmp_path / "source.ifc", tmp_path / "candidate.ifc"
    f.write(source)
    normalizer().normalize(source, target, converter_label="test fixture")
    out = ifcopenshell.open(target)
    assert out.by_id(volume.id()).Name == "CUBIC_METRE"
    assert out.by_id(volume.id()).Prefix is None
    assert out.by_id(length.id()).Prefix == "MILLI"


@pytest.mark.parametrize("values,scale,span,expected", [
    ([1100.,1100.], .001, 1.1, 1100.),
    ([1100.,1000.], .001, 1.1, None),
    ([1100.], .001, 1.1, None),
    ([1100.,1100.], .001, 2.2, None),
    ([0.,0.], .001, 0., None),
    ([1100.,1100.], 1., 1.1, None),
    ([float('nan'),float('nan')], .001, 1.1, None),
])
def test_height_correction_needs_independent_values_units_and_geometry(values, scale, span, expected):
    spec = importlib.util.spec_from_file_location("rvt_height", ROOT / "dataset/external/RVT/height_normalize.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.prove_height_value(values, scale, span) == expected


def test_unassigned_si_unit_fix_preserves_prefixed_and_other_units(tmp_path):
    import ifcopenshell
    spec = importlib.util.spec_from_file_location("rvt_units", ROOT / "dataset/external/RVT/unit_normalize.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    f = ifcopenshell.file(schema="IFC2X3")
    area = f.create_entity("IfcSIUnit", UnitType="AREAUNIT")
    volume = f.create_entity("IfcSIUnit", UnitType="VOLUMEUNIT")
    prefixed = f.create_entity("IfcSIUnit", UnitType="AREAUNIT", Prefix="MILLI")
    other = f.create_entity("IfcSIUnit", UnitType="MASSUNIT")
    source, target = tmp_path / "source.ifc", tmp_path / "candidate.ifc"
    f.write(source)
    original = source.read_bytes()
    report = module.normalize(source, target)
    out = ifcopenshell.open(target)
    assert out.by_id(area.id()).Name == "SQUARE_METRE"
    assert out.by_id(volume.id()).Name == "CUBIC_METRE"
    assert out.by_id(prefixed.id()).Name is None and out.by_id(other.id()).Name is None
    assert source.read_bytes() == original and len(report["changes"]) == 2


def test_assembly_rejects_competing_outputs_for_one_rvt():
    spec = importlib.util.spec_from_file_location("rvt_assemble", ROOT / "dataset/external/RVT/assemble.py")
    module = importlib.util.module_from_spec(spec)
    import sys
    sys.path.insert(0, str(ROOT / "dataset/external/RVT"))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    first = {"inventory_id": "INV-001", "status": "technical_candidate", "ifc_sha256": "a"}
    failed = {"inventory_id": "INV-002", "status": "validation_failed"}
    assert module.choose_passes([first, failed]) == {"INV-001": first}
    assert module.choose_passes([first, first]) == {"INV-001": first}
    with pytest.raises(ValueError, match="COMPETING_PASSING_OUTPUTS"):
        module.choose_passes([first, {**first, "ifc_sha256": "b"}])


def test_eligibility_requires_review_and_dependencies(pipeline):
    row = {"source_name": "reviewed", "dependencies": []}
    assert pipeline.conversion_blocker(row, {}) == "source_rights_review_required"
    policies = {"reviewed": {"local_conversion_research_supported": True}}
    assert pipeline.conversion_blocker(row, policies) is None
    assert pipeline.conversion_blocker({**row, "dependencies": [{"presence": "present_runtime_unverified"}]}, policies) == "dependency_resolution_required"


def test_original_metadata_conflict_is_detected_before_extraction(tmp_path, pipeline):
    make_bundle(tmp_path)
    path = tmp_path / "Text2IFC_RVT86_Handoff_Metadata_20260911.zip"
    with zipfile.ZipFile(path) as z:
        data = {i.filename: z.read(i) for i in z.infolist()}
    original = json.loads(data["02_METADATA/RVT_inventory_86_original.json"])
    original["unique_rvts"][0]["source_name"] = "conflicting source"
    data["02_METADATA/RVT_inventory_86_original.json"] = json.dumps(original).encode()
    with zipfile.ZipFile(path, "w") as z:
        for name, content in data.items(): z.writestr(name, content)
    with pytest.raises(ValueError, match="ORIGINAL_METADATA_CONFLICT"):
        pipeline.extract_handoff(tmp_path)
    assert not (tmp_path / "extracted").exists()
