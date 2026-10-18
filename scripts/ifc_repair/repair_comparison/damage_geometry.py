"""Read-only effective wall-cut measurements for experiment preparation.

The independent counterfactual removes only void relationships in an in-memory
copy. It never calls the damage mutator or ``root.remove_product`` and never
writes an IFC. Overshooting cutter solids are not mistaken for material removed
from their host. Multi-opening sums are admitted only after a group check.
"""
from __future__ import annotations

from collections import defaultdict
import math

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.shape


METHOD = 'host-volume-delta-after-in-memory-void-relation-removal/0.1'
POSITIVE_VOLUME_EPSILON_M3 = 1e-9
GROUP_VOLUME_TOLERANCE_M3 = 1e-7


class DamageGeometryError(ValueError):
    """A fail-closed preparation diagnostic with serializable evidence."""
    def __init__(self, code, evidence=None):
        super().__init__(code)
        self.code = code
        self.evidence = evidence or {}


def _volume_m3(entity):
    settings = ifcopenshell.geom.settings()
    shape = ifcopenshell.geom.create_shape(settings, entity)
    volume = float(ifcopenshell.util.shape.get_volume(shape.geometry))
    if not math.isfinite(volume) or volume <= 0:
        raise DamageGeometryError('NONPOSITIVE_OR_NONFINITE_GEOMETRY_VOLUME',
                                  {'guid': entity.GlobalId, 'volume_m3': volume if math.isfinite(volume) else None})
    return volume


def _binding(model, opening_guid):
    try:
        opening = model.by_guid(opening_guid)
    except RuntimeError as error:
        raise DamageGeometryError('OPENING_NOT_FOUND', {'opening_guid': opening_guid}) from error
    if not opening.is_a('IfcOpeningElement'):
        raise DamageGeometryError('ENTITY_IS_NOT_OPENING', {'opening_guid': opening_guid})
    relations = list(opening.VoidsElements)
    if len(relations) != 1 or not relations[0].RelatingBuildingElement.is_a('IfcWall'):
        raise DamageGeometryError('OPENING_REQUIRES_UNIQUE_WALL', {'opening_guid': opening_guid,
                                  'void_relation_count': len(relations)})
    return opening, relations[0].RelatingBuildingElement, relations[0]


def _unvoided_volume(model, wall_guid, opening_guids):
    counterfactual = ifcopenshell.file.from_string(model.to_string())
    for guid in opening_guids:
        _, wall, relation = _binding(counterfactual, guid)
        if wall.GlobalId != wall_guid:
            raise DamageGeometryError('COUNTERFACTUAL_HOST_MISMATCH')
        # Leave both opening and filling occurrences, their geometry, placement,
        # and all other relationships intact. Only this Boolean link is removed.
        counterfactual.remove(relation)
    return _volume_m3(counterfactual.by_guid(wall_guid))


def effective_opening_volume(model, opening_guid):
    """Return this opening's positive marginal cut volume in frozen original G.

    Other openings remain active. Therefore overlapping openings contribute only
    their individually exposed part; use ``effective_opening_volumes`` before
    summing two or three targets, which verifies that no overlap was omitted.
    """
    opening, wall, _ = _binding(model, opening_guid)
    before = _volume_m3(wall)
    raw = _volume_m3(opening)
    without = _unvoided_volume(model, wall.GlobalId, [opening_guid])
    delta = without - before
    evidence = {'method': METHOD, 'ifcopenshell_version': ifcopenshell.version,
                'opening_guid': opening_guid, 'wall_guid': wall.GlobalId,
                'wall_volume_before_m3': before, 'wall_volume_without_opening_m3': without,
                'effective_volume_m3': delta, 'raw_cutter_volume_m3': raw,
                'positive_volume_epsilon_m3': POSITIVE_VOLUME_EPSILON_M3}
    if not math.isfinite(delta) or delta <= POSITIVE_VOLUME_EPSILON_M3:
        raise DamageGeometryError('NONPOSITIVE_EFFECTIVE_OPENING_VOLUME', evidence)
    return evidence


def effective_opening_volumes(model, opening_guids):
    """Measure 1–3 openings and reject non-additive/overlapping wall cuts.

    This is a pre-damage admission check. The caller must still compare actual
    mutation output against each wall's independently measured group delta.
    """
    guids = list(opening_guids)
    if not 1 <= len(guids) <= 3:
        raise DamageGeometryError('ONE_TO_THREE_OPENINGS_REQUIRED')
    if len(set(guids)) != len(guids):
        raise DamageGeometryError('DUPLICATE_OPENINGS')
    rows = [effective_opening_volume(model, guid) for guid in guids]
    grouped = defaultdict(list)
    for row in rows:
        grouped[row['wall_guid']].append(row)
    walls = {}
    for guid, group in grouped.items():
        before = group[0]['wall_volume_before_m3']
        without = _unvoided_volume(model, guid, [row['opening_guid'] for row in group])
        delta = without - before
        total = sum(row['effective_volume_m3'] for row in group)
        discrepancy = abs(delta - total)
        evidence = {'wall_guid': guid, 'opening_guids': [row['opening_guid'] for row in group],
                    'wall_volume_before_m3': before, 'wall_volume_without_openings_m3': without,
                    'effective_sum_m3': total, 'group_delta_m3': delta,
                    'absolute_difference_m3': discrepancy, 'tolerance_m3': GROUP_VOLUME_TOLERANCE_M3,
                    'non_overlapping': discrepancy <= GROUP_VOLUME_TOLERANCE_M3}
        if not math.isfinite(delta) or delta <= POSITIVE_VOLUME_EPSILON_M3:
            raise DamageGeometryError('NONPOSITIVE_GROUP_OPENING_VOLUME', evidence)
        if not evidence['non_overlapping']:
            # Other geometric non-additivity is equally inadmissible; no guessed
            # subtraction or overlap correction may silently accept this case.
            raise DamageGeometryError('OVERLAPPING_OPENINGS_UNSUPPORTED', evidence)
        walls[guid] = evidence
    return {'method': METHOD, 'openings': rows, 'walls': walls}
