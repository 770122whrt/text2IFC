"""A unit-converted fixture tests B publication; not a scored experiment arm."""
from pathlib import Path
import ifcopenshell
import ifcopenshell.util.unit
from scripts.ifc_repair.repair_comparison.direct_runner import DirectRunner
from scripts.ifc_repair.repair_comparison.ours_adapter import OursAdapter, NativeReplayProvider, fixture_intent
from scripts.ifc_repair.repair_comparison.inspection import geometry_snapshot

REPO = Path(__file__).resolve().parents[3]


def test_b_native_publication_on_millimetre_control(tmp_path):
    original = REPO / 'dataset/processed/ifc-repair/repair-comparison/development/case-002/public'
    public = tmp_path / 'public'
    public.mkdir()
    model = ifcopenshell.util.unit.convert_file_length_units(ifcopenshell.open(str(original / 'model.ifc')), 'MILLIMETER')
    model.write(str(public / 'model.ifc'))
    (public / 'request.txt').write_text('离线单位对照：给二层空门洞补门。', encoding='utf-8')
    opening = next(o for o in model.by_type('IfcOpeningElement') if not o.HasFillings and o.VoidsElements
                   and abs(geometry_snapshot(o)['bounds_world_m'][2][0] - 3.1) < .001)
    intent = fixture_intent('door', {'allowed_ifc_classes': ['IfcOpeningElement'], 'global_id': opening.GlobalId},
                            {'fit_existing_opening': True, 'door': {'operation_type': 'SINGLE_SWING_LEFT', 'formal_enum_explicit': True}})
    runner = DirectRunner.create(public, tmp_path / 'run', case_id='unit-control', arm='B',
                                 budget={'tokens': 1000, 'calls': 10, 'active_seconds': 600, 'tool_seconds': 30, 'extensions': []})
    adapter = OursAdapter(runner.root, runner.run_id)
    result = adapter.run(NativeReplayProvider([intent]), reservation=100)
    assert result['status'] == 'submitted', (result, adapter.ledger.events(runner.run_id)[-1])
    assert result['native']['result']['successful_artifact_publishable'] is True
    assert Path(result['artifact']['path']).is_file()
