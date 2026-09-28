"""Exact storey identities derived from Brief IDs, independent of candidate claims."""
from collections import Counter, defaultdict
from collections.abc import Mapping


def storey_identity_records(storeys):
    records = []
    for row in storeys if isinstance(storeys, list) else []:
        identity = row.get('id') if isinstance(row, Mapping) else None
        if not isinstance(identity, str) or not identity:
            continue
        aliases = [identity] if identity.startswith('storey-') else [identity, 'storey-' + identity]
        records.append({'brief_id': identity, 'entity_id': identity, 'aliases': aliases,
            'ifc_class': 'IfcBuildingStorey'})
    return records


def resolve_storey_identities(candidate, expected):
    """Return unique exact aliases only; names/provenance do not grant identity."""
    records = storey_identity_records(expected.get('storeys', []))
    entities = [e for e in candidate.get('entities', []) if isinstance(e, Mapping)]
    counts = Counter(e.get('id') for e in entities if isinstance(e.get('id'), str))
    by_id = {e.get('id'): e for e in entities if isinstance(e.get('id'), str)}
    owners = defaultdict(set)
    brief_counts = Counter(r['brief_id'] for r in records)
    for row in records:
        for alias in row['aliases']:
            owners[alias].add(row['brief_id'])
    mapping, matches, issues = {}, [], []
    for row in records:
        identity = row['brief_id']
        present = [a for a in row['aliases'] if a in by_id]
        ambiguous = (brief_counts[identity] != 1 or len(present) > 1
            or any(len(owners[a]) != 1 or counts[a] != 1 for a in present))
        if ambiguous or len(present) != 1 or by_id[present[0]].get('ifc_class') != 'IfcBuildingStorey':
            issues.append({'code': 'STOREY_IDENTITY_AMBIGUOUS' if ambiguous else 'STOREY_IDENTITY_UNRESOLVED',
                'path': '/storeys/' + identity, 'expected_storey': identity,
                'candidate_ids': present, 'message': 'Require one uniquely assigned exact Brief ID or storey-prefix alias with IfcBuildingStorey class.'})
            continue
        actual = present[0]
        mapping[actual] = identity
        matches.append({'brief_id': identity, 'candidate_id': actual,
            'match_basis': 'exact_brief_id' if actual == identity else 'exact_storey_prefix_alias'})
    return mapping, matches, issues
