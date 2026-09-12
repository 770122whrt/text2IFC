"""One technical ID projection for cross-storey authoring and verification."""
from collections.abc import Mapping


def slab_openings(record):
    raw = record.get('openings')
    openings = [item for item in raw if isinstance(item, Mapping)] if isinstance(raw, list) else []
    if isinstance(record.get('opening'), Mapping):
        openings.insert(0, record['opening'])
    return openings


def floor_opening_id(record, slab_id, index):
    explicit = record.get('id')
    if isinstance(explicit, str) and explicit:
        return explicit
    suffix = '' if index == 0 else f'-{index + 1}'
    return f'opening-{slab_id}-stair{suffix}'


def stair_flight_ids(record, stair_id):
    explicit = record.get('flight_ids')
    if isinstance(explicit, list) and explicit:
        return [str(item) for item in explicit]
    # Preserve established IDs. A non-prefixed parent must not also become its
    # own child; IDs are opaque, so never strip an apparent role suffix.
    derived = stair_id.replace('stair-', 'stair-flight-', 1)
    return [derived if derived != stair_id else f'{stair_id}-flight']


def cross_storey_entity_records(*, slabs, stairs, roof):
    result = {key: [] for key in ('slabs', 'floor_openings', 'stairs', 'stair_flights', 'roof')}

    def add(collection, identity, **fields):
        result[collection].append({'brief_id': identity, 'entity_id': identity, **fields})

    for slab in slabs:
        identity = slab.get('id')
        if not isinstance(identity, str) or not identity:
            continue
        add('slabs', identity, storey=slab.get('storey'))
        for index, opening in enumerate(slab_openings(slab)):
            add('floor_openings', floor_opening_id(opening, identity, index), host_id=identity,
                storey=slab.get('storey'), identity_source='explicit' if opening.get('id') else 'derived')
    for stair in stairs:
        identity = stair.get('id')
        if not isinstance(identity, str) or not identity:
            continue
        endpoints = {'storey': stair.get('from_storey'), 'to_storey': stair.get('to_storey')}
        add('stairs', identity, **endpoints)
        for child in stair_flight_ids(stair, identity):
            add('stair_flights', child, parent_id=identity, **endpoints)
    if isinstance(roof, Mapping) and isinstance(roof.get('id'), str) and roof['id']:
        add('roof', roof['id'])
        for index, opening in enumerate(slab_openings(roof)):
            add('floor_openings', floor_opening_id(opening, roof['id'], index), host_id=roof['id'],
                storey=roof.get('storey'), identity_source='explicit' if opening.get('id') else 'derived')
    return result
