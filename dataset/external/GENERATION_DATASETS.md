# Generation 外部数据集说明与可用目录

更新：2026-09-15。本页说明现有数据对 Generation 的用途，并列出后续可考虑的公开来源。**本次不下载、不移动、不转换数据，不修改现有统计或训练准入。**

## 1. 现有统计从哪里看

沿用以下入口，不另建一套资产总表：

| 入口 | 内容 |
| --- | --- |
| [IFC_DATASET.md](IFC_DATASET.md) | 当前数据检查、修复与规模说明 |
| [ifc-asset-summary.json](ifc-asset-summary.json) | 当前统计快照 |
| [全部来源登记](ifc-asset-register.csv) | 每条来源记录及首选文件 |
| [可用清单 CSV](ifc-usable-register.csv) / [JSONL](ifc-usable-register.jsonl) | 当前技术检查通过的首选 IFC，含实际路径与许可信息 |
| [历史核心子集](ifc-core-register.csv) | 原 139 条核心记录，不与可用总数相加 |
| [来源与许可目录](../sources/CATALOG.md) | 各来源的使用依据与限制 |

2026-09-15 读取的统计版本为 `ifc-assets-20260914-v5`：**373 条来源记录、372 份唯一首选内容、202 份技术可用 IFC；其中 177 份为 IFC2X3，187 份小于 10 MB。** 本次逐条核对了可用登记中的 202 个检查路径，均存在；没有重新计算文件 hash 或重跑几何/规则检查。

“技术可用”指既有原生规则、几何与重开检查通过，不表示需求完整、无碰撞、可公开再分发或已获得训练准入。170 条“不可修复”分类表示当前没有已验证自动方案等限制，不是永久不可修复的结论。文件数、专业文件、格式变体与独立建筑数必须分开。

## 2. 现有数据对 Generation 有什么用

这些 IFC 大多是已有模型，不是现成的“完整建筑需求 → IFC”配对测试集。可用于检查器诊断、构件与关系参考、受控修改、复杂度分析和人工设计测试任务。将 IFC 反向写成需求后，必须另行核对文本覆盖；不能直接把重建同一个文件当作自然语言生成能力。

下表数量来自 `ifc-usable-register.jsonl` 的来源分组，**不是整个目录的文件数**。带修复的首选文件可能位于 `repairs/` 或既有检查目录；取样以登记中的 `assessment_path` / `local_path` 为准。

| 来源及本地目录 | 技术可用 / 其中 IFC2X3 | Generation 可用方式 | 主要限制 |
| --- | ---: | --- | --- |
| [BIMNet](bimnet/) | 25 / 25 | 构件、空间和关系检查；设计多场景任务 | 按已有 scene-family 分组；本地使用授权不等于公开再分发授权 |
| [buildingSMART Community](buildingsmart-community/) | 46 / 43 | 楼层、洞口、宿主和跨专业关系样例 | 同一项目可能有多个版本与专业文件；仅选可用登记中的文件 |
| [buildingSMART 官方示例](buildingsmart-official/) | 17 / 4 | 小型构件及关系检查，适合可解释演示 | 多种 IFC 版本及同一协调场景变体；不能都当作当前 IFC2X3 直接输入 |
| [IFC-Bench](ifc-bench/) | 11 / 9 | 复用实际模型和问题设计思路，检查已有场景理解 | 原任务主要是问答；许可按项目；修复后的首选路径可能在 `repairs/` |
| [ResBIM 当前集合](RVT/IFC/dataset-resbim50-20260913/ResBIM/) | 50 / 50 | 同源住宅单元的规模、几何及关系压力测试 | 同一生成来源，不代表 50 个独立建筑分布；无完整需求配对 |
| [GNI BIM](gni-bim-dataset/) | 17 / 11 | 较多构件与空间的检查负载、同类设计变体分析 | 课程模型存在共享建筑题型；部分首选路径是修复副本 |
| [DURAARK](duraark/) | 10 / 10 | 较完整模型的关系与复杂度参考 | 部分文件仍需明确模型级用途/再分发权利，技术可用不等于可公开 |
| [BIM Whale](bim-whale-ifc-samples/) | 5 / 5 | 小型墙、洞口、门窗诊断 | 小示例不是完整建筑；已有排除项不恢复 |
| 其余来源 | 21 / 20 | 专项构件和兼容性样例 | 逐项查看登记，不对整个来源一概准入 |
| **合计** | **202 / 177** | | |

可直接定位的例子：[BIMNet q9v](bimnet/q9v.ifc)、[Duplex 建筑模型](<buildingsmart-community/Duplex Apartment/Duplex_A_20110907.ifc>)、[ResBIM INV-010](RVT/IFC/dataset-resbim50-20260913/ResBIM/INV-010.ifc)。这些链接只方便取样，不代表已经完成 Generation 任务标注。

Schependomlaan 已在 [Community 目录](buildingsmart-community/Schependomlaan/) 中，不应作为“尚未引入的新来源”再次整包计数。其多专业/构件文件共用项目身份。当前登记未以 GeoBIM、Text2MBL、BIM-Edit 或 BIBIMBAP 为来源列出相应数据；这不是对整个磁盘的无文件证明。

## 3. 外部候选数据：可行性与建议目录

以下目录是**以后引入时的建议位置，当前没有创建或下载这些数据**。研究代码无需为了引用论文而整体放进 dataset；这里只考虑任务、模型和评测材料。

| 来源与官方入口 | 数据情况及适用任务 | 当前可行性 | 建议位置 |
| --- | --- | --- | --- |
| [BIM-Edit IFC](https://huggingface.co/datasets/BIM-Edit/BIM-Edit) + [Tasks](https://huggingface.co/datasets/BIM-Edit/BIM-Edit-Tasks) | 324 条编辑任务；输入与参考 IFC。适合宿主、关系、局部修改评估，非整栋从零生成 | **优先候选**；IFC 仓库页面标 CC BY 4.0，任务仓库独立许可需再核对；上游模型条款也需逐项确认。本次未下载 | `external/bim-edit/`，分开保留模型、任务和评估器侧参考 |
| [Text2MBL](https://github.com/CI3LAB/Text2MBL/tree/main/Data_and_code) | 模块化布局文本与代码；论文记载 198 个设计、396 对文本/代码。适合层次表示与需求配对参考 | **适合研究，接入需适配**；基于 Revit 代码，不是 IFC 数据。根目录及所读说明未明确数据许可，不直接纳入训练 | `external/text2mbl/`，保留上游 `Data_and_code/data/dataset` 结构 |
| [BIBIMBAP](https://ec-3.org/publication/ec32026_271/) | 100 个原子 CRUD 任务及可执行评测设计 | **优先核实发布包**；论文脚注提供 [作者入口](https://nbharathik.github.io/bibimbap/)，但本次未成功读取该页面，数据目录与许可尚未确认 | `external/bibimbap/` |
| [Self-Verification](https://github.com/Tsesterh/Text2BIM-Self-Verification) | 仓库含 `case_study/`，可参考规范、迭代产物与验证输出 | **适合案例对照**；不是大规模数据集；完整文件清单与数据许可未逐项核验 | `external/text2bim-self-verification/` |
| [Text2BIM](https://github.com/dcy0577/Text2BIM) | 公开代码、论文中的需求样例与补充材料 | **适合需求和基线设计**；[正式论文数据声明](https://doi.org/10.1061/JCCEE5.CPENG-6386)称部分数据/模型需向作者请求，不能声称完整 IFC 语料已公开 | `external/text2bim/`，仅在取得具体数据后使用 |
| [IFC-Copilot](https://show2instruct.github.io/ifc-copilot/) | 工具任务及生成演示，可作为 native IFC 系统基线 | **基线优先，数据另核实**；固定论文/代码版本，核实实际任务文件与许可，不把展示视频计作数据集 | `external/ifc-copilot/`，仅存实际采用的任务材料 |

注意 BIM-Edit 的 IFC 页面 viewer 只显示一条元数据记录，不代表只有一个模型；任务页显示的输入文件与参考文件数量也不是独立建筑数量。参考 IFC、评测答案和仅供评分的目标信息保留在评估器侧，不能混入模型的公开输入。

Trestle-Bridge 的 200 案例属于论文实验规模，本次未确认公开原始数据下载，不列为当前可用数据集。模型工程权限、ChronoSphere 和 CodeMEM 属于文献依据，不因相关就加入 IFC 数据库存。

## 4. 最可行的使用顺序

1. **先利用本地数据。** 从现有可用 IFC2X3 中按项目分组选择少量构件关系清楚的样例，服务检查器与局部纠错诊断。已有 [核心子集](ifc-core-register.csv)可作导航，仍需核对最新可用清单。
2. **另行建立整栋生成任务。** 写清楼层、空间、构件和关系要求，独立审查这些要求；参考 IFC 不必是唯一合法答案。最终按要求和产物质量评估。
3. **优先核实 BIM-Edit / BIBIMBAP。** 它们更适合补局部操作证据；Text2MBL 用于配对数据与分层生成参考，不能直接混用成绩。

ResBIM 使用已有 50 份即可；RVT 扩充和转换仍按 [RVT 当前状态](RVT/README.md)保持暂停。本页不恢复已排除模型、不改变已有 split。用途、许可、来源分组与检查状态均满足后，才由对应实验选择样本。

论文正文与 Claim 见 [Generation Demo 材料](../../docs/reports/generation-demo/README.md)。
