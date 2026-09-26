"""Persist human review before exporting a partially supported IFC description.

The private extraction stays here. Only approved, rendered text may cross the
existing text2IFC public bridge. Decisions never edit the original IFC or facts.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from .compact import cell
from .compact_pipeline import render_prepared_description
from .observation import all_items


def _sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    allow_nan=False).encode('utf-8')).hexdigest()


def _verify_source(facts):
    source = facts['source']
    actual = hashlib.sha256(Path(source['path']).read_bytes()).hexdigest()
    if actual != source['sha256'].removeprefix('sha256:'):
        raise ValueError('REVIEW_SOURCE_CHANGED')


def _inventory(facts):
    unsupported, blockers = [], []
    labels = [item['label'] for _, item in all_items(facts)]
    if len(labels) != len(set(labels)):
        raise ValueError('AMBIGUOUS_PUBLIC_LABEL')
    for category, item in all_items(facts):
        if category in {'doors', 'windows'}:
            detail = item.get('component_detail', {})
            if detail.get('status') == 'unsupported' and detail.get('unsupported'):
                reasons = list(dict.fromkeys(
                    issue['ifc_class'] + ': ' + issue['reason']
                    for issue in detail['unsupported']))
                unsupported.append({'label': item['label'], 'ifc_class': item['ifc_class'],
                    'name': item.get('name'), 'opening': item.get('opening'),
                    'host_wall': item.get('host_wall'), 'reasons': reasons})
            elif detail.get('status') != 'supported':
                blockers.append({'label': item['label'], 'reason': '门窗缺少完整部件解析结果'})
        elif category in {'walls', 'openings'}:
            key, required = ('solid_detail', 'supported_vertical_extrusion') if category == 'walls' else ('opening_solid_detail', 'supported_vertical_prism')
            if item.get(key, {}).get('status') != required:
                blockers.append({'label': item['label'], 'reason': '墙或开口尚不能按当前参数方式完整描述'})
    if facts.get('unrepresented_classes'):
        blockers.append({'label': '未描述类别', 'reason': json.dumps(facts['unrepresented_classes'], ensure_ascii=False)})
    return unsupported, blockers


def _question(unsupported, blockers):
    lines = ['以下内容需要确认后才能继续：']
    for item in unsupported:
        lines.append(f"- {cell(item['label'])} {cell(item['name'])}：" + '；'.join(item['reasons']) +
                     f"。若排除，将不生成整个门窗，保留宿主墙 {cell(item['host_wall'])} 和开口 {cell(item['opening'])}，输出标明部分重建。")
    for item in blockers:
        lines.append(f"- {cell(item['label'])}：{cell(item['reason'])}。这项不能由门窗排除决定代替。")
    lines.append('请选择暂停，或逐项确认排除列出的门窗后继续；未确认项不自动简化。')
    return '\n'.join(lines)


def start_review(*, store, facts):
    """Freeze source facts and return a human-readable question; no model call."""
    if facts.get('description_policy', {}).get('version') != '1.1':
        raise ValueError('COMPONENT_REVIEW_REQUIRES_DESCRIPTION_1_1')
    _verify_source(facts)
    unsupported, blockers = _inventory(facts)
    question = _question(unsupported, blockers)
    session = store.create_session(original_input=question)
    path = session.run_dir / 'component-review-facts.private.json'
    path.write_text(json.dumps(facts, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    review = {'schema_version': 'text2ifc/component-review/1.0',
              'facts_sha256': _sha(facts), 'unsupported': unsupported,
              'other_blockers': blockers, 'question': question}
    review['review_sha256'] = _sha(review)
    store.append_event(session.session_id, event_type='component_review_created', payload=review)
    store.record_artifact(session.session_id, kind='component-review-private-facts', path=path)
    return review_state(store=store, session_id=session.session_id)


def _load(store, session_id):
    session = store.get_session(session_id)
    events = store.list_events(session_id)
    created = [e.payload for e in events if e.event_type == 'component_review_created']
    if len(created) != 1:
        raise ValueError('COMPONENT_REVIEW_REQUIRED')
    review = created[0]
    facts = json.loads((session.run_dir / 'component-review-facts.private.json').read_text(encoding='utf-8'))
    if _sha(facts) != review['facts_sha256']:
        raise ValueError('REVIEW_FACTS_CHANGED')
    if _sha({k: v for k, v in review.items() if k != 'review_sha256'}) != review['review_sha256']:
        raise ValueError('REVIEW_RECORD_CHANGED')
    _verify_source(facts)
    decisions = [e.payload for e in events if e.event_type == 'component_review_decided']
    return review, facts, decisions


def review_state(*, store, session_id):
    review, _, decisions = _load(store, session_id)
    status = 'awaiting_human' if review['unsupported'] or review['other_blockers'] else 'ready'
    if decisions:
        status = 'paused' if decisions[-1]['action'] == 'pause' else 'approved_partial'
    return {**review, 'session_id': session_id, 'status': status,
            'decision': decisions[-1] if decisions else None}


def decide_review(*, store, session_id, review_sha256, action, excluded_labels):
    review, _, decisions = _load(store, session_id)
    if review_sha256 != review['review_sha256']:
        raise ValueError('STALE_REVIEW')
    if action not in {'pause', 'exclude_and_continue'}:
        raise ValueError('EXPLICIT_ACTION_REQUIRED')
    if action == 'pause' and excluded_labels:
        raise ValueError('PAUSE_CANNOT_EXCLUDE')
    if action == 'exclude_and_continue':
        if review['other_blockers']:
            raise ValueError('ADDITIONAL_UNSUPPORTED_CONTENT')
        wanted = sorted(item['label'] for item in review['unsupported'])
        if not wanted or sorted(excluded_labels) != wanted:
            raise ValueError('EXACT_UNSUPPORTED_SET_REQUIRED')
    decision = {'review_sha256': review_sha256, 'action': action,
                'excluded_labels': sorted(excluded_labels)}
    if decisions and decisions[-1] == decision:
        return review_state(store=store, session_id=session_id)
    if decisions and decisions[-1]['action'] == 'exclude_and_continue':
        raise ValueError('REVIEW_ALREADY_APPROVED')
    # One committed event is the authoritative decision, including after restart.
    store.append_event(session_id, event_type='component_review_decided', payload=decision)
    return review_state(store=store, session_id=session_id)


def approved_description(*, store, session_id):
    state = review_state(store=store, session_id=session_id)
    if state['status'] not in {'ready', 'approved_partial'}:
        raise ValueError('HUMAN_DECISION_REQUIRED')
    _, original, _ = _load(store, session_id)
    facts = copy.deepcopy(original)
    excluded = set((state['decision'] or {}).get('excluded_labels', []))
    excluded_guids = {i['source_global_id'] for _, i in all_items(facts) if i['label'] in excluded}
    for floor in [*facts['storeys'], facts.get('unassigned', {})]:
        for category in ('doors', 'windows'):
            floor[category] = [i for i in floor.get(category, []) if i['label'] not in excluded]
        for opening in floor.get('openings', []):
            if opening.get('filling') in excluded or opening.get('filling_global_id') in excluded_guids:
                opening.update(filling=None, filling_global_id=None)
    for category, count_key in [('doors', 'door_count'), ('windows', 'window_count')]:
        facts['capability'][count_key] = sum(c == category for c, _ in all_items(facts))
    text = render_prepared_description(facts)
    if excluded:
        text = ('## 本轮已确认的重建范围\n\n本轮为部分重建。已明确排除 ' +
                '、'.join(sorted(excluded)) + '；不生成这些门窗，不使用普通模板替代，保留对应墙体和开口。'
                '下文仅列出本轮需要生成的构件，编号沿用原说明。\n\n' + text)
    return {'status': state['status'], 'review_sha256': state['review_sha256'],
            'excluded_labels': sorted(excluded), 'refusals': state['unsupported'],
            'facts': facts, 'description': text, 'description_sha256': hashlib.sha256(text.encode('utf-8')).hexdigest()}


def reconstruct_reviewed_description(*, store, session_id, invoke_design_brief,
                                    provider_factory, **options):
    """Pending or paused reviews never reach a Provider; dispatch is not retried.

    Existing generation sessions own recovery after an interrupted dispatch.
    """
    state = review_state(store=store, session_id=session_id)
    if state['status'] not in {'ready', 'approved_partial'}:
        return {'status': state['status'], 'review_session_id': session_id,
                'question': state['question'], 'ifc_path': None}
    events = store.list_events(session_id)
    completed = [e.payload for e in events if e.event_type == 'component_generation_completed']
    if completed:
        return completed[-1]
    if any(e.event_type == 'component_generation_started' for e in events):
        raise ValueError('REVIEW_GENERATION_RECOVERY_REQUIRED')
    packet = approved_description(store=store, session_id=session_id)
    store.append_event(session_id, event_type='component_generation_started', payload={
        'review_sha256': packet['review_sha256'], 'description_sha256': packet['description_sha256']})
    from .text2ifc_public import reconstruct_description_with_public_text2ifc
    result = reconstruct_description_with_public_text2ifc(packet['description'], store=store,
        invoke_design_brief=invoke_design_brief, provider_factory=provider_factory, **options)
    result.update(review_session_id=session_id, partial_reconstruction=bool(packet['excluded_labels']),
                  excluded_labels=packet['excluded_labels'], refusals=packet['refusals'])
    store.append_event(session_id, event_type='component_generation_completed', payload=result)
    return result
