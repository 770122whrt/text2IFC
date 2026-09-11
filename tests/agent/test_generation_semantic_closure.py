"""S2 frozen public-gate family: explicit request values, never self-reported coverage."""
import json
from pathlib import Path

import pytest

from text2ifc_agent.live_pipeline import run_candidate_gate_stage

ROOT = Path(__file__).resolve().parents[2]


def setup_case(tmp_path, actual, expected='60'):
    candidate = json.loads((ROOT / 'tests/contract_v2/fixtures/complete.json').read_text(encoding='utf-8'))
    wall = next(e for e in candidate['entities'] if e['id'] == 'wall-1')
    if actual is not None:
        wall['property_sets']['Pset_WallCommon']['FireRating'] = actual
    (tmp_path / 'generator').mkdir()
    (tmp_path / 'generator/candidate.json').write_text(json.dumps(candidate), encoding='utf-8')
    brief = {'known_facts': {'semantic_requirements': [
        {'entity_id': 'wall-1', 'property_sets': {'Pset_WallCommon': {'FireRating': expected}},
         'source': 'user', 'scope': 'effective'}]}}
    (tmp_path / 'design-brief.json').write_text(json.dumps(brief), encoding='utf-8')
    (tmp_path / 'semantic-coverage.json').write_text(json.dumps({'valid': True, 'facts': [
        {'path': '/known_facts/semantic_requirements/0', 'coverage_state': 'represented'}]}), encoding='utf-8')
    return candidate


@pytest.mark.parametrize('actual', [None, '30'])
def test_public_gate_rejects_missing_or_wrong_value_despite_represented(tmp_path, actual):
    setup_case(tmp_path, actual)
    result = run_candidate_gate_stage(case_dir=tmp_path, output_dir=tmp_path, case_id='frozen-fire-rating')
    assert not result['valid']
    assert result['semantic_verification']['valid'] is False
    assert not result['compile_reopen_success']
    assert not (tmp_path / 'output.ifc').exists()


def test_public_gate_reads_correct_user_declared_value(tmp_path):
    setup_case(tmp_path, '60')
    result = run_candidate_gate_stage(case_dir=tmp_path, output_dir=tmp_path, case_id='frozen-fire-rating')
    assert result['semantic_verification']['valid'] is True
    assert result['compile_reopen_success'] is True


def test_frozen_expectations_cannot_be_replaced_by_candidate(tmp_path):
    setup_case(tmp_path, '30')
    (tmp_path / 'expected-facts.json').write_text(json.dumps({
        'semantic_expectations': [{'entity_id': 'wall-1', 'kind': 'property',
          'pset': 'Pset_WallCommon', 'property': 'FireRating', 'scope': 'effective', 'value': '60'}]
    }), encoding='utf-8')
    result = run_candidate_gate_stage(case_dir=tmp_path, output_dir=tmp_path, case_id='frozen-fire-rating')
    assert result['semantic_verification']['valid'] is False


@pytest.mark.parametrize('change', ['downgrade','theme'])
def test_new_request_contract_cannot_silently_downgrade_or_drop_theme(tmp_path, change):
    candidate = setup_case(tmp_path, '60')
    candidate['schema_version'] = 'bim-json/2.0' if change == 'downgrade' else 'bim-json/2.1'
    for entity in candidate['entities']:
        entity['property_sets'] = {}
    (tmp_path/'generator/candidate.json').write_text(json.dumps(candidate),encoding='utf-8')
    (tmp_path/'design-brief.json').write_text(json.dumps({'schema_version':'text2ifc/design-brief/2.1',
        'known_facts':{'appearance':{'profile':'warm-residential'}, 'semantic_requirements': []}}),encoding='utf-8')
    result = run_candidate_gate_stage(case_dir=tmp_path,output_dir=tmp_path,case_id='contract')
    assert not result['compile_reopen_success']
    assert not (tmp_path/'output.ifc').exists()
