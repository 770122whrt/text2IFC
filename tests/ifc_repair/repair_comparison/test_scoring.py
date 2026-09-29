"""Evaluator-only controls; reference-derived files are never model evidence."""
import importlib
from pathlib import Path
import ifcopenshell
import ifcopenshell.guid
from ifcopenshell.api.root import remove_product
from ifcopenshell.util.element import copy as copy_entity
import pytest

CASES = Path(__file__).resolve().parents[3] / 'dataset/processed/ifc-repair/repair-comparison/development'


def scorer():
    path = Path(__file__).resolve().parents[3] / 'scripts/ifc_repair/repair_comparison/scoring.py'
    assert path.exists(), 'Independent scorer is not implemented'
    return importlib.import_module('scripts.ifc_repair.repair_comparison.scoring')


@pytest.mark.parametrize('case_id', ['case-001', 'case-002'])
def test_reference_control_with_new_guid_and_step_numbers(tmp_path, case_id):
    mod = scorer()
    case = CASES / case_id
    import json
    spec = json.loads((case / 'private/task.json').read_text(encoding='utf-8'))
    model = ifcopenshell.open(str(case / 'private/reference.ifc'))
    model.by_guid(spec['definition']['damage']['target_guid']).GlobalId = ifcopenshell.guid.new()
    path = tmp_path / 'control.ifc'
    # STEP renumbering/serialization is not the matching key.
    rewritten = ifcopenshell.file(schema=model.schema)
    for entity in reversed(list(model)):
        rewritten.add(entity)
    rewritten.write(str(path))
    result = mod.score(case, path, terminal='submitted')
    assert result['repair_success'] is True, result
    assert result['evidence_class'] == 'offline_development_evaluation'


@pytest.mark.parametrize('case_id', ['case-001', 'case-002'])
def test_unrepaired_and_no_output_keep_denominators(case_id):
    case = CASES / case_id
    for path, terminal in [(case / 'public/model.ifc', 'submitted'), (None, 'no_output')]:
        result = scorer().score(case, path, terminal=terminal)
        assert result['repair_success'] is False
        assert result['products']['required'] == 1 and result['products']['correct'] == 0
        assert result['relations']['required'] == (3 if case_id == 'case-001' else 2)


@pytest.mark.parametrize('mutation', ['width', 'missing_fill', 'other_deleted', 'duplicate', 'no_geometry', 'other_property', 'wrong_host'])
def test_adversarial_results_are_not_success(tmp_path, mutation):
    mod = scorer()
    case = CASES / 'case-002'
    import json
    spec = json.loads((case / 'private/task.json').read_text(encoding='utf-8'))
    model = ifcopenshell.open(str(case / 'private/reference.ifc'))
    target = model.by_guid(spec['definition']['damage']['target_guid'])
    if mutation == 'width':
        target.OverallWidth += .2
    elif mutation == 'missing_fill':
        model.remove(target.FillsVoids[0])
    elif mutation == 'other_deleted':
        remove_product(model, product=model.by_guid(spec['definition']['task']['reference_guids'][1]))
    elif mutation == 'duplicate':
        copy_entity(model, target)
    elif mutation == 'no_geometry':
        target.Representation = None
    elif mutation == 'other_property':
        model.by_guid(spec['definition']['task']['reference_guids'][1]).Description = 'unexpected'
    elif mutation == 'wrong_host':
        target.FillsVoids[0].RelatingOpeningElement = next(o for o in model.by_type('IfcOpeningElement') if o.GlobalId != target.FillsVoids[0].RelatingOpeningElement.GlobalId)
    path = tmp_path / 'control.ifc'
    model.write(str(path))
    result = mod.score(case, path, terminal='submitted')
    assert result['repair_success'] is False, result


def test_waiting_is_pending_and_invalid_artifact_is_failure(tmp_path):
    mod = scorer()
    case = CASES / 'case-002'
    assert mod.score(case, None, terminal='awaiting_user')['status'] == 'pending'
    path = tmp_path / 'bad.ifc'
    path.write_text('not IFC', encoding='utf-8')
    result = mod.score(case, path, terminal='submitted')
    assert result['repair_success'] is False
    assert result['checks']['reopen'] is False


def test_clarification_is_separate_from_repair_success():
    mod = scorer()
    assert mod.clarification_score(['location'], [])['success'] is False
    events = [{'kind': 'answer', 'payload': {'requested_fact_ids': ['location'], 'answered_fact_ids': ['location']}}]
    assert mod.clarification_score(['location'], events)['success'] is True
    assert mod.clarification_score([], [])['status'] == 'not_applicable'


def test_task_fact_ids_and_no_output_interaction_are_scored_independently(monkeypatch):
    mod = scorer()
    case = CASES / 'case-002'
    spec = mod.read_json(case / 'private/task.json')
    spec['definition']['clarification']['required_user_facts'] = [{'fact_id': 'location'}]
    monkeypatch.setattr(mod, 'read_json', lambda _: spec)
    events = [{'kind': 'answer', 'payload': {'requested_fact_ids': ['location'], 'answered_fact_ids': ['location']}}]
    report = mod.score(case, None, terminal='no_output', events=events)
    assert report['clarification']['success'] is True
    assert report['repair_success'] is False
    assert report['interaction_success'] is False


def test_internal_evaluator_failure_is_not_a_model_failure(monkeypatch):
    mod = scorer()
    def fail(_):
        raise RuntimeError('evaluator failed')
    monkeypatch.setattr(mod, 'native_validation', fail)
    case = CASES / 'case-002'
    report = mod.score(case, case / 'public/model.ifc', terminal='submitted')
    assert report['status'] == 'not_evaluable'
    assert report['repair_success'] is None
    assert report['interaction_success'] is None
    assert report['products']['required'] == 1
