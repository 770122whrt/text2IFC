# Brief 属性与可见楼梯外观：局部诊断

第二版第一次重跑 d2c21f51c9bb69f6 经过真实 Brief、Generator 和候选修复，未通过发布门禁，没有 Audit，也没有可交付 IFC。三次调用共369,606 token；累计13次、1,198,096 token、2158.468秒，旧失败账本保留。

## 原因与修复

1. Brief 自行增加6个 Pset_SpaceCommon.IsExternal。注册表不含该属性；室外空间应由已存在的 external 事实表达为原生 InteriorOrExteriorSpace。原路径直到候选校验才发现，迫使下游与错误冻结要求冲突。将现有 IFC2X3 属性名称、类别适用性和值类型校验抽成共享函数，在 Brief2.7 冻结前执行；明确要求的不支持属性仍需澄清，不能随意改名或丢弃。
2. 被拒候选离线编译诊断发现楼梯颜色位于无 Body 的 IfcStair，真实梯段仍用主题色。Brief2.7 拦截总装外观目标，要求现有语义修正指向原身份合同确定的梯段。校正必须保留原 RGB/透明度及作用域，不能改几何、其他语义或目标。旧版本和编译样式继承含义保持。
3. 下游修复还改变了 provenance/report 等非授权事实，fact-delta 门禁正确拦截；本轮没有放宽它来接受这个候选。

## 证据边界

- red.xml：属性失败族6失败3通过；green-01.xml：9通过。
- preservation-red.xml：11通过，是既有保全能力的控制检查，不是新增修复的红证据。
- stage-01.xml：238通过，无跳过，涵盖属性注册、公共生成、澄清/恢复、两种策略与真实编译重开（Provider为fake）。
- stair-target-red.xml：楼梯目标及保全失败族6失败1通过。
- stair-target-green.xml：118通过1失败；唯一失败为测试运行过程中修改新 Prompt 产生的瞬时 registry 哈希不一致。完整保留，修改结束后的阶段检查另记 stage-02.xml。
- frozen-brief-diagnosis.json：原始真实 Brief 不改字节重验，确认在 Generator 前拒绝上述不合法语义；附加 semantic_review 声明冲突属于正确校验结果。
- rejected-candidate-diagnostic.json：离线编译被拒真实候选，545项独立检查仅梯段颜色失败。该诊断 IFC 没有 Audit、不是最终产物、不进入 accepted Proof。
- diagnostic-wrapper-error.json：初次诊断脚本误读 CompilationResult.issues，保留错误记录。独立 IFC2X3 检查器另修正原生 NumberOfRiser 单数名称；旧检查器保持，rerun-02 承载修正版。

新增 Prompt 2.24/2.25 和语义修正1.6；旧注册内容未改。以上证明局部错误及相关离线族修复，不代表系统级能力提升。新的真实完整 loop、最终 IFC、实际视觉审查和人工验收单独记录。

最终 stage-02.xml：245通过、0失败、0跳过，224.21秒。属性与楼梯目标通用修复提交 ee94b2a4 已普通推送；下一轮准入见 rerun-02/admission.json，677个路径绑定。未运行仓库 Full Preflight。

## 第二次完整重跑与矩形格式差异

53fe782c609b1d1b 的真实 Brief 使用75,958 token、164.187秒，完整stop返回。非法属性与楼梯总装外观均未再出现；但两个 outline_ref 指向精确的 x_min/x_max/y_min/y_max 对象，而检查器要求闭合顶点数组。累计14次、1,274,054 token、2322.655秒；未调用Generator/Audit。

补充严格无损格式转换，仅限Brief2.7 wall_layout，四字段精确匹配、有限非布尔数、正宽高，记录 before/after；不改变墙体、凹轮廓、旧full-envelope或其他版本。原Provider输出保留。outline-red.xml包含一个测试导入名错误；修正测试名后outline-public-red.xml在真实公共校验边界失败。首版转换遗漏known_facts根级引用，outline-stage.xml为137通过2失败；修复后outline-stage-final.xml为139通过0失败0跳过。outline-frozen-replay.json只作离线诊断，原真实Brief经一次等价转换后0问题；不冒充新的Provider成功。

无损轮廓转换提交1e46a1fb；rerun-03 新运行包装器离线1通过（16.18秒），新准入693个路径。没有复用先前经过离线转换的Brief。
