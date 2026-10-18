"""Public-input projections for an explicitly configured short Qwen window.

No learned summarizer or private benchmark input. A local tokenizer asset is
preferred; estimates are never reported as actual API usage.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import re


class ContextLimitError(ValueError):
    pass


@dataclass(frozen=True)
class ContextPolicy:
    context_tokens: int = 50000
    output_tokens: int = 8192
    overhead_tokens: int = 2048
    recent_pairs: int = 3
    recent_scene_queries: int = 2
    tokenizer_path: str | None = None

    def __post_init__(self):
        for name in ('context_tokens', 'output_tokens', 'overhead_tokens', 'recent_pairs', 'recent_scene_queries'):
            if type(getattr(self, name)) is not int or getattr(self, name) <= 0:
                raise ValueError('INVALID_CONTEXT_POLICY')
        if self.context_tokens <= self.output_tokens + self.overhead_tokens + 1024:
            raise ValueError('CONTEXT_HEADROOM_REQUIRED')
        if self.tokenizer_path is not None and (not isinstance(self.tokenizer_path, str) or not Path(self.tokenizer_path).is_file()):
            raise ValueError('LOCAL_TOKENIZER_REQUIRED')


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode('utf8')


_TOKENIZERS = {}


def estimate_input(value, policy):
    text = encoded(value).decode('utf8')
    if policy.tokenizer_path:
        from tokenizers import Tokenizer
        path = str(Path(policy.tokenizer_path).resolve())
        if path not in _TOKENIZERS:
            _TOKENIZERS[path] = Tokenizer.from_file(path)
        return len(_TOKENIZERS[path].encode(text, add_special_tokens=False).ids), 'local_qwen_tokenizer_json'
    # Offline fallback only: split punctuation/digits explicitly and give word
    # pieces and non-ASCII UTF-8 generous weight, plus 25% estimation margin.
    pieces = re.findall(r'[A-Za-z_]+|\d{1,3}|\s+|[^\x00-\x7f]|[^\w\s]', text)
    count = sum(math.ceil(len(p)/3) if p[0].isascii() and (p[0].isalpha() or p[0] == '_')
                else len(p.encode('utf8')) if not p[0].isascii() else 1 for p in pieces)
    return math.ceil(count*1.25), 'lexical_estimate_25pct_margin'


def _archive(workspace, text):
    if workspace is None:
        raise ContextLimitError('PUBLIC_ARCHIVE_WORKSPACE_REQUIRED')
    work = Path(workspace).resolve(strict=True)
    folder = work/'.qwen-context'
    if folder.is_symlink() or folder.resolve().parent != work:
        raise ValueError('CONTEXT_ARCHIVE_OUTSIDE_WORKSPACE')
    folder.mkdir(exist_ok=True)
    raw = text.encode('utf8')
    name = hashlib.sha256(raw).hexdigest()+'.txt'
    path = folder/name
    if path.is_symlink():
        raise ValueError('CONTEXT_ARCHIVE_SYMLINK')
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError('CONTEXT_ARCHIVE_CHANGED')
    else:
        path.write_bytes(raw)
    return '.qwen-context/'+name


def _blocks(messages):
    """Only completed call/result cohorts may be evicted together."""
    blocks = []
    for i, message in enumerate(messages):
        calls = message.get('tool_calls', []) if message.get('role') == 'assistant' else []
        if not calls:
            continue
        ids = {c.get('id') for c in calls}
        end = i+1
        returned = set()
        while end < len(messages) and messages[end].get('role') == 'tool':
            returned.add(messages[end].get('tool_call_id'))
            end += 1
        if None not in ids and returned == ids:
            blocks.append((i, end))
    return blocks


def _tool_view(content, workspace, *, preview_bytes):
    text = content if isinstance(content, str) else encoded(content).decode('utf8')
    ref = _archive(workspace, text)
    view = {'archived_public_tool_result': ref, 'bytes': len(text.encode('utf8')),
            'read_file': {'path': ref, 'offset': 0, 'limit': 4096},
            'preview': text.encode('utf8')[:preview_bytes].decode('utf8', errors='ignore')}
    try:
        value = json.loads(text)
        if isinstance(value, dict):
            for key in ('ok', 'status', 'exit_code', 'error', 'error_code', 'reason'):
                if key in value:
                    view[key] = value[key] if not isinstance(value[key], str) else value[key][:512]
    except ValueError:
        pass
    return encoded(view).decode('utf8')


def _generic(body, policy, target, workspace):
    messages = body['messages']
    cohorts = _blocks(messages)
    stats = {'archived_results': 0, 'collapsed_pairs': 0}
    recent = {i for a, b in cohorts[-policy.recent_pairs:] for i in range(a, b)}
    # Old results first. Very large recent results also need a file reference;
    # small recent numerical/error evidence is left verbatim.
    indices = [i for a, b in cohorts for i in range(a+1, b)]
    indices.sort(key=lambda i: (i in recent, i))
    for i in indices:
        if estimate_input(body, policy)[0] <= target:
            break
        content = messages[i].get('content', '')
        size = len(encoded(content))
        if size < 2048:
            continue
        messages[i]['content'] = _tool_view(content, workspace, preview_bytes=768 if i in recent else 128)
        stats['archived_results'] += 1
    # Never separate an assistant tool call from its results. Keep the newest
    # cohorts plus all system/user/pending messages; archive old complete blocks.
    remove, summaries = set(), []
    for a, b in cohorts[:-policy.recent_pairs]:
        if estimate_input(body, policy)[0] <= target:
            break
        block = messages[a:b]
        ref = _archive(workspace, encoded(block).decode('utf8'))
        names = [c['function']['name'] for c in block[0]['tool_calls']]
        summaries.append({'tools': names, 'completed': True, 'public_record': ref})
        remove.update(range(a, b))
        # Keep the program summary at the original position, not after the
        # latest user clarification or pending tool call.
        first = min(remove)
        body['messages'] = [
            *messages[:first],
            {'role': 'assistant', 'content': 'Earlier completed tool exchanges (public records can be read with read_file): '+encoded(summaries).decode('utf8')},
            *[m for i, m in enumerate(messages) if i >= first and i not in remove]]
        stats['collapsed_pairs'] += 1
    return stats


def _strings(value):
    if isinstance(value, str):
        return {value}
    if isinstance(value, dict):
        return set().union(*(_strings(v) for v in value.values())) if value else set()
    if isinstance(value, list):
        return set().union(*(_strings(v) for v in value)) if value else set()
    return set()


def _scene(body, policy):
    stats = {'omitted_query_cohorts': 0}
    for message in body['messages']:
        if message.get('role') != 'user' or not isinstance(message.get('content'), str):
            continue
        parts = re.split(r'(^## [^\n]+\n)', message['content'], flags=re.MULTILINE)
        sections = {}
        for i in range(1, len(parts)-1, 2):
            if parts[i].strip() == '## Public request':
                continue
            try:
                sections[parts[i].strip()] = (i+1, json.loads(parts[i+1]))
            except ValueError:
                continue
        key = '## Read-only query results so far'
        if key in sections:
            at, scene = sections[key]
            if isinstance(scene, dict) and isinstance(scene.get('queries'), list):
                citations = set()
                for title in ('## Validation feedback', '## Previous failed proposal (bounded data)'):
                    if title in sections:
                        citations |= _strings(sections[title][1])
                queries = scene['queries']
                # Some bounded error/proposal envelopes contain identifiers in
                # an excerpt string rather than a parsed field. Retain those
                # cohorts too; extra retention is safer than losing authority.
                cited_text = ' '.join(citations)
                for query in queries:
                    for identifier in [query.get('query_id'), *query.get('query_ids', []), *query.get('record_ids', [])]:
                        if isinstance(identifier, str) and re.search(r'(?<![\w.-])'+re.escape(identifier)+r'(?![\w.-])', cited_text):
                            citations.add(identifier)
                selected = []
                for i, query in enumerate(queries):
                    identifiers = set(query.get('query_ids', [])) | {query.get('query_id')}
                    records = set(query.get('record_ids', []))
                    if i >= len(queries)-policy.recent_scene_queries or (identifiers | records) & citations:
                        selected.append(query)
                ids = citations | {r for q in selected for r in q.get('record_ids', [])}
                scene['queries'] = selected
                scene['records'] = [r for r in scene.get('records', []) if r.get('id') in ids]
                # Types and complete query denominators are unchanged. Native
                # verification keeps the entire raw authority, outside this view.
                stats['omitted_query_cohorts'] += len(queries)-len(selected)
                if len(queries) != len(selected):
                    scene['context_projection'] = {'older_query_cohorts_omitted': len(queries)-len(selected),
                        'recover_via': 'existing read-only scene queries; omitted facts are not inferred'}
        for _, (at, value) in sections.items():
            parts[at] = encoded(value).decode('utf8')+'\n\n'
        message['content'] = ''.join(parts)
    return stats


def compact_request(body, *, arm, policy, workspace=None):
    if arm not in {'F', 'G'}:
        raise ValueError('QWEN_ARMS_ONLY')
    result = deepcopy(body)
    cap = result.get('max_tokens', result.get('max_completion_tokens', policy.output_tokens))
    if type(cap) is not int or not 0 < cap <= policy.output_tokens:
        raise ValueError('QWEN_OUTPUT_HEADROOM_EXCEEDED')
    budget = policy.context_tokens-cap-policy.overhead_tokens
    before, estimator = estimate_input(result, policy)
    stats = {'estimator': estimator, 'before_estimate': before, 'mode': 'unchanged'}
    if before > int(budget*.85):
        if arm == 'G':
            stats.update(_generic(result, policy, int(budget*.65), workspace))
            stats['mode'] = 'tool_archive'
        else:
            stats.update(_scene(result, policy))
            stats['mode'] = 'scene_projection'
    after, _ = estimate_input(result, policy)
    stats.update(after_estimate=after, input_limit=budget)
    if after > budget:
        raise ContextLimitError('PROTECTED_CONTEXT_EXCEEDS_WINDOW_AFTER_COMPACTION')
    return result, stats
