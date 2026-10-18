"""Stage, independently check, archive and update an active damage pilot in place.

No Provider calls. This command accepts an ignored experimental dataset only;
registered Proof is not an update target. All old bytes are archived before any
installation. Unchanged damaged IFC/native/mesh receipts are reused by hash.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import contextlib
import copy
import csv
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'src'), str(ROOT / '.deps/python312')]

import ifcopenshell

from scripts.ifc_repair.dataset_batch.engine import apply_recipe, seal_case, verify_seal, write_json
from scripts.ifc_repair.dataset_batch.pilot import _preserved_meshes
from scripts.ifc_repair.dataset_batch.prompt_check_v3 import audit_prompt
from scripts.ifc_repair.dataset_batch.prompts_v3 import PROFILE, prepare_inventory, prepare_recipe, render_prompts
from scripts.ifc_repair.dataset_batch.validation import program_hash, sha256
from scripts.ifc_repair.dataset_batch.wall_check import check_wall_closure

REPLACED_SOURCE = 'formal-007'
REPLACED_CASE = 'case-003-a01'
OLD_DOOR = '1UDFRzXYL0uenoP45X20Ib'
NEW_DOOR = '2EvxrJh$nBCOf6drB7QwTZ'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def require(value, code):
    if not value:
        raise ValueError(code)


def _refresh_recipe(inv, old, replacement=False):
    result = copy.deepcopy(old)
    targets = {t['guid']: t for rows in inv['targets'].values() for t in rows}
    deletions = []
    for target in old['deletions']:
        guid = NEW_DOOR if replacement and target['guid'] == OLD_DOOR else target['guid']
        require(guid in targets, 'CURRENT_TARGET_NOT_ADMITTED:' + guid)
        deletions.append({**copy.deepcopy(targets[guid]), 'preserve_opening': target.get('preserve_opening', True)})
    changes = []
    for change in old['property_changes']:
        matches = [p for p in inv['properties'] if (p['guid'], p['pset_name'], p['property_name']) == (change['guid'], change['pset_name'], change['property_name'])]
        require(len(matches) == 1, 'PROPERTY_NOT_ADMITTED')
        changes.append({**copy.deepcopy(matches[0]), 'after': change['after']})
    result.update(deletions=deletions, property_changes=changes)
    return prepare_recipe(result)


def update_source(original_root, staged_root, source_result):
    original_root, staged_root = Path(original_root), Path(staged_root)
    sid = source_result['source_id']
    old_source, source = original_root / 'sources' / sid, staged_root / 'sources' / sid
    reference = old_source / 'private/reference.ifc'
    source_hash = sha256(reference)
    require(source_hash == source_result['source_sha256'], 'REFERENCE_HASH_CHANGED')
    input_path = ROOT / source_result['source']['input_path']
    require(sha256(input_path) == source_hash, 'MOTHER_SOURCE_HASH_CHANGED')
    log_path = staged_root / 'private/update-logs' / (sid + '.log')
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open('w', encoding='utf-8') as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        inv = prepare_inventory(reference, read(old_source / 'private/inventory.json'))
        write_json(source / 'private/inventory.json', inv)
        original = ifcopenshell.open(str(reference))
        rows, details, updated_plans = [], [], []
        for old_row in source_result['cases']:
            case_id, relative = old_row['case_id'], old_row['path']
            old_case, case = original_root / relative, staged_root / relative
            require(verify_seal(old_case), 'OLD_CASE_SEAL_INVALID:' + relative)
            old_model_hash = sha256(old_case / 'public/model.ifc')
            old_manifest, old_case_json = read(old_case / 'private/mutation.json'), read(old_case / 'case.json')
            replacement = sid == REPLACED_SOURCE and case_id == REPLACED_CASE
            recipe = _refresh_recipe(inv, read(old_case / 'private/recipe.json'), replacement)
            updated_plans.append({'case_id': case_id, 'family': recipe['family'], 'severity': recipe['severity'],
                                  'deletions': [{'class_family': t['ifc_class'][3:].lower(), 'private_target_guid': t['guid'], 'preserve_opening': t.get('preserve_opening', True)} for t in recipe['deletions']],
                                  'property_change': {k: recipe['property_changes'][0][k] for k in ('guid','pset_name','property_name')} if recipe['property_changes'] else None})
            if replacement:
                building = staged_root / 'private/rebuilt' / sid / case_id
                result = apply_recipe(reference, recipe, building, inventory=inv, prompt_profile=PROFILE)
                require(result['status'] == 'passed', 'REPLACEMENT_GENERATION_FAILED')
                for path in building.rglob('*'):
                    if path.is_file():
                        dest = case / path.relative_to(building)
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copyfile(path, dest)
                manifest = read(case / 'private/mutation.json')
            else:
                result = copy.deepcopy(old_case_json)
                manifest = {**copy.deepcopy(old_manifest), 'schema_version': 'text2ifc/ifc-repair-dataset-mutation/1.3',
                            'prompt_profile': PROFILE, 'deletions': recipe['deletions'], 'property_changes': recipe['property_changes']}
                write_json(case / 'private/recipe.json', recipe)
                write_json(case / 'private/mutation.json', manifest)
            prompts = render_prompts(manifest)
            require(prompts['world'] is not None, 'WORLD_REQUEST_UNAVAILABLE:' + relative)
            for mode, text in prompts.items():
                path = case / f'public/request-{mode}.txt'
                if text is not None:
                    path.write_text(text, encoding='utf-8')
                elif path.exists():
                    historic = case / f'private/previous-public/request-{mode}.txt'
                    historic.parent.mkdir(parents=True, exist_ok=True)
                    os.replace(path, historic)
            damaged = ifcopenshell.open(str(case / 'public/model.ifc'))
            checks = {mode: audit_prompt(original, damaged, manifest, mode, (case / f'public/request-{mode}.txt').read_text(encoding='utf-8')) for mode, text in prompts.items() if text is not None}
            write_json(case / 'private/prompt-check.json', checks)
            require(all(c['passed'] for c in checks.values()), 'PUBLIC_INFORMATION_FAILED:' + relative + ':' + json.dumps({m: c.get('errors') for m, c in checks.items() if not c['passed']}, ensure_ascii=False))
            if replacement:
                write_json(case / 'private/wall-check.json', check_wall_closure(reference, case / 'public/model.ifc', manifest))
                write_json(case / 'private/mesh-check.json', _preserved_meshes(original, damaged, manifest))
            native, preservation = read(case / 'private/validation.json'), read(case / 'private/preservation.json')
            walls, meshes = read(case / 'private/wall-check.json'), read(case / 'private/mesh-check.json')
            require(native['passed'] and native['finding_count'] == 0 and preservation['passed'] and walls['passed'] and meshes['passed'], 'DATASET_GATES_FAILED:' + relative)
            primary = old_case_json['primary_prompt'] if prompts.get(old_case_json['primary_prompt']) is not None else 'world'
            (case / 'public/request.txt').write_text(prompts[primary], encoding='utf-8')
            model_hash = sha256(case / 'public/model.ifc')
            require(replacement or model_hash == old_model_hash, 'UNREQUESTED_IFC_CHANGE:' + relative)
            detail = {'source_id': sid, 'case_id': case_id, 'replaced_door': replacement,
                      'previous_ifc_sha256': old_model_hash, 'current_ifc_sha256': model_hash,
                      'ifc_bytes_unchanged': model_hash == old_model_hash,
                      'request_profile': PROFILE, 'previous_profile': old_manifest['prompt_profile'],
                      'native_preservation_wall_mesh_receipts': 'fresh for rebuilt IFC' if replacement else 'reused from verified old seal; exact IFC/source bytes unchanged',
                      'old_receipt_sha256': {p: sha256(old_case / p) for p in ('private/validation.json', 'private/preservation.json', 'private/wall-check.json', 'private/mesh-check.json')},
                      'shape_reference_count': sum(t['geometry']['request_shape']['method'] == 'surviving_instance' for t in manifest['deletions']),
                      'basic_box_count': sum(t['geometry']['request_shape']['method'] == 'basic_box' for t in manifest['deletions']),
                      'request_chars_before': len((old_case / 'public/request.txt').read_text(encoding='utf-8')),
                      'request_chars_after': len(prompts[primary]), 'passed': True}
            if replacement:
                detail['target_change'] = {'old_door_guid_private': OLD_DOOR, 'new_door_guid_private': NEW_DOOR,
                                           'window_guid_unchanged_private': [t['guid'] for t in recipe['deletions'] if t['ifc_class'] == 'IfcWindow']}
            write_json(case / 'private/update.json', detail)
            result.update(schema_version='text2ifc/ifc-repair-dataset-case/1.1', request_profile=PROFILE,
                          status='passed', machine_validated=True, human_reviewed=False, primary_prompt=primary,
                          information_sufficient=True, wall_check_passed=True, wall_check_applicable=walls['applicable'],
                          independent_mesh_check_passed=True,
                          prompt_templates={mode: {'applicable': text is not None, 'reason': None if text is not None else 'no unique wall/name/reference locator', 'sha256': sha256(case / f'public/request-{mode}.txt') if text is not None else None} for mode, text in prompts.items()},
                          additional_evidence=['public/request.txt', 'private/prompt-check.json', 'private/wall-check.json', 'private/mesh-check.json', 'private/update.json'])
            write_json(case / 'case.json', result)
            seal_case(case)
            require(verify_seal(case), 'NEW_CASE_SEAL_INVALID')
            row = {**copy.deepcopy(old_row), 'primary_prompt': primary, 'prompt_modes': list(checks), 'prompt_checks_passed': True, 'errors': []}
            rows.append(row)
            details.append(detail)
        require(sha256(reference) == sha256(input_path) == source_hash, 'SOURCE_CHANGED_DURING_UPDATE')
        updated_spec = {**copy.deepcopy(source_result['source']), 'request_profile': PROFILE, 'pilot_cases': updated_plans}
        write_json(source / 'private/update-plan.json', {'request_profile': PROFILE, 'cases': updated_plans, 'previous_plan_role': 'original 1.2 generation history, archived before update'})
        updated = {**copy.deepcopy(source_result), 'source': updated_spec, 'cases': rows, 'attempts': rows, 'request_profile': PROFILE, 'source_unchanged': True}
        write_json(source / 'result.json', updated)
    return updated, details


def write_report(root, summary, details):
    cases = [c for s in summary['sources'] for c in s['cases']]
    totals = Counter({k: sum(c['deleted_counts'][k] for c in cases) for k in ('door','window','beam','column')})
    lines = [f'# {len(cases)} 题损伤数据集审核报告', '',
             f"本次已在原集合更新为请求版本 1.3：{len(summary['sources'])} 个母 IFC、{len(cases)} 对 Prompt 与损伤 IFC，均通过本轮公开文本交叉检查。{summary['update']['ifc_bytes_unchanged_cases']} 份损伤 IFC 字节不变。" + ('formal-007/case-003-a01 换掉无同形存活实例的复杂门，原窗保留。' if summary['update']['rebuilt_cases'] else ''), '',
             '所有请求由脚本生成。墙名定位只用楼层、墙名、大体方位和相对距离；世界定位只用楼层、墙的几何范围及基点坐标。公开数值最多三位小数。优先复制损伤模型中可唯一定位的完整同形参照，朝向相同时不重复列轴和外包盒。', '',
             f"{sum(totals.values())} 个删除对象中，{summary['shape_reference_targets']} 个使用完整同形参照；{summary['basic_box_targets']} 个使用经过完整网格核对的单一长方体描述。当前 20 题集合的基本形状为 formal-003/case-003-a01 的梁。复杂形状没有合格参照时拒绝，两个无类型映射反例仍排除。门窗形状、洞口形状及相对安装关系分别核对，未把门窗外包盒当作洞口。", '',
             f"门 / 窗 / 梁 / 柱删除数量为 {' / '.join(str(totals[k]) for k in ('door','window','beam','column'))}，另有 {sum(c['property_changes'] for c in cases)} 次实例属性修改。共核对 {summary['removed_openings_checked']} 个移除洞口的墙体补全、{summary['preserved_openings_checked']} 个保留洞口；已删洞口的检查区域恢复为墙体。主请求分布：{summary['primary_prompt_counts']}；适用变体：{summary['prompt_counts']}（变体不另算题数）。", '',
             f"IfcOpenShell {ifcopenshell.version} 的 IFC2X3 schema＋EXPRESS 校验 {len(cases)}/{len(cases)} 为零 findings。换门题重新运行原生校验、损伤保全、墙体与保留网格检查；字节不变的题目复用原封存中的同源、同 IFC 字节检查记录。实际公开请求均重新检查并封存。全部母本与私有参考 SHA-256 均不变。", '',
             '信息检查先仅用实际公开文本和损伤 IFC 解析楼层、墙、参照、位置、朝向、完整形状、洞口 void/fill 和实例属性，之后才对照私有参考；公开阶段不读取隐藏几何参数来补答案。世界坐标保留三位小数对应每轴最多约 0.5 毫米的舍入，墙相对距离保留三位毫米小数对应约 0.0005 毫米，旋转角的舍入误差另行传播核对。完整参照的局部三角形仍按微米量级规范化比较。', '',
             '这些结果支持任务信息和损伤文件的机器检查，不代表 Harness 或真实模型已自动解答这 20 题。Provider 调用 0 次；全部派生题仍为人工待审。墙体补全使用独立对照网格、体积及有限内部点，保留构件网格为每题最多三个构件的抽查。', '',
             '## 逐题审核入口', '',
             '|母本 / 题目|损伤内容|门/窗/梁/柱|属性|定位|文件与检查|',
             '|---|---|---|---|---|---|---|']
    family_names = {'door': '门', 'window': '窗', 'door_window': '门＋窗', 'beam': '梁', 'column': '柱', 'beam_column': '梁＋柱', 'door_window_beam_column': '门窗梁柱', 'attribute': '属性'}
    for c in cases:
        p = c['path']
        counts = ' / '.join(str(c['deleted_counts'][k]) for k in ('door', 'window', 'beam', 'column'))
        links = f"[请求]({p}/public/request.txt) · [IFC]({p}/public/model.ifc) · [信息检查]({p}/private/prompt-check.json) · [墙体检查]({p}/private/wall-check.json)"
        lines.append(f"|{c['source_id']}/{c['case_id']}|{family_names.get(c['family'], c['family'])}|{counts}|{c['property_changes']}|{'墙名' if c['primary_prompt'] == 'host_wall' else '世界坐标'}|{links}|")
    lines += ['', '## 请求抽样', '']
    for sid, cid in (('formal-001', 'case-001-a01'), ('formal-007', 'case-003-a01'), ('formal-003', 'case-003-a01')):
        c = next((c for c in cases if c['source_id'] == sid and c['case_id'] == cid), None)
        if c:
            text = (root / c['path'] / 'public/request.txt').read_text(encoding='utf-8')
            lines += [f"**{sid}/{cid}**", '', '```text', text.rstrip(), '```', '']
    lines += ['## 更新记录与限制', '',
              '旧版本全部文件在 [更新前归档](private/history/request-1.2-before-1.3.zip) 保留，路径与哈希见 [归档清单](private/history/request-1.2-before-1.3.json)。本次状态、每题前后哈希与复用记录见 [summary.json](summary.json)、[integrity.json](integrity.json) 和各题 private/update.json；源码快照见 [request-1.3 快照](private/request-1.3-snapshot/sha256.json)。', '',
              '旧生成过程的 32 次尝试、8 次失败、24 次通过及其中 4 次未收录的通过保留在 summary.json.history 和旧归档中。本次是既有 20 题的更新，不能把 20/20 信息检查结果当作任意 IFC 的生成率或系统修复成功率。未扩展 40 × 25 数据，也未改写已接受的正式 Proof。']
    (root / 'REPORT.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def update_dataset(dataset, stage, *, workers=2, expected_cases=20, install=False):
    dataset, stage = Path(dataset).resolve(), Path(stage).resolve()
    require(dataset.is_relative_to(ROOT) and stage.is_relative_to(ROOT / '.tmp'), 'UPDATE_PATH_OUTSIDE_WORKSPACE')
    require(not stage.exists() and not dataset.is_relative_to(stage), 'NEW_STAGE_REQUIRED')
    registered = subprocess.run(['git', 'ls-files', '--', dataset.relative_to(ROOT).as_posix()], cwd=ROOT, capture_output=True, text=True, check=True)
    require(not registered.stdout.strip(), 'REGISTERED_DATASET_NOT_MUTABLE')
    previous = read(dataset / 'summary.json')
    require(previous['request_profile'] == 'text2ifc/dataset-request/1.2', 'EXPECTED_REQUEST_1_2')
    require(previous['machine_validated_cases'] == expected_cases, 'UNEXPECTED_CASE_COUNT')
    old_files = sorted(p for p in dataset.rglob('*') if p.is_file())
    old_hashes = {p.relative_to(dataset).as_posix(): sha256(p) for p in old_files}
    shutil.copytree(dataset, stage)
    write_json(stage / 'private/update-run.json', {'status': 'checking', 'request_profile': PROFILE,
               'original_dataset': str(dataset), 'program_sha256': program_hash(), 'provider_calls': 0})
    completed, details = [], []
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as pool:
        tasks = [pool.submit(update_source, str(dataset), str(stage), s) for s in previous['sources']]
        for future in concurrent.futures.as_completed(tasks):
            try:
                source, case_details = future.result()
            except Exception as exc:
                write_json(stage / 'private/update-run.json', {'status': 'failed', 'original_dataset': str(dataset),
                    'program_sha256': program_hash(), 'provider_calls': 0, 'error': type(exc).__name__ + ':' + str(exc),
                    'traceback': traceback.format_exc(), 'original_dataset_unchanged': all(sha256(dataset / p) == h for p, h in old_hashes.items())})
                raise
            completed.append(source)
            details.extend(case_details)
            print(json.dumps({'stage': 'source_checked', 'source': source['source_id'], 'cases': len(source['cases'])}), flush=True)
    completed.sort(key=lambda s: s['source_id'])
    details.sort(key=lambda d: (d['source_id'], d['case_id']))
    cases = [c for s in completed for c in s['cases']]
    require(len(cases) == expected_cases and len(details) == expected_cases, 'INCOMPLETE_UPDATE')
    require(all(sha256(dataset / p) == h for p, h in old_hashes.items()), 'ORIGINAL_DATASET_CHANGED_DURING_STAGE')
    current_hashes = [sha256(stage / c['path'] / 'public/model.ifc') for c in cases]
    require(len(set(current_hashes)) == len(cases), 'DUPLICATE_DAMAGED_IFC')
    summary = {**copy.deepcopy(previous), 'request_profile': PROFILE, 'program_sha256': program_hash(), 'sources': completed,
               'prompt_counts': dict(Counter(m for c in cases for m in c['prompt_modes'])),
               'primary_prompt_counts': dict(Counter(c['primary_prompt'] for c in cases)),
               'shape_reference_targets': sum(d['shape_reference_count'] for d in details),
               'basic_box_targets': sum(d['basic_box_count'] for d in details),
               'update': {'status': 'passed', 'checked_cases': len(cases), 'ifc_bytes_unchanged_cases': sum(d['ifc_bytes_unchanged'] for d in details),
                          'rebuilt_cases': sum(d['replaced_door'] for d in details), 'provider_calls': 0, 'details': details}}
    write_json(stage / 'summary.json', summary)
    write_json(stage / 'private/source-selection-request-1.3.json', [s['source'] for s in completed])
    with (stage / 'cases.csv').open('w', encoding='utf-8-sig', newline='') as out:
        writer = csv.writer(out)
        writer.writerow(['source_id','case_id','family','severity','status','primary_prompt','door','window','beam','column','properties','path'])
        for c in cases:
            writer.writerow([c[k] for k in ('source_id','case_id','family','severity','status','primary_prompt')] + [c['deleted_counts'][k] for k in ('door','window','beam','column')] + [c['property_changes'], c['path']])
    integrity = {'schema_version': 'text2ifc/dataset-pilot-update-integrity/1.0', 'passed': True,
                 'sealed_cases': sum(verify_seal(stage / c['path']) for c in cases), 'native_zero_findings_cases': len(cases),
                 'prompt_checked_cases': len(cases), 'source_hashes_unchanged': True,
                 'distinct_damaged_sha256': len(set(current_hashes)), 'program_sha256': program_hash(),
                 'ifc_bytes_unchanged_cases': summary['update']['ifc_bytes_unchanged_cases'],
                 'new_native_receipt_cases': summary['update']['rebuilt_cases'], 'checked_paths': [c['path'] for c in cases]}
    require(integrity['sealed_cases'] == expected_cases, 'FINAL_SEALS_FAILED')
    write_json(stage / 'integrity.json', integrity)
    snapshot = stage / 'private/request-1.3-snapshot'
    snapshot_hashes = {}
    paths = [Path(__file__), ROOT / 'scripts/ifc_repair/generate_damage_pilot.py', *sorted((ROOT / 'scripts/ifc_repair/dataset_batch').glob('*.py'))]
    for path in paths:
        relative = path.relative_to(ROOT)
        target = snapshot / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        snapshot_hashes[relative.as_posix()] = sha256(target)
    write_json(snapshot / 'sha256.json', snapshot_hashes)
    write_json(stage / 'build.json', {'schema_version': 'text2ifc/dataset-pilot-update-build/1.0', 'configuration': {'request_profile': PROFILE, 'workers': workers, 'program_sha256': program_hash()},
                                     'previous_build': previous.get('program_sha256'), 'provider_calls': 0, 'ifcopenshell_version': ifcopenshell.version, 'method': 'public request recheck; same-byte receipt reuse; one private-preselected door replacement'})
    history = stage / 'private/history'
    history.mkdir(parents=True, exist_ok=True)
    archive = history / 'request-1.2-before-1.3.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as out:
        for path in old_files:
            out.write(path, path.relative_to(dataset).as_posix())
    with zipfile.ZipFile(archive) as saved:
        require(saved.testzip() is None, 'ARCHIVE_CORRUPT')
        import hashlib
        require(all(hashlib.sha256(saved.read(p)).hexdigest() == h for p, h in old_hashes.items()), 'ARCHIVE_HASH_MISMATCH')
    write_json(history / 'request-1.2-before-1.3.json', {'archive_sha256': sha256(archive), 'files': old_hashes, 'restore_root': str(dataset)})
    write_report(stage, summary, details)
    write_json(stage / 'private/update-run.json', {'status': 'passed', 'request_profile': PROFILE,
        'program_sha256': program_hash(), 'provider_calls': 0, 'checked_cases': len(cases)})
    if install:
        # Archive is already verified. Copy the archive first, then explicit files.
        for p in (archive, history / 'request-1.2-before-1.3.json'):
            target = dataset / p.relative_to(stage)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, target)
        for path in sorted(stage.rglob('*')):
            if path.is_file() and not path.is_relative_to(stage / 'private/rebuilt'):
                target = dataset / path.relative_to(stage)
                target.parent.mkdir(parents=True, exist_ok=True)
                if not target.exists() or sha256(target) != sha256(path):
                    temporary = target.with_name(target.name + '.updating')
                    shutil.copyfile(path, temporary)
                    os.replace(temporary, target)
        for c in cases:
            folder = dataset / c['path']
            for mode, meta in read(folder / 'case.json')['prompt_templates'].items():
                path = folder / f'public/request-{mode}.txt'
                if not meta['applicable'] and path.exists():
                    historic = folder / f'private/previous-public/request-{mode}.txt'
                    historic.parent.mkdir(parents=True, exist_ok=True)
                    os.replace(path, historic)
        require(all(verify_seal(dataset / c['path']) for c in cases), 'INSTALLED_SEAL_FAILURE')
        require(all(sha256(dataset / 'sources' / s['source_id'] / 'private/reference.ifc') == s['source_sha256'] for s in completed), 'INSTALLED_REFERENCE_CHANGED')
        require(all(sha256(ROOT / s['source']['input_path']) == s['source_sha256'] for s in completed), 'INSTALLED_MOTHER_SOURCE_CHANGED')
    return {'status': 'passed', 'installed': install, 'cases': len(cases), 'request_profile': PROFILE,
            'same_ifc_cases': integrity['ifc_bytes_unchanged_cases'], 'rebuilt_cases': integrity['new_native_receipt_cases'],
            'shape_reference_targets': summary['shape_reference_targets'], 'basic_box_targets': summary['basic_box_targets'],
            'prompt_counts': summary['prompt_counts'], 'report': str((dataset if install else stage) / 'REPORT.md')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, required=True)
    parser.add_argument('--stage', type=Path, required=True)
    parser.add_argument('--workers', type=int, choices=(1, 2), default=2)
    parser.add_argument('--install', action='store_true', help='install checked updates in the original active pilot')
    args = parser.parse_args()
    result = update_dataset(args.dataset, args.stage, workers=args.workers, install=args.install)
    print(json.dumps(result, ensure_ascii=False), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
