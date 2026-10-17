"""Bounded diagnostics survive the public API/worker/ledger/export boundary."""
import copy
import json

import pytest

from text2ifc_ifc_repair.api import RepairAPI
from tests.ifc_repair.test_window_installation_anchor import scene
from tests.ifc_repair.repair_comparison.test_compact_task_results import _task
from scripts.ifc_repair.repair_comparison.results import export_task


def diagnostic():
    return {'schema_version': 'text2ifc/scene-diagnostics/0.1',
        'terminal_reason': 'SCENE_GROUNDING_EXHAUSTED',
        'rounds': [{'round': 1, 'action': 'intent', 'stage': 'schema', 'outcome': 'invalid',
                    'issue_codes': ['SCENE_RESPONSE_SCHEMA_INVALID'],
                    'issue_paths': ['/bindings'], 'context_bytes': 1234}]}


def failed_api(tmp_path, monkeypatch):
    model = scene(extension=0.)[0]
    source = tmp_path / 'input.ifc'
    model.write(str(source))
    api = RepairAPI(tmp_path / 'api', provider=object(), scene_grounding=True)
    monkeypatch.setattr(api, '_generate_intent', lambda **_: {
        'valid': False, 'intent': None, 'error_code': 'SCENE_GROUNDING_EXHAUSTED',
        'scene_diagnostics': diagnostic()})
    result = api.start(source, 'Repair the public window.')
    return api, result


def test_failed_public_api_retains_diagnostics_in_hashed_transition_and_evidence(tmp_path, monkeypatch):
    api, result = failed_api(tmp_path, monkeypatch)
    assert not result.successful_artifact_publishable
    assert api.read_scene_diagnostics(result.run_id) == diagnostic()
    state = api.store.load(result.run_id)
    assert state.transitions[-1].to_dict()['stage_payload']['scene_diagnostics'] == diagnostic()
    evidence = json.loads((api.store.runs_root / result.run_id / result.artifacts['evidence']).read_text(encoding='utf8'))
    assert evidence['evidence']['scene_diagnostics'] == diagnostic()
    # The registered public RunResult contract stays unchanged.
    assert 'scene_diagnostics' not in result.to_dict()


def test_api_worker_ledger_export_keeps_failure_fields_without_extra_files(tmp_path, monkeypatch):
    from scripts.ifc_repair.repair_comparison.isolated_b import _scene_diagnostics
    from scripts.ifc_repair.repair_comparison.demo_workflow import _harness_native_record
    api, result = failed_api(tmp_path, monkeypatch)
    native = {'result': result.to_dict(), 'scene_diagnostics': _scene_diagnostics(api, result.run_id)}
    root, run_id, _ = _task(tmp_path, status='no_output', native=_harness_native_record(native, 'test-volume'), native_envelope=True)
    exported = export_task(root, tmp_path / 'results', run_id)
    assert exported['scene_diagnostics'] == diagnostic()
    leaf = tmp_path / 'results/case-001/B'
    assert [p.name for p in leaf.iterdir()] == ['report.md']
    text = (leaf / 'report.md').read_text(encoding='utf8')
    assert '/bindings' in text and 'SCENE_RESPONSE_SCHEMA_INVALID' in text
    assert (leaf / 'report.md').stat().st_size <= 65536


@pytest.mark.parametrize('change', ['extra', 'too_many', 'oversized', 'invalid_path'])
def test_diagnostic_contract_rejects_raw_or_unbounded_content(change):
    from text2ifc_ifc_repair.scene_diagnostics import checked_scene_diagnostics
    value = copy.deepcopy(diagnostic())
    if change == 'extra': value['raw_response'] = 'must never be exported'
    if change == 'too_many': value['rounds'] *= 9
    if change == 'oversized': value['rounds'][0]['issue_codes'] = ['X' * 13000]
    if change == 'invalid_path': value['rounds'][0]['issue_paths'] = ['secret user content']
    with pytest.raises(ValueError, match='SCENE_DIAGNOSTICS_INVALID'):
        checked_scene_diagnostics(value)


def test_legacy_export_labels_missing_diagnostics_without_inventing_failure(tmp_path):
    root, run_id, _ = _task(tmp_path, status='no_output', native={'reason_code': 'SCENE_GROUNDING_EXHAUSTED'})
    result = export_task(root, tmp_path / 'results', run_id)
    assert result['scene_diagnostics'] is None


def test_maximal_valid_diagnostics_export_as_complete_json(tmp_path):
    from text2ifc_ifc_repair.scene_diagnostics import checked_scene_diagnostics
    value = diagnostic()
    value['rounds'] = [dict(value['rounds'][0], round=n,
        issue_codes=['X' * 132] * 5, issue_paths=['/' + 'p' * 131] * 5) for n in range(1, 9)]
    checked_scene_diagnostics(value)
    root, run_id, _ = _task(tmp_path, status='no_output', native={
        'result': {'reason_code': 'SCENE_GROUNDING_EXHAUSTED'}, 'scene_diagnostics': value}, native_envelope=True)
    export_task(root, tmp_path / 'results', run_id)
    report = (tmp_path / 'results/case-001/B/report.md').read_text(encoding='utf8')
    content = report.split('Bounded scene diagnostics (missing means not retained):', 1)[1]
    assert json.loads(content.split('```json', 1)[1].split('```', 1)[0]) == value
    assert len(report.encode('utf8')) <= 65536


def test_clarification_resume_after_api_restart_keeps_prior_and_latest_diagnostics(tmp_path):
    """Actual public API with a deterministic fake Provider; no live model calls."""
    from tests.ifc_repair.test_scene_repair_api import DEVELOPMENT, SceneDemoProvider
    from scripts.ifc_repair.repair_comparison.isolated_b import _scene_diagnostics

    source = DEVELOPMENT / 'case-001/public/model.ifc'
    provider = SceneDemoProvider('window', ask_first=True)
    api = RepairAPI(tmp_path / 'native', provider=provider, scene_grounding=True)
    waiting = api.start(source, '一层西侧长墙第二与第三扇窗中间补窗，高1830毫米，窗台305毫米。')
    assert waiting.status == 'clarification_required', waiting.to_dict()
    prior = api.read_scene_diagnostics(waiting.run_id)
    assert prior['terminal_reason'] == 'clarification_required'
    assert prior['rounds'][-1]['stage'] == 'clarification'
    assert 'scene_diagnostics' not in waiting.to_dict()

    restarted = RepairAPI(tmp_path / 'native', provider=provider)
    assert _scene_diagnostics(restarted, waiting.run_id) == prior
    completed = restarted.continue_with_answer(
        waiting.run_id, {'kind': 'add_detail', 'detail': '宽915毫米。'},
        clarification_id=waiting.clarification.clarification_id,
        expected_state_version=waiting.state_version,
    )
    assert completed.status == 'succeeded', completed.to_dict()
    latest = _scene_diagnostics(restarted, completed.run_id)
    assert latest['terminal_reason'] == 'repair_intent' and latest != prior
    saved = [transition.to_dict()['stage_payload']['scene_diagnostics']
             for transition in restarted.store.load(completed.run_id).transitions
             if 'scene_diagnostics' in transition.stage_payload]
    assert saved[0] == prior and saved[-1] == latest
    assert 'scene_diagnostics' not in completed.to_dict()
