"""G-only tool-wire compatibility: literal LF/CR/TAB in JSON strings.

The 0.1 parser, offered tools, schema checks and raw provider records remain
unchanged. No missing parameter, quote, delimiter or tool name is invented.
"""
from __future__ import annotations

import json
import re

from . import qwen_tools as base

VERSION = 'qwen-client-tools/0.2'
_BASE_DECODE = base.decode_tools
_CONTROLS = {'\n': '\\n', '\r': '\\r', '\t': '\\t'}


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('QWEN_TOOL_DUPLICATE_JSON_KEY')
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError('QWEN_TOOL_NONFINITE_JSON_VALUE')


def _json_wire(value):
    quoted = escaped = False
    result = []
    for character in value:
        if ord(character) < 32 and character not in _CONTROLS:
            raise ValueError('QWEN_TOOL_UNSUPPORTED_CONTROL_CHARACTER')
        if escaped:
            result.append(character)
            escaped = False
        elif quoted and character == '\\':
            result.append(character)
            escaped = True
        elif character == '"':
            quoted = not quoted
            result.append(character)
        elif quoted and character in _CONTROLS:
            result.append(_CONTROLS[character])
        else:
            result.append(character)
    normalized = ''.join(result)
    json.loads(normalized, object_pairs_hook=_unique_object, parse_constant=_reject_constant)
    return normalized


def decode_tools(content, tools):
    if not isinstance(content, str):
        return _BASE_DECODE(content, tools)
    offered = {t['function']['name']: t['function']['parameters'] for t in tools}
    def block(match):
        value = match.group(1)
        if value.lstrip().startswith('{'):
            value = _json_wire(value)
        else:
            function = re.fullmatch(r'\s*<function=([A-Za-z_][\w]*)>\s*(.*?)\s*</function>\s*', value, re.S)
            if function and function.group(1) in offered:
                properties = offered[function.group(1)].get('properties', {})
                def parameter(item):
                    key, raw = item.groups()
                    if key in properties and properties[key].get('type') != 'string':
                        raw = _json_wire(raw.strip())
                    return '<parameter='+key+'>'+raw+'</parameter>'
                value = re.sub(r'<parameter=([A-Za-z_][\w]*)>(.*?)</parameter>', parameter, value, flags=re.S)
        return '<tool_call>'+value+'</tool_call>'
    normalized = re.sub(r'<tool_call>(.*?)</tool_call>', block, content, flags=re.S)
    return _BASE_DECODE(normalized, tools)


def install():
    """Override the decoder only in the explicitly opted-in G CLI process."""
    base.decode_tools = decode_tools
    base.VERSION = VERSION
