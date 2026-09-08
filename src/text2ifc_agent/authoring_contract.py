"""Versioned, read-only projection of the same IFC registry used by validation."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable

from text2ifc_contract.capabilities import load_capabilities
from text2ifc_contract.materials import TYPE_OCCURRENCE
from text2ifc_contract.relationships_v2 import SUPPORTED_RELATIONSHIPS
from text2ifc_contract.validation_v2 import _ENUMERATION
from text2ifc_knowledge.registry import load_ifc2x3_registry

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_VERSION = 'text2ifc/generation-authoring-contract/1.0'
_MANAGED = {'GlobalId', 'OwnerHistory', 'HasPropertySets', 'RepresentationMaps'}


def build_authoring_contract(classes: Iterable[str] | None = None) -> dict:
    """Offer legal fields, not default facts or authorization to invent values."""
    registry = load_ifc2x3_registry()
    supported = {k for k, v in load_capabilities().items() if v == 'generate'}
    supported.update(k for k in TYPE_OCCURRENCE if registry.entity(k))
    supported.update(SUPPORTED_RELATIONSHIPS)
    selected = supported if classes is None else set(classes)
    unknown = selected - supported
    if unknown:
        raise ValueError(f'Classes outside generation authoring capability: {sorted(unknown)}')
    records = {}
    for name in sorted(selected):
        entity = registry.entity(name)
        if entity is None or entity['abstract']:
            raise ValueError(f'Not a concrete IFC entity: {name}')
        attrs = {}
        for field in entity['attributes']:
            key, expression = field['name'], field['type']
            if key in _MANAGED or field['derived']:
                continue
            value = {'ifc_type': expression, 'ifc_optional': field['optional']}
            enum = _ENUMERATION.search(expression)
            if key in {'ObjectPlacement', 'Representation'}:
                value['encoding'] = ('bim_json_object_placement' if key == 'ObjectPlacement'
                                     else 'bim_json_representation')
            elif enum:
                value['enum'] = enum.group(1).split(', ')
            elif '<string>' in expression:
                value['json_type'] = 'string'
            elif '<integer>' in expression:
                value['json_type'] = 'integer'
            elif '<real>' in expression:
                value['json_type'] = 'number'
            elif '<boolean>' in expression or '<logical>' in expression:
                value['json_type'] = 'boolean'
            elif name in SUPPORTED_RELATIONSHIPS:
                value['encoding'] = 'stable_entity_ids'
            else:
                # Low-level entity/select attachments are not authored as arbitrary JSON.
                continue
            attrs[key] = value
        records[name] = {'attributes': attrs}
    sources = ['schemas/ifc/generated/IFC2X3/declarations.json',
               'schemas/ifc/capabilities/IFC2X3.json', 'schemas/bim-json/2.1/schema.json']
    result = {
        'schema_version': CONTRACT_VERSION, 'ifc_schema': 'IFC2X3',
        'source_hashes': {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources},
        'classes': records,
        'policies': {
            'physical_materials': 'explicit_user_only', 'ordinary_properties': 'omit_unrequested',
            'attributes': 'Use only requested or contract-required values. IFC optional/required metadata is not a request to populate fields.',
            'types': 'No requested Type means omit explicit Type/Style entities and associations. The basic_filling compiler supplies a minimal legal DoorStyle. Explicit Type requests remain project-local and must match the requested template; do not merge coincident instances.',
            'enumerations': 'Use exact offered tokens. NOTDEFINED is legal only where offered and needed for a minimal IFC attachment, never as an invented property value or material.',
            'geometry': 'ObjectPlacement axes are local to relative_to. A child opening/filling inherits its rotated host once; identity local axes preserve host orientation. Preserve frozen world dimensions, position and opening.',
            'repair': 'The offered schema is read-only evidence, not write permission. Edit only explicitly authorized stable components and paths. Missing user facts or explicit conflicts require Draft.',
        },
    }
    encoded = json.dumps(result, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    result['contract_hash'] = 'sha256:' + hashlib.sha256(encoded).hexdigest()
    return result
