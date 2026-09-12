import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit

root = Path(__file__).resolve().parents[1]
base = root / 'dataset/processed/ifc-presentation-validation/live-semantic-20260908-01'
record = {'recorded_at': dt.datetime.now(dt.timezone.utc).isoformat(),
          'status': 'blocked_before_transport', 'network_transport_attempted': False,
          'reason': 'Automatic approval review requires explicit authorization for this Audit payload to api.deepseek.com.',
          'previous_block': 'audit-blocked.json', 'payload_preview': 'audit-payload-preview/audit/prompt-rendered.md',
          'provider': 'DeepSeek', 'host': 'api.deepseek.com', 'model': 'deepseek-v4-flash',
          'user_confirmation': 'requested_pending', 'note': 'No Audit response exists. All prior attempts remain preserved.'}
with (base / 'generation/audit-approval-blocked-02.json').open('x', encoding='utf-8') as f:
    json.dump(record, f, ensure_ascii=False, indent=2)

changes = {
    base / 'REPORT.md': [('真实 Audit 因审批额度未执行', '真实 Audit 被自动审批阻断，待具体载荷授权'),
                        ('后续：审批额度恢复后，', '后续：具体 Audit 载荷授权并通过自动审批后，')],
    base / 'generation/REPORT.md': [('真实 Audit 请求被自动审批额度阻断，尚未发出；详见 [阻断记录](audit-blocked.json)。',
        '真实 Audit 尚未发出：此前审批额度阻断已保留；最近自动审批要求明确授权具体载荷发送到 api.deepseek.com，详见 [当前阻断记录](audit-approval-blocked-02.json) 与 [本地载荷预览](audit-payload-preview/audit/prompt-rendered.md)。')],
    root / 'docs/architecture/semantic-appearance-plan.md': [('真实 Audit 因自动审批额度阻断，未发出；',
        '真实 Audit 尚未发出：此前审批额度阻断，最近自动审批又要求对具体载荷发往 DeepSeek 明确授权；')]
}
for path, replacements in changes.items():
    value = path.read_text(encoding='utf-8')
    for old, new in replacements:
        assert old in value, (path, old)
        value = value.replace(old, new)
    path.write_text(value, encoding='utf-8')

plan = root / 'docs/architecture/semantic-appearance-plan.md'
with plan.open('a', encoding='utf-8') as f:
    f.write('\n交付位置说明：本批真实运行及待人工检查材料仍保存在上述本地展示目录，尚未纳入 Git 或发布为 Proof；本轮只提交通用代码、测试和离线查看器。查看器可用 `.venv\\Scripts\\python.exe scripts/presentation/render_ifc_review.py <input.ifc> <新的输出.html>` 生成，已有输出拒绝覆盖。\n')

pending = json.loads((base / 'pending-review.json').read_text(encoding='utf-8'))
for name, digest in pending['artifacts_sha256'].items():
    assert hashlib.sha256((base / name).read_bytes()).hexdigest() == digest, name

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []
    def handle_starttag(self, tag, attrs):
        self.urls.extend(v for k, v in attrs if k in {'href', 'src'} and v)

checked = []
for name in ['REPORT.md', 'generation/REPORT.md', 'repair/REPORT.md', 'index.html']:
    path = base / name
    text = path.read_text(encoding='utf-8')
    if path.suffix == '.md':
        urls = re.findall(r'\]\(([^)]+)\)', text)
    else:
        parser = Links()
        parser.feed(text)
        urls = parser.urls
    for url in urls:
        parts = urlsplit(url)
        if parts.scheme or not parts.path:
            continue
        target = (path.parent / unquote(parts.path)).resolve()
        assert target.exists(), (name, url)
        checked.append([name, url])
summary = {'status': 'passed', 'immutable_artifact_hashes_checked': len(pending['artifacts_sha256']),
           'human_links_checked': len(checked), 'accepted_proof_installed': False,
           'scope': 'Human entry paths and frozen IFC/request/evaluation hashes; not curator or full preflight.'}
with (base / 'review-evidence/handoff-check.json').open('x', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
print(json.dumps(summary))
