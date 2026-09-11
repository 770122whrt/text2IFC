"""Post-run only: preserve failures, measure usage, replay a synthetic local patch."""
from pathlib import Path
import copy
import hashlib
import json

from text2ifc_agent.early_recovery import build_field_recovery_group
from text2ifc_agent.candidate_index import build_candidate_index
from text2ifc_agent.changeset_apply import apply_changeset
from text2ifc_agent.revisions import hash_json_value
from text2ifc_contract.validation_v2 import validate_v2_document

ROOT = Path(__file__).resolve().parent
RUN = ROOT / 'live-run/runs/916d8afe752160e3'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    source = RUN / 'generator/parsed-output.json'
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    candidate = read(source)
    repair = read(RUN / 'repair/parsed-output.json')
    issues = [vars(i) for i in validate_v2_document(candidate)]
    group = build_field_recovery_group(candidate, issues)
    assert group['eligible'] and len(issues) == 9
    index = build_candidate_index(candidate)
    expected = read(RUN / 'expected-facts.json')
    revision = {'schema_version': 'text2ifc/bim-json-revision/1.0', 'revision_id': 'revision-00',
        'sequence': 0, 'parent_revision_id': None, 'candidate_hash': index['candidate_hash'],
        'expected_facts_hash': hash_json_value(expected), 'component_hashes': index['component_hashes'],
        'source_route': 'initial_generation', 'artifacts': {'candidate': 'generator/parsed-output.json'}}
    cs = {'schema_version': 'text2ifc/bim-json-changeset/1.0', 'changeset_id': 'offline-diagnostic',
        'base_revision_id': 'revision-00', 'base_candidate_hash': index['candidate_hash'],
        'expected_facts_hash': revision['expected_facts_hash'], 'scope_id': group['scope']['scope_id'],
        'source_issue_ids': group['scope']['source_issue_ids'], 'operations': []}
    for entity_id, required in group['required_field_values'].items():
        attrs = copy.deepcopy(index['entities'][entity_id]['attributes'])
        for path in group['scope']['allowed_paths'][entity_id]:
            attrs.pop(path.rsplit('/', 1)[-1], None)
        attrs.update({p.rsplit('/', 1)[-1]: v for p, v in required.items()})
        cs['operations'].append({'operation_id': 'fix-' + entity_id, 'op': 'update_entity',
            'target_id': entity_id, 'target_component_hash': index['component_hashes'][entity_id],
            'changes': {'/attributes': attrs}, 'evidence_refs': [i + ':/actual' for i in cs['source_issue_ids']]})
    result = apply_changeset(candidate=candidate, changeset=cs, scope=group['scope'],
        base_revision=revision, expected_facts=expected, allow_field_containers=True,
        required_field_values=group['required_field_values'])
    assert result['valid'], result['issues']
    before_rel = {r['id']: r for r in candidate['relationships']}
    after_rel = {r['id']: r for r in result['candidate']['relationships']}
    assert before_rel == after_rel
    after_index = build_candidate_index(result['candidate'])
    changed = sorted(k for k, v in index['component_hashes'].items() if after_index['component_hashes'][k] != v)
    assert changed == sorted(group['scope']['entity_ids'])
    assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
    usage = []
    for stage in ['design-brief', 'generator', 'repair']:
        meta = read(RUN / stage / 'response-metadata.json')
        usage.append({'stage': stage, 'response_id': meta['response_id'], 'model': meta['model'], 'usage': meta['usage']})
    ledger = read(RUN / 'generation-budget.json')
    result = {'evidence_class': 'offline_diagnostic_of_frozen_live_failure', 'new_provider_calls': 0,
        'source_sha256': digest, 'original_schema_issues': issues,
        'live_full_repair_schema_issues': [vars(i) for i in validate_v2_document(repair)],
        'original_relationship_count': len(before_rel), 'live_repair_relationship_count': len(repair['relationships']),
        'live_repair_removed_relationships': sorted(set(before_rel) - {r['id'] for r in repair['relationships']}),
        'synthetic_local_patch': {'contract_valid': True, 'changed_component_ids': changed,
            'relationships_preserved': True, 'source_bytes_preserved': True,
            'ifc_compiled': False, 'quality_claim': 'None; hand-authored diagnostic, not a real Provider repair or final IFC.'},
        'live_usage': usage, 'new_live_tokens': sum(m['usage']['total_tokens'] for m in usage),
        'cumulative_calls': len(ledger['attempts']),
        'cumulative_tokens': sum(a['tokens_charged'] for a in ledger['attempts']),
        'cumulative_active_seconds': sum(a['elapsed_seconds'] for a in ledger['attempts']),
        'limits': ledger['limits']}
    with (ROOT / 'diagnosis.json').open('x', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(json.dumps({k: result[k] for k in ['new_live_tokens', 'cumulative_calls', 'cumulative_tokens', 'live_repair_removed_relationships']}))


if __name__ == '__main__':
    main()
