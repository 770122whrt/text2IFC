"""Collect complete pilot sources without rewriting IFCs or repeating validation."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'src'), str(ROOT / '.deps/python312')]

import ifcopenshell

from scripts.ifc_repair.dataset_batch.engine import verify_seal, write_json
from scripts.ifc_repair.dataset_batch.pilot import write_report
from scripts.ifc_repair.dataset_batch.prompts_v2 import PROFILE
from scripts.ifc_repair.dataset_batch.validation import program_hash, sha256

SUPPORTED_PROFILES = {PROFILE, 'text2ifc/dataset-request/1.3'}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def bound_origin_program(origin, current_hash):
    recorded = read(origin / 'build.json')['configuration']['program_sha256']
    if recorded != current_hash:
        snapshot = origin / 'private/source-snapshot'
        require((snapshot / 'sha256.json').is_file(), 'ORIGIN_PROGRAM_CHANGED_WITHOUT_SNAPSHOT')
        files = read(snapshot / 'sha256.json')
        require(all(sha256(snapshot / name) == value for name, value in files.items()), 'ORIGIN_SNAPSHOT_CHANGED')
        digest = hashlib.sha256()
        for path in sorted((snapshot / 'scripts/ifc_repair/dataset_batch').glob('*.py')):
            digest.update(path.name.encode())
            digest.update(path.read_bytes())
        require(digest.hexdigest() == recorded, 'ORIGIN_SNAPSHOT_PROGRAM_MISMATCH')
    return recorded


def inspect_source(origin, source_id, repository, count, *, profile=PROFILE):
    folder = origin / 'sources' / source_id
    result = read(folder / 'result.json')
    require(result['source_id'] == source_id and result['status'] == 'complete', 'SOURCE_INCOMPLETE')
    require(len(result['cases']) == count and result['source_unchanged'] and result['source_native_passed'], 'SOURCE_COUNT_OR_STATE')
    expected = result['source_sha256']
    input_path = (repository / result['source']['input_path']).resolve()
    require(sha256(input_path) == expected == sha256(folder / 'private/reference.ifc'), 'SOURCE_SHA_CHANGED')
    native = read(folder / 'private/source-validation.json')
    require(native['passed'] and native['finding_count'] == 0 and native['express_rules'] and native['schema'] == 'IFC2X3'
            and native['ifcopenshell_version'] == ifcopenshell.version and native['input_sha256'] == expected, 'SOURCE_NATIVE_RECEIPT')
    hashes, checked = [], []
    for row in result['cases']:
        require(re.fullmatch(r'case-\d+-a\d+', row['case_id']) is not None, 'CASE_ID_INVALID')
        relative = f"sources/{source_id}/cases/{row['case_id']}"
        require(row['path'] == relative, 'CASE_PATH_INVALID')
        case = origin / relative
        require(verify_seal(case), 'CASE_SEAL_INVALID:' + relative)
        data = read(case / 'case.json')
        require(data['status'] == 'passed' and data['machine_validated'] and not data['human_reviewed']
                and not data['private_identity_leakage'] and data['source_unchanged'], 'CASE_STATE_INVALID')
        require(data['information_sufficient'] and data['wall_check_passed'] and data['independent_mesh_check_passed'], 'CASE_CHECK_STATE')
        require(data['source_sha256'] == expected and data['damaged_sha256'] == sha256(case / 'public/model.ifc'), 'CASE_SHA_MISMATCH')
        require(set(data['additional_evidence']) == {'private/prompt-check.json', 'private/wall-check.json', 'private/mesh-check.json', 'public/request.txt'}, 'CHECKS_NOT_SEALED')
        native = read(case / 'private/validation.json')
        require(native['passed'] and native['finding_count'] == 0 and native['express_rules'] and native['schema'] == 'IFC2X3'
                and native['ifcopenshell_version'] == ifcopenshell.version, 'CASE_NATIVE_RECEIPT')
        require(read(case / 'private/preservation.json')['passed'], 'CASE_PRESERVATION_RECEIPT')
        prompts = read(case / 'private/prompt-check.json')
        modes = {m for m, meta in data['prompt_templates'].items() if meta['applicable']}
        require('world' in modes and modes == set(prompts) and all(p['passed'] and not p['errors'] for p in prompts.values()), 'CASE_PROMPT_RECEIPT')
        primary = data['primary_prompt']
        require(primary in modes and sha256(case / 'public/request.txt') == sha256(case / f'public/request-{primary}.txt'), 'PRIMARY_PROMPT_MISMATCH')
        wall = read(case / 'private/wall-check.json')
        require(wall['passed'] and wall['applicable'] == row['wall_checks']['applicable'] and not wall['errors'], 'CASE_WALL_RECEIPT')
        require(read(case / 'private/mesh-check.json')['passed'], 'CASE_MESH_RECEIPT')
        manifest = read(case / 'private/mutation.json')
        require(manifest['prompt_profile'] == profile and manifest['source_sha256'] == expected
                and manifest['damaged_sha256'] == data['damaged_sha256'], 'CASE_MANIFEST_MISMATCH')
        require(row['status'] == data['status'] and row['primary_prompt'] == primary and row['deleted_counts'] == data['deleted_counts'], 'CASE_INDEX_MISMATCH')
        hashes.append(data['damaged_sha256'])
        checked.append(relative)
    return result, hashes, checked


def collect(origins, output, source_ids, repository=ROOT, *, count_per_source=4):
    origins = [Path(p).resolve() for p in origins]
    output, repository = Path(output).resolve(), Path(repository).resolve()
    if output.exists():
        raise FileExistsError(output)
    require(source_ids and len(set(source_ids)) == len(source_ids), 'SOURCE_IDS_NOT_UNIQUE')
    require(all(re.fullmatch(r'[A-Za-z0-9_-]+', item) for item in source_ids), 'SOURCE_ID_INVALID')
    require(all(not output.is_relative_to(p) and not p.is_relative_to(output) for p in origins), 'OUTPUT_OVERLAPS_ORIGIN')
    current_hash = program_hash()
    history, results, chosen, hashes, checked = [], [], [], [], []
    source_hashes = []
    profile = None
    for origin in origins:
        origin_hash = bound_origin_program(origin, current_hash)
        summary = read(origin / 'summary.json')
        origin_profile = summary['request_profile']
        require(origin_profile in SUPPORTED_PROFILES and summary['program_sha256'] == origin_hash, 'ORIGIN_PROFILE_CHANGED')
        require(profile is None or profile == origin_profile, 'ORIGIN_PROFILES_MIXED')
        profile = origin_profile
        history.append({'path': str(origin), 'report_sha256': sha256(origin / 'REPORT.md'), 'summary_sha256': sha256(origin / 'summary.json'),
                        'program_sha256': origin_hash,
                        'attempted_cases': summary['attempted_cases'], 'machine_validated_cases': summary['machine_validated_cases'], 'failed_attempts': summary['failed_attempts']})
    for source_id in source_ids:
        matches = [p for p in origins if (p / 'sources' / source_id / 'result.json').is_file()
                   and read(p / 'sources' / source_id / 'result.json')['status'] == 'complete']
        require(len(matches) == 1, 'SOURCE_ORIGIN_NOT_UNIQUE:' + source_id)
        origin = matches[0]
        result, case_hashes, case_paths = inspect_source(origin, source_id, repository, count_per_source, profile=profile)
        require(not (repository / result['source']['input_path']).resolve().is_relative_to(output), 'SOURCE_INSIDE_OUTPUT')
        source_hashes.append(result['source_sha256'])
        results.append(result)
        hashes.extend(case_hashes)
        checked.extend(case_paths)
        chosen.append({'source_id': source_id, 'origin': str(origin), 'program_sha256': bound_origin_program(origin, current_hash),
                       'result_sha256': sha256(origin / 'sources' / source_id / 'result.json')})
    require(len(set(source_hashes)) == len(source_hashes), 'DUPLICATE_SOURCE_BYTES')
    require(len(set(hashes)) == len(hashes), 'DUPLICATE_DAMAGED_BYTES')
    # All admission checks occur before creating the destination. Copies retain
    # exact evidence bytes; no IFC is opened, edited, revalidated or resealed.
    output.mkdir(parents=True)
    for selection, result in zip(chosen, results):
        source_id = selection['source_id']
        destination = output / 'sources' / source_id
        shutil.copytree(Path(selection['origin']) / 'sources' / source_id, destination)
        for row in result['cases']:
            require(verify_seal(output / row['path']), 'COPIED_CASE_SEAL_INVALID')
        spec = result['source']
        source_text = (f"# {source_id} 来源与修改说明\n\n来源：{spec.get('source_url', '见 private/source.json')}\n\n"
                       f"许可：{spec.get('license', '未由本工具确认')}；源 SHA-256：`{result['source_sha256']}`。\n\n"
                       f"2026-10-10 使用固定脚本制作独立损伤副本；具体删除与属性前后值见每例私有记录。"
                       f"原文件字节未修改，既有来源及审核标签完整保留于 private/source.json；许可条件和通知仍适用。\n\n"
                       f"本目录 private/reference.ifc 是损伤前指定的合成任务评价参考，仅供离线评估，不能作为修复系统输入。\n\n"
                       f"生成来源目录：`{selection['origin']}`；本集合复制原始文件及检查记录，未重写 IFC。\n")
        (destination / 'SOURCE.md').write_text(source_text, encoding='utf-8')
    write_json(output / 'build.json', {'schema_version': 'text2ifc/dataset-pilot-collection/1.0',
                                     'configuration': {'program_sha256': current_hash, 'request_profile': profile, 'sources': chosen, 'cases_per_ifc': count_per_source},
                                     'collector_sha256': sha256(Path(__file__)), 'provider_calls': 0, 'method': 'exact-byte copy and sealed receipt reuse'})
    summary = write_report(output, results, [], len(source_ids) * count_per_source)
    summary['history'] = {'origins': history, 'prior_attempted_cases': sum(h['attempted_cases'] for h in history),
                          'prior_failed_attempts': sum(h['failed_attempts'] for h in history),
                          'prior_passing_cases': sum(h['machine_validated_cases'] for h in history),
                          'excluded_passing_cases': sum(h['machine_validated_cases'] for h in history) - len(hashes),
                          'selection_scope': 'complete sources only; all prior failures retained; not an unbiased benchmark or a repair success rate'}
    write_json(output / 'summary.json', summary)
    integrity = {'schema_version': 'text2ifc/dataset-pilot-integrity/1.0', 'passed': True, 'sealed_cases': len(hashes),
                 'native_zero_findings_cases': len(hashes), 'prompt_checked_cases': len(hashes), 'distinct_source_sha256': len(source_hashes),
                 'distinct_damaged_sha256': len(hashes), 'source_hashes_unchanged': True, 'program_sha256': current_hash,
                 'checked_paths': checked, 'method': 'source/reference SHA, exact sealed receipt and index consistency; no repeated IFC/native/mesh evaluation'}
    write_json(output / 'integrity.json', integrity)
    snapshot_hashes = {}
    scripts = [*sorted((ROOT / 'scripts/ifc_repair/dataset_batch').glob('*.py')),
               ROOT / 'scripts/ifc_repair/audit_initial_dataset.py', ROOT / 'scripts/ifc_repair/generate_damage_pilot.py', Path(__file__)]
    for path in scripts:
        relative = path.relative_to(ROOT)
        destination = output / 'private/source-snapshot' / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)
        snapshot_hashes[relative.as_posix()] = sha256(destination)
    write_json(output / 'private/source-snapshot/sha256.json', snapshot_hashes)
    with (output / 'REPORT.md').open('a', encoding='utf-8') as report:
        report.write('\n## 本集合的生成历史与筛选限制\n\n')
        report.write(f"已有批次共生成 {summary['history']['prior_attempted_cases']} 例，其中 {summary['history']['prior_failed_attempts']} 例未通过；本集合收录 {len(source_ids)} 个完整通过母本的 {len(hashes)} 例。失败及未收录的通过例均保留在原目录。不能把筛选后的通过数当作任意 IFC 的生成成功率或修复成功率。\n\n")
        for item in history:
            link = (Path(item['path']) / 'REPORT.md').as_posix()
            report.write(f"- [生成报告](<{link}>)：尝试 {item['attempted_cases']}，通过 {item['machine_validated_cases']}，失败 {item['failed_attempts']}。\n")
        report.write('\n完整性复核见 [integrity.json](integrity.json)；冻结源码与哈希见 [private/source-snapshot](private/source-snapshot/sha256.json)。各生成版本与所收录来源绑定在 build.json 和 summary.json 的 history 中；旧版本记录仅在源代码快照通过哈希复核后沿用。本集合复用原校验记录，未重复运行原生校验或改写损伤 IFC。\n')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--origin', type=Path, action='append', required=True)
    parser.add_argument('--source-id', action='append', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cases-per-ifc', type=int, choices=range(1, 9), default=4)
    args = parser.parse_args()
    summary = collect(args.origin, args.output, args.source_id, count_per_source=args.cases_per_ifc)
    print(json.dumps({k: v for k, v in summary.items() if k not in {'sources', 'history'}}, ensure_ascii=False))


if __name__ == '__main__':
    main()
