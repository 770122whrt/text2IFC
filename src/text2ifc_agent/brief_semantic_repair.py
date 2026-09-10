"""One bounded Agent repair of Brief extraction; no candidate-derived authority."""
from __future__ import annotations

import copy
import json
from dataclasses import asdict
from pathlib import Path

from .design_brief import load_design_brief_schema, validate_design_brief
from .live_trace import write_live_trace, write_provider_failure_trace
from .prompt_registry import render_prompt


FIELDS = ('semantic_requirements', 'semantic_review')


def _write(root, name, value):
    (root / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def _fixed_part(brief):
    fixed = copy.deepcopy(brief)
    for name in FIELDS:
        fixed.get('known_facts', {}).pop(name, None)
    return fixed


def semantic_repair_eligible(brief, issues):
    """Only schema/projection defects wholly inside the two semantic fields."""
    if not isinstance(brief, dict) or brief.get('schema_version') not in {'text2ifc/design-brief/2.2', 'text2ifc/design-brief/2.3'} or brief.get('status') != 'ready':
        return False
    if not issues:
        return False
    # A reference with valid empty declarations distinguishes extraction omissions
    # from geometry/schema defects. This copy is only a validator probe, not output.
    probe = copy.deepcopy(brief)
    known = probe.get('known_facts')
    if not isinstance(known, dict):
        return False
    known['semantic_requirements'] = []
    known['semantic_review'] = {kind: {'status': 'not_specified', 'source_turns': ['probe']}
        for kind in ('material', 'property', 'type', 'appearance', 'template')}
    # Do not validate evidence IDs without the caller's catalog in this eligibility
    # probe; use schema-only validity plus the actual issue locations instead.
    from jsonschema import Draft202012Validator
    if list(Draft202012Validator(load_design_brief_schema(brief['schema_version'])).iter_errors(probe)):
        return False
    for issue in issues:
        row = asdict(issue) if hasattr(issue, '__dataclass_fields__') else issue
        path = row['path']
        if path in {'/known_facts', '/known_facts/semantic_requirements', '/known_facts/semantic_review'}:
            continue
        if not any(path.startswith('/known_facts/' + field + '/') for field in FIELDS):
            return False
    return True


def repair_semantic_brief(*, provider, output_dir, brief, case, evidence_catalog, session_id):
    """Caller owns the shared budget. Every attempt is retained, success is atomic."""
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=False)
    version = brief.get('schema_version')
    schema = load_design_brief_schema(version)
    issues = validate_design_brief(brief, evidence_catalog=evidence_catalog,
        expected_schema_version=version, conversation=case['conversation'])
    if not semantic_repair_eligible(brief, issues):
        report = {'valid': False, 'issues': [asdict(i) for i in issues], 'status': 'not_eligible'}
        _write(root, 'validation.json', report)
        return report
    inputs = {'USER_REQUEST': case['user_request'], 'CONVERSATION': case['conversation'],
        'PREVIOUS_BRIEF': brief, 'VALIDATION_ISSUES': [asdict(i) for i in issues], 'DESIGN_BRIEF_SCHEMA': schema}
    if version == 'text2ifc/design-brief/2.3':
        from .semantic_requirements import element_appearance_schema
        inputs['ELEMENT_APPEARANCE_SCHEMA'] = element_appearance_schema()
    rendered = render_prompt(template_id='design-brief-semantic-repair.v1.1' if version == 'text2ifc/design-brief/2.3'
                             else 'design-brief-semantic-repair.v1.0', inputs=inputs)
    _write(root, 'prompt-render-input.json', inputs)
    _write(root, 'prompt-identity.json', rendered['metadata'])
    (root/'prompt-rendered.md').write_text(rendered['text'], encoding='utf-8')
    try:
        result = provider.generate_live(session_id=session_id, prompt=rendered['text'], schema=schema,
            state={'case_id': case.get('case_id', session_id), 'stage': 'design-brief-semantic-repair'})
    except Exception as error:
        write_provider_failure_trace(error=error, output_dir=root, stage='design-brief-semantic-repair')
        raise
    write_live_trace(result=result, output_dir=root, trace_level='debug')
    status, parsed, diagnostics = result.output.parse_json()
    errors = list(diagnostics)
    if status == 'ok' and parsed is not None and not errors:
        errors = [asdict(i) for i in validate_design_brief(parsed, evidence_catalog=evidence_catalog,
            expected_schema_version=version, conversation=case['conversation'])]
        if not errors and _fixed_part(parsed) != _fixed_part(brief):
            errors.append({'code': 'BRIEF_SEMANTIC_REPAIR_SCOPE_VIOLATION', 'path': '/',
                           'message': 'Brief 校正改变了冻结语义字段以外的内容。'})
        if not errors:
            from .semantic_requirements import project_semantic_requirements
            before = project_semantic_requirements(brief)['expectations']
            after = project_semantic_requirements(parsed)['expectations']
            def value_key(row):
                return {key: value for key, value in row.items() if key != 'source_path'}
            if any(value_key(row) not in [value_key(item) for item in after] for row in before):
                errors.append({'code': 'BRIEF_SEMANTIC_REPAIR_VALUE_LOSS', 'path': '/known_facts/semantic_requirements',
                               'message': '校正不得删除或覆盖初始 Brief 已结构化保留的要求。'})
    elif not errors:
        errors = [{'code': 'BRIEF_SEMANTIC_REPAIR_INVALID_JSON', 'path': '/', 'message': 'Incomplete JSON output.'}]
    report = {'valid': not errors, 'issues': errors, 'status': 'corrected' if not errors else 'blocked',
        'response_id': result.response.get('id'), 'evidence_class': result.evidence_class}
    _write(root, 'validation.json', report)
    if parsed is not None:
        _write(root, 'parsed-output.json', parsed)
    if not errors:
        _write(root, 'design-brief.json', parsed)
        report['brief'] = parsed
    return report
