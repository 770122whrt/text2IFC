"""Bounded automatic dataset production; no LLM or repair-system calls."""
from __future__ import annotations

import argparse
import concurrent.futures
import contextlib
import csv
import json
import os
import shutil
import time
import traceback
from collections import Counter
from pathlib import Path

import ifcopenshell
import numpy as np

from .engine import _wrong_value, apply_recipe, build_recipes, seal_case, verify_seal, write_json
from .prompts_v2 import PROFILE, prepare_inventory
from .sampling import _mesh
from .validation import native_validate, product_state, program_hash, sha256


def _preserved_meshes(original, damaged, manifest):
    excluded = {t['guid'] for t in manifest['deletions']}
    excluded.update(t['opening_guid'] for t in manifest['deletions'] if t.get('opening_guid') and not t.get('preserve_opening', True))
    excluded.update(t['host']['guid'] for t in manifest['deletions'] if t.get('host') and not t.get('preserve_opening', True))
    checked, errors = [], []
    candidates = sorted((p for p in original.by_type('IfcElement') if p.GlobalId not in excluded and p.Representation), key=lambda p: p.GlobalId)
    for p in candidates[:3]:
        try:
            av, af = _mesh(p)
            bv, bf = _mesh(damaged.by_guid(p.GlobalId))
            passed = av.shape == bv.shape and af.shape == bf.shape and np.array_equal(af, bf) and np.allclose(av, bv, atol=1e-8, rtol=0)
            checked.append({'guid': p.GlobalId, 'class': p.is_a(), 'passed': bool(passed)})
            if not passed:
                errors.append('preserved_mesh_changed:' + p.GlobalId)
        except Exception as exc:
            errors.append('preserved_mesh_uncheckable:' + p.GlobalId + ':' + str(exc)[:160])
    return {'passed': not errors and bool(checked), 'checked': checked, 'errors': errors, 'scope': 'up to three surviving elements, world geometry, per case'}


def select_recipes(recipes, count, desired=None):
    """Frozen coverage order; prefer small changes and keep alternatives for failures."""
    desired = desired or list(dict.fromkeys(r['family'] for r in recipes))[:count]
    if len(desired) < count:
        desired = desired + [r['family'] for r in recipes[:count - len(desired)]]
    groups = []
    for family in desired[:count]:
        candidates = [r for r in recipes if r['family'] == family and len(r['deletions']) <= 12]
        candidates.sort(key=lambda r: (len(r['deletions']), r['severity'] != 'light'))
        if not candidates:
            raise ValueError('REQUIRED_DAMAGE_FAMILY_UNAVAILABLE:' + family)
        groups.append(candidates[:6])
    return groups


def recipe_from_plan(inventory, plan):
    """Use fresh IFC facts for a preselected operation; never use stale shape data."""
    selected, changes = [], []
    for item in plan['deletions']:
        target = next((t for t in inventory['targets'][item['class_family']] if t['guid'] == item['private_target_guid']), None)
        if target is None:
            raise ValueError('PLANNED_TARGET_NOT_ADMITTED:' + item['class_family'])
        selected.append({**target, 'preserve_opening': bool(item.get('preserve_opening', False))})
    deleted = {t['guid'] for t in selected}
    deleted.update(t['opening_guid'] for t in selected if t.get('opening_guid') and not t['preserve_opening'])
    resolved = []
    for t, item in zip(selected, plan['deletions']):
        g = dict(t['geometry'])
        opening = t.get('opening')
        if not g.get('body_spec'):
            peer = next((p for p in g.get('peers', []) if p['guid'] not in deleted and p['guid'] == item.get('product_reference_guid_private')), None)
            peer = peer or next((p for p in g.get('peers', []) if p['guid'] not in deleted), None)
            if not peer:
                raise ValueError('PLANNED_SHAPE_REFERENCE_UNAVAILABLE')
            g['body_spec'] = {'method': 'surviving_instance', 'peer': peer}
        if opening and not t['preserve_opening']:
            og = dict(opening['geometry'])
            if not og.get('body_spec'):
                peer = next((p for p in og.get('peers', []) if p['guid'] not in deleted and p['guid'] == item.get('opening_reference_guid_private')), None)
                peer = peer or next((p for p in og.get('peers', []) if p['guid'] not in deleted), None)
                if not peer:
                    raise ValueError('PLANNED_OPENING_REFERENCE_UNAVAILABLE')
                og['body_spec'] = {'method': 'surviving_instance', 'peer': peer}
            opening = {**opening, 'geometry': og}
        resolved.append({**t, 'geometry': g, 'opening': opening})
    prop = plan.get('property_change')
    if prop:
        target = next((p for p in inventory['properties'] if p['guid'] == prop['guid'] and p['pset_name'] == prop['pset_name'] and p['property_name'] == prop['property_name']), None)
        if not target or target['guid'] in deleted:
            raise ValueError('PLANNED_PROPERTY_NOT_ADMITTED')
        changes.append({**target, 'after': _wrong_value(target, 0)})
    return {'family': plan['family'], 'severity': plan.get('severity', 'light'), 'deletions': resolved, 'property_changes': changes}


def process_source(spec, repository, output, count, seed):
    from .prompt_check import audit_prompt
    from .wall_check import check_wall_closure
    profile = spec.get('request_profile', PROFILE)
    prepare = prepare_inventory
    if profile == 'text2ifc/dataset-request/1.3':
        from .prompts_v3 import prepare_inventory as prepare
        from .prompts_v3 import prepare_recipe
        from .prompt_check_v3 import audit_prompt
    elif profile != PROFILE:
        raise ValueError('UNSUPPORTED_PILOT_REQUEST_PROFILE')

    started = time.monotonic()
    repository, output = Path(repository).resolve(), Path(output).resolve()
    source = (repository / spec['input_path']).resolve()
    if source.stat().st_size >= 20_000_000:
        raise ValueError('SOURCE_EXCEEDS_20_MB')
    source_hash = sha256(source)
    if spec.get('source_sha256') and spec['source_sha256'] != source_hash:
        raise ValueError('SOURCE_SHA_CHANGED')
    root = output / 'sources' / spec['source_id']
    root.mkdir(parents=True, exist_ok=False)
    write_json(root / 'private/source.json', spec)
    reference = root / 'private/reference.ifc'
    shutil.copyfile(source, reference)
    with (root / 'private/source-validation.log').open('w', encoding='utf-8') as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        admission = native_validate(reference)
    write_json(root / 'private/source-validation.json', {**admission, 'input_sha256': source_hash})
    if not admission['passed']:
        raise ValueError('SOURCE_NATIVE_VALIDATION_FAILED')
    original = ifcopenshell.open(str(reference))
    inv = prepare(reference)
    write_json(root / 'private/inventory.json', inv)
    recipes = build_recipes(inv, count=30, seed=seed)
    desired = spec.get('pilot_families')
    groups = [[recipe_from_plan(inv, plan)] for plan in spec['pilot_cases'][:count]] if spec.get('pilot_cases') else select_recipes(recipes, count, desired)
    write_json(root / 'private/plan.json', {'families': desired, 'candidate_groups': groups, 'seed': seed})
    baseline = product_state(original)
    attempts, accepted, seen_bytes = [], [], set()
    for number, candidates in enumerate(groups, 1):
        for attempt_number, recipe in enumerate(candidates, 1):
            folder = root / 'cases' / f'case-{number:03d}-a{attempt_number:02d}'
            row = {'source_id': spec['source_id'], 'case_id': folder.name, 'path': folder.relative_to(output).as_posix(), 'family': recipe['family'], 'severity': recipe['severity']}
            write_json(root / f'private/attempt-recipes/{folder.name}.json', recipe)
            try:
                if profile == 'text2ifc/dataset-request/1.3':
                    recipe = prepare_recipe(recipe)
                    write_json(root / f'private/attempt-recipes/{folder.name}.json', recipe)
                with (root / f'private/{folder.name}.log').open('w', encoding='utf-8') as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                    result = apply_recipe(reference, recipe, folder, inventory=inv, baseline_state=baseline, prompt_profile=profile)
                    manifest = json.loads((folder / 'private/mutation.json').read_text(encoding='utf-8'))
                    damaged = ifcopenshell.open(str(folder / 'public/model.ifc'))
                    prompt_checks = {mode: audit_prompt(original, damaged, manifest, mode, (folder / f'public/request-{mode}.txt').read_text(encoding='utf-8')) for mode, meta in result['prompt_templates'].items() if meta['applicable']}
                    walls = check_wall_closure(reference, folder / 'public/model.ifc', manifest)
                    meshes = _preserved_meshes(original, damaged, manifest)
                write_json(folder / 'private/prompt-check.json', prompt_checks)
                write_json(folder / 'private/wall-check.json', walls)
                write_json(folder / 'private/mesh-check.json', meshes)
                prompt_ok = 'world' in prompt_checks and all(c['passed'] for c in prompt_checks.values())
                passed = result['status'] == 'passed' and prompt_ok and walls['passed'] and meshes['passed'] and result['damaged_sha256'] not in seen_bytes
                primary = 'host_wall' if number % 2 == 1 and 'host_wall' in prompt_checks else 'world'
                if passed:
                    shutil.copyfile(folder / f'public/request-{primary}.txt', folder / 'public/request.txt')
                    seen_bytes.add(result['damaged_sha256'])
                result.update(schema_version='text2ifc/ifc-repair-dataset-case/1.1', status='passed' if passed else 'failed',
                              machine_validated=passed, primary_prompt=primary if passed else None,
                              information_sufficient=prompt_ok, wall_check_passed=walls['passed'],
                              wall_check_applicable=walls['applicable'], independent_mesh_check_passed=meshes['passed'],
                              additional_evidence=['private/prompt-check.json', 'private/wall-check.json', 'private/mesh-check.json'] + (['public/request.txt'] if passed else []))
                write_json(folder / 'case.json', result)
                seal_case(folder)
                if not verify_seal(folder):
                    raise ValueError('FINAL_CASE_SEAL_INVALID')
                wall_summary = {'passed': walls['passed'], 'applicable': walls['applicable'], 'walls_checked': len(walls['walls']),
                                'removed_openings': sum(not t.get('preserve_opening', True) for t in manifest['deletions'] if t.get('opening_guid')),
                                'preserved_openings': sum(t.get('preserve_opening', True) for t in manifest['deletions'] if t.get('opening_guid'))}
                row.update(status=result['status'], primary_prompt=result['primary_prompt'], deleted_counts=result['deleted_counts'], property_changes=result['property_changes'],
                           prompt_modes=list(prompt_checks), prompt_checks_passed=prompt_ok, wall_checks=wall_summary,
                           errors=[] if passed else {'native': not result['machine_validated'] and json.loads((folder / 'private/validation.json').read_text(encoding='utf-8'))['finding_count'], 'prompts': {k: v.get('errors', []) for k, v in prompt_checks.items() if not v['passed']}, 'walls': walls.get('errors', []), 'meshes': meshes['errors']})
                attempts.append(row)
                if passed:
                    accepted.append(row)
                    break
            except Exception as exc:
                row.update(status='failed', errors={'exception': type(exc).__name__ + ':' + str(exc)})
                attempts.append(row)
                write_json(root / f'private/attempt-errors/{folder.name}.json', {'error': row['errors'], 'traceback': traceback.format_exc()})
            finally:
                write_json(root / 'private/progress.json', {'target': count, 'accepted': len(accepted), 'attempts': len(attempts), 'provider_calls': 0})
    unchanged = sha256(source) == source_hash == sha256(reference)
    result = {'source_id': spec['source_id'], 'source': spec, 'status': 'complete' if len(accepted) == count and unchanged else 'incomplete',
              'source_unchanged': unchanged, 'source_native_passed': admission['passed'], 'source_sha256': source_hash,
              'class_counts': inv['class_counts'], 'eligible_counts': {k: len(v) for k, v in inv['targets'].items()},
              'cases': accepted, 'attempts': attempts, 'elapsed_seconds': round(time.monotonic() - started, 3)}
    write_json(root / 'result.json', result)
    return result


def write_report(output, sources, errors, count):
    output = Path(output)
    cases = [case for source in sources for case in source['cases']]
    attempts = [a for source in sources for a in source['attempts']]
    hashes = [json.loads((output / c['path'] / 'case.json').read_text(encoding='utf-8'))['damaged_sha256'] for c in cases]
    unique = len(hashes) == len(set(hashes))
    profiles = {json.loads((output / c['path'] / 'private/mutation.json').read_text(encoding='utf-8'))['prompt_profile'] for c in cases}
    profile = next(iter(profiles)) if len(profiles) == 1 else 'mixed' if profiles else PROFILE
    summary = {'schema_version': 'text2ifc/dataset-pilot-report/1.0', 'status': 'complete' if len(cases) == count and not errors and unique else 'incomplete',
               'source_models': len(sources), 'target_cases': count, 'machine_validated_cases': len(cases),
               'attempted_cases': len(attempts), 'failed_attempts': sum(a['status'] != 'passed' for a in attempts), 'worker_errors': errors,
               'unique_damaged_bytes': unique, 'source_hashes_unchanged': all(s['source_unchanged'] for s in sources),
               'families': dict(Counter(c['family'] for c in cases)), 'prompt_counts': dict(Counter(m for c in cases for m in c['prompt_modes'])),
               'primary_prompt_counts': dict(Counter(c['primary_prompt'] for c in cases)),
               'wall_check_cases': sum(c['wall_checks']['applicable'] for c in cases),
               'removed_openings_checked': sum(c['wall_checks']['removed_openings'] for c in cases),
               'preserved_openings_checked': sum(c['wall_checks']['preserved_openings'] for c in cases),
               'provider_calls': 0, 'system_repair_tested': False, 'human_reviewed_cases': 0,
               'request_profile': profile, 'program_sha256': program_hash(),
               'scope': 'native schema+EXPRESS, exact recorded damage/preservation, actual prompt geometry/location/relations/properties, wall closure, up to three surviving meshes per case; no live repair success claim',
               'sources': sources}
    write_json(output / 'summary.json', summary)
    with (output / 'cases.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['source_id', 'case_id', 'family', 'severity', 'status', 'primary_prompt', 'door', 'window', 'beam', 'column', 'properties', 'path'])
        for c in cases:
            writer.writerow([c['source_id'], c['case_id'], c['family'], c['severity'], c['status'], c['primary_prompt'], *[c['deleted_counts'][k] for k in ('door', 'window', 'beam', 'column')], c['property_changes'], c['path']])
    lines = ['# 小批量自动损伤与 Prompt 自检报告', '',
             f"状态：{summary['status']}；{len(sources)} 个 IFC，{len(cases)} 个通过案例，目标 {count}；共尝试 {len(attempts)} 次，失败 {summary['failed_attempts']} 次。", '',
             '全部 prompt 由脚本从 IFC 和固定损伤配方生成，无逐题人工代写。每例从完整母本重新生成，提供一份 damaged IFC 和一份 public/request.txt；附加定位变体不另算损伤案例。', '',
             '本轮仅使用墙名定位和世界坐标。楼层局部定位停用：其基准可从 IFC 楼层放置关系取得，但尚不纳入本轮试点。无墙宿主的梁柱只有世界坐标请求，不虚构墙定位。', '',
             '检查范围是任务明确指定的几何、位置、朝向、楼层归属、洞口关系和实例属性；不要求恢复原 GUID、原名称或未指定的全部语义属性。复杂形状仅引用损伤模型中仍存在且能唯一定位的同形几何，不以外包盒代替完整形状。', '',
             '|母本|通过/尝试|门/窗/梁/柱原生数量|可挖数量|', '|---|---|---|---|']
    for s in sources:
        lines.append(f"|{s['source_id']}|{len(s['cases'])}/{len(s['attempts'])}|{' / '.join(str(s['class_counts'][k]) for k in ('door','window','beam','column'))}|{' / '.join(str(s['eligible_counts'][k]) for k in ('door','window','beam','column'))}|")
    lines += ['', '损伤族：' + json.dumps(summary['families'], ensure_ascii=False), '',
              '每个通过案例均满足：写出后 IfcOpenShell schema+EXPRESS 零 findings；删除身份、属性变化及保全检查通过；从实际公开文本独立解析定位与完整几何并与私有参考对照；适用时墙体补全/保留洞口检查通过；最多三个保留构件世界网格一致；源文件与私有参考字节未改变，最终文件封存通过。', '',
              f"墙体检查适用于 {summary['wall_check_cases']} 例；共检查移除洞口 {summary['removed_openings_checked']} 个、保留洞口 {summary['preserved_openings_checked']} 个。", '',
              '窗/门与洞口一并删除时，检查原洞口内部区域恢复为墙体，并与只取消目标 void 的独立对照比较；只删除门窗、保留洞口时，检查空洞和其关联仍保留。仅梁柱/属性案例的墙体检查标为不适用。每洞口有限内部点检结合闭合/体积与规范化网格比较，不是完整开口体积的数学证明；复杂或不确定几何保守拒绝。', '',
              f"可用请求变体：{summary['prompt_counts']}；主请求分布：{summary['primary_prompt_counts']}。", '',
              '## 逐案例入口', '', '|母本/案例|损伤族|删除门/窗/梁/柱|属性改动|主定位|损伤 IFC / Prompt / 检查|', '|---|---|---|---|---|---|']
    for c in cases:
        path = c['path']
        links = f"[IFC]({path}/public/model.ifc) / [Prompt]({path}/public/request.txt) / [信息检查]({path}/private/prompt-check.json) / [墙体检查]({path}/private/wall-check.json)"
        lines.append(f"|{c['source_id']}/{c['case_id']}|{c['family']}|{' / '.join(str(c['deleted_counts'][k]) for k in ('door','window','beam','column'))}|{c['property_changes']}|{c['primary_prompt']}|{links}|")
    lines += ['', '## 失败与证据范围', '',
              '全部失败尝试保留在 sources 下，对应 result.json 与日志记录原因；没有覆盖失败 IFC、替失败记通过或发送模型。summary.json 是数量与完整结果入口，cases.csv 只列通过案例，build.json 记录冻结配置/源码/版本。旧全量停止批次及已有正式证据未续跑或改写。', '',
              '所有派生案例为机器校验数据、人工待审。母本既有审核标签保留；本批不代表人工验收、工程规范审查或修复系统成功率。系统修复及 Provider 调用为 0。']
    if errors:
        lines += ['', '工作单元错误：' + json.dumps(errors, ensure_ascii=False)]
    (output / 'REPORT.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument('--input', type=Path, help='one intact IFC2X3 input; use --cases-per-ifc for bounded automatic production')
    inputs.add_argument('--sources', type=Path, help='JSON source specs with optional pilot_families')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cases-per-ifc', type=int, choices=range(1, 9), default=4)
    parser.add_argument('--workers', type=int, choices=(1, 2), default=2)
    parser.add_argument('--seed', type=int, default=20261010)
    parser.add_argument('--request-profile', choices=('1.2', '1.3'), default='1.3')
    parser.add_argument('--repository-root', type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    root = args.repository_root.resolve()
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError('NEW_OUTPUT_REQUIRED:' + str(output))
    if args.input:
        path = args.input.resolve()
        specs = [{'source_id': 'input-001', 'input_path': str(path), 'source_sha256': sha256(path), 'kind': 'user_provided', 'license_status': 'not established by this tool'}]
    else:
        value = json.loads(args.sources.read_text(encoding='utf-8-sig'))
        if isinstance(value, list):
            specs = value
        elif 'selected_source_specs' in value:
            plans = {row['source_id']: row['recommended_cases'] for row in value['selected_sources']}
            specs = [{**s, 'pilot_cases': plans[s['source_id']]} for s in value['selected_source_specs']]
        else:
            specs = value['sources']
    if len({s['source_sha256'] for s in specs}) != len(specs):
        raise ValueError('DUPLICATE_SOURCE_BYTES')
    selected_profile = 'text2ifc/dataset-request/' + args.request_profile
    specs = [{**s, 'request_profile': selected_profile} for s in specs]
    if any((root / s['input_path']).resolve().is_relative_to(output) for s in specs):
        raise ValueError('SOURCE_INSIDE_OUTPUT')
    output.mkdir(parents=True)
    configuration = {'profile': selected_profile, 'sources': specs, 'cases_per_ifc': args.cases_per_ifc, 'seed': args.seed, 'workers': args.workers, 'program_sha256': program_hash()}
    write_json(output / 'build.json', {'schema_version': 'text2ifc/dataset-pilot-build/1.0', 'configuration': configuration, 'provider_calls': 0, 'ifcopenshell_version': ifcopenshell.version})
    write_json(output / 'private/source-selection.json', specs)
    completed, errors = [], []
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(process_source, spec, str(root), str(output), args.cases_per_ifc, args.seed + i): spec for i, spec in enumerate(specs)}
        for future in concurrent.futures.as_completed(futures):
            spec = futures[future]
            try:
                completed.append(future.result())
            except Exception as exc:
                errors.append({'source_id': spec['source_id'], 'error': type(exc).__name__ + ':' + str(exc), 'traceback': traceback.format_exc()})
            write_json(output / 'private/progress.json', {'completed_sources': len(completed), 'worker_errors': errors, 'provider_calls': 0})
            print(json.dumps({'stage': 'source_complete', 'source': spec['source_id'], 'completed': len(completed), 'errors': len(errors)}, ensure_ascii=False), flush=True)
    completed.sort(key=lambda s: s['source_id'])
    summary = write_report(output, completed, errors, len(specs) * args.cases_per_ifc)
    print(json.dumps({k: v for k, v in summary.items() if k not in ('sources', 'worker_errors')}, ensure_ascii=False), flush=True)
    return 0 if summary['status'] == 'complete' else 2


if __name__ == '__main__':
    raise SystemExit(main())
