"""Prepare two read-only demonstrations from archived genuine runs, not rerun/replay.
Only result.ifc, the separately public input and request, and an explicit provenance index
are exposed. No private reference IFC, credentials or experimental working directory.
"""
from pathlib import Path
import json
import zipfile
import ifcopenshell

ROOT=Path(__file__).resolve().parents[2]
ARCHIVE=ROOT/'dataset/processed/experiments/repair-comparison-demo-20261004/scene-b-20261007.zip'
INDEX=ARCHIVE.with_name('scene-b-20261007-index.json')
PUBLIC=ROOT/'dataset/processed/ifc-repair/repair-comparison/development'
OUT=ROOT/'ui/ifc-viewer/.artifacts/local-examples'

def main():
    index=json.loads(INDEX.read_text(encoding='utf-8'))
    assert index['archive']==ARCHIVE.name and index['real_calls']==12
    cases=[]
    with zipfile.ZipFile(ARCHIVE) as z:
        for case,kind,title,en in [('case-001','IfcWindow','补窗：同墙参照与洞口','Window and opening repair'),('case-002','IfcDoor','补门：复用现有洞口','Door in an existing opening')]:
            run_id=case+'-B'
            result_record=next(r for r in index['results'] if r['run_id']==run_id)
            assert result_record['repair_success'] is True
            candidates=[n for n in z.namelist() if n.endswith('/'+run_id+'/result.ifc')]
            if len(candidates)!=1:
                raise RuntimeError('Expected one archived output: '+repr([n for n in z.namelist() if n.endswith('.ifc') and run_id in n]))
            member=z.getinfo(candidates[0]);assert member.file_size<100*1024*1024
            source=(PUBLIC/case/'public/model.ifc').read_bytes();output=z.read(member)
            request=(PUBLIC/case/'public/request.txt').read_text(encoding='utf-8')
            assert source.startswith(b'ISO-10303-21;') and output.startswith(b'ISO-10303-21;')
            before=ifcopenshell.file.from_string(source.decode('utf-8'));after=ifcopenshell.file.from_string(output.decode('utf-8'))
            assert before.schema==after.schema=='IFC2X3'
            original={p.GlobalId for p in before.by_type('IfcProduct')}
            added=[p for p in after.by_type(kind) if p.GlobalId not in original]
            assert len(after.by_type(kind))==len(before.by_type(kind))+1 and len(added)==1
            directory=OUT/case;directory.mkdir(parents=True,exist_ok=True)
            (directory/'input.ifc').write_bytes(source);(directory/'result.ifc').write_bytes(output)
            entry={'id':case,'title':title,'title_en':en,'request':request,'evidence_class':'archived_live',
                   'recorded_at':index['created_at'],'recorded_code':index['live_code_commit'],'recorded_run':run_id,
                   'recorded_usage':result_record['usage'],'archived_success':True,'new_run_executed':False,
                   'source_record':INDEX.relative_to(ROOT).as_posix(),'archive_member':candidates[0],
                   'added':[{'global_id':p.GlobalId,'name':p.Name,'ifc_class':p.is_a()} for p in added]}
            (directory/'metadata.json').write_text(json.dumps(entry,ensure_ascii=False,indent=2),encoding='utf-8')
            cases.append(entry)
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'catalog.json').write_text(json.dumps({'examples':cases,'scope':'read-only archived successes; not new live calls'},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'prepared':len(cases),'cases':[{'id':e['id'],'archive_member':e['archive_member'],'kind':e['evidence_class']} for e in cases],'model_calls':0},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
