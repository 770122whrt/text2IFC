"""Occurrence part styles for BIM JSON 2.2; never alter geometry or materials."""
import math

from .validation import ValidationIssue

PARTS = {'IfcDoor': {'frame', 'panel'}, 'IfcWindow': {'frame', 'glazing'}}


def valid_part_appearance(value, ifc_class=None):
    allowed = PARTS.get(ifc_class, set()) if ifc_class else {'frame', 'panel', 'glazing'}
    if not isinstance(value, dict) or not value or not set(value) <= allowed:
        return False
    for channels in value.values():
        if not isinstance(channels, dict) or not channels or not set(channels) <= {'color', 'transparency'}:
            return False
        numbers = []
        if 'color' in channels:
            if not isinstance(channels['color'], list) or len(channels['color']) != 3:
                return False
            numbers.extend(channels['color'])
        if 'transparency' in channels:
            numbers.append(channels['transparency'])
        if any(isinstance(n, bool) or not isinstance(n, (int, float)) or not math.isfinite(n) or not 0 <= n <= 1 for n in numbers):
            return False
    return True


def validate_part_appearance_document(document):
    records = {e.get('id'): e for e in document.get('entities', []) if isinstance(e, dict)}
    types = {}
    for rel in document.get('relationships', []):
        if not isinstance(rel, dict) or rel.get('ifc_class') != 'IfcRelDefinesByType':
            continue
        attrs = rel.get('attributes', {})
        for identity in attrs.get('RelatedObjects', []):
            types.setdefault(identity, []).append(records.get(attrs.get('RelatingType'), {}))
    issues = []
    for index, record in enumerate(document.get('entities', [])):
        if not isinstance(record, dict) or 'part_appearance' not in record:
            continue
        rep = record.get('attributes', {}).get('Representation', {})
        conflict = 'appearance' in record or any('appearance' in t for t in types.get(record.get('id'), []))
        if (not valid_part_appearance(record['part_appearance'], record.get('ifc_class'))
                or rep.get('kind') != 'basic_filling' or conflict):
            issues.append(ValidationIssue('INVALID_PART_APPEARANCE', f'/entities/{index}/part_appearance',
                'Part appearance requires an existing basic-filling occurrence and applicable frame/panel/glazing channels; whole occurrence or inherited Type appearance conflicts.'))
    return issues
