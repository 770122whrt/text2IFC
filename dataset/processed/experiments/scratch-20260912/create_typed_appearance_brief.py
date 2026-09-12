import copy
import hashlib
import json
from pathlib import Path

from text2ifc_agent.semantic_requirements import element_appearance_schema

root = Path.cwd()
schema = json.loads((root/'schemas/agent/design-brief/2.2/schema.json').read_text(encoding='utf-8'))
schema['$id'] = schema['$id'].replace('/2.2/', '/2.3/')
schema['title'] = 'text2IFC Typed Appearance Design Brief 2.3'
schema['properties']['schema_version']['const'] = 'text2ifc/design-brief/2.3'
schema['properties']['known_facts']['properties']['semantic_requirements']['items']['properties']['appearance'] = copy.deepcopy(element_appearance_schema())
path = root/'schemas/agent/design-brief/2.3/schema.json'
path.parent.mkdir(exist_ok=False)
path.write_text(json.dumps(schema,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
registry_path = root/'prompts/agent/registry.json'
registry_text = registry_path.read_text(encoding='utf-8')
by_id = {r['template_id']:r for r in json.loads(registry_text)['templates']}
addition = '''

Executable appearance grammar and scope (Design Brief 2.3)

semantic_requirements[].appearance is ONLY a whole-element numerical override:
color is an RGB array of three numbers in [0,1]; transparency is a number in [0,1].
The object must not be empty and cannot contain profile, frame_color, frame_profile,
glazing_transparency, colour words, or other component descriptions. Follow the
actual Schema exactly. These fields are executable requirements, not free text.

Keep the overall theme in known_facts.appearance.profile and preserve qualitative
style cues in its style_notes. Basic filling templates already provide distinct
frame/glazing/leaf styles. A request for dark thin frames and transparent glazing
compatible with the selected theme belongs to those template/theme choices; it
does NOT authorize one RGB or transparency override for the whole window/door.
Do not invent exact RGB/opacity numbers from qualitative style cues or ask about
already approved theme/template defaults. Keep physical material requirements
separate. Never clear a material because an appearance description is unsupported.

semantic_review.appearance specifically reviews whole-element numeric overrides.
With only an overall theme/default part-style request, use not_specified for this
category and keep the part-style description and explicit templates separately.
specified requires a legal, explicitly requested whole-element override in the
canonical array. If a genuinely explicit part-level customization cannot be
represented by the supported theme/template contract, preserve its text and use
the normal clarification/unsupported route instead of flattening component styles.
'''
new = []
for previous,version in [('2.5','2.7'),('2.6','2.8')]:
    content = (root/f'prompts/agent/design-brief-v{previous}.md').read_text(encoding='utf-8')
    content = content.replace('Design Brief 2.2','Design Brief 2.3').replace('design-brief/2.2','design-brief/2.3') + addition
    path = root/f'prompts/agent/design-brief-v{version}.md'
    path.write_text(content,encoding='utf-8',newline='\n')
    row = copy.deepcopy(by_id[f'design-brief.v{previous}'])
    row.update(template_id=f'design-brief.v{version}', path=path.relative_to(root).as_posix(),
               sha256='sha256:'+hashlib.sha256(content.encode()).hexdigest())
    new.append(row)
content = (root/'prompts/agent/design-brief-semantic-repair-v1.0.md').read_text(encoding='utf-8')
content += addition + '\nExecutable whole-element appearance schema: {{ELEMENT_APPEARANCE_SCHEMA}}\n'
path = root/'prompts/agent/design-brief-semantic-repair-v1.1.md'
path.write_text(content,encoding='utf-8',newline='\n')
row = copy.deepcopy(by_id['design-brief-semantic-repair.v1.0'])
row.update(template_id='design-brief-semantic-repair.v1.1', path=path.relative_to(root).as_posix(),
           sha256='sha256:'+hashlib.sha256(content.encode()).hexdigest())
row['required_inputs'].append('ELEMENT_APPEARANCE_SCHEMA')
new.append(row)
suffix = '\n  ]\n}'
assert registry_text.rstrip().endswith(suffix)
registry_path.write_text(registry_text.rstrip()[:-len(suffix)]+',\n'+',\n'.join(
    '    '+json.dumps(r,ensure_ascii=False,indent=2).replace('\n','\n    ') for r in new)+suffix+'\n',encoding='utf-8',newline='\n')
