"""Independent, one-to-one slab opening binding for geometry contract 1.1."""
from collections import defaultdict
from collections.abc import Mapping
from math import isfinite

import ifcopenshell.util.element


def check_floor_openings(*, model, expected, tolerance, issues):
    # Imported at execution time: generated_ifc owns shared mesh diagnostics.
    from .generated_ifc import _bbox_for_product, _bbox_matches, _issue

    if not isinstance(expected, Mapping):
        return {}
    identities = defaultdict(list)
    product_ids = {}
    for product in model.by_type('IfcProduct'):
        value = ifcopenshell.util.element.get_psets(product, should_inherit=False).get(
            'Pset_text2IFCIdentity', {}).get('BimJsonId')
        if isinstance(value, str) and value:
            identities[value].append(product)
            product_ids[product.id()] = value
    metrics = {}
    used = set()
    bbox_cache = {}

    def bbox(product):
        if product.id() not in bbox_cache:
            bbox_cache[product.id()] = _bbox_for_product(product)
        return bbox_cache[product.id()]

    def on_host(opening, host):
        relations = opening.VoidsElements or ()
        return len(relations) == 1 and relations[0].RelatingBuildingElement == host

    for identity, record in expected.items():
        path = f'/floor_openings/{identity}'
        refs = record.get('source_fact_refs') if isinstance(record, Mapping) else None

        def fail(code, message, **details):
            issues.append(_issue(code, path, message, entity_ids=[str(identity)],
                                 source_fact_refs=refs, **details))

        if not isinstance(record, Mapping) or record.get('identity_source') not in {'explicit', 'derived'}:
            fail('GEOMETRY_EXPECTATION_INCOMPLETE', 'Opening identity provenance is missing or invalid.')
            continue
        bounds = record.get('bbox')
        if not _valid_bbox(bounds) or not isinstance(record.get('host_slab_id'), str):
            fail('GEOMETRY_EXPECTATION_INCOMPLETE', 'Opening requires frozen world bounds and host identity.')
            continue
        hosts = identities.get(record['host_slab_id'], [])
        if len(hosts) != 1 or not hosts[0].is_a('IfcSlab'):
            fail('FLOOR_OPENING_HOST_BINDING_INVALID', 'Expected host must identify exactly one IfcSlab.')
            continue
        host = hosts[0]
        targets = identities.get(str(identity), [])
        if len(targets) > 1:
            fail('FLOOR_OPENING_BINDING_AMBIGUOUS', 'Expected opening identity occurs more than once.')
            continue
        basis = record['identity_source'] + '_identity'
        if not targets and record['identity_source'] == 'derived':
            # Identity matching is deliberately tighter than the geometry gate:
            # a nearby equal-sized opening cannot stand in for the requested one.
            for opening in model.by_type('IfcOpeningElement'):
                if not on_host(opening, host):
                    continue
                try:
                    matches = _bbox_matches(bbox(opening), bounds, min(tolerance, 1e-6))
                except (RuntimeError, ValueError):
                    fail('FLOOR_OPENING_GEOMETRY_UNAVAILABLE', 'Cannot establish a unique binding with unreadable host opening geometry.')
                    continue
                if matches:
                    targets.append(opening)
            basis = 'unique_host_and_bounds'
        if not targets:
            fail('MISSING_STAIR_OPENING', 'No opening satisfies the frozen identity/host/bounds obligation.')
            continue
        if len(targets) != 1:
            fail('FLOOR_OPENING_BINDING_AMBIGUOUS', 'More than one opening satisfies the frozen host and bounds.')
            continue
        target = targets[0]
        actual_id = product_ids.get(target.id())
        if actual_id is None or len(identities[actual_id]) != 1:
            fail('FLOOR_OPENING_BINDING_AMBIGUOUS', 'Resolved opening lacks a unique compiler identity.')
            continue
        if not target.is_a('IfcOpeningElement'):
            fail('FLOOR_OPENING_FAMILY_MISMATCH', 'Resolved identity is not an IfcOpeningElement.')
            continue
        if not on_host(target, host):
            fail('FLOOR_OPENING_HOST_MISMATCH', 'Opening is not uniquely voiding its frozen host slab.')
            continue
        if target.id() in used:
            fail('FLOOR_OPENING_BINDING_REUSED', 'One IFC opening cannot satisfy two frozen obligations.')
            continue
        used.add(target.id())
        try:
            actual_bbox = bbox(target)
        except (RuntimeError, ValueError):
            fail('FLOOR_OPENING_GEOMETRY_UNAVAILABLE', 'Resolved opening geometry cannot be read.')
            continue
        metrics[str(identity)] = {'ifc_class': target.is_a(), 'bbox': actual_bbox,
            'binding_basis': basis, 'resolved_bim_json_id': actual_id,
            'resolved_global_id': target.GlobalId, 'host_slab_id': record['host_slab_id']}
        if not _bbox_matches(actual_bbox, bounds, tolerance):
            fail('FLOOR_OPENING_BBOX_MISMATCH', 'Opening bounds differ from the frozen requirement.',
                 expected=bounds, actual=actual_bbox)
    return metrics


def _valid_bbox(bounds):
    return isinstance(bounds, Mapping) and all(
        isinstance(bounds.get(axis), (list, tuple)) and len(bounds[axis]) == 2
        and all(isinstance(v, (int, float)) and not isinstance(v, bool) and isfinite(v) for v in bounds[axis])
        and bounds[axis][0] < bounds[axis][1] for axis in ('x', 'y', 'z'))
