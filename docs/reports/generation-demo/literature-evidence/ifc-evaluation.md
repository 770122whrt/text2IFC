# IFC 生成、编辑、知识使用与评价：全文证据卡

核查日期：2026-09-15。本文保留分配到的 B01–B10，并沿 IFC-Bench 原始出处补充 B11–B12。结果为 **FULL 9 篇、PARTIAL 3 篇**。FULL 表示已阅读原始正文的方法、实验和讨论；不表示运行过作者代码或复现过结果。PARTIAL 表示仅获得部分正文、摘要或出版元数据，相关条目仍保留，但不进入已核实结果比较。页码从论文 PDF 首页起计；arXiv HTML 使用节号和表号。

旧调研 `E:/Text2IFC-Generation-Literature-Survey-v2.1.md` 仅作查找线索。本轮检查公开论文、代码目录、README 和数据卡，未下载数据集、运行 Provider、修改产品或重新评分作者实验。文献中的 QA、编辑、点云重建、生成内部纠错分别记录，不能互换为 text2IFC 整体能力证据。

<a id="b01"></a>
## B01 — BIM-Edit

**BIM-Edit: Benchmarking Large Language Models for IFC-Based Building Information Modeling**。Bharathi Kannan Nithyanantham、Clemens Kujat、Tobias Sesterhenn、Stefan Telgmann、Ashwin Nedungadi、Jörn Plönnigs、Christian Bartelt、Stefan Lüdtke；2026，arXiv **2606.20146v3，2026-06-23**，预印本，前三位共同一作。**FULL**：[原文](https://arxiv.org/html/2606.20146v3)，已读 §3–5、附录 A、D–G，重点为表 1–3 和评分定义。

任务是“已有 IFC＋编辑指令→修改后 IFC”。11 个真实建筑场景与 36 个合成场景构成 47 个基础场景、324 项任务；同一修改的直接、空间、拓扑三种提示共享目标，不能当作独立建筑。创建、更新、删除各 108 项。评分检查变化部分：点云距离衡量几何、匹配后的类别/属性衡量语义、关系图 F1 衡量拓扑。七个模型共享单一 IfcOpenShell Python 执行工具、20 次调用预算，没有检索或 schema 专用工具。表 1 最佳均分为 Gemini 3 Flash 的 49.48/100；表 2 三项均达 0.98 的比例最高是 Qwen3.6 Plus 的 3.4%，不能把均分写成成功率。[方法和结果](https://arxiv.org/html/2606.20146v3#S3)

作者承认单一目标可能处罚合理替代方案，六类构件不能覆盖全部 BIM，评分权重尚缺专家标定。这套基线是受限环境中的直接编码能力，不代表增强系统上限。已检查 [任务卡](https://huggingface.co/datasets/BIM-Edit/BIM-Edit-Tasks)（324 行）和 [IFC 文件目录](https://huggingface.co/datasets/BIM-Edit/BIM-Edit/tree/main)；公开评分实现和论文缓存运行包的对应版本尚未独立核实。

**本轮判断：**几何、语义、拓扑联合评价已是明确先例；候选贡献应落在知识如何帮助编译及修改正确性，并与相同预算的强编码代理比较。任务变体、输入文件、目标文件和基础建筑应分别计数。

<a id="b02"></a>
## B02 — BIBIMBAP

**BIBIMBAP: A Benchmark for Instructional BIM-Based Automated Programming**。Clemens Kujat、Bharathi Kannan Nithyanantham、Stefan Telgmann、Tobias Sesterhenn、Jörn Plönnigs、Stefan Lüdtke、Christian Bartelt；EC³ 2026，Corfu，8 页。**FULL**：[会议原文](https://ec-3.org/wp-content/uploads/2026/08/EC32026_271.pdf)，已读 pp.3–8 的任务构建、评价、实验、局限，重点表 1–3。

100 个独立小任务，每题提供自然语言、小型 IFC 和 Python 检查，读取类另约束 JSON 输出。直接、空间几何、拓扑、数值、概念五类各 20 题，但 CRUD 分布是创建 15、读取 55、更新 15、删除 15。基线使用相同代码执行工具、25 次调用上限；六个模型中前三个重复三次。指标先计算每题通过的适用检查比例，再对任务平均；表 2 Opus 4.6 为 50.22±0.22，属于部分得分，并非完整完成约半数任务。作者明确：更新检查未覆盖非几何属性保留，删除后重建可能被判正确。[原文 pp.5–8](https://ec-3.org/wp-content/uploads/2026/08/EC32026_271.pdf)

作者将短任务、缺少多轮互动和命名检查列为限制。已核实 [公开仓库](https://github.com/nbharathik/bibimbap) 的 README、`data`、`llm_agents`、`tests` 和 `benchmark.py` 目录；“仓库未确认”的旧判断应更新，但本轮没有运行其测试。论文作者与 B01 重合七人，不据此推定共享实现或数据。

**本轮判断：**它适合原子能力与保持性切片，不能直接代表整栋生成。创建类在这里较易、在 B01 较难，首先反映任务与判据差异；不能跨基准宣称统一的难度规律。对候选方法，必须补齐未被检查的属性和关系保持要求。

<a id="b03"></a>
## B03 — Self-Verification

**A Self-Verification Framework Toward Reliable Text-to-BIM Generation**。Tobias Sesterhenn、Bharathi Kannan Nithyanantham、Stefan Lüdtke、Christian Bartelt；EC³ 2026，2 页短文。**FULL**：[会议原文](https://ec-3.org/wp-content/uploads/2026/08/EC32026_444.pdf)，两页全文，尤其 p.1 架构和 p.2 案例、讨论。

Specifier 在首轮把请求分解为 IDS 与非 IDS 要求；Modifier 生成或更新 IFC；IfcTester 执行 IDS，Verifier 生成并执行补充 Python 检查，合并结果反馈给下一轮。底层明确使用 MCP4IFC，允许调用预置工具和编写代码。GPT-5.2 的一个住宅案例运行五轮：部分构件和围护结构逐步改善，但 IfcSpace 与 IfcBuildingStorey 的关联始终未修复。这里的分母是一个案例、五次迭代，没有系统间对照、总体成功率或独立消融。[原文](https://ec-3.org/wp-content/uploads/2026/08/EC32026_444.pdf)

作者指出初始规范遗漏会传递到后续验证，删除操作也较难；自动生成检查并不保证需求覆盖完整。已检查 [作者仓库](https://github.com/Tsesterh/Text2BIM-Self-Verification)：README 明示依赖 `Show2Instruct/ifc-bonsai-mcp`，存在 IDS 构建、验证和逐轮产物流程，定位为研究原型。本轮仅审阅，不把 README 的功能描述当作运行验证。

**本轮判断：**“需求导出检查＋IDS/自定义规则＋生成内部纠错”已有直接覆盖。候选研究需证明检查覆盖、编译绑定和失败处置的具体改进；增加角色或反馈轮次本身不足以构成新方法。该文的生成纠错也不等于独立受损 IFC 修复评测。

<a id="b04"></a>
## B04 — Capability-based Evaluation

**Reliable LLM-driven BIM automation through capability-based multi-dimensional evaluation**。Zaid Alwashah、Bo Xiao、Hexu Liu、Shane T. Mueller、Xiaoyun Shao；*Automation in Construction* 187（2026），106910。**PARTIAL**：[DOI](https://doi.org/10.1016/j.autcon.2026.106910)，[出版社页](https://www.sciencedirect.com/science/article/pii/S0926580526001512)。实际可读摘要、方法/任务设计/结果/讨论的 section snippets；未取得连续全文和实验表。

片段可确认其围绕 BIM 自动化设计能力评价框架，并采用 31 个任务；不能据此还原任务独立性、完整提示与工具条件。摘要中关于 API 错误占比、可靠性分值和人工修正时间的数字，均未完成正文复核，本卡不将其列为已核实实验结果。六维评价的详细操作化定义、失败分母、人员介入程度、基线公平性及统计方法仍待全文。

已沿 DOI/出版社、精确题名检索、[作者实验室出版页](https://sites.google.com/view/dsc-lab/publications) 和 [Michigan Tech 机构记录](https://digitalcommons.mtu.edu/michigantech-p2/2484/) 寻找作者稿；机构“全文”链接仍回到 DOI，未发现公开稿。片段提到共享任务，但本轮未核实对应代码或数据仓库地址。因此不能把它写成可复现实验已经复核。

**本轮判断：**能力切片、多维可靠性和错误归因的总体方向已有同题研究，应保留为必要比较对象。尚不能借其摘要数字论证某类知识机制有效或失效，也不能把它当作我们方法的新颖性空白。作者组与 B05 相同；两文的任务是否复用未核实，不能把 31 与摘要中的 20 相加成独立样本。

<a id="b05"></a>
## B05 — Error Taxonomy

**Error Taxonomy and Failure Analysis of Large Language Models for BIM Scripting**。Zaid Alwashah、Bo Xiao、Hexu Liu、Shane Mueller、Xiaoyun Shao；*Construction Research Congress 2026*，pp.376–385，出版社页面在线日期 2026-08-27。**PARTIAL**：[ASCE 原始记录](https://ascelibrary.org/doi/10.1061/9780784486979.036)。已读元数据、摘要和参考文献，未读到方法、结果表及讨论全文。

摘要描述 GPT-4 为 Revit 编写 Python，开展 20 个任务并由人参与迭代调试，提出十类错误。这里记录的是摘要所述研究设计，不能认定十类定义、编码一致性和错误频率已被核查。尤其“最终任务完成”包含人工引导，不能转述为自主代理成功率 100%；重试次数、工具调用预算、人工劳动量和失败停止规则均未取得正文依据。

已尝试 [出版社 PDF 路径](https://ascelibrary.org/doi/epdf/10.1061/9780784486979.036)、精确题名及作者/机构稿检索；可找到会议日程和作者组的出版信息，未取得全文或独立公开代码、数据链接。不能因付费而删除该条，也不能以另文 B04 的片段填补它的方法。

**本轮判断：**它与代码错误分类、API 误用及人工修正成本直接相关，但目前只能作为待取得全文的先例。候选研究若声称“首次系统分析 BIM 脚本错误”存在明显风险；若声称知识利用减少错误，应自行定义可复核的事件单位，区分一次任务、多次失败和人工改写，而不是继承未审计的摘要结论。

<a id="b06"></a>
## B06 — Qwen-BIM

**Qwen-BIM: developing large language model for BIM-based design with domain-specific benchmark and dataset**。Jia-Rui Lin、Yun-Hong Cai、Xiang-Rui Ni、Shaojie Zhou、Peng Pan；arXiv **2602.20812v1，2026-02-24**，预印本；PDF 题名未带 Qwen-BIM 前缀。**FULL**：[版本记录](https://arxiv.org/abs/2602.20812v1)，[38 页原文](https://arxiv.org/pdf/2602.20812v1)，已读 §3–5，重点 pp.8–23 方法、pp.23–33 结果、表 7–8。

先把 BIM 局部空间块转换为文本，用 22 类问题模板及规则生成 QA，再生成并筛选推理答案，构建 3,493 条 QA/QRA 混合候选训练数据，对 Qwen2.5-14B 做 LoRA。任务包含信息问答、文本异常识别和修改建议，未验证生成 IFC。表 8 总体 G-Eval 从 0.689 到 0.834，约为相对提升 21%，不是增加 21 个百分点；评价使用 GLM-4-plus 裁判以及文本相似度。最佳配置仅用 1,364 条 QRA，训练轮次也与其他组合不同。表 7 声称 150 块/3,300 QA，但逐行相加为 160 块/3,520 QA，本文保留这个内在不一致。[原文](https://arxiv.org/pdf/2602.20812v1)

作者提出需扩展真实工程场景；数据声明为依请求提供，未核实公开权重、代码及完整数据下载入口。实验抽取不同空间块，未建立项目隔离的证据。

**本轮判断：**BIM 知识微调和合成 QA 已有先例，不能把 QA 分数转成几何、编译或修复能力。样本配比与训练轮次共同变化，推理监督的独立作用尚不清楚；候选方法需在真实输出、同等预算与未见项目上另证收益。

<a id="b07"></a>
## B07 — Building Descriptor

**Automated Natural Language Building Descriptor for Building Information Models**。Suhyung Jang、André Borrmann、Ghang Lee；EC³ / CIB W78 2025，Porto，8 页。**FULL**：[TUM 作者原文](https://mediatum.ub.tum.de/doc/1798649/mb4eded1rj089k4ppdqlxcgti.BIM_description_LLM_EC3_2025_CameraReady_Final.pdf)，已读 pp.3–7 方法、验证、表 4–5、讨论。原调研 EC3 文件链接失效，以上为恢复的机构稿。

方向是 BIM→建筑自然语言描述。Rhino.Inside.Revit 提取空间轮廓、面积、用途以及门窗楼梯连接，构成房间和关系 JSON，再让 o1 与 DeepSeek-R1 生成六类结构化描述。四个项目共有 139 个房间；表 4 中 o1 的四个房间数正确，R1 在三个项目漏数。表 5 的拓扑描述错误率，o1 为 0%、10.75%、10.70%、4.13%，R1 为 9.47%、24.90%、19.38%、31.78%。分母是被检查的描述内容，不是数千个独立模型；方向信息仍经常遗漏或错误。[原文 pp.5–7](https://mediatum.ub.tum.de/doc/1798649/mb4eded1rj089k4ppdqlxcgti.BIM_description_LLM_EC3_2025_CameraReady_Final.pdf)

作者指出复杂形状、邻接与围合易混淆，需要改善提示和元数据。论文没有验证由描述反向重建模型，未来用于训练也不等于已发布配对训练集；本轮未发现可核实的作者代码或数据集链接。

**本轮判断：**它支持“用结构化模型信息辅助语言描述”具有可行性，也给出了描述失真证据。若用于 text2IFC 数据构建，必须检查哪些约束被描述省略；不能默认 BIM→文本→BIM 可逆，或把自动描述直接当作完整设计要求和独立人工标签。

<a id="b08"></a>
## B08 — IFC-Agent

**Multi-agent framework for schema-guided reasoning and tool-augmented interaction with IFC models**（系统名 IFC-Agent）。Yan Gao、Fuji Hu、Chengzhang Chai、Yiwei Weng、Haijiang Li；*Automation in Construction* 186（2026），106888。**FULL**：[DOI](https://doi.org/10.1016/j.autcon.2026.106888)，[Cardiff 25 页开放全文](https://orca.cardiff.ac.uk/id/eprint/186047/1/1-s2.0-S0926580526001299-main.pdf)。已读 §3–6、附录 A–B，重点 pp.5–18 和 pp.20–22。

系统用 IFC schema 指导原子工具串联、缓存实体与流程信息；少量实体逐个探索，大量实体抽取少数样本后把推导的工具链交给确定性批处理，并允许受约束的计算代码。它假设同类实体的 schema 表示足够一致。正文与附录 A 实际列出 60 项查询/操作，跨三个 IFC 模型；引言的 48 项不能替代实验分母。按附录 A 成功标记逐行复算，GPT-3.5、4o-mini、4o 分别为 5、37、60 项；这只是表格复算，无重复试验。扩展实验最多 427 个目标实体。§6.3 明确承认缺少修改后模型一致性验证。[全文](https://orca.cardiff.ac.uk/id/eprint/186047/1/1-s2.0-S0926580526001299-main.pdf)

作者还保留复杂几何冲突、语义依赖和更大规模为后续问题；与 ifcOWL/GQL4BIM 的表 4 为定性对照，不是同集量化竞赛。数据依请求提供，本轮未核实公开实现仓库。

**本轮判断：**schema 知识驱动工具组合、状态缓存、抽样后确定性执行已有直接覆盖。当前证据不能建立全量属性保持或生成内部纠错可靠性；候选编译方法应比较实际约束和失败行为，而不是只把“知识引导代理”换个名称。

<a id="b09"></a>
## B09 — Scan-to-BIM / Scan-to-Graph

**LLM-enabled multi-agent framework for automated Scan-to-BIM and Scan-to-Graph reconstruction**。Yuandong Pan、Mudan Wang、Jiechao Gao、Jie Wang、Michael D. Lepech、Ioannis Brilakis；*Automation in Construction* 188（2026），107003。**FULL**：[DOI](https://doi.org/10.1016/j.autcon.2026.107003)，[Cambridge 记录](https://www.repository.cam.ac.uk/items/acda5588-8321-4f94-bb9b-30014bea1d54)，[18 页全文](https://www.repository.cam.ac.uk/bitstreams/bacf072d-a9b5-4a68-97fb-88069714f628/download)。已读 pp.4–16 方法、结果、讨论，重点表 4–7。

输入点云与自然语言范围，输出参数布局、IFC4 和拓扑图。Qwen 解释请求、SpatialLM 推断布局，后续墙连接修正、空间闭合、IFC 构造、图生成与验证包含确定性程序，不能把每个模块都称为 LLM。25 条范围指令上 Qwen-7B 分类正确 24 条；TUM CMS 六个房间的面积 MAE，两个 SpatialLM 配置约 1.45/1.51 平方米，传统 void-growing 对照为 0.87/1.23，未全面胜出。另有 S3DIS 五个房间的构件遗漏评估与合成例子。图的一致性主要相对生成布局检查。[全文 pp.10–15](https://www.repository.cam.ac.uk/bitstreams/bacf072d-a9b5-4a68-97fb-88069714f628/download)

作者承认规则室内平面几何、遮挡造成门窗遗漏等限制；生成图围绕房间节点组织，不能推广成多房间整栋拓扑验证。数据依请求提供，未核实作者公开代码。

**本轮判断：**参数表示→确定性 IFC/关系图→规则验证的链条已有先例。点云给出的几何证据与自由文本要求不同；查询分类正确、文件有效和相对布局一致，均不能替代独立建筑真值。候选编译器应说明新增约束、输入范围和实际增益。

<a id="b10"></a>
## B10 — Dual-Layer IFC Encoding

**A Dual-Layer Semantic-Lossless IFC Encoding for LLM-Readable Building Model Interaction**。Inho Jo、Yunku Lee、Lee Joo-sung、Namhyuk Ham（按 SSRN 作者显示）；2026，SSRN 6532559，2026-04-07 上传，41 页预印本，DOI 10.2139/ssrn.6532559。**PARTIAL**：[SSRN 原始记录](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6532559)。可读索引中的原始摘要、作者及参考文献；未取得 41 页正文。

摘要提出分离 IFC 空间层级和几何参数，并按需重建原文件。摘要中的字节压缩比、LLM token 降幅、问答准确率和 45 次生成试验均未经正文复核，因此不进入本文定量矩阵。尤其尚不能确认解码器是否依赖额外 sidecar、LLM 实际看见哪些信息、压缩前后输入如何匹配、任务与建筑独立单位及 schema 检查覆盖范围。

已尝试 SSRN 主页面、abstract 路径、DOI 和 PDF 获取路线，并用精确题名及作者机构寻找稿件；直接页面受阻，其他记录只提供摘要或索稿入口。没有核实代码或数据公开地址。它应保留为潜在强相关先例，不能写成“已经全文确认无损且全部生成成功”。

**本轮判断：**IFC 紧凑表示和按需重建与知识上下文效率直接相邻。可逆编码不自动意味着 LLM 可访问全部语义，schema 合法也不自动意味着满足设计要求；这两点是待检验问题，不能冒充该论文实际缺陷。候选方法若涉及压缩，应对齐语义可访问范围及解码依赖后再谈优劣。

<a id="b11"></a>
## B11 — IFC-Bench v1 的原始论文

**Natural Language Information Retrieval from BIM Models: An LLM-Based Agentic Workflow Approach**。Sylvain Hellin、Stavros Nousias、André Borrmann；EC³ / CIB W78 2025，8 页，DOI 10.35490/EC3.2025.265。**FULL**：[作者全文](https://mediatum.ub.tum.de/doc/1781947/66amsnnaqbygipuftj8b88oqv.2025_HELLIN_EC3.pdf)，已读 pp.2–7 方法、表 1–2、错误分析与局限。[出版社页](https://ec-3.org/publication/ec32025_265/) 题名后半为 *An LLM-Based Multi-Agent System Approach*；同作者、同 DOI，视为题名版本差异。

流程先用 CoT 选择模型与相关工具，再由 ReAct 调用所选 Python 函数，动机之一明确是缩短工具上下文。29 个预置工具支持查询与计算，不生成修改后的 IFC。IFC-Bench-v1 是两个项目、四个专业模型上的 99 问答；直接/间接/信息不足分别 44/29/26 题。七个候选 LLM 中只报告最优 Claude-3.5-Sonnet：LLM 裁判评为 79/99 正确，分组为 42/44、18/29、19/26。20 个错误中，工具错误与缺失共占 45%。[原文 pp.4–7](https://mediatum.ub.tum.de/doc/1781947/66amsnnaqbygipuftj8b88oqv.2025_HELLIN_EC3.pdf)

作者承认人工工具难以完备、提示尚未系统优化；造工具代理属于未来工作。已检查 [数据仓库](https://github.com/sylvainHellin/ifc-bench) 和 [当前 HF 卡](https://huggingface.co/datasets/sylvainHellin/ifc-bench)，当前 v2 与该文 v1 不是同一实验版本，不能把 v2 规模赋给 80% 结果。

**本轮判断：**动态工具预选在 2025 年已实现；缺少预选消融，不能从整体准确率分离其贡献。LLM 裁判、单次运行及少量项目也限制泛化推断。该文适合作为查询方法与工具知识的来源，不宜包装成独立的 IFC 生成基线。

<a id="b12"></a>
## B12 — Adaptive Exploration / Cobbie

**BIM Information Extraction Through LLM-based Adaptive Exploration**。Sylvain Hellin、Suhyung Jang、Stefan Fuchs、Stavros Nousias、André Borrmann；arXiv **2605.01698v1，2026-05-03**，投稿 *Automation in Construction* 的预印本，未据投稿标识当作已录用。**FULL**：[原文](https://arxiv.org/html/2605.01698v1)，已读 §2–7、算法 1、表 2–5、附录 A；[版本记录](https://arxiv.org/abs/2605.01698v1)。

CodeAct 逐步编写和执行 Python，利用返回值与错误探索实际 IFC 结构。可选增强包括 AST 文档分块，dense/BM25/反向问题检索融合重排，以及从训练轨迹创建、修正、独立评估工具，工具库上限 16。语料为 21 项目、37 IFC、1,027 QA；题级分层拆为 513 开发/514 测试。表 3 比较三种代理配置与四种增强：GLM-4.7 无增强 56.0%、文档 56.6%（无显著差异），人工/自动工具均 55.4%；GLM-4.5-Air 文档使 25.7% 升到 30.6%。评价是 LLM 裁判要求四项质量同时通过，**§4.3.2 排除崩溃和超时**。静态基线只执行一次代码。[方法和主表](https://arxiv.org/html/2605.01698v1#S3)

作者承认只测 GLM 家族、单次运行及 IfcOpenShell 特定条件。已检查 [Cobbie 仓库](https://github.com/sylvainHellin/cobbie) 的代码目录和 README；它仍描述 200 题/10 模型/10 配置，与论文不一致，不能认定当前 HEAD 即论文复现快照。它延续 B11 作者线，但扩充数据和方法，不是同一实验。

**本轮判断：**按需探索、API 知识检索、经验工具生成和知识收益消融均有直接覆盖。随机题级切分不证明未见建筑泛化；单次与多轮预算不同，未见成本匹配比较及完整故障分母。本文能提示“强模型＋成熟 API”的知识增益可能很小，不能证明所有知识无用。候选贡献必须明确编译约束、跨项目隔离和实际效率收益。

## 需要保留的版本和分母问题

| 对象 | 已核原文或资源 | 不能采用的合并方式 |
|---|---|---|
| B01 | v3：47 基础场景、324 提示任务；同一编辑有三种引用方式 | 输入/目标 IFC 文件数、提示变体数不能当独立建筑；均分不能当严格成功率 |
| B02 | 每题适用检查通过比例；读取任务占 55/100 | 50.22 部分得分不能解释为 50.22 个完整成功任务；更新评分未穷尽属性保持 |
| B06 | 表 7 合计声明 150/3,300；逐行复算 160/3,520 | 不静默“修正”论文；在作者澄清前保持两个口径 |
| B08 | 引言 48；正文 §4.1.2 与附录 A 列 60 | 采用实际逐题表的分母；5/37/60 为本轮复算成功标记，不是运行复现 |
| B11 | v1 原始实验 99 QA、两个项目、四个模型 | 后续 v2 的新增项目、重新分类和评测不能回填到 v1 结果 |
| B12 论文 | v1 原文 1,027 QA、21 项目/37 IFC；测试类别 72/283/57/102 | §4.3.2 排除系统错误；表 3 的统一 n=514 标注不足以解释各单元实际失败数；Static+Doc 有 † 且缺完整区间/类别表，不能称十二单元证据均完备 |
| 当前 IFC-Bench 卡 | 功能栏 1,027 QA、22 项目/51 IFC；固定测试类别 72/289/50/103；去重附注删除一个跨训练/测试重复问题后为 512+514 | 这与论文快照、卡片未更新总数均有差异；HF 聚合 1,131 行不是独立实验任务数。资源原文见 [版本说明和去重附注](https://huggingface.co/datasets/sylvainHellin/ifc-bench#fixed-evaluation-split-hellin-et-al-2026) |

B12 的原文把迭代上限写成参数 N，但实现细节未给出具体实验值；文档管线声称细节见 §4.4，该节也未完整给出嵌入版本、语料规模等参数。本轮不从当前仓库默认值反推论文配置。其表 1 对 B08“无任意代码生成”的归类还需按边界理解：B08 的确包含受约束计算代码，不能简单写成绝不生成代码；是否允许任意 schema 探索与是否生成任何代码是不同问题。[B12 全文](https://arxiv.org/html/2605.01698v1)，[B08 全文](https://orca.cardiff.ac.uk/id/eprint/186047/1/1-s2.0-S0926580526001299-main.pdf)

## 可并入主矩阵的行

这些行是上述阅读卡的导航，不增加新实验结论。跨论文数字没有统一数据、预算与评估器，不能排序成统一排行榜。

| ID / 状态 | 输入 → 实际输出 | 知识或约束机制 | 评价单位 / 基线性质 | 对候选方法的直接关系 |
|---|---|---|---|---|
| [B01](#b01) FULL | IFC+NL → 编辑 IFC | 原始编码代理；多维变化评分 | 324 提示任务，七模型共享工具预算 | 编辑评价直接先例；增强方法上限未测 |
| [B02](#b02) FULL | 小 IFC+NL → IFC/JSON | 任务级确定性检查 | 100 CRUD 任务，部分得分 | 原子能力先例；保持性覆盖需补 |
| [B03](#b03) FULL | 要求 → IFC+迭代报告 | IDS+生成检查+反馈纠错 | 单案例五轮，无系统对照 | 需求验证闭环直接碰撞 |
| [B04](#b04) PARTIAL | BIM 自动化任务，全文输出协议待核 | 能力分解、多维评价 | 31 任务见片段；完整结果不可核 | 保留相关先例，不引摘要数字证明机制 |
| [B05](#b05) PARTIAL | Revit 脚本任务，完整流程待核 | 错误分类、人工调试 | 20 任务仅摘要来源 | 不能当自主修复成功率 |
| [B06](#b06) FULL | BIM 文本块 → QA/修改建议 | 合成 QA/QRA、LoRA | 语言指标与 LLM 裁判 | 知识训练先例，未测 IFC 生成 |
| [B07](#b07) FULL | BIM → 结构化描述 | 几何/连接 JSON 支持描述 | 四项目、139 房间；两模型 | 反向数据构建候选来源，非可逆证明 |
| [B08](#b08) FULL | IFC+NL → 查询/受限操作 | schema 工具链、缓存、抽样批量执行 | 60 表列任务；三模型；无广义保持评价 | 知识指导操作直接先例 |
| [B09](#b09) FULL | 点云+范围 → IFC/图 | 参数布局、确定性构造与验证 | 房间级重建；传统几何对照 | 编译链先例，输入与整栋文本生成不同 |
| [B10](#b10) PARTIAL | IFC 紧凑表示/交互，全文待核 | 双层编码与重建仅摘要可核 | 实验定义与预算不可核 | 上下文压缩强相关，尚不能定量比较 |
| [B11](#b11) FULL | IFC+NL → QA | 29 工具预选+ReAct | v1 99 QA；最佳模型与 LLM 裁判 | 动态工具预选已实现 |
| [B12](#b12) FULL | IFC+NL → QA/弃答 | 运行探索、文档检索、经验工具生成 | v2 514 测试题；3×4 对照；排除系统错误 | 知识效率主线最直接近邻；需成本与项目隔离补证 |

## BIM-Edit 作者线与实际项目依赖

BIM-Edit 的作者是 B01 所列八人。以下“重合”按姓名逐一核对；它证明作者关系，不证明样本、代码和实验互相独立，也不证明全部作品属于同一个实现。

| 工作 | 与 BIM-Edit 重合作者 | 能核实的实现关系 | 应避免的说法 |
|---|---|---|---|
| BIBIMBAP | 七人：除 Ashwin Nedungadi 外的全部 B01 作者 | 独立命名的 [benchmark 仓库](https://github.com/nbharathik/bibimbap)，本轮未证同一数据/评分实现 | “两支独立团队同时证明”；或“必然同一基准换名” |
| Self-Verification | 四人：Sesterhenn、Nithyanantham、Lüdtke、Bartelt | [README](https://github.com/Tsesterh/Text2BIM-Self-Verification) 明示依赖 MCP4IFC 对应旧仓库 | 仅写作者重合而漏掉工具依赖；把示例当独立大样本复制 |
| MCP4IFC | 五人：Nithyanantham、Sesterhenn、Nedungadi、Bartelt、Lüdtke | [旧仓库](https://github.com/Show2Instruct/ifc-bonsai-mcp) 对应论文项目线；MCP4IFC 正文在主报告另卡审读 | 用作者重合推定 B01 的单 Python 工具就是其工具套件 |
| IFC-Copilot | 同上五人 | [官方项目页](https://show2instruct.github.io/ifc-copilot/) 作者为 Nithyanantham、Sesterhenn、Nedungadi、Sergio Peral Garijo、Janis Zenkner、Bartelt、Lüdtke，与 MCP4IFC 名单一致；Paper 链接实际返回 404 | 把项目网页当已读新论文，或自动增加一个独立基线 |
| Qwen-BIM | 无 | 作者为 Lin/Cai/Ni/Zhou/Pan；未发现此作者线的实现依赖证据 | 因同用 IFC/LLM 而称同一项目 |
| Building Descriptor | 无 | Jang/Borrmann/Lee；与 B12 重合 Jang、Borrmann，与 B11 重合 Borrmann | 把描述生成直接并入 BIM-Edit 作者线 |
| IFC-Bench v1 / Cobbie | 无 | B12 明确引 B11 为前作，共享 Hellin/Nousias/Borrmann，数据 v2 扩展 v1；B12 另有 Jang/Fuchs | 将两文或数据版本当互不相关的独立复制 |

[旧 Show2Instruct 仓库](https://github.com/Show2Instruct/ifc-bonsai-mcp) README 指向后续 [bonsai-mcp](https://github.com/Show2Instruct/bonsai-mcp)。仓库迁移与代码生成方向变化是项目演进证据；后续 HEAD 不自动等于 MCP4IFC 的工具快照，更不等于 B01/B02 的受限基线。完整比较应分别登记“论文版本、实现快照、工具依赖、数据复用”，不能用作者数量或项目名称数量充当独立证据数量。
