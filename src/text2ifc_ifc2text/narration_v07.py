"""Narrow narration contract: materials remain in the measured table section."""
from __future__ import annotations
import re
from .compact import narrative_context, validate_narration
from .compact_pipeline import narration_schema
from .llm_pipeline import _run_stage

TEMPLATE='ifc2text-compact-narrator.v0.7'


def validate_notes(output, context):
    validate_narration(output,context)
    for note in output['storey_notes']:
        if re.search(r'材料|材质|层序|涂料|油漆',note['text']):
            raise ValueError('MATERIAL_ASSERTIONS_BELONG_IN_DETERMINISTIC_SECTION')


def write_notes(facts, output_dir, provider):
    context=narrative_context(facts); schema=narration_schema(context)
    value=_run_stage(provider=provider,output_dir=output_dir,stage='compact_narration_v07',
        session_id='wall-detail:narration-v07',template_id=TEMPLATE,
        inputs={'FACT_SUMMARY':context,'OUTPUT_SCHEMA':schema},schema=schema,state={'stage':'compact_narration_v07'})
    validate_notes(value,context)
    return value
