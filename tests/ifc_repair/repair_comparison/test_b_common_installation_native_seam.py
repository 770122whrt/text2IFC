"""Real Linux B CLI/SDK; only the controller HTTP upstream is deterministic."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import httpx
import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.placement
import ifcopenshell.util.unit
import numpy as np
import pytest

from scripts.ifc_repair.repair_comparison import demo_workflow as carrier
from scripts.ifc_repair.repair_comparison.contracts import read_json, write_json, sha256
from scripts.ifc_repair.repair_comparison.formal_admission import capture_sources, file_ref
from scripts.ifc_repair.repair_comparison.inspection import native_validation
from scripts.ifc_repair.repair_comparison.ledger import Ledger
from tests.ifc_repair.test_window_installation_anchor import PublicWindowProvider, scene
from tests.ifc_repair.repair_comparison.test_batch_workflow import _FormalHTTPTransport


ANSWER = 'The nominal height is 1200 millimetres. Keep the opening height at 1190 millimetres.'


class AddingBrepDoorProvider:
    """Fake boundary: select offered public identities, then echo native draft."""
    def __init__(self, fixture):
        self.fixture = fixture

    def generate_candidate(self, **kwargs):
        from text2ifc_agent.providers import ProviderOutput
        from scripts.ifc_repair.repair_comparison.ours_adapter import _section, _draft, fixture_intent
        prompt = kwargs['prompt']
        if '## Immutable bindings' in prompt:
            value = _draft(prompt, _section(prompt, 'Draft schema'))
        else:
            pages = _section(prompt, 'Read-only query results so far')
            if not pages:
                value = {'kind': 'query', 'query': {'ifc_classes': ['IfcWall', 'IfcDoor']}}
            else:
                rows = pages[-1]['records']
                target = next(r for r in rows if r['id'] == self.fixture['target_wall'])
                reference = next(r for r in rows if r['id'] == self.fixture['reference'])
                body = fixture_intent('door', {'allowed_ifc_classes': ['IfcWall']}, {
                    'position': {'reference': 'wall_local_start', 'center_offset_mm': 950.},
                    'opening': {'width_mm': 900., 'height_mm': 2100., 'sill_height_mm': 0.,
                                'dimension_meaning': 'overall_opening'},
                    'door': {'operation_type': 'SINGLE_SWING_LEFT', 'formal_enum_explicit': True}})
                operation = body['operations'][0]
                operation['operation_type'] = 'add_door_with_opening_to_wall'
                operation['routing_intent'].update(action='add_with_opening', operation_profile='door.add-with-opening.v0.4')
                operation['prototype_intent'] = {'reference_kind': 'global_id', 'reference': reference['type_id'],
                                                 'source': operation['provenance'][0]}
                value = {'kind': 'intent', 'intent': body, 'bindings': [{
                    'operation_id': operation['operation_id'], 'target_id': target['id'], 'reference_id': reference['id'],
                    'position': {'kind': 'world_point', 'point_world_mm': self.fixture['target_point_world_mm']}}]}
        return ProviderOutput(text=json.dumps(value), metadata={
            'provider': 'fixture', 'model': 'offline-direct-body-add', 'evidence_class': 'offline_fake'})


class ClarifyingWindowProvider(PublicWindowProvider):
    def __init__(self):
        super().__init__(opening_height=1190., nominal_height=1200.)
        self.asked = False

    def generate_candidate(self, **kwargs):
        from text2ifc_agent.providers import ProviderOutput
        result = super().generate_candidate(**kwargs)
        value = json.loads(result.text)
        if value.get('kind') == 'intent':
            if not self.asked:
                self.asked = True
                # A missing-user-fact response must actually omit a required
                # fact. Do not ask to reconfirm an already complete intent.
                operation = value['intent']['operations'][0]
                operation['target_query']['global_id'] = value['bindings'][0]['target_id']
                del operation['parameters']['opening']['height_mm']
                operation['attribute_intents'] = [a for a in operation['attribute_intents']
                                                 if a['name'] != 'OverallHeight']
                value = {'kind': 'clarification', 'intent': value['intent'], 'reason': 'missing_user_fact',
                         'question': 'What are the opening height and nominal window height, in millimetres?',
                         'candidate_ids': [value['bindings'][0]['target_id']]}
            else:
                assert ANSWER in kwargs['prompt']
            return ProviderOutput(text=json.dumps(value), metadata=result.metadata)
        return result


class UndefinedStyleDoorProvider:
    """Offered exact Type is authoritative even when its operation is unknown."""
    def __init__(self):
        from tests.ifc_repair.test_door_installation_anchor import PublicOnlyProvider
        self.provider = PublicOnlyProvider()

    def generate_candidate(self, **kwargs):
        from text2ifc_agent.providers import ProviderOutput
        result = self.provider.generate_candidate(**kwargs)
        value = json.loads(result.text)
        if value.get('kind') == 'intent':
            for operation in value['intent']['operations']:
                operation['parameters'].pop('door', None)
        return ProviderOutput(text=json.dumps(value), metadata=result.metadata)


class BInstallationTransport(_FormalHTTPTransport):
    def __call__(self, request):
        run_id = request.url.path.strip('/').split('/')[0]
        case, arm = run_id.rsplit('-', 1)
        assert arm == 'B'
        body = json.loads(request.content)
        if run_id not in self.providers:
            if case == 'door-direct':
                provider = AddingBrepDoorProvider(read_json(self.root / 'fixture-bindings.json')[case])
            elif case == 'door-base':
                provider = UndefinedStyleDoorProvider()
            elif case == 'door-direct-denied':
                from tests.ifc_repair.test_door_installation_anchor import PublicOnlyProvider
                provider = PublicOnlyProvider()
            elif case == 'window-cohort':
                from tests.ifc_repair.test_public_semantic_and_base_authority import ExactPublicReferenceProvider
                provider = ExactPublicReferenceProvider(read_json(self.root / 'fixture-bindings.json')[case]['reference'])
            else:
                provider = (ClarifyingWindowProvider() if case == 'window-confirmation'
                    else PublicWindowProvider(nominal_height=1250. if case == 'window-incompatible' else 1200.))
            self.providers[run_id] = provider
        value = self.providers[run_id].generate_candidate(prompt=body['messages'][0]['content']).text
        response = httpx.Response(200, json={'id': 'offline-public-window', 'model': body['model'],
            'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': value}, 'finish_reason': 'stop'}],
            'usage': {'prompt_tokens': 11, 'completion_tokens': 7, 'total_tokens': 18}})
        path = self.root / 'runtime/window-upstream.jsonl'
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('a', encoding='utf8') as handle:
            handle.write(json.dumps({'run_id': run_id, 'request': body,
                'response_body': response.content.decode('utf8'),
                'evidence_class': 'deterministic_controller_upstream'}, ensure_ascii=False) + '\n')
        return response


def b_installation_fixture_cli():
    # Reuse only the existing stopped-container observation and fake HTTP seam.
    # Worker, public CLI, SDK, isolation, ledger and publication remain real.
    from tests.ifc_repair.repair_comparison import test_formal_revision_seams as base
    base.RevisionTransport = BInstallationTransport
    base.revision_fixture_cli()


@pytest.mark.parametrize('angle,millimetres', [(0., False), (90., False), (37., True), (180., True)])
def test_public_api_reuses_unknown_door_operation_without_extra_preference(tmp_path, angle, millimetres):
    from text2ifc_ifc_repair.api import RepairAPI
    from tests.ifc_repair.test_door_installation_anchor import scene as door_scene
    model, opening, reference, _, _ = door_scene(angle=angle, millimetres=millimetres)
    style = next(r.RelatingType for r in reference.IsDefinedBy if r.is_a('IfcRelDefinesByType'))
    style.OperationType = 'NOTDEFINED'
    source = tmp_path / 'public.ifc'
    model.write(str(source))
    before = source.read_bytes()
    assert native_validation(model)['passed']
    result = RepairAPI(tmp_path / 'native', provider=UndefinedStyleDoorProvider(), scene_grounding=True).start(
        source, 'Fill the empty 900 by 2100 mm opening using the retained complete door and frame; align the base.')
    assert result.successful_artifact_publishable, result.to_dict()
    root = tmp_path / 'native' / result.run_directory
    output = ifcopenshell.open(str(root / result.artifacts['successful_ifc']))
    added = next(d for d in output.by_type('IfcDoor') if d.GlobalId != reference.GlobalId)
    reused = next(r.RelatingType for r in added.IsDefinedBy if r.is_a('IfcRelDefinesByType'))
    assert reused.GlobalId == style.GlobalId and reused.OperationType == 'NOTDEFINED'
    assert added.FillsVoids[0].RelatingOpeningElement.GlobalId == opening.GlobalId
    assert native_validation(output)['passed']
    assert source.read_bytes() == before


def test_window_confirmation_fixture_resumes_public_api(tmp_path):
    from text2ifc_ifc_repair.api import RepairAPI
    model, _, _, _, _, _ = scene(opening_height=1190., nominal_height=1200.,
                                 body_height=1170., base_gap=20., angle=90.)
    source = tmp_path / 'public.ifc'
    model.write(str(source))
    api = RepairAPI(tmp_path / 'native', provider=ClarifyingWindowProvider(), scene_grounding=True)
    waiting = api.start(source, 'Add a 900 mm wide window; confirm the opening and nominal heights.')
    assert waiting.status == 'clarification_required', waiting.to_dict()
    result = api.continue_with_answer(waiting.run_id, {'kind': 'add_detail', 'detail': ANSWER},
        clarification_id=waiting.clarification.clarification_id, expected_state_version=waiting.state_version)
    assert result.successful_artifact_publishable, result.to_dict()


def _direct_addition_binding(model, opening, unit):
    from ifcopenshell.util.element import remove_deep2
    target_wall = opening.VoidsElements[0].RelatingBuildingElement
    placement = ifcopenshell.util.placement.get_local_placement(opening.ObjectPlacement)
    point = placement @ np.array([450. * unit, 50. * unit, 0., 1.])
    binding = {'target_wall': target_wall.GlobalId, 'target_point_world_mm': (point[:3] / unit).tolist()}
    model.remove(opening.VoidsElements[0])
    remove_deep2(model, opening)
    return binding


def test_direct_body_addition_fixture_public_api(tmp_path):
    from text2ifc_ifc_repair.api import RepairAPI
    from tests.ifc_repair.test_door_direct_body_reference import brep_scene
    model, opening, reference, unit = brep_scene(millimetres=True, angle=90., sign=-1., target_thickness_mm=100.)
    binding = _direct_addition_binding(model, opening, unit)
    binding['reference'] = reference.GlobalId
    source = tmp_path / 'public.ifc'
    model.write(str(source))
    result = RepairAPI(tmp_path / 'native', provider=AddingBrepDoorProvider(binding), scene_grounding=True).start(
        source, 'Open a 900 by 2100 mm hole at the specified public world point. Preserve the retained frame, '
        'leaf, hardware and finish; adapt the installation to the wall face and wall thickness.')
    assert result.successful_artifact_publishable, result.to_dict()


@pytest.mark.skipif(os.environ.get('REPAIR_FORMAL_DOCKER') != '1', reason='explicit keyless window Linux validation')
def test_b_common_installation_real_linux_public_cli(tmp_path):
    from text2ifc_ifc_repair.window_geometry import public_window_installation_anchor, measure_window_installation
    before = capture_sources('admission')
    fixture_directory = Path(__file__).resolve().parents[1]
    helpers = [file_ref(fixture_directory / name) for name in (
        'test_window_installation_anchor.py', 'test_door_installation_anchor.py',
        'test_public_semantic_and_base_authority.py', 'test_door_direct_body_reference.py')]
    cases = tmp_path / 'public-cases'
    specifications = {
        'window-complete': {'extension': 60., 'normal': 35., 'sign': -1., 'angle': 37., 'millimetres': True},
        'window-confirmation': {'opening_height': 1190., 'nominal_height': 1200., 'body_height': 1170., 'base_gap': 20., 'angle': 90.},
        'window-incompatible': {},
        'window-cohort': {},
        'door-base': {},
        'door-direct': {'millimetres': True, 'angle': 90., 'sign': -1., 'target_thickness_mm': 100.},
        'door-direct-denied': {'target_thickness_mm': 100.},
    }
    bindings = {}
    for case, configuration in specifications.items():
        folder = cases / case / 'public'
        folder.mkdir(parents=True)
        if case.startswith('door-direct'):
            from tests.ifc_repair.test_door_direct_body_reference import brep_scene, _reference_signature
            model, opening, reference, unit = brep_scene(**configuration)
        elif case == 'window-cohort':
            from tests.ifc_repair.test_public_semantic_and_base_authority import conflicting_windows
            model, wall, reference = conflicting_windows()
        elif case == 'door-base':
            from tests.ifc_repair.test_door_installation_anchor import scene as door_scene
            model, opening, reference, _, unit = door_scene()
            style = next(r.RelatingType for r in reference.IsDefinedBy if r.is_a('IfcRelDefinesByType'))
            style.OperationType = 'NOTDEFINED'
            for item in style.RepresentationMaps[0].MappedRepresentation.Items:
                point = item.Position.Location
                point.Coordinates = (*point.Coordinates[:2], point.Coordinates[2] + 100 * unit)
        else:
            model, wall, opening, reference, _, unit = scene(**configuration)
        direct_target = None
        if case == 'door-direct':
            direct_target = _direct_addition_binding(model, opening, unit)
            # Legal authoring labels are free text. The host Body is bound to
            # Design, while other unused 3D roots belong to Outline and Sketch.
            # The fixture helper's convenience Body subcontext must not mask
            # the production dependency on a global Model label.
            host = model.by_guid(direct_target['target_wall'])
            host_context = next(r.ContextOfItems for r in host.Representation.Representations
                                if r.RepresentationIdentifier == 'Body')
            host_context.ContextType = 'Design'
            host_context.ContextIdentifier = 'Plan'
            for sub in list(model.by_type('IfcGeometricRepresentationSubContext')):
                for inverse in model.get_inverse(sub):
                    if inverse.is_a('IfcShapeRepresentation'):
                        inverse.ContextOfItems = sub.ParentContext
                model.remove(sub)
            project = model.by_type('IfcProject')[0]
            extra = []
            for label in ('Outline', 'Sketch'):
                extra.append(model.createIfcGeometricRepresentationContext(
                    'Plan', label, 3, host_context.Precision, host_context.WorldCoordinateSystem, None))
            project.RepresentationContexts = [*project.RepresentationContexts, *extra]
        source = folder / 'model.ifc'
        model.write(str(source))
        validation = native_validation(model)
        assert validation['passed'], (case, validation)
        request = 'Add a window at the specified wall position, 700 mm sill, using the retained frame, glazing and installation. '
        request += ('Opening 900 mm wide; confirm the opening and nominal heights.' if case == 'window-confirmation'
            else 'Opening 900 by 1200 mm; nominal height ' + ('1250' if case == 'window-incompatible' else '1200') + ' mm.')
        if case == 'door-base':
            request = 'Fill the empty 900 by 2100 mm opening using the retained door frame and installation. Preserve its mapped geometry and nominal base datum.'
        elif case.startswith('door-direct'):
            from tests.ifc_repair.test_door_direct_body_reference import REQUEST_ZH, REQUEST_NO_ADAPTATION
            request = REQUEST_ZH if case == 'door-direct' else REQUEST_NO_ADAPTATION
            if direct_target:
                request = ('Open a new 900 by 2100 mm hole at global point ' +
                    json.dumps(direct_target['target_point_world_mm']) +
                    ' mm in the 100 mm wall; install a door using the retained frame, leaf, hardware and finish. '
                    'Keep the retained installation relative to the target wall face and adapt to wall thickness.')
        (folder / 'request.txt').write_text(request, encoding='utf8')
        if case.startswith('door-direct'):
            from text2ifc_ifc_repair.door_geometry import public_door_installation_anchor
            anchor = public_door_installation_anchor(reference, allow_wall_face_adaptation=case == 'door-direct')
        elif case == 'door-base':
            from text2ifc_ifc_repair.door_geometry import public_door_installation_anchor
            anchor = public_door_installation_anchor(reference)
        else:
            anchor = public_window_installation_anchor(reference)
        bindings[case] = {'source': file_ref(source), 'reference': reference.GlobalId, 'anchor': anchor,
                         'original_window_ids': [w.GlobalId for w in model.by_type('IfcWindow')]}
        if case.startswith('door-direct'):
            bindings[case]['reference_signature'] = _reference_signature(model, reference)
            if direct_target:
                bindings[case].update(direct_target)
    sentinel = 'PRIVATE_WINDOW_SEAM_SENTINEL'
    private = tmp_path / 'private-gold'
    private.mkdir()
    (private / 'sentinel.txt').write_text(sentinel, encoding='utf8')
    budgets = {case: {'tokens': 2500000, 'calls': 50, 'active_seconds': 600, 'tool_seconds': 120, 'extensions': []}
               for case in specifications}
    budget_path = tmp_path / 'budgets.json'
    write_json(budget_path, budgets)
    root = tmp_path / 'experiment'
    logs = tmp_path / 'logs'
    logs.mkdir()
    command = [sys.executable, '-c',
        'from tests.ifc_repair.repair_comparison.test_b_common_installation_native_seam import b_installation_fixture_cli; b_installation_fixture_cli()']
    commands = []

    def call(action, *arguments, timeout=600):
        argv = command + [action, '--root', str(root), *map(str, arguments)]
        response = subprocess.run(argv, cwd=carrier.REPO, capture_output=True, text=True, encoding='utf8', timeout=timeout)
        log = logs / f'{len(commands):02d}-{action}.log'
        log.write_text(response.stdout + '\nSTDERR\n' + response.stderr, encoding='utf8')
        commands.append({'argv': argv, 'exit_code': response.returncode, 'log': file_ref(log)})
        assert response.returncode == 0, (action, response.stdout[-3000:], response.stderr[-3000:])
        return json.loads(response.stdout)

    config = call('init', '--mode', 'offline', '--cases-root', cases, '--case-ids', *specifications,
                  '--budgets', budget_path, '--stage', carrier.FORMAL_STAGE, '--scene-grounding')
    write_json(root / 'fixture-bindings.json', bindings)
    report = {'schema_version': 'repair-comparison-b-installation-native-seams/0.1',
              'real_models_called': False, 'source_bindings': before, 'configuration': config['configuration'],
              'images': carrier.bindings(config['configuration'])['images'], 'fixture_helpers': helpers, 'runs': []}
    evidence = tmp_path / 'b-installation-native-seams.json'
    write_json(evidence, report)
    service_log = (logs / 'service.log').open('wb')
    service = subprocess.Popen(command + ['serve', '--root', str(root)], cwd=carrier.REPO,
                               stdout=service_log, stderr=subprocess.STDOUT)
    ledger = Ledger(root / 'control.sqlite')
    try:
        deadline = time.monotonic() + 90
        while not (root / 'service.json').exists() or read_json(root / 'service.json').get('state') != 'running':
            assert service.poll() is None and time.monotonic() < deadline
            time.sleep(.25)
        for case in specifications:
            run_id = case + '-B'
            state = call('run', '--run-id', run_id, timeout=300)
            action = 'start'
            if case == 'window-confirmation':
                assert state['status'] == 'awaiting_user'
                native_id = state['native']['result']['run_id']
                call_count = state['usage']['calls']
                budget = deepcopy(state['budget'])
                question = state['question']['question_id']
                answer = tmp_path / 'answer.json'
                write_json(answer, {'text': ANSWER, 'event_id': 'preauthored-public-window-confirmation'})
                call('answer', '--run-id', run_id, '--answer-file', answer)
                state = call('run', '--run-id', run_id, timeout=300)
                action = 'answer'
                assert state['native']['result']['run_id'] == native_id
                assert state['usage']['calls'] > call_count and state['budget'] == budget
                assert any(e['kind'] == 'answer' and e['payload']['question_id'] == question for e in ledger.events(run_id))
            expected = 'no_output' if case in {'window-incompatible', 'door-direct-denied'} else 'submitted'
            assert state['status'] == expected and state['mode'] == 'real_runtime_fake_model' and not state['activities'], state
            assert not any(c['state'] == 'inflight' for c in ledger.calls(run_id))
            assert sum(e['kind'] == 'started' for e in ledger.events(run_id)) == 1
            source = Path(bindings[case]['source']['path'])
            assert sha256(source) == bindings[case]['source']['sha256'] == sha256(root / 'workspaces' / run_id / 'model.ifc')
            row = {'family': 'B', 'scenario': case.removeprefix('window-'), 'run_id': run_id,
                   'experiment_root': str(root.resolve()), 'expected_status': expected,
                   'public_source': file_ref(source), 'container_state': file_ref(root / 'runtime' / f'{run_id}-{action}-container.json')}
            container = read_json(Path(row['container_state']['path']))
            assert not container['State']['Running'] and container['State']['Pid'] == 0
            assert all('private-gold' not in mount['Source'] for mount in container['Mounts'])
            if expected == 'submitted':
                assert state['native']['result']['successful_artifact_publishable']
                model = ifcopenshell.open(state['artifact']['path'])
                if case == 'door-base' or case.startswith('door-direct'):
                    from text2ifc_ifc_repair.door_geometry import measure_door_opening_alignment
                    new = [d for d in model.by_type('IfcDoor') if d.GlobalId != bindings[case]['reference']]
                else:
                    new = [w for w in model.by_type('IfcWindow') if w.GlobalId not in bindings[case]['original_window_ids']]
                assert len(new) == 1
                if case == 'door-base' or case.startswith('door-direct'):
                    installation = measure_door_opening_alignment(new[0], new[0].FillsVoids[0].RelatingOpeningElement,
                                                                  installation_anchor=bindings[case]['anchor'])
                    if case == 'door-base':
                        style = next(r.RelatingType for r in new[0].IsDefinedBy if r.is_a('IfcRelDefinesByType'))
                        assert style.OperationType == 'NOTDEFINED'
                        row['exact_unknown_operation_preserved'] = True
                    assert installation['expected_base_offset_mm'] == pytest.approx(100. if case == 'door-base' else 0.)
                    if case == 'door-direct':
                        from tests.ifc_repair.test_door_direct_body_reference import assert_complete_public_reuse, assert_authored_installation
                        assert_complete_public_reuse(model, new[0], model.by_guid(bindings[case]['reference']),
                                                     bindings[case]['reference_signature'])
                        assert_authored_installation(new[0], new[0].FillsVoids[0].RelatingOpeningElement, sign=-1., thickness=100.)
                        new_opening = new[0].FillsVoids[0].RelatingOpeningElement
                        host = new_opening.VoidsElements[0].RelatingBuildingElement
                        opening_body = next(rep for rep in new_opening.Representation.Representations
                                            if rep.RepresentationIdentifier == 'Body')
                        host_body = next(rep for rep in host.Representation.Representations
                                         if rep.RepresentationIdentifier == 'Body')
                        assert opening_body.ContextOfItems == host_body.ContextOfItems
                        assert opening_body.ContextOfItems.ContextType == 'Design'
                        assert opening_body.ContextOfItems.CoordinateSpaceDimension == 3
                        row['host_body_context_preserved'] = True
                        # Independent authored public world coordinates; no G.
                        settings = ifcopenshell.geom.settings()
                        settings.set(settings.USE_WORLD_COORDS, True)
                        shape = ifcopenshell.geom.create_shape(settings, new_opening)
                        vertices = np.asarray(shape.geometry.verts).reshape(-1, 3) * 1000.
                        center = (vertices.min(axis=0) + vertices.max(axis=0)) / 2
                        assert center[:2].tolist() == pytest.approx(
                            bindings[case]['target_point_world_mm'][:2], abs=.01)
                        assert vertices[:, 2].min() == pytest.approx(0., abs=.01)
                else:
                    installation = measure_window_installation(new[0], new[0].FillsVoids[0].RelatingOpeningElement, bindings[case]['anchor'])
                assert installation['valid'], installation
                if case == 'window-cohort':
                    from ifcopenshell.util.element import get_psets
                    assert get_psets(new[0])['Pset_WindowCommon']['IsExternal'] is True
                    row['host_external_authority_preserved'] = True
                validation = native_validation(model)
                assert validation['passed'] and validation['express_rules'] and validation['diagnostic_count'] == 0
                row.update(installation=installation, native_validation=validation, artifact=file_ref(Path(state['artifact']['path'])))
            else:
                assert state['artifact'] is None and not state['native']['result']['successful_artifact_publishable']
                assert not list((root / 'artifacts' / run_id).glob('*.ifc'))
            report['runs'].append(row)
            write_json(evidence, report)
        call('stop')
        service.wait(timeout=40)
        assert before == capture_sources('admission')
        assert all(helper == file_ref(Path(helper['path'])) for helper in helpers)
        upstream = root / 'runtime/window-upstream.jsonl'
        assert sentinel not in upstream.read_text(encoding='utf8')
        report.update(commands=commands, upstream_records=file_ref(upstream))
        write_json(evidence, report)
        print('B_INSTALLATION_NATIVE_SEAMS', str(evidence.resolve()), flush=True)
    except BaseException as error:
        report.update(error=f'{type(error).__name__}: {error}', commands=commands)
        write_json(evidence, report)
        raise
    finally:
        if service.poll() is None:
            service.terminate()
            service.wait(timeout=30)
            for name in [r['container'] for r in config['routes'].values()] + [config['relay']]:
                inspected = subprocess.run(['docker', 'inspect', name], capture_output=True, text=True)
                if inspected.returncode == 0:
                    carrier.docker('stop', '--time', '2', name)
                    if name == config['relay']:
                        carrier.docker('rm', name)
            subprocess.run(['docker', 'network', 'rm', config['network']], capture_output=True)
        service_log.close()
