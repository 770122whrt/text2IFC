"""Full formal controller path with real IFC/scoring and a fixture adapter.

This does not impersonate the B/DSH native runtimes: their actual Docker/SDK
seams have separate receipts. Only the adapter boundary is deterministic here.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid

import ifcopenshell
import ifcopenshell.util.element
import pytest

from scripts.ifc_repair.repair_comparison import formal_workflow as formal
from scripts.ifc_repair.repair_comparison.authoring import author_candidate
from scripts.ifc_repair.repair_comparison.contracts import read_json, write_json, sha256
from scripts.ifc_repair.repair_comparison.direct_runner import DirectRunner, ReplayProvider
from scripts.ifc_repair.repair_comparison.formal_batch import prepare_candidate, check_candidate
from scripts.ifc_repair.repair_comparison.inspection import native_validation
from scripts.ifc_repair.repair_comparison.ledger import Ledger, TERMINAL
from scripts.ifc_repair.repair_comparison.neutral_tools import TOOLS

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / '.tmp/repair-comparison-formal-expansion'
AUTH = {'user_quote': 'SYNTHETIC WRAPPER TEST FIXTURE ONLY: no real benchmark approval is represented.', 'at': '2026-10-08T00:00:00+00:00'}


def _source(path, index):
    """Fresh, schema-valid geometry with a target and retained equal reference."""
    model = ifcopenshell.file(schema='IFC2X3')
    def point(coords): return model.create_entity('IfcCartesianPoint', Coordinates=tuple(float(v) for v in coords))
    def axis(coords): return model.create_entity('IfcAxis2Placement3D', Location=point(coords))
    zero = axis((0,0,0))
    context = model.create_entity('IfcGeometricRepresentationContext', ContextType='Model', CoordinateSpaceDimension=3, Precision=1e-5, WorldCoordinateSystem=zero)
    org = model.create_entity('IfcOrganization', Name='Synthetic public-path fixture')
    owner = model.create_entity('IfcPersonAndOrganization', ThePerson=model.create_entity('IfcPerson', FamilyName='Fixture'), TheOrganization=org)
    app = model.create_entity('IfcApplication', ApplicationDeveloper=org, Version='1', ApplicationFullName='Offline controller test', ApplicationIdentifier='offline-test')
    history = model.create_entity('IfcOwnerHistory', OwningUser=owner, OwningApplication=app, ChangeAction='ADDED', CreationDate=1)
    def entity(kind, **kwargs): return model.create_entity(kind, GlobalId=ifcopenshell.guid.new(), OwnerHistory=history, **kwargs)
    project = entity('IfcProject', Name=f'Synthetic source {index}', RepresentationContexts=[context], UnitsInContext=model.create_entity('IfcUnitAssignment', Units=[model.create_entity('IfcSIUnit', UnitType='LENGTHUNIT', Name='METRE')]))
    storey = entity('IfcBuildingStorey', Name='Ground', CompositionType='ELEMENT', Elevation=0., ObjectPlacement=model.create_entity('IfcLocalPlacement', RelativePlacement=zero))
    entity('IfcRelAggregates', RelatingObject=project, RelatedObjects=[storey])
    def product(kind, xyz, width, depth, height):
        result = entity(kind, Name='Public synthetic element', ObjectPlacement=model.create_entity('IfcLocalPlacement', RelativePlacement=axis(xyz)))
        profile = model.create_entity('IfcRectangleProfileDef', ProfileType='AREA', Position=model.create_entity('IfcAxis2Placement2D', Location=point((0,0))), XDim=float(width), YDim=float(depth))
        solid = model.create_entity('IfcExtrudedAreaSolid', SweptArea=profile, Position=zero, ExtrudedDirection=model.create_entity('IfcDirection', DirectionRatios=(0.,0.,1.)), Depth=float(height))
        representation = model.create_entity('IfcShapeRepresentation', ContextOfItems=context, RepresentationIdentifier='Body', RepresentationType='SweptSolid', Items=[solid])
        result.Representation = model.create_entity('IfcProductDefinitionShape', Representations=[representation])
        if kind == 'IfcWindow': result.OverallWidth, result.OverallHeight = float(width), float(height)
        return result
    shift = index * .25
    width = .9 + (index % 3) * .01
    wall = product('IfcWall', (shift+3.5,0,0), 10, .2, 3.2)
    windows = []
    for x in (shift+2, shift+5):
        opening = product('IfcOpeningElement', (x,0,.85), width, .2, 1.2)
        window = product('IfcWindow', (x,0,.85), width, .05, 1.2)
        entity('IfcRelVoidsElement', RelatingBuildingElement=wall, RelatedOpeningElement=opening)
        entity('IfcRelFillsElement', RelatingOpeningElement=opening, RelatedBuildingElement=window)
        windows.append(window)
    entity('IfcRelContainedInSpatialStructure', RelatingStructure=storey, RelatedElements=[wall,*windows])
    path.parent.mkdir(parents=True, exist_ok=True)
    model.write(str(path))
    validation = native_validation(model)
    assert validation['passed'], validation['diagnostics']
    write_json(path.with_suffix('.validation.json'), validation)
    return windows[0].id(), windows[1].id()


def build_cases(base, count=20):
    from scripts.ifc_repair.repair_comparison.task_review import audit_case, enable_sill_clarification
    base.mkdir(parents=True, exist_ok=True)
    cases = base / 'cases'
    for index in range(1, count+1):
        name = f'formal-{index:03d}'
        case = cases / name
        if (case/'private/technical-review.json').exists() and read_json(case/'private/technical-review.json')['passed']:
            assert check_candidate(case)['valid']
            continue
        source = base / 'sources' / (name + '.ifc')
        target, reference = _source(source, index)
        selection = {'asset_id': 'synthetic-public-path-'+name, 'proposed_slot': name,
            'assessment_path': source.relative_to(base).as_posix(), 'assessment_sha256': sha256(source),
            'schema': 'IFC2X3', 'license': 'self-authored synthetic test fixture',
            'source_family': 'one-shared-synthetic-controller-fixture-family',
            'building_identity': name, 'independent_building_verified': False,
            'building_identity_basis': 'Different synthetic layouts/files, not independent real buildings.',
            'native_pass_registered': True, 'assessment_native_evidence': str(source.with_suffix('.validation.json')),
            'rights': {'public_release_policy': 'open_modification_with_notice', 'conditions': 'Synthetic test only, not research data.', 'source_url': 'local-self-authored-fixture'},
            'proposals': [{'targets': [{'step_id': target}], 'reference': {'step_id': reference}}], 'recommended_target_count': 1}
        row = author_candidate(selection, repository_root=base, plan=[(0,1)])
        if index == 1:
            row = enable_sill_clarification(row, repository_root=base)
        prepare_candidate(row, repository_root=base, output=case)
        card = read_json(case/'private/answer-card.json')
        card['status'] = 'accepted_by_delegation'
        write_json(case/'private/answer-card.json', card)
        # Audit only after the card has its final pre-freeze bytes.
        report = audit_case(case, authorization=AUTH, accept=True)
        assert report['passed'], (name, report['errors'])
        (case/'private/PRIVATE-CANARY.txt').write_text('PRIVATE-GOLD-CANARY-'+name, encoding='utf8')
        print('FIXTURE_PREPARED',name,flush=True)
    return cases


def _repair_from_public(text, request, run_id, *, duplicate=False):
    """Response fixture depends solely on exposed D bytes and user messages."""
    model = ifcopenshell.file.from_string(text)
    ref = model.by_type('IfcWindow')[0]
    ref_opening = ref.FillsVoids[0].RelatingOpeningElement
    wall = ref_opening.VoidsElements[0].RelatingBuildingElement
    xy = re.search(r'X=([-\d.]+)、Y=([-\d.]+)', request)
    height = re.search(r'世界标高\s*([-\d.]+)\s*米', request)
    assert xy and height, 'Fake provider cannot recover an omitted bottom without the actual answer.'
    for index in range(2 if duplicate else 1):
        opening = ifcopenshell.util.element.copy(model, ref_opening)
        opening.Representation = ifcopenshell.util.element.copy_deep(model,ref_opening.Representation,exclude=('IfcGeometricRepresentationContext',))
        opening.GlobalId = ifcopenshell.guid.compress(uuid.uuid5(uuid.NAMESPACE_URL, run_id+f'-opening-{index}').hex)
        position = model.create_entity('IfcAxis2Placement3D', Location=model.create_entity('IfcCartesianPoint', Coordinates=(float(xy[1]), float(xy[2]), float(height[1]))))
        opening.ObjectPlacement = model.create_entity('IfcLocalPlacement', RelativePlacement=position)
        window = ifcopenshell.util.element.copy(model, ref)
        window.Representation = ifcopenshell.util.element.copy_deep(model,ref.Representation,exclude=('IfcGeometricRepresentationContext',))
        window.GlobalId = ifcopenshell.guid.compress(uuid.uuid5(uuid.NAMESPACE_URL, run_id+f'-window-{index}').hex)
        window.ObjectPlacement = model.create_entity('IfcLocalPlacement', RelativePlacement=position)
        for relation, values in [('IfcRelVoidsElement', {'RelatingBuildingElement':wall,'RelatedOpeningElement':opening}),('IfcRelFillsElement',{'RelatingOpeningElement':opening,'RelatedBuildingElement':window})]:
            model.create_entity(relation, GlobalId=ifcopenshell.guid.new(), OwnerHistory=wall.OwnerHistory, **values)
        containment = ref.ContainedInStructure[0]
        containment.RelatedElements = [*containment.RelatedElements,window]
    return model.to_string()


class PublicOnlyProvider(ReplayProvider):
    def __init__(self, run_id, records):
        super().__init__([])
        self.run_id, self.records = run_id, records

    def complete(self, index, *, messages, tools):
        question = self.run_id == 'formal-001-A'
        out_of_card = self.run_id == 'formal-003-C'
        answers = [m['content'] for m in messages if m['role']=='user'][1:]
        request = '\n'.join(m['content'] for m in messages if m['role']=='user')
        if 'PRIVATE-GOLD-CANARY' in json.dumps(messages): raise AssertionError('PRIVATE_LEAK')
        reads = [json.loads(m['content']) for m in messages if m['role']=='tool' and '"text"' in m['content']]
        if out_of_card:
            response = {'tool_calls':[{'name':'ask_user','arguments':{'question':'这处窗的防火等级需要多少？'}}]}
        elif question and not answers:
            response = {'tool_calls':[{'name':'ask_user','arguments':{'question':'第1处窗洞下沿标高是多少？'}}]}
        elif not reads:
            response = {'tool_calls':[{'name':'read_file','arguments':{'path':'model.ifc'}}]}
        elif self.run_id in {'formal-001-B','formal-001-D'}:
            response = {'content':'无法完成，未提交任何文件。'}
        elif self.run_id == 'formal-002-A':
            response = {'error':'deterministic_transport_failure'}
        elif not any(m['role']=='tool' and '"characters"' in m['content'] for m in messages):
            data = 'NOT AN IFC FILE' if self.run_id == 'formal-001-C' else _repair_from_public(reads[-1]['text'], request, self.run_id, duplicate=self.run_id=='formal-002-C')
            response = {'tool_calls':[{'name':'write_file','arguments':{'path':'output/repaired.ifc','text':data}}]}
        else:
            response = {'tool_calls':[{'name':'submit','arguments':{'path':'output/repaired.ifc'}}]}
        response['usage'] = None if self.run_id in {'formal-001-C','formal-002-D'} and index==0 else {'prompt_tokens':11,'completion_tokens':7,'total_tokens':18}
        self.records.parent.mkdir(parents=True, exist_ok=True)
        with self.records.open('a',encoding='utf8') as handle:
            handle.write(json.dumps({'run_id':self.run_id,'call_index':index,'request':{'messages':messages,'tools':tools},'response':response,'evidence_class':'deterministic_public_only_fixture'},ensure_ascii=False)+'\n')
        return response


def fixture_adapter(root, run_id):
    """Use production ledger/tool/submit machinery, replacing native dispatch only."""
    runner = DirectRunner(root,run_id)
    state = runner.ledger.snapshot(run_id)
    if state['status'] in TERMINAL or state['status']=='awaiting_user': return state
    if state['status']=='ready': runner.ledger.start(run_id)
    provider = PublicOnlyProvider(run_id,Path(root)/'raw-provider'/f'{run_id}.jsonl')
    while True:
        runner._apply_pending()
        state = runner.ledger.snapshot(run_id)
        if state['status']!='running': return state
        calls = runner.ledger.calls(run_id)
        if calls and not calls[-1]['response'].get('tool_calls'):
            return runner.ledger.finish(run_id,'runtime_error' if calls[-1]['response'].get('error') else 'no_output')
        request_id = f'fixture-call-{len(calls)}'
        runner.ledger.reserve(run_id,request_id,1000,metadata={'evidence_class':'deterministic_public_only_fixture','wire_protocol':'chat'})
        response = provider.complete(len(calls),messages=runner.messages(),tools=deepcopy(TOOLS))
        runner.ledger.settle(run_id,request_id,usage=response['usage'],response=response,failed=bool(response.get('error')))


def test_pending_task_success_is_unknown_not_zero():
    row = {'arm':'A','status':'ready','success':None,'quantity':{'numerator':None,'denominator':1},'components':{'numerator':None,'denominator':1},'relations':{'numerator':None,'denominator':3},'known_tokens':0,'unknown_calls':0,'active_seconds':0}
    assert formal.summarize([row])['A']['task_success']['value'] is None


def test_full_formal_wrapper_public_path(tmp_path, monkeypatch):
    cached_cases = build_cases(EVIDENCE/'formal-public-path-fixtures')
    cases = tmp_path/'cases'
    shutil.copytree(cached_cases,cases)
    root = tmp_path/'experiment'
    plan_path = tmp_path/'frozen-plan.json'
    # Keep this test reproducible without any pre-existing ignored launcher.
    launcher = tmp_path/'formal-public-path-fixture-cli.py'
    launcher.write_text(
        'from pathlib import Path\nimport sys\n'
        f'root = Path({str(ROOT)!r})\n'
        'for path in (root, root / "src"):\n    sys.path.insert(0, str(path))\n'
        'from scripts.ifc_repair.repair_comparison import formal_workflow\n'
        'from tests.ifc_repair.repair_comparison.test_formal_public_path import fixture_adapter\n'
        'formal_workflow.carrier.run = fixture_adapter\n'
        'raise SystemExit(formal_workflow.main())\n', encoding='utf8')
    commands, command_logs = [], []
    def cli(action, *arguments):
        argv = [sys.executable,str(launcher),action,*map(str,arguments)]
        completed = subprocess.run(argv,cwd=ROOT,encoding='utf8',capture_output=True,check=False)
        log = tmp_path / f'command-{len(commands):02d}-{action}.log'
        log.write_text(completed.stdout+'\n'+completed.stderr,encoding='utf8')
        commands.append(argv)
        command_logs.append({'path':str(log.resolve()),'sha256':sha256(log),'exit_code':completed.returncode})
        assert completed.returncode==0, log.read_text(encoding='utf8')
    cli('freeze','--cases',cases,'--output',plan_path)
    plan = read_json(plan_path)
    cli('verify','--plan',plan_path)
    assert formal.verify_plan(plan_path)==plan
    cli('initialize','--root',root,'--plan',plan_path,'--mode','offline')
    ledger = Ledger(root/'control.sqlite')
    states = formal.carrier.status(root)
    assert len(states)==80 and len({r['metadata']['workspace'] for r in states})==80
    before = {str(p):sha256(p) for p in cases.glob('formal-*/private/reference.ifc')}
    for state in states:
        workspace = Path(state['metadata']['workspace'])
        assert (workspace/'model.ifc').read_bytes()==(cases/state['case_id']/'public/model.ifc').read_bytes()
        assert {p.name for p in workspace.iterdir()}=={'model.ifc','task.txt','work','output'}
        with pytest.raises(ValueError): DirectRunner(root,state['run_id']).tools.read_file('../private/reference.ifc')
    def next_cli(answer=False):
        selected = formal.next_task(formal.carrier.status(root))
        cli('next','--root',root,*(['--answer-from-card'] if answer else []))
        return ledger.snapshot(selected['run_id'])
    pending = next_cli()
    assert pending['status']=='awaiting_user' and pending['run_id']==plan['configuration']['order'][0]
    waiting_calls = pending['usage']['calls']
    cli('evaluate','--root',root,'--output',tmp_path/'pending-evaluation')
    pending_report = read_json(tmp_path/'pending-evaluation/results.json')
    assert pending_report['rows'][0]['success'] is None
    assert all(r['components']['numerator'] is None for r in pending_report['rows'])
    state = next_cli(answer=True)
    assert state['status']=='submitted' and state['usage']['calls']>waiting_calls
    for _ in range(7):
        assert next_cli()['status'] in TERMINAL
    # Ninth task waits on an unapproved question: it must not release a card.
    pending = next_cli()
    assert pending['run_id']=='formal-003-C' and pending['status']=='awaiting_user'
    assert next_cli(answer=True)['status']=='awaiting_user'
    reloaded = Ledger(root/'control.sqlite')
    assert reloaded.snapshot(pending['run_id'])['question']==pending['question']
    with pytest.raises(ValueError,match='RUN_ALREADY_STARTED'): reloaded.start(plan['configuration']['order'][0])
    with pytest.raises(ValueError,match='TERMINAL_IMMUTABLE'): DirectRunner(root,plan['configuration']['order'][0]).submit('output/repaired.ifc')
    started = [r['run_id'] for r in formal.carrier.status(root) if any(e['kind']=='started' for e in ledger.events(r['run_id']))]
    assert started==plan['configuration']['order'][:9]
    cli('evaluate','--root',root)
    report = read_json(root/'evaluation/results.json')
    assert len(report['rows'])==80
    scored = {r['run_id']:r for r in report['rows']}
    assert scored['formal-001-A']['success'] is True
    assert scored['formal-001-A']['clarification']['success'] is True
    assert scored['formal-001-C']['ifc_valid'] is False
    assert scored['formal-001-D']['success'] is False and scored['formal-001-D']['artifact'] is None
    assert scored['formal-002-C']['success'] is not True
    assert scored['formal-002-A']['status']=='runtime_error'
    assert scored['formal-001-C']['unknown_calls']==1
    assert all(scored[run]['success'] is None for run in plan['configuration']['order'][8:])
    assert all(s['task_success']['value'] is None for s in report['summary'].values())
    assert all(sha256(Path(path))==digest for path,digest in before.items())
    for run in plan['configuration']['order'][:8]:
        state = reloaded.snapshot(run)
        assert sum(e['kind']=='started' for e in ledger.events(run))==1
        if state['artifact']:
            assert sha256(Path(state['artifact']['path']))==state['artifact']['sha256']
            assert len(list((root/'artifacts'/run).glob('*.ifc')))==1
    receipt = {'schema_version':'repair-comparison-formal-public-path/0.1','mode':'offline',
        'fixture_kind':'synthetic_public_path_only','runtime_scope':'controller_wrapper_with_deterministic_fixture_adapter',
        'native_runtime_claim':False,'d_cold_resume_supported':False,
        'configuration':plan['configuration'],'plan':{'path':str(plan_path.resolve()),'sha256':sha256(plan_path)},
        'experiment_root':str(root.resolve()),'results':{'path':str((root/'evaluation/results.json').resolve()),'sha256':sha256(root/'evaluation/results.json')},
        'logs':command_logs+[{'path':str(p.resolve()),'sha256':sha256(p)} for p in (root/'raw-provider').glob('*.jsonl')],
        'commands':commands,'pytest_argv':sys.orig_argv,'terminal_tasks':8,'started_tasks':9,
        'fixture_launcher':{'path':str(launcher.resolve()),'sha256':sha256(launcher)},
        'limitations':['Shared synthetic family; not model capability evidence.','Actual B/DSH native runtime and process-stop behavior use separate runtime-seam evidence.','Local tool path boundaries checked; native OS isolation is not claimed by this controller fixture.']}
    write_json(EVIDENCE/'formal-public-path-pytest-result.json',receipt)
    print('FORMAL_PUBLIC_PATH_RECEIPT',str(EVIDENCE/'formal-public-path-pytest-result.json'),flush=True)
