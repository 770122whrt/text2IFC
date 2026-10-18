"""Frozen offline failure-injection family for the public validation loop.

The real public API, Provider renderer/binder, apply, independent production
evaluation and durable publication run. Only the first evaluation's public
decision is fault-injected; this is mechanism evidence, not model capability.
"""
from copy import deepcopy
import json

import pytest

from tests.ifc_repair.test_window_installation_anchor import scene, PublicWindowProvider
from text2ifc_agent.providers import ProviderOutput
from text2ifc_ifc_repair.api import RepairAPI, _executable_changeset_hash
from text2ifc_ifc_repair.evaluation import evaluation_to_dict
from text2ifc_ifc_repair.evaluation_projection import project_public_evaluation
from text2ifc_ifc_repair.production_evaluation import evaluate_production
from text2ifc_ifc_repair.operations import create_default_registry
from text2ifc_ifc_repair.run_models import RunStoreError


def feedback_fixture():
    from text2ifc_ifc_repair.orchestrator import OrchestrationResult
    operation = {'operation_id': 'window-01', 'operation_type': 'add_window_with_opening_to_wall',
        'target': {'wall_global_id': '0'+'a'*21}, 'parameters': {
            'position': {'reference': 'wall_local_start', 'center_offset_mm': 1500},
            'opening': {'sill_height_mm': 700}}}
    report = {'successful_artifact_publishable': False, 'complete_repair_success': False,
        'application': {'status': 'passed'}, 'preservation': {'status': 'passed'}, 'operations': [{
            'operation_id': 'window-01', 'operation_type': operation['operation_type'],
            'levels': [{'level': 'L2', 'status': 'failed', 'checks': [{
                'check_id': 'window.width', 'mandatory': True, 'status': 'failed',
                'difference_category': 'dimension', 'reason': 'PRIVATE_GOLD_REASON',
                'expected': 'PRIVATE_GOLD_EXPECTED', 'actual': 'PRIVATE_GOLD_ACTUAL'}]}]}]}
    return OrchestrationResult(status='l2_failed', changeset={'operations': [operation]}, evaluation=report)


def test_validation_feedback_states_error_and_public_location_without_gold():
    from text2ifc_ifc_repair.api import _public_validation_feedback
    feedback = _public_validation_feedback(feedback_fixture())
    message = feedback[0]['message']
    assert 'dimensions' in message and 'window.width' in message
    assert 'window-01' in message and 'wall_global_id' in message
    assert 'center_offset_mm' in message and '1500' in message and '700' in message
    assert 'PRIVATE_GOLD' not in json.dumps(feedback) and len(message) <= 512


def test_feedback_cannot_assign_error_to_an_unbound_operation():
    from text2ifc_ifc_repair.api import _public_validation_feedback
    result = feedback_fixture()
    result.evaluation['operations'][0]['operation_id'] = 'unoffered-operation'
    assert _public_validation_feedback(result) == []


def test_location_feedback_reaches_existing_prompt_slot(tmp_path):
    api, result, provider, _ = run_case(tmp_path)
    assert result.status == 'succeeded'
    renderer = next((api.store.runs_root/result.run_id).glob('validation-correction-*/attempt-001/renderer-input.json'))
    feedback = json.loads(renderer.read_text(encoding='utf8'))['VALIDATION_FEEDBACK']
    assert 'Location:' in feedback[0]['message'] and 'offline-window-0' in feedback[0]['message']
    assert 'center_offset_mm' in feedback[0]['message']
    assert 'private-canary-evaluator-only' not in ''.join(call['prompt'] for call in provider.calls)


class CorrectionProvider(PublicWindowProvider):
    def __init__(self, *, repeat=False, budget_fail=False):
        super().__init__()
        self.drafts = 0
        self.repeat = repeat
        self.budget_fail = budget_fail

    def generate_candidate(self, **kwargs):
        result = super().generate_candidate(**kwargs)
        if kwargs['state']['stage'] != 'ifc_repair_bound_changeset':
            return result
        self.drafts += 1
        if self.budget_fail and self.drafts > 1:
            raise ValueError('EXPERIMENT_TOKEN_BUDGET_EXHAUSTED')
        body = json.loads(result.text)
        body['draft_id'] = f'offline-draft-{self.drafts}'
        conditions = create_default_registry().require('add_window_with_opening_to_wall').precondition_names
        # Preconditions affect executable checking; random draft IDs do not.
        body['preconditions'] = [] if self.repeat else list(conditions[:self.drafts - 1])
        return ProviderOutput(text=json.dumps(body), metadata=result.metadata)


def run_case(tmp_path, *, failures=1, fault='check', repeat=False, budget_fail=False,
             corrections=2, crash=False):
    model, *_ = scene()
    source = tmp_path / 'damaged.ifc'
    model.write(str(source))
    before = source.read_bytes()
    provider = CorrectionProvider(repeat=repeat, budget_fail=budget_fail)
    reports = []

    def evaluator(inputs):
        report = project_public_evaluation(evaluation_to_dict(evaluate_production(inputs)))
        assert report['successful_artifact_publishable'], report
        reports.append(report)
        if crash and len(reports) == crash:
            raise KeyboardInterrupt('offline crash injection')
        if len(reports) <= failures:
            report = deepcopy(report)
            report.update(status='failed', complete_repair_success=False,
                          successful_artifact_publishable=False, diagnostic_artifact_retained=True)
            if fault == 'preservation':
                report['preservation']['status'] = 'failed'
            elif fault == 'exception':
                raise ValueError('offline evaluator exception')
            else:
                operation = report['operations'][0]
                operation['status'] = 'failed'
                level = next(item for item in operation['levels'] if item['level'] == 'L2')
                level['status'] = 'failed'
                check = next(item for item in level['checks'] if item['mandatory'])
                check.update(status='failed', remediation_required=True)
                check['reason'] = 'Injected public production check failure'
                # Unoffered evaluator fields must never enter Provider feedback.
                check['gold_value'] = 'private-canary-evaluator-only'
                if fault == 'not_evaluable':
                    check['status'] = 'not_evaluable'
                if fault == 'empty':
                    level['checks'] = []
        return report

    api = RepairAPI(tmp_path / 'runs', provider=provider, scene_grounding=True,
                    max_validation_corrections=corrections,
                    orchestrator_options={'evaluation_stage': evaluator})
    if crash:
        with pytest.raises(KeyboardInterrupt):
            api.start(source, 'Add one window using the retained public reference.', run_id='repair-offline-correction')
        result = RepairAPI(tmp_path / 'runs', provider=provider).resume('repair-offline-correction')
    else:
        result = api.start(source, 'Add one window using the retained public reference.', run_id='repair-offline-correction')
    assert source.read_bytes() == before
    return api, result, provider, reports


@pytest.mark.parametrize('corrections,failures,expected,drafts', [(2,1,'succeeded',2),
    (2,2,'succeeded',3), (2,3,'not_publishable',3), (0,1,'not_publishable',1),
    (1,2,'not_publishable',2), (2,0,'succeeded',1)])
def test_public_api_bounded_validation_correction(tmp_path, corrections, failures, expected, drafts):
    api, result, provider, reports = run_case(tmp_path, corrections=corrections, failures=failures)
    assert result.status == expected, result.to_dict()
    assert provider.drafts == drafts
    assert len(reports) == drafts
    assert result.successful_artifact_publishable is (expected == 'succeeded')
    run = api.store.runs_root / result.run_id
    attempts = sorted(run.glob('validation-attempt-*.json'))
    assert len(attempts) == drafts
    assert len(list(run.glob('.terminal-bundles/*'))) == 1
    if failures:
        first = json.loads(attempts[0].read_text(encoding='utf-8'))
        assert first['evaluation']['successful_artifact_publishable'] is False
    if drafts > 1:
        renderers = sorted(run.glob('validation-correction-*/attempt-001/renderer-input.json'))
        assert len(renderers) == drafts - 1
        assert all(json.loads(path.read_text(encoding='utf-8'))['VALIDATION_FEEDBACK'] for path in renderers)
        assert 'private-canary-evaluator-only' not in ''.join(call['prompt'] for call in provider.calls)
    terminal_before = len(provider.calls)
    assert api.read_result(result.run_id).status == expected
    assert len(provider.calls) == terminal_before
    if expected != 'succeeded':
        assert 'successful_ifc' not in result.artifacts


def test_repeated_executable_changeset_stops_even_with_new_draft_id(tmp_path):
    api, result, provider, reports = run_case(tmp_path, repeat=True)
    assert result.status == 'not_publishable'
    assert result.reason_code == 'VALIDATION_CHANGESET_REPEATED'
    assert provider.drafts == 2 and len(reports) == 1
    assert (api.store.runs_root / result.run_id / 'changeset-correction-001.json').is_file()


@pytest.mark.parametrize('fault', ['preservation', 'exception', 'not_evaluable', 'empty'])
def test_safety_or_unusable_feedback_is_not_sent_back(tmp_path, fault):
    api, result, provider, reports = run_case(tmp_path, fault=fault)
    assert not result.successful_artifact_publishable
    assert provider.drafts == 1 and len(reports) == 1
    assert not list((api.store.runs_root / result.run_id).glob('validation-correction-*'))


def test_budget_failure_keeps_original_failure_and_stops(tmp_path):
    api, result, provider, reports = run_case(tmp_path, budget_fail=True)
    assert result.status == 'provider_failed'
    assert result.reason_code == 'EXPERIMENT_TOKEN_BUDGET_EXHAUSTED'
    assert provider.drafts == 2 and len(reports) == 1
    assert (api.store.runs_root / result.run_id / 'validation-attempt-001.json').is_file()
    assert 'successful_ifc' not in result.artifacts


@pytest.mark.parametrize('crash', [1, 2])
def test_crash_recovery_terminates_without_provider_replay(tmp_path, crash):
    api, result, provider, _ = run_case(tmp_path, crash=crash)
    assert result.status == 'not_publishable'
    assert result.reason_code == 'VALIDATION_EXECUTION_INTERRUPTED'
    assert provider.drafts == crash
    assert 'successful_ifc' not in result.artifacts
    if crash == 2:
        assert (api.store.runs_root / result.run_id / 'validation-attempt-001.json').is_file()


def test_source_tampering_after_evaluation_blocks_feedback_and_publication(tmp_path):
    model, *_ = scene()
    source = tmp_path / 'damaged.ifc'
    model.write(str(source))
    provider = CorrectionProvider()

    def mutate_source(inputs):
        report = project_public_evaluation(evaluation_to_dict(evaluate_production(inputs)))
        assert report['successful_artifact_publishable']
        with source.open('ab') as stream:
            stream.write(b'\n/* injected source change */\n')
        report.update(status='failed', complete_repair_success=False,
                      successful_artifact_publishable=False)
        report['operations'][0]['levels'][1]['status'] = 'failed'
        return report

    api = RepairAPI(tmp_path / 'runs', provider=provider, scene_grounding=True,
                    orchestrator_options={'evaluation_stage': mutate_source})
    with pytest.raises(RunStoreError, match='RUN_SOURCE_CHANGED'):
        api.start(source, 'Add a window using the retained public reference.', run_id='repair-tampered-source')
    assert provider.drafts == 1
    run = api.store.runs_root / 'repair-tampered-source'
    assert (run / 'validation-attempt-001.json').is_file()
    assert not list(run.glob('.terminal-bundles/*'))


def test_prior_failed_candidate_is_hash_bound_after_success(tmp_path):
    api, result, _, _ = run_case(tmp_path)
    run = api.store.runs_root / result.run_id
    record = json.loads((run / 'validation-attempt-001.json').read_text(encoding='utf-8'))
    candidate = run / record['artifacts']['diagnostic_candidate']['path']
    with candidate.open('ab') as stream:
        stream.write(b'\n/* injected evidence tamper */\n')
    with pytest.raises(RunStoreError, match='RUN_TAMPER_DETECTED'):
        api.read_result(result.run_id)


@pytest.mark.parametrize('value', [-1, 3, True, 1.5, '2'])
def test_correction_limit_is_strict_and_finite(tmp_path, value):
    with pytest.raises(ValueError, match='VALIDATION_CORRECTION_LIMIT_INVALID'):
        RepairAPI(tmp_path, provider=object(), max_validation_corrections=value)


def test_changeset_fingerprint_ignores_labels_refs_and_set_order_but_not_execution():
    first = {'changeset_id': 'candidate-1', 'semantic_manifest_ref': 'changeset/a.json',
             'preconditions': ['target_exists', 'source_request_hash_matches'],
             'scope': {'target_ids': ['host-a', 'host-b'], 'forbidden_ids': []},
             'operations': [{'operation_id': 'op', 'parameters': {'width_mm': 900}}]}
    reordered = deepcopy(first)
    reordered.update(changeset_id='candidate-2', semantic_manifest_ref='validation-correction-001/a.json')
    reordered['preconditions'].reverse()
    reordered['scope']['target_ids'].reverse()
    assert _executable_changeset_hash(first) == _executable_changeset_hash(reordered)
    changed = deepcopy(reordered)
    changed['operations'][0]['parameters']['width_mm'] = 901
    assert _executable_changeset_hash(first) != _executable_changeset_hash(changed)


def test_production_feedback_survives_a_malformed_provider_correction(tmp_path):
    from tests.ifc_repair.test_draft_authority_set_semantics import (
        _resolved_operations, _manifest, _draft, MODEL, REQUEST, MANIFEST_HASH,
    )
    from text2ifc_ifc_repair.provider_stage import generate_bound_changeset

    class MalformedThenValid:
        def __init__(self):
            self.calls = []

        def generate_candidate(self, **kwargs):
            self.calls.append(kwargs)
            return ProviderOutput(text='{"truncated":' if len(self.calls) == 1 else json.dumps(_draft()),
                                  metadata={'provider': 'offline-fixture'})

    provider = MalformedThenValid()
    feedback = [{'code': 'PRODUCTION_CHECK_FAILED', 'path': '/operations/0/levels/1/checks/0',
                 'message': 'Mandatory public production check l2.beam-material failed.'}]
    result = generate_bound_changeset(provider=provider, case_id='feedback-retry',
        repair_request='Add a resolved beam and column.', source_request_hash=REQUEST,
        resolved_operations=_resolved_operations(), model_fingerprint=MODEL,
        registry=create_default_registry(), output_dir=tmp_path,
        semantic_manifests=(_manifest('beam-1','add_beam'),_manifest('column-1','add_column')),
        semantic_manifest_hashes={'beam-1':MANIFEST_HASH,'column-1':MANIFEST_HASH},
        validation_feedback=feedback)
    assert result['valid'], result
    assert len(provider.calls) == 2
    second = json.loads((tmp_path / 'attempt-002/renderer-input.json').read_text(encoding='utf-8'))
    assert second['VALIDATION_FEEDBACK'][0] == feedback[0]
    assert len(second['VALIDATION_FEEDBACK']) > 1
