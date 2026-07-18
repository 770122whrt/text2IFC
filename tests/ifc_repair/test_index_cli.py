from __future__ import annotations

import hashlib
import json
from pathlib import Path

import ifcopenshell
import pytest


def _api() -> object:
    try:
        from scripts.ifc_repair import index
    except ImportError:
        pytest.fail("Phase 7 index CLI is not implemented yet")
    return index


def test_cli_build_and_query_emit_json_without_modifying_source(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    cli = _api(); source = tmp_path / "source.ifc"; model = ifcopenshell.file(schema="IFC2X3")
    guid = "0AAAAAAAAAAAAAAAAAAAAA"; model.create_entity("IfcWall", GlobalId=guid, Name="CLI wall"); model.write(str(source))
    before = hashlib.sha256(source.read_bytes()).hexdigest(); database = tmp_path / "index.sqlite"
    assert cli.main(["build", str(source), "--database", str(database)]) == 0
    build_payload = json.loads(capsys.readouterr().out); assert build_payload["status"] == "built"
    query_path = tmp_path / "query.json"
    query_path.write_text(json.dumps({"schema_version": "text2ifc/ifc-target-query/0.1", "allowed_ifc_classes": ["IfcWall"], "global_id": guid}), encoding="utf-8")
    assert cli.main(["query", str(database), "--query", str(query_path)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["resolution"]["status"] == "resolved"
    assert payload["context"]["candidate_targets"][0]["target_id"] == f"ifc:{guid}"
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before
    rendered = json.dumps(payload); assert "ISO-10303-21" not in rendered


def test_cli_uses_stable_nonzero_codes_for_invalid_query_and_nonresolution(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    cli = _api(); source = tmp_path / "source.ifc"; model = ifcopenshell.file(schema="IFC2X3")
    model.create_entity("IfcWall", GlobalId="0AAAAAAAAAAAAAAAAAAAAA", Name="wall"); model.write(str(source)); database = tmp_path / "index.sqlite"
    assert cli.main(["build", str(source), "--database", str(database)]) == 0; capsys.readouterr()
    invalid = tmp_path / "invalid.json"; invalid.write_text("{}", encoding="utf-8")
    assert cli.main(["query", str(database), "--query", str(invalid)]) == 2
    assert json.loads(capsys.readouterr().out)["code"] == "INVALID_TARGET_QUERY"
    missing = tmp_path / "missing.json"; missing.write_text(json.dumps({"schema_version": "text2ifc/ifc-target-query/0.1", "allowed_ifc_classes": ["IfcDoor"]}), encoding="utf-8")
    assert cli.main(["query", str(database), "--query", str(missing)]) == 3
    assert json.loads(capsys.readouterr().out)["resolution"]["status"] == "not_found"
