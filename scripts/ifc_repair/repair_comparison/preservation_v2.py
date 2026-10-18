"""Subtract new roots without recursively changing shared source geometry.

The projection is an evaluator-owned copy, never a published IFC. Retaining
unreachable non-root entities is deliberate: they do not enter the existing
root fingerprints and must not be recursively deleted through shared edges.
The legacy scorer and all its stored reports remain unchanged.
"""
import ifcopenshell

from text2ifc_ifc_repair.compare import normalized_model_diff
from .formal_scoring import RELATIONS

VERSION = 'repair-comparison-preservation/0.2'


def preservation(damaged, result, new_guids):
    new_guids = set(new_guids)
    old = {entity.GlobalId for entity in damaged.by_type('IfcRoot')}
    if new_guids & old:
        raise ValueError('PRESERVATION_CANNOT_SUBTRACT_EXISTING_ROOT')
    stripped = ifcopenshell.file.from_string(result.to_string())
    for guid in sorted(new_guids):
        entity = stripped.by_guid(guid)
        if not entity.is_a('IfcProduct'):
            raise ValueError('PRESERVATION_SUBTRACTION_REQUIRES_PRODUCT')
        # Only normalize the new occurrence's relationship memberships. A
        # singular link or an empty membership disappears with the occurrence;
        # existing members and their support graphs must remain exactly intact.
        for inverse in tuple(stripped.get_inverse(entity)):
            if not inverse.is_a('IfcRelationship'):
                continue
            if any(value == entity for value in inverse):
                stripped.remove(inverse)
                continue
            for index, value in enumerate(inverse):
                if isinstance(value, tuple) and entity in value:
                    retained = tuple(item for item in value if item != entity)
                    if retained:
                        inverse[index] = retained
                    else:
                        stripped.remove(inverse)
                        break
        stripped.remove(entity)
    baseline = ifcopenshell.file.from_string(damaged.to_string())
    history = baseline.by_type('IfcOwnerHistory')[0]
    for model in (baseline, stripped):
        normalized = model.add(history)
        for root in model.by_type('IfcRoot'):
            root.OwnerHistory = normalized
    diff = normalized_model_diff(baseline, stripped)
    old_products = {entity.GlobalId for entity in damaged.by_type('IfcProduct')}
    extra = []
    for row in diff['created']:
        entity = stripped.by_guid(row['global_id'])
        if entity.is_a('IfcRelationship'):
            references = [item for value in entity
                          for item in (value if isinstance(value, tuple) else (value,))
                          if hasattr(item, 'GlobalId')]
            if any(item.GlobalId in old_products for item in references):
                extra.append(row['global_id'])
    # Same occurrence-support rule as the legacy independent formal scorer.
    allowed = set(new_guids)
    support = []
    for guid in new_guids:
        product = result.by_guid(guid)
        support.extend(result.traverse(product))
        for inverse in result.get_inverse(product):
            if inverse.is_a('IfcRelDefines') or inverse.is_a('IfcRelAssociates'):
                related = getattr(inverse, 'RelatedObjects', ())
                if related and all(getattr(item, 'GlobalId', None) in new_guids for item in related):
                    support.extend(result.traverse(inverse))
            elif inverse.is_a() in RELATIONS:
                allowed.add(inverse.GlobalId)
    allowed.update(entity.GlobalId for entity in support if entity.is_a('IfcRoot'))
    unrelated = sorted(entity.GlobalId for entity in result.by_type('IfcRoot')
                       if entity.GlobalId not in old and entity.GlobalId not in allowed)
    return {
        'passed': not diff['removed'] and not diff['modified'] and not extra and not unrelated,
        'removed_roots': [row['global_id'] for row in diff['removed']],
        'modified_roots': [row['global_id'] for row in diff['modified']],
        'extra_old_object_relations': extra, 'unrelated_added_roots': unrelated,
        'projection_version': VERSION,
        'scope': 'unchanged existing roots after shallow new-product/relationship projection; '
                 'no host waiver; same occurrence-support rule; unreachable non-root entities not audited',
    }
