"""Prepare pending formal task packages; never accepts tasks or invokes models."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[3]
for directory in (ROOT, ROOT / 'src'):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

import ifcopenshell
from text2ifc_ifc_repair.compare import normalized_model_diff
from ifcopenshell.api.root import remove_product
from text2ifc_ifc_repair.mutation import (
    _snapshot_owner_history, _restore_owner_history,
    _canonicalize_modified_relationship_sets, _element_volume_m3,
)
from .contracts import PUBLIC_FILES, damage_profile, read_json, safe_path, sha256, write_json
from .inspection import geometry_snapshot, native_validation, relation_evidence
from .review_materials import render_validation
from .viewer import write_viewer


def _recipe(row, model):
    proposal = row['task_proposal']
    door_damage = proposal.get('door_damage', 'remove_door_keep_opening')
    if door_damage not in {'remove_door_keep_opening', 'remove_door_and_opening'}:
        raise ValueError('UNKNOWN_DOOR_DAMAGE')
    ids = proposal['provisional_source_step_ids']
    if not ids or len(set(ids)) != len(ids):
        raise ValueError('EMPTY_OR_DUPLICATE_TARGETS')
    text = proposal['public_request']
    if not isinstance(text, str) or not text.strip():
        raise ValueError('PUBLIC_REQUEST_REQUIRED')
    if re.search(r'(?<![A-Za-z0-9_$])[0-3][A-Za-z0-9_$]{21}(?![A-Za-z0-9_$])', text):
        raise ValueError('GUID_IN_PUBLIC_REQUEST')
    if re.search(r'IfcOpenShell|ChangeSet|run_python|Python|STEP', text, re.I):
        raise ValueError('METHOD_HINT_IN_PUBLIC_REQUEST')
    targets = []
    for step in ids:
        entity = model.by_id(step)
        if entity.is_a() not in {'IfcDoor', 'IfcWindow'} or len(entity.FillsVoids) != 1:
            raise ValueError('TARGET_MUST_HAVE_UNIQUE_OPENING')
        opening = entity.FillsVoids[0].RelatingOpeningElement
        if len(opening.VoidsElements) != 1 or len(opening.HasFillings) != 1:
            raise ValueError('OPENING_MUST_HAVE_UNIQUE_WALL_AND_FILL')
        wall = opening.VoidsElements[0].RelatingBuildingElement
        if not wall.is_a('IfcWall'):
            raise ValueError('UNSUPPORTED_TARGET_HOST')
        kind = 'door' if entity.is_a('IfcDoor') else 'window'
        targets.append({'kind': kind, 'target_guid': entity.GlobalId,
            'opening_guid': opening.GlobalId, 'wall_guid': wall.GlobalId,
            'preserve_opening': kind == 'door' and door_damage == 'remove_door_keep_opening', 'source_step_id': step})
    return targets


def check_candidate(output):
    output = safe_path(Path(output))
    task = read_json(output / 'private/task.json')
    checks = read_json(output / 'private/checks.json')
    errors = []
    if set(p.name for p in (output / 'public').iterdir()) != PUBLIC_FILES:
        errors.append('PUBLIC_FILE_ALLOWLIST_MISMATCH')
    if not all(checks['checks'].values()):
        errors.append('PREPARATION_CHECK_FAILED')
    if sha256(output / 'private/reference.ifc') != task['source_sha256']:
        errors.append('REFERENCE_CHANGED')
    if sha256(output / 'private/mutation/damaged.ifc') != task['damaged_sha256'] or sha256(output / 'public/model.ifc') != task['damaged_sha256']:
        errors.append('DAMAGED_INPUT_CHANGED')
    text = (output / 'public/request.txt').read_text(encoding='utf8')
    if text.strip() != task['request'].strip():
        errors.append('PUBLIC_REQUEST_MISMATCH')
    public_bytes = (output / 'public/model.ifc').read_text(encoding='utf8') + text
    if any(guid in public_bytes for guid in checks['removed_product_guids']):
        errors.append('DELETED_ID_IN_PUBLIC_INPUT')
    return {'valid': not errors, 'human_accepted': task['review']['status'] == 'accepted',
        'case_id': task['case_id'], 'errors': errors,
        'scope': 'Input preparation/reopen/schema/EXPRESS and intended damage; no model capability claim'}


def prepare_candidate(row, *, repository_root, output):
    root, output = safe_path(Path(repository_root)), safe_path(Path(output))
    source = safe_path(root / row['source_path'])
    if not source.is_relative_to(root) or source.is_relative_to(output):
        raise ValueError('INVALID_SOURCE_OR_OUTPUT')
    if sha256(source) != row['source_sha256']:
        raise ValueError('SOURCE_CHANGED')
    before = ifcopenshell.open(str(source))
    if before.schema != 'IFC2X3':
        raise ValueError('UNSUPPORTED_SCHEMA')
    damage = _recipe(row, before)
    if output.exists():
        previous = read_json(output / 'private/task.json')
        if previous.get('purpose') != 'formal_candidate' or previous['case_id'] != row['candidate_slot'] or previous['review']['status'] != 'pending_human_review':
            raise ValueError('ONLY_PENDING_FORMAL_CANDIDATE_CAN_REFRESH')
    private = output / 'private'
    mutation_dir = private / 'mutation'
    mutation_dir.mkdir(parents=True, exist_ok=True)
    write_json(private / 'task.json', {'purpose': 'formal_candidate', 'case_id': row['candidate_slot'],
        'review': {'status': 'pending_human_review'}, 'preparation_state': 'building'})
    reference, damaged = private / 'reference.ifc', mutation_dir / 'damaged.ifc'
    shutil.copyfile(source, reference)
    model = ifcopenshell.open(str(reference))
    owners = _snapshot_owner_history(model)
    closure = {}
    for target in damage:
        if not target['preserve_opening']:
            wall = model.by_guid(target['wall_guid'])
            item = closure.setdefault(wall.GlobalId, {'volume_before_m3': _element_volume_m3(wall), 'expected_delta_m3': 0.0})
            item['expected_delta_m3'] += _element_volume_m3(model.by_guid(target['opening_guid']))
    # General deletion is a preparation operation, independent of B's wall
    # axis restrictions. Retain shared representations and other occurrences.
    for target in damage:
        remove_product(model, product=model.by_guid(target['target_guid']))
        if not target['preserve_opening']:
            remove_product(model, product=model.by_guid(target['opening_guid']))
    _restore_owner_history(model, owners)
    _canonicalize_modified_relationship_sets(model)
    model.write(str(damaged))
    after = ifcopenshell.open(str(damaged))
    for guid, item in closure.items():
        item['volume_after_m3'] = _element_volume_m3(after.by_guid(guid))
        item['actual_delta_m3'] = item['volume_after_m3'] - item['volume_before_m3']
        item['closed'] = abs(item['actual_delta_m3'] - item['expected_delta_m3']) <= 1e-5
    before_products = {p.GlobalId: p for p in before.by_type('IfcProduct')}
    after_products = {p.GlobalId: p for p in after.by_type('IfcProduct')}
    removed = set(before_products) - set(after_products)
    expected_removed = {t['target_guid'] for t in damage} | {t['opening_guid'] for t in damage if not t['preserve_opening']}
    diff = normalized_model_diff(before, after)
    source_validation, damaged_validation = native_validation(before), native_validation(after)
    refs = [before.by_id(i).GlobalId for i in row['task_proposal']['retained_reference_step_ids']]
    targets, relations = [], []
    for index, target in enumerate(damage):
        entity = before.by_guid(target['target_guid'])
        obligations = [('fill', 'IfcRelFillsElement')]
        if not target['preserve_opening']:
            obligations.append(('void', 'IfcRelVoidsElement'))
        if entity.ContainedInStructure:
            obligations.append(('storey', 'IfcRelContainedInSpatialStructure'))
        requirements = [{'id': f'target-{index+1}.{key}', 'ifc_class': kind, 'basis': 'One required membership edge for this target.'} for key, kind in obligations]
        relations += relation_evidence(before, after, {'damage': target, 'task': {'required_relations': requirements}}, target['opening_guid'])
        targets.append({**target, 'target': geometry_snapshot(entity),
            'opening': geometry_snapshot(before.by_guid(target['opening_guid'])),
            'host': geometry_snapshot(after.by_guid(target['wall_guid'])),
            'required_relations': requirements})
    checks = {'checks': {
        'source_unchanged': sha256(source) == row['source_sha256'] == sha256(reference),
        'schema_preserved': before.schema == after.schema == 'IFC2X3',
        'only_expected_products_removed': removed == expected_removed,
        'no_products_created': not (set(after_products) - set(before_products)),
        'no_unexpected_modified_products': not [r for r in diff['modified'] if r['global_id'] in before_products],
        'source_native_validation_passed': source_validation['passed'],
        'damaged_native_validation_passed': damaged_validation['passed'],
        'required_relation_edges_verified': all(r['verified'] for r in relations),
        'removed_window_regions_closed': all(closure[t['wall_guid']]['closed'] for t in damage if t['kind'] == 'window'),
        'removed_door_regions_closed': all(closure[t['wall_guid']]['closed'] for t in damage if t['kind'] == 'door' and not t['preserve_opening']),
        'retained_door_openings_empty_and_hosted': all(not after.by_guid(t['opening_guid']).HasFillings and len(after.by_guid(t['opening_guid']).VoidsElements) == 1 for t in damage if t['preserve_opening']),
        'targets_and_references_have_geometry': all(t['target']['geometry_status'] == 'available' for t in targets) and all(geometry_snapshot(after.by_guid(g))['geometry_status'] == 'available' for g in refs),
    }, 'source_validation': source_validation, 'damaged_validation': damaged_validation,
        'removed_product_guids': sorted(removed), 'targets': targets,
        'required_relation_evidence': relations, 'wall_closure': closure, 'root_diff': diff, 'host': targets[0]['host']}
    write_json(private / 'checks.json', checks)
    write_json(mutation_dir / 'mutation_manifest.private.json', {'targets': damage, 'wall_closure': closure,
        'method': 'IfcOpenShell root.remove_product; preserve owner history and canonical relationship sets'})
    if not all(checks['checks'].values()):
        raise ValueError('FORMAL_DAMAGE_PREPARATION_CHECK_FAILED')
    counts = dict(Counter(before.by_guid(t['target_guid']).is_a() for t in damage))
    task = {'schema_version': 'repair-comparison-task-candidate/0.1', 'purpose': 'formal_candidate',
        'case_id': row['candidate_slot'], 'source': row, 'damage': damage,
        'source_sha256': row['source_sha256'], 'damaged_sha256': sha256(damaged),
        'request': row['task_proposal']['public_request'], 'required_product_count': len(damage),
        'required_products': counts, 'required_relation_count': len(relations),
        'damage_profile': damage_profile(counts), 'targets': targets,
        'review': {'status': 'pending_human_review', 'reviewer': None, 'reviewed_at': None},
        'budget': {'provider_calls_allowed': False, 'status': 'not_frozen'},
        'allowed_alternatives': ['New identities and different STEP serialization are allowed.', 'Door swing is not a mandatory clarification; match the retained frame/leaf/material reference.'],
        'preservation': ['Only the requested target areas may change; retain all other products and their geometry/relationships.'],
        'metrics': {'status': 'deferred_by_user', 'formal_scoring_frozen': False}}
    write_json(private / 'task.json', task)
    write_json(private / 'answer-card.json', {'status': 'pending_human_review', 'required_user_facts': [], 'out_of_card_policy': 'Ask the human; never retrieve an answer from G.'})
    public = output / 'public'
    public.mkdir(exist_ok=True)
    shutil.copyfile(damaged, public / 'model.ifc')
    (public / 'request.txt').write_text(task['request'].strip() + '\n', encoding='utf8')
    validation = {**damaged_validation, 'ifc_path': 'public/model.ifc', 'ifc_schema': after.schema, 'ifc_sha256': task['damaged_sha256']}
    write_json(private / 'damaged-ifc-validation.json', validation)
    (output / 'IFC-VALIDATION.md').write_text(render_validation(validation), encoding='utf8')
    visual = write_viewer(output, {'case_id': task['case_id'], 'damage': damage,
        'task': {'summary': row['task_proposal'].get('description', '修复局部缺失'), 'reference_guids': refs}})
    if not visual['removed_target_absent_in_d'] or not visual['reference_geometry_unchanged']:
        raise ValueError('VISUAL_PREPARATION_CHECK_FAILED')
    notice = [f'# {task["case_id"]} 来源和修改声明', '', f'许可：{row["license"]}', f'来源：{row["rights_source_url"]}',
        f'源模型：{row["asset_id"]}', f'参考角色：{row["source_role"]}', row['rights_conditions'], '',
        '修改：为本实验删除上述局部门／窗；公开模型是修改副本。保留原源文件和权利登记，未改贴项目软件许可。']
    (private / 'SOURCE-LICENSE.md').write_text('\n\n'.join(notice) + '\n', encoding='utf8')
    attribution = private / 'attribution'
    attribution.mkdir(exist_ok=True)
    if row.get('rights_record'):
        rights = root / row['rights_record']
        matched = [r for r in rights.read_text(encoding='utf8').splitlines() if row['asset_id'] in r]
        if not matched:
            raise ValueError('MODEL_RIGHTS_RECORD_MISSING')
        (attribution / 'rights.jsonl').write_text('\n'.join(matched) + '\n', encoding='utf8')
    if row['license'].startswith('GPL'):
        license_file = root / 'dataset/external/_checks/ifc-assets-20260913/sources/opensourcebim-testdata-license.txt'
        shutil.copyfile(license_file, attribution / 'license.txt')
    lines = [f'# {task["case_id"]}：{row["task_proposal"].get("description", "局部修复")}', '',
        '**待人工审阅（pending_human_review）**。五题测试先检查输入与损伤；未调用模型，不是模型成绩。', '',
        '[局部剖切图](REVIEW.png) · [打开 G/D 同步视角查看器](VIEW.html) · [格式校验](IFC-VALIDATION.md) · [许可与修改说明](private/SOURCE-LICENSE.md)', '',
        '![损坏前后的同尺度局部剖切；D 红十字只作定位标注](REVIEW.png)', '',
        '## 公开请求', '', task['request'], '', '## 损伤及私有核对', '',
        '|删除构件 STEP ID|类别|保留洞口|世界包围盒中心（m）|', '|---|---|---|---|']
    for t in targets:
        center = ', '.join(f'{sum(b)/2:.4f}' for b in t['target']['bounds_world_m'])
        lines.append(f'|{t["source_step_id"]}|{t["target"]["class"]}|{"是" if t["preserve_opening"] else "否"}|{center}|')
    lines += ['', f'主目标 {len(targets)} 个；{task["damage_profile"]["level"]} / {task["damage_profile"]["composition"]}。独立 schema＋EXPRESS：G 与 D 均零诊断。', '',
        '## 审阅要点', '', '请核对定位是否唯一、尺寸／参照是否清楚、损伤是否合理，以及其余对象是否原位保留。门开向不是必答项。本批都是信息充分题；必要澄清题随后另选。', '',
        '修复需生成实际构件及相应洞口／宿主／楼层成员关系。允许新身份和等价序列化，不能只补数量、移动参照、重复补建或误改其他对象。具体容差与指标随后确认。', '',
        'private/ 和查看器只供审题／评估；被测环境只获得 public/ 的两个文件。']
    (output / 'REVIEW.md').write_text('\n'.join(lines) + '\n', encoding='utf8')
    return check_candidate(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inventory', type=Path, default=Path(__file__).with_name('formal_candidates.private.json'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    rows = read_json(args.inventory)['candidates']
    results = []
    for row in rows:
        results.append(prepare_candidate(row, repository_root=ROOT, output=args.output / row['candidate_slot']))
        print(json.dumps(results[-1], ensure_ascii=False), flush=True)
    lines = ['# Repair 首批五题', '', '五个不同 IFC；三份 CC BY 4.0、两份 GPL。输入测试已做，人审未自动接受，指标尚未冻结。', '']
    lines += [f'- [{row["candidate_slot"]}：{row["task_proposal"]["description"]}]({row["candidate_slot"]}/REVIEW.md)' for row in rows]
    (args.output / 'README.md').write_text('\n'.join(lines) + '\n', encoding='utf8')
    write_json(args.output / 'batch-checks.json', {'cases': results, 'scope': 'preparation_only_not_model_results'})
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
