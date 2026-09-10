"""Freeze the boundary between structured appearance and narrative review."""
import copy
import json

import pytest

from text2ifc_agent.semantic_requirements import request_contract_issues, request_semantics_for_case


@pytest.mark.parametrize('profile', ['neutral-architectural', 'warm-residential'])
@pytest.mark.parametrize('note', [None, '浅暖墙与深色框，颜色不代表物理材料。', 'Coordinated facade; no material inference.'])
@pytest.mark.parametrize('wrong_profile', [False, True])
def test_narrative_does_not_override_or_invalidate_structured_choice(profile, note, wrong_profile):
    selection = {'profile': profile}
    if note is not None:
        selection['style_notes'] = note
    alternate = 'warm-residential' if profile == 'neutral-architectural' else 'neutral-architectural'
    candidate = {'appearance': {'profile': alternate if wrong_profile else profile}}
    request = {'appearance_requests': [selection]}
    original = copy.deepcopy((candidate, request))
    issues = request_contract_issues(candidate, request)
    assert bool(issues) == wrong_profile
    assert (candidate, request) == original


@pytest.mark.parametrize('actual', ['frozen', 'changed', None])
def test_explicit_seed_is_still_required(actual):
    candidate = {'appearance': {'profile': 'warm-residential'}}
    if actual is not None:
        candidate['appearance']['seed'] = actual
    issues = request_contract_issues(candidate, {'appearance_requests': [
        {'profile': 'warm-residential', 'seed': 'frozen', 'style_notes': '协调配色'}]})
    assert bool(issues) == (actual != 'frozen')


@pytest.mark.parametrize('selection', [
    {'profile': 'unregistered-theme'}, {'seed': 0}, {'seed': None},
    {'profile': 'warm-residential', 'style_notes': {'color': [1, 0, 0]}},
    {'profile': 'warm-residential', 'color': [1, 0, 0]},
    {'profile': 'warm-residential', 'frame_width': 65},
    [], None,
])
def test_unknown_structured_or_malformed_selection_cannot_silently_pass(selection):
    # Matching malformed candidate values must not make an invalid request valid.
    issues = request_contract_issues({'appearance': copy.deepcopy(selection)},
                                    {'appearance_requests': [selection]})
    assert issues
    assert any(i['code'] in {'REQUEST_APPEARANCE_INVALID', 'REQUEST_APPEARANCE_UNSUPPORTED_FIELD'} for i in issues)


@pytest.mark.parametrize('candidate', [{'appearance': None}, {'appearance': []}, {}])
def test_missing_or_malformed_candidate_is_structured_failure(candidate):
    issues = request_contract_issues(candidate, {'appearance_requests': [{'profile': 'warm-residential'}]})
    assert issues and issues[0]['code'] == 'REQUEST_APPEARANCE_MISMATCH'


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')


@pytest.mark.parametrize('changed', [None, 'profile', 'seed'])
def test_resume_keeps_saved_choices_and_narrative_provenance(tmp_path, changed):
    frozen = {'profile': 'warm-residential', 'seed': 'frozen', 'style_notes': '原说明：浅墙深框。'}
    later = {**frozen, 'style_notes': '追加说明：需要人工看近景。'}
    if changed:
        later[changed] = 'neutral-architectural' if changed == 'profile' else 'changed'
    write(tmp_path / 'design-brief.json', {'schema_version': 'text2ifc/design-brief/2.1',
                                          'known_facts': {'appearance': later, 'semantic_requirements': []}})
    write(tmp_path / 'expected-facts.json', {'generation_schema_version': 'bim-json/2.1', 'appearance': frozen})
    original = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    request = request_semantics_for_case(tmp_path)
    assert request['valid']
    assert all('style_notes' not in item for item in request['appearance_requests'])
    assert {item['text'] for item in request['appearance_notes']} == {frozen['style_notes'], later['style_notes']}
    assert all(item['source_path'] for item in request['appearance_notes'])
    candidate = {'schema_version': 'bim-json/2.1', 'appearance': {k: v for k, v in later.items() if k != 'style_notes'}}
    assert bool(request_contract_issues(candidate, request)) == bool(changed)
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == original


def test_notes_only_do_not_create_a_theme_requirement(tmp_path):
    write(tmp_path / 'design-brief.json', {'known_facts': {'appearance': {'style_notes': '协调、整洁，需要视觉检查。'}}})
    request = request_semantics_for_case(tmp_path)
    assert request['valid'] and request['appearance_requests'] == []
    assert request['appearance_notes'][0]['text'] == '协调、整洁，需要视觉检查。'
    assert request_contract_issues({}, request) == []


def test_unsupported_appearance_is_retained_and_blocks_projection(tmp_path):
    write(tmp_path / 'design-brief.json', {'known_facts': {'appearance': {'color': [1, 0, 0]}}})
    original = (tmp_path / 'design-brief.json').read_bytes()
    request = request_semantics_for_case(tmp_path)
    assert not request['valid']
    assert any(i['code'] == 'REQUEST_APPEARANCE_UNSUPPORTED_FIELD' for i in request['issues'])
    assert (tmp_path / 'design-brief.json').read_bytes() == original


def test_note_source_identifies_the_selected_final_brief(tmp_path):
    write(tmp_path / 'design-brief.json', {'known_facts': {'appearance': {'style_notes': '旧副本'}}})
    final = tmp_path / 'design-brief'
    final.mkdir()
    write(final / 'design-brief.json', {'known_facts': {'appearance': {'style_notes': '最终说明'}}})
    request = request_semantics_for_case(tmp_path)
    assert request['appearance_notes'] == [{
        'text': '最终说明', 'source_path': 'design-brief/design-brief.json#/known_facts/appearance/style_notes'}]
