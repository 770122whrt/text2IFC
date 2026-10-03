"""First-batch preparation: multiple targets, valid D, no self acceptance."""
import copy
import json

import ifcopenshell
import ifcopenshell.util.element
import pytest

from tests.ifc_repair.repair_comparison.test_preparation import sample
from scripts.ifc_repair.repair_comparison.contracts import sha256


@pytest.fixture
def candidate(sample):
    root, source, definition = sample
    model = ifcopenshell.open(str(source))
    door = model.by_type('IfcDoor')[0]
    opening = model.by_type('IfcOpeningElement')[0]
    wall = model.by_type('IfcWall')[0]
    second = model.create_entity('IfcWindow', GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=door.OwnerHistory, ObjectPlacement=door.ObjectPlacement,
        Representation=ifcopenshell.util.element.copy_deep(model, door.Representation, exclude=('IfcGeometricRepresentationContext',)), OverallHeight=door.OverallHeight,
        OverallWidth=door.OverallWidth)
    second_opening = ifcopenshell.util.element.copy(model, opening)
    second_opening.Representation = ifcopenshell.util.element.copy_deep(model, opening.Representation, exclude=('IfcGeometricRepresentationContext',))
    placement = model.createIfcLocalPlacement(None, model.createIfcAxis2Placement3D(
        model.createIfcCartesianPoint((1.0, 0.0, 0.0))))
    second.ObjectPlacement = placement
    second_opening.ObjectPlacement = ifcopenshell.util.element.copy_deep(model, placement)
    for kind, attrs in (
        ('IfcRelFillsElement', {'RelatingOpeningElement': second_opening, 'RelatedBuildingElement': second}),
        ('IfcRelVoidsElement', {'RelatingBuildingElement': wall, 'RelatedOpeningElement': second_opening}),
    ):
        model.create_entity(kind, GlobalId=ifcopenshell.guid.new(), OwnerHistory=door.OwnerHistory, **attrs)
    reference = model.create_entity('IfcDoor', GlobalId=ifcopenshell.guid.new(), OwnerHistory=door.OwnerHistory,
        ObjectPlacement=ifcopenshell.util.element.copy_deep(model, door.ObjectPlacement),
        Representation=ifcopenshell.util.element.copy_deep(model, door.Representation, exclude=('IfcGeometricRepresentationContext',)),
        OverallWidth=door.OverallWidth, OverallHeight=door.OverallHeight)
    model.write(str(source))
    row = {'candidate_slot': 'formal-001', 'asset_id': 'unit-fixture',
        'source_path': 'source.ifc', 'source_sha256': sha256(source),
        'scene_family': 'unit-family', 'license': 'fixture license',
        'rights_source_url': 'https://example.org/source',
        'rights_conditions': 'Unit fixture only', 'source_role': 'preselected_reference',
        'task_proposal': {'provisional_source_step_ids': [door.id(), second.id()],
            'retained_reference_step_ids': [reference.id()],
            'public_request': '请在墙上空着的门洞里补一扇门，另补一扇宽900毫米、高2100毫米的窗，其他地方保持原样。',
            'clarification_required': False}}
    return root, source, row


def test_mixed_damage_is_valid_with_two_targets_and_pending_review(candidate):
    from scripts.ifc_repair.repair_comparison.formal_batch import prepare_candidate, check_candidate
    root, source, row = candidate
    before = source.read_bytes()
    output = root / 'batch/formal-001'
    report = prepare_candidate(row, repository_root=root, output=output)
    assert report['valid'] and not report['human_accepted']
    assert source.read_bytes() == before
    model = ifcopenshell.open(str(output / 'public/model.ifc'))
    assert not model.by_type('IfcWindow') and len(model.by_type('IfcDoor')) == 1
    assert len(model.by_type('IfcOpeningElement')) == 1
    task = json.loads((output / 'private/task.json').read_text(encoding='utf8'))
    assert task['required_product_count'] == 2
    assert task['damage_profile']['composition'] == 'mixed'
    assert task['review']['status'] == 'pending_human_review'
    assert task['budget']['provider_calls_allowed'] is False
    checks = json.loads((output / 'private/checks.json').read_text(encoding='utf8'))
    assert checks['damaged_validation']['passed']
    assert checks['damaged_validation']['express_rules'] is True
    assert all(checks['checks'].values())
    assert check_candidate(output)['valid']
    assert sorted(p.name for p in (output / 'public').iterdir()) == ['model.ifc', 'request.txt']


def test_pending_refresh_is_in_place_but_human_review_is_not_overwritten(candidate):
    from scripts.ifc_repair.repair_comparison.formal_batch import prepare_candidate
    root, _, row = candidate
    output = root / 'batch/formal-001'
    prepare_candidate(row, repository_root=root, output=output)
    prepare_candidate(row, repository_root=root, output=output)
    task_file = output / 'private/task.json'
    task = json.loads(task_file.read_text(encoding='utf8'))
    task['review']['status'] = 'accepted'
    task_file.write_text(json.dumps(task), encoding='utf8')
    with pytest.raises(ValueError, match='ONLY_PENDING'):
        prepare_candidate(row, repository_root=root, output=output)


@pytest.mark.parametrize('bad', ['duplicate', 'guid', 'method'])
def test_ambiguous_recipe_or_private_public_hints_fail_before_damage(candidate, bad):
    from scripts.ifc_repair.repair_comparison.formal_batch import prepare_candidate
    root, source, row = candidate
    row = copy.deepcopy(row)
    if bad == 'duplicate':
        row['task_proposal']['provisional_source_step_ids'] *= 2
    else:
        row['task_proposal']['public_request'] += (
            ifcopenshell.open(str(source)).by_type('IfcDoor')[0].GlobalId if bad == 'guid' else '请使用 IfcOpenShell')
    with pytest.raises(ValueError):
        prepare_candidate(row, repository_root=root, output=root / bad)
    assert not (root / bad).exists()
