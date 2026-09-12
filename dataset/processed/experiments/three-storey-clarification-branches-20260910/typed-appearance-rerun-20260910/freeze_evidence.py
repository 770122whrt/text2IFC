"""Preserve the failed live run and its subsequent scoped offline diagnosis."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import xml.etree.ElementTree as ET

from text2ifc_agent.artifact_scan import scan_path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[4]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, value):
    with path.open('x',encoding='utf-8') as f:
        json.dump(value,f,ensure_ascii=False,indent=2)


def main():
    run = OUT/'A-revise/runtime/runs/411166603facdde6'
    execution = read(OUT/'A-revise/execution.json')
    assert execution['status']=='exception' and not list(run.rglob('*.ifc'))
    assert not (OUT/'B-retain').exists()
    reference=OUT.parent.parent/'three-storey-human-review-20260909/generated.ifc'
    assert sha(reference)=='756cf1ad4b8175ecb2571ce09483bd6ab83edfd562ae2f66c33a650b9e610d63'
    old_count=0
    for authority in read(OUT/'admission.json')['frozen_authority_checks']:
        manifest=ROOT/authority['path']
        assert sha(manifest)==authority['sha256']
        for row in read(manifest)['files']:
            assert sha(manifest.parent/row['path'])==row['sha256'], row['path']
            old_count += 1
    target=OUT/'material-source-validation'
    target.mkdir(exist_ok=False)
    checks=[]
    for label in ['red','green','green2','public']:
        for suffix in ['xml','log']:
            source=ROOT/'.tmp'/f'material-source-{label}-20260910.{suffix}'
            shutil.copyfile(source,target/source.name)
        cases=list(ET.parse(target/f'material-source-{label}-20260910.xml').iter('testcase'))
        failed=sum(c.find('failure') is not None or c.find('error') is not None for c in cases)
        checks.append({'run':label,'testcases':len(cases),'failed_or_error_cases':failed,
                       'note':'green command named a nonexistent test file; no tests collected' if label=='green' else ''})
        if label in {'green2','public'}:
            assert cases and not failed and not any(c.find('skipped') is not None for c in cases)
    shutil.copyfile(ROOT/'.tmp/material_source_comparison.py',OUT/'diagnostics/material_source_comparison.py')
    write(target/'checks.json',checks)
    with (OUT/'REPORT.md').open('a',encoding='utf-8') as f:
        f.write('\n## 本轮结束前的离线修复\n\n')
        f.write('已在源头复用实际材料 Schema；空对象、未知字段、不完整分层和非法厚度不再被冻结为要求。失败族初次27失败/14通过；修复后与外观、语义保全合计116项通过，公共生成/语义闭环补验'+str(checks[-1]['testcases'])+'项通过。一次命令含不存在的测试文件，未收集测试，原日志保留。新检查未宣称修好错误路由或 Audit 异常收尾，也没有随后调用 Provider。\n\n')
        f.write('实际 Brief 的离线重放：原先接受20项材料（其中1项为空），现在拒绝空项并完整保留19项合法要求。详见 [重放结果](diagnostics/material-source-comparison.json) 与 [离线检查](material-source-validation/checks.json)。\n')
    links=re.findall(r'\[[^\]]+\]\(([^)]+)\)',(OUT/'REPORT.md').read_text(encoding='utf-8'))
    assert all((OUT/p).is_file() for p in links)
    scan=scan_path(OUT)
    assert scan['finding_count']==0, scan['findings']
    write(OUT/'presentation-checks.json',{'status':'failed live diagnostic; no accepted Proof',
        'links_checked':len(links),'broken_links':0,'no_ifc_output':True,'B_not_started':True,
        'reference_unchanged':True,'prior_frozen_files_unchanged':old_count,'artifact_scan':scan,
        'scan_limits':'Declared text suffixes only; not a general secret audit.'})
    files=sorted(p for p in OUT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='FILES.json')
    write(OUT/'FILES.json',{'schema_version':'text2ifc/curated-evidence-files/1.0',
        'status':'failed live attempt preserved; no accepted Proof',
        'files':[{'path':p.relative_to(OUT).as_posix(),'size_bytes':p.stat().st_size,'sha256':sha(p)} for p in files]})
    print(json.dumps({'frozen_files':len(files),'checks':checks,'old_files_unchanged':old_count,'links':len(links)}))


if __name__=='__main__':
    main()
