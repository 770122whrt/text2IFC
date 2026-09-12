import copy
import json
from pathlib import Path
from text2ifc_agent.prompt_registry import _template_sha256
root = Path(__file__).resolve().parents[1]
target = root/'prompts/agent/bim-json-changeset-v1.4.md'
target.write_text((root/'prompts/agent/bim-json-changeset-v1.2.md').read_text(encoding='utf-8') + '''

## 只读依赖与当前任务上下文

FEW_SHOTS 与 IFC_AUTHORING_CONTRACT 已按当前包或修复范围选择。原始请求和冻结
EXPECTED_FACTS 保持完整，不能把示例值当作请求。以下依赖仅提供坐标、宿主和共享
Type 的影响范围，不增加 CHANGE_SCOPE 中的写权限：
{{READ_ONLY_COMPONENTS}}
''', encoding='utf-8')
path = root/'prompts/agent/registry.json'
raw = path.read_text(encoding='utf-8')
data = json.loads(raw)
entry = copy.deepcopy(next(e for e in data['templates'] if e['template_id']=='bim-json-changeset.v1.2'))
entry.update(template_id='bim-json-changeset.v1.4', path='prompts/agent/bim-json-changeset-v1.4.md', sha256=_template_sha256(target))
entry['required_inputs'].append('READ_ONLY_COMPONENTS')
position = raw.rfind(']')
formatted = '\n'.join('    ' + line for line in json.dumps(entry, ensure_ascii=False, indent=2).splitlines())
path.write_text(raw[:position].rstrip() + ',\n' + formatted + '\n  ' + raw[position:], encoding='utf-8')
