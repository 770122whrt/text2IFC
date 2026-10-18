# RVT 交接核验与 IFC 重建记录（2026-09-13）

本次按用户确认统一在 `dataset/external/RVT` 内处理。先完成交接材料和现有 authority 的核对，再解包、核实来源并运行转换。原文件、失败输出及旧 metadata 均保留。

**最新调整：**按用户要求，当前主集合改为 [50 份 ResBIM＋4 份补充 IFC](IFC/dataset-resbim50-20260913/README.md)，共 54 个唯一文件，39.69 MiB。54 份已重新解析且与此前严格检查报告逐一匹配哈希。原 104 份转换池保持原字节，作为历史储备。下文 104/378 是完整历史转换池及逻辑素材统计，不是当前主集合数量。

[22 份许可复查](license-recheck-20260913/README.md) 新确认 HF 两个上游哈希，累计 21/22 来源字节可核实，但 22 份模型训练/再分发范围仍未确认。[7 份视觉抽检](review-visual-20260913/README.md) 发现 UFH 空楼层异常、Dynamo 局部构件场景和 Primer 全 Proxy 分类等限制，四份补充样本没有获得完整建筑准入。最新逐文件状态以 [当前 manifest](IFC/dataset-resbim50-20260913/manifest.json) 为准。

## 首轮完整转换池结果（保留历史）

已形成 [104 个唯一 IFC2X3 的本地集合](IFC/dataset-20260913/README.md)，约 72.15 MiB：ResBIM 100，UFH、APS Check Models、DynamoRevit、Dynamo Primer 各 1。全部 Schema＋EXPRESS 错误为 0，累计 4,879 个带表示对象的几何检查无失败。汇总时重新核对所有 136 份源 RVT 和 104 份入选 IFC 的哈希。

与原有 274 份 IFC 去重后，当前 external 的逻辑素材为 **378 个唯一 IFC，其中 331 个 IFC2X3**。这是来源文件的逻辑统计，不包含过程副本，也不是建筑数量；原有 227 个 IFC2X3 没有被自动提升到本次严格验证等级。[最终对应关系检查](review-20260913/final-ifc-correspondence.json) 未发现完全相同的 IFC 哈希，也未发现本轮抽取的主要构件 GUID 集合与旧清单有至少 3 个重合的线索；这不能替代完整的几何/建筑相似性分析。

136 份 RVT 中仍有 32 份未纳入：22 份许可待确认，1 份依赖加载未验证，9 份质量/语义或建筑主体问题。质量待处理为 INV-051、052、064、065、066、069、070、073、074；依赖项为 INV-071。它们保留各自失败/待判断证据，没有通过删除属性、任意改身份或补造构件准入。

转换、输入保护、规范化和汇总的 scoped 测试结果为 **33 passed**。未运行仓库 Full Preflight，未进行 Provider 调用，未提交或推送 Git 变更。

## 交接与新增获取

原交接是 5 个 ZIP：CrossSource A/B 各 18 份 RVT，ResBIM 两包各 25 份 RVT，Metadata 包 0 份 RVT。ZIP CRC 检查通过，四个模型包与 `PARTS_MANIFEST.json` 的大小和 SHA-256 一致；86 份 RVT 的路径、大小、SHA-256 与 enriched metadata 一致，文件 SHA-256 全部唯一。RVT 原始字节合计 657,862,656。

通过作者公开链接另行获取 `datapoints_100.7z`：732,361,930 字节，SHA-256 为 `347f05d75996f03d0e81fd6627a651435891e6def977db3a75f750cfff234b41`。7-Zip 25.01 完整 CRC 检查通过。包中有 100 份 RVT、100 份配对 JPG 和目录条目；只解出 RVT。前 50 份与交接文件逐字节一致，新增 50 份，合计 **136 份唯一 RVT**。[下载和上游比对](additional/ResBIM/upstream-byte-comparison.json)

原索引 [asset-index.json](asset-index.json) 保持 86 份；新增获取记录进入 [asset-index-expanded.json](asset-index-expanded.json)。这两个文件中的转换状态是获取时快照，不能用来代替 `runs/*/outcome.json` 或最终集合的当前结果。

用户已删除两个不合格旧 IFC ZIP，历史 80 个 IFC 条目不作为当前模型数，也没有恢复。Metadata 内另有 13 个历史参考 IFC 文件出现、11 个唯一 SHA-256，属于历史变体和修复参考，本次未混入新转换结果。

## 来源与许可核实

以下统计覆盖扩充后的 136 份 RVT。原始交接中的 `unverified` 字段作为历史记录保留，复核结论在 [source-review-expanded.json](review-20260913/source-review-expanded.json)，网页/API/许可证快照在 `review-20260913/source-evidence/`。

| 来源 | RVT | 当前证据 | 使用结论 |
|---|---:|---|---|
| ResBIM | 100 | 作者公开包、MIT、README 明确提到研究/AI 训练；原 50 份与公开包精确匹配 | 有本地研究和训练用途依据，发布时保留许可和引用 |
| ADN | 2 | 上游 Git 文件精确匹配，MIT，无嵌套许可覆盖 | 有来源使用依据 |
| UFH | 4 | 上游 Git 文件精确匹配，MIT | 有来源使用依据；house/nowalls 是变体 |
| APS Check Models | 1 | 上游 Git 文件精确匹配，MIT | 有来源使用依据 |
| DynamoRevit | 6 | 上游 Git 文件精确匹配，Apache-2.0 | 有来源使用依据，host/link 另查依赖 |
| Dynamo Primer | 1 | Git 文件精确匹配；Primer 网站有 Apache-2.0 声明，仓库未发现独立 LICENSE | 支持本地示例研究；单模型训练/再分发范围保留条件 |
| Tertiary | 11 | 上游 Git 文件精确匹配，未发现明确 LICENSE | 来源可核对，数据使用授权待确认 |
| aussieBIMguru | 8 | 6 个直接 Git 文件、2 个上游 ZIP 内文件均精确匹配，未发现明确 LICENSE | 来源可核对，数据使用授权待确认 |
| HF cad-environments | 3 | 当前元数据无明确许可证；2 个名称仍可见，第 3 个文件当前索引未找到 | 来源身份/许可/依赖待确认 |

因此有 **114 份**具备本地转换研究依据，其中 **113 份**有来源支持的训练用途依据；这仍不是技术通过数量或已创建的训练集数量。其余 22 份没有因“公开可下载”而自动标为许可通过。

主要来源：[ResBIM](https://github.com/RogerLiang0725/ResBIM)、[ADN](https://github.com/ADN-DevTech/RevitTrainingMaterial)、[UFH](https://github.com/Hei5enber9/HierarchicalLayoutApproachUFHsystem)、[APS](https://github.com/autodesk-platform-services/aps-checkmodels-createissues-revit)、[DynamoRevit](https://github.com/DynamoDS/DynamoRevit)、[Primer 的许可声明](https://primer.dynamobim.org/)、[ABG](https://github.com/aussieBIMguru/Revit-Files)、[Tertiary](https://github.com/tertiarycourses/TGS-2026064717-Application-of-BIM-using-Revit)、[HF](https://huggingface.co/datasets/markov-ai/cad-environments)。

## 依赖和 variant

原依赖表含 6 条记录、5 个 host。原表使用旧 `RVT-xxx` 标识和旧目录名；本地索引通过原始 inventory 的 SHA-256 映射到 `INV-xxx`，同时保留原字段。不能直接按新 ID 猜测旧依赖关系。

| Host | 依赖 | 状态 |
|---|---|---|
| INV-061 Studio Block Finished | INV-062 Studio Block Structure | 文件存在，运行时加载未验证 |
| INV-071 hostFile | INV-072 linkFile | 文件存在，运行时加载未验证；host 暂不准入 |
| INV-075 HF PROJECT | `00-ASN-IFC-STR-FL_R00.dwg` | 缺失 |
| INV-076 HF PROJECT-1 | 上述 DWG 与 `01-ASN-IFC-STR-TB_R00.dwg` | 缺失 |
| INV-083 ABG FormworkStarter | `Technical_school-current_m.rvt` | 缺失 |

不能把 host 与 link、house 与 nowalls、课程的步骤文件、同一设计的导出/修复变体都作为独立建筑。ResBIM 官方说明其为算法合成的住宅单元设计数据。最终 manifest 的 `independent_building_count` 为 `null`；保守的 `provisional_leakage_group` 只用于避免错误切分，不作为建筑数量证明。

## 与现有 IFC 的关系

现有正式 `ifc-files.jsonl` 有 **274 个唯一 IFC**，合计 3,535,049,440 字节。本轮逐文件存在性和 SHA-256 核对无冲突。Schema 分布：IFC2X3 227，IFC4 30，IFC2X2_FINAL 12，IFC4X3_ADD2 3，IFC4X2 1，IFC4X3_RC2 1。正式清单中 `training_eligible=true` 仍为 25。

证据：[现有 IFC 核对](review-20260913/existing-ifc-inventory.json)。274 条记录未提供与本次 RVT 的可证明转换 lineage；历史参考包的 11 个唯一 IFC 与它们没有 SHA-256 相同项。新结果通过本次输入 RVT 哈希、真实命令、原始输出、规范化报告和验证报告建立对应关系。构件 GUID 重合只能作为相关性线索，不能单独证明来源相同或建筑独立。

原来的 `ifc2x3-certified.jsonl` 主要记录解析、遍历、往返重开等结果，不能把其 227 份都表述为已通过本轮完整 Schema＋EXPRESS＋全对象几何检查。本次新集合的更严格结果单独记录；正式 authority 的既有准入语义保持原样。

## RVT→IFC 路线选择与实测

| 路线 | 核实结果 | 本轮执行状态 |
|---|---|---|
| DDC RVT2IFC Community | 已下载完整 209 文件包，固定 Git revision，逐项核对 Git blob、大小、SHA-256；实际帮助版本 18.4.1 | 已进行真实转换，包装程序及直接引擎 CLI 都有实测记录 |
| 自编 Python + IfcOpenShell | 负责输入核验、隔离执行、证据受限的规范化、独立验证及集合构建 | 已实现并运行，RVT 解码由 DDC 完成 |
| Autodesk `revit-ifc` | 开源 IFC exporter，需要匹配版本的 Revit 宿主和 DLL | 本机未发现 Revit 安装；未声称编译或转换成功 |
| APS Revit Automation | 官方提供 `Document.Export` 导出 IFC2x3CV2 的调用路径，需要账户、AppBundle/WorkItem 和云端环境 | 本轮未配置或调用云端服务 |
| ODA BimRv SDK | 官方提供 RVT 读写及 IFC export API，需要其 SDK 和许可 | 未取得独立 SDK；本机 TeighaX 3.09 不等于 BimRv SDK |
| BricsCAD BIM | 官方支持 RVT 导入和 IFC2x3/IFC4 导出 | 本机未发现 BricsCAD 安装，未实测 |

[DDC 项目](https://github.com/datadrivenconstruction/cad2data-Revit-IFC-DWG-DGN)、[用户指定的 DeepWiki](https://deepwiki.com/datadrivenconstruction/cad2data-Revit-IFC-DWG-DGN/2.2-rvt2ifcconverter)、[Autodesk exporter](https://github.com/Autodesk/revit-ifc)、[APS 官方示例](https://aps.autodesk.com/blog/export-ifc-rvt-using-revit-automation-api-part-i)、[ODA SDK](https://www.opendesign.com/products/bimrv)、[ODA IFC 导出](https://www.opendesign.com/blog/2021/december/bimrv-sdk-export-ifc)、[BricsCAD IFC](https://help.bricsys.com/en-us/document/bricscad-bim/project-collaboration/ifc-import-and-export-in-bricscad?version=V25)。

DeepWiki 在本轮多次读取失败。DDC 随包 HTML 的旧参数写法与实际帮助不同，执行采用已验证的 `input --output ... --mode custom --config ...`。保留的完整软件包约 751.6 MB。它是专有二进制许可，不因放在 GitHub 就变成开源 SDK；仅作本地工具使用，不随 IFC 数据集分发。[DDC EULA](https://datadrivenconstruction.io/term-of-use-and-eula/)

DDC 原始输出普遍存在 IFC2X3 编码问题，不能以退出码 0 或可以打开作为成功准入条件。第一份 ResBIM 0 原始结果有 95 项 native 错误；固定规则处理后为 0，33 个带表示对象均可生成几何。ResBIM 25 的零栏杆高度通过两个 1100 mm 源参数与 1.1 m 几何高度交叉核对后修正。每一步都保留原版本；LittleHouse 的属性/空间层级冲突、UFH 的属性冲突和未满足高度证据条件的 Dynamo 样本继续保持阻塞。

## 检查范围与边界

每份最终文件需通过 IfcOpenShell 0.8.5 的 native Schema＋EXPRESS 检查、所有带表示的 IfcProduct 几何生成、重新打开、非空建筑主体要求，以及规范化的源文件/构件 GUID/修改范围保留检查。Grid 用包含曲线、曲面和实体的几何设置检查，不通过删除 Grid 消除报错。[IfcOpenShell 验证文档](https://docs.ifcopenshell.org/ifcopenshell-python/validation.html)

这些检查尚不能证明 RVT 中所有应导出的内容都已保留，也不检查建筑设计规范、模型碰撞、特定 MVD/IDS 或施工可用性。ResBIM 是合成数据，数量扩充不能替代来源多样性和建筑层面的分组评估。原始数据中没有 Roof 实体等现象在计数中如实保留，没有为通过检查补造构件。

更大规模来源已定位到作者约 7 GB 的完整包（1000+ 配对设计）；本次实际获取的是 100 模型包。扩展前应复用相同去重与质量规则，并针对完整包中作者声明的失败案例建立额外筛查。不能将下载页的样本数量提前加入本地 dataset 统计。
