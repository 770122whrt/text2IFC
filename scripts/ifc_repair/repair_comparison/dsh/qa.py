"""Complete official DSH search, page-reading and final-answer validation."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import re
from pathlib import Path
import sys
import time
import uuid
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

import httpx

from .. import demo_workflow as carrier
from ..batch_operator import accounted_usage, budget_allows_next
from ..budget import fixed_budget_profile
from ..contracts import read_json, safe_path, sha256, write_json
from ..controller_owner import task_owner
from ..dsh_search import search_api_key
from ..formal_admission import file_ref
from ..ledger import Ledger
from ..isolated_dsh import NativeDSH, validate_web_access
from ..wire_gateway import WireGateway

SEARCH_QUESTION = ('As of {date}, what is the latest GPT model released by OpenAI? '
                   'Distinguish the latest model in ChatGPT from the latest API model family. '
                   'Give release dates and cite current official OpenAI pages. Perform web search rather than relying on memory.')
QA_ADMISSION = 'repair-comparison-d-qa-admission/0.1'
QA_SOURCES = ('dsh/qa.py', 'dsh_search.py', 'isolated_dsh.py', 'dsh/native_worker.py', 'dsh/web_proxy.py',
    'dsh/question-bridge.mjs', 'wire_gateway.py', 'container_relay.py', 'container_tools.py',
    'ledger.py', 'budget.py', 'contracts.py', 'controller_owner.py', 'batch_operator.py', 'demo_workflow.py')


def qa_bindings():
    return {name: sha256(Path(__file__).parent.parent/name) for name in QA_SOURCES}


def page_evidence(root, run_id):
    """Read native web_fetch results actually returned in later root requests."""
    fetches, pages = {}, {}
    for call in Ledger(Path(root)/'control.sqlite').calls(run_id):
        if call['metadata'].get('stage') != 'model':
            continue
        request = read_json(Path(root)/'wire'/run_id/(call['request_id']+'.json'))['request']
        for message in request.get('messages', []):
            content = message.get('content', [])
            for block in content if isinstance(content, list) else []:
                if block.get('type') == 'tool_use' and block.get('name') == 'web_fetch':
                    fetches[block['id']] = block.get('input', {}).get('url')
                if block.get('type') != 'tool_result' or block.get('tool_use_id') not in fetches:
                    continue
                body = block.get('content', '')
                text = body if isinstance(body, str) else '\n'.join(b.get('text', '') for b in body if isinstance(b, dict))
                match = re.match(r'Fetched (.+?) \(HTTP (\d{3})\)\n\n(.+)', text, re.DOTALL)
                code = int(match[2]) if match else None
                excerpt = match[3] if match else text
                pages[block['tool_use_id']] = {'url': fetches[block['tool_use_id']], 'status_code': code,
                    'ok': bool(match and 200 <= code < 300 and not block.get('is_error')),
                    'excerpt': excerpt[:800]}
    return list(pages.values())


def qa_outcome(root, run_id, native, *, require_pages=False):
    """Require real search blocks in a subsequent root request, then final text."""
    calls = Ledger(Path(root)/'control.sqlite').calls(run_id)
    sources, consumed, roots, searches = [], False, 0, 0
    for call in calls:
        record = read_json(Path(root)/'wire'/run_id/(call['request_id']+'.json'))
        if call['metadata']['stage'] == 'web_search':
            searches += 1
            sources.extend(search_sources(record['response'].get('body')))
        elif call['metadata']['stage'] == 'model':
            roots += 1
            request = json.dumps(record['request'], ensure_ascii=False)
            consumed |= any(s['url'] in request for s in sources)
    result = native.get('result', {})
    pages = page_evidence(root, run_id)
    answer = result.get('final_response', '')
    complete = (native.get('ok') is True and result.get('finish_reason') == 'completed'
        and bool(answer.strip()) and consumed and roots >= 2 and sources
        and not any(c['failed'] or c['state'] != 'completed' for c in calls)
        and (not require_pages or any(p['ok'] for p in pages)))
    return {'status': 'completed' if complete else 'failed', 'answer': answer,
        'finish_reason': result.get('finish_reason'), 'sources': sources,
        'search_results_consumed': consumed, 'root_requests': roots, 'search_requests': searches,
        'error': native.get('error'), 'pages': pages}


def admit_qa(native_report, local_junit, native_junit, output):
    report = read_json(safe_path(Path(native_report)))
    if (report.get('schema_version') != 'repair-comparison-d-qa-result/0.1'
            or report.get('mode') != 'offline' or report.get('status') != 'completed'
            or report.get('source_bindings') != qa_bindings()
            or not report.get('container_stopped') or report.get('usage', {}).get('unknown_calls') != 0):
        raise ValueError('NATIVE_QA_OFFLINE_EVIDENCE_REQUIRED')
    suites = [passed_suite(local_junit, 'test_dsh_qa'),
              passed_suite(native_junit, 'test_dsh_search_native_seam')]
    root = safe_path(Path(report['experiment_root']))
    native = read_json(root/'runtime/result.json')
    state = Ledger(root/'control.sqlite').snapshot('dsh-full-qa-D')
    if qa_outcome(root, 'dsh-full-qa-D', native, require_pages=report.get('web_access') == 'proxy')['status'] != 'completed' or state['activities']:
        raise ValueError('NATIVE_QA_FINAL_ANSWER_REQUIRED')
    if Path(output).exists():
        raise ValueError('SEARCH_ADMISSION_EXISTS')
    value = {'schema_version': QA_ADMISSION, 'scope': 'One complete native search Q&A; no IFC repair',
        'source_bindings': qa_bindings(), 'native_report': file_ref(native_report), 'suites': suites,
        'settings': report['settings'], 'image_id': report['image_id'], 'web_access': report.get('web_access'),
        'evidence': [file_ref(root/'runtime'/name) for name in ('result.json', 'container.json', 'versions.json')]}
    write_json(safe_path(Path(output)), value)
    return value


def verify_qa_admission(path):
    value = read_json(safe_path(Path(path)))
    if value.get('schema_version') != QA_ADMISSION or value.get('source_bindings') != qa_bindings():
        raise ValueError('CURRENT_QA_ADMISSION_REQUIRED')
    for ref in [value['native_report'], *value['suites'], *value['evidence']]:
        if ref != file_ref(ref['path']):
            raise ValueError('QA_ADMISSION_EVIDENCE_CHANGED')
    return value


def qa_budget_available(usage, next_limit, total_limit, unresolved_search_token_hold):
    """An explicit planning hold never substitutes for unknown actual usage."""
    if usage['unknown_calls'] and unresolved_search_token_hold <= 0:
        return False
    held = dict(usage)
    held['reserved_tokens'] += unresolved_search_token_hold
    return budget_allows_next(held, next_limit, total_limit)


def qa_question(web_access):
    question = SEARCH_QUESTION.format(date=datetime.now(timezone(timedelta(hours=8))).date().isoformat())
    question += (' Search the English official OpenAI announcement index '
        '(https://openai.com/research/index/release/) and English ChatGPT release notes '
        '(https://help.openai.com/en/articles/6825453-chatgpt-release-notes). ')
    if web_access == 'proxy':
        question += ('The native web_fetch tool can read public pages through a configured proxy. '
            'Read relevant official pages with web_fetch to verify publication dates and API availability; '
            'do not infer the latest release from search titles alone. If an official page refuses automated access, '
            'try the official API models (https://developers.openai.com/api/docs/models), '
            'API changelog (https://developers.openai.com/api/docs/changelog), '
            'or OpenAI news RSS (https://openai.com/news/rss.xml). Fetch at most six pages. ')
    else:
        question += ('This isolated container has no direct internet access: web_fetch and shell networking are unavailable; '
            'the native web_search auxiliary endpoint is available. Use the returned search excerpts and sources. ')
    return question + ('Use at most four search queries in total, then give a final answer in Chinese with supporting URLs. '
        'State uncertainty for any fact the sources do not establish; do not continue searching indefinitely. '
        'This is a knowledge question and requires no IFC file.')


def qa(root, *, mode, budget_root=None, admission=None, unresolved_search_token_hold=0, web_access=None):
    """Single persistent official SDK turn; waits and accounting stay in script."""
    validate_web_access(web_access)
    authority = verify_qa_admission(admission) if mode == 'live' else None
    if authority and authority.get('web_access') != web_access:
        raise ValueError('QA_WEB_ACCESS_ADMISSION_MISMATCH')
    root = safe_path(Path(root))
    if root.exists():
        raise ValueError('QA_EXISTS_NO_AUTOMATIC_RETRY')
    from ..dsh_search import search_configuration
    settings = authority['settings'] if authority else search_configuration({})
    image_id = carrier.docker('image', 'inspect', carrier.DSH_IMAGE, '--format', '{{.Id}}')
    if authority and image_id != authority['image_id']:
        raise ValueError('QA_RUNTIME_IMAGE_CHANGED')
    budget, run_id = fixed_budget_profile('S1'), 'dsh-full-qa-D'
    if type(unresolved_search_token_hold) is not int or unresolved_search_token_hold < 0:
        raise ValueError('INVALID_UNKNOWN_USAGE_HOLD')
    budget_check = None
    if mode == 'live':
        if budget_root is None:
            raise ValueError('EXISTING_BUDGET_AUTHORIZATION_REQUIRED')
        parent = safe_path(Path(budget_root))
        with task_owner(parent, 'additional-attempt-registry'):
            binding = read_json(parent/'formal-plan-binding.json')
            if sha256(Path(binding['path'])) != binding['sha256']:
                raise ValueError('BUDGET_AUTHORIZATION_CHANGED')
            limit = read_json(Path(binding['path']))['authorization']['total_api_token_limit']
            states = carrier.status(parent)
            registry = parent/'operator/additional-attempts.json'
            extra = read_json(registry) if registry.exists() else {'roots': []}
            prior_roots = [parent, *map(Path, extra['roots'])]
            all_states = [s for prior in prior_roots for s in carrier.status(prior)]
            used = accounted_usage(parent, states)
            missing = [(prior, s, c) for prior in prior_roots for s in carrier.status(prior)
                for c in Ledger(prior/'control.sqlite').calls(s['run_id']) if c['normalized_usage'] is None]
            # Retired traces keep only financial provenance, including unknown calls.
            missing.extend((Path(c['origin']), {'case_id': c['case_id'], 'status': c['run_status']}, c)
                           for c in extra.get('archived_unknown_calls', []))
            # The explicit hold is restricted to already stopped search-only
            # failures of this Q&A diagnostic, never formal/active/model calls.
            if used['unknown_calls'] and (len(missing) != used['unknown_calls'] or any(
                    s['case_id'] != 'dsh-full-qa' or s['status'] != 'no_output'
                    or c['state'] != 'failed' or c['metadata'].get('stage') != 'web_search'
                    for _, s, c in missing)):
                raise ValueError('UNKNOWN_USAGE_OUTSIDE_STOPPED_QA_SEARCH')
            if (any(s['status'] in {'running', 'awaiting_user'} for s in all_states)
                    or not qa_budget_available(used, budget['tokens'], limit, unresolved_search_token_hold)):
                raise ValueError('QA_BATCH_BUDGET_UNAVAILABLE')
            budget_check = {'prior_usage': used, 'unresolved_search_token_hold': unresolved_search_token_hold,
                'hold_is_actual_usage': False, 'total_api_token_limit': limit,
                'unresolved_calls': [{'root': str(prior), 'request_id': c['request_id']} for prior, _, c in missing]}
            root.mkdir(parents=True)
            write_json(root/'experiment.json', {'order': [run_id], 'scope': 'Native search Q&A, no IFC task'})
            Ledger(root/'control.sqlite').create(run_id, case_id='dsh-full-qa', arm='D', budget=budget,
                mode='live_development', metadata={'admission': file_ref(admission), 'budget_check': budget_check})
            extra['roots'].append(str(root))
            write_json(registry, extra)  # reserve the existing authorization before any paid request
        from dotenv import dotenv_values
        env = dotenv_values(carrier.REPO/'.env')
        key, search_key = env['DEEPSEEK_API_KEY'], search_api_key(env, settings)
    else:
        root.mkdir(parents=True)
        write_json(root/'experiment.json', {'order': [run_id], 'scope': 'Native Q&A with fake HTTP only'})
        Ledger(root/'control.sqlite').create(run_id, case_id='dsh-full-qa', arm='D', budget=budget,
            mode='real_runtime_fake_model')
        key = search_key = 'offline-unused'
    ledger = Ledger(root/'control.sqlite')
    ledger.start(run_id)
    work = root/'workspace'; work.mkdir()
    question = qa_question(web_access)
    (work/'task.txt').write_text(question, encoding='utf8')
    public_hash = sha256(work/'task.txt')
    suffix = uuid.uuid4().hex[:10]
    network, relay = 'repair-qa-'+suffix, 'repair-qa-relay-'+suffix
    name, volume = 'repair-qa-native-'+suffix, 'repair-qa-state-'+suffix
    report = {'schema_version': 'repair-comparison-d-qa-result/0.1', 'mode': mode,
        'experiment_root': str(root), 'question': question, 'source_bindings': qa_bindings(),
        'settings': settings, 'image_id': image_id, 'status': 'failed', 'web_access': web_access}
    if budget_check:
        report['budget_check'] = budget_check
    made_network = made_relay = False
    native = None
    try:
        with WireGateway(ledger, root/'wire', timeout_seconds=180) as gateway:
            token = gateway.register(run_id, model=settings['model'], api_key=key,
                endpoints={'messages': 'https://api.deepseek.com/anthropic/v1/messages'},
                evidence_class='live_provider' if mode == 'live' else 'real_runtime_fake_model',
                web_search=settings, search_api_key=search_key, quiescent=lambda packet: False)
            carrier.docker('network', 'create', '--internal', network); made_network = True
            relay_file = Path(__file__).parent.parent/'container_relay.py'
            page_proxy = Path(__file__).with_name('web_proxy.py')
            proxy_environment = ['--env=REPAIR_WEB_PROXY=1'] if web_access == 'proxy' else []
            carrier.docker('create', '--name', relay, '--pull=never', '--network=bridge', '--read-only',
                '--user=10001:10001', '--cap-drop=ALL', '--security-opt=no-new-privileges',
                '--memory=256m', '--cpus=1', '--pids-limit=32', '--env',
                f'REPAIR_CONTROLLER_PORT={gateway.server.server_port}', *proxy_environment, '--mount',
                f'type=bind,source={page_proxy},target=/opt/web_proxy.py,readonly', '--mount',
                f'type=bind,source={relay_file},target=/opt/relay.py,readonly', carrier.IMAGE, 'python', '/opt/relay.py')
            made_relay = True
            carrier.docker('network', 'connect', '--alias', 'repair-gateway', network, relay)
            carrier.docker('start', relay)
            native = NativeDSH(work, root/'runtime', name=name, state_volume=volume, network=network,
                base_url='http://repair-gateway:8000/'+token, model=settings['model'], session_id=run_id,
                web_search=settings, task_kind='knowledge_qa', web_access=web_access)
            ledger.activity(run_id, 'native-worker', begin=True)
            result = native.run(ledger=ledger, run_id=run_id)
            ledger.activity(run_id, 'native-worker', begin=False)
            deadline = time.monotonic()+10
            while any(c['state'] == 'inflight' for c in ledger.calls(run_id)):
                if time.monotonic() >= deadline:
                    raise RuntimeError('QA_GATEWAY_SETTLEMENT_PENDING')
                time.sleep(.05)
            report.update(qa_outcome(root, run_id, result, require_pages=web_access == 'proxy'))
            stopped = read_json(root/'runtime/container.json')['State']
            report['container_stopped'] = not stopped['Running'] and stopped['Pid'] == 0
            report['public_question_unchanged'] = sha256(work/'task.txt') == public_hash
            report['private_material_not_mounted'] = not any(p.name == 'private' for p in work.iterdir())
            ledger.record(run_id, 'native_qa_return', {'status': report['status'], 'finish_reason': report['finish_reason']})
            ledger.finish(run_id, 'no_output', detail='KNOWLEDGE_QA_NO_IFC_TASK' if report['status'] == 'completed' else 'KNOWLEDGE_QA_FAILED')
    except Exception as error:
        report['error'] = type(error).__name__+':'+str(error) if isinstance(error, ValueError) else type(error).__name__
    finally:
        if made_relay:
            carrier.docker('stop', '--time', '2', relay)
            carrier.docker('rm', relay)
        if made_network:
            carrier.docker('network', 'rm', network)
        if native and (root/'runtime/container.json').exists() and report.get('container_stopped'):
            carrier.docker('volume', 'rm', volume)
        report['usage'] = ledger.snapshot(run_id)['usage']
        report['active_seconds'] = ledger.snapshot(run_id)['active_elapsed_s']
        report['source_bindings_unchanged'] = report['source_bindings'] == qa_bindings()
        write_json(root/'result.json', report)
    return report


def search_sources(payload):
    """Prose or an empty result block does not establish search connectivity."""
    found = []
    for block in payload.get('content', []) if isinstance(payload, dict) else []:
        if not isinstance(block, dict) or block.get('type') != 'web_search_tool_result':
            continue
        for item in block.get('content', []) if isinstance(block.get('content'), list) else []:
            if (isinstance(item, dict) and item.get('type') == 'web_search_result'
                    and isinstance(item.get('url'), str)
                    and urlsplit(item['url']).scheme in {'https', 'http'}):
                found.append({k: item[k] for k in ('url', 'title') if k in item})
    return found


def passed_suite(path, required_class):
    cases = list(ET.parse(safe_path(Path(path))).getroot().iter('testcase'))
    if not cases or not any(required_class in c.get('classname', '') for c in cases):
        raise ValueError('SEARCH_OFFLINE_SUITE_MISSING')
    if any(any(c.find(tag) is not None for tag in ('failure', 'error', 'skipped')) for c in cases):
        raise ValueError('SEARCH_OFFLINE_SUITE_FAILED')
    return file_ref(path)








def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    admission = sub.add_parser('admit-qa')
    for name in ('native-report', 'local-junit', 'native-junit', 'output'):
        admission.add_argument('--'+name, type=Path, required=True)
    run = sub.add_parser('qa')
    run.add_argument('--root', type=Path, required=True)
    run.add_argument('--mode', choices=('offline', 'live'), required=True)
    run.add_argument('--budget-root', type=Path)
    run.add_argument('--admission', type=Path)
    run.add_argument('--web-access', choices=['proxy'])
    run.add_argument('--unresolved-search-token-hold', type=int, default=0,
        help='Planning hold for stopped QA search failures; actual usage stays unknown')
    args = parser.parse_args()
    if args.action == 'admit-qa':
        value = admit_qa(args.native_report, args.local_junit, args.native_junit, args.output)
    else:
        value = qa(args.root, mode=args.mode, budget_root=args.budget_root,
            admission=args.admission, unresolved_search_token_hold=args.unresolved_search_token_hold,
            web_access=args.web_access)
    print(json.dumps(value, ensure_ascii=False, indent=2))
    return 0 if args.action == 'admit-qa' or value['status'] == 'completed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
