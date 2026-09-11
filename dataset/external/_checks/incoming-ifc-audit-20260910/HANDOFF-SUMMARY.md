# IFC 数据检查交接：数量、问题与处理建议

日期：2026-09-10。仓库：`E:\code for project\bimnet`；项目名称：text2IFC。

## 1. 本次已落实的更正与迁移

用户确认：IFC-bench 的 `projects/sixty5/arc.ifc`、`projects/sixty5/plumbing.ifc` 是因体积过大而主动排除，不是意外丢失。已在 `dataset/manifests/external-corpora.json` 登记用户确认来源和不自动恢复策略。具体历史排除阈值未提供，不能反推为 10 MiB。

检查材料已从 `dataset/processed/review/incoming-ifc-audit-20260910/` 迁至 `dataset/external/_checks/incoming-ifc-audit-20260910/`。迁移涉及 88 份原文件、3,610,228 字节，迁移时直接逐字节比对一致；旧目录已不存在。路径映射保存在 [migration.json](migration.json)。之后只更新人读说明、导航和脚本输出路径，原始机器检查结果及失败、超时记录保留。

原 IFC、两个 ZIP、IFC-bench 子模块内容没有修改；代码仍在 `scripts/dataset/`，测试仍在 `tests/dataset/`。本轮只整理、迁移和交接，没有执行 IFC 修复或正式准入。

## 2. 不要混淆两个“50”

| 数据范围 | IFC 文件数 | 说明 |
|---|---:|---|
| IFC-bench 旧登记 | 50 | 历史引入清单，不是上游当前版本总量声明 |
| IFC-bench 当前本地 | 48 | 排除 2 份过大文件后，25 个 IFC2X3、22 个 IFC4、1 个 IFC4X3_ADD2 |
| ResBIM_IFC2X3_50.zip | 50 | 另一个来源的转换文件，与 IFC-bench 无关 |
| Text2IFC_29RVT_IFC2X3_NoGrid_Full.zip | 30 | 29 个新转换 IFC + 1 个原有 Circular 示例 |
| 现有 canonical 清单 | 274 | 多来源正式文件登记，两个新 ZIP 尚未并入 |

所以，新 ZIP 的检查分母是 80 个 IFC 文件，其中 79 个为转换结果；不是“IFC-bench 又新增了 50 个”，也不是“新增 80 个独立建筑”。字节级重复为零不等于建筑变体为零。

## 3. 已核实的主要合规问题

### 3.1 格式层：79 个转换文件共同存在的问题

1. 同一 IFC 文件内部分 IfcRoot 实体 GlobalId 重复，涉及属性集等实体。不能把不同对象合并，也不应重生成全体构件 GUID。
2. 部分 IfcSIUnit 的必填 Name 缺失。不能为了通过验证统一填 METRE，必须核对 UnitType、Prefix、项目单位与实际用途。
3. FILE_NAME.originating_system 缺失。补写应真实反映有证据的生成/规范化过程，不能伪造 Revit 或其他导出来源。

上述三项已对全部 79 个转换文件第二次直接解析核对。深入属性、基数、逆关系、唯一性校验完成了其中 75 个未超限转换文件，均发现错误；4 个超限文件只完成基础解析和直接必填字段/GlobalId 检查，不能称为完整校验通过。另有部分文件存在其他错误，例如定位实体的逆关系约束问题，必须逐规则分类处理，不能只消掉三类错误便宣称完成。

这些是确认存在的缺陷；产生于转换器、Grid 清理还是其他处理步骤，尚未确定。两个包都使用相同转换链的历史说明只是定位线索，不是根因证据。

### 3.2 体积与模型内容

| 类别 | 数量 | 处理定位 |
|---|---:|---|
| 小于 10 MiB 且有主体形状的转换文件 | 70 | ResBIM 50 + 其他来源 20；待修复候选，不等于完整独立建筑 |
| 超限且有主体 | 4 | RVT-004、005、011、012；约 37.9450、37.8857、67.9031、67.9031 MiB |
| 可解析但没有主体形状 | 5 | RVT-002、013、020、022、023；不是零字节，也不能断言原 RVT 为空 |
| 附带原有 Circular IFC | 1 | 已通过本轮基础技术检查，作为未修改对照；许可与最终准入仍单独审核 |

80 个文件均成功解析为 IFC2X3，IfcGrid 与 IfcGridAxis 均为零。71 个小体积有主体文件共抽检 1,660 个构件，未发现几何生成失败；76 个未超限文件内存往返重开成功。这些结果不替代全部 EXPRESS 规则、全构件几何或建筑完整性验收。

### 3.3 不能用格式补丁替代的审核

变体：发现 12 对高构件 GlobalId 重合关系，例如 RVT-006/007、008/010、house/nowalls，以及 RVT-004/005/011/012。单文件内部重复 ID 是格式问题；不同版本间共享 ID 是身份线索，两者必须分开。高重合也不能独立证明建筑相同，应结合来源和模型内容。

依赖：包内记录称 RVT-025、026、028 缺少部分 DWG/RVT 输入依赖；RVT-008、022 的链接是否完整导出未知。本轮没有重新运行 RVT 链接解析，不能把来源包缺依赖直接称为当前 IFC 无法独立打开。

屋顶：50 个 ResBIM 均没有 IfcRoof 或 ROOF 类型 IfcSlab，属于屋顶语义待核实；不能仅由计数断言屋顶几何丢失，更不能凭空加屋顶。修复格式不会自动解决建筑完整性。

拓扑：50 个 ResBIM 的 Opening 有 Voids 关系，Door/Window 有 Fills 关系；其他 29 个转换文件中有 7 个存在部分门窗缺 Fills 链。这里只是关系存在性核查，不是完整拓扑或规范证明；先核对实际宿主/构件表达，不盲目补洞或填充关系。

许可：模型级许可终审未完成，不能因技术修复成功直接放行训练或再分发。

## 4. 建议处理路线

先复核检查器并把问题按“规则 + 受影响实体类型 + 修复前提”分类。先用 ResBIM 的 `0.ifc` 和 `RVT-001__LittleHouse__IFC2X3_NoGrid.ifc` 两份代表样本，在独立副本上验证最小修复；再选未参与规则设计的同类文件交叉复验。对新问题类型补充代表样本，不把两份通过推断为整批通过。

GlobalId 只修复文件内真实冲突，保留已有合法身份和对象关联；记录包含原 STEP ID 的映射，因为单独用旧 GUID 不能区分发生冲突的对象。IfcPatch 的 RegenerateGlobalIds 支持 only_duplicates，但默认是全量重生成，因此不得无参数直接套用；是否采用还需验证当前安装版本、确定性和映射要求。

单位缺失只在现有属性及来源证据可确定正确单位时补齐；保留前缀及数值，不进行无依据的单位重标或量纲转换。文件头补写保存原值并说明真实依据。孤立定位等其他缺陷先核对完整引用图，不因为某项逆引用为空就删除仍被子对象使用的节点。

样本与保留性检查通过后，可以将同一已验证问题族的处理应用到 70 个小体积候选中的匹配文件；未知问题、单位歧义、身份映射歧义或模型内容变化阻断相关处理，不降低校验标准。4 个超限和 5 个无主体文件单列诊断，暂不通过删构件、裁切或虚构几何凑数。

建议产物在 `dataset/external/_repairs/incoming-ifc-repair-<run-id>/` 下按来源和模型编号存放，保留 before/after 证据与修复报告。这是派生修复候选目录，不自动进入 canonical 文件清单。不得更改既有 Proof、来源 IFC、原 ZIP、正式 manifest 或实验划分。

## 5. 给下一位 Agent 的材料

直接使用 [REPAIR-AGENT-PROMPT.md](REPAIR-AGENT-PROMPT.md)。证据入口为 [README.md](README.md)、[REPORT.md](REPORT.md)、[verified-register.json](verified-register.json)、[summary.json](summary.json) 和 `member-v2-*.json`。

旧版 `member-000` 至 `member-004` 是检查器兼容错误记录，不能当最终检查结论。`member-v2-020` 是深入检查超时证据，不能当空模型。`reconciliation-before.json` 中原因未知和旧路径属于历史快照，当前更正以本摘要及 external-corpora.json 为准。

## 6. 技术参考与证据范围

实际数量和问题来自本地报告，不来自网上资料。IFC2X3 的字段和约束以仓库 `schemas/ifc/IFC2X3_TC1.exp` 及实际安装的 schema 为核对依据。在线接口参考核对日期：2026-09-10；不据此推定本机版本。

```text
https://docs.ifcopenshell.org/autoapi/ifcopenshell/validate/index.html
https://docs.ifcopenshell.org/autoapi/ifcpatch/recipes/RegenerateGlobalIds/index.html
```

IfcOpenShell 文档区分解析、属性/基数校验与 EXPRESS 规则。后续应记录实际启用范围及解析日志，不把一次成功打开、一次抽样成功或错误数下降写成完整 IFC 标准认证。
