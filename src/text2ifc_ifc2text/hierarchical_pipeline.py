"""Executed LLM paragraph organization with deterministic fact insertion and review."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .hierarchy import assemble_hierarchy, batch_plan
from .llm_pipeline import _run_stage, _load_schema, _write_json
from text2ifc_text.splits import atomic_write_text

TEMPLATE_ID = 'ifc2text-hierarchical-writer.v0.3'


def run_hierarchical_writing(*, plan: dict, output_dir, provider: Any, run_id: str,
                             max_batch_chars: int = 6000, budget=None) -> dict:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    marker = root/'attempt-started.json'
    if marker.exists():
        raise ValueError('WRITING_ATTEMPT_ALREADY_EXISTS')
    batches = batch_plan(plan, max_chars=max_batch_chars)
    if budget is not None:
        budget.check_capacity('writing', calls=len(batches))
    _write_json(marker, {'run_id':run_id, 'batch_count':len(batches), 'template_id':TEMPLATE_ID})
    _write_json(root/'writing-plan.json', plan)
    schema = _load_schema('layout-0.3.schema.json')
    outputs = []
    try:
        for n, batch in enumerate(batches, 1):
            directory = root/f'batch-{n:03d}'
            output = _run_stage(provider=provider, output_dir=directory,
                stage='hierarchical_writing', session_id=f'{run_id}:batch-{n:03d}',
                template_id=TEMPLATE_ID, inputs={'BATCH':batch,'OUTPUT_SCHEMA':schema},
                schema=schema, state={'stage':'hierarchical_writing','run_id':run_id})
            validation = json.loads((directory/'validation.json').read_text(encoding='utf-8'))
            if validation.get('normalization_diagnostics'):
                raise ValueError('BARE_JSON_REQUIRED')
            # Validate each batch before the next transport, not just at final merge.
            assemble_hierarchy({'blocks':batch['blocks']}, [output])
            _write_json(directory/'content-check.json', {'valid':True, 'check':'ordered_exact_fact_fragment_coverage'})
            outputs.append(output)
        if budget is not None:
            budget.check_capacity('writing', calls=0)
        description = assemble_hierarchy(plan, outputs)
        atomic_write_text(root/'design-description.md', description)
        _write_json(root/'layout-results.json', outputs)
        report = {
            'schema_version':'text2ifc/ifc2text-hierarchical-run/0.3', 'status':'completed',
            'run_id':run_id,'template_id':TEMPLATE_ID,'provider_calls':len(outputs),
            'description_path':str(root/'design-description.md'),
            'fact_fragments_preserved':plan['fact_fragment_count'],
            'component_counts':plan['component_counts'],
            'mode':'LLM_paragraph_grouping_with_deterministic_fact_sentences',
            'checks':{'exact_coverage':True, 'no_generated_numeric_facts':True,
                      'no_free_prose_claims_accepted':True},
            'not_proven':['all_source_extraction_correct','room_function','all_IFC_classes_reconstructable'],
        }
        _write_json(root/'run.json', report)
        return report
    except Exception as error:
        if budget is not None:
            budget.halt('WRITING_STAGE_FAILED')
        _write_json(root/'terminal.json', {'status':'failed', 'error_type':type(error).__name__,
                                          'completed_batches':len(outputs), 'publication_permitted':False})
        raise
