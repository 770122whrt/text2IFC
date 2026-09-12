import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dataset/processed/ifc-presentation-validation/c-shaped-teaching-building-20260910'
OUT.mkdir(parents=True,exist_ok=False)
request='''请帮我建一栋三层的小型教学活动楼，平面做成向东敞开的C形。重点是清楚、整齐、协调，保留中间开敞空间；这次只建建筑本体，不做景观、家具、栏杆和设备，不把模型当作可直接施工的设计。

尺寸按毫米表达，下面提到的距离也给出米，方便读。以建筑外轮廓西南角为定位原点，往东、往北、往上分别是三个正方向。

建筑外包络东西13.2米、南北16.8米。西侧是一条宽4.8米、贯通南北的交通体量；北翼和南翼各向东伸出8.4米，各宽4.8米。中间东侧留出东西8.4米、南北7.2米的开敞缺口，缺口南边距建筑最南端4.8米。三层的外轮廓完全相同，屋面也跟着C形走，不能拿一个完整矩形把中间缺口盖上，也不加跨缺口的桥。

首层、二层、三层完成面标高分别是0、3.15、6.30米；各层净高3米。楼板厚150毫米，顶面与相应完成面齐平；平屋面底面在9.30米，厚150毫米。各层楼板和屋面采用连续C形轮廓。首层楼板没有楼梯洞口，二、三层按下面的楼梯要求真实开洞。

外墙及内部分隔墙统一厚200毫米，墙体全部落在外轮廓以内。外墙沿C形的八条边布置，相邻墙端部连接但不要重复堆叠。每层只有南、北两个教学活动室，以及西侧一个贯通的交通/楼梯空间，共九个空间。教学室与西侧交通空间之间的分隔墙，都放在距建筑西侧4.6到4.8米这一条带内；南室的分隔墙从南端内墙面延伸到4.8米位置，北室的分隔墙从12米位置延伸到北端内墙面。不要再分小教室。

两个教学室的净空间：南室东西4.8到13.0米、南北0.2到4.6米；北室东西4.8到13.0米、南北12.2到16.6米。交通空间的净范围为东西0.2到4.6米、南北0.2到16.6米。空间高度都取3米，与所属楼层对应。

楼梯放在西侧交通空间内，用两个在平面上并列的直跑梯段联系三层：一层到二层的梯段距建筑西侧0.4到1.6米，南北5.4到10.8米，从南向北上升；二层到三层的梯段距西侧2.8到4.0米，南北范围相同，从北向南上升。两段净宽均1.2米，每段18级、每级高175毫米，踏步水平进深300毫米；标高分别0到3.15米、3.15到6.30米。北侧平台利用二层楼板在南北10.8到12米之间的区域，南侧平台利用三层楼板在4.2到5.4米之间的区域，两处平台东西范围均0.2到4.6米，不另叠加一块实体板。二层楼板洞口只对应第一段，三层只对应第二段，洞口平面范围与各自梯段一致，穿透150毫米楼板。

每层南、北教学室各有一扇900毫米宽、2100毫米高的右单开门，都在上述分隔墙上，门中心分别距建筑南侧2.4米和14.4米，门底与本层完成面平齐。首层另设一扇1200毫米宽、2400毫米高的左单开入口门，位于西外墙中间，中心距南侧8.4米。上层不要复制这个入口门。门都带基本门框和门扇，不加复杂五金。

每层七扇窗：南教学室的南外墙、北教学室的北外墙各两扇，中心距西侧7.2米和10.8米；南教学室朝缺口的墙和北教学室朝缺口的墙各一扇，中心距西侧9米。这六扇窗均宽1800毫米、高1500毫米，采用双竖面板。西外墙再设一扇宽900毫米、高1800毫米的单面板窗，中心距南侧2.4米。所有窗台距本层完成面900毫米，窗洞、窗和宿主墙一一对应，三层上下对齐。不要在东侧两个端墙上额外加窗。

墙体明确采用砖，楼板及屋面明确采用混凝土，其他构件暂不指定物理材料。风格用现有warm-residential协调主题：暖浅墙面、深色细门窗框、通透玻璃和与框分色的门扇。不要为了视觉效果增加别的物理材料、整件颜色覆盖或性能属性。我没有要求共享Type；只保留合法表达所需的最小附件。

这些尺寸与布置是本次希望忠实表达的方案。若有必要事实缺失、输入矛盾、当前系统不支持的表达，或你认为会影响使用的明显几何问题，请先集中指出并澄清，不要自行改尺寸或补构件。最终报告应区分用户要求符合性、确定性检查和尚未验证的工程合理性；没有检测到问题也不能写成全面合规。
'''
(OUT/'request.txt').write_text(request,encoding='utf-8',newline='\n')
def write(name,obj):
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
expected=dict(schema_version='text2ifc/c-shape-review-expectations/1.0',
    author='Assistant-authored evaluation request using human engineering language; not a spontaneous external-user transcript.',
    request_sha256=hashlib.sha256((OUT/'request.txt').read_bytes()).hexdigest(),
    units='mm',storey_elevations_mm=[0,3150,6300],clear_height_mm=3000,slab_thickness_mm=150,
    footprint_mm=[[0,0],[13200,0],[13200,4800],[4800,4800],[4800,12000],[13200,12000],[13200,16800],[0,16800]],
    footprint_area_m2=161.28,roof_z_mm=[9300,9450],
    space_xy_mm=[[[4800,13000],[200,4600]],[[4800,13000],[12200,16600]],[[200,4600],[200,16600]]],
    counts={'IfcBuildingStorey':3,'IfcSpace':9,'IfcDoor':7,'IfcWindow':21,'IfcStairFlight':2},
    wall_thickness_mm=200,wall_material='brick',slab_roof_material='concrete',theme='warm-residential',
    floors_z_mm=[[-150,0],[3000,3150],[6150,6300]],
    floor_openings=[{'storey_elevation_mm':3150,'bbox_mm':[[400,1600],[5400,10800],[3000,3150]]},
                    {'storey_elevation_mm':6300,'bbox_mm':[[2800,4000],[5400,10800],[6150,6300]]}],
    stairs=[{'bbox_mm':[[400,1600],[5400,10800],[0,3150]],'direction':'north'},
            {'bbox_mm':[[2800,4000],[5400,10800],[3150,6300]],'direction':'south'}],
    window_rows_per_storey=[['south',7200,1800,1500,900],['south',10800,1800,1500,900],
        ['north',7200,1800,1500,900],['north',10800,1800,1500,900],
        ['courtyard_south',9000,1800,1500,900],['courtyard_north',9000,1800,1500,900],['west',2400,900,1800,900]],
    door_rows_per_storey=[['partition_south',2400,900,2100,0,'SINGLE_SWING_RIGHT'],['partition_north',14400,900,2100,0,'SINGLE_SWING_RIGHT']],
    entrance=[0,'west',8400,1200,2400,0,'SINGLE_SWING_LEFT'],
    no_performance_properties=True,no_unsolicited_types_materials_or_appearance=True,
    design_review=dict(preseeded_known_issue=False,reference_ifc_supplied=False,
        aim='Record spontaneously identified concerns separately from deterministic checks; no engineered conflict is planted.',
        limitation='One new scene is a prospective viability/stability observation, not a statistical success-rate estimate.'))
write('frozen-expectations.json',expected)
write('payload-preview.json',dict(status='pending_explicit_case_authorization',destination='https://api.deepseek.com',model='deepseek-v4-flash',
    request=request,request_sha256=expected['request_sha256'],
    purpose='One fresh C-shaped three-storey teaching building Generation/Audit/bounded repair loop after applicable offline admission; pause for real clarification or deterministic defect.',
    subsequent_payloads=['this case clarification conversation if approved','Design Brief','candidate JSON','automatic check feedback','runtime metadata'],
    exclusions=['A/B IFC files and evidence','private Gold','other task data','credential text','frozen evaluator expectations/checker source'],
    proposed_limits={'max_calls':32,'max_tokens':2000000,'max_active_seconds':3600},
    full_preflight=False,proof_registration='after user review only'))
print(json.dumps({'folder':str(OUT),'request_sha256':expected['request_sha256'],'request_characters':len(request)},ensure_ascii=False))
