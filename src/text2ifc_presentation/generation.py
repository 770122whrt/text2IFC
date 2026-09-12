"""Coordinated Generation 2.1 appearance; never authors physical semantics."""
from __future__ import annotations

import json
import math
import ifcopenshell.util.element as util
from ifcopenshell.api.pset.add_pset import add_pset
from ifcopenshell.api.pset.edit_pset import edit_pset

from . import AppearanceSpec, assign_item_appearance, assign_material_appearance, item_appearance_signatures

THEMES = {
    'neutral-architectural': {
        'default': (0.72, 0.74, 0.73), 'wall': (0.84, 0.85, 0.81),
        'slab': (0.66, 0.67, 0.65), 'structural': (0.37, 0.43, 0.47),
        'frame': (0.25, 0.29, 0.31), 'panel': (0.60, 0.47, 0.34),
        'glazing': (0.60, 0.77, 0.83), 'roof': (0.25, 0.29, 0.30),
    },
    'warm-residential': {
        'default': (0.76, 0.70, 0.61), 'wall': (0.86, 0.80, 0.69),
        'slab': (0.68, 0.63, 0.55), 'structural': (0.45, 0.40, 0.34),
        'frame': (0.35, 0.30, 0.25), 'panel': (0.59, 0.38, 0.23),
        'glazing': (0.63, 0.77, 0.79), 'roof': (0.31, 0.26, 0.22),
    },
}


def _identity(entity):
    return util.get_psets(entity, should_inherit=False).get('Pset_text2IFCIdentity', {}).get('BimJsonId')


def _role(product):
    if product.is_a('IfcWall'): return 'wall'
    if product.is_a('IfcBeam') or product.is_a('IfcColumn'): return 'structural'
    return {'IfcDoor': 'panel', 'IfcWindow': 'glazing', 'IfcSlab': 'slab', 'IfcRoof': 'roof'}.get(product.is_a(), 'default')


def apply_coordinated_appearance(model, document, context):
    selection = document.get('appearance', {})
    theme = selection.get('profile', 'neutral-architectural')
    palette = THEMES[theme]
    records = {e['id']: e for e in document['entities']}
    styled_material_ids = set()
    for product in model.by_type('IfcProduct'):
        if product.is_a('IfcOpeningElement') or product.is_a('IfcSpace') or not product.Representation:
            continue
        record = records.get(_identity(product), {})
        type_object = util.get_type(product)
        type_record = records.get(_identity(type_object), {}) if type_object else {}
        explicit = record.get('appearance') or type_record.get('appearance')
        source = 'user' if record.get('appearance') else 'type' if explicit else 'theme'
        overrides = record.get('part_appearance', {}) if document.get('schema_version') in {'bim-json/2.2', 'bim-json/2.3'} else {}
        if overrides:
            source = 'user-parts'
        material = util.get_material(product)
        role = _role(product)
        if material and material.is_a('IfcMaterial') and material.id() not in styled_material_ids:
            # Styles are assigned to this actual material entity; its Name is
            # neither a material identity nor evidence of physical performance.
            material_spec = AppearanceSpec(f'{theme}:material', *palette['default'])
            assign_material_appearance(model, material=material, context=context, spec=material_spec)
            styled_material_ids.add(material.id())
        part_roles = {}
        for aspect in getattr(product.Representation, 'HasShapeAspects', ()):
            part_role = {'Framing': 'frame', 'Lining': 'frame', 'Glazing': 'glazing', 'Panel': 'panel'}.get(aspect.Name)
            if part_role:
                for representation in aspect.ShapeRepresentations:
                    part_roles.update({item.id(): part_role for item in representation.Items})
        applied = []
        for representation in product.Representation.Representations:
            if representation.RepresentationIdentifier != 'Body': continue
            for item in representation.Items:
                part = part_roles.get(item.id(), role)
                if explicit:
                    spec = AppearanceSpec('explicit-user', *explicit.get('color', palette[part]), transparency=explicit.get('transparency', 0.0))
                elif part in overrides:
                    channels = overrides[part]
                    spec = AppearanceSpec(f'explicit-user:{part}', *channels.get('color', palette[part]),
                                          transparency=channels.get('transparency', .45 if part == 'glazing' else 0.))
                else:
                    spec = AppearanceSpec(f'{theme}:{part}', *palette[part], transparency=0.45 if part == 'glazing' else 0.0)
                # Part/default item bindings make effective style deterministic
                # across viewers, while material-owned style remains available.
                assign_item_appearance(model, item=item, spec=spec)
                applied.append({'role': part, **spec.signature(), **({'channel_sources': {
                    key: 'user' if key in overrides.get(part, {}) else f'theme:{theme}'
                    for key in ('color', 'transparency')}} if overrides else {})})
        pset = add_pset(model, product=product, name='Pset_text2IFCAppearance')
        edit_pset(model, pset=pset, properties={'Profile': theme, 'Source': source,
                  'Seed': str(selection.get('seed', '')), 'PartsJson': json.dumps(applied, sort_keys=True)})


def verify_appearance(model, document):
    from text2ifc_compiler.verification import IfcValidationIssue
    issues = []
    records = {e['id']: e for e in document['entities']}
    palette = THEMES[document.get('appearance', {}).get('profile', 'neutral-architectural')]
    for product in model.by_type('IfcProduct'):
        if product.is_a('IfcOpeningElement') or product.is_a('IfcSpace') or not product.Representation:
            continue
        identity = _identity(product)
        record = records.get(identity, {})
        type_object = util.get_type(product)
        explicit = record.get('appearance') or (records.get(_identity(type_object), {}).get('appearance') if type_object else None)
        overrides = record.get('part_appearance', {}) if document.get('schema_version') in {'bim-json/2.2', 'bim-json/2.3'} else {}
        roles = {}
        for aspect in getattr(product.Representation, 'HasShapeAspects', ()):
            role = {'Framing':'frame','Lining':'frame','Glazing':'glazing','Panel':'panel'}.get(aspect.Name)
            if role:
                roles.update({item.id():role for shape in aspect.ShapeRepresentations for item in shape.Items})
        for shape in product.Representation.Representations:
            if shape.RepresentationIdentifier != 'Body': continue
            for item in shape.Items:
                values = item_appearance_signatures(item)
                valid = len(values) == 1 and all(0 <= float(values[0][k]) <= 1 for k in ('red','green','blue','transparency'))
                role = roles.get(item.id(), _role(product))
                wanted = [*explicit.get('color', palette[role]), explicit.get('transparency', 0.0)] if explicit else [*palette[role], .45 if role == 'glazing' else 0.0]
                if role in overrides:
                    channels = overrides[role]
                    wanted = [*channels.get('color', palette[role]), channels.get('transparency', .45 if role == 'glazing' else 0.)]
                if valid:
                    valid = all(math.isclose(values[0][k], v, abs_tol=1e-6) for k, v in zip(('red','green','blue','transparency'), wanted))
                if not valid:
                    issues.append(IfcValidationIssue('IFC_APPEARANCE_MISMATCH', str(identity), 'appearance', 'Missing, ambiguous or incorrect effective item style.'))
        if overrides and not set(overrides).issubset(roles.values()):
            issues.append(IfcValidationIssue('IFC_APPEARANCE_MISMATCH', str(identity), 'part_appearance', 'Requested part is absent from the actual IFC shape aspects.'))
    return tuple(issues)
