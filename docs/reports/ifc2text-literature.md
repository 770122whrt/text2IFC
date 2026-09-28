# IFC2Text 文献：已有工作、差异与数据来源

本文承接[研究方案](../architecture/bim2text-bidirectional-bridge-research.md)，只保存文献分析。以下为原检索记录，未在本次文档整理中重新检索。


检索截至 2026-09-16，使用 IFC2Text、BIM-to-text、building descriptor、natural language generation、BIM description 和 captioning 等关键词，并追查直接论文的作者与机构页面。结论是：**存在直接的 BIM→自然语言研究，当前查到的完整重建及跨建筑迭代证据较少。** 这是本轮检索结论，不是“从未有人做过”的证明。

## 1 直接描述与 IFC 解析

**Automated Natural Language Building Descriptor for Building Information Models，EC3 / CIB W78，2025。**
[出版页](https://ec-3.org/publication/ec32025_310/)，[全文](https://ec-3.org/wp-content/uploads/2025/10/EC32025_310.pdf)，重点为 Method、Validation 和 Results。

这是最直接的先例。它在 Revit / Rhino.Inside 环境中提取房间形状、面积及门窗楼梯连接，用 TETI 判断连接，整理为 JSON，再让 o1 和 DeepSeek-R1 写多层建筑说明。四个项目的实验检查房间覆盖、面积和连接描述，报告了形状与方向误读。其提示已经要求支持重建；论文未报告实际的文本→BIM 往返重建或跨建筑策略更新实验。

**数据公开情况（核查至 2026-09-16）：** 论文使用四个项目 A–D，分别为住宅、两个办公项目和宿舍，提取环境为 Revit 2025 / Rhino.Inside.Revit。在全文、出版页、[TUM 论文记录](https://portal.fis.tum.de/en/publications/automated-natural-language-building-descriptor-for-building-infor/)和[第一作者页面](https://www.cee.ed.tum.de/ccbe/team/suhyung-jang/)中，未找到这四个项目的公开 RVT／IFC 下载或数据仓库，也未找到明确的按申请提供数据声明。论文中的 JSON 中间数据不等于公开的建筑源模型数据集。因此，目前将其作为方法参考，不列入可下载数据来源；如需复现实验模型，还需向作者询问文件格式、获取方式与使用许可。这个结论是未找到公开发布证据，不是断言作者不能提供。起步实验可以使用手头已有 IFC，不依赖这四个项目。

我们的比较应从这一流程出发：描述不仅包含空间组织，还保留主要构件的定位与尺寸，并实际重建验证。把 Revit 换成 IFC、增加楼层标题，都不足以单独构成方法创新。

**IfcLLM，2026。**
[作者全文](https://arxiv.org/html/2605.13236v1)。

将属性和几何组织为关系表示、空间关系组织为图，让 LLM 查询和迭代获取答案；作者在三个 IFC、30 类查询场景中评价。它提供 IFC 空间信息读取的参考，但问答只需找到问题相关的事实，完整建筑说明还要主动覆盖没有被问到的空间和构件。包围盒关系可帮助找候选邻接，不能直接代表通行。

**BIM Information Extraction Through LLM-based Adaptive Exploration，2026。**
[作者全文](https://arxiv.org/html/2605.01698v1)。

Agent 根据问题编写并执行读取代码，再利用结果继续探索。作者用 ifc-bench v2 的 1,027 个任务、37 个模型、21 个项目评价。对本项目的启示是复杂 IFC 可能需要按需探索；但逐问查询能否稳定组成完整设计说明，仍需单独检验。可把“按提纲连续提问读取”作为空间解析方案的对照。

## 2 模型—文本配对与正向生成

**Text2CAD，2024。**
[作者全文](https://arxiv.org/html/2409.17106v1)。

从 DeepCAD 模型的视觉外观和草图／拉伸序列生成不同详细程度的描述，再训练文本到参数化 CAD 序列的模型，报告约 170K 模型、660K 文本标注。它证明反向标注服务正向生成是一条已有路线；我们的工作需要在建筑空间与构件描述、重建反馈上推进，不能把“模型自动生成 caption”本身作为新方法。

**Text2MBL，2025。**
[作者全文](https://arxiv.org/html/2509.23713v1)。

用模块、住宅单元和房间的层次化代码表示模块化布局，以 198 个设计、每个两份人工描述起步，配合合成文本微调 Qwen2.5，输出可在 Revit 执行的动作。实验比较输出表示及扩充方式，也观察到扩充越多并非越好。我们的区别是从既有 IFC 反向提取建筑事实，并用实际重建结果改进配对文本；它是数据与生成部分的重要对照。

**Text2BIM。**
[作者 v2 全文](https://arxiv.org/html/2408.08054v2)。

多 Agent 将需求转成建筑方案和工具代码，通过执行与检查反馈修订建筑；v2 比较 25 个提示、三种模型、各三次运行。其生成—检查—修改与已有 text2IFC 都说明任务内返工不是新贡献。本项目当前复用自己的正向系统，重点检验反向描述与跨建筑学习。

**BIM-Edit，2026。**
[作者 v3 全文](https://arxiv.org/html/2606.20146v3)。

输入已有 IFC 和编辑指令，评价增改删任务的几何、语义和拓扑表现，包含 324 个任务。它为后续改写设计说明的实验提供参考，但首个实验仍是未经修改的文本往返重建，不能把研究重新收缩为局部 repair。

## 3 API 下如何积累经验，以及哪些思路已经有人做过

**GEPA，2025，2026 年修订。**
[论文](https://arxiv.org/abs/2507.19457)，[作者实现](https://github.com/gepa-ai/gepa)。

通过执行轨迹和自然语言反馈提出、测试、选择提示候选，并组合不同候选的优势。论文报告六项任务的实验；本次核查摘要和官方方法说明，没有复核其全部实验表。它可以作为现成优化器，也必须成为对照：我们要证明建筑差异如何帮助学习，不能把提示自动优化重新命名为创新。

**ExpeL: LLM Agents Are Experiential Learners，AAAI 2024。**
[作者全文](https://arxiv.org/html/2308.10144v3)。

从训练任务中的成功／失败经验抽取自然语言经验，并检索成功轨迹帮助新任务，全程不更新模型权重。在 HotpotQA、ALFWorld 和 WebShop 等任务上验证。它直接支持 API 经验学习的可行性，也说明“失败总结＋示例库”已有先例；本项目需要增加建筑任务特有的差异定位和可检验的描述改动。

**Dual Learning for Machine Translation，2016。**
[论文](https://arxiv.org/abs/1611.00179)，[作者机构说明](https://www.microsoft.com/en-us/research/publication/dual-learning-machine-translation/)。

以英法两个翻译方向相互提供反馈，通过翻译后再翻译回来的结果学习。可借鉴往返监督，但建筑模型与设计说明并非信息量天然等价的两种语言，不能直接照搬句子重建目标。当前固定 text2IFC，因此并不声称已经进行双向联合训练。

**Self-Alignment with Instruction Backtranslation，2023。**
[作者全文](https://arxiv.org/html/2308.06259v2)。

从少量种子示例与大量现有网页文本反向生成指令，筛选配对数据并微调，再迭代改善筛选。它解释了如何利用“已有答案”构建输入—输出对。现有 IFC 同样可以作为已有结果，但我们仍要证明所生成的说明是否支持建筑重建，以及重建反馈是否比一次性标注更有用。

[Scan2BIM-Data](https://www.mds-lab.de/theses/scan2bim-data-automated-ifc-generation/)也提出空间描述与 IFC 配对方向，但所核查页面为开放 thesis topic，不能计为已完成的实验结果。
