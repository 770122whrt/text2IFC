"""B adapter exercises the unchanged native facade with offline responses."""
import importlib
from pathlib import Path
import pytest

from scripts.ifc_repair.repair_comparison.direct_runner import DirectRunner

CASES = Path(__file__).resolve().parents[3] / 'dataset/processed/ifc-repair/repair-comparison/development'
BUDGET = {'tokens': 10000, 'calls': 20, 'active_seconds': 600, 'tool_seconds': 30, 'extensions': []}


def adapter():
    path = Path(__file__).resolve().parents[3] / 'scripts/ifc_repair/repair_comparison/ours_adapter.py'
    assert path.exists(), 'B native adapter is not implemented'
    return importlib.import_module('scripts.ifc_repair.repair_comparison.ours_adapter')


def test_real_b_clarification_survives_restart_and_rejects_unoffered_answer(tmp_path):
    module = adapter()
    runner = DirectRunner.create(CASES / 'case-002/public', tmp_path, case_id='case-002', arm='B', budget=BUDGET)
    # Broad public class query intentionally produces native ambiguity; no private IDs.
    provider = module.NativeReplayProvider([module.fixture_intent('door', {'allowed_ifc_classes': ['IfcOpeningElement'], 'storey_name': 'Level 2'}, {'fit_existing_opening': True})])
    ours = module.OursAdapter(tmp_path, runner.run_id)
    state = ours.run(provider, reservation=100)
    assert state['status'] == 'awaiting_user', state
    assert state['native']['result']['clarification']['candidates']
    assert state['usage']['known_total_tokens'] > 0
    restarted = module.OursAdapter(tmp_path, runner.run_id)
    with pytest.raises(ValueError, match='NOT_OFFERED'):
        restarted.answer(text='这个', native_answer={'kind': 'select_candidate', 'candidate_token': 'not-offered'}, event_id='human')
    assert restarted.ledger.snapshot(runner.run_id)['status'] == 'awaiting_user'
    restarted.answer(text='取消本次离线演练', native_answer={'kind': 'cancel'}, event_id='human-cancel')
    terminal = restarted.run(module.NativeReplayProvider([]), reservation=100)
    assert terminal['status'] == 'cancelled' and terminal['artifact'] is None
    assert terminal['usage']['known_total_tokens'] == state['usage']['known_total_tokens']


@pytest.mark.parametrize('case_id', ['case-001', 'case-002'])
def test_native_malformed_provider_failure_kept_without_staging_publication(tmp_path, case_id):
    module = adapter()
    runner = DirectRunner.create(CASES / case_id / 'public', tmp_path, case_id=case_id, arm='B', budget=BUDGET)
    ours = module.OursAdapter(tmp_path, runner.run_id)
    result = ours.run(module.NativeReplayProvider(['{truncated'] * 10), reservation=100)
    assert result['status'] == 'no_output', result
    assert result['artifact'] is None
    assert len(ours.ledger.calls(runner.run_id)) >= 1
    assert result['native']['result']['successful_artifact_publishable'] is False


def test_native_budget_is_checked_before_every_provider_call(tmp_path):
    module = adapter()
    small = {**BUDGET, 'calls': 1}
    runner = DirectRunner.create(CASES / 'case-002/public', tmp_path, case_id='case-002', arm='B', budget=small)
    ours = module.OursAdapter(tmp_path, runner.run_id)
    result = ours.run(module.NativeReplayProvider(['{truncated'] * 10), reservation=100)
    assert result['status'] == 'budget_exhausted'
    assert len(ours.ledger.calls(runner.run_id)) == 1


def test_native_real_metre_door_repair_and_preserved_before_fix_evidence(tmp_path):
    import ifcopenshell
    from scripts.ifc_repair.repair_comparison.inspection import geometry_snapshot
    module = adapter()
    runner = DirectRunner.create(CASES / 'case-002/public', tmp_path, case_id='case-002', arm='B', budget=BUDGET)
    damaged = ifcopenshell.open(str(runner.workspace / 'model.ifc'))
    # Deterministic test oracle derives an identity from PUBLIC D, not reference G.
    candidates = [o for o in damaged.by_type('IfcOpeningElement') if not o.HasFillings and o.VoidsElements
                  and abs(geometry_snapshot(o)['bounds_world_m'][2][0] - 3.1) < .001]
    assert len(candidates) == 1
    intent = module.fixture_intent('door', {'allowed_ifc_classes': ['IfcOpeningElement'], 'global_id': candidates[0].GlobalId}, {'fit_existing_opening': True})
    intent['operations'][0]['parameters']['door'] = {'operation_type': 'SINGLE_SWING_LEFT', 'formal_enum_explicit': True}
    ours = module.OursAdapter(tmp_path, runner.run_id)
    result = ours.run(module.NativeReplayProvider([intent]), reservation=100)
    assert result['status'] == 'submitted', result
    assert result['native']['result']['successful_artifact_publishable'] is True
    assert len(ours.ledger.calls(runner.run_id)) == 2
    repaired = ifcopenshell.open(result['artifact']['path'])
    new_door = next(d for d in repaired.by_type('IfcDoor') if d.GlobalId not in {p.GlobalId for p in damaged.by_type('IfcDoor')})
    assert new_door.OverallWidth == pytest.approx(.864)
    assert new_door.OverallHeight == pytest.approx(2.032)
    assert (CASES / 'case-002/public/model.ifc').read_bytes() == (runner.workspace / 'model.ifc').read_bytes()
    # Frozen negative evidence is preserved separately from the repaired run.
    manifest = Path(__file__).with_name('fixtures') / 'door-metre-before-fix.json'
    import json
    evidence = json.loads(manifest.read_text(encoding='utf-8'))
    text = json.dumps(evidence)
    assert '863136.0' in text and 'DOOR_DIMENSIONS_MATCH' in text


def test_native_replay_cursor_is_persistent_across_add_detail(tmp_path):
    module = adapter()
    import ifcopenshell
    from scripts.ifc_repair.repair_comparison.inspection import geometry_snapshot
    runner = DirectRunner.create(CASES / 'case-002/public', tmp_path, case_id='case-002', arm='B', budget=BUDGET)
    model = ifcopenshell.open(str(runner.workspace / 'model.ifc'))
    opening = next(o for o in model.by_type('IfcOpeningElement') if not o.HasFillings and o.VoidsElements
                   and abs(geometry_snapshot(o)['bounds_world_m'][2][0] - 3.1) < .001)
    incomplete = module.fixture_intent('door', {'allowed_ifc_classes': ['IfcOpeningElement'], 'global_id': opening.GlobalId}, {'fit_existing_opening': True})
    import copy
    complete = copy.deepcopy(incomplete)
    complete['operations'][0]['parameters']['door'] = {'operation_type': 'SINGLE_SWING_LEFT', 'formal_enum_explicit': True}
    transcript = [incomplete, complete]
    ours = module.OursAdapter(tmp_path, runner.run_id)
    first = ours.run(module.NativeReplayProvider(transcript), reservation=100)
    assert first['status'] == 'awaiting_user'
    ours.answer(text='离线夹具指定SINGLE_SWING_LEFT。', native_answer={'kind': 'add_detail', 'detail': '离线夹具指定SINGLE_SWING_LEFT。'}, event_id='detail-1')
    restarted = module.OursAdapter(tmp_path, runner.run_id)
    second = restarted.run(module.NativeReplayProvider(transcript), reservation=100)
    assert second['status'] == 'submitted', second
    assert len(restarted.ledger.calls(runner.run_id)) == 3  # two Intent + one Stage 2; no replay from zero
    assert second['usage']['known_total_tokens'] > first['usage']['known_total_tokens']


def test_native_saved_question_can_recover_before_experiment_pause(tmp_path, monkeypatch):
    module = adapter()
    runner = DirectRunner.create(CASES / 'case-002/public', tmp_path, case_id='case-002', arm='B', budget=BUDGET)
    ours = module.OursAdapter(tmp_path, runner.run_id)
    def crash(*args, **kwargs):
        raise RuntimeError('crash before pause')
    monkeypatch.setattr(ours.ledger, 'ask', crash)
    provider = module.NativeReplayProvider([module.fixture_intent('door', {'allowed_ifc_classes': ['IfcOpeningElement'], 'storey_name': 'Level 2'}, {'fit_existing_opening': True})])
    with pytest.raises(RuntimeError, match='crash'):
        ours.run(provider, reservation=100)
    recovered = module.OursAdapter(tmp_path, runner.run_id).run(module.NativeReplayProvider([]), reservation=100)
    assert recovered['status'] == 'awaiting_user'
    assert len(ours.ledger.calls(runner.run_id)) == 1


def test_native_window_public_input_binding_and_publication(tmp_path):
    import ifcopenshell
    import ifcopenshell.util.placement
    import ifcopenshell.util.unit
    import numpy as np
    from scripts.ifc_repair.repair_comparison.inspection import geometry_snapshot
    module = adapter()
    runner = DirectRunner.create(CASES / 'case-001/public', tmp_path, case_id='case-001', arm='B', budget=BUDGET)
    model = ifcopenshell.open(str(runner.workspace / 'model.ifc'))
    def bounds(product):
        return np.array(geometry_snapshot(product)['bounds_world_m'])
    walls = [(bounds(w)[0].mean(), w) for w in model.by_type('IfcWall')
             if bounds(w)[0, 1] - bounds(w)[0, 0] < .3 and bounds(w)[1, 1] - bounds(w)[1, 0] > 10 and abs(bounds(w)[2, 0]) < .001]
    host = min(walls, key=lambda item: item[0])[1]
    windows = [fill.RelatedBuildingElement for void in host.HasOpenings for fill in void.RelatedOpeningElement.HasFillings if fill.RelatedBuildingElement.is_a('IfcWindow')]
    windows.sort(key=lambda w: bounds(w)[1].mean(), reverse=True)
    center = (bounds(windows[1]).mean(axis=1) + bounds(windows[2]).mean(axis=1)) / 2
    scale = ifcopenshell.util.unit.calculate_unit_scale(model)
    local = np.linalg.inv(ifcopenshell.util.placement.get_local_placement(host.ObjectPlacement)) @ np.append(center / scale, 1.)
    params = {'position': {'reference': 'wall_local_start', 'center_offset_mm': float(local[0] * scale * 1000)},
              'opening': {'width_mm': 915., 'height_mm': 1830., 'sill_height_mm': 305.}, 'window': {'fit_opening': True}}
    intent = module.fixture_intent('window', {'allowed_ifc_classes': ['IfcWall'], 'global_id': host.GlobalId}, params)
    ours = module.OursAdapter(tmp_path, runner.run_id)
    result = ours.run(module.NativeReplayProvider([intent]), reservation=100)
    assert result['status'] == 'submitted', (result, ours.ledger.events(runner.run_id)[-1])
    assert result['native']['result']['successful_artifact_publishable'] is True
