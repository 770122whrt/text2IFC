import copy
import hashlib
import json
from pathlib import Path

root = Path.cwd()
old = json.loads((root/'schemas/agent/design-brief/2.1/schema.json').read_text(encoding='utf-8'))
schema = copy.deepcopy(old)
schema['$id'] = schema['$id'].replace('/2.1/', '/2.2/')
schema['title'] = 'text2IFC Semantic Authority Design Brief 2.2'
schema['properties']['schema_version']['const'] = 'text2ifc/design-brief/2.2'
known = schema['properties']['known_facts']
known['required'] = ['semantic_requirements', 'semantic_review']
known['properties']['semantic_review'] = {
    'type': 'object', 'additionalProperties': False,
    'required': ['material', 'property', 'type', 'appearance', 'template'],
    'properties': {kind: {'type': 'object', 'additionalProperties': False,
        'required': ['status', 'source_turns'], 'properties': {
            'status': {'enum': ['specified', 'not_specified', 'unresolved']},
            'source_turns': {'type': 'array', 'minItems': 1, 'uniqueItems': True,
                             'items': {'type': 'string', 'minLength': 1}}}}
        for kind in ['material', 'property', 'type', 'appearance', 'template']}}
target = root/'schemas/agent/design-brief/2.2/schema.json'
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(schema, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
addition = '''

Semantic authority completeness (Design Brief 2.2)

Before ready, review every original and confirmed user turn separately for material,
property, Type, element appearance and filling template requirements. ALWAYS emit
known_facts.semantic_requirements (an explicit empty array only when no such records
are required) and known_facts.semantic_review with all five required categories.
Each review entry uses specified / not_specified / unresolved and exact source_turns
from CONVERSATION. These are a review of input, not a claim about the final IFC.
specified requires at least one matching canonical semantic requirement;
not_specified requires none. unresolved cannot be ready. Do not create properties
or materials merely to fill this review. The global appearance profile/default
does not itself authorize element-level appearance overrides.

Narrative material policies, design notes and appearance descriptions cannot replace
canonical semantic_requirements. If the user requests one material for all members
of a group, enumerate every affected stable entity_id before generation; preserve
Type/instance scope. Preserve restrictions on every unrequested category. Basic
filling template choices use the existing approved defaults and source labels.
Never infer material or performance from a colour or template. Missing extraction
must be corrected by the Agent; do not ask the user to re-enter already clear facts.
Genuine ambiguity or unsupported semantics still follow the normal user route.
'''
registry_path = root/'prompts/agent/registry.json'
registry_text = registry_path.read_text(encoding='utf-8')
registry = json.loads(registry_text)
by_id = {r['template_id']: r for r in registry['templates']}
new = []
for previous, version in [('2.3', '2.5'), ('2.4', '2.6')]:
    text = (root/f'prompts/agent/design-brief-v{previous}.md').read_text(encoding='utf-8')
    text = text.replace('Design Brief 2.1', 'Design Brief 2.2').replace('design-brief/2.1', 'design-brief/2.2') + addition
    path = root/f'prompts/agent/design-brief-v{version}.md'
    path.write_text(text, encoding='utf-8', newline='\n')
    row = copy.deepcopy(by_id[f'design-brief.v{previous}'])
    row.update(template_id=f'design-brief.v{version}', path=path.relative_to(root).as_posix(),
               sha256='sha256:'+hashlib.sha256(text.encode()).hexdigest())
    new.append(row)
repair = '''Return exactly one bare JSON object satisfying DESIGN_BRIEF_SCHEMA. No Markdown.
You are correcting incomplete semantic extraction in a text2IFC Design Brief.
Original user request: {{USER_REQUEST}}
Frozen conversation: {{CONVERSATION}}
Initial Brief: {{PREVIOUS_BRIEF}}
Validation issues: {{VALIDATION_ISSUES}}
Complete target schema: {{DESIGN_BRIEF_SCHEMA}}

Only known_facts.semantic_requirements and known_facts.semantic_review may change.
Copy every other field exactly, including original_request, geometry, status,
identities, storeys, dimensions, locations, decisions and fact sources. Do not
redesign, rename, invent values, reclassify an acknowledged defect or ask the user
to repeat clear facts. Extract from user turns, never from a candidate IFC/JSON.
Review all five semantic categories, using exact user turn IDs. specified requires
matching canonical records; not_specified means no request, never failed extraction.
Place every explicit material/property/Type/element appearance/template requirement
in the canonical array with its exact stable target and scope. Enumerate all targets
of a requested group; preserve explicit negatives. Global theme defaults do not
authorize element overrides or physical materials. No performance value without
an explicit request. If this cannot be corrected within the two allowed fields,
retain the unresolved status in semantic_review; the deterministic boundary stops.
'''
repair_path = root/'prompts/agent/design-brief-semantic-repair-v1.0.md'
repair_path.write_text(repair, encoding='utf-8', newline='\n')
row = copy.deepcopy(by_id['design-brief.v2.4'])
row.update(template_id='design-brief-semantic-repair.v1.0', mode='semantic_repair',
           path=repair_path.relative_to(root).as_posix(), sha256='sha256:'+hashlib.sha256(repair.encode()).hexdigest(),
           required_inputs=['USER_REQUEST','CONVERSATION','PREVIOUS_BRIEF','VALIDATION_ISSUES','DESIGN_BRIEF_SCHEMA'])
new.append(row)
suffix = '\n  ]\n}'
assert registry_text.rstrip().endswith(suffix)
prefix = registry_text.rstrip()[:-len(suffix)]
registry_path.write_text(prefix + ',\n' + ',\n'.join('    '+json.dumps(r, ensure_ascii=False, indent=2).replace('\n','\n    ') for r in new) + suffix+'\n', encoding='utf-8', newline='\n')
