import json
import subprocess
from pathlib import Path

path = Path('prompts/agent/registry.json')
current = json.loads(path.read_text(encoding='utf-8'))
baseline = subprocess.check_output(['git', 'show', 'HEAD:prompts/agent/registry.json']).decode('utf-8')
old = json.loads(baseline)
new_ids = {'audit.v3', 'design-brief.v2.4'}
entries = [v for v in current['templates'] if v['template_id'] in new_ids]
unchanged = {**current, 'templates': [v for v in current['templates'] if v['template_id'] not in new_ids]}
assert unchanged == old  # Preserve all pre-existing registry values.
assert len(entries) == 2
tail = '\n  ]\n}'
assert baseline.rstrip().endswith(tail)
prefix = baseline.rstrip()[:-len(tail)]
addition = ',\n' + ',\n'.join('\n'.join('    ' + line for line in json.dumps(v, ensure_ascii=False, indent=2).splitlines()) for v in entries)
path.write_text(prefix + addition + tail + '\n', encoding='utf-8', newline='\n')
