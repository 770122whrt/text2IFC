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


def prepare_case(source, target):
    source, target = Path(source).resolve(), Path(target).resolve()
    if target == source or target.is_relative_to(source):
        raise ValueError('CONTINUATION_MUST_BE_OUTSIDE_PARENT')
    if load(source/'generation-budget-decision.json').get('status') != 'budget_blocked':
        raise ValueError('BUDGET_BLOCKED_PARENT_REQUIRED')
    brief = load(source/'design-brief.json')
    if brief.get('status') != 'ready':
        raise ValueError('READY_PARENT_BRIEF_REQUIRED')
    if brief != load(source/'design-brief/design-brief.json') or brief != load(source/'generator/design-brief.json'):
        raise ValueError('PARENT_BRIEF_COPIES_CONFLICT')
    budget = load(source/'generation-budget.json')
    if any(a.get('status') == 'reserved' for a in budget.get('attempts', [])):
        raise ValueError('UNSETTLED_PARENT_BUDGET')
    from text2ifc_agent.generator import validate_generation_document
    candidate = load(source/'generator/candidate.json')
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
    hashes.update({name:digest(source/name) for name in ['generation-budget.json','generation-budget-decision.json']})
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
    cap = cfg['generation_output_tokens'] if stage == 'repair' else cfg['audit_output_tokens']
    conf,client,provider = runtime(cfg,budget,'reconstruction',cap)
    try:
        result = repair_case(case,lambda:provider) if stage == 'repair' else audit_case(case,provider)
        save(case/(stage+'-continuation-budget.json'),budget.snapshot())
        admitted(cfg)
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except Exception as error:
        save(case/(stage+'-continuation-failure.json'),{'error_type':type(error).__name__,
            'at':now(),'budget':budget.snapshot()})
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage',choices=['repair','audit'])
    parser.add_argument('--config',required=True)
    args = parser.parse_args()
    live(load(args.config),args.stage)
