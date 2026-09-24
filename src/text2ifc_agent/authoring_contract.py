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
CONTRACT_VERSION = 'text2ifc/generation-authoring-contract/1.1'
_MANAGED = {'GlobalId', 'OwnerHistory', 'HasPropertySets', 'RepresentationMaps'}


def build_authoring_contract(classes: Iterable[str] | None = None, *, version: str = '1.1') -> dict:
    """Offer legal fields, not default facts or authorization to invent values."""
    if version not in {'1.0', '1.1', '1.2', '1.3', '1.4', '1.5', '1.6'}:
        raise ValueError(f'Unsupported authoring contract version: {version}')
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
    if version == '1.2':
        sources[-1] = 'schemas/bim-json/2.2/schema.json'
    if version == '1.3':
        sources[-1] = 'schemas/bim-json/2.3/schema.json'
    if version == '1.4':
        sources[-1] = 'schemas/bim-json/2.4/schema.json'
    if version == '1.5':
        sources[-1] = 'schemas/bim-json/2.5/schema.json'
    if version == '1.6':
        sources[-1] = 'schemas/bim-json/2.6/schema.json'
    result = {
        'schema_version': f'text2ifc/generation-authoring-contract/{version}', 'ifc_schema': 'IFC2X3',
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
    if version in {'1.1', '1.2', '1.3', '1.4', '1.5', '1.6'}:
        result['geometry_encoding'] = {
            'rectangle': {
                'anchor': 'profile_center_at_extrusion_base',
                'local_bounds': '[-x/2,+x/2] by [-y/2,+y/2]; vertical extrusion z=0..depth',
                'requested_bounds_to_origin': 'For an axis-aligned requested box [xmin,xmax] [ymin,ymax] [zmin,zmax], origin=((xmin+xmax)/2,(ymin+ymax)/2,zmin), profile=(xmax-xmin,ymax-ymin), depth=zmax-zmin.',
                'position': 'ObjectPlacement origin is NOT the southwest corner. Rectangle, polygon and stair profiles have different anchor meanings. Polygon coordinates are explicit local vertices; do not recenter them implicitly.',
            },
            'placement': {
                'child_origin_formula': 'inverse(parent_world) @ requested_world_point',
                'child_axes_formula': 'inverse(parent_world_rotation) @ requested_world_rotation',
                'composition': 'world = parent_world @ local; include each rotation and storey elevation exactly once.',
                'storey': 'Set ObjectPlacement translation to the requested storey elevation. Elevation metadata alone is not the placement. Children use storey-relative Z; never add the storey elevation twice.',
            },
            'wall_opening_filling': {
                'wall': 'Local X is wall length, Y is thickness, Z is height. Start the wall at its bottom center. A north-running wall may use ref_direction=[0,1,0]; its local +Y points west.',
                'opening': 'Use the opening bottom CENTER expressed in the host wall local frame, not its edge or an unconverted world coordinate. For aligned host and opening use local axis=[0,0,1], ref_direction=[1,0,0]. Opening profile x=nominal width, y=cut depth; extrusion depth=nominal height.',
                'filling': 'When relative_to is the opening and centers align, use origin=[0,0,0], axis=[0,0,1], ref_direction=[1,0,0]. Do not copy the rotated host axes into its child a second time. basic_filling width/depth are centered in XY; height starts at local Z=0.',
                'bounds': 'Check opening in host coordinates: abs(center_x)+width/2 <= host_length/2, bottom_z>=0, bottom_z+height<=host_height. Filling installation depth must fit wall thickness, even if cut depth is greater.',
            },
            'slab_void': 'Rectangular slabs and slab openings also use XY center origins. Convert a requested opening center into the slab frame; use an actual IfcRelVoidsElement and a cut spanning the slab thickness. Do not subtract half-width/half-length twice.',
            'policy': 'These are encoding rules, not permission to alter requested dimensions, materials, host, position, Type or opening. If explicit geometry is inconsistent, return Draft; do not fix it by resizing or moving user requirements.',
        }
        for source in ['src/text2ifc_compiler/geometry.py', 'src/text2ifc_contract/placement.py',
                       'src/text2ifc_contract/basic_filling.py', 'src/text2ifc_compiler/basic_filling.py']:
            result['source_hashes'][source] = hashlib.sha256((ROOT/source).read_bytes()).hexdigest()
    if version in {'1.2', '1.3', '1.4', '1.5', '1.6'}:
        result['policies']['part_appearance'] = 'Occurrence-only basic_filling frame/panel/glazing RGB and transparency. Explicit requested channels only; unspecified channels keep theme defaults. Whole occurrence or Type appearance conflicts. No geometry, Type, material or property changes.'
    if version in {'1.3', '1.4', '1.5', '1.6'}:
        from text2ifc_contract.basic_railing import VERSION, DEFAULTS, RANGES
        result['geometry_encoding']['basic_railing'] = {
            'template_id': 'metal-picket', 'template_version': VERSION,
            'family': 'IfcRailing occurrence only', 'units': 'mm',
            'required': ['length', 'height', 'depth'], 'optional': ['rise', 'parameters'],
            'anchor': 'Local X=0..length; Y centered on baseline; base Z=rise*X/length. Height is vertical above the baseline. Convert frozen world start and horizontal direction into the parent frame.',
            'bounds': {'length': [300,20000], 'height': [700,1600], 'depth': [20,100]},
            'rise': 'Signed end Z minus start Z; magnitude <= horizontal length. Keep local Z vertical; do not tilt placement and apply slope twice.',
            'parameter_defaults': DEFAULTS, 'parameter_ranges': RANGES,
            'limits': 'At most 512 solids; post/picket widths <= depth. Explicit parameters only; omitted parameters retain versioned defaults. No performance certification.',
        }
        result['policies']['basic_railing'] = 'Single explicit material and whole occurrence appearance only. No automatic physical material, properties, Type or mixed-part styling. Compiler generates and verifies posts, pickets and top/bottom rails; do not author them as extra entities.'
        for source in ['src/text2ifc_contract/basic_railing.py', 'src/text2ifc_compiler/basic_railing.py']:
            result['source_hashes'][source] = hashlib.sha256((ROOT/source).read_bytes()).hexdigest()
    if version in {'1.4', '1.5', '1.6'}:
        result['geometry_encoding']['polygon_wall_host'] = {
            'geometry': 'Positive-local-Z extrusion, convex constant-thickness polygon with parallel local-X sides; beveled ends allowed. Representation.position may translate or rotate about Z.',
            'opening_and_filling': 'Opening cutters may cross a wall end but need positive-volume intersection with the transformed wall solid. Fillings fit the opening and intersect the wall; full wall containment is not required. Preserve explicit end crossings.',
            'unsupported': 'Sloped, concave or variable-thickness layered walls require Draft.'}
        result['geometry_encoding']['wall_opening_filling']['explicit_depth'] = 'Preserve explicitly measured outside frame depth in basic_filling parameters.frame_depth when the frame defines the outside extent. Representation.depth is installation capacity, not frame thickness. Do not infer panel/glazing thickness from overall depth.'
    if version in {'1.5','1.6'}:
        result['policies']['physical_materials'] = 'Explicit single material, supported complete layers, or nonempty material_list of named items. Preserve list order and duplicates without inferring layer thickness or part assignment. Lists are unsupported on IfcWallStandardCase.'
        result['policies']['basic_railing'] = 'Explicit single material or material_list and whole occurrence appearance only. No part-specific material assignment, automatic physical material, properties, Type or mixed-part styling. Compiler generates and verifies posts, pickets and rails; do not author them as extra entities.'
    if version == '1.6':
        result['geometry_encoding']['component_geometry'] = {
            'family': ['IfcDoor','IfcWindow'], 'part_products': False,
            'version': 'text2ifc/components/1.0', 'units': 'millimetres',
            'profiles': ['rectangle','circle','polygon_with_optional_holes'],
            'parts': 'Local definition IDs, stable part IDs, geometry_refs, required part placement and solid position; optional finite repeated translation in the parent product frame.',
            'composition': 'product placement @ part placement @ solid position; direction is in the solid frame; profile XY anchor is explicit.',
            'nominal_dimensions': 'OverallWidth/OverallHeight are installation dimensions, not the union bounding box. Handles/trim may protrude. Never resize openings or recenter source geometry to make a template fit.',
            'appearance': 'Part RGB/transparency > occurrence > requested Type > theme. Physical part materials are unsupported.',
            'unsupported': 'No BRep, arbitrary curves, scaling/mirroring, implicit simplification, or template substitution. Missing required dimensions require clarification/Draft.'}
        result['geometry_encoding']['wall_opening_filling']['bounds'] += ' These template fit rules do not constrain exterior handles of an explicit component product; preserve its declared installation frame and dimensions.'
        for source in ['src/text2ifc_contract/component_geometry.py','src/text2ifc_compiler/component_geometry.py']:
            result['source_hashes'][source] = hashlib.sha256((ROOT/source).read_bytes()).hexdigest()
    encoded = json.dumps(result, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    result['contract_hash'] = 'sha256:' + hashlib.sha256(encoded).hexdigest()
    return result
