"""Frozen offline compatibility family for an optional installation anchor.

All IFCs are authored public synthetic scenes. The direct-body reference is
exactly the simple rectangular geometry the existing legacy creator supports;
this does not claim arbitrary Brep cloning, wall-thickness adaptation, or any
improvement on a revealed formal task. Only the Provider boundary is fake.

Hypotheses frozen before the resolution fix:
* No Type maps: selecting an offered reference must retain the legacy path.
* Type maps present: malformed geometry must never trigger that fallback.
* Skipping an inapplicable anchor must not skip source or identity authority.
"""
from __future__ import annotations

from copy import deepcopy
import json

import ifcopenshell
import ifcopenshell.api.geometry
import ifcopenshell.guid
import pytest

from text2ifc_agent.providers import ProviderOutput
from text2ifc_ifc_repair.api import RepairAPI, RepairIntent, SQLiteIndexRepository
from text2ifc_ifc_repair.geometry import product_geometry_bounds_in_host_mm
from text2ifc_ifc_repair.operations import create_default_registry
from text2ifc_ifc_repair.resolution_flow import resolve_repair_intent
from tests.ifc_repair.test_door_installation_anchor import PublicOnlyProvider, scene


REQUEST = (
    'Fill the empty opening with a 900 by 2100 mm single-swing door, using '
    'the retained public door type. Keep all existing geometry unchanged.'
)


def direct_rectangle_scene(*, millimetres=False, angle=0.):
    """A symmetric 900 x 2100 x 50 mm direct Body, centred in a 150 mm wall."""
    model, opening, reference, _, unit = scene(
        overhang=0., millimetres=millimetres, angle=angle,
    )
    style = reference.IsDefinedBy[0].RelatingType
    context = model.by_type('IfcGeometricRepresentationContext')[0]
    direct = ifcopenshell.api.geometry.add_wall_representation(
        model, context=context, length=.9, height=2.1, thickness=.05,
        offset=-.025,
    )
    reference.Representation = model.createIfcProductDefinitionShape(
        None, None, [direct],
    )
    style.RepresentationMaps = None
    assert not style.RepresentationMaps
    assert direct.Items[0].is_a('IfcExtrudedAreaSolid')
    return model, opening, reference, unit


class CompatibilityProvider(PublicOnlyProvider):
    """Reads public scene pages and echoes native Stage 2 authority only."""

    def __init__(self, *, omit_reference=False, fault=None):
        super().__init__(unoffered=fault == 'unoffered')
        self.omit_reference = omit_reference
        self.fault = fault

    def generate_candidate(self, **kwargs):
        result = super().generate_candidate(**kwargs)
        value = json.loads(result.text)
        stage2 = '## Immutable bindings' in kwargs['prompt']
        if stage2 and self.fault == 'malformed_stage2':
            return ProviderOutput(text='{', metadata=result.metadata)
        if stage2 and self.fault == 'injected_anchor':
            value['operations'][0]['parameters']['door_installation_anchor'] = {
                'method': 'public-door-opening-installation/0.1',
                'reference_global_id': 'unoffered',
            }
        if not stage2 and value.get('kind') == 'intent':
            if self.omit_reference:
                for binding in value['bindings']:
                    binding.pop('reference_id')
            if self.fault == 'prototype_mismatch':
                value['intent']['operations'][0]['prototype_intent']['reference'] = 'unoffered-type'
        return ProviderOutput(text=json.dumps(value), metadata=result.metadata)

    @property
    def stage2_calls(self):
        return [call for call in self.calls if '## Immutable bindings' in call['prompt']]


def _start(tmp_path, model, provider):
    source = tmp_path / 'public.ifc'
    model.write(str(source))
    before = source.read_bytes()
    result = RepairAPI(tmp_path / 'run', provider=provider, scene_grounding=True).start(source, REQUEST)
    assert source.read_bytes() == before
    return source, result, tmp_path / 'run' / result.run_directory


def _successful_rectangle(result, run, opening, reference):
    assert result.status == 'succeeded', result.to_dict()
    repaired = ifcopenshell.open(str(run / result.artifacts['successful_ifc']))
    created = next(d for d in repaired.by_type('IfcDoor') if d.GlobalId != reference.GlobalId)
    target_opening = repaired.by_guid(opening.GlobalId)
    bounds = product_geometry_bounds_in_host_mm(created, target_opening)
    # Independent authored envelope: x 0..900, y 50..100, z 0..2100 mm.
    for axis, expected in {'x': [0., 900.], 'y': [50., 100.], 'z': [0., 2100.]}.items():
        assert bounds[axis] == pytest.approx(expected, abs=1e-5)
    resolution = json.loads((run / 'resolution.json').read_text(encoding='utf8'))
    assert 'door_installation_anchor' not in resolution['operations'][0]['parameters']
    assert created.IsDefinedBy[0].RelatingType.GlobalId == reference.IsDefinedBy[0].RelatingType.GlobalId
    manifest = json.loads((run / result.artifacts['manifest']).read_text(encoding='utf8'))
    evidence = next(a['path'] for a in manifest['artifacts'] if a['role'] == 'public_evidence')
    application = json.loads((run / evidence).read_text(encoding='utf8'))['evidence']['application']
    assert application['published'] and application['valid']


def _no_output(result, run):
    assert result.status != 'succeeded'
    assert not result.successful_artifact_publishable
    assert 'successful_ifc' not in result.artifacts
    assert not list(run.rglob('application-candidate.ifc'))
    assert not list(run.rglob('repaired.ifc'))


@pytest.mark.parametrize('millimetres', [False, True], ids=['m', 'mm'])
def test_existing_no_occurrence_anchor_legacy_path_supports_rectangle(tmp_path, millimetres):
    model, opening, reference, _ = direct_rectangle_scene(millimetres=millimetres)
    provider = CompatibilityProvider(omit_reference=True)
    _, result, run = _start(tmp_path, model, provider)
    _successful_rectangle(result, run, opening, reference)
    assert provider.stage2_calls


@pytest.mark.parametrize('millimetres,angle', [(False, 0.), (False, 90.), (True, 0.), (True, 90.)],
                         ids=['m-0', 'm-90', 'mm-0', 'mm-90'])
def test_offered_direct_reference_keeps_supported_legacy_geometry(tmp_path, millimetres, angle):
    model, opening, reference, _ = direct_rectangle_scene(millimetres=millimetres, angle=angle)
    provider = CompatibilityProvider()
    source, result, run = _start(tmp_path, model, provider)
    _successful_rectangle(result, run, opening, reference)
    assert provider.stage2_calls
    context = json.loads((run / 'api-context.json').read_text(encoding='utf8'))
    assert context['installation_references']['offline-repair-0']['reference_global_id'] == reference.GlobalId
    assert all('private' not in str(call['state']) for call in provider.calls)
    assert source.name == 'public.ifc'


class CrashAfterIntent(RepairAPI):
    def _resolve_and_finish(self, *args, **kwargs):
        raise RuntimeError('synthetic crash after committed public intent')


def _committed_intent(tmp_path):
    model, opening, reference, _ = direct_rectangle_scene(millimetres=True, angle=90.)
    source = tmp_path / 'public.ifc'
    model.write(str(source))
    provider = CompatibilityProvider()
    with pytest.raises(RuntimeError, match='synthetic crash'):
        CrashAfterIntent(tmp_path / 'run', provider=provider, scene_grounding=True).start(source, REQUEST)
    run = next((tmp_path / 'run/runs').iterdir())
    return source, opening, reference, provider, run


def test_direct_reference_is_restored_from_committed_context(tmp_path):
    source, opening, reference, provider, run = _committed_intent(tmp_path)
    before = source.read_bytes()
    calls = len(provider.calls)
    result = RepairAPI(tmp_path / 'run', provider=provider).resume(run.name)
    _successful_rectangle(result, run, opening, reference)
    assert len(provider.calls) > calls
    assert all('## Immutable bindings' in call['prompt'] for call in provider.calls[calls:])
    assert source.read_bytes() == before


def test_normal_mapped_reference_still_uses_anchor(tmp_path):
    model, _, reference, _, _ = scene(angle=90., sign=-1.)
    provider = CompatibilityProvider()
    _, result, run = _start(tmp_path, model, provider)
    assert result.status == 'succeeded', result.to_dict()
    params = json.loads((run / 'resolution.json').read_text(encoding='utf8'))['operations'][0]['parameters']
    assert params['door_installation_anchor']['reference_global_id'] == reference.GlobalId
    assert params['door_installation_anchor']['mapped_body']


@pytest.mark.parametrize('fault', ['missing_body', 'wrong_mapping', 'rotated_reference', 'different_depth'])
def test_maps_present_never_fall_back_on_invalid_reference(tmp_path, fault):
    model, opening, reference, _, unit = scene()
    if fault == 'missing_body':
        reference.Representation.Representations[0].RepresentationIdentifier = 'Other'
    elif fault == 'wrong_mapping':
        original = reference.Representation.Representations[0].Items[0].MappingSource
        reference.Representation.Representations[0].Items[0].MappingSource = model.createIfcRepresentationMap(
            original.MappingOrigin, original.MappedRepresentation,
        )
    elif fault == 'rotated_reference':
        reference.ObjectPlacement.RelativePlacement.RefDirection.DirectionRatios = (0., 1., 0.)
    else:
        opening.Representation.Representations[0].Items[0].SweptArea.YDim = 200 * unit
    provider = CompatibilityProvider()
    _, result, run = _start(tmp_path, model, provider)
    _no_output(result, run)
    assert not provider.stage2_calls


@pytest.mark.parametrize('fault', ['missing_type', 'ambiguous_type', 'wrong_type_class'])
def test_direct_reference_requires_unique_door_style(tmp_path, fault):
    model, _, reference, _ = direct_rectangle_scene()
    relation = reference.IsDefinedBy[0]
    if fault == 'missing_type':
        model.remove(relation)
    elif fault == 'ambiguous_type':
        model.createIfcRelDefinesByType(ifcopenshell.guid.new(), reference.OwnerHistory,
                                       None, None, [reference], relation.RelatingType)
    else:
        other = model.create_entity('IfcWindowStyle', GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=reference.OwnerHistory, Name='Wrong public type class',
            ConstructionType='NOTDEFINED', OperationType='NOTDEFINED',
            ParameterTakesPrecedence=False, Sizeable=False)
        relation.RelatingType = other
    provider = CompatibilityProvider()
    _, result, run = _start(tmp_path, model, provider)
    _no_output(result, run)
    assert not provider.stage2_calls


@pytest.mark.parametrize('fault', ['unoffered', 'prototype_mismatch', 'injected_anchor', 'malformed_stage2'])
def test_legacy_eligibility_does_not_authorize_provider_tampering(tmp_path, fault):
    model, *_ = direct_rectangle_scene()
    provider = CompatibilityProvider(fault=fault)
    _, result, run = _start(tmp_path, model, provider)
    _no_output(result, run)
    if fault in {'injected_anchor', 'malformed_stage2'}:
        assert provider.stage2_calls, result.to_dict()
    else:
        assert not provider.stage2_calls


@pytest.mark.parametrize('fault,reason', [
    ('target', 'DOOR_INSTALLATION_BINDING_MISMATCH'),
    ('reference_class', None),
    ('prototype', None),
    ('source', 'DOOR_INSTALLATION_SOURCE_MISMATCH'),
])
def test_legacy_selection_still_verifies_bound_resolver_inputs(tmp_path, fault, reason):
    source, opening, reference, provider, run = _committed_intent(tmp_path)
    before = source.read_bytes()
    context = json.loads((run / 'api-context.json').read_text(encoding='utf8'))
    installation = deepcopy(context['installation_references'])
    body = deepcopy(context['intent'])
    if fault == 'target':
        installation['offline-repair-0']['target_global_id'] = reference.GlobalId
    elif fault == 'reference_class':
        installation['offline-repair-0']['reference_global_id'] = opening.GlobalId
    elif fault == 'prototype':
        body['operations'][0]['prototype_intent']['reference'] = 'not-the-bound-type'
    else:
        source.write_bytes(before + b'\n')  # deliberate test fault, never a runtime source edit
    registry = create_default_registry()
    intent = RepairIntent.from_dict(body, registry=registry)
    state = json.loads((run / 'state.json').read_text(encoding='utf8'))
    with SQLiteIndexRepository.open(run / 'index/targets.sqlite',
            expected_source_ifc_sha256=state['source']['sha256']) as repository:
        result = resolve_repair_intent(intent, repository,
            expected_source_sha256=state['source']['sha256'], operation_registry=registry,
            source_ifc_path=source, installation_references=installation)
    # A nonexistent prototype already pauses in the door parameter resolver.
    # Preserve that safe earlier boundary, rather than imposing a later code.
    assert result.status == ('clarification_required' if fault == 'prototype' else 'failed')
    if reason is not None:
        assert result.reason_code == reason
    assert not provider.stage2_calls
    assert not (run / 'changeset').exists()
    assert not list(run.rglob('repaired.ifc'))
    assert source.read_bytes() == (before + b'\n' if fault == 'source' else before)
