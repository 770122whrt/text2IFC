import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
import ifcopenshell

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dataset/processed/ifc-presentation-validation/live-semantic-20260908-01'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

gen=OUT/'generation';gen.mkdir(exist_ok=False)
request='''请生成一个单层矩形接待室的完整 IFC2X3 文件，单位为毫米。室内净长 6000、净宽 4000，墙高 3000、墙厚 200，四面墙闭合。地坪顶面标高 0，厚 150，覆盖整个房间及墙底。为便于检查室内，本次明确不建屋顶或吊顶。设一个室内空间。
正南面墙正中设置一樘左单开门，宽 1000、高 2100，门底与地坪齐平。正东面墙正中设置一樘双竖面板窗，正西面墙正中设置一樘单面板窗；两窗均宽 1600、高 1200、窗台标高 900。开口与各自门窗名义宽高一致并穿透墙厚；门窗居中安装，保留窗框、玻璃、门框和门扇细节，不加外伸门套或复杂五金。
四面墙材料明确为砖，地坪材料明确为混凝土；其他构件不指定物理材料。采用 warm-residential 协调风格，窗玻璃透明、窗框与门扇有协调的部件分色。没有提供任何耐火、承重、强度、热工性能或普通属性，请不要自动添加这些属性。没有共享 Type 要求。不改变上述尺寸和位置；模型原点取室内地坪中心，X 向东、Y 向北、Z 向上。'''
(gen/'request.txt').write_text(request+'\n',encoding='utf-8')
write(gen/'frozen-expectations.json',{'frozen_at':datetime.now(timezone.utc).isoformat(),'source':'request.txt','request_sha256':sha(gen/'request.txt'),'schema':'IFC2X3','strategy':'legacy_full','counts':{'IfcWall':4,'IfcSlab':1,'IfcSpace':1,'IfcDoor':1,'IfcWindow':2,'IfcOpeningElement':3},'room_clear_size_mm':[6000,4000,3000],'wall_thickness_mm':200,'floor_top_mm':0,'floor_thickness_mm':150,'door':{'side':'south','width_mm':1000,'height_mm':2100,'sill_mm':0,'template':'door-left'},'windows':[{'side':'east','template':'window-double-vertical'},{'side':'west','template':'window-single'}],'window_size_mm':[1600,1200],'window_sill_mm':900,'materials':{'IfcWall':'砖','IfcSlab':'混凝土'},'appearance_profile':'warm-residential','unspecified_properties':'must_be_absent','type_sharing_requested':False,'purpose':'single live viability and human review, not capability benchmark'})

repair=OUT/'repair';repair.mkdir(exist_ok=False)
private=repair/'evaluator-private';private.mkdir()
source=ROOT/'dataset/external/bimnet/vvo.ifc'
shutil.copyfile(source,repair/'01-original.ifc')
m=ifcopenshell.open(str(source))
# Selection is frozen before Provider execution. No original entity is deleted.
target=m.by_guid('2CsmzAChHF6O6maGXlo6PS')
rel=next(r for r in target.IsDefinedBy if r.is_a('IfcRelDefinesByProperties') and r.RelatingPropertyDefinition.Name=='Pset_WallCommon')
ps=rel.RelatingPropertyDefinition
mutation={'source_dataset_path':source.relative_to(ROOT).as_posix(),'source_sha256':sha(source),'original_role':'private_ground_truth','frozen_at':datetime.now(timezone.utc).isoformat(),'operation':'remove_one_IfcRelDefinesByProperties_only','target_guid':target.GlobalId,'removed_relationship':rel.get_info(),'retained_orphan_property_set_guid':ps.GlobalId,'private_only':True}
# get_info includes entity handles: serialize as strings solely in private evidence.
(private/'mutation.json').write_text(json.dumps(mutation,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
m.remove(rel);m.write(str(repair/'02-damaged.ifc'))
# The public request values are read ONLY from the surviving orphan in damaged IFC.
d=ifcopenshell.open(str(repair/'02-damaged.ifc'))
orphan=d.by_guid(ps.GlobalId)
props={p.Name:p.NominalValue.wrappedValue for p in orphan.HasProperties}
public='请修复这个 IFC2X3 文件中墙体 '+target.GlobalId+' 的实例属性关联。该墙的几何、Type、材料、颜色和其他对象均须保留。请按下述明确要求写入实例 Pset_WallCommon：Reference 为字符串 "240"，IsExternal 为布尔 true，ExtendToStructure 为布尔 false，LoadBearing 为布尔 false。上述属性值也可在输入 IFC 尚存的独立 Pset_WallCommon 属性集中核对；不要修改共享 Type，不要增加其他属性，也不要更改任何几何。请输出修复后的完整 IFC。\n'
assert props=={'Reference':'240','IsExternal':True,'ExtendToStructure':False,'LoadBearing':False}
(repair/'request.txt').write_text(public,encoding='utf-8')
write(repair/'public-input-facts.json',{'source':'02-damaged.ifc only','source_sha256':sha(repair/'02-damaged.ifc'),'target_guid':target.GlobalId,'values_observed_in_surviving_orphan':props,'request_sha256':sha(repair/'request.txt')})
write(private/'frozen-expectations.json',{'original_sha256':sha(repair/'01-original.ifc'),'damaged_sha256':sha(repair/'02-damaged.ifc'),'request_sha256':sha(repair/'request.txt'),'target_guid':target.GlobalId,'pset':'Pset_WallCommon','properties':props,'original_role':'private_ground_truth','acceptance':'same direct typed values; restored property attachment; unchanged geometry, original Type/material/style and unrelated entities; relationship GlobalId need not match deleted identity','provider_inputs':['02-damaged.ifc','request.txt'],'private_inputs_forbidden':['01-original.ifc','evaluator-private'],'selection':'single preselected development viability case, not blind benchmark'})
assert sha(source)==sha(repair/'01-original.ifc')
print('Prepared frozen generation request and dataset relation-damage repair case; no Provider calls.')
