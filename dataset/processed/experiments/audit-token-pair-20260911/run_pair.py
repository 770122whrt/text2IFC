"""One frozen Audit input, two formats, two new real responses at most."""
import argparse
from dataclasses import replace
import datetime as dt
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import sys
from urllib.parse import urlparse

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
sys.path[:0] = [str(ROOT), str(ROOT/'src')]
from text2ifc_agent.audit_context import render_audit_context
from text2ifc_agent.generation_budget import GenerationBudget, BudgetLimits, BudgetedProvider
from text2ifc_agent.live_pipeline import _validate_live_audit_output
from text2ifc_agent.live_trace import write_live_trace, write_provider_failure_trace
from text2ifc_agent.providers import validate_provider_output


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def execute(output, protocol, provider_factory, *, evidence_class):
    source = ROOT/protocol['input_path']
    if sha(source) != protocol['input_sha256']:
        raise ValueError('Frozen Audit input changed')
    if sorted(protocol['order']) != ['deduplicated', 'full']:
        raise ValueError('Exactly two distinct formats are required')
    inputs = read(source)
    output = Path(output)
    output.mkdir(exist_ok=False)
    budget = GenerationBudget(output, BudgetLimits(**protocol['limits']))
    record = {'status': 'running', 'evidence_class': evidence_class, 'started_at': dt.datetime.now(dt.timezone.utc).isoformat(),
              'budget_before': budget.snapshot(), 'arms': []}
    write(output/'execution.json', record)
    for mode in protocol['order']:
        arm = output/mode
        arm.mkdir()
        rendered, context = render_audit_context(inputs=inputs, review_enabled=True, mode=mode)
        if sha(source) != protocol['input_sha256']:
            raise ValueError('Frozen Audit input changed before transport')
        if 'prompt_sha256' in protocol and context['selected']['prompt_sha256'] != protocol['prompt_sha256'][mode]:
            raise ValueError('Frozen rendered prompt changed')
        (arm/'prompt-rendered.md').write_text(rendered['text'], encoding='utf-8')
        write(arm/'prompt-wire-input.json', rendered['inputs'])
        write(arm/'audit-context.json', context)
        remaining = protocol['limits']['max_active_seconds']-budget.snapshot()['active_seconds']
        row = {'mode': mode, 'valid': False, 'usage': None, 'status': 'running'}
        result = None
        try:
            if remaining <= 0:
                raise ValueError('No remaining activity budget')
            provider = BudgetedProvider(provider_factory(remaining), budget, max_output_tokens=protocol['max_output_tokens'])
            result = provider.generate_live(session_id=f'audit-token-pair-20260911-{mode}', prompt=rendered['text'],
                                            schema={'schema_version': 'text2ifc/audit/3.0'}, state={'stage': 'audit'})
            write_live_trace(result=result, output_dir=arm, trace_level='debug')
            validate_provider_output(result.output)
            status, payload, diagnostics = result.output.parse_json()
            issues = _validate_live_audit_output(payload, case_dir=ROOT/protocol['case_dir'],
                       deterministic_gates=inputs['DETERMINISTIC_GATES'], review_context=inputs['DESIGN_REVIEW_CONTEXT']) if status == 'ok' and payload else diagnostics
            valid = status == 'ok' and payload is not None and not diagnostics and not issues
            write(arm/'audit-report.json', payload)
            write(arm/'validation.json', {'valid': valid, 'issues': issues, 'diagnostics': diagnostics})
            row.update(status='completed' if valid else 'invalid', valid=valid,
                       response_id=result.response.get('id'), usage=result.response.get('usage'),
                       recommendation=payload.get('recommendation') if payload else None,
                       design_review=payload.get('design_review') if payload else None)
        except Exception as error:
            if result is not None:
                error.live_result = result
            failure = write_provider_failure_trace(error=error, output_dir=arm, stage='audit')
            row.update(status='failed', exception_type=type(error).__name__, failure_class=failure['failure_class'],
                       usage=failure['details'].get('usage'))
        row['budget_after'] = budget.snapshot()
        record['arms'].append(row)
        write(arm/'execution.json', row)
        write(output/'execution.json', record)
        if not row['valid']:
            break
    record.update(status='completed' if len(record['arms']) == 2 and all(r['valid'] for r in record['arms']) else 'stopped',
                  budget_after=budget.snapshot(), finished_at=dt.datetime.now(dt.timezone.utc).isoformat(),
                  source_unchanged=sha(source) == protocol['input_sha256'])
    write(output/'execution.json', record)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true')
    args = parser.parse_args()
    admission = read(OUT/'admission.json')
    assert admission['status'] == 'admitted'
    for path, digest in admission['files_sha256'].items():
        assert sha(ROOT/path) == digest, path
    for package, version in admission['dependencies'].items():
        assert importlib.metadata.version(package) == version, package
    if not args.live:
        print('Admission valid; no credentials read or transport attempted.')
        return
    protocol = read(OUT/'protocol.json')
    authorization = read(OUT/'authorization.json')
    assert authorization['status'] == 'approved'
    assert authorization['protocol_sha256'] == sha(OUT/'protocol.json')
    from scripts.agent.run_phase6_2_cli import load_env_file
    from text2ifc_agent.openai_compat import load_openai_compatible_runtime_config, OpenAICompatibleLiveProvider
    load_env_file(ROOT/'.env')
    config = load_openai_compatible_runtime_config(dict(os.environ))
    assert config.model == protocol['model'] and urlparse(config.base_url).hostname == 'api.deepseek.com'
    config = replace(config, max_completion_tokens=protocol['max_output_tokens'], max_input_tokens=protocol['max_input_tokens'])
    result = execute(OUT/'live', protocol,
        lambda remaining: OpenAICompatibleLiveProvider(config=replace(config, timeout_seconds=min(remaining, 600)), connection_max_attempts=1),
        evidence_class='live')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
