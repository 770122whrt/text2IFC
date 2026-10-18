"""V2 remains an independent full scorer and binds cached unaffected checks."""
from copy import deepcopy

import ifcopenshell.guid
import pytest

from scripts.ifc_repair.repair_comparison import formal_scoring as legacy
from scripts.ifc_repair.repair_comparison import formal_scoring_v2 as fixed
from tests.ifc_repair.repair_comparison.test_formal_scoring import cases
from tests.ifc_repair.repair_comparison.test_preparation import sample


def result_file(case, model):
    path = case / 'result.ifc'
    model.write(str(path))
    return path


@pytest.mark.parametrize('kinds,keep', [(('door',), True), (('door',), False),
                                      (('window', 'window'), False), (('door', 'door'), False),
                                      (('window', 'door'), False)])
def test_full_scorer_preserves_frozen_checks_and_legacy_report(cases, kinds, keep):
    case, model, spec, policy = cases(kinds, keep)
    for target in spec['targets']:
        model.by_guid(target['target_guid']).GlobalId = ifcopenshell.guid.new()
        if not target['preserve_opening']:
            model.by_guid(target['opening_guid']).GlobalId = ifcopenshell.guid.new()
    path = result_file(case, model)
    old = legacy.score(case, path, terminal='submitted', policy=policy)
    before = deepcopy(old)
    report = fixed.rescore_preservation(old, case / 'private/mutation/damaged.ifc', path, policy=policy)
    assert old == before
    assert report['schema_version'] == fixed.SCHEMA != old['schema_version']
    assert report['repair_success'] is True, report
    assert report['target_results'] == old['target_results']
    for name in ('quantity_completion', 'component_completion', 'relation_completion', 'ifc_validation_pass'):
        assert report['metrics'][name] == old['metrics'][name]


@pytest.mark.parametrize('fault', ['width', 'missing_fill', 'other_property', 'wall_geometry'])
def test_full_v2_does_not_excuse_target_or_preservation_faults(cases, fault):
    case, model, spec, policy = cases(('door',), True)
    if fault == 'width':
        model.by_guid(spec['targets'][0]['target_guid']).OverallWidth += .2
    elif fault == 'missing_fill':
        model.remove(model.by_guid(spec['targets'][0]['target_guid']).FillsVoids[0])
    elif fault == 'other_property':
        model.by_guid(policy['targets']['target-1']['reference_guid']).Name = 'unauthorized'
    else:
        model.by_guid(spec['targets'][0]['wall_guid']).Representation = None
    report = fixed.score(case, result_file(case, model), terminal='submitted', policy=policy)
    assert report['repair_success'] is False, report


@pytest.mark.parametrize('tamper', ['artifact', 'damaged', 'policy'])
def test_reuse_requires_unchanged_input_and_policy(cases, tamper):
    case, model, spec, policy = cases(('door',), True)
    path = result_file(case, model)
    old = legacy.score(case, path, terminal='submitted', policy=policy)
    damaged = case / 'private/mutation/damaged.ifc'
    if tamper == 'policy':
        policy = {**policy, 'length_mm': 2.}
    else:
        target = path if tamper == 'artifact' else damaged
        target.write_bytes(target.read_bytes() + b'\n')
    with pytest.raises(ValueError, match='BINDING_MISMATCH'):
        fixed.rescore_preservation(old, damaged, path, policy=policy)


def test_no_output_keeps_denominators_and_invalid_output_stays_failure(cases):
    case, model, spec, policy = cases(('window', 'door'), False)
    report = fixed.score(case, None, terminal='no_output', policy=policy)
    assert report['repair_success'] is False
    assert report['metrics']['component_completion']['denominator'] == 2
    path = case / 'bad.ifc'
    path.write_text('not IFC', encoding='utf8')
    report = fixed.score(case, path, terminal='submitted', policy=policy)
    assert report['repair_success'] is False
