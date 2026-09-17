"""Versioned compact IFC2Text execution and explicit content review boundary."""
from __future__ import annotations
from collections import Counter
from pathlib import Path
import copy
import json
import re
import ifcopenshell
from text2ifc_text.splits import atomic_write_text
from .compact import compact_description, narrative_context, validate_narration
from .observation import extract_description_facts, all_items, CATEGORIES
from .llm_pipeline import _write_json, _run_stage, _load_schema

TEMPLATE = 'ifc2text-compact-narrator.v0.4'
CLASSES = dict(zip(CATEGORIES, ['IfcWall','IfcOpeningElement','IfcDoor','IfcWindow','IfcSpace','IfcStair','IfcSlab','IfcCovering']))


def prepare_compact(source, output):
    source = Path(source); output = Path(output)
    if (output/'prepared.json').exists(): raise ValueError('PREPARED_ALREADY_EXISTS')
    before = source.read_bytes()
    facts = extract_description_facts(source)
    text = compact_description(facts)
    model = ifcopenshell.open(str(source))
    observed = {c: len(model.by_type(t)) for c,t in CLASSES.items()}
    counts = Counter(c for c,i in all_items(facts))
    if any(observed[c] != counts[c] for c in CATEGORIES): raise ValueError('ENTITY_COVERAGE_MISMATCH')
    if source.read_bytes() != before: raise ValueError('SOURCE_CHANGED')
    _write_json(output/'source-facts.json', facts)
    _write_json(output/'narrative-context.json', narrative_context(facts))
    atomic_write_text(output/'design-description-deterministic.md', text)
    report = {'schema_version':'text2ifc/compact-prepared/0.4', 'status':'prepared',
        'source_path':str(source), 'schema':model.schema, 'counts':observed,
        'derived_regions':sum(len(s.get('derived_spaces',[])) for s in facts['storeys']),
        'unrepresented_classes':facts.get('unrepresented_classes',{}),
        'characters':len(text), 'han_characters':len(re.findall(r'[\u4e00-\u9fff]',text)),
        'source_unchanged':True, 'coordinate_unit':'mm', 'coordinate_decimals':1}
    _write_json(output/'prepared.json', report)
    return report


def narration_schema(context):
    """Pin output positions to canonical IDs; never silently accept name aliases."""
    schema = _load_schema('compact-narration-0.4.schema.json')
    notes = schema['properties']['storey_notes']
    prototype = notes['items']
    notes['prefixItems'] = []
    for storey in context['storeys']:
        item = copy.deepcopy(prototype)
        item['properties']['storey'] = {'const': storey['id']}
        notes['prefixItems'].append(item)
    notes['items'] = False
    notes['minItems'] = notes['maxItems'] = len(context['storeys'])
    return schema


def write_compact(*, output, provider, budget=None, template_id=TEMPLATE):
    output = Path(output)
    if (output/'writing/attempt.json').exists(): raise ValueError('WRITING_ATTEMPT_EXISTS')
    load = lambda p: json.loads(p.read_text(encoding='utf-8'))
    facts = load(output/'source-facts.json'); context = narrative_context(facts)
    _write_json(output/'writing/attempt.json', {'template':template_id, 'stage':'compact_narration'})
    schema = narration_schema(context) if template_id in {'ifc2text-compact-narrator.v0.5', 'ifc2text-compact-narrator.v0.6'} else _load_schema('compact-narration-0.4.schema.json')
    try:
        result = _run_stage(provider=provider, output_dir=output/'writing/narration', stage='compact_narration',
            session_id=output.name+':narration', template_id=template_id,
            inputs={'FACT_SUMMARY':context,'OUTPUT_SCHEMA':schema}, schema=schema, state={'stage':'compact_narration'})
        validate_narration(result, context)
        text = compact_description(facts, result)
        atomic_write_text(output/'design-description.md', text)
        atomic_write_text(output/'design-description.txt', text)
        report = {'schema_version':'text2ifc/compact-writing/0.4', 'status':'text_complete_pending_prose_review',
            'provider_calls':1, 'template':template_id, 'characters':len(text),
            'mode':'LLM_short_narrative_plus_deterministic_measurement_tables',
            'numeric_table_authority':'source-facts.json', 'checks':{'deterministic_tables_unchanged':True},
            'description_path':str(output/'design-description.md')}
        _write_json(output/'writing/result.json', report)
        return report
    except Exception as error:
        if budget: budget.halt('COMPACT_WRITING_FAILED')
        _write_json(output/'writing/terminal.json', {'status':'failed', 'error_type':type(error).__name__,
            'reason':str(error) if isinstance(error, ValueError) else 'See preserved provider evidence'})
        raise
