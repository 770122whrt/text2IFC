"""Offline tests for explicit polygon-host generation; no live Provider calls."""
import json
from pathlib import Path

import pytest

from text2ifc_agent.generator import validate_generation_document
from text2ifc_agent.live_pipeline import run_generator_stage
from tests.agent.test_phase6_5_staged_generation import SequenceProvider

ROOT = Path(__file__).resolve().parents[2]


def fixture_candidate():
    candidate = json.loads((ROOT / 'tests/contract_v2/fixtures/complete.json').read_text(encoding='utf-8'))
    candidate['schema_version'] = 'bim-json/2.4'
    return candidate


def prepare_source(tmp_path, selected=True):
    source = tmp_path / 'design-brief'
    source.mkdir()
    (source / 'input.txt').write_text('Keep the measured wall polygon and door frame depth.', encoding='utf-8')
    brief = {'schema_version': 'text2ifc/design-brief/2.7', 'status': 'ready',
             'known_facts': {'semantic_requirements': []}}
    for name, value in [('design-brief', brief), ('conversation', []), ('context-selection', {'evidence': []})]:
        (source / (name + '.json')).write_text(json.dumps(value), encoding='utf-8')
    if selected:
        (tmp_path / 'generation-contract.json').write_text(json.dumps({
            'schema_version': 'text2ifc/generation-contract-selection/1.0',
            'bim_json_schema_version': 'bim-json/2.4', 'generation_strategy': 'legacy_full'}), encoding='utf-8')
    return source


def test_v24_classification_uses_new_contract():
    assert validate_generation_document(fixture_candidate())['status'] == 'formal'


@pytest.mark.parametrize('selected', [True, False])
def test_generator_uses_explicit_contract_and_keeps_legacy_default(tmp_path, selected):
    source = prepare_source(tmp_path, selected)
    candidate = fixture_candidate()
    candidate['schema_version'] = 'bim-json/2.4' if selected else 'bim-json/2.3'
    provider = SequenceProvider([candidate])
    result = run_generator_stage(provider=provider, output_dir=tmp_path/'generator',
                                 design_source_dir=source, case_id='version-route')
    assert result['valid'], result
    assert provider.calls[0]['schema']['properties']['schema_version']['const'] == candidate['schema_version']
    rendered = (tmp_path/'generator/prompt-render-input.json').read_text(encoding='utf-8')
    assert ('bim-json-draft/1.4' in rendered) == selected
    if selected:
        prompt = (tmp_path/'generator/prompt-rendered.md').read_text(encoding='utf-8')
        assert 'frame_depth' in prompt
        assert 'BIM JSON 2.4' in prompt


def test_selected_contract_rejects_downgrade(tmp_path):
    source = prepare_source(tmp_path)
    candidate = fixture_candidate()
    candidate['schema_version'] = 'bim-json/2.3'
    result = run_generator_stage(provider=SequenceProvider([candidate]), output_dir=tmp_path/'generator',
                                 design_source_dir=source, case_id='downgrade')
    assert not result['valid']


def test_public_rejects_v24_staged_before_any_provider_call():
    from text2ifc_agent.interactive_cli_flow import run_ready_session_to_ifc
    with pytest.raises(ValueError, match='legacy_full'):
        run_ready_session_to_ifc(store=None, session='unused', provider_factory=lambda: pytest.fail('called'),
                                 generation_strategy='staged', bim_json_schema_version='bim-json/2.4')


def test_public_v24_reaches_final_acceptance_and_reopen(tmp_path):
    import ifcopenshell
    from text2ifc_agent.interactive_cli_flow import run_ready_session_to_ifc
    from text2ifc_agent.session_store import SessionStore
    from tests.agent.test_interactive_cli_generation import (
        _write_ready_design_brief_call, _SequenceLiveProvider, PHASE6_1_COMPLETE)
    store = SessionStore.open(tmp_path/'sessions.sqlite', artifact_root=tmp_path)
    session = store.create_session(original_input='Create the confirmed room with its door and window.')
    _write_ready_design_brief_call(session.run_dir)
    for path in [session.run_dir/'design-brief.json', session.run_dir/'calls/01-design-brief/design-brief.json']:
        brief = json.loads(path.read_text(encoding='utf-8'))
        brief['schema_version'] = 'text2ifc/design-brief/2.1'
        brief['known_facts']['semantic_requirements'] = []
        path.write_text(json.dumps(brief), encoding='utf-8')
    before = (session.run_dir/'design-brief.json').read_bytes()
    store.mark_session_status(session.session_id, 'ready')
    candidate = json.loads((PHASE6_1_COMPLETE/'generator/candidate.json').read_text(encoding='utf-8'))
    candidate['schema_version'] = 'bim-json/2.4'
    audit = {'schema_version': 'text2ifc/audit/2.0', 'recommendation': 'accept', 'blocking': False,
             'deterministic_gate_status': 'passed', 'findings': [],
             'evidence_paths': ['generator/candidate.json']}
    provider = _SequenceLiveProvider([candidate, audit])
    try:
        result = run_ready_session_to_ifc(store=store, session=session.session_id,
            provider_factory=lambda: provider, bim_json_schema_version='bim-json/2.4')
        assert result.status == 'compiled', result
        assert ifcopenshell.open(str(result.ifc_path)).by_type('IfcWall')
        assert (tmp_path/'final-acceptance.json').is_file()
        expected = json.loads((session.run_dir/'expected-facts.json').read_text(encoding='utf-8'))
        assert expected['generation_schema_version'] == 'bim-json/2.4'
        assert (session.run_dir/'design-brief.json').read_bytes() == before
        # Final acceptance reuses these actual gates: an otherwise-valid old
        # contract cannot bypass the persisted selection after generation.
        from text2ifc_agent.live_pipeline import run_candidate_gate_stage
        candidate['schema_version'] = 'bim-json/2.3'
        (session.run_dir/'generator/candidate.json').write_text(json.dumps(candidate), encoding='utf-8')
        downgraded = run_candidate_gate_stage(case_dir=session.run_dir,
            output_dir=tmp_path/'downgrade-gate', case_id='downgrade')
        assert not downgraded['compile_reopen_success']
        semantics = json.loads((tmp_path/'downgrade-gate/request-semantics.json').read_text(encoding='utf-8'))
        assert any(i['code'] == 'REQUEST_CONTRACT_DOWNGRADE' for i in semantics['issues'])
    finally:
        store.close()


def test_ifc2text_bridge_passes_explicit_version(monkeypatch):
    from types import SimpleNamespace
    from text2ifc_ifc2text.text2ifc_public import reconstruct_description_with_public_text2ifc
    import text2ifc_agent.interactive_cli_flow as flow
    seen = {}
    def brief(**kwargs):
        return SimpleNamespace(status='ready', session_id='s', session_hash='h')
    def ready(**kwargs):
        seen.update(kwargs)
        return SimpleNamespace(status='compiled', session_id='s', session_hash='h', ifc_path=Path('out.ifc'),
                               report_path=None, generator_status='formal', audit_status='accept')
    monkeypatch.setattr(flow, 'run_design_brief_clarification_loop', brief)
    monkeypatch.setattr(flow, 'run_ready_session_to_ifc', ready)
    store = SimpleNamespace(create_session=lambda **kwargs: SimpleNamespace(session_id='s'))
    reconstruct_description_with_public_text2ifc('description', store=store,
        invoke_design_brief=lambda *_: None, provider_factory=lambda: None,
        bim_json_schema_version='bim-json/2.4')
    assert seen['bim_json_schema_version'] == 'bim-json/2.4'
    assert 'source_ifc' not in seen and 'source_facts' not in seen


@pytest.mark.parametrize('frame_depth', [60, 100])
def test_frozen_generator_frame_depth_survives_polygon_compile(tmp_path, frame_depth):
    import ifcopenshell
    import numpy as np
    from text2ifc_compiler import compile_document
    from tests.compiler.test_basic_filling import vertices
    from tests.compiler.test_polygon_wall_hosts_v24 import document, record
    source = prepare_source(tmp_path)
    candidate = document()
    record(candidate, 'door-1')['attributes']['Representation']['parameters']['frame_depth'] = frame_depth
    provider = SequenceProvider([candidate])
    result = run_generator_stage(provider=provider, output_dir=tmp_path/'generator',
                                 design_source_dir=source, case_id='frame-depth')
    assert result['valid']
    saved = json.loads((tmp_path/'generator/candidate.json').read_text(encoding='utf-8'))
    compiled = compile_document(saved, tmp_path/'frame.ifc')
    assert compiled.success, compiled.input_issues
    door = ifcopenshell.open(str(compiled.output_path)).by_type('IfcDoor')[0]
    depth_mm = np.ptp(vertices(door), axis=0)[1] * 1000
    assert abs(depth_mm - frame_depth) < 0.1


def test_scoped_repair_v24_can_return_canonical_draft(tmp_path):
    from text2ifc_agent.changeset_stage import run_changeset_stage
    from text2ifc_agent.failure_routing import _is_draft
    draft = {'draft_version': 'bim-json-draft/1.4', 'target_schema_version': 'bim-json/2.4',
             'partial_document': {}, 'missing_facts': [{'entity_id': 'wall-1', 'path': '/geometry',
                 'code': 'MISSING_GEOMETRY', 'message': 'Need a complete polygon.'}],
             'losses': [], 'clarification_targets': [], 'provenance': {'source': 'test'}}
    assert validate_generation_document(draft)['status'] == 'draft'
    assert _is_draft(draft)
    provider = SequenceProvider([draft])
    result = run_changeset_stage(provider=provider, output_dir=tmp_path, case_id='draft', call_index=1,
        user_request='Preserve the wall.', conversation=[], design_brief={}, expected_facts={},
        candidate=fixture_candidate(), base_revision={},
        scope={'entity_ids': ['wall-1'], 'relationship_ids': []}, issues=[])
    assert result['classification'] == 'draft', result
    rendered = json.loads((tmp_path/'prompt-render-input.json').read_text(encoding='utf-8'))
    assert rendered['FORMAL_SCHEMA']['properties']['schema_version']['const'] == 'bim-json/2.4'
    assert rendered['DRAFT_SCHEMA']['properties']['draft_version']['const'] == 'bim-json-draft/1.4'
