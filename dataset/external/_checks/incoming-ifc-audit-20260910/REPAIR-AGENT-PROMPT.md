# 给执行 Agent 的 Prompt：新增 IFC 合规修复与复验

请在 `E:\code for project\bimnet` 的 text2IFC 仓库中执行下面的任务。你负责确定性数据修复与验证，不是改写项目的 LLM/Agent 生产链路。

## 一、目标与已确认事实

主要目标：处理两个新增 ZIP 中 IFC 的合规缺陷，交付修复副本、逐文件结果和明确的阻断项。先小样本验证修复规则，再按问题类型有条件扩大；不要为了得到通过数量而降低标准、删模型内容或伪造语义。

输入 ZIP 原地只读：

```text
dataset/external/ResBIM_IFC2X3_50.zip
dataset/external/Text2IFC_29RVT_IFC2X3_NoGrid_Full.zip
```

第一个 ZIP 是 50 个 ResBIM 转换 IFC。第二个 ZIP 是 29 个新转换 IFC 加 1 个原有 Circular IFC，实际 30 个。合计 80 个 IFC 文件、79 个转换结果，不是 80 个独立建筑。

IFC-bench 与 ResBIM 是不同来源。IFC-bench 历史登记 50 个 IFC，用户主动排除了 `projects/sixty5/arc.ifc`、`projects/sixty5/plumbing.ifc` 两份过大文件，当前本地 48 个，其中 25 个 IFC2X3。原因已确认，不要重新问用户，也不要恢复或下载这两份文件。具体历史体积阈值未知，不作推定。

## 二、阅读与工作范围

先确认当前工作区、分支、工作树及并行修改，读取适用 AGENTS.md、`docs/how-to/agent-takeover.md`、`docs/README.md`，再读取 dataset 说明、manifest 规则和以下检查材料：

```text
dataset/external/_checks/incoming-ifc-audit-20260910/HANDOFF-SUMMARY.md
dataset/external/_checks/incoming-ifc-audit-20260910/README.md
dataset/external/_checks/incoming-ifc-audit-20260910/summary.json
dataset/external/_checks/incoming-ifc-audit-20260910/verified-register.json
dataset/external/_checks/incoming-ifc-audit-20260910/inventory.json
dataset/external/_checks/incoming-ifc-audit-20260910/member-v2-*.json
scripts/dataset/check_incoming_ifc_archives.py
scripts/dataset/summarize_incoming_ifc_checks.py
tests/dataset/test_incoming_ifc_archives.py
schemas/ifc/IFC2X3_TC1.exp
```

先读汇总，再按问题读取必要的单文件记录，不把全部 JSON 原文一次性塞入上下文。核对实际安装的 Python、IfcOpenShell/IfcPatch 版本和接口，优先使用仓库 .venv。

现有检查材料已迁入 external；旧 `dataset/processed/review/incoming-ifc-audit-20260910/` 不再存在。历史 JSON 中的旧路径通过新目录的 migration.json 映射，不改写历史机器证据。member-000 至 member-004 是旧检查器失败记录；member-v2-020 是一次深入检查超时，不能当作模型空输出。

允许新增确定性脚本、聚焦测试和本任务的独立修复产物。产物放在：

```text
dataset/external/_repairs/incoming-ifc-repair-<唯一运行编号>/
```

按来源与模型编号组织原始副本、修复副本及报告；脚本仍放 scripts/dataset，测试放 tests/dataset。本目录是派生候选，不是正式来源清单。不要移动或覆盖源 ZIP、源 IFC、已有审计报告、既有 Proof 或别人的工作，不改 canonical manifests、训练划分、生产 Prompt/Schema/RepairAPI，不 commit/push。仅可在本轮新建目录内安全读取所需 ZIP 成员副本，检查成员路径、同名冲突与体积，不无条件 extractall，也不直接执行包内附带脚本。

## 三、现有检查结果：必须复核，不盲信

全部 79 个转换文件都被报告存在：文件内 GlobalId 重复、IfcSIUnit.Name 缺失、FILE_NAME.originating_system 缺失。另有其他属性或逆关系错误，须从逐文件证据重新归类。

全体 80 个 IFC 已解析为 IFC2X3，Grid/GridAxis 均为 0。79 个转换结果中有 70 个小于 10 MiB 且有主体形状、4 个超限、5 个无主体形状。严格阈值为 `< 10,485,760 bytes`，不是 ZIP 压缩大小。Circular 单列为未修改的技术对照。

深入属性/基数/逆关系/唯一性检查已覆盖 75 个未超限转换文件及 Circular；4 个超限文件只完成基础解析与直接字段检查。几何仅为有限抽样，共 1,660 个构件未报错。没有完成全量 EXPRESS 规则、全模型几何、RVT 转换完整性、屋顶完整性和许可终审。

先在少量文件中复现并核对 schema 定义。若检查器误报、日志归因不准或假设错误，先修检查器并保留新旧证据，不按错误报告改 IFC。错误分类使用真实规则、实体类型、STEP ID 与解析内容交叉核对，不仅依赖 logger 可能残留的 attribute 字段。不要把 parse 成功、错误数下降或一次往返重开当作合规完成。

## 四、修复顺序与边界

### A. 先诊断根因和问题族

先区分缺陷发生于转换输出、Grid 清理、其他后处理还是检查器。只有实际存在未清理输出或源 RVT/日志时才做对应比较；没有原始输出就保留根因未定，不能把猜测写成结论。不默认重新转换、联网下载模型或安装更换依赖。

建立“规则—受影响类型—文件范围—修复前提—保留性风险”清单。先选 ResBIM `0.ifc` 与 `RVT-001__LittleHouse__IFC2X3_NoGrid.ifc` 两个小样本；有理由可以换代表样本，但需说明。使用只读源及独立输出，不复写输入。

### B. 针对已确认缺陷做最小修复

GlobalId：只处理同一文件内违反唯一性的冲突，不重生成全部 GUID，不把不同文件/不同版本共享 GUID 当成单文件格式错误。先列出每个冲突对象的类型、STEP ID、名称和引用关系，制定可重复的保留/改号规则。优先保持已有合法构件 ID；物理构件身份归属不明确时阻断，不随意选一个保留。不要因重复 GUID 合并或删除不同属性集。记录 `(来源文件, 原STEP ID, 原GlobalId) -> 新GlobalId` 的逐实体映射，单独以旧 GUID 作键不够。保持关联关系、属性内容和未涉及实体不变；重新运行修复不能再次改号。IfcPatch RegenerateGlobalIds 可作参考，但默认会重生成全部 ID；必须明确 only_duplicates 行为并核对当前版本与本项目身份保留要求，不能直接无参数套用。

单位：逐项核对 UnitType、Name、Prefix、项目单位、量值/属性单位及可用导出证据。仅在正确补值可确定时修复；不能把体积单位补成 METRE，不能统一清空 Prefix 或重标数值。记录补值依据并检查量纲和尺度。存在歧义时报告单位未决并阻断相关修复，不用近似几何尺寸猜单位。对原本无法确定的单位，不宣称修复前后的物理意义已经被证明等价。

文件头：补写应真实反映可核对的生成或当前规范化过程，保留原值与依据；不要伪造 Revit 等软件来源或编造版本。

其他 schema 缺陷：逐规则定位，先补能复现的聚焦测试。孤立定位或关系问题必须检查完整引用图；没有直接 PlacesObject 引用不意味着不被子定位使用。不能用广泛清理、删属性/材质/关系、把未知引用改成 $ 等手段消掉报错。

### C. 样本验收、交叉复验后才扩大

样本修复后，使用独立验证路径，不读取修复器自报 success 作为验收。先确认两份代表样本已覆盖的问题族通过，再选择至少两份未用于规则设计的同族文件复验。新增问题族需要自己的代表样本和测试。满足同样修复前提的文件才可加入批处理；预计优先池是 70 个小体积有主体转换文件，但最终数量据实统计。

出现未知错误、单位/身份歧义或保留性失败时，立即暂停相关写入并报告，不扩散同一策略到其他文件。不得把样本通过或修复器退出码 0 推断成所有文件通过。

## 五、复验要求

修复前后用同版本、同一套验证规则和同一份样本选择策略比较，保存完整错误及解析日志。原 IFC 是不合规基线，不要求修复前无错误，但不能新增错误；最终仍有阻断项则保持未通过。

验证至少包括 IFC2X3 解析与磁盘写出后重开、GlobalId 格式及文件内唯一性、必填字段/属性类型/基数/逆关系、STEP 引用、Grid/Axis 清零、对象与楼层归属及门窗关系保留。用实际启用的 EXPRESS 规则补验，并记录规则执行范围、版本、失败、超时或不支持项；不能声称取得完整标准认证。

对两个小样本尽量检查全部有主体构件几何；扩大处理时记录每文件的几何总数、尝试数、成功数、失败数和未执行数。比较修复前后的构件数量和身份、几何表达及坐标、可稳定比较的形状/包围盒/尺度、门窗宿主关系、材质与颜色、Pset/QTO 内容。只允许预先声明的字段差异。无法验证的部分明确标记，不将抽样升级为全模型通过。

补充修复器幂等性、源文件未改、失败不发布半成品、未知错误拒绝修复、单位歧义不猜测、GUID 最小变更等测试。复用既有来源身份记录，不无理由重跑全仓库内容哈希或 Full Preflight；运行本任务聚焦测试即可，测试不足不得夸大结论。

## 六、其他问题独立登记，不伪装修复完成

4 个超限：RVT-004、005、011、012。保留诊断，当前不删除构件、裁切模型或关闭属性来凑体积。

5 个无主体：RVT-002、013、020、022、023。记录为可解析但无主体形状的输出，不能凭空造几何或断言源 RVT 为空。

变体：保留 model_family/variant 关联和来源证据；已有 12 对高 GUID 重合仅是线索，不能仅凭名称、大小或 GUID 重合率确认独立建筑数。不得将原文件与修复副本分别算两个模型。

依赖：RVT-025、026、028 有来源包缺依赖记录；RVT-008、022 链接导出未确认。区分原 RVT 转换缺依赖、IFC 纹理/外部资源依赖和检查环境缺依赖，不能混为一谈。不擅自补下载。

屋顶：ResBIM 50 个未发现 IfcRoof 或 ROOF 类型 IfcSlab，仅作为语义待审；没有几何或源模型证据时，不创建屋顶、不强行改分类。

拓扑：部分门窗缺 Fills 链是审核信号，先核对实际构件表达，不一律补洞；无填充 Opening 也不能自动视为错误。

许可：格式和几何修复不改变来源授权，训练与再分发权限继续未准入。技术通过、模型内容合适、独立性确认和许可通过分开登记，不能做一个含混的 accepted 标记。

## 七、交付

在本轮独立输出目录交付：中文 README/REPORT，问题分类与修复规则，逐文件 before/after 结果，逐实体变更和 GUID 映射，修复副本，可复现脚本与聚焦测试，失败/超时记录，以及仍待审核清单。为 80 个输入成员保留明确去向：修复、对照、超限、无主体或阻断；不因失败而从分母中消失。

最终直接汇报：实际检查及处理数量、通过哪些技术检查、修复了什么、哪些内容确认未变化、剩余问题、变体/依赖/屋顶/许可状态、准确产物路径，以及后续正式登记建议。不要改现有 canonical manifests，也不要把全部小体积文件直接计成合规建筑。

先输出你对目标和边界的简短确认，然后实际进行诊断、样本修复与验证；不是只回复计划。不重复询问已经明确的文件位置、数量、IFC-bench 排除原因或是否允许制作修复副本。

## 技术参考

以下为官方接口参考，应结合本机安装版本和 IFC2X3 schema 核对，而不是照搬参数或忽略检查边界：

```text
https://docs.ifcopenshell.org/autoapi/ifcopenshell/validate/index.html
https://docs.ifcopenshell.org/autoapi/ifcpatch/recipes/RegenerateGlobalIds/index.html
```
