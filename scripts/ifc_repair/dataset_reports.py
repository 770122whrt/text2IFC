"""Project the immutable delivery authority into the one current human report.

This entry reads JSON and hashes files. It never opens IFCs, runs native/mesh,
changes authority receipts, or calls a Provider. Current views are replaceable;
the first-pass report must already be preserved in private/history.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

SCHEMA = 'text2ifc/dataset-report-projection/1.1'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_counts(data):
    """Fail closed on inconsistent totals; partial deliveries remain reportable."""
    try:
        rows = data['per_mother']
        active = [row for row in rows if row['active'] is True]
        rounds = data['rounds']
        passed = (data['schema_version'] in {'text2ifc/dataset-offline-delivery/1.1',
                                           'text2ifc/dataset-offline-delivery/1.2',
                                           'text2ifc/dataset-offline-delivery/1.3'}
            and data['status'] == 'complete'
            and len(rows) == data['historical_source_models'] == 41
            and len({r['source_id'] for r in rows}) == len(rows)
            and len(active) == data['active_source_models'] == 40
            and data['pairs_per_ifc'] == 30 and data['target_pairs'] == 1200
            and all(type(r['total_pairs']) is int and 0 <= r['total_pairs'] <= 30
                    and r['cap'] == 30 and r['missing_pairs'] == 30-r['total_pairs'] for r in active)
            and sum(r['total_pairs'] for r in active) == data['pairs']
            and sum(r['distinct_damages'] for r in active) == data['distinct_damages']
            and sum(r['total_pairs'] > 0 for r in active) == data['source_models']
            and data['missing_pairs'] == 1200-data['pairs']
            and data['quota_complete'] is (data['missing_pairs'] == 0)
            and all(sum(r[key] for r in rounds) == data[key]
                    for key in ('pairs', 'distinct_damages', 'attempted_cases', 'failed_attempts'))
            and sum(data['damage_families'].values()) == data['distinct_damages']
            and all(sum(data[key].values()) == data['pairs']
                    for key in ('locator_modes', 'pair_task_kinds', 'budget_levels')))
    except (KeyError, TypeError):
        passed = False
    if not passed:
        raise ValueError('REPORT_COUNT_MISMATCH')
    return True


def _table(headers, rows):
    return '\n'.join(['|'+'|'.join(headers)+'|', '|'+'|'.join(['---']*len(headers))+'|',
                      *('|'+'|'.join(str(value) for value in row)+'|' for row in rows)])


def _reason(attempt):
    errors = attempt.get('errors', {})
    text = json.dumps(errors, ensure_ascii=False)
    if 'Only entities with ids' in text and 'IfcParameterValue' in text:
        return '历史内联值id=0几何守卫异常'
    if errors.get('walls') or 'OPENING_CLOSURE_UNCONFIRMED' in text or 'UNCUT_WALL_INTERIOR_UNCONFIRMED' in text:
        return '墙内部/闭洞证据未确认'
    if 'BASIC_SHAPE_WITH_SURVIVING_PEER' in text:
        return '基本形状与存活参照规则冲突'
    if errors.get('native'):
        return 'native未通过'
    if errors.get('preservation'):
        return '保全未通过'
    if errors.get('meshes'):
        return '保留网格未通过'
    if errors.get('duplicate_damaged_bytes') or 'DUPLICATE_DAMAGE' in text:
        return '重复损伤字节'
    if errors.get('prompts'):
        return '请求检查未通过'
    return '其他异常（见原始失败记录）'


def project(batch, *, sample_review, preservation_review):
    batch = Path(batch).resolve()
    authority_path = batch/'private/finalization/summary.json'
    data = read(authority_path)
    validate_counts(data)
    for path, expected in data['authority_sha256'].items():
        if digest(path) != expected:
            raise ValueError('REPORT_AUTHORITY_CHANGED')
    sample, preserved = read(sample_review), read(preservation_review)
    if sample.get('passed') is not True or preserved.get('passed') is not True:
        raise ValueError('FINAL_SAMPLE_OR_PRESERVATION_PENDING')
    history = batch/'private/history/first-pass-20261011'
    if not all((history/name).is_file() for name in ('REPORT.md', 'summary.json')):
        raise ValueError('FIRST_PASS_REPORT_HISTORY_REQUIRED')
    catalogue = read(batch/'private/finalization/catalogue.json')['historical_sources']
    extras = {}
    for name in ('extension-r2', 'property-tail-r3'):
        for path in (batch/'private'/name).glob('sources/*/mother-summary.json'):
            row = read(path)
            extra = extras.setdefault(path.parent.name, {'added_pairs':0, 'borrowed_pairs':0})
            for key in extra:
                extra[key] += row.get(key, 0)
    # The single-source tail writes one round summary, rather than mother summaries.
    if data.get('property_tail_pairs'):
        extra = extras.setdefault('formal-041', {'added_pairs':0, 'borrowed_pairs':0})
        extra['added_pairs'] += data['property_tail_pairs']
    failures = Counter()
    for name in ('production', 'supplement-r1', 'extension-r2', 'property-tail-r3'):
        for path in (batch/'private'/name).glob('sources/*/result.json'):
            failures.update(_reason(a) for a in read(path)['attempts'] if a['status'] == 'failed')
    if sum(failures.values()) != data['failed_attempts']:
        raise ValueError('REPORT_FAILURE_HISTORY_MISMATCH')
    licenses = Counter(str(item['source'].get('license', 'unknown')) for item in catalogue if item['active'])
    quota = '已填满' if data['quota_complete'] else f"尚缺{data['missing_pairs']}题，按实际通过数量交付"
    lines = [
        '# text2IFC 批量损伤数据集：完整报告', '',
        f"当前交付为 **{data['pairs']}个IFC＋请求对、{data['distinct_damages']}份不同损伤IFC**；"
        f"{data['active_source_models']}个有效母本，每母本上限30题，目标1,200题，{quota}。"
        '派生题标注**机器校验、人工待审**，不继承母本的人审状态。', '',
        '[公开交接CSV](public/inputs.csv) · '
        '[新抽样报告](private/reviews/spot-20261011-final/REPORT.md) · '
        '[不可变数量与交付回执](private/finalization/summary.json) · '
        '[配对映射](private/finalization/pairs.json)', '',
        '本报告和根summary.json只投影机器权威。原首轮报告保存在private/history/first-pass-20261011；'
        '原母本、已通过题包、checkpoint和失败历史均保留。所有产物仍在此根目录，目录名中的25是首轮配额。', '',
        '## 各制作回合与去重', '',
        _table(['回合','新增配对','新损伤IFC','补录定位变体','落盘尝试','失败'],
               [(r['name'],r['pairs'],r['distinct_damages'],r.get('borrowed_pairs',0),
                 r['attempted_cases'],r['failed_attempts']) for r in data['rounds']]), '',
        f"合计{data['attempted_cases']}次落盘尝试、{data['failed_attempts']}次失败。"
        f"追加补录{data['borrowed_pairs']}条旧损伤的另一种适用定位，另产生"
        f"{data['extension_new_damage_pairs']+data.get('property_tail_pairs',0)}个新损伤配对、"
        f"{data['extension_new_damages']+data.get('property_tail_new_damages',0)}份新损伤IFC。"
        '定位变体可复用同一损伤字节；同一损伤/同一模式、不同损伤配方及损伤SHA均去重。', '',
        '## 来源与formal-028替补', '',
        '保存41份历史母本记录，有效集合为40份：formal-028保留为零题历史，formal-041接续其母本角色，'
        '未重命名或覆盖原028。028的84根柱放置原点相同，实际位置在各Body内部偏移；'
        '当前原点定位合同不能唯一指向它们，不表示柱几何重叠或IFC未通过native。', '',
        'formal-041使用已登记的Jesse.1元数据修正副本，2,721,491字节、IFC2X3、GPL-3.0-or-later；'
        '上游原件、修正副本、许可及修正过程分别绑定。缓存检查未发现其源SHA、场景族及可出题构件网格'
        '与旧40母本重合；不能据此宣称40个独立建筑。已知补墙失败墙上的3个删除目标已排除。'
        '[替补来源报告](private/reviews/replacement-intake-20261011/REPORT.md)给出7条许可文件绑定及容量检查范围。', '',
        '041追加轮实际通过28题：10份纯属性、2份删门和2份删门＋属性修改损伤，各有两种适用定位。'
        '16次补墙未确认的尝试不收录。原配方排序在30次尝试内未覆盖足量属性候选，'
        '因此按剩余缺口另开纯属性尾轮，复用相同校验门槛、跳过已试配方并保存独立预算与游标；'
        '这不是IFC不合规或属性容量不足。'
        f"尾轮实际收录{data.get('property_tail_pairs',0)}题、"
        f"{data.get('property_tail_new_damages',0)}份新损伤。", '',
        '有效母本许可计数：'+ '，'.join(f'{k}={v}' for k,v in sorted(licenses.items()))+'。'
        '母本原有人审标记保留；新增派生题均机器校验。当前完成本地实验交接，未建立公开发布、训练或盲测准入。', '',
        '## 校验与抽样范围', '',
        f"每份收录损伤制作时通过IfcOpenShell 0.8.5的IFC2X3 schema＋EXPRESS、公开请求信息、精确保全、"
        f"适用闭洞及保留网格检查，并保存封存。共有{data['removed_openings_checked']}个被删洞口，"
        f"{data['wall_checked_damages']}份损伤进行了适用闭洞检查。"
        '交付核对母本、缓存、程序、seal和公开文件哈希，复用原生回执，不重复运行全部native或网格。', '',
        f"本次固定分层便利抽样复核{sample['case_count']}份损伤、{sample['request_count']}条请求；"
        f"fresh native＋EXPRESS {sample['native_passed_cases']}/{sample['case_count']}，零findings，"
        f"删除合同复核{sample['contract_passed_cases']}/{sample['case_count']}，"
        f"最终公开请求实物复查{sample['final_public_passed_requests']}/{sample['request_count']}。"
        '补墙重验由独立审核者使用同一算法，不能称为独立算法验证。抽样不代表总体通过率，'
        '没有运行修复系统或Provider，不能给出系统恢复成功率。', '',
        '生成请求1.3原封存继续保留；公开交付使用1.4固定说明，明确构件放置基点、单位、完整参照Body内部偏移、'
        '局部轴和旋转顺序。目标正文保持原字节；前缀换行差异另记，不从Gold补答案。'
        '公开坐标与几何尺寸最多三位小数，仍采用墙Name/大体方位或世界坐标单一定位，不引入楼层局部定位。', '',
        f"独立保全见证核对{preserved['files_checked']}个旧文件，首尾变化{len(preserved['changed_files'])}个；"
        '包含原源字节、准入缓存、旧checkpoint/result/失败ledger、690个已接受seal和冻结程序。'
        '[保全回执](private/reviews/extension-preservation-20261011/after.json)；'
        '主工作区的并发代码漂移记录保留，实际制作与交付从各自冻结运行时加载项目模块。', '',
        '## 逐母本数量', '',
        _table(['母本','有效','配对','不同损伤','本轮追加','补录变体','累计失败','状态'],
            [(r['source_id'],'是' if r['active'] else '否',r['total_pairs'],r['distinct_damages'],
              extras.get(r['source_id'],{}).get('added_pairs',0),
              extras.get(r['source_id'],{}).get('borrowed_pairs',0),r['failed_attempts'],r['status'])
             for r in data['per_mother']]), '',
        '缺额说明：'+ ('无；40个有效母本均达到30题。' if data['quota_complete'] else
            '；'.join(f"{r['source_id']}缺{r['missing_pairs']}题（{r['stop_reason']}）"
                     for r in data['per_mother'] if r['active'] and r['missing_pairs'])) , '',
        '## 题型、定位与失败历史', '',
        _table(['损伤族','不同损伤IFC'],sorted(data['damage_families'].items())), '',
        '配对定位：'+json.dumps(data['locator_modes'],ensure_ascii=False)+'；题型：'+
        json.dumps(data['pair_task_kinds'],ensure_ascii=False)+'；预算档：'+
        json.dumps(data['budget_levels'],ensure_ascii=False)+'。', '',
        _table(['失败归因','次数'],sorted(failures.items())), '',
        '旧id=0几何守卫异常已由单独版本修正；原负记录不删除。闭洞未确认和请求规则冲突均不收录。'
        '预筛拒绝不计落盘尝试；中断或写出失败仍占预算并保留配方、错误、日志和candidate_cursor。'
        '同一冻结命令可从本轮checkpoint继续，不覆盖成功题或重置预算。', '',
        '尾轮曾在启动配置核对处被旧交付器拦截：原调度按首轮清单索引递增随机种子，旧核对器误用统一种子。'
        '新交付1.3按冻结调度公式派生每母本预期种子，并交原校验器完整核对配置；补充轮沿用首轮母本种子。'
        '原配置和程序不改写，启动红记录单独保留，不算作损伤落盘尝试。', '',
        '## 规范交接', '',
        f"只向被测系统挂载public/，其中{data['pairs']}对、{2*data['pairs']+1}个文件："
        '每题model.ifc＋request.txt及一份inputs.csv。CSV六列为 '
        '`case_id,ifc_path,request_path,level,primary_target_count,task_kind`；'
        '私有来源、完整参考IFC、Gold、配方、失败和评分映射不提供给被测系统。', '',
        '同一实例多项属性修改只算一个主要目标，洞口与关系不计；1/2/≥3目标分别为S1/S2/S3，'
        '预算1.5M/2M/2.5M。定位变体按damage分组，母本及已知建筑族仍需隔离开发和评估。'
        '没有执行实验侧prepare、真实模型调用或修复实验。脚本入口、续跑及历史记录见'
        '[脚本说明](../../../../docs/validation/ifc-repair-dataset/README.md)。', '']
    projection = {**data, 'projection_schema':SCHEMA, 'projection_program_sha256':digest(__file__),
        'machine_authority':'private/finalization/summary.json',
        'machine_authority_sha256':digest(authority_path), 'sample_review':str(Path(sample_review).resolve()),
        'sample_review_sha256':digest(sample_review), 'preservation_review':str(Path(preservation_review).resolve()),
        'preservation_review_sha256':digest(preservation_review), 'provider_calls':0,
        'human_review':'pending_human_review', 'validation_label':'machine_validated'}
    (batch/'REPORT.md').write_text('\n'.join(lines),encoding='utf-8')
    (batch/'summary.json').write_text(json.dumps(projection,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return {'status':'complete','pairs':data['pairs'],'distinct_damages':data['distinct_damages'],
            'quota_complete':data['quota_complete'],'report':str(batch/'REPORT.md')}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batch',type=Path,required=True)
    parser.add_argument('--sample-review',type=Path,required=True)
    parser.add_argument('--preservation-review',type=Path,required=True)
    args=parser.parse_args(argv)
    print(json.dumps(project(args.batch,sample_review=args.sample_review,
        preservation_review=args.preservation_review),ensure_ascii=False))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
