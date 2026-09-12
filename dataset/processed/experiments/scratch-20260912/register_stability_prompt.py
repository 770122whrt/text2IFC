import copy
import json
from pathlib import Path
from text2ifc_agent.prompt_registry import _template_sha256

root = Path(__file__).resolve().parents[1]
target = root/'prompts/agent/bim-json-changeset-v1.3.md'
target.write_text((root/'prompts/agent/bim-json-changeset-v1.2.md').read_text(encoding='utf-8') + '''

## 有界早期字段恢复合同 1.0

本次必须一次修完 ISSUES 中全部错误；任何残留非法字段都会使整个事务回滚。
只编辑 CHANGE_SCOPE.allowed_paths 指定的字段。字段改名可以用 update_entity
的 changes["/attributes"] 提交保留其他字段的完整 attributes 对象；机器仍逐叶检查
实际变更，只授权旧字段和唯一合法新字段。改名必须保留原始值，禁止改成其他数值。
禁止 add/remove 构件或关系；不得改名或改写无关对象。提供合法枚举不代表授权猜测
用户材料、性能或 Type 请求。无法保持明确要求时返回 Draft。

## 只读语义依赖

下面包含共享 Type 及其他实例，仅用于判断影响范围，不授予写权限：
{{READ_ONLY_COMPONENTS}}
''', encoding='utf-8')
path = root/'prompts/agent/registry.json'
raw = path.read_text(encoding='utf-8')
data = json.loads(raw)
entries = data['templates'] if isinstance(data, dict) else data
entry = copy.deepcopy(next(e for e in entries if e['template_id']=='bim-json-changeset.v1.2'))
entry['template_id'] = 'bim-json-changeset.v1.3'
entry['path'] = 'prompts/agent/bim-json-changeset-v1.3.md'
entry['sha256'] = _template_sha256(target)
entry['required_inputs'].append('READ_ONLY_COMPONENTS')
# Preserve every registered entry and its formatting.
position = raw.rfind(']')
raw = raw[:position].rstrip() + ',\n' + json.dumps(entry, ensure_ascii=False, indent=2) + '\n' + raw[position:]
path.write_text(raw, encoding='utf-8')
