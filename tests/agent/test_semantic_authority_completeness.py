"""Missing extraction is not authority to erase candidate semantics (offline)."""
import copy
import json

import pytest

from text2ifc_agent.semantic_requirements import project_semantic_requirements
from text2ifc_agent.semantic_correction import build_semantic_correction
from tests.agent.test_generation_semantic_correction import fixture


KINDS = ('material', 'property', 'type', 'appearance', 'template')


def review(**specified):
    return {kind: {'status': 'specified' if kind in specified else 'not_specified',
                   'source_turns': ['turn-user-001']}
            for kind in KINDS}


@pytest.mark.parametrize('layout', ['missing', 'notes', 'nested'])
@pytest.mark.parametrize('field', ['materials', 'property_sets', 'appearance'])
def test_missing_authority_never_permits_cleanup(layout, field):
    candidate, brief, expected, wall, *_ = fixture()
    known = {'notes': 'Use the explicitly requested values'} if layout == 'notes' else (
        {'design': {'policy': 'Preserve explicit semantic requirements'}} if layout == 'nested' else {})
    brief['known_facts'] = known
    wall[field] = {'materials': [{'kind': 'single_material', 'name': 'Requested'}],
                   'property_sets': {'Pset_WallCommon': {'FireRating': '60'}},
                   'appearance': {'color': [.1, .2, .3]}}[field]
    expected.pop('semantic_expectations')
    projected = project_semantic_requirements(brief)
    assert not projected['valid']
    assert any(i['code'] == 'SEMANTIC_AUTHORITY_INCOMPLETE' for i in projected['issues'])
    actual = f'/entities/{wall["id"]}/{field}'
    if field == 'property_sets':
        actual += '/Pset_WallCommon/FireRating'
    plan = build_semantic_correction(candidate=candidate, design_brief=brief, expected_facts=expected,
        issues=[{'issue_id': 'frozen-error', 'actual_ref': actual}])
    assert not plan['edits']


def test_explicit_legacy_empty_array_remains_distinct_from_missing():
    assert project_semantic_requirements({'schema_version': 'text2ifc/design-brief/2.1',
        'known_facts': {'semantic_requirements': []}})['valid']


@pytest.mark.parametrize('change', ['missing_review', 'missing_category', 'unresolved',
                                  'false_none', 'false_specified', 'outside_canonical'])
def test_new_contract_refuses_partial_or_contradictory_declarations(change):
    brief = {'schema_version': 'text2ifc/design-brief/2.2', 'status': 'ready', 'known_facts': {
        'semantic_requirements': [{'entity_id': 'opaque-element', 'material': {
            'kind': 'single_material', 'name': 'Explicit material'}}],
        'semantic_review': review(material=True)}}
    known = brief['known_facts']
    if change == 'missing_review':
        known.pop('semantic_review')
    elif change == 'missing_category':
        known['semantic_review'].pop('property')
    elif change == 'unresolved':
        known['semantic_review']['property']['status'] = 'unresolved'
    elif change == 'false_none':
        known['semantic_review']['material']['status'] = 'not_specified'
    elif change == 'false_specified':
        known['semantic_review']['property']['status'] = 'specified'
    else:
        known['other'] = {'entity_id': 'other', 'property_sets': {'Pset_WallCommon': {'FireRating': '60'}}}
    assert not project_semantic_requirements(brief)['valid']


def test_new_contract_preserves_canonical_values_and_does_not_read_candidate():
    _, brief, _, *_ = fixture()
    brief['schema_version'] = 'text2ifc/design-brief/2.2'
    brief['known_facts']['semantic_review'] = review(material=True, property=True)
    before = copy.deepcopy(brief)
    result = project_semantic_requirements(brief)
    assert result['valid'], result
    assert {e['kind'] for e in result['expectations']} == {'material', 'property'}
    assert brief == before


def valid_brief():
    from tests.agent.test_phase6_1_live import _valid_ready_brief, complete_room_case
    case = complete_room_case()
    brief = _valid_ready_brief(case)
    brief['schema_version'] = 'text2ifc/design-brief/2.2'
    brief['known_facts']['semantic_requirements'] = []
    brief['known_facts']['semantic_review'] = review()
    brief['fact_sources'] = []
    brief['user_corrections'] = []
    brief['provenance']['selected_evidence_ids'] = []
    return case, brief


@pytest.mark.parametrize('attack', ['none', 'geometry', 'original_request', 'unknown_source', 'still_missing'])
def test_bounded_brief_repair_preserves_every_nonsemantic_fact(tmp_path, attack):
    from text2ifc_agent.brief_semantic_repair import repair_semantic_brief
    from tests.agent.test_phase6_5_staged_generation import SequenceProvider
    case, corrected = valid_brief()
    initial = copy.deepcopy(corrected)
    initial['known_facts'].pop('semantic_requirements')
    initial['known_facts'].pop('semantic_review')
    if attack == 'geometry':
        corrected['known_facts']['invented_room_width'] = 9900
    elif attack == 'original_request':
        corrected['original_request'] += ' changed'
    elif attack == 'unknown_source':
        corrected['known_facts']['semantic_review']['material']['source_turns'] = ['invented-turn']
    elif attack == 'still_missing':
        corrected['known_facts'].pop('semantic_requirements')
    provider = SequenceProvider([corrected])
    before = copy.deepcopy(initial)
    result = repair_semantic_brief(provider=provider, output_dir=tmp_path/'repair',
        brief=initial, case=case, evidence_catalog=[], session_id='offline-repair')
    assert result['valid'] is (attack == 'none'), result
    assert len(provider.calls) == 1
    assert initial == before
    assert (tmp_path/'repair/validation.json').is_file()
    assert (tmp_path/'repair/design-brief.json').exists() is (attack == 'none')


@pytest.mark.parametrize('review_enabled', [False, True])
@pytest.mark.parametrize('repair', [False, True])
def test_public_brief_stage_uses_new_contract_and_shared_budget(tmp_path, review_enabled, repair):
    from text2ifc_agent.generation_budget import GenerationBudget, BudgetedProvider
    from text2ifc_agent.live_pipeline import run_design_brief_stage
    from tests.agent.test_phase6_5_staged_generation import SequenceProvider
    case, brief = valid_brief()
    initial = copy.deepcopy(brief)
    if repair:
        initial['known_facts'].pop('semantic_requirements')
    provider = SequenceProvider([initial, brief] if repair else [brief])
    budget = GenerationBudget(tmp_path)
    result = run_design_brief_stage(provider=BudgetedProvider(provider, budget), output_dir=tmp_path/'brief',
        case=case, design_review_enabled=review_enabled, design_brief_schema_version='text2ifc/design-brief/2.2')
    assert result['valid'], result
    assert len(provider.calls) == 1 + repair
    assert len(budget.snapshot()['attempts']) == 1 + repair
    assert json.loads((tmp_path/'brief/design-brief.json').read_text(encoding='utf-8')) == brief
    assert json.loads((tmp_path/'brief/parsed-output.json').read_text(encoding='utf-8')) == initial
    trace = json.loads((tmp_path/'brief/trace-manifest.json').read_text(encoding='utf-8'))
    assert trace['template_id'] == ('design-brief.v2.6' if review_enabled else 'design-brief.v2.5')


def test_semantic_extraction_failure_routes_to_brief_not_user_or_candidate(tmp_path):
    from text2ifc_agent.issue_normalizers import normalize_validation_issues, normalize_gate_sidecars
    from tests.agent.test_semantic_scope_and_type_policy import _write
    issue = {'code': 'SEMANTIC_AUTHORITY_INCOMPLETE', 'path': '/known_facts/semantic_requirements',
             'message': 'Extraction missing'}
    direct = normalize_validation_issues([issue], source='semantic_validation')
    _write(tmp_path/'gate-summary.json', {'overall_status': 'failed',
        'gates': [{'name': 'semantics', 'status': 'failed', 'issues': [issue]}]})
    for row in [*direct, *normalize_gate_sidecars(tmp_path)]:
        assert row.owner == 'design_brief'
        assert row.suggested_route == 'revise_design_brief'


@pytest.mark.parametrize('version', ['2.2', '2.3'])
def test_interactive_invoker_repairs_with_same_budget_and_preserves_initial_trace(tmp_path, version):
    from types import SimpleNamespace
    from text2ifc_agent.interactive_cli_flow import make_openai_design_brief_invoker
    from text2ifc_agent.openai_compat import load_openai_compatible_runtime_config
    case, brief = valid_brief()
    brief['schema_version'] = 'text2ifc/design-brief/' + version
    initial = copy.deepcopy(brief)
    initial['known_facts'].pop('semantic_review')
    payloads = [initial, brief]
    sent = []
    def create(**kwargs):
        sent.append(kwargs)
        payload = {'id': f'fake-{len(sent)}', 'model': 'fake',
            'choices': [{'finish_reason': 'stop', 'message': {'content': json.dumps(payloads.pop(0))}}],
            'usage': {'prompt_tokens': 10, 'completion_tokens': 20, 'total_tokens': 30}}
        return SimpleNamespace(model_dump=lambda: payload)
    config = load_openai_compatible_runtime_config({'TEXT2IFC_PROVIDER': 'deepseek', 'API_KEY': 'fake-key',
        'OPENAI_BASE_URL': 'https://example.invalid', 'TEXT2IFC_DEEPSEEK_MODEL': 'fake'})
    invoke = make_openai_design_brief_invoker(config=config, run_dir=tmp_path,
        design_brief_schema_version=brief['schema_version'],
        client_factory=lambda **_: SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create))))
    result = invoke(case['conversation'], 1)
    assert result.brief == brief
    assert len(sent) == 2
    original = json.loads((tmp_path/'calls/01-design-brief/parsed-output.json').read_text(encoding='utf-8'))
    assert original == initial
    ledger = json.loads((tmp_path/'generation-budget.json').read_text(encoding='utf-8'))
    assert len(ledger['attempts']) == 2
    assert all(a['status'] == 'completed' for a in ledger['attempts'])


def test_brief_repair_must_keep_previously_structured_semantics(tmp_path):
    from text2ifc_agent.brief_semantic_repair import repair_semantic_brief
    from tests.agent.test_phase6_5_staged_generation import SequenceProvider
    case, initial = valid_brief()
    initial['known_facts']['semantic_requirements'] = [{'entity_id': 'wall-requested',
        'material': {'kind': 'single_material', 'name': 'Explicit brick'}}]
    initial['known_facts'].pop('semantic_review')
    replacement = copy.deepcopy(initial)
    replacement['known_facts']['semantic_requirements'] = []
    replacement['known_facts']['semantic_review'] = review()
    result = repair_semantic_brief(provider=SequenceProvider([replacement]), output_dir=tmp_path/'repair',
        brief=initial, case=case, evidence_catalog=[], session_id='preserve-values')
    assert not result['valid']
    assert any(i['code'] == 'BRIEF_SEMANTIC_REPAIR_VALUE_LOSS' for i in result['issues'])
    assert not (tmp_path/'repair/design-brief.json').exists()


def test_candidate_without_any_request_authority_cannot_publish(tmp_path):
    from text2ifc_agent.live_pipeline import run_candidate_gate_stage
    from tests.agent.test_semantic_scope_and_type_policy import _write
    candidate, *_ = fixture()
    for e in candidate['entities']:
        e['materials'], e['property_sets'] = [], {}
    candidate['entities'] = [e for e in candidate['entities'] if not e['ifc_class'].endswith('Type')]
    candidate['relationships'] = [r for r in candidate['relationships'] if r['ifc_class'] != 'IfcRelDefinesByType']
    _write(tmp_path/'generator/candidate.json', candidate)
    result = run_candidate_gate_stage(case_dir=tmp_path, output_dir=tmp_path, case_id='missing-source')
    assert not result['compile_reopen_success']
    assert 'SEMANTIC_AUTHORITY_INCOMPLETE' in json.dumps(result)
    assert not (tmp_path/'output.ifc').exists()


@pytest.mark.parametrize('payload', [None, [], {'known_facts': 'invalid'}, 'truncated {'])
def test_bad_semantic_repair_output_is_retained_and_never_retried(tmp_path, payload):
    from text2ifc_agent.brief_semantic_repair import repair_semantic_brief
    from tests.agent.test_phase6_5_staged_generation import SequenceProvider
    case, initial = valid_brief()
    initial['known_facts'].pop('semantic_review')
    provider = SequenceProvider([payload])
    result = repair_semantic_brief(provider=provider, output_dir=tmp_path/'repair', brief=initial,
        case=case, evidence_catalog=[], session_id='invalid-output')
    assert not result['valid']
    assert len(provider.calls) == 1
    assert (tmp_path/'repair/validation.json').is_file()
    assert not (tmp_path/'repair/design-brief.json').exists()


def test_brief_repair_cannot_reset_or_exceed_shared_call_budget(tmp_path):
    from text2ifc_agent.generation_budget import GenerationBudget, BudgetedProvider, BudgetLimits, GenerationBudgetExceeded
    from text2ifc_agent.live_pipeline import run_design_brief_stage
    from tests.agent.test_phase6_5_staged_generation import SequenceProvider
    case, initial = valid_brief()
    initial['known_facts'].pop('semantic_review')
    provider = SequenceProvider([initial])
    budget = GenerationBudget(tmp_path, BudgetLimits(max_calls=1))
    with pytest.raises(GenerationBudgetExceeded):
        run_design_brief_stage(provider=BudgetedProvider(provider, budget), output_dir=tmp_path/'brief',
            case=case, design_brief_schema_version='text2ifc/design-brief/2.2')
    assert len(provider.calls) == 1
    assert len(budget.snapshot()['attempts']) == 1
    assert (tmp_path/'brief/parsed-output.json').is_file()
    assert not (tmp_path/'brief/design-brief.json').exists()


def test_new_brief_clarification_preserves_user_turns_and_resumes(tmp_path):
    from dataclasses import replace
    from text2ifc_agent.interactive_cli_flow import run_design_brief_clarification_loop
    from text2ifc_agent.session_store import SessionStore
    from tests.agent.test_interactive_cli_flow import _call
    store = SessionStore.open(tmp_path/'sessions.sqlite', artifact_root=tmp_path)
    session = store.create_session(original_input='创建6米乘4米高3米的房间。')
    seen = []
    def invoke(transcript, call_index):
        seen.append(copy.deepcopy(transcript))
        call = _call(call_index, original_request=session.original_input,
            status='needs_clarification' if call_index == 1 else 'ready',
            source_turns=[t['turn_id'] for t in transcript if t['role'] == 'user'])
        brief = copy.deepcopy(call.brief)
        brief['schema_version'] = 'text2ifc/design-brief/2.2'
        brief['known_facts']['semantic_review'] = review()
        return replace(call, brief=brief)
    try:
        result = run_design_brief_clarification_loop(store=store, session=session.session_hash,
            invoke_design_brief=invoke, user_answers=['墙厚200毫米。'])
        assert result.status == 'ready'
        assert len(seen) == 2
        assert seen[1][0] == seen[0][0]
        assert seen[1][-1]['content'] == '墙厚200毫米。'
    finally:
        store.close()


@pytest.mark.parametrize('status', ['ready', 'needs_clarification', None])
def test_unresolved_semantics_never_authorize_cleanup_even_outside_ready(status):
    candidate, brief, expected, *_ = fixture()
    brief['schema_version'] = 'text2ifc/design-brief/2.2'
    brief['status'] = status
    brief['known_facts']['semantic_review'] = review(material=True, property=True)
    brief['known_facts']['semantic_review']['type']['status'] = 'unresolved'
    projection = project_semantic_requirements(brief)
    assert not projection['valid']
    plan = build_semantic_correction(candidate=candidate, design_brief=brief, expected_facts=expected,
        issues=[{'issue_id': 'extra-type', 'actual_ref': '/entities/sample-definition'}])
    assert not plan['edits']
