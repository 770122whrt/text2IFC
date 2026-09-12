"""Add pending human views using the existing package contract; no registration."""
import hashlib
import html
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
from markdown_it import MarkdownIt
from scripts.proof.package import SCHEMA, capture_bundle, digest, validate_package

SOURCE = ROOT / 'dataset/processed/ifc-presentation-validation/live-semantic-20260908-01'
PROOF = ROOT / 'dataset/processed/proof'
NAME = 'semantic-appearance-20260908'
COLLECTIONS = {'generation': PROOF / 'generation/phase6.6' / NAME,
               'repair': PROOF / 'repair/phase12.1' / NAME}
IDS = {'generation': 'reception-basic-fillings', 'repair': 'vvo-instance-properties'}
for directory in COLLECTIONS.values():
    assert not directory.exists(), directory
nav = [PROOF / n for n in ['README.md', 'PROOF-INVENTORY.json', 'generation/README.md', 'repair/README.md']]
nav_hashes = {p: digest(p) for p in nav}
md = MarkdownIt('commonmark').enable('table')
STYLE = '<style>body{max-width:1100px;margin:32px auto;padding:0 24px;background:#f5f5f0;color:#293b32;font:16px/1.7 system-ui}a{color:#266345}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:white;padding:20px;border:1px solid #d6dfd6;border-radius:8px}table{border-collapse:collapse;width:100%;background:white}td,th{border:1px solid #d6dfd6;padding:10px;text-align:left}img{max-width:100%}.notice{background:#fff3cd;padding:14px}code{overflow-wrap:anywhere}</style>'
def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as f:
        f.write(text)
def dump(path, value):
    write(path, json.dumps(value, ensure_ascii=False, indent=2) + '\n')
def rel(target, parent):
    return Path(os.path.relpath(target, parent)).as_posix()
def page(title, body):
    return '<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>' + html.escape(title) + '</title>' + STYLE + body + '</html>'

summaries = {}
for workflow, collection in COLLECTIONS.items():
    collection.mkdir(parents=True)
    source = SOURCE / workflow
    identity = IDS[workflow]
    case = collection / identity
    roots = (['request.txt', 'generated.ifc'] if workflow == 'generation'
             else ['request.txt', '01-original.ifc', '02-damaged.ifc', '03-repaired.ifc'])
    mapping = {p.relative_to(source).as_posix(): f'{identity}/evidence/frozen/{p.relative_to(source).as_posix()}'
               for p in source.rglob('*') if p.is_file()}
    for name in roots:
        mapping[name] = f'{identity}/{name}'
    mapping['REPORT.md'] = f'{identity}/evidence/prior-REPORT.md'
    if workflow == 'generation':
        mapping['corrective-02-general-revalidation/generator/candidate.json'] = f'{identity}/model.json'
        mapping['review-final.html'] = f'{identity}/review.html'
        visual = ['overall.png', 'window-double.png', 'window-single.png', 'door.png']
    else:
        for name in ['review-original.html', 'review-damaged.html', 'review-repaired.html']:
            mapping[name] = f'{identity}/{name}'
        visual = ['overall-depth.png']
    for name in visual:
        mapping[name] = f'{identity}/evidence/views/{name}'
    bundle = capture_bundle(source, collection, 'frozen', mapping)
    bundle['old_root'] = source.relative_to(ROOT).as_posix()
    bundles = [bundle]
    if workflow == 'generation':
        for name in ['admission', 'review-evidence']:
            common = capture_bundle(SOURCE / name, collection, name)
            common['old_root'] = (SOURCE / name).relative_to(ROOT).as_posix()
            bundles.append(common)

    frozen_request = (case / 'request.txt').read_text(encoding='utf-8')
    write(case / 'request.html', page('text2IFC · 中文请求',
          '<h1>实际用户请求</h1><p class="notice">待人工检查，尚未登记。以下正文按 UTF-8 显示，原始 request.txt 字节不变。</p>'
          '<p><a href="REPORT.html">返回案例报告</a> · <a href="request.txt" download>下载原始请求</a></p><pre>'
          + html.escape(frozen_request) + '</pre>'))

    original_report = (source / 'REPORT.md').read_text(encoding='utf-8')
    def rebind(match):
        url = match.group(1)
        parsed = urlsplit(url)
        if parsed.scheme or not parsed.path:
            return match.group(0)
        key = unquote(parsed.path)
        assert key in mapping, (workflow, key)
        target = case / 'request.html' if key == 'request.txt' else collection / mapping[key]
        return '](' + rel(target, case) + ('#' + parsed.fragment if parsed.fragment else '') + ')'
    report = re.sub(r'\]\(([^)]+)\)', rebind, original_report)
    report = report.replace('才能安装到 processed/proof', '才能登记为 accepted Proof')
    report = report.replace('本页不是 accepted 标记。', '本页已按既有格式收纳到 Proof 目录，但尚未登记。')
    report = report.replace('实際', '实际')
    report = report.replace('尚未安装 accepted Proof', '尚未登记为 accepted Proof')
    report = report.replace('\n\n', '\n\n> **pending_human_review · 未登记**。仅供人工检查，不更新总索引、accepted 名单或阶段结论。\n\n', 1)
    report += '\n## 中文请求全文\n\n' + frozen_request + '\n\n[完整证据导航](evidence/README.md) · [案例文件绑定](FILES.json)\n'
    write(case / 'REPORT.md', report)
    write(case / 'REPORT.html', page('text2IFC · ' + workflow + ' 检查报告', md.render(report)))

    if workflow == 'generation':
        authority_key = 'corrective-02-general-revalidation/acceptance-metrics.json'
        important = ['corrective-02-general-revalidation/execution.json', authority_key,
                     'final-independent-review.json', 'final-view-equivalence.json',
                     'corrective-02-general-revalidation/audit/audit-report.json']
        artifacts_names = roots + ['model.json']
    else:
        authority_key = 'result-live-04.json'
        important = ['execution-live-04.json', authority_key, 'independent-review.json', 'public-input-facts.json']
        artifacts_names = roots
    evidence = '# 机器证据导航\n\n状态：pending_human_review，未登记。源运行保留不动；本包逐字节复制并以 review-manifest.json 的 legacy_bundles 记录旧路径映射。这里包含真实成功和失败尝试，旧报告路径属于历史上下文。\n\n'
    evidence += '\n'.join('- [' + n + '](' + rel(collection / mapping[n], case / 'evidence') + ')' for n in important)
    common_root = COLLECTIONS['generation'] / 'evidence'
    evidence += '\n\n- [真实调用总清单](' + rel(common_root / 'review-evidence/actual-provider-attempts.json', case / 'evidence') + ')\n'
    evidence += '- [完整阶段／聚焦离线测试](' + rel(common_root / 'admission', case / 'evidence') + ')\n'
    evidence += '\n原运行：`' + source.relative_to(ROOT).as_posix() + '`。原始／私有评估材料仅供运行后核对，不能成为 Provider 输入。本次整理无 Provider 调用、无重新生成、无 accepted curator。\n'
    write(case / 'evidence/README.md', evidence)

    artifacts = {n: {'sha256': digest(case / n), 'size_bytes': (case / n).stat().st_size,
                      'source': f'{identity}/{n}'} for n in artifacts_names}
    case_record = {'case_id': identity, 'path': identity, 'status': 'pending_human_review',
                   'outcome': 'generated' if workflow == 'generation' else 'repaired',
                   'evidence_mode': 'live', 'provider_calls': 5 if workflow == 'generation' else 2,
                   'total_provider_calls_including_failed_attempts': 5 if workflow == 'generation' else 4,
                   'authority': mapping[authority_key], 'artifacts': artifacts,
                   'ifccompare': 'Independent frozen request / IFC readback; full IFCCompare benchmark not run'}
    if workflow == 'repair':
        case_record['original_role'] = 'private_ground_truth'
    manifest = {'schema_version': SCHEMA, 'collection_id': NAME, 'workflow': workflow,
                'status': 'pending_human_review', 'registration_status': 'unregistered',
                'accepted_proof_installed': False, 'phase_assignment': 'Organization only; phase status unchanged',
                'cases': [case_record], 'legacy_bundles': bundles}
    dump(collection / 'review-manifest.json', manifest)
    dump(case / 'FILES.json', {'schema_version': 'text2ifc/package-artifacts/0.1', 'artifacts': artifacts})
    sibling = COLLECTIONS['repair' if workflow == 'generation' else 'generation']
    readme = '# text2IFC ' + workflow + ' · 待人工检查\n\n**pending_human_review / 未登记**。本批采用既有 Proof 格式；仅有独立 review-manifest.json，不创建主 manifest.json，不更新总索引。\n\n'
    readme += '- [中文案例报告](' + identity + '/REPORT.md) · [浏览器报告](' + identity + '/REPORT.html)\n'
    readme += '- [中文请求](' + identity + '/request.html) · [原始请求文件](' + identity + '/request.txt)\n'
    readme += '- [另一条链路](' + rel(sibling / 'index.html', collection) + ')\n\n人工确认后再执行适用 accepted 检查并登记；本次人读校验不冒充 curator 或能力评估。\n'
    write(collection / 'README.md', readme)
    write(collection / 'REPORT.md', readme + '\n本次仅整理已完成运行。代码、测试和模型结论见案例报告；原始证据与先前失败尝试全部保留。\n')
    request_link = f'{identity}/request.html'
    display = '<h1>text2IFC · ' + workflow + ' 人工检查</h1><p class="notice">待人工检查 · 未登记。人工确认后才进入 accepted 流程。</p>'
    display += '<p><a href="' + request_link + '">中文请求</a> · <a href="' + identity + '/REPORT.html">完整中文报告</a> · <a href="' + rel(sibling / 'index.html', collection) + '">另一条链路</a></p>'
    if workflow == 'generation':
        display += f'<p><a href="{identity}/generated.ifc">完整 IFC</a> · <a href="{identity}/model.json">实际候选 JSON</a> · <a href="{identity}/review.html">三维与属性</a></p>'
    else:
        display += '<p>' + ' · '.join(f'<a href="{identity}/{n}">{label}</a>' for n, label in [('01-original.ifc','原始 IFC'),('02-damaged.ifc','损坏 IFC'),('03-repaired.ifc','修复 IFC')]) + '</p>'
        display += '<p>' + ' · '.join(f'<a href="{identity}/review-{n}.html#2CsmzAChHF6O6maGXlo6PS">{label}目标属性</a>' for n, label in [('original','原始'),('damaged','损坏'),('repaired','修复')]) + '</p>'
    display += '<img alt="实际 IFC 网格整体视图" src="' + identity + '/evidence/views/' + visual[0] + '">'
    display += '<h2>请求正文</h2><pre>' + html.escape(frozen_request) + '</pre>'
    write(collection / 'index.html', page('text2IFC · 待人工检查', display))
    result = validate_package(collection, manifest, reopen=True)
    assert result['status'] == 'passed', result
    dump(collection / 'review-validation.json', result)
    summaries[workflow] = {**result, 'root': str(collection), 'captured_files': sum(len(b['entries']) for b in bundles)}

assert all(digest(p) == sha for p, sha in nav_hashes.items()), 'Main inventory/navigation changed'
assert all(not (p / 'manifest.json').exists() for p in COLLECTIONS.values())
print(json.dumps(summaries, ensure_ascii=False))
