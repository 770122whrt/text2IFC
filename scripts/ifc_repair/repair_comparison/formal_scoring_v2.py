"""Versioned correction of preservation; all target policies stay unchanged.

Use ``score`` for a full evaluation. ``rescore_preservation`` reuses an
immutable, hash-bound legacy report's unaffected checks and changes only the
defective preservation projection. Both baseline and current outputs can be
re-evaluated without requesting a model or overwriting their original reports.
"""
from copy import deepcopy
from pathlib import Path

import ifcopenshell

from . import formal_scoring as legacy
from .contracts import sha256
from .preservation_v2 import VERSION, preservation

SCHEMA = 'repair-comparison-formal-score/0.2'


def rescore_preservation(report, damaged_path, result_path, *, policy):
    if report['schema_version'] != legacy.SCHEMA or report['policy'] != legacy._policy(policy):
        raise ValueError('LEGACY_SCORE_OR_POLICY_BINDING_MISMATCH')
    fixed = deepcopy(report)
    fixed['schema_version'] = SCHEMA
    fixed['evaluator_revision'] = {
        'preservation': VERSION, 'legacy_schema': legacy.SCHEMA,
        'unchanged': ['input', 'target matching', 'quantity', 'component checks',
                      'relationships', 'IFC validator', 'policy tolerances', 'clarification'],
    }
    if result_path is None:
        if report.get('input_bindings', {}).get('result_sha256'):
            raise ValueError('NO_OUTPUT_SCORE_HAS_RESULT_BINDING')
        return fixed
    damaged_path, result_path = Path(damaged_path), Path(result_path)
    bindings = report['input_bindings']
    if (sha256(damaged_path) != bindings['damaged_sha256']
            or sha256(result_path) != bindings['result_sha256']):
        raise ValueError('SCORE_INPUT_BINDING_MISMATCH')
    # Invalid/duplicate/unknown checks cannot become valid by this correction.
    if (report.get('duplicate_guids') or report.get('errors') or report.get('evaluator_error')
            or report.get('checks', {}).get('reopen') is not True):
        return fixed
    damaged, result = ifcopenshell.open(str(damaged_path)), ifcopenshell.open(str(result_path))
    old = {entity.GlobalId for entity in damaged.by_type('IfcProduct')}
    new = [entity.GlobalId for entity in result.by_type('IfcProduct') if entity.GlobalId not in old]
    try:
        evidence = preservation(damaged, result, new)
    except Exception as error:
        fixed['errors'].append(f'PRESERVATION:{type(error).__name__}:{error}')
        fixed['status'] = 'not_evaluable'
        legacy._unavailable(fixed)
        return legacy._aliases(fixed)
    fixed['preservation'] = {**evidence, 'status': 'scored'}
    metrics = fixed['metrics']
    changed = set(evidence['removed_roots']) | set(evidence['modified_roots']) | set(evidence['extra_old_object_relations']) | set(evidence['unrelated_added_roots'])
    metrics['collateral_changes'] = {
        'status': 'scored', 'affected_root_count': len(changed),
        'affected_root_ids': sorted(changed), 'preservation_pass': evidence['passed'],
        'extra_products': not fixed['checks']['no_extra_products'],
    }
    component, relation = metrics['component_completion'], metrics['relation_completion']
    gates = [metrics['ifc_validation_pass']['value'], evidence['passed'],
             *fixed['checks'].values(),
             None if component['value'] is None else component['numerator'] == component['denominator'],
             relation['numerator'] == relation['denominator']]
    success = False if any(value is False for value in gates) else None if any(value is None for value in gates) else True
    # Preserve review-required target checks; remove only the old projection's
    # false rejection. Never infer target success from the native Harness.
    fixed['status'] = 'needs_review' if success is None else 'scored'
    metrics['task_success'] = legacy._flag(success, fixed['status'])
    metrics['interactive_success'] = legacy._flag(
        False if fixed['clarification']['success'] is False or success is False else success,
        fixed['status'])
    return legacy._aliases(fixed)


def score(case, result_path, *, terminal, events=(), policy=None):
    report = legacy.score(case, result_path, terminal=terminal, events=events, policy=policy)
    return rescore_preservation(report, Path(case) / 'private/mutation/damaged.ifc',
                               result_path, policy=policy)
