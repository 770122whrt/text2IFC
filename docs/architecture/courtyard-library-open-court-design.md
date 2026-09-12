# 光庭阅读馆第二版：开敞围庭、完整真实生成

> 2026-09-12 收纳更新：最新第二版已人工验收，见[光庭 Proof](../../dataset/processed/proof/generation/phase6.6/courtyard-library-20260912/REPORT.md)。第一版作为历史参考；下文保留设计/调试时点的叙述。
2026-09-12。当前执行方向，取代第一版完整盒子/封闭楼梯间的设计选择。依据为用户要求“基本做成右上角的形式即可，不需要家具和植物”，并要求修复后从中文输入重新走完真实 Provider pipeline；必要时补 Generation 柱子能力。

## 已确定的设计要求

参照[概念图右上角](../../dataset/processed/proof/generation/phase6.6/courtyard-library-20260912/evidence/concept/concept.png)的建筑关系，采用两层、后部与两翼围合、前侧真实开敞的U形阅读馆。右上角是示意，不按图中剖切推断不存在的施工细节。沿庭外露直跑楼梯连接首层与二层回廊，不能藏进实体楼梯间。二层临庭及两翼前端均有可辨认的深色细杆护栏，楼梯两侧的防护及扶手明确表达；柱梁形成沿庭节奏。保留浅暖灰主体、深灰框和有限木色；板面也指定明确颜色，不再靠米棕色主题代替定性要求。排除家具、植物和园艺造景。

24×18米外轮廓、0/3.6米楼层标高可作为委托设计起点；庭院扩大并向前开敞。后翼、两侧翼和回廊的准确范围、窗门表、柱网、楼梯落脚和到达口在真实调用前冻结，注明为Agent委托设计选择。不能为了出图改变IFC或让半透明物体伪装成空洞。基本单开门与单/双竖面板窗沿用现有合法模板，不扩推拉门或整面幕墙。

## 实际缺口与分步实施

1. **梁柱公共语义。** 编译器已有 IfcColumn / IfcBeam 拉伸表示；但当前 Expected Facts 的额外构件只主动投影 railings，梁柱可能不进入数量、分包归属和重开几何预期。先建立显式梁柱请求被漏投影的失败族，打通世界坐标明确长方体的数量/身份/归属/实际网格核对。不自动布柱、不宣称结构计算通过。
2. **受限细杆护栏。** 现有 IfcRailing 是整片拉伸，不等于已有立柱、竖杆与横向/斜向扶手模板。核对可行表达后，以单一金属材料、直线水平或直跑楼梯边为边界新增有版本的受限表示。明确高度基准、端点、杆件数量上限、间距、截面和来源；不改旧 extruded_profile 的含义，不用大量随意LLM补件或错误材料附件凑图。
3. **新设计与完整链路。** 先冻结人类语言输入、设计意图及独立预期，运行本阶段完整公共路径离线检查，包括澄清/恢复和失败不发布，再执行新的真实 Brief→Generator→必要修复→Audit→最终IFC。原第一版候选只留在历史证据，不能作为新运行起点。

独立检查包含：前侧开敞、庭院范围、楼梯与回廊实际连通、梁柱无堵门/侵占净宽、护栏杆件和坡度、门窗宿主、Type/材料/颜色、各层归属及新旧版本兼容。设计异议通过现有 design-review-context / Audit3.0保留；要求修改不等于已解决。冻结评价器只在本地使用，不送Provider。

## 运行与证据

第一版真实运行保存在[报告](../../dataset/processed/proof/generation/phase6.6/courtyard-library-20260912/evidence/v1/continuation-01/REPORT.md)，提交532a4a4c，人工未验收。原自动loop失败、确定性修复和后续真实Audit成功分别记录。

第二版使用新目录及独立输入，不覆盖旧数据。新的完整运行不复用候选；共享费用账本继续保留此前9次/750000 token，预算改变须明确说明。本段记录设计初稿时的检查点；最终输入与后续进度见下节，新的真实调用尚未执行。后续运行保留每个阶段原始响应、失败、修复原因、token和最终IFC，最终实际出图交人工检查后再决定Proof。

## 2026-09-12 实施与新输入位置

第一版532a4a4c已按用户明确授权推送。梁柱公共语义修复为7df706b2；有界细杆护栏及新版本公共接入的代码与离线验证正在收尾，尚未宣称第二版真实生成完成。

[第二版输入](../../dataset/processed/proof/generation/phase6.6/courtyard-library-20260912/evidence/v2/request.txt)已按委托设计冻结；[独立预期](../../dataset/processed/proof/generation/phase6.6/courtyard-library-20260912/evidence/v2/expected-independent.json)在Provider候选出现前建立，不作为模型输入。两层开敞U形，外露北上直梯和连接平台，20根柱、6条梁、14段水平/斜细杆护栏；不建家具植物。精确几何以冻结请求为准。

新增合同：Brief2.6→BIM JSON2.3；Draft1.3、ChangeSet1.3；basic_railing的metal-picket模板text2ifc/basic-railing/1.0。仅在新版本中允许新表示，旧版默认与Repair几何不变。实际杆件、坡向及参数来源需从重开IFC核对。完整失败/成功记录见[调试报告](../../dataset/processed/proof/generation/phase6.6/courtyard-library-20260912/evidence/v2/railing-debug/REPORT.md)。本轮是具体缺陷修复和可行性验证，不是盲测能力提升或建筑施工合规证明。
