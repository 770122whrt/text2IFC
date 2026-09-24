"""Explicit generation-version selection independent of a frozen Design Brief."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .semantic_requirements import generation_schema_version


def selected_generation_version(brief: Mapping[str, Any], case_dir: Path) -> str:
    path = Path(case_dir) / 'generation-contract.json'
    if not path.is_file():
        return generation_schema_version(brief)
    selection = json.loads(path.read_text(encoding='utf-8'))
    if (selection.get('schema_version') != 'text2ifc/generation-contract-selection/1.0'
            or selection.get('bim_json_schema_version') not in {'bim-json/2.4', 'bim-json/2.5'}
            or selection.get('generation_strategy') != 'legacy_full'):
        raise ValueError('Invalid generation contract selection')
    return selection['bim_json_schema_version']


def draft_schema_relative_path(version: str) -> str:
    minor = {'bim-json/2.0': '1.0', 'bim-json/2.1': '1.1',
             'bim-json/2.2': '1.2', 'bim-json/2.3': '1.3', 'bim-json/2.4': '1.4', 'bim-json/2.5': '1.5'}[version]
    return f'schemas/bim-json/draft/{minor}/schema.json'
