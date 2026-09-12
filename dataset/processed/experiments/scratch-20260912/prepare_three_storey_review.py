import datetime as dt
import hashlib,json
from pathlib import Path

out=Path('dataset/processed/ifc-presentation-validation/three-storey-human-review-20260909')
out.mkdir(exist_ok=False)
request='''请生成一栋三层的小型社区阅读活动楼，输出完整 IFC2X3 文件，单位毫米。首层是接待阅览厅，二层是安静阅览厅，三层是多功能活动厅，东侧为独立楼梯间。采用 warm-residential 协调风格，浅暖色墙面配深色细框，玻璃透明，入口清楚，门窗上下对齐。需要真实的窗框、玻璃面板、门框、门扇和楼梯踏步；本次不做光庭、家具、花草、机电、栏杆、复杂五金或外伸装饰。

室内净尺寸东西10米、南北8.4米，外墙厚200毫米。首层、二层、三层完成面标高分别为0、3150、6300毫米，每层净高3000毫米。地坪及两块层间楼板厚150毫米，顶面与所属层完成面齐平；平屋面底标高9300毫米、厚150毫米。地坪、楼板与屋面覆盖外墙外边界。二层和三层楼板各留一个真实穿透的楼梯洞口，不能用完整楼板封住楼梯。各层墙独立建模。

以首层室内西南角为原点，向东为X、向北为Y、向上为Z。每层西侧大厅净范围X=0～7600、Y=0～8400；分隔墙完整占X=7600～7800、Y=0～8400；楼梯间净范围X=7800～10000、Y=0～8400。三层分隔墙都保持这一完整长度，不按小平台的接邻长度缩短，也不重复建墙。每层分隔墙开一樘900宽、2100高的右单开门：首层及三层门中心距室内南边700毫米，二层距南边7650毫米；门底与本层完成面齐平。

两段直跑楼梯都位于X=8200～9400、Y=1500～6900，净宽1200毫米。第一段从首层南端向北升到二层北端，标高0到3150；第二段从二层北端反向向南升到三层南端，标高3150到6300。每段18个踢面、每个高175毫米，18个踏面、进深300毫米；两段分别属于出发楼层并连接上一层。二层及三层楼板洞口平面范围都为X=8000～9600、Y=1500～6900，分别穿透各自的150毫米楼板；屋面不留洞。二层北端Y=6900～8400为换向平台，三层南端Y=0～1500为到达平台。首层建大厅与整间楼梯间两个空间，二层建大厅与北端平台两个空间，三层建大厅与南端平台两个空间；平台的X范围都是7800～10000。共6个空间，不把楼梯洞口当成房间。

首层南墙主入口中心距室内西边3800毫米，宽1200、高2400，左单开，门底与首层地坪齐平。每层南墙两扇双竖面板窗，中心距室内西边分别为1700、5900毫米，宽1800、高1500、窗台高900。每层北墙一扇双竖面板窗，中心距西边3800毫米，宽2400、高1500、窗台高900。每层西墙一扇双竖面板窗，中心距南边4200毫米，宽1800、高1500、窗台高900。每层东墙一扇单面板窗，中心距南边4200毫米，宽900、高1800、窗台高600。窗台均从所属层完成面起算。共4樘门、15扇窗，门窗开口与名义宽高相同并穿透自己的宿主墙。

墙体物理材料为砖；地坪、两块层间楼板和屋面物理材料为混凝土。其他构件不指定物理材料，不要由木色或透明样式推断材料。未指定强度、耐火、承重、热工性能，也未要求共享Type，不要自动补属性或强制合并Type。如果有真实冲突请明确指出，不要悄悄改变尺寸、位置或关系。
'''
(out/'request.txt').write_text(request,encoding='utf-8',newline='\n')
floors=[0,3150,6300]
expected={'created_at':dt.datetime.now(dt.timezone.utc).isoformat(),
 'request_sha256':hashlib.sha256((out/'request.txt').read_bytes()).hexdigest(),
 'purpose':'new related three-storey development viability case, not blind capability comparison',
 'schema':'IFC2X3','strategy':'legacy_full','unit':'mm','storey_elevations_mm':floors,
 'net_height_mm':3000,'outer_bounds_mm':{'x':[-200,10200],'y':[-200,8600]},
 'counts':{'IfcBuildingStorey':3,'IfcSpace':6,'IfcWall':15,'IfcSlab':4,'IfcDoor':4,'IfcWindow':15},
 'door_templates':{'door-left':1,'door-right':3},'window_templates':{'window-double-vertical':12,'window-single':3},
 'floor_tops_mm':floors,'roof_bottom_mm':9300,'slab_thickness_mm':150,
 'wall_intervals_mm':{'south':[1,[-200,0]],'north':[1,[8400,8600]],'west':[0,[-200,0]],'east':[0,[10000,10200]],'partition':[0,[7600,7800]]},
 'spaces_mm':[[[0,7600],[0,8400],[z,z+3000]] for z in floors]+[[[7800,10000],y,[z,z+3000]] for z,y in zip(floors,[[0,8400],[6900,8400],[0,1500]])],
 'stairs':[{'bbox_mm':[[8200,9400],[1500,6900],[z,z+3150]],'direction':direction,'risers':18,'treads':18,'rise_mm':175,'tread_mm':300} for z,direction in [(0,'+Y'),(3150,'-Y')]],
 'openings_mm':[[[8000,9600],[1500,6900],[z-150,z]] for z in floors[1:]],
 'theme':'warm-residential','requested_materials':{'walls':'砖','slabs':'混凝土'},
 'doors':[[0,'south',3800,1200,2400,0]]+[[z,'partition',c,900,2100,0] for z,c in zip(floors,[700,7650,700])],
 'windows_per_storey':[{'side':'south','centers_mm':[1700,5900],'width_mm':1800,'height_mm':1500,'sill_mm':900},
  {'side':'north','centers_mm':[3800],'width_mm':2400,'height_mm':1500,'sill_mm':900},
  {'side':'west','centers_mm':[4200],'width_mm':1800,'height_mm':1500,'sill_mm':900},
  {'side':'east','centers_mm':[4200],'width_mm':900,'height_mm':1800,'sill_mm':600}],
 'evaluator_policy':'Read native IFC geometry/relations/materials/styles; exact requested values. A physical IfcRoof may fulfill the roof slab role. Brick/砖 and Concrete/混凝土 equivalent. No Agent coverage claims used.',
 'limits':'Schematic model excludes rails and building-code certification; no courtyard or landscaping'}
(out/'frozen-expectations.json').write_text(json.dumps(expected,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(out)
