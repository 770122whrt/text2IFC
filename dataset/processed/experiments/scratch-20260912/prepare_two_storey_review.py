import datetime as dt
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
out = root / 'dataset/processed/ifc-presentation-validation/two-storey-human-review-20260908'
out.mkdir(exist_ok=False)
request = '''请设计并生成一栋两层的小型社区阅读与活动楼，提供完整 IFC2X3 文件，单位毫米。首层是接待阅览厅，二层是安静的多功能活动厅，东侧设置独立楼梯间。希望它看起来像一栋完整的小建筑：立面门窗上下对齐、间距均衡，墙体、门窗框和门扇配色协调，有真实的窗框、玻璃、门框、门扇与楼梯踏步。采用 warm-residential 风格，玻璃透明；不要求家具、机电、栏杆、复杂五金或外伸装饰。

建筑内部净尺寸为东西 9 米、南北 8 米，外墙厚 200 毫米。首层完成面标高 0，二层完成面标高 3150，每层室内净高 3000。地坪和二层楼板厚 150；平屋面底标高 6150、厚 150。地坪、楼板和屋面覆盖外墙外边界；二层楼板须留实际楼梯洞口，不能用整块楼板封住楼梯。各层外墙独立，不能跨楼层复用。

以首层室内西南角为原点，向东为 X、向北为 Y、向上为 Z。每层西侧大厅净范围为 X=0～6800、Y=0～8000；分隔墙占 X=6800～7000，东侧楼梯间净范围为 X=7000～9000、Y=0～8000。首层在分隔墙南端开一樘门，中心距室内南边 600；二层在分隔墙北端开一樘门，中心距室内南边 7300，两樘门均宽 900、高 2100，右单开，底面与本层地坪齐平。只生成这一道分隔墙，不把大厅与楼梯間的边界重复建成两道墙。

楼梯沿北向直跑，从首层完成面 0 升到二层完成面 3150，属于首层并连接二层。净宽 1200，平面范围 X=7400～8600、Y=1200～6600，18 级、每级高 175、踏步进深 300。首层南端保留 1200 深的进梯区域，二层北端保留 Y=6600～8000 的平台。二层楼梯洞口范围为 X=7200～8800、Y=1200～6600，洞口穿透楼板。首层为阅览厅和楼梯间各建一个空间，二层为活动厅及北端楼梯平台各建一个空间；洞口不得当成房间。

主入口位于首层南墙，中心距室内西边 3400，宽 1200、高 2400，左单开，门底与地坪齐平。南立面每层各有两扇双竖面板窗，中心距室内西边分别为 1500、5300，均宽 1800、高 1500、窗台高 900；上下层窗中心对齐，首层入口在两窗之间。每层北墙在西侧大厅中部各有一扇宽 2400、高 1500 的双竖面板窗，中心距西边 3400、窗台高 900。每层西墙中央各有一扇宽 1800、高 1500 的双竖面板窗，中心距南边 4000、窗台高 900。每层东墙中央各有一扇宽 900、高 1800 的单面板窗，中心距南边 4000、窗台高 600。窗台高度均从所属楼层完成面算起。总计 3 樘门、10 扇窗，每个开口必须与门窗名义宽高相同并穿透自己的宿主墙，门窗均置于相应楼层。

墙体材料为砖；地坪、二层楼板和屋面材料为混凝土。其他构件不指定物理材料，不要由颜色推断木材或玻璃材料。未提供强度、耐火、承重或热工性能，也没有共享 Type 的要求，不要自动补写这些属性或强制合并 Type。尺寸及空间关系必须满足以上要求；如果有真实冲突，请明确指出，不要静默改变。
'''
(out / 'request.txt').write_text(request, encoding='utf-8')
frozen = {'created_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'request_sha256': hashlib.sha256((out/'request.txt').read_bytes()).hexdigest(),
    'purpose':'new development viability Proof; not blind capability comparison',
    'schema':'IFC2X3', 'strategy':'legacy_full', 'unit':'mm', 'storey_elevations_mm':[0,3150],
    'net_height_mm':3000, 'outer_bounds_mm':{'x':[-200,9200],'y':[-200,8200]},
    'counts':{'IfcBuildingStorey':2,'IfcSpace':4,'IfcWall':10,'IfcSlab':3,'IfcDoor':3,'IfcWindow':10},
    'door_templates':{'door-left':1,'door-right':2}, 'window_templates':{'window-double-vertical':8,'window-single':2},
    'floor_tops_mm':[0,3150], 'roof_bottom_mm':6150, 'slab_thickness_mm':150,
    'stair':{'bounds_mm':{'x':[7400,8600],'y':[1200,6600],'z':[0,3150]},'risers':18,'rise_mm':175,'tread_mm':300},
    'floor_opening_mm':{'x':[7200,8800],'y':[1200,6600],'z':[3000,3150]},
    'theme':'warm-residential', 'requested_materials':{'walls':'砖','slabs':'混凝土'},
    'unrequested_materials_properties':'must be absent except internal provenance and minimum IFC attachments',
    'windows_per_storey':[{'side':'south','centers_mm':[1500,5300],'width_mm':1800,'height_mm':1500,'sill_mm':900},
        {'side':'north','centers_mm':[3400],'width_mm':2400,'height_mm':1500,'sill_mm':900},
        {'side':'west','centers_mm':[4000],'width_mm':1800,'height_mm':1500,'sill_mm':900},
        {'side':'east','centers_mm':[4000],'width_mm':900,'height_mm':1800,'sill_mm':600}],
    'limits':'schematic architectural model, no furniture, MEP, rails or complex hardware; physical construction compliance not evaluated'}
(out / 'frozen-expectations.json').write_text(json.dumps(frozen,ensure_ascii=False,indent=2),encoding='utf-8')
print(str(out))
