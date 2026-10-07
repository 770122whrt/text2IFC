"""Batch carrier contracts, without Docker or real Provider calls."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest

from scripts.ifc_repair.repair_comparison import demo_workflow as workflow
from scripts.ifc_repair.repair_comparison.contracts import read_json, write_json
from scripts.ifc_repair.repair_comparison.ledger import Ledger


def inputs(tmp_path, count=20):
    cases = tmp_path / 'cases'
    ids = [f'formal-{i:03d}' for i in range(1, count + 1)]
    budgets = {}
    for i, case in enumerate(ids):
        public = cases / case / 'public'
        public.mkdir(parents=True)
        (public / 'model.ifc').write_text(f'public damaged IFC {i}', encoding='utf8')
        (public / 'request.txt').write_text(f'修复第 {i + 1} 题。', encoding='utf8')
        private = cases / case / 'private'
        private.mkdir()
        (private / 'gold.ifc').write_text('PRIVATE-CANARY', encoding='utf8')
        budgets[case] = {**deepcopy(workflow.BUDGET), 'tokens': 300000 + i, 'active_seconds': 300 + i}
    return cases, ids, budgets


@pytest.fixture
def carrier_seams(monkeypatch):
    def bundle(repo, destination):
        destination.mkdir(parents=True)
        (destination / 'worker.py').write_text('runtime only')
    monkeypatch.setattr(workflow, 'build_runtime_bundle', bundle)
    monkeypatch.setattr(workflow, 'bindings', lambda configuration=None: {'bound': deepcopy(configuration)})


def initialize_batch(tmp_path, carrier_seams, count=20, **kwargs):
    cases, ids, budgets = inputs(tmp_path, count)
    root = tmp_path / 'run'
    config = workflow.initialize(root, mode='offline', cases_root=cases, case_ids=ids,
                                 budgets=budgets, stage=workflow.FORMAL_STAGE, **kwargs)
    return root, config, cases, ids, budgets


def test_twenty_case_batch_has_eighty_rotated_public_only_tasks(tmp_path, carrier_seams):
    root, config, cases, ids, budgets = initialize_batch(tmp_path, carrier_seams)
    assert len(config['order']) == len(set(config['order'])) == 80
    assert [run.rsplit('-', 1)[1] for run in config['order'][:16]] == list('ABCDBCDACDABDABC')
    ledger = Ledger(root / 'control.sqlite')
    for case in ids:
        for arm in 'ABCD':
            state = ledger.snapshot(case + '-' + arm)
            assert state['budget'] == budgets[case]
            workspace = Path(state['metadata']['workspace'])
            assert {p.name for p in workspace.iterdir()} == {'model.ifc', 'task.txt', 'work', 'output'}
            assert (workspace / 'model.ifc').read_bytes() == (cases / case / 'public/model.ifc').read_bytes()
            assert 'PRIVATE-CANARY' not in (workspace / 'task.txt').read_text(encoding='utf8')
    ledger.start(ids[0] + '-A')
    with pytest.raises(ValueError, match='OTHER_ACTIVE_TASK'):
        ledger.start(ids[0] + '-B')


def test_formal_rejects_demo_admission_before_creating_workspaces(tmp_path, carrier_seams):
    cases, ids, budgets = inputs(tmp_path, 1)
    admission = tmp_path / 'admission.json'
    write_json(admission, {'stage': 'repair-comparison-two-demo-live', 'passed': True, 'bindings': {}})
    with pytest.raises(ValueError, match='ADMISSION'):
        workflow.initialize(tmp_path / 'run', mode='live', admission=admission,
                            cases_root=cases, case_ids=ids, budgets=budgets, stage=workflow.FORMAL_STAGE)
    assert not (tmp_path / 'run').exists()


def test_formal_admission_binds_exact_configuration(tmp_path, carrier_seams):
    cases, ids, budgets = inputs(tmp_path, 1)
    configuration = workflow.batch_configuration(cases_root=cases, case_ids=ids, budgets=budgets,
                                                stage=workflow.FORMAL_STAGE, scene_grounding=True)
    admission = tmp_path / 'admission.json'
    write_json(admission, {'stage': workflow.FORMAL_STAGE, 'passed': True, 'configuration': configuration,
                          'bindings': workflow.bindings(configuration)})
    assert workflow.verify_admission(admission, configuration)['passed']
    changed = deepcopy(configuration)
    changed['budgets'][ids[0]]['tokens'] += 1
    with pytest.raises(ValueError, match='ADMISSION'):
        workflow.verify_admission(admission, changed)
    config = workflow.initialize(tmp_path / 'live', mode='live', admission=admission,
                                 cases_root=cases, case_ids=ids, budgets=budgets,
                                 stage=workflow.FORMAL_STAGE, scene_grounding=True)
    ledger = Ledger(tmp_path / 'live/control.sqlite')
    assert all(ledger.snapshot(run_id)['mode'] == 'live_formal' for run_id in config['order'])


@pytest.mark.parametrize('entry', ['serve', 'run'])
def test_live_entries_recheck_current_formal_admission(tmp_path, carrier_seams, monkeypatch, entry):
    root, config, *_ = initialize_batch(tmp_path, carrier_seams, count=1)
    admission = tmp_path / 'admission.json'
    write_json(admission, {'stage': workflow.DEMO_STAGE, 'passed': True})
    config.update(mode='live', admission=str(admission))
    write_json(root / 'experiment.json', config)
    monkeypatch.setattr(workflow, 'docker', lambda *a, **k: pytest.fail('rejected admission reached Docker'))
    with pytest.raises(ValueError, match='ADMISSION'):
        getattr(workflow, entry)(root, *([config['order'][0]] if entry == 'run' else []))


@pytest.mark.parametrize('entry', ['serve', 'run'])
def test_serve_and_run_reject_mutated_frozen_configuration(tmp_path, carrier_seams, monkeypatch, entry):
    root, config, *_ = initialize_batch(tmp_path, carrier_seams, count=1)
    config['models']['C'] = 'changed-model'
    write_json(root / 'experiment.json', config)
    monkeypatch.setattr(workflow, 'docker', lambda *a, **k: pytest.fail('configuration reached Docker'))
    with pytest.raises(ValueError, match='CONFIGURATION'):
        getattr(workflow, entry)(root, *([config['order'][0]] if entry == 'run' else []))


def test_formal_runtime_cannot_switch_live_evidence_to_fake_dispatch(tmp_path, carrier_seams, monkeypatch):
    root, config, *_ = initialize_batch(tmp_path, carrier_seams, count=1)
    run_id = config['order'][0]
    ledger = Ledger(root / 'control.sqlite')
    with ledger.transaction() as db:
        state = ledger._load(db, run_id)
        state['mode'] = 'live_formal'
        ledger._save(db, state)
    write_json(root / 'service.json', {'state': 'running', 'url': 'http://127.0.0.1:1'})
    monkeypatch.setattr(workflow, 'ChatExecutor', lambda *a, **k: pytest.fail('live-labeled ledger reached fake dispatch'))
    with pytest.raises(ValueError, match='LEDGER_CONFIGURATION_CHANGED'):
        workflow.run(root, run_id)


def test_service_restart_consumes_old_stop_marker_only_when_idle(tmp_path, carrier_seams):
    root, config, *_ = initialize_batch(tmp_path, carrier_seams, count=1)
    write_json(root / 'service.json', {'state': 'stopped'})
    (root / 'stop-service').write_text('stop')
    ledger = Ledger(root / 'control.sqlite')
    workflow.prepare_service_start(root, config, ledger)
    assert not (root / 'stop-service').exists()
    ledger.start(config['order'][0])
    (root / 'stop-service').write_text('stop')
    with pytest.raises(ValueError, match='ACTIVE|RECOVERY'):
        workflow.prepare_service_start(root, config, ledger)
    assert (root / 'stop-service').exists()
    with pytest.raises(ValueError, match='ACTIVE|RECOVERY'):
        workflow.request_service_stop(root)


def test_serve_can_stop_and_restart_without_running_a_task(tmp_path, carrier_seams, monkeypatch):
    root, config, *_ = initialize_batch(tmp_path, carrier_seams, count=1)
    registrations, commands, started = [], [], []
    class Gateway:
        url = 'http://127.0.0.1:12345'
        server = SimpleNamespace(server_port=12345)
        def __init__(self, *args, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def register(self, run_id, **kwargs): registrations.append((run_id, kwargs['model']))
    def pause(_):
        assert read_json(root / 'service.json')['state'] == 'running'
        assert not (root / 'stop-service').exists()
        started.append(True)
        workflow.request_service_stop(root)
    monkeypatch.setattr(workflow, 'WireGateway', Gateway)
    monkeypatch.setattr(workflow, 'docker', lambda *a, **k: commands.append(a))
    monkeypatch.setattr(workflow.time, 'sleep', pause)
    for _ in range(2):
        workflow.serve(root)
        assert read_json(root / 'service.json')['state'] == 'stopped'
    assert len(started) == 2
    assert len(registrations) == 8
    assert sum(c[:2] == ('network', 'create') for c in commands) == 2
    assert all(s['status'] == 'ready' for s in workflow.status(root))


def test_stopping_service_cannot_start_or_answer_a_task(tmp_path, carrier_seams):
    root, config, *_ = initialize_batch(tmp_path, carrier_seams, count=1)
    write_json(root / 'service.json', {'state': 'running', 'url': 'http://127.0.0.1:1'})
    run_id = config['order'][0]
    workflow.request_service_stop(root)
    with pytest.raises(ValueError, match='SERVICE_STOPPING'):
        workflow.run(root, run_id)
    ledger = Ledger(root / 'control.sqlite')
    assert ledger.snapshot(run_id)['status'] == 'ready'
    ledger.start(run_id)
    ledger.ask(run_id, question_id='q1', text='Where?')
    with pytest.raises(ValueError, match='SERVICE_STOPPING'):
        workflow.answer(root, run_id, {'text': 'Second opening.'})
    assert ledger.snapshot(run_id)['status'] == 'awaiting_user'


def test_dsh_pending_question_cannot_be_cold_restarted(tmp_path, carrier_seams):
    root, config, _, ids, _ = initialize_batch(tmp_path, carrier_seams, count=1)
    ledger = Ledger(root / 'control.sqlite')
    run_id = ids[0] + '-D'
    ledger.start(run_id)
    ledger.ask(run_id, question_id='question1', text='Which location?')
    write_json(root / 'service.json', {'state': 'stopped'})
    with pytest.raises(ValueError, match='D_COLD_RESUME_UNSUPPORTED'):
        workflow.prepare_service_start(root, config, ledger)
    assert ledger.snapshot(run_id)['status'] == 'awaiting_user'


def test_interrupted_dsh_does_not_create_new_native_session(tmp_path, carrier_seams, monkeypatch):
    root, config, _, ids, _ = initialize_batch(tmp_path, carrier_seams, count=1)
    write_json(root / 'service.json', {'state': 'running', 'url': 'http://127.0.0.1:1'})
    run_id = ids[0] + '-D'
    ledger = Ledger(root / 'control.sqlite')
    ledger.start(run_id)
    ledger.record(run_id, 'd_native_started', {'state_volume': config['routes'][run_id]['volume']})
    monkeypatch.setattr(workflow, 'NativeDSH', lambda *a, **k: pytest.fail('D cold-resume started a new runtime'))
    with pytest.raises(ValueError, match='D_COLD_RESUME_UNSUPPORTED'):
        workflow.run(root, run_id)
    assert len([e for e in ledger.events(run_id) if e['kind'] == 'd_native_started']) == 1


def test_b_worker_uses_remaining_task_deadline_and_budget_terminal(tmp_path, carrier_seams, monkeypatch):
    root, config, _, ids, budgets = initialize_batch(tmp_path, carrier_seams, count=1)
    write_json(root / 'service.json', {'state': 'running', 'url': 'http://127.0.0.1:1'})
    ledger = Ledger(root / 'control.sqlite')
    run_id = ids[0] + '-B'
    ledger.start(run_id)
    with ledger.transaction() as db:
        state = ledger._load(db, run_id)
        state['active_elapsed_s'] = 70
        ledger._save(db, state)
    seen = []
    class Worker:
        def __init__(self, cfg): seen.append(cfg)
        def prepare_state_volume(self): pass
        def start(self, run_id):
            return {'ok': False, 'error': 'WORKER_TIMEOUT', 'container_stopped': True, 'artifact_relative': None}
    monkeypatch.setattr(workflow, 'IsolatedB', Worker)
    final = workflow.run(root, run_id)
    assert 225 < seen[0].timeout_seconds <= budgets[ids[0]]['active_seconds'] - 70
    assert final['status'] == 'budget_exhausted'
    assert final['budget'] == budgets[ids[0]]


def test_b_clarification_resumes_binding_and_cumulative_budget(tmp_path, carrier_seams, monkeypatch):
    root, config, _, ids, budgets = initialize_batch(tmp_path, carrier_seams, count=1)
    write_json(root / 'service.json', {'state': 'running', 'url': 'http://127.0.0.1:1'})
    run_id = ids[0] + '-B'
    ledger = Ledger(root / 'control.sqlite')
    ledger.start(run_id)
    ledger.reserve(run_id, 'call1', upper_bound=100)
    ledger.settle(run_id, 'call1', usage={'prompt_tokens': 10, 'completion_tokens': 5}, response={})
    question = {'clarification_id': 'q1', 'answer_schema': {'type': 'object'}, 'candidates': []}
    native = {'clarification': question, 'state_version': 3}
    ledger.set_native(run_id, {'result': native})
    with ledger.transaction() as db:
        state = ledger._load(db, run_id)
        state['active_elapsed_s'] = 75
        ledger._save(db, state)
    ledger.ask(run_id, question_id='q1', text='Where?', binding={'native_question': question, 'state_version': 3})
    workflow.answer(root, run_id, {'text': 'The second opening.', 'event_id': 'answer1'})
    seen = []
    class Worker:
        def __init__(self, cfg): seen.append(cfg)
        def answer(self, actual_id, **kwargs):
            assert actual_id == run_id
            assert kwargs == {'answer': {'kind': 'add_detail', 'detail': 'The second opening.'},
                              'clarification_id': 'q1', 'expected_state_version': 3}
            return {'ok': True, 'container_stopped': True, 'artifact_relative': None,
                    'result': {'status': 'unsupported', 'state_version': 4}}
        def start(self, *a): pytest.fail('resume started a fresh B task')
        def prepare_state_volume(self): pytest.fail('resume initialized state')
        def export_state(self, destination): pass
    monkeypatch.setattr(workflow, 'IsolatedB', Worker)
    final = workflow.run(root, run_id)
    assert final['status'] == 'unsupported'
    assert final['budget'] == budgets[ids[0]] and final['usage']['calls'] == 1
    assert 220 < seen[0].timeout_seconds <= budgets[ids[0]]['active_seconds'] - 75
    assert len([e for e in ledger.events(run_id) if e['kind'] == 'answer']) == 1


def test_demo_defaults_keep_original_order_and_admission_contract(tmp_path, carrier_seams):
    config = workflow.initialize(tmp_path / 'demo', mode='offline', arms=['B'])
    assert config['order'] == ['case-001-B', 'case-002-B']
    assert 'configuration' not in config
    assert config['budget'] == workflow.BUDGET


def test_formal_synthetic_multitarget_public_api_fixture(tmp_path):
    """Earn the multi-operation fake response before dispatching containers."""
    import ifcopenshell
    from text2ifc_ifc_repair.api import RepairAPI
    cases, ids, _ = _formal_public_inputs(tmp_path)
    for case in ids[:2]:
        source = cases / case / 'public/model.ifc'
        before = source.read_bytes()
        provider = _FormalSceneProvider(case)
        api = RepairAPI(tmp_path / ('native-' + case), provider=provider, scene_grounding=True)
        result = api.start(source, (source.parent / 'request.txt').read_text(encoding='utf8'))
        if case == 'synthetic-002':
            assert result.status == 'clarification_required', result.to_dict()
            result = api.continue_with_answer(result.run_id, {'kind': 'add_detail', 'detail': '两个窗都宽900毫米。'},
                        clarification_id=result.clarification.clarification_id, expected_state_version=result.state_version)
        assert result.successful_artifact_publishable, result.to_dict()
        repaired = tmp_path / ('native-' + case) / result.run_directory / result.artifacts['successful_ifc']
        assert len(ifcopenshell.open(str(repaired)).by_type('IfcWindow')) == 2
        assert source.read_bytes() == before


def _formal_public_inputs(root):
    """Fresh authored D only: no original, Gold, damage recipe or deleted ID."""
    import ifcopenshell
    cases = root / 'public-cases'
    ids = ['synthetic-001', 'synthetic-002', 'synthetic-003']
    budgets = {}
    for case, length in zip(ids, (6., 8., 6.)):
        folder = cases / case / 'public'
        folder.mkdir(parents=True)
        model = ifcopenshell.file(schema='IFC2X3')
        def point(values): return model.create_entity('IfcCartesianPoint', Coordinates=values)
        origin = model.create_entity('IfcAxis2Placement3D', Location=point((0., 0., 0.)))
        context = model.create_entity('IfcGeometricRepresentationContext', ContextType='Model', CoordinateSpaceDimension=3,
                                      Precision=1e-5, WorldCoordinateSystem=origin)
        person = model.create_entity('IfcPerson', FamilyName='Offline fixture')
        organization = model.create_entity('IfcOrganization', Name='Synthetic runtime tests')
        user = model.create_entity('IfcPersonAndOrganization', ThePerson=person, TheOrganization=organization)
        application = model.create_entity('IfcApplication', ApplicationDeveloper=organization, Version='1',
                                          ApplicationFullName='Synthetic runtime tests', ApplicationIdentifier='fixture')
        history = model.create_entity('IfcOwnerHistory', OwningUser=user, OwningApplication=application, ChangeAction='ADDED', CreationDate=1)
        def entity(kind, **values): return model.create_entity(kind, GlobalId=ifcopenshell.guid.new(), OwnerHistory=history, **values)
        units = model.create_entity('IfcUnitAssignment', Units=[model.create_entity('IfcSIUnit', UnitType='LENGTHUNIT', Name='METRE')])
        project = entity('IfcProject', Name='Synthetic public input', RepresentationContexts=[context], UnitsInContext=units)
        storey = entity('IfcBuildingStorey', Name='Ground', CompositionType='ELEMENT', Elevation=0.,
                         ObjectPlacement=model.create_entity('IfcLocalPlacement', RelativePlacement=origin))
        entity('IfcRelAggregates', RelatingObject=project, RelatedObjects=[storey])
        wall = entity('IfcWall', Name='Public wall', ObjectPlacement=model.create_entity('IfcLocalPlacement',
                      PlacementRelTo=storey.ObjectPlacement, RelativePlacement=origin))
        external = model.create_entity('IfcPropertySingleValue', Name='IsExternal', NominalValue=model.create_entity('IfcBoolean', True))
        properties = entity('IfcPropertySet', Name='Pset_WallCommon', HasProperties=[external])
        entity('IfcRelDefinesByProperties', RelatedObjects=[wall], RelatingPropertyDefinition=properties)
        profile = model.create_entity('IfcRectangleProfileDef', ProfileType='AREA', XDim=length, YDim=.2,
                    Position=model.create_entity('IfcAxis2Placement2D', Location=point((length / 2., 0.))))
        solid = model.create_entity('IfcExtrudedAreaSolid', SweptArea=profile, Position=origin,
                    ExtrudedDirection=model.create_entity('IfcDirection', DirectionRatios=(0., 0., 1.)), Depth=3.2)
        body = model.create_entity('IfcShapeRepresentation', ContextOfItems=context, RepresentationIdentifier='Body', RepresentationType='SweptSolid', Items=[solid])
        axis = model.create_entity('IfcShapeRepresentation', ContextOfItems=context, RepresentationIdentifier='Axis', RepresentationType='Curve2D',
                    Items=[model.create_entity('IfcPolyline', Points=[point((0., 0.)), point((length, 0.))])])
        wall.Representation = model.create_entity('IfcProductDefinitionShape', Representations=[body, axis])
        entity('IfcRelContainedInSpatialStructure', RelatingStructure=storey, RelatedElements=[wall])
        model.write(str(folder / 'model.ifc'))
        positions = (2000, 6000) if case == 'synthetic-002' else (1500, 4500)
        width = '宽度请先向我确认' if case == 'synthetic-002' else '每扇窗宽900毫米'
        (folder / 'request.txt').write_text(f'在底层唯一长墙上补两扇窗，中心世界坐标x分别为{positions[0]}和{positions[1]}毫米，y为0。'
                    f'窗高1200毫米，窗台高900毫米，{width}。开洞并使窗填入对应洞口，其他对象保持原样。', encoding='utf8')
        budgets[case] = {'tokens': 2500000, 'calls': 50, 'active_seconds': 60 if case == 'synthetic-003' else 600,
                         'tool_seconds': 120, 'extensions': []}
    return cases, ids, budgets


class _FormalSceneProvider:
    """Echo synthetic public geometry/explicit fixture facts through real scene 0.2."""
    def __init__(self, case):
        self.case, self.asked = case, False

    def generate_candidate(self, **kwargs):
        from text2ifc_agent.providers import ProviderOutput
        from scripts.ifc_repair.repair_comparison.ours_adapter import _draft, _section, fixture_intent
        prompt = kwargs['prompt']
        if '## Immutable bindings' in prompt:
            value = _draft(prompt, kwargs.get('schema') or _section(prompt, 'Draft schema'))
        else:
            pages = _section(prompt, 'Read-only query results so far')
            if not pages:
                value = {'kind': 'query', 'query': {'ifc_classes': ['IfcWall']}}
            else:
                wall = pages[0]['records'][0]
                parameters = {'opening': {'width_mm': 900., 'height_mm': 1200., 'sill_height_mm': 900.}, 'window': {'fit_opening': True}}
                intent = fixture_intent('window', {'allowed_ifc_classes': ['IfcWall'], 'global_id': wall['id']}, parameters)
                intent['operations'][0]['operation_id'] = 'window-left'
                other = deepcopy(intent['operations'][0])
                other['operation_id'] = 'window-right'
                intent['operations'].append(other)
                if self.case == 'synthetic-002' and not self.asked:
                    self.asked = True
                    for op in intent['operations']: op['parameters']['opening'].pop('width_mm')
                    value = {'kind': 'clarification', 'intent': intent, 'reason': 'missing_user_fact',
                             'question': '两个窗的宽度分别是多少毫米？', 'candidate_ids': []}
                else:
                    points = (2000., 6000.) if self.case == 'synthetic-002' else (1500., 4500.)
                    value = {'kind': 'intent', 'intent': intent, 'bindings': [
                        {'operation_id': op['operation_id'], 'target_id': wall['id'],
                         'position': {'kind': 'world_point', 'point_world_mm': [x, 0., 0.]}}
                        for op, x in zip(intent['operations'], points)]}
        return ProviderOutput(text=json.dumps(value, ensure_ascii=False), metadata={
            'provider': 'fixture', 'model': 'formal-synthetic-fixture', 'evidence_class': 'deterministic_fake',
            'usage': {'input_tokens': 11, 'output_tokens': 7}})


_FORMAL_REPAIR_SCRIPT = '''import sys
from pathlib import Path
import ifcopenshell
model=ifcopenshell.open('model.ifc')
assert not Path('/var/run/docker.sock').exists()
assert not Path('/runtime/src/text2ifc_ifc_repair').exists()
assert not Path('/private').exists() and not Path('/source').exists()
history=model.by_type('IfcOwnerHistory')[0]
context=model.by_type('IfcGeometricRepresentationContext')[0]
wall=model.by_type('IfcWall')[0]
def point(values): return model.create_entity('IfcCartesianPoint',Coordinates=values)
def axis(values): return model.create_entity('IfcAxis2Placement3D',Location=point(values))
def entity(kind,**kw): return model.create_entity(kind,GlobalId=ifcopenshell.guid.new(),OwnerHistory=history,**kw)
def shape(product,depth):
 profile=model.create_entity('IfcRectangleProfileDef',ProfileType='AREA',XDim=.9,YDim=depth,
   Position=model.create_entity('IfcAxis2Placement2D',Location=point((.45,0.))))
 solid=model.create_entity('IfcExtrudedAreaSolid',SweptArea=profile,Position=axis((0.,0.,0.)),
   ExtrudedDirection=model.create_entity('IfcDirection',DirectionRatios=(0.,0.,1.)),Depth=1.2)
 body=model.create_entity('IfcShapeRepresentation',ContextOfItems=context,RepresentationIdentifier='Body',RepresentationType='SweptSolid',Items=[solid])
 product.Representation=model.create_entity('IfcProductDefinitionShape',Representations=[body])
windows=[]
for x in (float(sys.argv[1]),float(sys.argv[2])):
 opening=entity('IfcOpeningElement',ObjectPlacement=model.create_entity('IfcLocalPlacement',PlacementRelTo=wall.ObjectPlacement,RelativePlacement=axis((x-.45,0.,.9))))
 shape(opening,.2)
 window=entity('IfcWindow',OverallWidth=.9,OverallHeight=1.2,ObjectPlacement=model.create_entity('IfcLocalPlacement',PlacementRelTo=opening.ObjectPlacement,RelativePlacement=axis((0.,0.,0.))))
 shape(window,.05)
 entity('IfcRelVoidsElement',RelatingBuildingElement=wall,RelatedOpeningElement=opening)
 entity('IfcRelFillsElement',RelatingOpeningElement=opening,RelatedBuildingElement=window)
 style=entity('IfcWindowStyle',Name='Synthetic window style',ConstructionType='NOTDEFINED',OperationType='NOTDEFINED',ParameterTakesPrecedence=False,Sizeable=False)
 entity('IfcRelDefinesByType',RelatedObjects=[window],RelatingType=style)
 windows.append(window)
containment=wall.ContainedInStructure[0]
containment.RelatedElements=[*containment.RelatedElements,*windows]
Path('output').mkdir(exist_ok=True)
model.write('output/repaired.ifc')
print('SYNTHETIC_PUBLIC_REPAIR_OK',len(model.by_type('IfcWindow')))
'''


class _FormalHTTPTransport:
    """Controller-only fake; no package or runtime container imports this module."""
    def __init__(self, root, config):
        self.root, self.config, self.counts, self.providers = Path(root), config, {}, {}

    def __call__(self, request):
        import httpx
        from tests.ifc_repair.repair_comparison.dsh_fake_gateway import chunks
        run_id = request.url.path.strip('/').split('/')[0]
        case, arm = run_id.rsplit('-', 1)
        step = self.counts.get(run_id, 0)
        self.counts[run_id] = step + 1
        body = json.loads(request.content)
        question = case == 'synthetic-002'
        points = ('2.', '6.') if question else ('1.5', '4.5')
        if arm == 'B':
            provider = self.providers.setdefault(run_id, _FormalSceneProvider(case))
            value = provider.generate_candidate(prompt=body['messages'][0]['content']).text
            message = {'role': 'assistant', 'content': value, 'reasoning_content': 'OFFLINE_FORMAL_FIXTURE'}
            finish = 'stop'
        elif arm == 'D':
            if case == 'synthetic-003':
                assert step == 0, 'budget fixture must stop the first native foreground process'
                code = "import time; from pathlib import Path; exec('while True:\\n Path(\"heartbeat\").write_text(str(time.time()))\\n time.sleep(.1)')"
                command = "python -u - <<'HEARTBEAT'\n" + code + '\nHEARTBEAT'
                events = chunks(tool=('bash', {'command': command, 'description': 'Offline process deadline fixture', 'timeoutMs': 120000}, 'deadline-shell'))
            elif question and step == 0:
                events = chunks(tool=('ask_user_question', {'questions': [{'id': 'width', 'question': '两个窗都需要多宽？'}]}, 'width-question'))
            elif step == (1 if question else 0):
                if question: assert '900' in json.dumps(body['messages'], ensure_ascii=False)
                command = "mkdir -p work output && cat > work/fixture.py <<'PUBLIC_SCRIPT'\n" + _FORMAL_REPAIR_SCRIPT + '\nPUBLIC_SCRIPT\npython work/fixture.py ' + ' '.join(points)
                events = chunks(tool=('bash', {'command': command, 'description': 'Repair synthetic public IFC', 'timeoutMs': 120000}, 'repair-shell'))
            else:
                assert 'SYNTHETIC_PUBLIC_REPAIR_OK' in json.dumps(body['messages'])
                events = chunks(text='{"submitted_ifc":"output/repaired.ifc"}')
            return httpx.Response(200, headers={'Content-Type': 'text/event-stream'},
                content=''.join('event: ' + e['type'] + '\ndata: ' + json.dumps(e) + '\n\n' for e in events).encode())
        else:
            if question and step == 0:
                name, args = 'ask_user', {'question': '两个窗都需要多宽？'}
            else:
                offset = step - int(question)
                actions = [('write_file', {'path': 'work/fixture.py', 'text': _FORMAL_REPAIR_SCRIPT}),
                           ('execute', {'argv': ['python', 'work/fixture.py', *points], 'timeout_s': 120}),
                           ('submit', {'path': 'output/repaired.ifc'})]
                assert offset < len(actions), 'inspect prior tool failure; no automatic retry fixture'
                if offset == 2: assert 'SYNTHETIC_PUBLIC_REPAIR_OK' in json.dumps(body['messages'])
                name, args = actions[offset]
            message = {'role': 'assistant', 'content': None, 'reasoning_content': 'OFFLINE_FORMAL_FIXTURE',
                       'tool_calls': [{'id': f'offline-{step}', 'type': 'function', 'function': {'name': name, 'arguments': json.dumps(args)}}]}
            finish = 'tool_calls'
        return httpx.Response(200, json={'id': f'offline-{step}', 'model': body['model'],
            'choices': [{'index': 0, 'message': message, 'finish_reason': finish}],
            'usage': {'prompt_tokens': 11, 'completion_tokens': 7, 'total_tokens': 18}})


def _formal_fixture_cli():
    # The sole replacement is the existing controller's offline HTTP seam.
    # Parser, ledger, isolated carriers, SDK and worker tools remain real.
    from tests.ifc_repair.repair_comparison import demo_http_fixture
    demo_http_fixture.FakeDemoTransport = _FormalHTTPTransport
    workflow.main()


@pytest.mark.skipif(os.environ.get('REPAIR_FORMAL_DOCKER') != '1', reason='explicit keyless formal runtime validation')
def test_formal_batch_real_containers_public_cli_and_native_budget_stop(tmp_path):
    import ifcopenshell
    import ifcopenshell.validate
    from scripts.ifc_repair.repair_comparison.contracts import sha256
    cases, ids, budgets = _formal_public_inputs(tmp_path)
    root = tmp_path / 'experiment'
    budgets_path = tmp_path / 'budgets.json'
    write_json(budgets_path, budgets)
    command = [sys.executable, '-c', 'from tests.ifc_repair.repair_comparison.test_batch_workflow import _formal_fixture_cli; _formal_fixture_cli()']
    log_folder = tmp_path / 'logs'
    log_folder.mkdir()
    sequence = 0
    def call(action, *extra, timeout=600):
        nonlocal sequence
        sequence += 1
        process = subprocess.run(command + [action, '--root', str(root), *extra], cwd=workflow.REPO,
            capture_output=True, text=True, encoding='utf8', timeout=timeout)
        (log_folder / f'{sequence:02d}-{action}.log').write_text(process.stdout + '\nSTDERR\n' + process.stderr, encoding='utf8')
        assert process.returncode == 0, (action, process.stdout[-2500:], process.stderr[-2500:])
        return json.loads(process.stdout)
    config = call('init', '--cases-root', str(cases), '--case-ids', *ids, '--budgets', str(budgets_path),
                  '--stage', workflow.FORMAL_STAGE, '--scene-grounding')
    report = {'stage': workflow.FORMAL_STAGE, 'real_models_called': False, 'evidence_class': 'real_runtime_fake_model',
              'full_admission': False, 'configuration': config['configuration'], 'bindings': workflow.bindings(config['configuration']),
              'public_inputs': {case: sha256(cases / case / 'public/model.ifc') for case in ids}, 'runs': [], 'checks': {}}
    evidence = tmp_path / 'formal-runtime-seams.json'
    write_json(evidence, report)
    service, service_log, native, native_log = None, None, None, None
    def start_service():
        handle = (log_folder / f'service-{len(report["runs"])}.log').open('wb')
        process = subprocess.Popen(command + ['serve', '--root', str(root)], cwd=workflow.REPO, stdout=handle, stderr=subprocess.STDOUT)
        deadline = time.monotonic() + 90
        while True:
            assert process.poll() is None, 'gateway service exited'
            if (root / 'service.json').exists() and read_json(root / 'service.json').get('state') == 'running': break
            assert time.monotonic() < deadline, 'gateway startup timeout'
            time.sleep(.25)
        return process, handle
    def inspect_output(state):
        assert state['status'] == 'submitted', state
        assert state['mode'] == 'real_runtime_fake_model' and state['usage']['coverage'] == 'complete'
        path = Path(state['artifact']['path'])
        model = ifcopenshell.open(str(path))
        assert len(model.by_type('IfcWindow')) == len(model.by_type('IfcRelFillsElement')) == len(model.by_type('IfcRelVoidsElement')) == 2
        logger = ifcopenshell.validate.json_logger()
        ifcopenshell.validate.validate(model, logger, express_rules=True)
        assert not logger.statements, logger.statements[:3]
        source = cases / state['case_id'] / 'public/model.ifc'
        assert sha256(source) == report['public_inputs'][state['case_id']]
        assert (root / 'workspaces' / state['run_id'] / 'model.ifc').read_bytes() == source.read_bytes()
        report['runs'].append({'run_id': state['run_id'], 'state': state, 'reopen': True, 'native_schema_express': True, 'new_windows': 2})
        write_json(evidence, report)
    try:
        service, service_log = start_service()
        ledger = Ledger(root / 'control.sqlite')
        for case in ids[:2]:
            for run_id in (r for r in config['order'] if r.rsplit('-', 1)[0] == case):
                if case == 'synthetic-002' and run_id.endswith('-D'):
                    native_log = (log_folder / 'd-question.log').open('wb')
                    native = subprocess.Popen(command + ['run', '--root', str(root), '--run-id', run_id], cwd=workflow.REPO, stdout=native_log, stderr=subprocess.STDOUT)
                    deadline = time.monotonic() + 180
                    while ledger.snapshot(run_id)['status'] != 'awaiting_user':
                        assert native.poll() is None and time.monotonic() < deadline, ledger.snapshot(run_id)
                        time.sleep(.25)
                    state = ledger.snapshot(run_id)
                else: state = call('run', '--run-id', run_id)
                if case == 'synthetic-002':
                    assert state['status'] == 'awaiting_user', state
                    before = state
                    time.sleep(.3)
                    waiting = ledger.snapshot(run_id)
                    assert waiting['usage']['calls'] == before['usage']['calls']
                    assert abs(waiting['active_elapsed_s'] - before['active_elapsed_s']) < .01
                    answer_file = tmp_path / 'answer.json'
                    write_json(answer_file, {'text': '两个窗都宽900毫米。', 'event_id': 'confirmed-width'})
                    call('answer', '--run-id', run_id, '--answer-file', str(answer_file))
                    if run_id.endswith('-D'):
                        native.wait(timeout=180)
                        native_log.close()
                        assert native.returncode == 0
                        state = ledger.snapshot(run_id)
                        assert {c['metadata']['native_session_id'] for c in ledger.calls(run_id)} == {run_id}
                    else: state = call('run', '--run-id', run_id)
                    assert state['usage']['calls'] > before['usage']['calls'] and state['budget'] == before['budget']
                    if run_id.endswith('-B'):
                        assert state['native']['result']['run_id'] == before['native']['result']['run_id']
                        assert state['native']['result']['state_version'] > before['native']['result']['state_version']
                    report['checks'][run_id + '-same-task-resume'] = True
                inspect_output(state)
            if case == ids[0]:
                call('stop')
                service.wait(timeout=30)
                service_log.close()
                service, service_log = start_service()
                report['checks']['service_safe_restart'] = True
        run_id = ids[2] + '-D'
        state = call('run', '--run-id', run_id, timeout=180)
        assert state['status'] == 'budget_exhausted' and state['artifact'] is None, state
        assert state['usage']['calls'] == 1 and not state['activities']
        container = read_json(root / 'runtime' / run_id / 'container.json')
        assert not container['State']['Running'] and container['State']['Pid'] == 0
        heartbeat = root / 'workspaces' / run_id / 'heartbeat'
        last = heartbeat.read_bytes()
        time.sleep(.3)
        assert heartbeat.read_bytes() == last
        report['runs'].append({'run_id': run_id, 'state': state, 'process_stopped': True, 'heartbeat_stopped': True})
        report['checks'].update(abcd_two_complete_public_inputs=True, b_scene_02_two_operations=True,
                               d_native_budget_stop=True, a_c_same_generic_tools=True, formal_binding_recorded=True)
    except BaseException as error:
        report['error'] = f'{type(error).__name__}: {error}'
        raise
    finally:
        write_json(evidence, report)
        if native is not None and native.poll() is None:
            # Fail closed, retain native evidence; stop only this fixture's container.
            route = config['routes']['synthetic-002-D']
            workflow.docker('stop', '--time', '2', route['container'])
            native.wait(timeout=30)
        if native_log is not None and not native_log.closed: native_log.close()
        if service is not None and service.poll() is None:
            states = workflow.status(root)
            if all(s['status'] != 'running' and s['status'] != 'awaiting_user' for s in states):
                call('stop')
                service.wait(timeout=30)
            else:
                # Failed fixture cleanup only: terminate the fixture controller,
                # never clear its ledger or restart a stopped task.
                service.terminate()
                service.wait(timeout=30)
                workflow.docker('stop', '--time', '2', config['relay'])
                workflow.docker('rm', config['relay'])
                workflow.docker('network', 'rm', config['network'])
        if service_log is not None: service_log.close()
