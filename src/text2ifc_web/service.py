"""Framework-independent Repair service. HTTP is a thin adapter to this interface."""
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path
import json
import multiprocessing
import re
import threading
import uuid

import ifcopenshell
from jsonschema import Draft202012Validator
from text2ifc_ifc_repair.run_store import RunStore
from text2ifc_ifc_repair.run_models import TERMINAL_STAGES, RunState, RunStoreError
from .contracts import WebError
from .selection_context import build_request
from .store import Store, identity, now, write_json


def execute_command(root, task_id, api_factory, command, arguments):
    """Called in a worker process. No shell, CLI, experiment runner or stdout parser."""
    store = Store(root)
    task = store.task(task_id)
    request = store.prepared(task['prepared_id'])
    try:
        # Factory injection is Python-only; an HTTP caller cannot select a Provider.
        api = api_factory(store.root/'native')
        from .selection_guard import guard_for_request
        from .observation import ObservedProvider
        emit=lambda event:store.record_activity(task_id,event)
        selection_check=guard_for_request(request)
        def before_apply(context):
            budget=getattr(api,'integration_budget',None)
            if budget is not None:budget.assert_publishable()
            return selection_check(context)
        api.configure_integration(before_apply=before_apply,observer=emit)
        api.provider=ObservedProvider(api.provider,emit)
        if command == 'start':
            result = api.start(store.source(request['input_id']), request['effective_repair_text'], run_id=task['run_id'])
        elif command == 'answer':
            result = api.continue_with_answer(task['run_id'], arguments['answer'],
                clarification_id=arguments['clarification_id'], expected_state_version=arguments['expected_state_version'])
        else:
            raise ValueError('UNSUPPORTED_WORKER_COMMAND')
        if result.status!='clarification_required':
            try:
                from .result_summary import write_result_summary
                write_result_summary(store,task_id,result)
            except Exception:
                store.record_activity(task_id,{'stage':'summary','action':'failed','code':'RESULT_SUMMARY_UNAVAILABLE'})
        store.finish(task_id, result=result.to_dict())
        # There is deliberately no post-Evaluation regeneration here.
    except Exception as error:
        code = str(getattr(error, 'code', 'REPAIR_WORKER_ERROR'))
        if not re.fullmatch(r'[A-Z0-9_]{1,128}', code):
            code = 'REPAIR_WORKER_ERROR'
        # Persist a bounded technical diagnosis, never exception text/locals or credentials.
        try:
            import traceback
            store.record_activity(task_id,{'stage':'worker','action':'failed','code':code,
                'error_type':type(error).__name__,'errno':getattr(error,'errno',None),'winerror':getattr(error,'winerror',None),
                'frames':[{'file':Path(f.filename).name,'function':f.name,'line':f.lineno} for f in traceback.extract_tb(error.__traceback__)[-6:]]})
        except Exception:
            pass
        store.finish(task_id, error_code=code)


class RepairService:
    def __init__(self, root, *, api_factory=None, executor=None, rework_policy=None):
        if rework_policy is not None:
            raise ValueError('REWORK_NOT_SUPPORTED')
        self.rework_policy = None
        self.store = Store(root)
        self.native = RunStore(self.store.root/'native')
        self.api_factory, self.executor = api_factory, executor
        self._owns_executor = executor is None
        self._lock = threading.RLock()
        self._futures = set()
        self.store.mark_interrupted()

    @property
    def execution_enabled(self):
        return self.api_factory is not None

    def close(self):
        if self.executor is not None and self._owns_executor:
            self.executor.shutdown(wait=True, cancel_futures=False)

    def upload(self, filename, data):
        if not filename or not filename.lower().endswith('.ifc') or any(c in filename for c in '/\\\r\n\x00') or len(filename)>240:
            raise WebError('INVALID_IFC_FILENAME')
        head = data[:65536].lstrip()
        if not head.startswith(b'ISO-10303-21;'):
            raise WebError('INVALID_IFC_STEP')
        input_id = identity('input')
        directory = self.store.root/'inputs'/input_id
        directory.mkdir()
        source = directory/'source.ifc'
        source.write_bytes(data)
        try:
            model = ifcopenshell.open(str(source))
            if model.schema != 'IFC2X3':
                raise WebError('IFC_SCHEMA_UNSUPPORTED')
            metadata = {'input_id':input_id, 'source_name':filename,'size_bytes':len(data),
                        'schema':model.schema,'product_count':len(model.by_type('IfcProduct')),
                        'created_at':now(),'download_url':f'/api/ifc-inputs/{input_id}/source'}
            write_json(directory/'metadata.json', metadata)
            return metadata
        except Exception as error:
            source.unlink(missing_ok=True)
            directory.rmdir()
            if isinstance(error, WebError):
                raise
            raise WebError('IFC_SOURCE_INVALID') from None

    def prepare(self, request):
        data = build_request(self.store.source(request.input_id), request)
        data.update(prepared_request_id=identity('request'),input_id=request.input_id,created_at=now())
        write_json(self.store.root/'requests'/(data['prepared_request_id']+'.json'),data)
        return self.read_prepared(data['prepared_request_id'])

    def read_prepared(self, ident):
        return {**self.store.prepared(ident), 'execution_enabled':self.execution_enabled,
                'execution_mode':getattr(self.api_factory,'evidence_class','configured' if self.execution_enabled else 'disabled')}

    def _queue(self, task_id, command, arguments):
        if self.executor is None:
            self.executor = ProcessPoolExecutor(max_workers=1, mp_context=multiprocessing.get_context('spawn'))
        try:
            future = self.executor.submit(execute_command, str(self.store.root), task_id, self.api_factory, command, arguments)
        except Exception:
            self.store.finish(task_id,error_code='WORKER_START_FAILED')
            raise WebError('WORKER_START_FAILED',503) from None
        self._futures.add(future)
        def done(f):
            if f.cancelled() or f.exception() is not None:
                self.store.finish(task_id,error_code='WORKER_INTERRUPTED')
            with self._lock:
                self._futures.discard(f)
        future.add_done_callback(done)

    def start(self, request):
        prepared = self.store.prepared(request.prepared_request_id)
        self.store.source(prepared['input_id'])
        if not self.execution_enabled:
            raise WebError('REPAIR_EXECUTION_NOT_ENABLED',503)
        with self._lock:
            task_limit=self.api_factory.task_limit() if hasattr(self.api_factory,'task_limit') else None
            task, fresh = self.store.claim_start(request.prepared_request_id,request.client_request_id,task_limit=task_limit)
            if fresh:
                self._queue(task['task_id'],'start',{})
        return self.task(task['task_id'])

    def _native_state(self, task):
        path = self.native.runs_root/task['run_id']/'state.json'
        if not path.exists():
            return None
        try:
            if task['busy']:
                # state.json is atomically committed. Polling must not acquire native
                # publication/recovery locks while a worker owns that transaction.
                return RunState.from_dict(json.loads(path.read_text(encoding='utf-8')))
            return self.native.load(task['run_id'])
        except Exception:
            raise WebError('NATIVE_STATE_UNAVAILABLE',409) from None

    def task(self, task_id):
        task = self.store.task(task_id)
        state = self._native_state(task)
        result = None
        if state is not None and not task['busy']:
            result = self.native.read_result(task['run_id']).to_dict()
            if state.stage in TERMINAL_STAGES or (state.clarification is not None and task['status'] != 'interrupted'):
                task['status'] = result['status']
        status = task['status']
        if task['busy']:
            status = 'running' if state is not None else 'queued'
        return {'task_id':task_id,'run_id':task['run_id'],'prepared_request_id':task['prepared_id'],
                'status':status,'native_stage':state.stage.value if state else None,
                'state_version':state.state_version if state else None,'busy':bool(task['busy']),
                'error_code':task['error_code'],'clarification':result.get('clarification') if result and status=='clarification_required' else None,
                'successful_artifact_publishable':bool(result and result['successful_artifact_publishable']),
                'complete_repair_success':bool(result and result['complete_repair_success']),
                'reason_code':result.get('reason_code') if result else None,'rework_enabled':False,
                'events_url':f'/api/repair-tasks/{task_id}/events','artifacts_url':f'/api/repair-tasks/{task_id}/artifacts'}

    def answer(self, task_id, answer):
        payload = answer.model_dump(exclude={'client_answer_id'})
        self.store.task(task_id)
        with self._lock:
            if self.store.prior_answer(task_id,answer.client_answer_id,payload):
                return self.task(task_id)
            task = self.task(task_id)
            if task['busy'] or task['status'] != 'clarification_required':
                raise WebError('TASK_NOT_WAITING',409)
            question = task['clarification']
            if question is None or question['clarification_id'] != answer.clarification_id or task['state_version'] != answer.expected_state_version:
                raise WebError('CLARIFICATION_STALE',409)
            if list(Draft202012Validator(question['answer_schema']).iter_errors(answer.answer)):
                raise WebError('CLARIFICATION_ANSWER_INVALID')
            if 'candidate_token' in answer.answer and answer.answer['candidate_token'] not in {c['token'] for c in question.get('candidates',[])}:
                raise WebError('CLARIFICATION_CANDIDATE_NOT_OFFERED')
            preview = question.get('property_preview') or {}
            if 'preview_hash' in answer.answer and answer.answer['preview_hash'] != preview.get('preview_hash'):
                raise WebError('CLARIFICATION_PREVIEW_MISMATCH',409)
            if not self.execution_enabled:
                raise WebError('REPAIR_EXECUTION_NOT_ENABLED',503)
            if self.store.claim_answer(task_id,answer.client_answer_id,payload):
                self._queue(task_id,'answer',payload)
        return self.task(task_id)

    def events(self, task_id, after=-1, activity_after=-1):
        task = self.store.task(task_id)
        state = self._native_state(task)
        events = []
        if state:
            for transition in state.transitions:
                if transition.transition_id > after:
                    events.append({'event_seq':transition.transition_id,'state_version':transition.state_version,
                        'stage':transition.to_stage.value,'occurred_at':transition.created_at,
                        'reason_code':transition.reason_code,'kind':'native_committed_boundary',
                        'clarification':transition.to_dict().get('clarification'),'answer':transition.to_dict().get('answer')})
        activity=self.store.activities(task_id,activity_after)
        return {'events':events,'cursor':state.transitions[-1].transition_id if state else after,
                'activity':activity,'activity_cursor':activity[-1]['activity_seq'] if activity else activity_after,
                'granularity':'native committed boundaries and directly observed provider/application/evaluation actions'}

    def artifacts(self, task_id):
        task = self.store.task(task_id)
        state = self._native_state(task)
        if state is None:
            return []
        run_dir = self.native.runs_root/task['run_id']
        entries = {}
        def add(rel, role):
            path = run_dir/rel
            if path.is_symlink() or not path.is_file():
                return
            resolved = path.resolve()
            if not resolved.is_relative_to(run_dir.resolve()):
                return
            key = 'artifact-'+uuid.uuid5(uuid.NAMESPACE_URL,task['run_id']+'/'+rel).hex
            entries[key] = {'artifact_id':key,'name':Path(rel).name,'relative_path':rel,'role':role,'size_bytes':path.stat().st_size,
                            'download_url':f'/api/repair-tasks/{task_id}/artifacts/{key}', '_path':str(resolved)}
        def bindings(value):
            if isinstance(value,dict):
                if isinstance(value.get('path'),str) and 'schema_version' in value:
                    add(value['path'],'stage_record')
                for v in value.values(): bindings(v)
            elif isinstance(value,(list,tuple)):
                for v in value: bindings(v)
        for transition in state.transitions:
            bindings(transition.to_dict().get('stage_payload',{}))
        add('selection-check.json','selection_check')
        # Only completed native attempt directories, never an arbitrary repository scan.
        for area in ('intent','changeset'):
            base=run_dir/area
            markers=[*base.glob('**/attempt-*.json'),*base.glob('**/diagnostics.json')]
            for marker in markers[:100]:
                if marker.is_symlink() or not marker.resolve().is_relative_to(run_dir.resolve()):continue
                try:json.loads(marker.read_text(encoding='utf-8'))
                except (OSError,ValueError):continue
                add(marker.relative_to(run_dir).as_posix(),'attempt_diagnostics')
                for name in ('rendered-prompt.md','renderer-input.json','raw-response.txt','provider-metadata.json'):
                    add((marker.parent/name).relative_to(run_dir).as_posix(),'provider_record')
        for rel in ('intent/scene-overview.json','intent/scene-queries.json','intent/grounding-evidence.json',
                    'intent/repair-intent.json','intent/repair-intent-completeness.json',
                    'changeset/provider-draft.json','changeset/bound-changeset.json'):
            add(rel,'stage_record')
        if task['busy']:
            return list(entries.values())
        result = self.native.read_result(task['run_id'])
        for role,rel in result.artifacts.items():
            if role == 'successful_ifc' and not result.successful_artifact_publishable:
                continue
            add(rel,role)
        # These records are already committed in the native publication manifest.
        manifest_ref = result.artifacts.get('manifest')
        if manifest_ref:
            manifest_path = run_dir/manifest_ref
            if manifest_path.resolve().is_relative_to(run_dir.resolve()):
                manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
                for item in manifest.get('artifacts',[]):
                    if item.get('role') == 'successful_ifc' and not result.successful_artifact_publishable:
                        continue
                    add(item['path'],item.get('role','public_record'))
        return list(entries.values())

    def artifact(self, task_id, artifact_id):
        for item in self.artifacts(task_id):
            if item['artifact_id'] == artifact_id:
                return item
        raise WebError('ARTIFACT_NOT_FOUND',404)
