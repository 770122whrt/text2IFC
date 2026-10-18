# IFC 数据集当前入口

更新：2026-09-26。当前 **387 条来源记录、386 份唯一首选内容；可用 224、可修复 0、当前无已验证自动修复方案 162**。可用集 196 份 IFC2X3、202 份小于 10 MB；34 份 IFC2X3 建筑专业候选，小型优先描述候选 16 份。可用总大小 **1124.878 MB**，收集许可明确 198、待核实 26；公开修改副本另按逐文件许可判断。

本轮新增8份IFC2X3、修复采用5份；LCA单户原型和同母族版本单独计数。执行结果与母族/变体讨论分栏见[2026-09-26扩充报告](_checks/ifc-expand-20260926-v8/REPORT.md)，以及[新增/修复/许可登记](_checks/ifc-expand-20260926-v8/batch-registration.csv)、[当前建筑候选](_checks/ifc-expand-20260926-v8/whole-building-ifc2x3.csv)。原件、139核心场景和训练划分保留。

[2026-09-24选材评估](IFC_POSTTRAINING_READINESS.md)为历史快照，其中Type5的整栋建筑口径已在本轮更正。

## 2026-09-16 历史批次：许可复核、简单修复与新增

日期：2026-09-16。保持原文件；修复只写副本。MB 按 1,000,000 字节计算。

本轮已复核原28份许可待确认文件，解除其中4份；额外复核医院结构模型已有授权，不重复计作新解除。简单修复成功 **5 份**；下载 **6 份**新候选，其中 **3 份**原件直接通过检查。

当前 **379 条来源记录、378 份唯一首选 IFC**；可用 **210**、可修复 **0**、不可修复 **168**。可用共 **988.718 MB**，其中 **195 份小于 10 MB**。

“不可修复”沿用三分类表名，准确含义仍是当前未证实可自动修复、工具不支持或缺源资料，不代表永久无法修复。已修好并复检通过的直接归“可用”。

## 1. 0.002 MB 到底是什么

[tessellation-with-individual-colors.ifc](buildingsmart-official/ifc4/iso-reference-view/tessellation-with-individual-colors.ifc) 是 buildingSMART 官方 IFC4 彩色三角网格功能示例，**2,593 字节（0.002593 MB）**。

它有32个IFC实体，但只有1个有几何的 IfcBuildingElementProxy：8个顶点、12个三角面，包围盒1×1×2米。它有IfcProject/IfcBuilding容器，并不意味着它是一栋真实完整建筑。保留为几何功能测试样本，登记已明确标注 `geometry_feature_sample_not_complete_building`；不增加独立建筑数量。

![最小文件的实际网格预览](_checks/ifc-assets-20260916-v6/smallest-file-preview.png)

预览来自实际IfcOpenShell网格，只展示几何，不用于验证源文件的面颜色。

## 2. 许可复核结果

| 文件 | 核实结果 |
|---|---|
| IFC-Bench Duplex 建筑 | 项目专项 CC BY 4.0，修复副本保留来源并注明修改 |
| KIT-Bridge | 官方明确 unrestricted use，出版需署名 KIT/IAI |
| Jesse.1 | TestData 专项 GPL-3.0-or-later |
| HHS_Office_construction | 数据专项 CC BY-ND 4.0；本项仅放行未修改原件的收集 |
| West Riverside Hospital 结构 | 项目专项 CC BY 3.0，远端LFS SHA与本地原件一致 |

原28份中仍有24份待确认；本轮另有技术修好但许可未明的Trapelo。当前全部可用文件中，**185 份收集许可明确、25 份许可待核实**。已发现的Office许可错引诊所项目，继续暂停该项许可放行。DURAARK公开披露身份已查明，但没有把“公开下载”当作逐模型开放许可。

未修改训练准入；收集许可、允许发布修复派生版、训练用途是不同判断。完整出处和适用范围见 [28份复核](_checks/ifc-assets-20260916-v6/LICENSE_REVIEW.md) 与 [补充两份复核及勘误](_checks/ifc-assets-20260916-v6/supplement.md)。

## 3. 本轮简单修复

| 首选修复副本 | 修复内容 | 原生错误 | 完整网格比较构件数 |
|---|---|---:|---:|
| [model_203.ifc](repairs/grid-v6/gni-bim-dataset-model_203-da9fbdc27038/model_203.ifc) | 32条严格Z=0轴线改为独立二维曲线 | 32 → 0 | 1557 |
| [model_39.ifc](repairs/grid-v6/gni-bim-dataset-model_39-e0eab00c0cab/model_39.ifc) | 90条严格Z=0轴线改为独立二维曲线 | 90 → 0 | 800 |
| [model_7_arc.ifc](repairs/grid-v6/gni-bim-dataset-model_7_arc-a7e1509c0ebe/model_7_arc.ifc) | 70条严格Z=0轴线改为独立二维曲线 | 70 → 0 | 1156 |
| [20160125Trapelo - Existing-RST_2010_Trapelo.ifc](repairs/metadata-v6/kaggle-ifc-examples-20160125trapelo---existing-rst_2010_trapelo-83bf63775589/20160125Trapelo - Existing-RST_2010_Trapelo.ifc) | 2个缺失必填类型改为NOTDEFINED | 2 → 0 | 1322 |
| [str_ifc2x3.ifc](repairs/metadata-v6/ifc-bench-str_ifc2x3-5f404bfbce09/str_ifc2x3.ifc) | 3个缺失必填类型改为NOTDEFINED | 3 → 0 | 2897 |

轴网修复遵循 [IfcGridAxis.WR1](https://standards.buildingsmart.org/IFC/RELEASE/IFC2x3/TC1/HTML/ifcgeometricconstraintresource/lexical/ifcgridaxis.htm)：二维曲线定义于网格局部XY平面。只接受原曲线所有Z严格等于0的折线，新建二维引用，原三维曲线、点和显示表示均保留。非零Z或混合维数跳过。

基础构件修复将缺失的必填PredefinedType明确写成 [NOTDEFINED](https://standards.buildingsmart.org/IFC/RELEASE/IFC2x3/TC1/HTML/ifcstructuralelementsdomain/lexical/ifcfootingtypeenum.htm)，不猜测条基、独基等实际分类。已有分类及IFC4的可选空值不变。

8项针对性测试通过，保留失败再通过记录。每份采用副本都重新完成原生EXPRESS、全部带表示构件几何、写出重开，并逐构件比较世界坐标顶点、面索引、边索引哈希。源文件哈希、GUID、其他属性和几何定义保持不变。

## 4. 新获取的6份 IFC

| 文件 | 来源 | MB | 版本 | 原生错误 | 几何通过/应检查 | 本轮结论 |
|---|---|---:|---|---:|---:|---|
| [Type 5.ifc](european-lca-typical-buildings/20260916/Type 5.ifc) | [european-lca-typical-buildings](https://data.mendeley.com/datasets/yv723tdtv9/1) | 6.563 | IFC2X3 | 0 | 47/47 | 可用 |
| [Test model 1.1.ifc](scan-vs-bim-quality/20260916/Test model 1.1.ifc) | [scan-vs-bim-quality](https://data.mendeley.com/datasets/p6bd3n5fjj/2) | 1.277 | IFC2X3 | 67 | 100/100 | 保留问题文件，未纳入可用 |
| [Test model.ifc](htsm-historic-timber/20260916/Test model.ifc) | [htsm-historic-timber](https://data.mendeley.com/datasets/mywtvtvhwc/1) | 10.576 | IFC2X3 | 48 | 519/519 | 保留问题文件，未纳入可用 |
| [BIM4EEB_DEMONSTRATION_BLDG_ITA.ifc](bim4eeb-demonstration/20260916/BIM4EEB_DEMONSTRATION_BLDG_ITA.ifc) | [bim4eeb-demonstration](https://zenodo.org/records/6685810) | 9.437 | IFC2X3 | 61 | 2778/2778 | 保留问题文件，未纳入可用 |
| [BIM4EEB_DEMONSTRATION_BLDG_FIN.ifc](bim4eeb-demonstration/20260916/BIM4EEB_DEMONSTRATION_BLDG_FIN.ifc) | [bim4eeb-demonstration](https://zenodo.org/records/6685810) | 1.962 | IFC2X3 | 0 | 939/939 | 可用 |
| [BIM4EEB_DEMONSTRATION_BLDG_POL.ifc](bim4eeb-demonstration/20260916/BIM4EEB_DEMONSTRATION_BLDG_POL.ifc) | [bim4eeb-demonstration](https://zenodo.org/records/6685810) | 1.253 | IFC2X3 | 0 | 356/356 | 可用 |

六份来源均明确为CC BY 4.0，下载字节与发布平台校验和一致，无已登记字节副本。5份小于10 MB；历史木结构10.576 MB是为结构类型多样性保留的例外。BIM4EEB按来源说明省略住户内部布局，适用于建筑外壳、结构与公共区域，不能当作完整室内模型。

剩余问题：Scan-vs-BIM有重复全零GUID及楼梯必填枚举缺失；木结构有48个属性集被多个类型共享的逆向基数错误；BIM4EEB意大利模型有52项共享属性集错误及9项比值越界。三份都能解析、全部带表示构件几何通过，但尚未证明整体可自动修好，本轮保留原件和错误证据。

文件按来源/场景分组，未把6个文件直接声明为6个独立建筑。获取、去重与未下载来源见 [新来源报告](_checks/ifc-assets-20260916-v6/NEW_SOURCES.md)。

## 5. 当前可用文件的简单统计

| 版本 | 数量 |
|---|---:|
| IFC2X3 | 185 |
| IFC4 | 19 |
| IFC4X2 | 1 |
| IFC4X3_ADD2 | 5 |

| 大小区间 | 数量 |
|---|---:|
| <1 MB | 129 |
| 1–<10 MB | 66 |
| 10–<100 MB | 15 |
| ≥100 MB | 0 |

按唯一内容的代表来源归属统计；跨来源的相同内容不重复累加。

| 代表来源 | 可用数 | 合计 MB | IFC版本与数量 |
|---|---:|---:|---|
| bim-whale-ifc-samples | 5 | 54.973 | IFC2X3×5 |
| bim2modelica | 3 | 3.341 | IFC2X3×3 |
| bim4eeb-demonstration | 2 | 3.215 | IFC2X3×2 |
| bimcollab-example | 2 | 0.789 | IFC2X3×2 |
| bimnet | 25 | 74.788 | IFC2X3×25 |
| buildingsmart-community | 46 | 103.252 | IFC2X3×43, IFC4×3 |
| buildingsmart-official | 17 | 5.378 | IFC2X3×4, IFC4×8, IFC4X3_ADD2×5 |
| duraark-public | 10 | 209.936 | IFC2X3×10 |
| european-lca-typical-buildings | 1 | 6.563 | IFC2X3×1 |
| geometrygym-ifc-examples | 1 | 0.168 | IFC2X3×1 |
| gni-bim-dataset | 20 | 120.982 | IFC2X3×14, IFC4×6 |
| ifc-bench | 12 | 338.711 | IFC2X3×10, IFC4×2 |
| kaggle-ifc-examples | 4 | 12.329 | IFC2X3×4 |
| kit-examples | 1 | 1.750 | IFC4X2×1 |
| livingbim | 2 | 0.446 | IFC2X3×2 |
| opensourcebim-ifc-files | 1 | 3.906 | IFC2X3×1 |
| opensourcebim-testfiles | 4 | 12.940 | IFC2X3×4 |
| resbim | 50 | 33.373 | IFC2X3×50 |
| steptools-samples | 2 | 0.870 | IFC2X3×2 |
| thatopen-web-ifc-three | 1 | 0.727 | IFC2X3×1 |
| xbim-essentials-examples | 1 | 0.279 | IFC2X3×1 |

[全部来源登记](ifc-asset-register.csv) · [三分类总表](ifc-condition-register.csv) · [可用文件](ifc-usable-register.csv) · [本轮机器统计](_checks/ifc-assets-20260916-v6/summary.json) · [本轮核验](_checks/ifc-assets-20260916-v6/publication-checks.json)

原核心139份、50份ResBIM和已有训练划分保持不变。没有删除文件，没有恢复RVT统计/转换。技术可用仅对应上述原生规则、几何和重开范围，不能扩大为所有MVD/IDS、工程正确性或逐文件原生GUI验收。

历史：[2026-09-15简报](IFC_COMPLIANCE_REPORT_20260915.md) · [v5修复扩展报告](_checks/ifc-assets-20260914-v5/REPORT.md)。旧报告和检查证据保留日期语境，本轮更新前的活动清单在v6/baseline保存。
