"""Continue a preserved candidate through production repair, gates and Audit.

The failed parent and its session budget remain untouched. Live execution uses
the campaign's cumulative budget and admission; no new token grant is created.
"""
from pathlib import Path
import argparse
import json
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT/'src'), str(ROOT/'.deps/python312')]
from scripts.ifc2text.component_campaign import load, save, digest, now


def prepare_case(source, target, *, recovery=None):
    source, target = Path(source).resolve(), Path(target).resolve()
    if target == source or target.is_relative_to(source):
        raise ValueError('CONTINUATION_MUST_BE_OUTSIDE_PARENT')
    closure = None
    guard = 'generation-budget-decision.json'
    if recovery is None:
        if load(source/guard).get('status') != 'budget_blocked':
            raise ValueError('BUDGET_BLOCKED_PARENT_REQUIRED')
    elif recovery == 'polygon_closure':
        guard = 'case-result.json'
        terminal = load(source/guard)
        if terminal.get('final_status') != 'blocked' or terminal.get('output_type') != 'none':
            raise ValueError('BLOCKED_INVALID_PARENT_REQUIRED')
        from text2ifc_agent.generator import validate_generation_document
        from text2ifc_agent.live_pipeline import _repair_allowed_change_paths, _repair_evidence_by_path
        from text2ifc_agent.polygon_closure import recover_repair_polygons
        original = load(source/'generator/parsed-output.json')
        feedback = validate_generation_document(original)['diagnostics']
        if not feedback or feedback != load(source/'generator/validation.json')['issues']:
            raise ValueError('PARENT_VALIDATION_MISMATCH')
        metrics = load(source/'repair/metrics.json')
        if metrics.get('valid') or metrics.get('provider_call_count') != 1:
            raise ValueError('FAILED_REPAIR_RESPONSE_REQUIRED')
        paths = _repair_allowed_change_paths(feedback,candidate=original)
        closure = recover_repair_polygons(original,load(source/'repair/parsed-output.json'),
            allowed_change_paths=paths,evidence_by_path=_repair_evidence_by_path(feedback,paths))
        if not closure['eligible']:
            raise ValueError('CLOSURE_RECOVERY_NOT_ELIGIBLE')
    else:
        raise ValueError('UNKNOWN_CONTINUATION_RECOVERY')
    brief = load(source/'design-brief.json')
    if brief.get('status') != 'ready':
        raise ValueError('READY_PARENT_BRIEF_REQUIRED')
    if brief != load(source/'design-brief/design-brief.json') or brief != load(source/'generator/design-brief.json'):
        raise ValueError('PARENT_BRIEF_COPIES_CONFLICT')
    budget = load(source/'generation-budget.json')
    if any(a.get('status') == 'reserved' for a in budget.get('attempts', [])):
        raise ValueError('UNSETTLED_PARENT_BUDGET')
    from text2ifc_agent.generator import validate_generation_document
    candidate = closure['candidate'] if closure else load(source/'generator/candidate.json')
    if validate_generation_document(candidate)['status'] != 'formal':
        raise ValueError('FORMAL_SAVED_CANDIDATE_REQUIRED')
    names = ['design-brief.json','expected-facts.json','generation-contract.json']
    for name in ['candidate-origin.json','semantic-capabilities.json','generation-strategy.json']:
        if (source/name).is_file():
            names.append(name)
    for directory in ['design-brief','generator','repair']:
        names.extend(p.relative_to(source).as_posix() for p in (source/directory).iterdir()
                     if p.is_file() and p.suffix in {'.json','.md','.txt'} and '.private.' not in p.name)
    hashes = {name:digest(source/name) for name in names}
    target.mkdir(parents=True, exist_ok=False)
    for name in names:
        destination = target/name
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source/name,destination)
    hashes.update({name:digest(source/name) for name in ['generation-budget.json',guard]})
    sealed = {name:sha for name,sha in hashes.items()
              if name in {'design-brief.json','expected-facts.json','generation-contract.json'}
              or name.startswith('design-brief/')
              or (name.startswith('generator/') and Path(name).name not in {'candidate.json','validation.json','metrics.json'})}
    lineage = {'schema_version':'text2ifc/component-candidate-continuation/1.0',
        'parent':str(source),'parent_hashes':hashes,'sealed_child_inputs':sealed,
        'parent_generator_evidence_class':load(source/'generator/metrics.json').get('evidence_class'),
        'budget_policy':'All new calls charge the existing cumulative allocation; parent budget remains frozen.',
        'created_at':now()}
    save(target/'continuation-lineage.json',lineage)
    if closure:
        from text2ifc_agent.interactive_cli_flow import _promote_repaired_candidate
        save(target/'polygon-closure-recovery.json',{k:v for k,v in closure.items() if k!='candidate'})
        save(target/'recovered-candidate.json',closure['candidate'])
        _promote_repaired_candidate(target,target/'recovered-candidate.json')
        save(target/'candidate-origin.json',{'candidate_origin':'live_repair_response_with_deterministic_polygon_closure',
            'live_acceptance_eligible':True,'raw_parent_response':str(source/'repair/response.raw.json'),
            'raw_parent_response_sha256':digest(source/'repair/response.raw.json'),
            'recovery_evidence':'polygon-closure-recovery.json','new_provider_calls':0})
    verify_lineage(target)
    return lineage


def verify_lineage(case):
    case = Path(case)
    lineage = load(case/'continuation-lineage.json')
    for name,sha in lineage['parent_hashes'].items():
        if digest(Path(lineage['parent'])/name) != sha:
            raise ValueError('PARENT_CHANGED:'+name)
    for name,sha in lineage['sealed_child_inputs'].items():
        if digest(case/name) != sha:
            raise ValueError('SEALED_INPUT_CHANGED:'+name)
    return lineage


def prepare_regeneration_case(source,target):
    """Start a separate generation attempt using only the existing public Brief."""
    from collections import Counter
    source,target=Path(source).resolve(),Path(target).resolve()
    if target==source or target.is_relative_to(source):
        raise ValueError('CONTINUATION_MUST_BE_OUTSIDE_PARENT')
    brief=load(source/'design-brief.json')
    if brief.get('status')!='ready' or brief!=load(source/'design-brief/design-brief.json'):
        raise ValueError('READY_PARENT_BRIEF_REQUIRED')
    budget=load(source/'generation-budget.json')
    if any(a.get('status')=='reserved' for a in budget.get('attempts',[])):
        raise ValueError('UNSETTLED_PARENT_BUDGET')
    names=['design-brief.json','expected-facts.json','generation-contract.json']
    names += [p.relative_to(source).as_posix() for p in (source/'design-brief').iterdir()
              if p.is_file() and p.suffix in {'.json','.md','.txt'} and '.private.' not in p.name]
    hashes={name:digest(source/name) for name in names}
    prior_names=['generation-budget.json']+[p.relative_to(source).as_posix()
        for directory in ['generator','repair'] for p in (source/directory).iterdir()
        if p.is_file() and p.suffix in {'.json','.md','.txt'} and '.private.' not in p.name]
    hashes.update({name:digest(source/name) for name in prior_names})
    target.mkdir(parents=True,exist_ok=False)
    for name in names:
        (target/name).parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source/name,target/name)
    prior=load(source/'generator/parsed-output.json')
    feedback={'reason':'Previous generation did not complete the requested building; regenerate the full document from the frozen public Brief.',
        'expected_counts':load(source/'expected-facts.json').get('total_counts',{}),
        'previous_output_counts':dict(Counter(e['ifc_class'] for e in prior.get('entities',[]))),
        'instruction':'Include every explicitly requested entity, component, opening, slab, material and relationship. Preserve all public dimensions and placements. Return Draft if genuinely missing information; do not omit whole categories from a Formal document.'}
    save(target/'regeneration-feedback.json',feedback)
    lineage={'schema_version':'text2ifc/component-candidate-continuation/1.0','parent':str(source),
        'parent_hashes':hashes,'sealed_child_inputs':{**{n:hashes[n] for n in names},
            'regeneration-feedback.json':digest(target/'regeneration-feedback.json')},
        'parent_generator_evidence_class':load(source/'generator/metrics.json').get('evidence_class'),
        'budget_policy':'Same cumulative allocation; no Brief call or parent budget reset.', 'created_at':now()}
    save(target/'continuation-lineage.json',lineage)
    verify_lineage(target)
    return lineage


def regenerate_case(case,provider):
    from text2ifc_agent.live_pipeline import run_generator_stage,run_repair_stage
    from text2ifc_agent.interactive_cli_flow import _promote_repaired_candidate
    case=Path(case);verify_lineage(case);start_once(case,'continuation-regenerate')
    result=run_generator_stage(provider=provider,output_dir=case/'generator',design_source_dir=case/'design-brief',
        case_id='component-regeneration',generation_feedback=load(case/'regeneration-feedback.json'),generator_call_index=2)
    save(case/'continuation-regenerate-result.json',result)
    repair=run_repair_stage(provider_factory=lambda:provider,output_dir=case/'repair',
        generator_source_dir=case/'generator',case_id='component-regeneration')
    save(case/'continuation-repair-result.json',repair)
    if repair.get('valid') and (case/'repair/repaired-candidate.json').is_file():
        _promote_repaired_candidate(case,case/'repair/repaired-candidate.json')
    if result.get('valid') or repair.get('valid'):
        _,gates=refresh_gates(case)
        save(case/'continuation-gates-result.json',gates)
    verify_lineage(case)
    return result


def start_once(case, stage):
    with (Path(case)/(stage+'-started.json')).open('x',encoding='utf-8') as handle:
        json.dump({'stage':stage,'started_at':now()},handle)


def refresh_gates(case):
    from text2ifc_agent.live_pipeline import run_candidate_gate_stage, run_semantic_coverage_stage
    verify_lineage(case)
    coverage = run_semantic_coverage_stage(case_dir=case,output_dir=case,case_id='component-continuation')
    gates = run_candidate_gate_stage(case_dir=case,output_dir=case,case_id='component-continuation')
    return coverage, gates


def repair_case(case, provider_factory):
    from text2ifc_agent.live_pipeline import run_repair_stage
    from text2ifc_agent.interactive_cli_flow import _promote_repaired_candidate
    case = Path(case)
    verify_lineage(case)
    start_once(case,'continuation-repair')
    coverage,gates = refresh_gates(case)
    if not coverage['valid']:
        raise ValueError('SEMANTIC_COVERAGE_BLOCKS_GEOMETRY_REPAIR')
    issues = list(gates['geometry_feedback']['issues'])
    for gate in gates['gate_summary']['gates']:
        if gate.get('name') == 'dynamic_opening_fill':
            issues.extend(gate.get('issues', []))
    save(case/'continuation-repair-feedback.json',issues)
    save(case/'continuation-base-candidate.json',load(case/'generator/candidate.json'))
    prior = load(case/'repair/metrics.json').get('repair_attempt_count',0)
    result = run_repair_stage(provider_factory=provider_factory,output_dir=case/'repair',
        generator_source_dir=case/'generator',case_id='component-continuation',
        geometry_feedback=issues,prior_attempt_count=prior)
    save(case/'continuation-repair-result.json',result)
    if result.get('valid') and result.get('route') == 'repair_attempted':
        _promote_repaired_candidate(case,case/'repair/repaired-candidate.json')
        coverage,gates = refresh_gates(case)
        save(case/'continuation-gates-result.json',gates)
    verify_lineage(case)
    return result


def repair_fields_case(case, provider_factory, *, attempt=1, max_attempts=3):
    """Resume invalid scalar fields without replacing the preserved raw output."""
    from text2ifc_agent.early_recovery import build_field_recovery_group
    from text2ifc_agent.generator import validate_generation_document
    from text2ifc_agent.live_pipeline import run_repair_stage
    from text2ifc_agent.interactive_cli_flow import _promote_repaired_candidate
    case = Path(case)
    verify_lineage(case)
    if type(attempt) is not int or attempt < 1:
        raise ValueError('POSITIVE_EXPLICIT_ATTEMPT_REQUIRED')
    name = 'field-repair' if attempt == 1 else f'field-repair-{attempt:02d}'
    if attempt > 1:
        previous = 'field-repair' if attempt == 2 else f'field-repair-{attempt-1:02d}'
        if load(case/f'continuation-{previous}-result.json').get('valid') is not False:
            raise ValueError('PREVIOUS_FAILED_FIELD_ATTEMPT_REQUIRED')
    start_once(case, 'continuation-'+name)
    source = case/'generator'
    raw_hash = digest(source/'parsed-output.json')
    candidate = load(source/'parsed-output.json')
    feedback = validate_generation_document(candidate)['diagnostics']
    if feedback != load(source/'validation.json')['issues']:
        raise ValueError('SAVED_VALIDATION_MISMATCH')
    group = build_field_recovery_group(candidate, feedback)
    if not group['eligible']:
        raise ValueError('LOCAL_FIELD_RECOVERY_NOT_ELIGIBLE')
    save(case/f'continuation-{name}-scope.json', group)
    result = run_repair_stage(provider_factory=provider_factory,
        output_dir=case/name, generator_source_dir=source,
        case_id='component-field-repair', max_field_attempts=max_attempts)
    save(case/f'continuation-{name}-result.json', result)
    if result.get('valid') and (case/name/'repaired-candidate.json').is_file():
        _promote_repaired_candidate(case, case/name/'repaired-candidate.json')
        _, gates = refresh_gates(case)
        save(case/'continuation-gates-result.json', gates)
    if digest(source/'parsed-output.json') != raw_hash:
        raise ValueError('RAW_GENERATOR_RESPONSE_CHANGED')
    verify_lineage(case)
    return result


def prepare_audit_case(source, target, *, repair_name):
    """Materialize canonical Audit inputs while preserving separate failed repairs."""
    from text2ifc_agent.generator import validate_generation_document
    source, target = Path(source).resolve(), Path(target).resolve()
    verify_lineage(source)
    repair = (source/repair_name).resolve()
    if repair.parent != source or target == source or target.is_relative_to(source):
        raise ValueError('AUDIT_CHILD_PATH_INVALID')
    candidate = load(source/'generator/candidate.json')
    if (validate_generation_document(candidate)['status'] != 'formal'
            or candidate != load(repair/'repaired-candidate.json')
            or load(repair/'metrics.json').get('valid') is not True
            or load(repair/'route.json').get('route') != 'repair_attempted'):
        raise ValueError('SUCCESSFUL_MATCHING_REPAIR_REQUIRED')
    copies = {n:n for n in ['design-brief.json','expected-facts.json','generation-contract.json']}
    for n in ['candidate.json','candidate-origin.json','semantic-capabilities.json','generation-strategy.json']:
        if (source/n).is_file():copies[n]=n
    for directory, destination in [(source/'design-brief','design-brief'),(source/'generator','generator'),(repair,'repair')]:
        for p in directory.rglob('*'):
            if p.is_file() and p.suffix in {'.json','.md','.txt'} and '.private.' not in p.name:
                copies[(Path(destination)/p.relative_to(directory)).as_posix()] = p.relative_to(source).as_posix()
    hashes = {p.relative_to(source).as_posix():digest(p) for p in source.rglob('*') if p.is_file()}
    target.mkdir(parents=True,exist_ok=False)
    for destination, original in copies.items():
        p = target/destination;p.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source/original,p)
    lineage = {'schema_version':'text2ifc/component-candidate-continuation/1.0',
        'parent':str(source),'parent_hashes':hashes,
        'sealed_child_inputs':{d:hashes[s] for d,s in copies.items()
            if d not in {'candidate.json','generator/candidate.json','generator/validation.json','generator/metrics.json'}},
        'parent_generator_evidence_class':load(source/'generator/metrics.json').get('evidence_class'),
        'selected_repair_source':repair_name,'copy_map':copies,
        'budget_policy':'Audit only under the same cumulative allocation; no generator or repair call.',
        'created_at':now()}
    save(target/'continuation-lineage.json',lineage)
    verify_lineage(target)
    return lineage


def audit_case(case, provider):
    from text2ifc_agent.live_pipeline import run_audit_report_stage, run_final_acceptance_stage
    case = Path(case)
    coverage,gates = refresh_gates(case)
    if not coverage['valid'] or not gates['deterministic_gates_passed']:
        raise ValueError('DETERMINISTIC_GATES_BLOCK_AUDIT')
    start_once(case,'continuation-audit')
    result = run_audit_report_stage(provider=provider,case_dir=case,case_id='component-continuation')
    save(case/'continuation-audit-result.json',result)
    if result.get('valid') and result.get('status') == 'accepted':
        accepted = run_final_acceptance_stage(case_dir=case,output_dir=case/'accepted',case_id='component-continuation')
        save(case/'continuation-acceptance-result.json',accepted)
    verify_lineage(case)
    return result


def live(cfg, stage):
    from scripts.ifc2text.component_campaign import admitted, budget_for, runtime
    admitted(cfg)
    case = ROOT/cfg['continuation']['case']
    if digest(case/'continuation-lineage.json') != cfg['continuation']['lineage_sha256']:
        raise ValueError('LINEAGE_CHANGED')
    lineage = verify_lineage(case)
    if lineage['parent_generator_evidence_class'] != 'live':
        raise ValueError('LIVE_PARENT_REQUIRED')
    budget = budget_for(cfg)
    budget.check_capacity('reconstruction')
    cap = cfg['audit_output_tokens'] if stage == 'audit' else cfg['generation_output_tokens']
    conf,client,provider = runtime(cfg,budget,'reconstruction',cap)
    receipt = (f"field-repair-{cfg['continuation']['field_attempt']:02d}"
               if stage == 'field-repair' and cfg['continuation'].get('field_attempt',1) > 1 else stage)
    try:
        result = (repair_case(case,lambda:provider) if stage == 'repair' else
                  repair_fields_case(case,lambda:provider,
                    attempt=cfg['continuation'].get('field_attempt',1),
                    max_attempts=cfg['continuation'].get('field_max_attempts',3)) if stage == 'field-repair' else
                  regenerate_case(case,provider) if stage == 'regenerate' else audit_case(case,provider))
        save(case/(receipt+'-continuation-budget.json'),budget.snapshot())
        admitted(cfg)
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except Exception as error:
        save(case/(receipt+'-continuation-failure.json'),{'error_type':type(error).__name__,
            'at':now(),'budget':budget.snapshot()})
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage',choices=['repair','audit','regenerate','field-repair'])
    parser.add_argument('--config',required=True)
    args = parser.parse_args()
    live(load(args.config),args.stage)
