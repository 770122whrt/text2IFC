"""Model echo formatting must not replace the saved human request."""
import copy
import json

import pytest

from tests.agent.test_component_requirements_v26 import component_brief


SOURCE = '门宽 850 mm。\n\n\n\n窗高 1100 mm。\n'
ECHO = SOURCE.replace('\n\n\n\n', '\n\n\n')


@pytest.mark.parametrize('echo', [ECHO, '__TEXT2IFC_SAVED_REQUEST_V1__'])
def test_public_invoker_restores_only_repeated_blank_lines_and_keeps_raw_response(tmp_path, echo):
    from tests.ifc2text.test_component_public_chain_v10 import fake_brief_invoker
    from text2ifc_agent.interactive_cli_flow import run_design_brief_clarification_loop
    from text2ifc_agent.session_store import SessionStore
    brief = component_brief()
    brief['original_request'] = echo
    before = copy.deepcopy(brief)
    requests = []
    with SessionStore.open(tmp_path/'sessions.sqlite', artifact_root=tmp_path) as store:
        session = store.create_session(original_input=SOURCE)
        result = run_design_brief_clarification_loop(store=store, session=session.session_id,
            invoke_design_brief=fake_brief_invoker(session.run_dir, brief, requests), user_answers=())
        assert result.status == 'ready' and len(requests) == 1
        saved = json.loads((session.run_dir/'design-brief.json').read_text(encoding='utf-8'))
        assert saved == {**brief, 'original_request': SOURCE}
        assert store.get_session(session.session_id).original_input == SOURCE
        call = session.run_dir/'calls/01-design-brief'
        assert json.loads((call/'request-echo-input.json').read_text(encoding='utf-8')) == before
        trace = json.loads((call/'request-echo-normalization.json').read_text(encoding='utf-8'))
        assert trace['changed_paths'] == ['/original_request']
        assert trace['extra_provider_calls'] == 0
        assert json.loads((call/'model-text.txt').read_text(encoding='utf-8')) == before
        assert brief == before


@pytest.mark.parametrize('echo', [SOURCE, ECHO, SOURCE.replace('\n\n\n\n', '\n\n')])
def test_normalizer_is_idempotent_and_leaves_all_facts_unchanged(echo):
    from text2ifc_agent.brief_request_echo import normalize_request_echo
    brief = component_brief(); brief['original_request'] = echo
    before = copy.deepcopy(brief)
    result, changed = normalize_request_echo(brief, SOURCE)
    assert result == {**brief, 'original_request': SOURCE}
    assert changed is (echo != SOURCE)
    assert normalize_request_echo(result, SOURCE) == (result, False)
    assert brief == before


@pytest.mark.parametrize('change', ['dimension', 'word', 'indent', 'paragraph', 'space-line',
                                  'leading-space', 'trailing-newline', 'legacy', 'missing', 'fenced'])
def test_content_or_structural_changes_are_not_repaired(change):
    from text2ifc_agent.brief_request_echo import normalize_request_echo
    brief = component_brief(); brief['original_request'] = ECHO
    source = SOURCE
    if change == 'dimension': brief['original_request'] = ECHO.replace('850', '900')
    elif change == 'word': brief['original_request'] = ECHO.replace('门', '墙')
    elif change == 'indent': brief['original_request'] = ECHO.replace('窗', '  窗')
    elif change == 'paragraph': brief['original_request'] = ECHO.replace('\n\n\n', '\n')
    elif change == 'space-line': brief['original_request'] = ECHO.replace('\n\n\n', '\n \n')
    elif change == 'leading-space': brief['original_request'] = ' '+ECHO
    elif change == 'trailing-newline': brief['original_request'] = ECHO.rstrip('\n')
    elif change == 'legacy': brief['schema_version'] = 'text2ifc/design-brief/2.8'
    elif change == 'missing': brief.pop('original_request')
    elif change == 'fenced':
        source = '```\n'+SOURCE+'```'; brief['original_request'] = '```\n'+ECHO+'```'
    assert normalize_request_echo(brief, source) == (brief, False)


def test_changed_dimension_still_blocks_public_controller(tmp_path):
    from tests.ifc2text.test_component_public_chain_v10 import fake_brief_invoker
    from text2ifc_agent.interactive_cli_flow import run_design_brief_clarification_loop
    from text2ifc_agent.session_store import SessionStore
    from text2ifc_agent.clarification import ClarificationError
    brief = component_brief(); brief['original_request'] = ECHO.replace('850', '900')
    requests = []
    with SessionStore.open(tmp_path/'sessions.sqlite', artifact_root=tmp_path) as store:
        session = store.create_session(original_input=SOURCE)
        with pytest.raises(ClarificationError, match='changed the original request'):
            run_design_brief_clarification_loop(store=store, session=session.session_id,
                invoke_design_brief=fake_brief_invoker(session.run_dir, brief, requests), user_answers=())
        assert len(requests) == 1 and not list(tmp_path.rglob('*.ifc'))


@pytest.mark.parametrize('echo', [ECHO, '__TEXT2IFC_SAVED_REQUEST_V1__'])
def test_stage_api_restores_the_same_request_echo(tmp_path, echo):
    from text2ifc_agent.live_pipeline import run_design_brief_stage
    from tests.agent.test_semantic_authority_completeness import valid_brief
    from tests.agent.test_phase6_5_staged_generation import SequenceProvider
    case, _ = valid_brief(); brief = component_brief()
    case['user_request'] = SOURCE
    case['conversation'][0]['content'] = SOURCE
    brief['original_request'] = echo
    result = run_design_brief_stage(provider=SequenceProvider([brief]), output_dir=tmp_path/'stage',
        case=case, design_brief_schema_version='text2ifc/design-brief/2.9')
    assert result['valid']
    saved = json.loads((tmp_path/'stage/design-brief.json').read_text(encoding='utf-8'))
    assert saved == {**brief, 'original_request': SOURCE}
    assert json.loads((tmp_path/'stage/request-echo-input.json').read_text(encoding='utf-8')) == brief


@pytest.mark.parametrize('template,accepted', [('design-brief.v2.30', False),
    ('design-brief.v2.31', False), ('design-brief.v2.32', True), ('design-brief.v2.33', True), ('', False)])
def test_saved_request_reference_is_explicitly_versioned(template, accepted):
    from text2ifc_agent.brief_request_echo import normalize_request_echo
    brief = component_brief(); brief['original_request'] = '__TEXT2IFC_SAVED_REQUEST_V1__'
    result, changed = normalize_request_echo(brief, SOURCE, template_id=template)
    assert changed is accepted
    assert result == ({**brief, 'original_request': SOURCE} if accepted else brief)


def test_new_prompt_asks_for_reference_instead_of_copying_saved_text():
    from pathlib import Path
    from text2ifc_agent.design_brief import design_brief_template_id
    for review, version in [(False, '2.32'), (True, '2.33')]:
        assert design_brief_template_id('text2ifc/design-brief/2.9', design_review_enabled=review) == 'design-brief.v'+version
        prompt = Path('prompts/agent/design-brief-v'+version+'.md').read_text(encoding='utf-8')
        assert '__TEXT2IFC_SAVED_REQUEST_V1__' in prompt
        assert 'original_request MUST exactly equal CONVERSATION[0].content' not in prompt
