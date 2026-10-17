"""Deleting a product must not strand relationships or erase other members."""
from __future__ import annotations

import hashlib

import ifcopenshell
import ifcopenshell.guid
import pytest

from scripts.ifc_repair.dataset_batch.engine import apply_recipe, inventory_model
from scripts.ifc_repair.dataset_batch.validation import native_validate


@pytest.mark.parametrize("relation_kind", ["covering", "assignment_single", "assignment_shared"])
def test_deletion_cleans_required_endpoints_and_preserves_shared_members(scene_factory, tmp_path, relation_kind):
    source = scene_factory(tmp_path / "source.ifc")
    model = ifcopenshell.open(str(source))
    target, sibling = model.by_type("IfcBeam")
    target_guid, sibling_guid = target.GlobalId, sibling.GlobalId
    history = target.OwnerHistory

    def root(cls, **attributes):
        return model.create_entity(cls, GlobalId=ifcopenshell.guid.new(), OwnerHistory=history, **attributes)

    actor = root("IfcActor", Name="Retained actor", TheActor=model.by_type("IfcPerson")[0])
    unrelated = root("IfcRelAssignsToActor", RelatedObjects=[sibling], RelatingActor=actor)
    unrelated_guid, actor_guid = unrelated.GlobalId, actor.GlobalId
    cover_guid = None
    if relation_kind == "covering":
        covering = root("IfcCovering", Name="Retained covering", PredefinedType="CLADDING")
        cover_guid = covering.GlobalId
        relation = root("IfcRelCoversBldgElements", RelatingBuildingElement=target, RelatedCoverings=[covering])
    else:
        members = [target, sibling] if relation_kind == "assignment_shared" else [target]
        relation = root("IfcRelAssignsToActor", RelatedObjects=members, RelatingActor=actor)
    relation_guid = relation.GlobalId
    model.write(str(source))
    assert native_validate(source)["passed"], "The reproduction must begin with a valid IFC."
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    inventory = inventory_model(source)
    snapshot = next(item for item in inventory["targets"]["beam"] if item["guid"] == target_guid)
    recipe = {"family": "beam", "severity": "light", "deletions": [{**snapshot, "preserve_opening": False}], "property_changes": []}
    output = tmp_path / "case"
    result = apply_recipe(source, recipe, output, inventory=inventory)
    assert result["status"] == "passed"
    damaged = ifcopenshell.open(str(output / "public/model.ifc"))
    assert native_validate(damaged)["passed"]
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before
    assert damaged.by_guid(actor_guid).TheActor == damaged.by_type("IfcPerson")[0]
    assert [p.GlobalId for p in damaged.by_guid(unrelated_guid).RelatedObjects] == [sibling_guid]
    if relation_kind == "assignment_shared":
        assert [p.GlobalId for p in damaged.by_guid(relation_guid).RelatedObjects] == [sibling_guid]
    else:
        with pytest.raises(RuntimeError):
            damaged.by_guid(relation_guid)
    if cover_guid:
        assert damaged.by_guid(cover_guid).Name == "Retained covering"


def test_batch_deletion_removes_assignment_when_its_last_member_is_deleted(scene_factory, tmp_path):
    source = scene_factory(tmp_path / "source.ifc")
    model = ifcopenshell.open(str(source))
    targets = model.by_type("IfcBeam")
    actor = model.create_entity("IfcActor", GlobalId=ifcopenshell.guid.new(), OwnerHistory=targets[0].OwnerHistory,
                                Name="Retained actor", TheActor=model.by_type("IfcPerson")[0])
    relation = model.create_entity("IfcRelAssignsToActor", GlobalId=ifcopenshell.guid.new(), OwnerHistory=targets[0].OwnerHistory,
                                   RelatedObjects=targets, RelatingActor=actor)
    relation_guid, actor_guid = relation.GlobalId, actor.GlobalId
    model.write(str(source))
    assert native_validate(source)["passed"]
    inventory = inventory_model(source)
    recipe = {"family": "beam", "severity": "medium",
              "deletions": [{**target, "preserve_opening": False} for target in inventory["targets"]["beam"]], "property_changes": []}
    output = tmp_path / "case"
    assert apply_recipe(source, recipe, output, inventory=inventory)["status"] == "passed"
    damaged = ifcopenshell.open(str(output / "public/model.ifc"))
    assert damaged.by_guid(actor_guid).Name == "Retained actor"
    assert not damaged.by_type("IfcBeam")
    with pytest.raises(RuntimeError):
        damaged.by_guid(relation_guid)
    assert native_validate(damaged)["passed"]
