from pathlib import Path
import json, hashlib

root=Path('prompts/agent')
registry_path=root/'registry.json'
text=registry_path.read_text(encoding='utf-8')
registry=json.loads(text)
entries=[]
for old,new,oldfile,newfile in [
    ('design-brief.v2.2','design-brief.v2.3','design-brief-v2.2.md','design-brief-v2.3.md'),
    ('bim-json-changeset.v1.4','bim-json-changeset.v1.5','bim-json-changeset-v1.4.md','bim-json-changeset-v1.5.md')]:
    assert not (root/newfile).exists()
    content=(root/oldfile).read_text(encoding='utf-8')
    if old.startswith('design-brief'):
        content=content.replace('Use this shape for spaces, stairs, and slab openings when their bounds were supplied.',
            'Use this shape for spaces, exterior and interior walls, stairs, and slab openings when their bounds were supplied. '
            'Keep explicit wall bounds even when the same wall also has connects; connects records adjacency and does not replace its full extent.')
        old_clause=('3. Before returning `ready`, verify that each explicitly located door or window\n'
            '   has a host wall on the same storey. For an interior door, its stated center\n'
            '   must lie on a positive-length shared boundary segment of the named spaces.\n'
            '   If not, record `DOOR_HOST_NO_SHARED_SEGMENT` in a blocking item\'s reason;\n'
            '   do not move the door or substitute another wall.')
        new_clause=('3. Before returning `ready`, verify that each explicitly located door or window\n'
            '   has a host wall on the same storey. For an interior door with an explicitly\n'
            '   bounded or centerline-defined wall, check its position against that confirmed\n'
            '   host and the stated connected rooms. Net room rectangles may be separated\n'
            '   by the confirmed wall thickness; do not require them to share an edge.\n'
            '   Only when no explicit wall geometry exists may a unique shared boundary\n'
            '   determine the wall. Missing or contradictory host facts remain blocking;\n'
            '   do not move the door, extend a room, or substitute another wall.')
        assert old_clause in content
        content=content.replace(old_clause,new_clause)
        content+='''\nExplicit geometry fact completeness\n\n1. Before ready, compare the original request and all confirmed corrections with each wall record: retain full bounds or centerline endpoints, thickness, height, storey, and source_turns whenever explicitly supplied. A room adjacency label is not a substitute for any supplied coordinate.\n2. A landing or a net room may touch only part of a wall. Preserve the wall's explicit full length; never shorten it to the overlapping span of connected spaces. Do not infer a full-length wall across an unconfirmed gap.\n3. If explicit wall geometry and adjacency conflict, keep both facts and record an ambiguity. Ask only for the contradictory engineering fact; do not ask the user to provide IFC IDs or JSON implementation. Missing bounds must remain missing when they cannot be derived uniquely.\n4. Preserve each supplied slab opening separately, including its explicit id if supplied, host, and bounds. Never merge rectangles or silently discard a duplicate or incomplete opening.\n5. Material, appearance, and performance remain separate facts: a wood tone alone does not specify wood material or a fire rating. No unstated physical or performance property may be added to fill a template.\n'''
    else:
        old_clause='3. For an interior wall with `connects: [space_a, space_b]`, derive an interior wall only from the unique shared boundary of those two confirmed space bounds. Do not guess a wall axis or coordinate. If the boundary is missing or non-unique, return Draft or a scoped unresolved result.'
        new_clause='3. For an interior wall, use its confirmed explicit bounds or centerline endpoints and thickness first, even when `connects: [space_a, space_b]` is present. Net rooms may be separated by wall thickness, and a landing may touch only part of a longer wall. Never shorten explicit wall geometry to the room overlap. Only when explicit wall geometry is absent may a unique shared boundary of the two confirmed spaces determine it. Do not guess a wall axis, thickness, or coordinate; missing, non-unique, or conflicting facts require Draft or a scoped unresolved result. Preserve explicit wall and opening identities and stay within CHANGE_SCOPE.'
        assert old_clause in content
        content=content.replace(old_clause,new_clause)
    (root/newfile).write_text(content,encoding='utf-8',newline='\n')
    entry=next(e.copy() for e in registry['templates'] if e['template_id']==old)
    entry.update(template_id=new,path=f'prompts/agent/{newfile}',sha256='sha256:'+hashlib.sha256(content.encode()).hexdigest())
    entries.append(entry)
addition=',\n'+',\n'.join('\n'.join('    '+line for line in json.dumps(e,ensure_ascii=False,indent=2).splitlines()) for e in entries)
index=text.rfind('\n  ]')
assert index>0
registry_path.write_text(text[:index]+addition+text[index:],encoding='utf-8',newline='\n')
