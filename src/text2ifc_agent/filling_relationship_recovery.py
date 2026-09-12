"""Append missing Generation attachments only when frozen endpoints agree.

This is not host inference and cannot repair an external IFC. Existing entities,
relationships and all geometry remain untouched; full validation is atomic.
"""
import copy
import hashlib

from text2ifc_contract.validation_v2 import validate_v2_document
from .expected_facts import build_expected_facts, ExpectedFactsError


CONTRACT = 'text2ifc/filling-relationship-recovery/1.0'


def recover_filling_relationships(candidate, brief, *, case_id):
    blocked = {'eligible': False, 'candidate': None, 'contract': CONTRACT}
    if not isinstance(candidate, dict) or candidate.get('schema_version') not in {'bim-json/2.1', 'bim-json/2.2', 'bim-json/2.3'}:
        return blocked
    issues = validate_v2_document(candidate)
    if not issues or any(i.code != 'BASIC_FILLING_CONSTRAINT_CONFLICT' for i in issues):
        return blocked
    try:
        expected = build_expected_facts(case_id=case_id, design_brief=brief)
    except (ExpectedFactsError, ValueError, TypeError, KeyError):
        return blocked
    records = {r['id']: r for r in candidate['entities']}
    ids = [r['id'] for r in candidate['entities'] + candidate['relationships']]
    if len(ids) != len(set(ids)):
        return blocked
    identity = expected['entity_id_contract']
    added, evidence = [], []
    claimed_openings = set()
    for collection, cls in [('doors', 'IfcDoor'), ('windows', 'IfcWindow')]:
        for binding in identity.get(collection, []):
            eid = binding['entity_id']
            record = records.get(eid, {})
            if record.get('attributes', {}).get('Representation', {}).get('kind') != 'basic_filling':
                continue
            facts = [r for r in expected[collection] if r['id'] == binding['brief_id'] and r['storey'] == binding['storey']]
            if len(facts) != 1:
                return blocked
            fact = facts[0]
            hosts = [r['entity_id'] for r in identity.get('walls', [])
                     if r['brief_id'] == fact.get('host_wall') and r['storey'] == binding['storey']]
            if len(hosts) != 1:
                return blocked
            host, opening = hosts[0], 'opening-' + eid
            if opening in claimed_openings:
                return blocked
            claimed_openings.add(opening)
            if (record.get('ifc_class') != cls
                    or records.get(host, {}).get('ifc_class') not in {'IfcWall', 'IfcWallStandardCase'}
                    or records.get(opening, {}).get('ifc_class') != 'IfcOpeningElement'
                    or record['attributes'].get('ObjectPlacement', {}).get('relative_to') != opening
                    or records[opening]['attributes'].get('ObjectPlacement', {}).get('relative_to') != host):
                return blocked
            required = [
                ('IfcRelVoidsElement', {'RelatingBuildingElement': host, 'RelatedOpeningElement': opening}),
                ('IfcRelFillsElement', {'RelatingOpeningElement': opening, 'RelatedBuildingElement': eid}),
            ]
            for relation_class, attributes in required:
                # Include competing uses of either filling or opening, not just the desired pair.
                matching = [r for r in candidate['relationships'] if r['ifc_class'] == relation_class and (
                    r['attributes'].get('RelatedOpeningElement') == opening if relation_class == 'IfcRelVoidsElement'
                    else r['attributes'].get('RelatedBuildingElement') == eid or r['attributes'].get('RelatingOpeningElement') == opening)]
                if matching:
                    if len(matching) != 1 or any(matching[0]['attributes'].get(k) != v for k, v in attributes.items()):
                        return blocked
                    continue
                digest = hashlib.sha256((relation_class + '\0' + opening + '\0' + eid).encode()).hexdigest()[:24]
                rid = 'attachment-' + digest
                if rid in ids:
                    return blocked
                ids.append(rid)
                added.append({'id': rid, 'ifc_class': relation_class, 'attributes': attributes,
                              'provenance': {'source': CONTRACT}})
                evidence.append({'relationship_id': rid, 'filling_id': eid, 'opening_id': opening,
                                 'host_id': host, 'brief_id': binding['brief_id'], 'storey': binding['storey'],
                                 'basis': 'frozen Brief identity and host_wall; matching candidate placement parents'})
    if not added:
        return blocked
    after = copy.deepcopy(candidate)
    after['relationships'].extend(added)
    remaining = validate_v2_document(after)
    if remaining:
        return {**blocked, 'remaining_issues': [vars(i) for i in remaining]}
    return {'eligible': True, 'candidate': after, 'contract': CONTRACT,
            'added_relationships': added, 'evidence': evidence}
