"""B thin adapter: unchanged RepairAPI, native clarification and publication.

This entry only accepts deterministic fixtures. Synchronous native execution
does not yet have an external watchdog; real isolation/timeout admission remains
stage 3/5 work. No environment Provider or credentials are loaded here.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import re
import shutil
import uuid

import jsonschema
from text2ifc_agent.providers import ProviderOutput
from text2ifc_ifc_repair.api import RepairAPI

from .contracts import safe_path
from .direct_runner import DirectRunner
from .ledger import TERMINAL
from .provider_observer import ObservedReplay


def fixture_intent(kind, query, parameters):
    """Hand-authored seam fixture, not a natural-language inference algorithm."""
    source = {'source_kind': 'user_request', 'reference': 'request:/text', 'excerpt': 'offline fixture'}
    operation, profile = {'door': ('fill_existing_opening_with_door', 'door.fill-existing-opening.v0.4'),
                          'window': ('add_window_with_opening_to_wall', 'window.add-with-opening.v0.3')}[kind]
    return {'schema_version': 'text2ifc/ifc-repair-intent-body/0.10', 'unsupported_requests': [],
            'semantic_bundles': [], 'provenance': [source], 'operations': [{
                'operation_id': 'offline-repair', 'operation_type': operation,
                'routing_intent': {'component_family': kind, 'action': 'fill_existing_opening' if kind == 'door' else 'add_with_opening', 'operation_profile': profile, 'source': source},
                'target_query': {'schema_version': 'text2ifc/ifc-target-query/0.1', **query},
                'parameters': parameters, 'attribute_intents': [], 'property_intents': [],
                'semantic_bundle_refs': [], 'quantity_intents': [], 'occurrence_reuse_intent': None,
                'prototype_intent': None, 'appearance_intent': None, 'provenance': [source]}]}


def _section(prompt, heading):
    return json.JSONDecoder().raw_decode(prompt.split(f'## {heading}', 1)[1].strip())[0]


def _draft(prompt, schema):
    """Echo only native public projection; never reads benchmark reference G."""
    from text2ifc_ifc_repair.operations import create_default_registry
    raw = _section(prompt, 'Resolved operation projection')['operations']
    operations, scope, evidence = [], [], []
    if isinstance(raw, dict):
        registry = create_default_registry()
        raw = [{'operation_id': key, **value,
                'target': registry.bind_resolved_target(value['operation_type'], value['target_global_id']),
                'evidence_refs': value['evidence_pointers']} for key, value in raw.items()]
    for op in raw:
        operations.append({k: op[k] for k in ('operation_id', 'operation_type', 'target', 'parameters', 'evidence_refs')})
        scope.extend(op.get('scope_ids') or op['target'].values())
        evidence.extend(op['evidence_refs'])
    lines = prompt.split('## Immutable bindings', 1)[1].split('## Resolved operation projection', 1)[0]
    bindings = dict(re.findall(r'^- ([^:]+): (.+)$', lines, re.MULTILINE))
    return {'schema_version': schema['$id'], 'draft_id': 'offline-draft',
            'base_model_fingerprint': bindings['model'], 'source_request_hash': bindings['source request'],
            'semantic_manifest_ref': bindings['semantic manifest ref'], 'semantic_manifest_sha256': bindings['semantic manifest hash'],
            'semantic_summary': _section(prompt, 'Semantic group counts'),
            'scope': {'target_ids': sorted(set(scope)), 'forbidden_ids': []}, 'evidence_refs': sorted(set(evidence)),
            'preconditions': [], 'postconditions': [], 'operations': operations}


class NativeReplayProvider:
    """Explicit fake native responses. Each provided item is consumed once."""
    def __init__(self, intents):
        self.intents = copy.deepcopy(intents)
        self.intent_offset = 0

    def generate_candidate(self, **kwargs):
        if kwargs['state']['stage'] == 'ifc_repair_intent':
            value = self.intents[self.intent_offset]
            self.intent_offset += 1
        else:
            value = _draft(kwargs['prompt'], kwargs['schema'])
        return ProviderOutput(text=value if isinstance(value, str) else json.dumps(value, ensure_ascii=False),
                              metadata={'provider': 'fixture', 'model': 'offline-fixture', 'evidence_class': 'deterministic_replay',
                                        'usage': {'input_tokens': 2, 'output_tokens': 3}, 'reasoning_status': 'not_returned'})


class OursAdapter(DirectRunner):
    def answer(self, *, text, native_answer, event_id, requested_fact_ids=(), answered_fact_ids=()):
        state = self.ledger.snapshot(self.run_id)
        if state['status'] != 'awaiting_user':
            raise ValueError('QUESTION_BINDING_STALE')
        question = state['question']
        clarification = question['binding']['clarification']
        jsonschema.Draft202012Validator(clarification['answer_schema']).validate(native_answer)
        if 'candidate_token' in native_answer and native_answer['candidate_token'] not in {c['token'] for c in clarification['candidates']}:
            raise ValueError('CLARIFICATION_CANDIDATE_NOT_OFFERED')
        self.ledger.answer(self.run_id, question_id=question['question_id'], text=text, event_id=event_id,
                           native_answer=native_answer, requested_fact_ids=requested_fact_ids, answered_fact_ids=answered_fact_ids)

    def run(self, provider, *, reservation):
        if not isinstance(provider, NativeReplayProvider):
            raise ValueError('OFFLINE_REPLAY_ONLY')
        state = self.ledger.snapshot(self.run_id)
        if state['arm'] != 'B':
            raise ValueError('OURS_ADAPTER_REQUIRES_B')
        if state['status'] == 'ready':
            state = self.ledger.start(self.run_id)
        if state['status'] != 'running':
            return state
        if state['activities'] or any(c['state'] == 'inflight' for c in self.ledger.calls(self.run_id)):
            raise ValueError('NATIVE_RECOVERY_REQUIRED_NO_AUTOMATIC_REDISPATCH')
        provider.intent_offset = sum(c['metadata'].get('stage') == 'ifc_repair_intent' for c in self.ledger.calls(self.run_id))
        pending = state['native'].get('result', {}).get('clarification')
        if pending and not any(e['kind'] == 'answer' and e['payload']['question_id'] == pending['clarification_id'] for e in self.ledger.events(self.run_id)):
            return self.ledger.ask(self.run_id, question_id=pending['clarification_id'], text=pending['question'], binding={'clarification': pending})
        observer = ObservedReplay(provider, self.ledger, self.run_id, reservation)
        native_root = self.root / 'native' / self.run_id
        api = RepairAPI(native_root, provider=observer)
        native_id = 'repair-' + uuid.uuid5(uuid.NAMESPACE_URL, self.run_id).hex
        self.ledger.activity(self.run_id, 'native-api', begin=True)
        try:
            previous = state['native'].get('result')
            if previous is None:
                if (api.store.runs_root / native_id).exists():
                    # Uncertain crash: never restart an existing native run implicitly.
                    raise ValueError('NATIVE_RECOVERY_REQUIRED')
                result = api.start(self.workspace / 'model.ifc', (self.workspace / 'task.txt').read_text(encoding='utf-8'), run_id=native_id)
            elif previous.get('clarification'):
                q = previous['clarification']
                answers = [e['payload'] for e in self.ledger.events(self.run_id) if e['kind'] == 'answer' and e['payload']['question_id'] == q['clarification_id']]
                if len(answers) != 1:
                    raise ValueError('NATIVE_ANSWER_REQUIRED')
                result = api.continue_with_answer(native_id, answers[0]['native_answer'], clarification_id=q['clarification_id'], expected_state_version=previous['state_version'])
            else:
                result = api.read_result(native_id)
            document = result.to_dict()
            self.ledger.set_native(self.run_id, {'root': str(native_root), 'result': document})
        except Exception as error:
            self.ledger.activity(self.run_id, 'native-api', begin=False)
            return self.ledger.finish(self.run_id, 'budget_exhausted' if observer.budget_error else 'runtime_error', detail=f'{type(error).__name__}: {error}')
        self.ledger.activity(self.run_id, 'native-api', begin=False)
        state = self.ledger.snapshot(self.run_id)
        if observer.budget_error or state['active_elapsed_s'] >= state['limits']['active_seconds'] or state['usage']['token_overrun']:
            return self.ledger.finish(self.run_id, 'budget_exhausted', detail=observer.budget_error)
        if document.get('clarification'):
            q = document['clarification']
            return self.ledger.ask(self.run_id, question_id=q['clarification_id'], text=q['question'], binding={'clarification': q})
        if document['successful_artifact_publishable']:
            # Native read_result validates publication. Never scan staging directories.
            published = api.read_result(native_id)
            path = safe_path(native_root / published.run_directory / published.artifacts['successful_ifc'])
            if not path.is_relative_to(native_root.resolve()):
                raise ValueError('NATIVE_ARTIFACT_PATH_ESCAPE')
            shutil.copyfile(path, self.workspace / 'output/native-result.ifc')
            return self.submit('output/native-result.ifc')
        status = {'cancelled': 'cancelled', 'unsupported': 'unsupported'}.get(document['status'], 'no_output')
        return self.ledger.finish(self.run_id, status, detail=document.get('reason_code'))
