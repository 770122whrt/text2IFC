"""Restore a redundant model echo only for repeated empty-line differences.

The conversation remains authoritative. No parameter, nonempty line, indentation,
single line break, or paragraph boundary is normalized. Fenced inputs remain
strict because blank lines may be part of literal content.
"""
import copy
import hashlib
import json
import re
from pathlib import Path


SAVED_REQUEST_REFERENCE = '__TEXT2IFC_SAVED_REQUEST_V1__'
REFERENCE_TEMPLATES = {'design-brief.v2.32', 'design-brief.v2.33'}


def normalize_request_echo(brief, original_request, *, template_id=''):
    result = copy.deepcopy(brief)
    if not isinstance(result, dict) or result.get('schema_version') != 'text2ifc/design-brief/2.9':
        return result, False
    echoed = result.get('original_request')
    if not isinstance(echoed, str) or not isinstance(original_request, str) or not original_request:
        return result, False
    if echoed == original_request:
        return result, False
    if template_id in REFERENCE_TEMPLATES and echoed == SAVED_REQUEST_REFERENCE:
        result['original_request'] = original_request
        return result, True
    if any(marker in text for marker in ('```', '~~~') for text in (original_request, echoed)):
        return result, False
    # Two newlines still mark a paragraph boundary. Never collapse to one, strip
    # whitespace, or touch a nonempty line (including a whitespace-only line).
    canonical = lambda text: re.sub(r'\n{3,}', '\n\n', text)
    if canonical(echoed) != canonical(original_request):
        return result, False
    result['original_request'] = original_request
    return result, True


def normalize_request_echo_with_trace(brief, original_request, root, *, template_id=''):
    normalized, changed = normalize_request_echo(brief, original_request, template_id=template_id)
    if changed:
        digest = lambda text: hashlib.sha256(text.encode('utf-8')).hexdigest()
        reference = brief['original_request'] == SAVED_REQUEST_REFERENCE and template_id in REFERENCE_TEMPLATES
        record = {
            'schema_version': 'text2ifc/brief-request-echo-normalization/1.1' if reference else 'text2ifc/brief-request-echo-normalization/1.0',
            'changed_paths': ['/original_request'],
            'reason': 'Resolve versioned saved-request reference from the conversation' if reference else 'Repeated empty-line count only; restore exact saved conversation input',
            'echo_sha256': digest(brief['original_request']),
            'original_request_sha256': digest(original_request),
            'known_facts_changed': False,
            'extra_provider_calls': 0,
        }
        for name, value in [('request-echo-input.json', brief), ('request-echo-normalization.json', record)]:
            with (Path(root)/name).open('x', encoding='utf-8') as stream:
                stream.write(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
    return normalized
