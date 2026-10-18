"""Delegated technical review must earn acceptance from real G/D evidence."""
from __future__ import annotations

import copy
import importlib
import json

import ifcopenshell
import pytest

from tests.ifc_repair.repair_comparison.test_task_authoring import author_source
from scripts.ifc_repair.repair_comparison.authoring import author_candidate
from scripts.ifc_repair.repair_comparison.contracts import sha256, read_json, write_json
from scripts.ifc_repair.repair_comparison.formal_batch import prepare_candidate

AUTHORIZATION = {'user_quote': '请代我做技术审题，然后先做实验。', 'at': '2026-10-08T09:00:00+08:00'}


def test_shared_y_and_multiple_x_form_complete_public_coordinates():
    module = importlib.import_module('scripts.ifc_repair.repair_comparison.task_review')
    text = 'Y约-4.780米的外墙上少了两扇窗。平面中心的X分别为4.455米和-2.595米。'
    assert module._coordinate_pairs(text) == [('4.455', '-4.780'), ('-2.595', '-4.780')]
    assert module._coordinate_pairs('Y约-4.780米的外墙上。X没有给出。') == []
    assert module._coordinate_pairs('窗位于Y约10.753米的外墙上，平面中心X为-10.014米；') == [('-10.014','10.753')]


def test_missing_first_target_fact_is_not_supplied_by_second_target_sentence():
    module=importlib.import_module('scripts.ifc_repair.repair_comparison.task_review')
    vertical='洞口下沿距该层标高 850 毫米（世界标高 0.850 米）。'
    request='1．补第一扇窗。\n\n2．补第二扇窗。'+vertical+'\n\n请保留其余墙体。'
    assert vertical not in module._target_paragraph(request,1)
    assert vertical in module._target_paragraph(request,2)


def api():
    return importlib.import_module('scripts.ifc_repair.repair_comparison.task_review')


@pytest.fixture
def review_case(author_source):
    root, source, selection, _ = author_source
    model = ifcopenshell.open(str(source))
    scale = selection.get('unit_to_mm', 1)
    # Complete the deliberately minimal authoring fixture for native EXPRESS.
    person = model.create_entity('IfcPerson', FamilyName='Review fixture')
    org = model.create_entity('IfcOrganization', Name='Review fixture')
    owner = model.create_entity('IfcPersonAndOrganization', ThePerson=person, TheOrganization=org)
    app = model.create_entity('IfcApplication', ApplicationDeveloper=org, Version='1', ApplicationFullName='Review fixture', ApplicationIdentifier='fixture')
    history = model.create_entity('IfcOwnerHistory', OwningUser=owner, OwningApplication=app, ChangeAction='ADDED', CreationDate=1)
    for entity in model.by_type('IfcRoot'):
        entity.OwnerHistory = history
    model.by_type('IfcBuildingStorey')[0].CompositionType = 'ELEMENT'
    project = model.by_type('IfcProject')[0]
    project.Name = 'Technical review fixture'
    model.create_entity('IfcRelAggregates', GlobalId=ifcopenshell.guid.new(), OwnerHistory=history,
        RelatingObject=project, RelatedObjects=[model.by_type('IfcBuildingStorey')[0]])
    wall = model.by_type('IfcWall')[0]
    wall.Representation.Representations[0].Items[0].SweptArea.XDim *= 2
    model.write(str(source))
    selection['assessment_sha256'] = sha256(source)
    row = author_candidate(selection, repository_root=root)
    row['rights_record'] = None
    case = root / 'case'
    prepare_candidate(row, repository_root=root, output=case)
    return root, source, case, row


def test_real_review_passes_without_claiming_human_view(review_case):
    _, source, case, _ = review_case
    before = source.read_bytes()
    result = api().audit_case(case, authorization=AUTHORIZATION, accept=True)
    assert result['passed'] is True
    assert result['checks']['native_recomputed'] is True
    assert result['checks']['public_facts_match_measurements'] is True
    assert result['checks']['retained_reference_geometry_unchanged'] is True
    task = read_json(case / 'private/task.json')
    assert task['review']['status'] == 'accepted_by_delegation'
    assert task['review']['kind'] == 'delegated_technical'
    assert task['review']['reviewer'] == 'Codex'
    assert task['review']['human_viewed'] is False
    assert task['review']['technical_review_passed'] is True
    assert task['review']['authorization'] == AUTHORIZATION
    audit = read_json(case / 'private/geometry-review.json')
    assert audit['passed'] is True
    assert audit['targets'][0]['requested_dimensions_mm'] == pytest.approx([900, 1200])
    assert audit['targets'][0]['opening_sill_mm'] == pytest.approx(800)
    assert source.read_bytes() == before


def test_accepted_card_binds_same_fact_and_review_stays_current(review_case):
    _, _, case, _ = review_case
    assert api().audit_case(case,authorization=AUTHORIZATION,accept=True)['passed']
    card=read_json(case/'private/answer-card.json')
    assert card['status']=='accepted_by_delegation'
    assert card['authorization']==AUTHORIZATION
    assert api().audit_case(case)['passed']


def test_accept_requires_recorded_user_authorization(review_case):
    _, _, case, _ = review_case
    with pytest.raises(ValueError, match='USER_AUTHORIZATION_REQUIRED'):
        api().audit_case(case, accept=True)
    assert read_json(case / 'private/task.json')['review']['status'] == 'pending_human_review'


def test_green_metadata_cannot_hide_modified_reference(review_case):
    _, _, case, row = review_case
    damaged = case / 'private/mutation/damaged.ifc'
    model = ifcopenshell.open(str(damaged))
    ref_guid = row['task_proposal']['author_expectations']['target-1']['reference_guid']
    ref = model.by_guid(ref_guid)
    coordinates = list(ref.ObjectPlacement.RelativePlacement.Location.Coordinates)
    coordinates[0] += 1
    ref.ObjectPlacement.RelativePlacement.Location.Coordinates = coordinates
    model.write(str(damaged))
    (case / 'public/model.ifc').write_bytes(damaged.read_bytes())
    task = read_json(case / 'private/task.json')
    task['damaged_sha256'] = sha256(damaged)
    write_json(case / 'private/task.json', task)
    assert all(read_json(case / 'private/checks.json')['checks'].values())
    result = api().audit_case(case, authorization=AUTHORIZATION, accept=True)
    assert result['passed'] is False
    assert result['checks']['retained_reference_geometry_unchanged'] is False
    assert read_json(case / 'private/task.json')['review']['status'] != 'accepted_by_delegation'


def test_changed_public_request_invalidates_previous_review(review_case):
    _, _, case, _ = review_case
    api().audit_case(case, authorization=AUTHORIZATION, accept=True)
    # A read-only refresh must not erase the original acceptance binding.
    assert api().audit_case(case)['passed'] is True
    task = read_json(case / 'private/task.json')
    task['request'] += '\n修改后的新要求。'
    task['source']['task_proposal']['public_request'] = task['request']
    write_json(case / 'private/task.json', task)
    (case / 'public/request.txt').write_text(task['request'], encoding='utf-8')
    result = api().audit_case(case, authorization=AUTHORIZATION, accept=True)
    assert result['passed'] is False
    assert 'REVIEW_BINDING_STALE' in result['errors']
    assert read_json(case / 'private/task.json')['review']['status'] == 'stale_review'


def test_author_number_is_checked_against_actual_source(review_case):
    _, _, case, _ = review_case
    task = read_json(case / 'private/task.json')
    for proposal in [task, task['source']['task_proposal']]:
        proposal['author_expectations']['target-1']['width_mm'] = 950
        proposal['public_numeric_spec']['targets'][0]['width_mm'] = 950
    task['request'] = task['request'].replace('名义宽 900', '名义宽 950')
    task['source']['task_proposal']['public_request'] = task['request']
    write_json(case / 'private/task.json', task)
    (case / 'public/request.txt').write_text(task['request'], encoding='utf-8')
    result = api().audit_case(case, authorization=AUTHORIZATION, accept=True)
    assert result['passed'] is False
    assert result['checks']['public_facts_match_measurements'] is False


def test_missing_author_contract_blocks_acceptance(review_case):
    _, _, case, _ = review_case
    task = read_json(case / 'private/task.json')
    del task['author_expectations']
    write_json(case / 'private/task.json', task)
    result = api().audit_case(case, authorization=AUTHORIZATION, accept=True)
    assert result['passed'] is False
    assert 'AUTHOR_CONTRACT_MISSING_OR_CHANGED' in result['errors']


def test_sill_clarification_has_two_real_feasible_heights_and_frozen_answer(review_case):
    root, _, case, row = review_case
    row = copy.deepcopy(row)
    row['candidate_slot'] = 'formal-013'
    drafted = api().enable_sill_clarification(row, repository_root=root)
    proposal = drafted['task_proposal']
    assert proposal['clarification_required'] is True
    card = proposal['clarification']
    fact_id = 'target-1.opening_bottom_world_m'
    assert card['required_user_facts'] == [fact_id]
    fact = card['facts'][fact_id]
    assert fact['alternative_feasibility']['passed'] is True
    assert '洞口下沿距该层标高 800' not in proposal['public_request']
    assert '800' in fact['answer']
    assert fact['keywords'] == ['窗台', '下沿', '标高', '高度', 'height', 'sill']
    assert '必须问' not in proposal['public_request']
    prepare_candidate(drafted, repository_root=root, output=root / 'clarification-case')
    # The preparer carries this contract in the integrated path; set it here as
    # an explicit boundary fixture while that separate module is being updated.
    package = root / 'clarification-case'
    task = read_json(package / 'private/task.json')
    task['clarification'] = card
    write_json(package / 'private/task.json', task)
    write_json(package / 'private/answer-card.json', card)
    result = api().audit_case(package, authorization=AUTHORIZATION, accept=True)
    assert result['passed'] is True
    assert result['clarification']['passed'] is True


def test_explicit_legacy_public_spans_are_checked_without_rewriting_language(review_case):
    _, _, case, _ = review_case
    task = read_json(case / 'private/task.json')
    spans = {'dimensions': '请补一扇宽900毫米、高1200毫米的窗。',
        'location': '位置在标高1.000米楼层，平面坐标（2.000，0.000）米。',
        'reference': '外观以平面坐标（5.000，0.000）米的现存窗为准。',
        'vertical': '窗洞下沿距楼层800毫米，世界标高1.800米。'}
    request = ''.join(spans.values())
    task['request'] = task['source']['task_proposal']['public_request'] = request
    for proposal in [task, task['source']['task_proposal']]:
        proposal['author_expectations']['target-1']['public_fact_spans'] = spans
    write_json(case / 'private/task.json', task)
    (case / 'public/request.txt').write_text(request, encoding='utf-8')
    assert api().audit_case(case)['passed'] is True


def test_public_wall_thickness_rule_derives_both_sides_without_gold_sign_choice():
    identity = [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]
    target = {'kind': 'door', 'host_placement_world_m': identity, 'host_thickness_m': .16}
    ref = {'host_thickness_m': .25}
    text = '门框相对于目标墙面的进出位置按参照门相对于其墙面的方式安装，并适配墙厚；左右开启均可。'
    rule = {'kind': 'public_wall_face_alignment', 'reference_wall_thickness_m': .25,
        'target_wall_thickness_m': .16, 'public_text': text}
    allowed, errors = api().allowed_center_offsets(target, ref, [0,.1,0], {'installation_rule': rule}, text)
    assert errors == []
    assert any(offset == pytest.approx([0,.055,0]) for offset in allowed)
    assert any(offset == pytest.approx([0,-.055,0]) for offset in allowed)
    rule['target_wall_thickness_m'] = .25
    _, errors = api().allowed_center_offsets(target, ref, [0,.1,0], {'installation_rule': rule}, text)
    assert errors == ['PUBLIC_WALL_THICKNESS_RULE_INVALID']
