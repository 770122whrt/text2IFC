# text2IFC 文献综述·完整版

更新：2026-09-18。本文件统一收录三模块逐篇矩阵及后续重点核查；[简版](literature-review-short.md)用于讨论，[研究方案](research-plan.md)决定当前RQ0、D1/D2及实验；IFC Repair 投稿专项另见 [Repair 专项矩阵](../repair-demo/repair-literature-matrix-20260921.md)。旧N01–N08、P1/P2/V1/L1仅表示调查当时的问题，不再是并行推荐路线。

**证据口径。** F：已有记录列明所读版本的方法、实验及相关限制；不是本轮重新阅读了所有全文，也不表示复现。P：仅部分正文/项目/书目信息，缺口保持开放，不能用它证明对方没有某项能力。本轮在既有 TileGPT、ChopChop 与 SCOPE 核查基础上新增 Wu 等 2026 IFC alteration 近邻的出版商摘要/正文片段核查；其余整合2026-09-14至18的阅读记录。此综述围绕选题，不宣称系统检索穷尽。

每条保留名称与来源、贡献、实验场景及边界、与text2IFC的冲突。共134条研究记录，其中118条F、16条P。原始104条矩阵整体保留；后续对同文的核查链接合并，不以重复卡片增加论文数量。记录包含论文、基准、综述和项目，因此条目数不等于独立论文或系统数。更新卡若补充旧行，以明确版本和更完整的核查为准；作者结果与本项目比较判断分开。

**当前结论。** Self-Verification限制闭环首创说法；Wu 等 2026 的 component alteration 工作进一步限制“verification 后自动 BIM repair/alteration”的首创说法；TileGPT限制多解/约束组合说法；ChopChop与SCOPE限制约束输出和执行分工说法。Repair 方向若继续投稿，增量应具体落在目标/属性执行权威、原子 ChangeSet、fail-closed、reopen 验证与 non-target preservation 等可替换系统语义，而不是泛称“LLM 自动修 BIM”。D1/D2 两条研究方向仍均未证实方法创新。

**历史编号说明。** N01技能修订；N02组合能力；N03修复迁移；N04空间约束；N05信息动作；N06澄清；N07表示搜索；N08知识组合。表内对这些问题的冲突分析仍有参考价值，不能把原建议措辞理解为当前排期。

**旧扩展矩阵的整合说明（2026-09-23）。** [扩展调研索引](https://github.com/770122whrt/text2IFC/blob/c58888fb5eb10aceb25e03e1eb8b4f8262074e38/docs/reports/generation-demo/novelty-literature-addendum.md)中的 41 张全文阅读卡对应 40 篇不同论文：FK04 与 SK02 是 ExpeL 的不同版本／专题阅读，合并计数但分别保留原卡。DepthBenchCAD 仍是 P；AIDL 所读 v1 不代表正式 CGF 版已全文核对；未披露的精确测试分母继续留在卡片中，不反推补数。四组原始证据入口为[知识](literature-evidence/frontier-knowledge.md)、[技能](literature-evidence/frontier-skills.md)、[空间](literature-evidence/frontier-spatial.md)、[规格与关系](literature-evidence/frontier-reasoning.md)。本次只是收拢旧索引的计数与版本说明，没有新增文献、升级 F/P 或恢复旧 N01／N06 优先级。



## 1. BIM / IFC：生成、编辑、表示与评价

直接领域先例已经覆盖自然语言建模、领域工具和自验证。当前系统重点比较受控修改与非目标保全；D1/D2仍需额外机制与实验。

本模块30条研究记录。

| Paper：名称、版本与原始来源 | 贡献与观点 | 实验场景与证据边界 | 与我们的冲突点 |
|---|---|---|---|
| **Interactive Design by Integrating a Large Pre-Trained Language Model and Building Information Modeling**<br>A01 · F；arXiv 2306.14165v1，2023-06-25；Computing in Civil Engineering 2023 正式条目于 2024 上线，定稿未核<br>[作者全文 v1](https://arxiv.org/pdf/2306.14165v1)；[ASCE 正式条目](https://ascelibrary.org/doi/10.1061/9780784485231.035) | 将已有 Revit 模型的任务相关属性与拓扑抽成 XML，让 GPT 修改后确定性写回。论文已明确针对 IFC STEP 的 token 负担选择紧凑表示；GAIA 是此版本中间模块名。 | 一个 Villa Savoye 模型、48 面墙、五类细化标签；GPT-3/3.5/4 各提示预测五次取众数。GPT-4 accuracy 0.83、F1 0.62，属于分类/细化结果。<br>边界：单案例、稀少类别且含人工复制输入输出，不能换算整栋生成成功率；正式定稿和公开实现未核，不能套入后续 NADIA 细节。 | 已覆盖 text2IFC 的任务属性选择与压缩动机。N08 必须证明知识组合的执行协同，而不能以 XML 换 JSON 作为贡献；N05 的增量也须超出静态抽取任务字段。 |
| **Towards a copilot in BIM authoring tool using a large language model-based agent for intelligent human-machine interaction**<br>A02 · F；EG-ICE 2024，pp.403–412；核查 arXiv 2406.16903 作者正文<br>[作者全文](https://arxiv.org/pdf/2406.16903)；[机构会议书目](https://portal.fis.tum.de/en/publications/towards-a-copilot-in-bim-authoring-tool-using-a-large-language-mo/) | 自然语言或语音驱动 Python 调用 Vectorworks 高层工具，建楼工具封装 Marionette 工程流程；软件文档 RAG、解释器异常、对话变量与人工反馈共同辅助执行。 | 1911 份 HTML 转 Markdown 后检索前两项。展示生成与连续编辑；另外 20 个问答的 RAGAs faithfulness 为 99.5%，这是问答忠实度，不是建模完成率。<br>边界：工具覆盖、选择幻觉与环境感知受限；未核实论文专属公开代码/评测数据。软件 SDK 示例不等于论文实现。 | N02 的技能扩展不能仅新增高层函数，N05 不能仅增加文档检索。text2IFC 需显示如何选择信息动作或修订技能适用条件，并对齐双方工具、模型和预算。 |
| **Text2BIM: Generating Building Models Using a Large Language Model-based Multi-Agent Framework**<br>A03 · F；arXiv v1（2024-08-15）和 v2（2025-07-11）分别核查；JCCE 40(2),04025142（2026）定稿未核<br>[v1 全文](https://arxiv.org/html/2408.08054v1)；[v2 全文](https://arxiv.org/html/2408.08054v2)；[正式 DOI](https://doi.org/10.1061/JCCEE5.CPENG-6386)；[作者代码](https://github.com/dcy0577/Text2BIM) | 四代理分担需求增强、方案、编程、审阅。高层 Vectorworks 工具执行建模，内层报错修代码，外层用导出 IFC 的 Solibri 问题继续修订。 | v1：10 提示×3 模型×5=150 运行、391 IFC；v2：25×3×3=225 运行、534 IFC，均含中间输出且不能跨版本合并。v2 有 30 项检查及四位专家评 75 个模型。<br>边界：早期基本构件范围，少量导出/保存仍人工；存在删墙降错误却破坏完整性、重建产生重复冲突。部分资产需索取，代码依赖商业软件。 | N03 不能把生成内自修复称新，需证明修复经验跨任务预防错误；N01/N02 要超出固定角色与高层工具，N04 要超出普通反馈重建，并同时约束需求与既有模型保留。 |
| **BIMgent: Towards Autonomous Building Modeling via Computer-use Agents**<br>A04 · F；arXiv 2506.07217v2，2025-06-30；ICML 2025 Workshop on Computer Use Agents，非主会<br>[版本记录](https://arxiv.org/abs/2506.07217)；[v2 全文](https://arxiv.org/html/2506.07217v2)；[作者仓库](https://github.com/ZihanDDD/BIMgent) | 文本或平面图经分割和层级规划，通过 GUI 在 Vectorworks 建模；软件文档检索、截图定位、监督代理和动作批处理共同支持执行。 | 25 任务分五组，完成 8/25=32%，两种通用代理为 0%；两千余动作及构件子任务另计，不能作为独立建筑。opening 成功率表 1 的 95.12% 与正文 92.68% 不一致。<br>边界：混合系统和基线使用模型不完全相同，不能把总差值归因单一知识机制；GUI 效率、跨软件泛化及规模有限。已查仓库，未运行。 | N05 的主动信息选择必须区别于既有文档、截图和反馈组合；N06 要比较澄清策略而非只增交互界面。对 text2IFC，主要价值是动作成功与整任务成功分开评价。 |
| **Large language model driven BIM collaborative automatic trestle-bridge modeling technology**<br>A05 · F；Journal of Engineering and Applied Science 73,272（2026），正式全文<br>[出版商全文](https://link.springer.com/article/10.1186/s44147-026-01130-3)；[正式 PDF](https://link.springer.com/content/pdf/10.1186/s44147-026-01130-3.pdf) | 参数合同、默认补全、工程规则与族库指导几何基准和布置计划，再生成 Revit 函数调用并局部纠错；明确用参数化抽象减少密集坐标及 token 负担。 | 200 案例含 50 实际、150 模板模拟，各重复三次。API 成功率 95.1%、规则符合率 92.4%；移除工程规则后符合率 55.3%。77 案例触发纠错，65 成功。<br>边界：比较含启发式工程规则 HE、规则脚本和单代理；HE 不是人工专家。数据需索取、代码未核，非定 token 比较；工程符合率也非完整 IFC/力学验算。 | 参数知识、几何抽象、执行和修复已有高碰撞先例。N02 须研究组合失败怎样反向修订抽象，N03 须证明跨任务迁移，N08 须区分执行协同与简单规则有无。 |
| **Knowledge-driven automated prefabricated bridge modeling from natural language using LLM and RAG**<br>A06 · F；Scientific Reports 16,23838（2026），正式全文<br>[出版商全文](https://www.nature.com/articles/s41598-026-53765-0)；[正式 PDF](https://www.nature.com/articles/s41598-026-53765-0.pdf) | GLM4-9B 与人工核查标准图集 RAG 抽取结构参数，交给 Rhino/Grasshopper 建模，明确支持 3dm 和 IFC 导出；知识主要是特定预制桥图集。 | 核心为广州一个预制箱梁桥、两种指令；200+ 是参数数目。作者报告参数准确率 100% 对纯 LLM 44.5%，耗时 210 秒对工程师约 4 小时；去 RAG 为 54.8%，去结构提示为 77.6%。<br>边界：参数准确率与其任务成功定义不同；不能写成 200 多建筑泛化实验。知识整理劳动、全部重试成本、额外稳健性样本分母未充分交代。 | N05/N08 不能只把标准资料接进 RAG。text2IFC 的候选增量应是何时查询/探测、知识如何相互作用及未见条件泛化；不能用“不输出 IFC”制造差异。 |
| **A Multiagent Large Language Model–Based System for Early-Stage Building Layout Planning**<br>A07 · P；JCCE 40(6)（2026），2026-08-07 在线；仅书目和摘要<br>[ASCE 原始条目](https://ascelibrary.com/doi/10.1061/JCCEE5.CPENG-7723) | 摘要描述多代理需求规划、气泡图、执行规则与 LLM director，并涉及多模态 RAG、扩散布局和 Tell2Design 比较。这里记录公开研究定位，尚未取得连续方法正文。 | 实验任务、模型版本、样本独立单位、重复次数、比较配置和主结果表均未完成全文核查；不能提供已确认的效果数字。<br>边界：没有读到限制节和完整布局评价，不能用摘要重建算法，也不能据全文不可得推断其缺少关系约束、知识选择或人机反馈。 | 这是 text2IFC 空间规划近邻。N04 的跨层依赖开放、N06 的意图澄清可能有交集，但具体覆盖未知，应作为创新判断缺口保留，而非先宣布已排除。 |
| **AI BIM coordinator for non-expert interaction in building design using LLM-driven multi-agent systems**<br>A08 · P；Automation in Construction 180,106563（2025）；出版商预览/机构条目<br>[出版商原始页](https://www.sciencedirect.com/science/article/abs/pii/S092658052500603X)；[作者机构记录](https://pure.psu.edu/en/publications/ai-bim-coordinator-for-non-expert-interaction-in-building-design-/) | 可读材料描述面向非专家的 Revit/AutoGen 多代理交互，以 assistant、checker、sender、executor、terminator 等角色结合知识技能、代码执行和检查。 | 完整任务数、模型配置、重试、人力和结果分母未核实；方法与结果仅有章节片段。不能借用作者 AHFE 2024 前作的实验数字。<br>边界：知识库建造方式、几何/拓扑检查范围和编译约束未取得连续正文依据；不能把已见的语义知识定位说成没有知识，也不能称实验已复现。 | N02 的能力扩展和 N05 的知识利用均需区别于现有技能执行与检查；对 text2IFC 是否覆盖动态适用条件或信息动作选择，当前证据不足，必须保持未知。 |
| **An LLM-Integrated BIM Workflow for Rapid Early-Stage Layout Generation of Worksite Trailers**<br>A09 · F；ISARC 2026，pp.2481–2487；DOI 10.22260/ISARC2026/0317<br>[会议论文页](https://www.iaarc.org/publications/2026_proceedings_of_the_43rd_isarc_singapore/an_llm_integrated_bim_workflow_for_rapid_early_stage_layout_generation_of_worksite_trailers.html)；[会议全文](https://www.iaarc.org/publications/fulltext/ISARC2026_1215.pdf) | GPT-4o-mini 将语言和尺寸转为 JSON 数据层，经 Revit API 生成房间边界、墙、洞口和标签；以属性匹配检索历史案例，用户选择复用并在视图中迭代。 | 展示工地拖车早期布局的功能原型和生成/复用流程，未给系统性样本数、受控计时对照或自主完成率。<br>边界：范围主要为正交模块和小案例，规范与后续工程任务尚未完成；“快速”功能定位不等于经过定量实验验证的时间优势。 | Demo 展示形式与 text2IFC 直接相邻。N02 若只是复用旧模块、N06 若只是加交互视图，方法差异不足；需研究组合适用条件或有信息价值的澄清选择。 |
| **BIMVLM: A vision-language model for iterative generation of component BIM models**<br>A10 · P；Expert Systems with Applications 315,131765（2026）；方法/结果片段<br>[出版商原始页](https://www.sciencedirect.com/science/article/pii/S0957417426006780)；[正式 DOI](https://doi.org/10.1016/j.eswa.2026.131765) | 已读片段将多视图和自然语言映射为构件动作序列，再转可执行代码迭代生成；基于 LLaVA/LoRA，借助 DeepCAD、Text2CAD 序列的语言化资料。 | 完整训练/测试数量、划分隔离、模型版本、迭代停止准则、主表和基线条件尚未核实，不能据片段报告已确认的性能优势。<br>边界：对象是构件级模型，不能直接推成整栋 IFC 的宿主、包含和跨构件关系正确性；涉及微调，也不等同当前固定模型下的推理机制。 | N02 的可执行动作抽象、N07 的视觉/表示修正有相邻内容，具体机制覆盖未知。text2IFC 应明确无训练候选改变了什么，并区分构件几何和整模型语义。 |
| **Automated detailing of exterior walls using NADIA: Natural-language-based architectural detailing through interaction with AI**<br>A11 · P；Advanced Engineering Informatics 61,102532（2024）；出版商正文预览<br>[出版商原始页](https://www.sciencedirect.com/science/article/pii/S1474034624001800)；[作者机构记录](https://pure.seoultech.ac.kr/en/publications/automated-detailing-of-exterior-walls-using-nadia-natural-languag/)；[作者预印本入口](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4674577) | 研究外墙细化：从要求确定材料、厚度及性能相关参数，以 assistant/consultant 方式帮助用户补充知识和细化模型；已读介绍、验证与讨论片段。 | 摘要出现的 240/1920 和 83.33%/98.54% 尚未核对完整实验单位与分母，因此不列为本次确认结果。完整基线、干预和停止规则待正文。<br>边界：不能将 GAIA、NADIA、NADIA-S 当作同一版系统，或将后续语音框架实验补到此文。材料与性能知识的覆盖范围也未完整核实。 | N05 的领域知识供给、N06 的交互澄清已有相邻研究。text2IFC 若研究最少有效澄清，需证明问题选择改变可执行结果，而非只重新提供聊天式参数补全。 |
| **A Generalized LLM-Augmented BIM Framework: Application to a Speech-to-BIM system**<br>A12 · F；CIB W78 2024，Marrakesh；arXiv 2409.18345，核查会议正文<br>[会议全文](https://eres.scix.net/pdfs/w78-2024-paper_155.pdf) | 提出解释、补全、匹配、结构化、执行、检查六阶段；将术语和单位映射成 JSON，再调用预定义 Revit 函数。NADIA-S 使用语音输入和领域适配模型。 | Revit 2024、Whisper、微调 GPT-3.5/GPT-4；8 个墙提示各 30 次，共 240 次细化。检查前为 92.50%/91.66%，重复执行到检查通过后报告 100%。<br>边界：未给固定重试或 token 上限，故 100% 不能当作首轮或预算内成功；任务集中在墙细化，也没有证明完整模型的一致性和跨任务迁移。 | N03 的执行—检查—修正循环已有直接先例，创新需落在经验如何预防新生成错误；N05 的术语知识匹配也非空白。text2IFC 应计入所有失败轮次与成本。 |
| **BIM–LLM integration in AECO workflows: Applications, validation, and future directions**<br>A13 · P；Automation in Construction 187,106905（2026）；综述，PRISMA 方法/结果预览<br>[出版商原始页](https://www.sciencedirect.com/science/article/abs/pii/S0926580526001469)；[作者机构记录](https://pure.skku.edu/en/publications/bim-llm-integration-in-aeco-workflows-applications-validation-and/) | 这是一篇 BIM–LLM 领域综述，按生命周期应用与技术/工业验证组织文献，讨论系统集成及后续方向；并非新的生成系统或算法基线。 | 摘要称纳入 61 篇，但检索截止、排除标准、编码规则和提取表没有完成正文复核；摘要中的类别百分比不作为本次已核实统计。<br>边界：取得的是 PRISMA 和结果章节片段，不能以其二次转述替代原论文的方法、分母与实验限制，也不能认定覆盖所有 2026 新作。 | 可帮助 text2IFC 组织 motivation 和验证层次；不能用综述分类的空白证明 N01–N08 新颖，亦不能将技术验证、工业验证和定预算任务成功混成同一种证据。 |
| **Bridging Building Information Modelling and Natural Language Processing: A Systematic Review on Current Applications and Limitations**<br>A14 · F；ISARC 2026，pp.1888–1895；系统综述，DOI 10.22260/ISARC2026/0241<br>[会议全文](https://www.iaarc.org/publications/fulltext/ISARC2026_1081.pdf) | 按 Fink 流程在六库检索 BIM/NLP 同义词，分类应用、任务和 NLP 技术，讨论严格模型结构与概率语言系统结合的困难；它是二级综述而非生成方法。 | 截止 2025-05，初始 430 条、纳入 92：78 研究、11 综述、3 案例。部分任务分类分母为 85，NLP 分类为 81；Modify 为 12/81，类别可多标。<br>边界：2026 出版不代表覆盖 2026 系统；筛选期与分类粒度限制结论，未提供统一生成基准或效果量元分析，不能从类别占比推出质量高低。 | 为 text2IFC 的语言到结构动机提供背景，但 N01–N08 仍须各自对照原方法。尤其“自然语言与结构模型之间有鸿沟”已是公共问题陈述，不能单独作创新。 |
| **MCP4IFC: IFC-Based Building Design using Large Language Models**<br>D02 · F；arXiv 2511.05533v1（2025），预印本；完整题名由主任务补核<br>[v1 全文](https://arxiv.org/html/2511.05533v1)；[作者仓库](https://github.com/Show2Instruct/ifc-bonsai-mcp) | IFC 工具、结构化场景信息、文档向量检索与动态 Python/IfcOpenShell 执行组合，支持问答、编辑和生成；同团队后续发展为 IFC-Copilot，不能当互不相关谱系。 | Duplex 的 65 QA：GPT-5 mini 54/65、Sonnet 4.5 49/65，部分模糊答案乐观接受；另有 8 语义编辑、6 生成例，分母不能混合。<br>边界：direct-query 计数正文/表格 26/25 不一致；生成存在洞口、包含、材料或 Pset 缺失。约 40k token 工具定义和动态预选已讨论，预选在该版尚属方向。 | N02/N05/N08 不能把原生 IFC、知识检索、动态代码和 loop 整体称新。text2IFC 要证明新技能适用边界或信息选择机制；少量演示失败不能代表增强代码代理能力上限。 |
| **IFC-Copilot**<br>D03 · P；后续项目页与新版仓库；未取得论文全文，不作为独立已读论文<br>[作者项目页](https://show2instruct.github.io/ifc-copilot/)；[新版仓库](https://github.com/Show2Instruct/bonsai-mcp) | 项目页介绍 52 个工具、代码执行及读取/创建/修改能力。旧 MCP4IFC 仓库直接链接此新版仓库，能够建立作者和实现演进关系，不能重复算两套独立方法。 | 页面报告 100 个自定义任务、最高 86%；这是项目自报，未核实论文实验模型、评测器、失败分母和成本，不纳入已读正文结果比较。<br>边界：Paper 链接在本轮返回 404，未取得替代全文；当前代码也不能自动等同页面实验快照。项目可用和结果可复现是不同证据。 | 必须纳入 text2IFC 最近系统，N01/N02 的动态技能及 N05/N08 的知识利用不能在全文缺失时宣称未被覆盖。候选的具体冲突应保持待核，不凭项目规模先下优劣结论。 |
| **Automated building component alterations driven by LLM-formalized human strategies to achieve code compliance**<br>RPR01 · P；Automation in Construction 190,107148（2026）；本轮核查出版商摘要、Highlights 与公开正文片段<br>[出版商原始页](https://www.sciencedirect.com/science/article/pii/S0926580526003894)；[作者代码](https://github.com/Jaaaaabin/AutoComplianceWu) | 从 ACC/BCF issue 出发，用 LLM 将 designer-authored improvement strategies 形式化为可执行 building-component operations；结合 violation 的拓扑关联构件实例化 alteration，并对修改后的模型重新评价以搜索 feasible alterations / resolution clusters。作者明确把 LLM 定位为 semantic formalization layer，修改范围仍由 designer input 治理。 | 论文以 IBC spatial requirements case study 演示跨相互依赖 compliance issues 的 alteration；本轮未完整逐表复核全部实验分母、候选数和定量结果，因此保留 P，不用摘要重建性能结论。<br>边界：目标是合规方案探索而非通用自然语言 repair；已有 improvement strategy 是重要输入，不能直接等同自由用户请求；本轮也未确认其是否具备与 text2IFC 相同的原子多操作 rollback、reopen publish gate 或 non-target preservation 合同。 | **直接限制 Repair 首创说法。** “verification 后自动修改 BIM”“LLM 将人类策略转成 component-level alteration”“用 topology 扩展相关修改对象”均已有直接先例。text2IFC 若投稿 Repair，应把差异收紧到自然语言 request 的 target/property authority、atomic ChangeSet、fail-closed、reopened IFC verification 与 non-target preservation，并逐项证明，而不是泛称自动修复。 |
| **BIM-Edit: Benchmarking Large Language Models for IFC-Based Building Information Modeling**<br>B01 · F；arXiv 2606.20146v3，2026-06-23，预印本<br>[v3 全文](https://arxiv.org/html/2606.20146v3)；[任务卡](https://huggingface.co/datasets/BIM-Edit/BIM-Edit-Tasks)；[IFC 资源目录](https://huggingface.co/datasets/BIM-Edit/BIM-Edit/tree/main) | 针对已有 IFC 编辑，以变化部分的几何距离、类别/属性语义和关系图 F1 联合评分。七个模型统一使用单一 IfcOpenShell Python 执行工具，最多 20 次调用，无检索或 schema 专用工具。 | 11 真实与 36 合成基础场景，共 47 场景、324 提示变体，创建/更新/删除各 108。最佳均分 49.48/100；三项均达 0.98 的最高比例仅 3.4%，均分不是成功率。<br>边界：同目标的直接/空间/拓扑提示非独立建筑；单一目标可能处罚合理替代，六类构件与评分权重有限。受限代码基线不能代表增强代理上限。 | 联合评价已存在，不能作为 text2IFC 新方法。N01–N04 应用其任务检查技能/修复的完整性；N07/N08 需与同预算强代码代理比较，不能靠限制基线证明优势。 |
| **BIBIMBAP: A Benchmark for Instructional BIM-Based Automated Programming**<br>B02 · F；EC³ 2026，8 页，会议正文<br>[会议全文](https://ec-3.org/wp-content/uploads/2026/08/EC32026_271.pdf)；[作者仓库](https://github.com/nbharathik/bibimbap) | 以自然语言、小 IFC 和确定性 Python 检查评估 CRUD；读取任务另约束 JSON。直接、几何、拓扑、数值、概念五类各 20 题，适合拆分原子能力。 | 100 题的 CRUD 为 15/55/15/15；统一 25 次调用，六模型中前三个重复三次。Opus 4.6 的 50.22±0.22 是逐题适用检查通过比例的平均，不是完成率。<br>边界：更新未评非几何属性保留，删除重建可能判正确；任务短、缺多轮互动。与 BIM-Edit 作者重合不意味着共享实现或独立样本可以相加。 | N01–N03 的新技能或经验若只提高已检查项，仍可能破坏其他属性。text2IFC 可借原子切片，但必须新增保全检查；N04 不能把删除后重建算正确局部修订。 |
| **A Self-Verification Framework Toward Reliable Text-to-BIM Generation**<br>B03 · F；EC³ 2026，2 页短文<br>[会议全文](https://ec-3.org/wp-content/uploads/2026/08/EC32026_444.pdf)；[作者原型仓库](https://github.com/Tsesterh/Text2BIM-Self-Verification) | 首轮将要求分成 IDS 与非 IDS；Modifier 用 MCP4IFC 工具和代码生成/修改，IfcTester 检查 IDS，Verifier 生成补充 Python 检查，再将结果反馈下一轮。 | GPT-5.2 在一个住宅案例运行五轮，部分构件与围护改善，但 IfcSpace 与 IfcBuildingStorey 关联始终未修好。没有系统间比较、总体成功率或独立消融。<br>边界：初始规范遗漏会进入后续验证；自动生成检查不保证覆盖全部需求。仓库是研究原型，本轮未运行，生成内部纠错不等于受损 IFC 修复基准。 | 直接覆盖 text2IFC 的需求分解、双类检查和生成自修复。N03 要证明修复知识迁移到未见生成任务，N04 要提出跨层依赖选择，而非增加验证代理或循环次数。  <br>补充核查见[本条更新](#update-22)。 |
| **Reliable LLM-driven BIM automation through capability-based multi-dimensional evaluation**<br>B04 · P；Automation in Construction 187,106910（2026）；章节片段<br>[正式 DOI](https://doi.org/10.1016/j.autcon.2026.106910)；[出版商原始页](https://www.sciencedirect.com/science/article/pii/S0926580526001512)；[作者机构记录](https://digitalcommons.mtu.edu/michigantech-p2/2484/) | 可读片段确认面向 BIM 自动化的能力切片和多维评价，讨论错误、可靠性与人工修正；完整六维操作定义尚未取得。 | 片段提到 31 个任务，任务独立性、提示工具、人员介入、失败分母、基线和统计方法未核。摘要中的 API 错误占比及可靠性数字不进入已证实比较。<br>边界：只有方法/任务/结果/讨论的零散预览，不能说已完成评价复核。与 Error Taxonomy 同作者组，但 31 与后者摘要的 20 不应相加，复用关系未知。 | 多维可靠性并非 text2IFC 空白。N01–N08 要给各自可证伪的机制实验，而非重新命名能力分组；全文不足也不能用于断言其没有知识或失败归因方法。 |
| **Error Taxonomy and Failure Analysis of Large Language Models for BIM Scripting**<br>B05 · P；Construction Research Congress 2026，pp.376–385；2026-08-27 在线，摘要/元数据<br>[ASCE 原始记录](https://ascelibrary.org/doi/10.1061/9780784486979.036)；[出版商 PDF 入口（全文未取得）](https://ascelibrary.org/doi/epdf/10.1061/9780784486979.036) | 摘要描述 GPT-4 为 Revit 编写 Python，由人参与迭代调试并提出十类错误。这是已有 BIM 脚本失败分析线索，分类定义和编码一致性尚未读到正文。 | 20 个任务是摘要所述规模；完整试验次数、人工改写劳动、预算、最终停止和失败事件分母均未知。人工引导后完成不能当自主代理 100% 成功。<br>边界：方法、结果表和讨论全文未取得，不能用同作者另一文补齐，也没有核实对应公开数据/代码。记录 P 是读取状态，非论文质量评价。 | N01/N03 可借问题定位，但分类本身不等于可迁移技能条件。text2IFC 不能声称首次系统分析 BIM 错误；应区分任务、失败尝试与人工修正，并验证反例是否改善新任务。 |
| **Qwen-BIM: developing large language model for BIM-based design with domain-specific benchmark and dataset**<br>B06 · F；arXiv 2602.20812v1，2026-02-24；记录页有 Qwen-BIM 前缀，PDF 题名无此前缀<br>[版本记录](https://arxiv.org/abs/2602.20812v1)；[v1 全文](https://arxiv.org/pdf/2602.20812v1) | BIM 局部空间块转文本，22 类问题模板生成 QA，再筛推理答案，对 Qwen2.5-14B 做 LoRA；任务为问答、文本异常识别与修改建议，未验证 IFC 生成。 | 候选训练数据 3493 条，最佳配置用 1364 QRA；GLM-4-plus 裁判 G-Eval 0.689→0.834，约相对 21%。表 7 总称 150 块/3300 QA，分项相加却为 160/3520。<br>边界：训练轮次与数据配比共同变化，不能单归因推理监督；未证明项目隔离，数据需索取。语言分数不代表几何或修复执行成功。 | 领域微调及合成知识并非 text2IFC 首创。N01/N03 若坚持同模型外部经验，需要另测执行迁移而非复用 QA 分数；N05/N08 也须区分标准知识、实例事实和训练记忆。 |
| **Automated Natural Language Building Descriptor for Building Information Models**<br>B07 · F；EC³ / CIB W78 2025，8 页，TUM 作者稿<br>[作者机构全文](https://mediatum.ub.tum.de/doc/1798649/mb4eded1rj089k4ppdqlxcgti.BIM_description_LLM_EC3_2025_CameraReady_Final.pdf) | 从 Revit 抽取空间轮廓、面积、用途以及门窗楼梯连接，构成关系 JSON，再用 o1/DeepSeek-R1 生成六类建筑描述。研究方向是 BIM→语言。 | 四项目、139 房间；o1 四个房间数均正确，R1 三项目漏数。拓扑描述错误率 o1 为 0/10.75/10.70/4.13%，R1 为 9.47/24.90/19.38/31.78%，分母是描述内容。<br>边界：复杂形状、方向、邻接/围合仍易出错；未验证由描述反向建模，也未核实公开配对训练集。不能默认自动描述完整或可逆。 | 为 text2IFC 构造要求和反向数据提供参照，但 N06 需面对遗漏而非拿自动描述当用户真意；N07 的参考系/方向修正需独立几何验证，不能只依赖同一语言描述器。 |
| **Multi-agent framework for schema-guided reasoning and tool-augmented interaction with IFC models**<br>B08 · F；Automation in Construction 186,106888（2026），25 页开放正文<br>[正式 DOI](https://doi.org/10.1016/j.autcon.2026.106888)；[Cardiff 开放全文](https://orca.cardiff.ac.uk/id/eprint/186047/1/1-s2.0-S0926580526001299-main.pdf) | 用 schema 指导原子工具串联，缓存实体和流程；先探索少量同类实体，再将工具链交给确定性批处理，另允许受约束计算代码。 | 正文/附录列三 IFC 上 60 查询/操作，引言却写 48。逐行复算成功标记：GPT-3.5/4o-mini/4o 为 5/37/60；仅作者表格复算，无重复试验。扩展最多 427 个目标实体。<br>边界：假设同类实体表示足够一致，缺修改后模型一致性验证；复杂几何/语义依赖尚有限。与图查询工具的比较是定性，数据需索取。 | N05 的实例探索、N02 的工具组合已有直接先例。text2IFC 的增量可检验何时样本不足、何时必须探测异质实例；N01 的适用条件不能仅继承同类一致假设。 |
| **LLM-enabled multi-agent framework for automated Scan-to-BIM and Scan-to-Graph reconstruction**<br>B09 · F；Automation in Construction 188,107003（2026），18 页正文<br>[正式 DOI](https://doi.org/10.1016/j.autcon.2026.107003)；[Cambridge 记录](https://www.repository.cam.ac.uk/items/acda5588-8321-4f94-bb9b-30014bea1d54)；[开放全文](https://www.repository.cam.ac.uk/bitstreams/bacf072d-a9b5-4a68-97fb-88069714f628/download) | 点云与语言范围经 Qwen、SpatialLM 形成参数布局，再做墙连接、闭合、确定性 IFC4 构造、图生成与检查；不是每个模块都由 LLM 执行。 | 25 范围指令中正确分类 24；TUM CMS 六房间的面积 MAE 约 1.45/1.51 平方米，传统对照 0.87/1.23。另测 S3DIS 五房间的构件遗漏及合成例。<br>边界：范围偏规则室内和房间级，遮挡造成门窗缺失；图主要相对自身生成布局验证，不能当独立整栋真值。未核实公开实现。 | 参数到确定性 IFC/图的链条已有先例。N04 应区别于固定墙连接/闭合规则，N07 应使用独立几何检查；text2IFC 纯文本不具有点云输入的同等几何证据。 |
| **A Dual-Layer Semantic-Lossless IFC Encoding for LLM-Readable Building Model Interaction**<br>B10 · P；SSRN 6532559，2026-04-07 上传，41 页预印本；仅摘要/元数据<br>[SSRN 原始记录](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6532559) | 摘要提出分离 IFC 空间层级与几何参数，并按需重建文件，属于紧凑模型编码的直接近邻；尚未取得编码、解码方法正文。 | 字节压缩比、token 降幅、QA 准确率与 45 次生成都是未完成正文复核的摘要报告，本条不将它们作为已确认实验成绩。<br>边界：解码是否依赖 sidecar、模型实际可读的语义、建筑独立单位、输入匹配、检查覆盖与全部成本未知；这些是待核问题，不能冒充作者已经暴露的缺陷。 | 与 text2IFC 上下文效率高度相关。N07 的表示搜索须区别于可逆压缩，N08 须证明执行知识组合价值而非仅降低长度；在全文缺口解决前，不能宣称编码/重建无人做过。 |
| **Natural Language Information Retrieval from BIM Models: An LLM-Based Agentic Workflow Approach**<br>B11 · F；EC³ / CIB W78 2025；DOI 10.35490/EC3.2025.265；出版页题名后半为 An LLM-Based Multi-Agent System Approach<br>[作者全文](https://mediatum.ub.tum.de/doc/1781947/66amsnnaqbygipuftj8b88oqv.2025_HELLIN_EC3.pdf)；[会议出版页](https://ec-3.org/publication/ec32025_265/)；[IFC-Bench 仓库](https://github.com/sylvainHellin/ifc-bench) | 先用 CoT 选择模型和相关工具，再由 ReAct 调用 29 个预置 Python 查询/计算工具；缩短工具上下文是明确动机，不输出修改后的 IFC。 | 两项目、四专业模型上的 99 QA，直接/间接/不足信息为 44/29/26。七候选模型只报告最优 Claude-3.5-Sonnet：LLM 裁判 79/99；20 错误中工具错误/缺失占 45%。<br>边界：没有工具预选消融、单次运行且项目少；造工具代理当时仍属未来工作。当前 v2 数据卡规模不能赋给 v1 的结果。 | N05 的选择工具、N08 的减少工具上下文已有直接先例，需检验新的选择目标与完整成本。text2IFC 可引用查询知识机制，但不能将 QA 成绩作为生成/修复 baseline。 |
| **BIM Information Extraction Through LLM-based Adaptive Exploration**<br>B12 · F；arXiv 2605.01698v1，2026-05-03；投稿 AIC 的预印本，非据此认定已录用<br>[v1 全文](https://arxiv.org/html/2605.01698v1)；[版本记录](https://arxiv.org/abs/2605.01698v1)；[Cobbie 仓库](https://github.com/sylvainHellin/cobbie) | CodeAct 探索实际 IFC；可加 AST 文档混合检索、重排，以及由开发轨迹创建/修正/评估的经验工具，最多 16 个。延续 IFC-Bench v1 作者线。 | 21 项目、37 IFC、1027 QA，题级拆为 513 开发/514 测试。GLM-4.7 文档增强 56.0%→56.6%，不显著；Air 为 25.7%→30.6%。评测排除崩溃与超时。<br>边界：仅 GLM 家族、单次运行，题级拆分不证未见建筑泛化；静态基线只执行一次。仓库描述仍为 200 题，未确认论文快照。 | N01/N02 的经验工具、N05 的主动探索和 N08 的知识收益均有强近邻。候选必须提出适用边界/反例或执行协同的具体机制；不能只新增知识库，成本还要包含失败和学习。 |
| **Ishigaki-IDS, 2606.08545v1**<br>补查 · F；[指定版本正文](https://arxiv.org/html/2606.08545v1) | 持续预训练、SFT与验证奖励生成IDS规格，使用gold facets。 | 166专家项；8B的108项通过audit，其中65项FacetF1<0.5；16H200训练。 | BIM验证奖励学习已有；格式通过不能替代需求正确。 [详细核查](#update-21) |

### 作者与工具谱系


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

### 重点补充核查

<a id="update-21"></a>
#### Ishigaki-IDS, 2606.08545v1

**来源与读取：** [Ishigaki-IDS, 2606.08545v1](https://arxiv.org/html/2606.08545v1)，§4–6、表1–4

**方法、实验与限制：** CPT+SFT+验证奖励，训练还用 gold facets；166 个专家评测项、单次输出。8B 有 108 项过 IDS audit，其中 65 项 FacetF1<0.5。论文训练用 16 H200；不是检索小改动的成本。

**冲突点：** “BIM 中 verifier-aware 学习”已有；标准校验通过不等于用户要求正确。它生成 IDS，不生成或修复完整 IFC。

<a id="update-22"></a>
#### Self-Verification：直接重合与规格遗漏

[A Self-Verification Framework Toward Reliable Text-to-BIM Generation](https://ec-3.org/wp-content/uploads/2026/08/EC32026_444.pdf)，Sesterhenn 等，EC³ 2026，2 页。重读全部正文与两幅图。Specifier 从请求产生 IDS 和非 IDS 要求，Modifier 创建/修改 IFC，Verifier 写并执行补充检查，结合 IfcTester 反馈继续修订；工具基于 MCP4IFC。非 IDS 明确涉及几何、拓扑、复杂关系，不能说它只查属性。

实验是 GPT-5.2 的一个两层住宅案例、五轮修订；房间计数、屋顶和材质改善，空间与楼层关联仍未解决。论文没有提供可支持总体优势的系统对照或消融；作者明确承认初始规格可能漏需求。**证据弱不代表方法不存在。**

[作者仓库](https://github.com/Tsesterh/Text2BIM-Self-Verification)另确认 spec.md、IDS、逐轮 IFC/报告与合并 patch plan 的实现组织，依赖 MCP4IFC；本轮只核 README，不宣称运行成功。

### 阅读位置与来源记录

逐篇原始卡片保留定位细节：[bim-authoring](literature-evidence/bim-authoring.md)；[ifc-evaluation](literature-evidence/ifc-evaluation.md)；[coding-knowledge-and-control](literature-evidence/coding-knowledge-and-control.md)。阅读卡是证据，不是额外研究路线。

## 2. CAD / 空间建模：表示、约束与多种有效设计

多解不是取消评价标准。表示、几何和拓扑会共同限制有效解集合；TileGPT使“质量—多样性＋LLM＋约束”的先例尤其明确。

本模块40条研究记录。

| Paper：名称、版本与原始来源 | 贡献与观点 | 实验场景与证据边界 | 与我们的冲突点 |
|---|---|---|---|
| **SceneCraft: An LLM Agent for Synthesizing 3D Scenes as Blender Code**<br>C01 · F；ICML 2024，PMLR 235:19252–19282；正式正文及相关附录<br>[正式全文](https://raw.githubusercontent.com/mlresearch/v235/main/assets/hu24g/hu24g.pdf)；[会议论文页](https://proceedings.mlr.press/v235/hu24g.html) | GPT-4V 分解子场景、检索资产，生成资产—关系图与数值约束函数交求解器；视觉反馈修订，外层归纳可复用空间技能库，无需参数微调。 | 40 手写查询，20 学习/20 测试；约束分数 88.9，对改造 BlenderGPT 5.6；去技能库 64.5，再去内循环 26.1。另有 Sintel 与 22 份人工响应；约 6k 平均、15k 最高 token/场景。<br>边界：递进消融并非每个因素独立析因；大于 20 资产子问题较差，依赖资产检索和分解。软约束分数不等于 IFC 关系验收。 | N01/N02 若仅从成功轨迹归纳技能、N04 若仅分解关系后交求解器，均与此文直接冲突。text2IFC 需研究失败如何改变适用边界/组合接口，并用未见组合和独立保全检验。 |
| **Text2CAD: Generating Sequential CAD Designs from Beginner-to-Expert Level Text Prompts**<br>C02 · F；NeurIPS 2024，37:7552–7579；正式正文及补充<br>[正式全文](https://proceedings.neurips.cc/paper_files/paper/2024/file/0e5b96f97c1813bb75f6c28532c2ecc7-Paper-Conference.pdf)；[作者代码](https://github.com/SadilKhan/Text2CAD)；[作者数据](https://huggingface.co/datasets/SadilKhan/Text2CAD) | 自动标注 DeepCAD 的四档文本，以 BERT、领域适配层和自回归解码器生成量化 sketch/extrude 序列，保留可编辑 CAD 历史；知识来自表示和监督语料。 | 约 170k 模型、660k 文本，约 150k 训练、验证/测试各 8k。L3 主表无效率 0.93% 对 10%；四档各 1000 例视觉、各 100 例人工比较，L1 视觉偏好未胜基线。<br>边界：数值分词、透视标注、矩形/圆柱偏置明显；主表最详细提示不能代表所有文本。可执行率与描述符合率不同，构件 CAD 非整栋 IFC。 | N02 不能仅以可编辑动作表示称新；N07 若换表示，需要区分监督学习收益与固定模型推理收益。text2IFC 可借鉴表示消融，但必须另测关系、要求和全部成本。 |
| **Generating CAD Code with Vision-Language Models for 3D Designs**<br>C03 · F；ICLR 2025；核查 arXiv 2410.05340v2 并核对会议版身份<br>[arXiv v2 全文](https://arxiv.org/pdf/2410.05340v2)；[会议版](https://proceedings.iclr.cc/paper_files/paper/2025/file/81a934cd364e18ea6fdeaf57a93c17d4-Paper-Conference.pdf)；[作者代码和 CADPrompt](https://github.com/Kamel773/CAD_Code_Generation) | 先生成 CadQuery 并按执行异常修码，再从需求产生 2–5 问题，以四视图作 Yes/No/Unclear 判定后修订两轮；包括直接视觉反馈对照与读取 GT 的求解器上界。 | CADPrompt 200 专家对象。GPT-4 few-shot 编译率 91%→96.5%、点云距离 0.137→0.127；100 例消融、50 例人工/问答检查，视觉问答正确率仅 64.6%/68.2%。<br>边界：GT 求解器不是生产基线；点云距离会漏部件脱离等逻辑错误，生成检查本身不可靠，初始提示有影响。 | N03 的生成内自验证已有先例；N06 须区别于让模型自问需求题，证明询问用户的价值；N07 要用独立几何/关系检查验证参考系修正，不能只循环视觉反馈。 |
| **LLM4CAD: Multimodal Large Language Models for Three-Dimensional Computer-Aided Design Generation**<br>C04 · F；JCISE 2025，DOI 10.1115/1.4067085；作者稿<br>[正式 DOI](https://doi.org/10.1115/1.4067085)；[作者实验室全文](https://sidilab.net/wp-content/uploads/2025/01/llm4cad_jcise_preprint.pdf) | GPT-4/GPT-4V 零样本生成 CadQuery 2.3.1 与 STL；尺寸文本可加渲染图/草图，错误连同历史最多修三次，没有知识检索。 | 五类机械零件各 1000 参数模型，清洗后 3331 文本，不等于各条件独立样本。文本条件解析率 GPT-4 0.517→0.711、GPT-4V 0.525→0.710；部分总体 IoU 随调试下降。<br>边界：IoU 仅在解析成功子集计算，调试改变入选集合，不能推断同例被修差。仅五类合成单视图，尺寸仅在文本，未核实公开实现数据。 | text2IFC 必须同时测执行和需求质量。N07 的多表示信息若有效，需排除信息量、采样和成功筛选差异；N05 也不能预设增加模态或资料必然改善结果。 |
| **Building-Diffusion: Graph Discrete Diffusion Model For Architectural Volumetric Design Generation**<br>C05 · F；CVPRW 2026，CV4AEC，正式正文<br>[正式全文](https://openaccess.thecvf.com/content/CVPR2026W/CV4AEC/papers/Sehaba_Building-Diffusion_Graph_Discrete_Diffusion_Model_For_Architectural_Volumetric_Design_Generation_CVPRW_2026_paper.pdf)；[作者仓库](https://github.com/Sehaba95/building_diffusion) | 用 program graph 表达功能、楼层、面积和邻接，自监督编码后条件化离散扩散；架构师初始化 voxel 邻接并固定，只生成节点标签，无 LLM 或 RAG。 | 120k 合成建筑、1–11 层，测试数未明确。FAR 误差优于 GAN，但 TPR/FGW 较差；多样本按相对 GT 的 FGW 择优。20 建筑师各比 30 对，偏好 41.5% 对 31%。<br>边界：单次波动、部分过拟合和指标取舍；不能把 GT 选样当无 GT 策略。仓库仅 README/LICENSE、待发布，非代码已开放。 | N04 的保持既成关系有相邻先例，但固定 voxel 邻接与重新开放跨层依赖不同；N07 不能用 GT 选表示。text2IFC 应测实体/宿主/包含关系，而非借体素指标宣称保全。 |
| **MANSION: Multi-floor lANguage-to-3D Scene generatIOn for loNg-horizon tasks**<br>C06 · F；CVPR 2026，正式正文及补充<br>[正式全文](https://openaccess.thecvf.com/content/CVPR2026/papers/Che_MANSION_Multi-floor_lANguage-to-3D_Scene_generatIOn_for_loNg-horizon_tasks_CVPR_2026_paper.pdf)；[补充材料](https://openaccess.thecvf.com/content/CVPR2026/supplemental/Che_MANSION_Multi-floor_lANguage-to-3D_CVPR_2026_supplemental.pdf)；[作者代码](https://github.com/AgibotGeneral/MANSION) | 多代理分层规划，求解器排除破坏已成拓扑的候选；anchor/member、matrix/paired 关系原语压缩重复约束，处理碰撞与可达性。输出 AI2-THOR 场景。 | 1000 栋场景、2–10 层。ResPlan 1000 例 micro-IoU 63.56 对 CHD 29.36，但 T2D 69.98 低于 76.34；放置四类房间各 10 次，52 人评估。<br>边界：MA 条件使用 GT 面积/质心；无解可缩小阵列或丢弃对象，100% 可达性需连同覆盖率看。跨层交互靠加载/卸载，非 IFC 整栋交换。 | N02 的关系组原语、N04 的确定性求解与保持拓扑已有强碰撞。text2IFC 需研究失败后怎样选择重开依赖或修订组合接口，不能只把 LLM 关系交给 solver。 |
| **Tell2Design: A Dataset for Language-Guided Floor Plan Generation**<br>C14 · F；ACL 2023，pp.14680–14697，正式全文<br>[ACL 全文](https://aclanthology.org/2023.acl-long.820.pdf)；[作者代码和数据](https://github.com/LengSicong/Tell2Design) | 将房间类型、框坐标和边界编码成序列，用 T5-base 生成二维布局；先模板预训练再人工描述微调，没有 IFC 关系或执行纠错。 | 80788 图中仅 5051 人工描述、75737 模板；人工训练/测试 2743/2308 且标注者隔离。micro/macro-IoU 54.34/53.30；100 例、5 人评全部要求满足仅 38%，GT 85%。<br>边界：英语平面域、模板向人工描述转移较弱，未优化多样性；同一需求多种正确布局，IoU 不是语义满足充分条件，80k 不能全称人工标注。 | N06 要在多解和遗漏要求下评价澄清，N07 应区分表示改善与接近单 GT。text2IFC 可借标注隔离和全要求满足指标，不能借平面像素分数替代 IFC 关系验收。 |
| **CIT-CAD: Constraint Intent Tree-based CAD Code Generation and Verification**<br>FSP01 · F；arXiv v1，2026-09-07 预印本<br>[arXiv v1 全文](https://arxiv.org/html/2609.07434v1) | 将文本转成约束意图树，再生成 CadQuery；从代码 AST 与执行几何提取实际约束并关联失败节点。修复仍接收完整代码，只接受减少违例且保持已满足约束的候选，不保证最小补丁。 | 151K 来源对筛至 26,783 条，描述额外用参考代码补入尺寸等，各法得到相同增强文本。GPT-5.4-mini 可执行率 87.2→90.4，IoU@0.95 为 4.6→5.5，约束满足率 16.7→37.7；三者不是联合成功率。<br>边界：候选多两轮或五轮修复，成本未完全匹配；生成和评测共同依赖意图树，不能检出树本身误读。有效 IoU 选择及缺失输出分母表述有待澄清。 | 直接冲突 N04 的意图树、局部诊断和保留满足约束。text2IFC 更严格的独立意图评测有价值，但新方法必须是接口干预选择或其他可替换决策；更扎实的闭环不自动带来新颖性。 |
| **HistCAD: A Constraint-Aware Parametric History-Based CAD Representation, Dataset, and Benchmark with Industrial Complexity**<br>FSP02 · F；arXiv v2；未混合早期不同题名版本<br>[arXiv v2 全文](https://arxiv.org/html/2602.19171v2) | 以平展图元序列把环路恢复交给前端，保留 19 类草图约束与多种特征，用三维点和内核匹配跨特征引用。减少模型输出的确定性恢复工作，同时保留影响编辑的关系。 | 170,236 序列含工业 8,093；134,896 共同形状上 Gemma4-31B-it tokenizer 比较。原生序列回放的完整/仅闭合约束编辑总成功 OES 为 95.42%/64.75%；Qwen3-8B LoRA 生成另评，不能混作冻结模型结果。<br>边界：编辑任务精确 D 未恢复；cPCSR 以有效重建为分母，OES 以全部请求为分母。网格距离选择共同有效例；主要局部尺寸编辑，不代表复杂重排或拓扑变化。 | 约束 N04 和旧编译器/压缩叙述：紧凑表示、显式关系与编辑保持已有直接实验。text2IFC 应研究冲突时如何选变量或改构造行为，并区分表示收益、训练数据收益及推理机制。 |
| **A multimodal benchmark for editable constraint preserving history based CAD modeling**<br>FSP03 · F；Discover Artificial Intelligence 6, 1022，2026-09-02 正式论文<br>[出版商正式全文](https://link.springer.com/article/10.1007/s44163-026-01899-5) | 将轮廓恢复交给前端，以参数化序列表达约束、布尔过程与部件关系，并从包围盒等信息构造粗空间语言标注。功能性描述是生成标签，不等于功能已获工程验证。 | 约 129K 共同形状上用 Qwen3-0.6B tokenizer，含约束/无约束平均 476.11/358.87 token。FreeCAD 编辑是定性比较；Qwen3-8B LoRA 生成无效率 1.40%、平均 CD 3.00，不是零样本结果。<br>边界：与 HistCAD 是不同作者、不同论文，不能合并数据或跨 tokenizer 排名。部分资源需申请、工业文件不能再分发；未提供同等量化编辑保持分母，长装配与实用性覆盖有限。 | 冲突 N04 及压缩/编译器承担结构的宽泛思想。text2IFC 需要可检验的选择或调整机制；仅将一部分结构移交编译器、保留关系并减少 token，已经是已知表示路线。 |
| **CAD-Factory: A Language-Driven CAD Generation System**<br>FSP04 · F；作者页标示 SIGGRAPH 2026；依据公开主文与补充<br>[作者项目页](https://cad-factory.github.io/)；[作者主文 PDF](https://cad-factory.github.io/pdf/main.pdf)；[作者补充 PDF](https://cad-factory.github.io/pdf/appendix.pdf) | 用 21 类 AST token 分离结构和数值参数，Manager 产 AST、Coder 写代码，执行反馈辅助修正；Editor 以颜色/部件映射支持修改。含词表扩展、领域预训练、LoRA 和联合微调。 | 约 110K 数据，生成微调 50K、编辑 15K；4×A100 80GB，领域/分阶段/联合训练约 32/18/3 小时。AST 消融支持结构作用；9,000 输出与 3,000 参考只属于无条件分布评测，不能作文本任务分母。<br>边界：文本评测精确分母未给；通用基线有格式示例和语法反馈，但没有同等专门训练。编辑主要定性，不能推出全局关系保持率，也不是冻结模型推理策略的直接比较。 | N02/N04 不能以先结构后参数、多 Agent 或反馈分工为新。text2IFC 若借鉴需先做同模型结构决策对照；训练能力扩展要单列数据与计算投入，不混作少量方法补强。 |
| **AIDL: A Constraint-Solving CAD Language**<br>FSP05 · F；完整阅读 arXiv v1，2025-02-13；CGF 44(7) 正式版仅核身份，全文未取得<br>[arXiv v1 全文](https://arxiv.org/html/2502.09819v1)；[作者 PDF（预印本内容）](https://vovakim.com/papers_small/25_PG_AIDL.pdf)；[正式版 DOI（身份记录）](https://doi.org/10.1111/cgf.70250) | 以具名几何引用、约束及 SOLID/HOLE/ASSEMBLY 表达层次；局部求解失败后，先按深度开放后代平移，再逐层开放全部几何参数，最终可扩至全模型。已经具备两阶段自由度释放。 | v1 为 36 条人工二维任务×10 次，GPT-4o、6 示例、最多 5 次失败反馈。有效率 AIDL 64%、无约束 94%、无层次 77%、OpenSCAD 79%；CLIP 只统计有效结果，不能作全部任务成功率。<br>边界：非完整三维 IFC；编辑性主要定性，存在删约束或结构以消除错误。正式版作者/摘要变化，不能将 v1 结果无条件归属期刊版。 | N04 的最直接先例：分层求解、失败扩大范围、释放内部自由度均已有。剩余假设只能是按冲突选择哪组接口变量比固定逐层释放更有效，须在相同约束/求解器与预算下验证。 |
| **WorldCoder, a Model-Based LLM Agent: Building World Models by Writing Code and Interacting with the Environment**<br>FSP06 · F；NeurIPS 2024；核查 arXiv v3，2024-09-20<br>[arXiv v3 全文](https://arxiv.org/html/2402.12275v3)；[NeurIPS 2024 正式 PDF](https://papers.neurips.cc/paper_files/paper/2024/file/820c61a0cd419163ccbd2c33b268816e-Paper-Conference.pdf) | 冻结 GPT-4 编写状态转移与目标奖励函数，模型解释已有转移且保留可达目标的可能性；执行反例触发修订，REx 选候选，VI/MCTS 规划。分离动态与任务奖励以便跨任务复用。 | Sokoban、MiniGrid、改写 ALFWorld，含乐观条件、奖励提示与迁移消融。Sokoban 初始能力形成约耗 400K token；ALFWorld 改成完全可观察 PDDL 状态，图 5 为代表任务和三种子，非原测试集全量结果。<br>边界：规则可能已在预训练中；部分对照输入表示不同，五箱以上规划仍受限。理论依赖真模型可表达及理想规划条件，不能直接赋予启发式实现。 | 冲突 N01/N03 的失败驱动程序规则和跨任务知识复用。IFC API 已精确实现的动态未必值得重学；需证明适用条件及关系副作用学习超过文档与程序案例，且计全部获得成本。 |
| **SayPlan: Grounding Large Language Models using 3D Scene Graphs for Scalable Robot Task Planning**<br>FSP07 · F；CoRL 2023 / PMLR 229 正式全文及补充<br>[PMLR 正式全文及补充](https://proceedings.mlr.press/v229/rana23a/rana23a.pdf) | LLM 按任务展开/收起楼层、房间、物体的三维场景图，仅保留相关子图和搜索记忆；Dijkstra 处理路径，LLM 处理高层计划，仿真谓词反馈驱动最多五轮重规划。 | 90 任务，包括 60 搜索及 30 规划；正文办公室 37 房间/150 物体，住宅 28 房间/112 物体。长程计划正确率 73.3%、可执行率 86.6%，不是联合成功率。图输入明显缩短，但未包含所有重试/工具成本。<br>边界：两个预先提供的场景图规模有限，距离、否定、计数仍失败；基线未完全匹配修订预算。不能推出从任意自然语言自动学会完整空间模型。 | 直接约束 N05/N08 和编译器分工叙述：关系上下文缩减、确定性求解器分工与闭环已有。text2IFC 需给出优于普通图遍历的选择准则，不能仅新增层次图或声称把确定性工作外包就是创新。 |
| **Aligning Constraint Generation with Design Intent in Parametric CAD**<br>FSP08 · F；ICCV 2025 正式论文，pp. 8613–8622<br>[ICCV 2025 正式全文](https://openaccess.thecvf.com/content/ICCV2025/papers/Casey_Aligning_Constraint_Generation_with_Design_Intent_in_Parametric_CAD_ICCV_2025_paper.pdf) | 从草图几何预测约束，以监督模型为基础比较 DPO、ExIt、ReMax、RLOO、GRPO；用 Fusion 的可解、充分约束、过约束和稳定性反馈训练，不是简单把报错反馈进提示。 | 来源约 2.8M 独特草图，最多 16 图元/64 约束，精确测试分母未给。每草图生成八组；RLOO 充分约束率 93.05%、监督 34.24%，严格联合 pass@1 为 83.57%/33.32%。超时两秒计不可解。<br>边界：求解器奖励会诱导多余尺寸约束和奖励投机；充分约束不代表保留用户修改自由度。来源规模不是测试规模，结果依赖训练及奖励目标。 | N03/N04 必须防止“更多约束通过就是意图正确”。text2IFC 需明确必保关系、可变参数及合法拓扑改变；若以求解反馈训练，应另计训练投入，不能作为冻结模型的小改动。 |
| **CAD-Editor: A Locate-then-Infill Framework with Automated Training Data Synthesis for Text-Based CAD Editing**<br>FSP09 · F；ICML 2025；核查 arXiv v2，2025-07-03<br>[arXiv v2 全文](https://arxiv.org/html/2502.03997v2)；[作者代码](https://github.com/microsoft/CAD-Editor) | 生成编辑前后 CAD 对及语言指令，用 LCS 等形成修改掩码，模型先定位再补写、复制保留未改 token。以约 120K 合成数据和人类筛选训练 Llama-3-8B LoRA，程序层面的局部保留不等于所有空间关系保持。 | 2,000 测试指令×5 次，共 10,000 输出，主要指标汇总三运行；人评抽 2,000 模型对、五评价者。有效率 95.6%、人工编辑成功率 43.2%，GPT-4o ICL 为 84.5%/15.6%。<br>边界：通用基线没有同等领域训练；同训练内定位/直接生成消融更接近机制证据。4×A800 80GB、70 epoch，不是廉价提示改动；未直接量化全局关系保持。 | 约束 N01/N03/N04 的定位修补与保留未改部分。text2IFC 需证明修复经验跨任务迁移或修订选择的新机制，而非把另一套局部编辑闭环当创新；有效 IFC 与完成用户编辑必须分开。 |
| **DepthBenchCAD: When Does Deeper Auditing Yield More Reliable Conclusions?**<br>DEPTH · P；2026-09-14 索引/仓库线索；完整题名已补核，原文方法和实验未完成阅读<br>[arXiv 题名与摘要入口](https://arxiv.org/abs/2609.15122)；[作者仓库](https://github.com/HongyeYangGT/DepthBenchCAD) | 当前只确认题名、原始入口和仓库线索，可归入 CAD 审核深度及结论可靠性的待查近邻。不能用题名或仓库简介代替方法，也不据此声称它已实现某种约束检查或参数变化算法。 | 未读到原文方法与实验，实验任务、数据规模、审查深度、模型、预算、指标及基线均保留未知；不编造数字，不将项目页示例或仓库数量转成评测分母。<br>边界：P 表示全文核查尚未完成，不是论文质量评级。补齐题名不提升证据等级；目前不能对其泛化、成本、代码可复现性或验证覆盖作肯定判断。 | 可能影响 N04 的跨层审核及空间参数变化评价，但冲突范围待正文确认。text2IFC 选题应保留这个查重缺口，既不能据未读材料认定创新被覆盖，也不能因为没有证据就宣称该方向空白。 |
| **LLM-Based Instance Model Generation via Code Synthesis**<br>C07 · P；MODELS 2026 Research Papers / FT，10 月 8 日议程；官方摘要，全文未取得<br>[官方论文摘要](https://conf.researchr.org/details/models-2026/models-2026-research-papers/16/LLM-Based-Instance-Model-Generation-via-Code-Synthesis)；[作者论文入口](https://antolin1.github.io/) | 摘要描述将元模型编码成 Pydantic 类、良构约束变成验证器，LLM 生成构造实例的代码，并按失败反馈修正；这是领域类型/API 承担知识的直接先例。 | 摘要称两用例、三个 LLM 与 Refinery 比较，循环可构造逾 2000 元素。元素数不是测试例数；模型、重复、失败分母、预算和求解器配置未正文核查。<br>边界：一致性、多样性、真实性效果仍仅为摘要报告；未找到可确认工件。随规模多样性下降的具体证据表也未核，不能断言全面胜过求解器。 | N01/N02 不能仅以类型化工具和代码循环称新；N08 要区分执行协同与元模型知识供给。text2IFC 尚不能据摘要排除适用边界、剩余义务或关系上下文上的细分碰撞。 |
| **Well-Formed Executable Suggestions for Continuous Model-Driven Engineering**<br>C08 · P；MODELS 2026 Research Papers / FT；官方摘要及 TTool-AI 实现线索<br>[官方论文摘要](https://conf.researchr.org/details/models-2026/models-2026-research-papers/7/Well-Formed-Executable-Suggestions-for-Continuous-Model-Driven-Engineering)；[TTool-AI 作者工具页](https://ttool.telecom-paris.fr/ttoolai.html)；[公开合并请求 550](https://gitlab.telecom-paris.fr/mbe-tools/TTool/-/merge_requests/550) | 摘要中 γμS 以形式化 mutation 语言、MCP 规则验证、外部工具和反馈生成可执行建议，另用 LLM 语义 oracle 判断相关性；用于 SysML block/state-machine 多视图编辑。 | 仅知 TTool 初步案例，模型、数量、基线、成功率、token 和人工干预未取得论文正文。公开合并请求说明存在实现线索，不等于论文实验复核。<br>边界：形式保证、允许变更范围、跨视图一致性和失败处理均待全文；不能以作者其他 TTool 论文替代，也不能由无法访问推断缺机制。 | 受限修改语言与良构/语义分工已公开，text2IFC 不应整体称新。N03/N04 必须进一步比较规则迁移或依赖重开，N01 的边界修订也要区别于固定 mutation 限制。 |
| **The impact of Software Model Slicing on Software Model Completion with Large Language Models**<br>C09 · P；MODELS 2026 Research Papers / FT；官方摘要、作者目录，全文未取得<br>[官方论文摘要](https://conf.researchr.org/details/models-2026/models-2026-research-papers/15/The-impact-of-Software-Model-Slicing-on-Software-Model-Completion-with-Large-Language)；[作者出版目录](https://www.se.cs.uni-saarland.de/publications/lists/welter.html) | 摘要提出任务/元模型无关图切片，包含半径、模块化、LLM 引导策略，与 identity/random 对照；直接研究较小上下文能否改善补全并减少 token。 | 两个公开数据集的 1000 真实模型和结构/语义改善是摘要报告。具体数据、移除任务、模型版本、重复、切片定义及全部选择成本未正文核查。<br>边界：未取得算法、依赖闭包、统计、失败分母与限制节；不能把摘要的 1000 视为已审计样本，也不能声称此前未研究关系上下文。 | N08 必须超越通用切片和文本覆盖，验证执行协同的预测价值；N04 要区分上下文选取与真正改变可修改依赖。text2IFC 的上下文创新判断必须保留此高相关缺口。 |
| **An agent-based approach for the automatic generation of valid SysMLv2 Models in industrial contexts**<br>C10 · P；Computers in Industry 172,104350（2025）；摘要/开放稿索引，连续正文未取得<br>[正式 DOI](https://doi.org/10.1016/j.compind.2025.104350)；[出版商原始页](https://www.sciencedirect.com/science/article/pii/S0166361525001150)；[大学永久入口](https://hdl.handle.net/10016/48940) | 可访问材料描述自然语言生成 SysML v2，结合领域示例检索、官方 ANTLR 语法校验和迭代修正；已有知识检索与验证循环的相邻系统。 | 摘要称 20 个提示达到 100% 语法有效；不是本次已核实的语义正确率。模型版本、RAG 库、循环上限、基线与统计未取得正文。<br>边界：大学开放稿下载受限/超时，没有连续方法、实验表和限制节；数据按请求提供不等于开放数据，代码未确认。不能据访问失败断言其没有全局约束。 | N03 的重试修复、N05 的示例检索均非空白。text2IFC 要在固定预算下验证跨任务经验或信息动作价值，并区分语法通过、关系成立与真实用户要求满足。 |
| **MCeT: Behavioral Model Correctness Evaluation using Large Language Models**<br>C11 · F；MODELS 2025；arXiv 2508.00630v2，2025-08-30<br>[v2 全文](https://arxiv.org/pdf/2508.00630v2)；[作者仓库](https://github.com/Huawei-TTE/MCeT) | 对需求和 PlantUML 序列图做整体、图原子、需求原子检查，五次投票；MCeT-X 用较高精度需求判定交叉过滤。输出错误解释，非生成器或形式证明。 | 28 需求的 87 变体筛成 76 例。GPT-4o-mini：整体精确率/已标问题召回 0.58/34.1%，A 为 0.72/68.1%，X 为 0.81/65.2%；mini token/图 12k→80.5k。<br>边界：X 删 211 假阳性也删 158 真阳性；其他模型仅复测 8 图，人工标注及开发分析来自同语料。原子检查并不自动省成本或保证完整。 | N03 的规则/经验必须测漏检而非只降假阳性；N06 的需求原子问题也需与已有检查区分。text2IFC 不可将 LLM 投票包装成确定性 IFC 保证，需保持独立验收。 |
| **Event-B Agent: Towards LLM Agent for Formal Model Synthesis and Repair**<br>C12 · F；Proc. ACM Softw. Eng. 3/FSE,FSE211（2026）；arXiv 2605.17475v1<br>[正式 DOI](https://doi.org/10.1145/3808218)；[v1 全文](https://arxiv.org/pdf/2605.17475v1)；[作者代码](https://github.com/HongshuW/EventB_Agent) | 规划需求细化与 gluing invariants，以 JSON schema、编译类型检查和证明器分工；七类 proof-state 规则选择原子修复，修改后重放全部证明。 | 27 系统、三复杂度各 9，固定 GPT-5 medium 对照 prover、Cursor、PAT-Agent。PDR/RC/RF 为 97.86/97.13/93.79%，非整模型成功；平均约 165.8 万 token/系统。<br>边界：RC/RF 依赖跨层保留近似，refinement PDR 92.56%；要求内部一致，标签格式曾人工纠正。规则有限，保留形式性质不等于实体字节不变。 | 编译器/Agent 义务分工、原子修复已是强先例。N03 应证明经验跨任务预防，N04 应研究何时重开依赖，N01/N08 应提供边界/知识机制，而非仅把 Event-B 换 IFC。 |
| **Software Model Evolution with Large Language Models: Experiments on Simulated, Public, and Industrial Datasets**<br>C13 · F；ICSE 2025，pp.950–962；24 页作者稿含附录<br>[作者全文及附录](https://www.se.cs.uni-saarland.de/publications/docs/TWA%2B25.pdf)；[代码和公开数据](https://github.com/se-sic/icse_model_completion) | SiDiff 变更图保留变化和直接相连的既有元素，用 EdgeList 表示；MiniLM 检索最多 12 个历史变更，由 GPT-4 补全边，支持增删和属性修改。 | 工业/RepairVision/合成为 8/42/24 模型，测试补全 122/221/210；工业格式/类型结构/语义为 92.62/76.23/62.30%。51 例旧方法对照模型不同，不能全归因 RAG。<br>边界：切片外节点难引用，有 ID 冲突、错误父节点、层级摊平；截断长属性并排除超窗变更。增加示例数不显著，工业数据不开放。 | N03 的历史变更知识、N04 的局部依赖、N08 的相关性检索已有先例。text2IFC 应证明经验适用条件及跨范围关系收益，固定模型与预算，而非只做邻域加 RAG。 |
| **Multi-Location Software Model Completion**<br>C15 · F；ICSE 2026；arXiv 2601.13894，作者正文与补充稿<br>[arXiv 版本入口](https://arxiv.org/abs/2601.13894)；[作者全文](https://www.se.cs.uni-saarland.de/publications/docs/WTA26.pdf)；[补充稿](https://raw.githubusercontent.com/se-sic/modelcompletion_multilocations/master/Multi-Location_Software_Model_Completion.pdf)；[作者代码](https://github.com/se-sic/modelcompletion_multilocations) | 从历史共同变更学习下一 focus，再局部补全和迭代十次；改版 RaMc′ 同时使用两跳切片、JSON、GPT-5-mini 和两条检索示例。 | RepairVision 41 项目/912 commits 筛到 32 项目，另抽 10 跨项目。0.98 是特定分母排序指标；项目均分同项目 0.58、跨项目 0.36。类型结构完成率 RaMc 12.19%、加 NextFocus 8.48%、改版 16.11%。<br>边界：改版多因素共同变化，不能归因单一表示；稀有/层级变更较弱，排除过大项目，预测对位置不等于生成对模型。 | N04/N08 须超过已有历史共变与两跳选择，并测最终关系正确性；N03 跨任务经验不能只用同项目末次变更。text2IFC 应区分定位、知识选择与完成率。 |
| **Large language models in model-driven engineering: a systematic mapping study**<br>C16 · F；Empirical Software Engineering 32,article 3（2027 卷期）；2026-07-16 在线，系统映射综述<br>[出版商全文](https://link.springer.com/article/10.1007/s10664-026-10921-4)；[同版 PDF](https://link.springer.com/content/pdf/10.1007/s10664-026-10921-4.pdf) | 五库检索并做前后向滚雪球，以 43 字段抽取、频数/共现整理 LLM-MDE 文献；限定同行评审、有经验评价，属于综述而非生成系统或效果量元分析。 | 2025-09 初检 1666 条、筛到 45 篇，2026-02 滚雪球加 44、合并版本后 86；62 涉及生成，36/86 无基线，21/86 报成本。<br>边界：单轮滚雪球、主观分类、发表偏差及早期 2026 截面；未细拆提示和错误类型，不能由分类空白推导方法空白。OSF 包入口未完成内容核查。 | 支持 text2IFC 完善对照、工件有效性和成本报告。N01–N08 必须各有机制实验及失败分母；“本领域评价不严谨”可以构成动机，却不自动构成自己的方法创新。 |
| **Text-to-Code Generation for Modular Building Layouts in Building Information Modeling**<br>D01 · F；NeurIPS 2025；核查 arXiv 2509.23713v1<br>[正式会议入口](https://proceedings.neurips.cc/paper_files/paper/2025/hash/61a3e68eb9059ccacdde0bb84870b80e-Abstract-Conference.html)；[v1 全文](https://arxiv.org/html/2509.23713v1) | 将模块建筑组织为 Module、Unit、Room 等 C#/Revit 操作，用接口表达相对位置、邻接与连接，再配合合成数据微调；并非只把坐标文本改成代码语法。 | 198 设计、396 描述，按设计拆 138/20/40。多种 Qwen2.5 比较代码/坐标表示，测编译、实例/参数 F1、IoU；7B Coder 代码 IoU 98.43，对坐标 84.64。<br>边界：包围盒 IoU 不覆盖全部碰撞、构件顺序和不规则几何；需求详细、构件族受限。抽象与表示共同变化，不能单独归因代码，也无用户可用性实验。 | N02 不能仅把关系封装成高级接口，N07 需控制等价表示的表达能力；text2IFC 可借任务—表示—数据—消融结构，但目前没有同任务证据支持比它更强。 |
| **ATLAS: A Layered Constraint-Guided Framework for Structured Artifact Generation in LLM-Assisted MDE**<br>D04 · F；arXiv 2510.25890v3，2026-04-05；早期同编号题名含 PRISM<br>[v3 全文](https://arxiv.org/html/2510.25890v3) | 以 ICM 统一元模型/约束，结合完整结构上下文、JSON Schema/GBNF 约束解码、确定性 ARXML 投影、SHACL/SMT 审核和定向修订。 | 固定 32B 模型，60 个 AUTOSAR 组件、三种提示详略；多文件另测 20 系统、284 文件。表 6 完整率/XSD 为 100%，各复杂度系统 SMT 首轮通过却均为 0。<br>边界：结构可导入不等于设计逻辑成立；不能从首轮失败推出后续不可修复。跨领域效果未实证，结果也非独立工业生产率实验，版本不能混算。 | 与 text2IFC 编译器分工有强碰撞。N03/N04 应提出新的修复知识或依赖决策；N08 应验证上下文的执行协同，而不能将领域约束、中间表示、编译和验证整体称新。 |
| **Enforcing fine-grained access control for secure collaborative modelling using bidirectional transformations**<br>D05 · F；Software and Systems Modeling，2017 在线，后有勘误；核查出版商正文<br>[出版商全文](https://link.springer.com/article/10.1007/s10270-017-0631-8) | 对对象、属性、引用设读写权限，Get 导出过滤视图，PutBack 验证写回；明确读写依赖、反向引用和包含关系，讨论条件性 lens 性质。 | 行业风机模型合成扩展，分别增加模型规模及协作者数，重复测在线传播和离线提交成本；在线成本主要随受影响视图变化，离线需处理全文件。<br>边界：适用于中央完整模型、特定规则和主要无序集合；保证内部结构/权限一致性，不是全部领域良构。文中 gold model 是共享完整模型，不是私有评测真值。 | N04 的局部修改边界、依赖和写回检查有成熟基础，N01 的限制适用范围也不能借权限术语直接称新。text2IFC 的学习/选择机制需另证，保全接口本身不足以贡献 AI 方法。 |
| **ChronoSphere: a graph-based EMF model repository for IT landscape models**<br>D06 · F；Software and Systems Modeling，2019，出版商全文<br>[出版商全文](https://link.springer.com/article/10.1007/s10270-019-00725-0) | 版本化键值存储、属性图、EMF 三层映射，使元模型和实例共同版本化；事务提交新版本，支持回滚、分支及依赖查询。 | 约 20 万 EObject 的专家辅助合成模型，和 Eclipse CDO 比插入、名称查询、根因及影响分析；预热后重复，图遍历较有优势，插入并不始终最快。<br>边界：CDO 的 OCL 路线、索引及查询表达影响差值；合成数据和运行时限制外推。snapshot isolation 不应升级为所有并发执行都已证明串行化。 | text2IFC 的冻结状态、回滚和版本证据是已有系统机制。N01–N04 可以以此保障试错，但创新须来自技能/依赖的推理决策；它本身不回答语言意图或知识选择问题。 |
| **MAS4SysML: A Multi-Agent Framework for SysML v2 Model Generation from Natural Language**<br>D21 · P；JoVE，2026-05-19，DOI 10.3791/70395；方法/设置可读，主结果受限<br>[原始正文页](https://www.jove.com/t/70395/mas4sysml-multi-agent-framework-for-sysml-v2-model-generation-from) | 可读方法中 task card 含 ID、依赖、目标、约束、参数及预期输出；自底向上生成，官方语法检查后有限修复，再按卡片验证语义。 | 五类视图各 15，共 75 作者建模例；描述由 GPT-4o 起草并人工审阅，修复预算三次，计划测语法、语义覆盖及人工评分。主表数字未取得，摘要高分不作确认结果。<br>边界：英文 Results/Discussion 关键内容受限；论文不声称一次生成严格跨视图一致的完整系统，但不能反说它没有结构约束。 | N02 的任务卡和依赖排序、N03 的双验证修复已有先例。N04 的增量应是局部失败后重新开放哪些依赖，而非仅分层生成；text2IFC 效果比较仍待完整结果和公平预算。 |
| **Geometry-Aware Test-Time Learning for Quantitative Spatial Reasoning**<br>FR06 · F；核查 arXiv v1，2026-09-05；完整题名另从同版本顶部补核，不提升正式发表核实等级<br>[arXiv v1 全文](https://arxiv.org/html/2609.06004v1) | 将距离、分量和尺度预测放入几何约束，生成数值伪标签并更新 LoRA；适配参数沿测试流累计，不逐例重置。以几何一致性提供不依赖逐题标准答案的适配信号。 | 两个开源 VLM，对比 Tent/COME/TLM，在 Q-Spatial、SPAR 距离与 SpatialRGPT 评估。Qwen3-VL-4B 的 Q-Spatial-ScanNet 平均准确率 40.00→46.47，相对误差容差为 25%；水平距离却 31.7→28.3。<br>边界：不是所有切片提升，实际运行分母和更多设置转引补充，本地卡不补猜。需要参数访问；自洽可能一起偏离真实尺度，测试流顺序及累计更新影响归因。 | 约束 N07：几何自洽驱动测试时改进已有。text2IFC 可先研究冻结权重下的参考系绑定/表示选择，并比较确定性规范化；若引入 LoRA，应单列适配成本与分布迁移，不能称整个模型不训练。 |
| **LLMorph: Automated Metamorphic Testing of Large Language Models**<br>FR07 · F；arXiv v1，2026 工具稿；未合并其引用的 ICSME 2025 独立评测<br>[arXiv v1 全文](https://arxiv.org/html/2603.23611v1) | 实现 36 种变形关系，变换输入并检查两次输出间应保持的关系，也验证变换适用条件。无需为每一个变体准备 Gold，即可发现不一致行为，作为测试工具而非绝对正确性证明。 | 四个 NLP 数据集、三个模型，共 561,267 次执行；人工复核 937 个违例，不同任务/变形关系的误报率为 0%–70%。执行次数、原始问题数量及人工复核分母必须分别理解。<br>边界：违例不能判断哪一侧正确；LLM 改写可能破坏前提，语义相似也不是正确性。工具稿引用另一篇完整评测，不能重复计为两次独立实验。 | 约束 N01/N07 的反例探测与等价表示。text2IFC 可用单位换算、重命名及合法坐标变换，但须同步转换用户要求；N07 的新意须是绑定定位和候选选择，不能只是跑变形测试。 |
| **Do Vision-Language Models Represent Space and How? Evaluating Spatial Frame of Reference under Ambiguities**<br>FR08 · F；阅读 arXiv v2；ICLR 2025 正式身份已核，正式大体积 PDF 未取得<br>[arXiv v2 全文](https://arxiv.org/html/2410.17385v2)；[ICLR 2025 正式记录](https://proceedings.iclr.cc/paper_files/paper/2025/hash/af2d9fb5bcee19ef2dfa70d843520c97-Abstract-Conference.html) | 每 10° 采样对象朝向，比较相机、观察者、对象及未指定参考系，系统测方向判断的准确性、无关变化鲁棒性、空间对称和相反关系一致性，揭示参考系歧义。 | 英文 COMFORT-BALL 720、COMFORT-CAR 57,600 测试条件，九个 VLM，另扩展 109 种语言。大量条件来自少数配置，不能当作同等数量的独立真实场景或建筑。<br>边界：重点是四方向关系，遮挡有限；接受区域为分析性近似，多语言依赖机器翻译。正式 PDF 未读取，数据与结论归属作者 v2，不能假称全部版本都已一致核实。 | N06/N07 不能首创视角/坐标系歧义。text2IFC 应检验层级局部坐标绑定定位，或选择何时向用户确认参照系；多数模型偏好和几何自洽都不能代替用户选择。 |
| **B-SP01 — SceneMotifCoder：少样本抽取可复用空间程序已经成立**<br>补查 · F；[指定版本正文](https://arxiv.org/html/2408.02211v2) | 从1–3例抽参数化空间程序，再检索资产与优化物理关系。 | 202描述/50物体类；数量、布局、物理性分测；31人偏好研究。 | 空间程序抽象与组合已有；三项指标不可当联合成功。 [详细核查](#update-23) |
| **B-SP02 — PSDL：已有保持程序关系的无 LLM 参数搜索**<br>补查 · F；[指定版本正文](https://arxiv.org/html/2510.16147v1) | 用相对坐标和共享参数表达场景，搜索数值与朝向改善布局。 | 70自建＋66 Holodeck，10人比较；无LLM修正仅指布局阶段。 | D1需超过数值搜索；执行异常仍可触发LLM重试。 [详细核查](#update-24) |
| **B-SP03 — CADIR：构造图、局部子结构与稳定实体绑定已有近邻**<br>补查 · F；[指定版本正文](https://arxiv.org/html/2608.00891v1) | 带来源与约束的构造图、依赖闭合子图、文本/图检索与稳定选择。 | 200生成、4k/4k检索；100模型跨后端、294编辑；不全是成本匹配。 | 局部结构检索和稳定实体绑定已有，不能作为独立首创。 [详细核查](#update-25) |
| **B-SP04 — TraceCAD：有条件、带负例的 repair 技能也不是空白**<br>补查 · F；[指定版本正文](https://arxiv.org/html/2608.03062v1) | 连接需求、步骤和失败，局部回溯并复用带条件技能。 | 200消融、1000比较；在线记忆更新与评测顺序须控制。 | D2须超过条件技能与局部搜索；恢复分数不等于概率。 [详细核查](#update-26) |
| **B-SP05 — Graph-CAD：图分解、动作规划和能力边界课程都有直接先例**<br>补查 · F；[指定版本正文](https://proceedings.iclr.cc/paper_files/paper/2026/file/90e06fe49254204248cb12562528b952-Paper-Conference.pdf) | 几何分解图→动作→代码，三个模块LoRA并用能力边界课程。 | 12k来源；CADBench700，几何约束只测280/约500条；冻结模型另有两示例。 | 图分解、计划和课程均已有；须与冻结提示版本公平比较。 [详细核查](#update-27) |
| **TileGPT — Generative Design through Quality-Diversity Data Synthesis and Language Models**<br>补查 · F；[指定版本正文](https://arxiv.org/html/2405.09997v1) | QD数据训练语言模型生成粗布局，WFC完成约束细化。 | 两组各50k训练设计；243提示各100次；25×15网格，属性匹配只在有效结果计。 | 多样性＋LLM＋约束已有建筑先例；D1必须超越标准QD。 [详细核查](#update-32) |

### 重点补充核查

<a id="update-23"></a>
#### B-SP01 — SceneMotifCoder：少样本抽取可复用空间程序已经成立

**来源。** Hou In Ivan Tam 等，3DV 2025；[arXiv 2408.02211v2 正文](https://arxiv.org/html/2408.02211v2)，2025-06-03 camera-ready 修订。读 §3–5 与附录相关说明。

**方法。** 1–3 个实例先转成逐对象位置程序，再通过观察、改写和回放检查，抽成带数量、尺寸等参数的 meta-program。推理时选一个 motif 并补函数参数；检索网格后另做碰撞、接触、支撑优化。meta-program 验证包含复现实例数量和对象间相对方向，已超过简单存代码示例。

**实验。** 202 条测试描述、50 类物体；人工分别检查数量、布局、物理合理性，报告 0.93 / 0.90 / 0.76，三者不是联合成功率。用户偏好实验另抽 20 个提示、60 个比较问题、31 名参与者。Table 2 有直接 DSL、无观察、直接示例替代 meta-program 的消融。

**限制和对照意义。** 主要是简单 motif，依赖预先整理的物体库；与文本生成网格模型相比，任务表示和资产条件有差异。文中还展示多个 motif 填充场景，不能声称它完全没有组合。我们的接口合成或能力复用必须超越“抽程序、参数化、再组合”。

<a id="update-24"></a>
#### B-SP02 — PSDL：已有保持程序关系的无 LLM 参数搜索

**来源。** Maxim Gumin 等，*Procedural Scene Programs for Open-Universe Scene Generation: LLM-Free Error Correction via Program Search*，[arXiv 2510.16147v1](https://arxiv.org/html/2510.16147v1)，2025-10-17；arXiv 元数据注明将发表于 SIGGRAPH Asia 2025。本卡依据预印本正文 §3–7、Tables 2–6。

**方法。** 相对坐标、共享变量、循环构成 PSDL。搜索只改数值常量与四种朝向，目标包括越界/碰撞/支撑损失和相对初始布局的变化成本；共享参数同时带动多个对象。每个常量抽十个扰动，朝向枚举四个，迭代选择改善候选。运行异常仍重新请求 LLM，因此“无 LLM 修正”只指布局错误阶段。

**实验。** 自建 70 个提示，加 Holodeck 的 66 个提示；人工比较使用自建 70 个，10 名参与者分两组。Table 6 平均剩余错误：PSDL 1.1、逐对象局部搜索 0.8、梯度下降 0.5；PSDL 的人类代理偏好更高。PSDL 修正平均 9.3 秒，LLM 自修 106.7 秒。它没有在所有指标上占优。

**限制和对照意义。** 对象清单和大小由共同上游给定，方向限四个；搜索不改对象身份、关系结构或程序分支。相近代码与小几何变化只是语义保持的代理，论文明确未覆盖完整通行、视线等功能。它是“保持关系的局部搜索”的强基线，不能只用逐对象坐标优化作对照。

<a id="update-25"></a>
#### B-SP03 — CADIR：构造图、局部子结构与稳定实体绑定已有近邻

**来源。** Yu Liu 等，*CADIR: A Cross-Backend Editable Intermediate Representation for Agentic CAD Generation*，[arXiv 2608.00891v1](https://arxiv.org/html/2608.00891v1)，2026-08-01。读方法全部小节、Algorithm 1、Experiments / Tables 1–5。

**方法。** 115 个显式操作记录参数、依赖、约束、拓扑选择与产生的变化。实体选择使用来源范围、几何谓词、数量要求；跨后端用几何签名匹配并拒绝歧义，支持边分裂/合并。双塔对比训练对齐查询与构造图；子图取特征所需的上游依赖闭包，图检索模型只在整图上训练。

**实验。** 生成 200 模型，DeepCAD / Fusion 360 各 100；同 Agent、GPT-5.4 和文档条件比较表示。文本无检索 / 整图 / 整图加子图的 IoU 为 0.2702 / 0.2837 / 0.3064。检索另有 4K 训练、4K 测试；生成时案例库为独立 100 例。跨后端是独立 100 模型、30,466 构造节点、294 个编辑任务，不能混为同一分母。

**限制和对照意义。** 部分后端缺原生可编辑操作；跨后端几何不完全相同。生成成功率与独立用户要求满足不是同一件事，文中没有全流程成本匹配结果。构造图、可靠绑定、依赖子图复用均不能单独宣称新意；检索增益还包含新训练。

<a id="update-26"></a>
#### B-SP04 — TraceCAD：有条件、带负例的 repair 技能也不是空白

**来源。** Fengxiao Fan 等，*TraceCAD: Trace-Guided Repair for Agentic CAD Generation*，[arXiv 2608.03062v1](https://arxiv.org/html/2608.03062v1)，2026-08-04。读 PDF pp.2–7 的完整 Method、System、Experiments、Discussion，以及 Algorithm 1。

**方法。** 要求、执行步骤和失败证据持续绑定；疑似步骤加上游 1 跳作为编辑区，可扩到 2 跳，下游另行检查。每次最多 3 候选、2 个目标步骤。技能明确保存适用签名、原因、策略、补丁、验证证据和成功/失败复用统计；错误复用会降低排名。保全主要依赖视觉 shape-delta 反馈，不是几何等价证明。

**实验。** 200 模型消融，1K 模型对比；Agent 基线共用后端模型，消融共用重试预算。在 200 例上，去局部搜索的 Recovery Score 0.4865，完整冷启动 0.9167；这是按后续调用数加权的恢复分数，不是任务成功概率。冷启动评测允许先前测试任务形成技能供后续任务使用；warm-up 另用 1K 个互斥训练模型。前者属于有顺序的在线评测，不能写成冻结记忆的独立测试。

**限制和对照意义。** 功能步骤切分与视觉归因会错，冷启动结果受顺序/调度影响；成功导出与几何忠实分开。旧“条件化修复规则跨任务迁移”候选应降级。若继续做动作推理，应研究它未直接隔离验证的**多步效果交互与搜索顺序**，并直接复现同预算局部搜索作为基线。

<a id="update-27"></a>
#### B-SP05 — Graph-CAD：图分解、动作规划和能力边界课程都有直接先例

**来源。** Shengjie Gong 等，*Learning Hierarchical and Geometry-Aware Graph Representations for Text-to-CAD*，ICLR 2026。[正式 PDF](https://proceedings.iclr.cc/paper_files/paper/2026/file/90e06fe49254204248cb12562528b952-Paper-Conference.pdf)。读 §3–4、Tables 1–3、Appendix C.4、D 的相关实验。

**方法。** 三阶段是几何分解图→动作序列→bpy 代码。三个 Qwen3-8B 模块做 LoRA；SAPCL 生成易/中/难结构变体，在能力边界及稍难处补数据，再训练。也比较冻结通用模型的两示例三阶段推理，不能说全部改善只能靠训练。

**实验。** BlendGeo 约 12K 数据，90/10 训练/验证；CADBench 700 例。但 GCS 只基于其中 **280 例、约 500 条人工几何约束**，利用部件名称匹配和数值几何检查，并非全部 700 例的联合成功率。Table 3 有去图、去动作计划、直接生成；Figure 6 的课程对照匹配每轮数据量。训练每轮约 30 小时数据合成＋双 A800 上三天微调，共四轮。

**限制和对照意义。** GCS、图精度与 VLM 外观分数不同；复杂有机形状和精密装配仍失败，训练与评测部分共享 VLM 判别方式。不能把“分层图＋动作规划”或“按当前能力边界造题训练”重新命名为新方法。对冻结模型的研究，应与其三阶段提示版本比较。

<a id="update-32"></a>
#### TileGPT — Generative Design through Quality-Diversity Data Synthesis and Language Models

**来源与读取：** GECCO 2024；本轮读取[arXiv 2405.09997v1](https://arxiv.org/html/2405.09997v1) §2–5，重点§3与§4.1–4.2；[Autodesk官方入口](https://www.research.autodesk.com/publications/generative-design-quality-diversity-data-synthesis-language-models/)核对出版身份。

**方法与实验：** MAP-Elites生成带属性设计，微调DistilGPT2生成粗布局，WFC补全约束细节。两组训练数据各50,000设计，比较QD与随机WFC数据；25×15网格，243种属性提示各生成100次。有效性按WFC补全计，属性匹配在有效结果上分别计算。

**边界与冲突：** 不是任意IFC与开放自然语言；交互修改没有独立评测。直接覆盖“多样性＋语言模型＋约束”，压缩粗表示也已有。D1须比较同表示的QD，并证明新的结构冲突/预算机制；不能仅因换成IFC称新颖。

### 阅读位置与来源记录

逐篇原始卡片保留定位细节：[structured-generation](literature-evidence/structured-generation.md)；[frontier-spatial](literature-evidence/frontier-spatial.md)；[frontier-reasoning](literature-evidence/frontier-reasoning.md)。阅读卡是证据，不是额外研究路线。

## 3. 通用AI：知识利用、技能、规划与验证

普通检索、上下文压缩、技能记忆、世界模型和规格检查都不能单独作为新方法。D2应研究操作交互的条件与迁移，D1应研究结构冲突与覆盖决策。

本模块64条研究记录。

| Paper：名称、版本与原始来源 | 贡献与观点 | 实验场景与证据边界 | 与我们的冲突点 |
|---|---|---|---|
| **Executable Code Actions Elicit Better LLM Agents**<br>D08 · F；ICML 2024，正式正文<br>[会议入口](https://proceedings.mlr.press/v235/wang24h.html)；[正式全文](https://raw.githubusercontent.com/mlresearch/v235/main/assets/wang24h/wang24h.pdf) | 以可执行 Python 统一工具调用，用控制流组合操作与中间结果，再依运行反馈纠错；另构造 CodeActInstruct 并微调 7B 模型。 | APIBank 和 82 个 M3ToolEval 比较代码、JSON、文本行动格式；MINT 等另测微调与域内/外泛化。代码总体有优势，但部分模型和原子调用下 JSON 更好。<br>边界：JSON 对照是工具行动格式，不等于与高层 BIM 编译器表达能力匹配的 JSON。微调实验与提示格式比较必须分开，不能合并成同一因果论证。 | N02 的代码工具组合、N05 的执行探查有基础先例；text2IFC 的强基线必须允许组合、执行和调试。N07 不能预设 JSON 比代码更优，需控制相对位置抽象与复用能力。 |
| **SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering**<br>D12 · F；NeurIPS 2024；主文、相关表格，未逐页审计全部附录<br>[会议全文](https://papers.neurips.cc/paper_files/paper/2024/file/5a7c947568c1b1328ccc5230172e1e7c-Paper-Conference.pdf) | 围绕代理设计搜索、文件窗口、编辑/linting 和历史管理接口，通过工具反馈处理真实仓库；接口设计本身是受控研究变量。 | 完整 SWE-bench 2294、Lite 300，另有 HumanEvalFix；对照 shell-only/RAG 并消融接口。GPT-4 Turbo 在 Lite 为 18%，shell-only 11%；全文件或全历史不如所选窗口。<br>边界：费用主表按成功实例平均，不能与全任务费用直接比较；每题有美元上限，模型和接口是当时固定版本，未必代表当前最强代理。 | N05/N08 若只增加专用工具或调整可见上下文，已有很强先例。text2IFC 需要可分离的新决策机制，基线也应具备合理搜索、反馈与编辑，而不是仅单次吐 IFC。 |
| **Demystifying LLM-Based Software Engineering Agents**<br>D18 · F；FSE 2025，作者正文<br>[作者全文](https://lingming.cs.illinois.edu/publications/fse2025.pdf) | 分层定位文件和片段，采样 Search/Replace 补丁，以现有回归测试及生成复现测试筛选；采取明确的定位—生成—验证流程，而非自由探索代理。 | SWE-bench Lite 正文 96/300=32%，均费约 0.70 美元，默认每题 40 补丁及 40 测试候选。98/300 是直接采用 benchmark PASS_TO_PASS 列表的另一个条件。<br>边界：榜单比较含系统/模型差异，测试泄漏和覆盖有限；多候选最佳值不等于最终提交表现，不同测试条件的成绩不能混用。 | N05 主动探索、N01/N04 动态决策应有固定流程强对照，否则 loop 复杂度不是贡献。text2IFC 还需隔离独立评测器，不可把私有答案反复作为生成反馈。 |
| **RepairAgent: An Autonomous, LLM-Based Agent for Program Repair**<br>D19 · F；arXiv 2403.17134v2，2024-10-28<br>[v2 全文](https://arxiv.org/html/2403.17134v2) | 状态机控制可用工具，动态提示保存故障假设、代码和测试反馈，代理在理解、检索和修补之间切换，进行自主程序修复。 | Defects4J 全部 835 故障，另抽 100 新 GitBug-Java 故障；区分测试通过与人工判定正确，报告正确修复 164。真实故障定位消融降低效果并增加成本。<br>边界：需要揭示故障的测试，定位质量影响结论；270k token 在摘要称 average、正文称 median，不能据此给可靠均值或沿用旧价格。 | N03 的 Repair+Agent+记忆已有先例，创新应是有条件经验如何预防未见生成失败；N05 的故障假设探索也需具体差异。text2IFC 要另外验证几何、关系及未受影响内容保全。 |
| **PAFT: Preservation-Aware Fine-Tuning for Minimal-Edit Program Repair**<br>D20 · F；arXiv 2604.03113v1（2026）<br>[v1 全文](https://arxiv.org/html/2604.03113v1) | 对齐 buggy/fixed token，提高稳定片段权重，将全序列监督、修改难度课程和 QLoRA 组合，优化修复中不必改动内容的保留。 | 1535 训练对、三种微调 backbone，测试 Java 修复；报告测试通过、编辑距离、复制比例及人评。SFT/PAFT 主对照监督 mask 也不同，另有拆分消融。<br>边界：编辑量主要在 plausible patch 子集计算，通过测试不等于完全语义正确；局限单文件 Java，不能直接外推跨文件或 IFC 关系保全。 | N01/N03 若以最小改动或保全作为新目标，已有研究；但其训练机制不等同同模型的经验条件修订。text2IFC 要独立评几何/属性/关系保全，并把微调投入与当前无训练候选分开。 |
| **CodeMEM: AST-Guided Adaptive Memory for Repository-Level Iterative Code Generation**<br>D07 · F；Findings of ACL 2026，正文<br>[ACL 全文](https://aclanthology.org/2026.findings-acl.834.pdf) | AST 引导代码记忆选择，以签名和轻量描述索引实现；保存会话要求与修改，检测遗忘指令再修订，面向仓库级多轮生成。 | CodeIF 40 对话/360 指令、CoderEval 230 Python 任务，对照完整上下文与记忆系统。CodeIF token 为 107.8k，低于 FC BM25 的 131.8k，但高于若干记忆对照。<br>边界：CoderEval 中成本也高于 FC BM25，不能概括为一律省 token；长工业仓库、选择遗漏仍受限。历史保存和最终正确是不同指标。 | N03 的跨任务预防要区别于会话内遗忘修订，N08 要超越 AST 检索；N01 若只把失败轨迹写入记忆也不足。text2IFC 应同时计成功、学习成本与后续检索，不只挑昂贵基线。 |
| **RepoCoder: Repository-Level Code Completion Through Iterative Retrieval and Generation**<br>D09 · F；EMNLP 2023，正式正文<br>[ACL 全文](https://aclanthology.org/2023.emnlp-main.151.pdf) | 未完成代码和前轮预测共同形成新检索查询，持续提供仓库片段再补全；包括滑窗和 Jaccard 相似度实现，属于预测反馈的迭代 RAG。 | 正文 RepoEval：行/API 各 1600、函数 373，测匹配及函数测试。GPT-3.5 函数通过率 23.32%→一次检索 38.34%→两轮 42.63%，继续迭代并非单调提升。<br>边界：基准命名在摘要入口和 PDF 有差异，此处按正文；低重复仓库、停止时机、在线成本仍有限制，oracle 上下文只是分析条件。 | N05 的增量必须超过“生成后再检索”，N08 必须区别于相关性迭代更新。text2IFC 应测某次获取知识为何有价值与何时停止，而不能仅增加 loop 轮数后称方法创新。 |
| **Repoformer: Selective Retrieval for Repository-Level Code Completion**<br>D10 · F；ICML 2024，正式正文<br>[会议入口](https://proceedings.mlr.press/v235/wu24a.html)；[正式全文](https://raw.githubusercontent.com/mlresearch/v235/main/assets/wu24a/wu24a.pdf) | 通过联合训练选择与补全，预测特殊 token 及阈值决定是否需要仓库上下文，把“何时检索”变成模型行为，兼顾检索延迟与生成质量。 | 在 RepoEval、CrossCodeEval、CrossCodeLongEval 比较模型大小及串/并行检索，测匹配、测试和延迟；1B greedy/API 约 69% 加速伴随 edit similarity 下降。<br>边界：最高约 70% 加速不是所有质量点都成立，保守阈值收益较小。训练过的选择器不能当无训练插件；本地卡未保留各测试规模，不补推分母。 | N05 的信息动作选择必须超越检索开关，N08 的组合价值也需区别于单次检索收益。text2IFC 若固定模型，应报告无需微调的机制及同预算效果，不能直接套用其训练结论。 |
| **RepoGraph: Enhancing AI Software Engineering with Repository-Level Code Graph**<br>D11 · F；ICLR 2025，正式正文<br>[会议全文](https://proceedings.iclr.cc/paper_files/paper/2025/file/4a4a3c197deac042461c677219efd36c-Paper-Conference.pdf) | 从 AST 提取定义、引用、包含和调用边，以符号查 k-hop 子图，平铺或摘要后接入 Agentless、SWE-agent 等系统。 | SWE-bench Lite 300 题及 Python CrossCodeEval；四个基础系统均提高成功率，但 token 与费用也均增加。2-hop 平铺可弱于 1-hop，摘要也并非总有利。<br>边界：部分基线来自榜单/公开轨迹，不构成严格等预算因果比较；更多依赖上下文可能引入干扰。图邻域增益不代表最终保全或所有仓库通用收益。 | N04/N08 不能以依赖图、局部切片或摘要本身称新。text2IFC 要同时测遗漏关键关系和引入干扰的代价；只有执行层面的依赖开放/知识协同胜过相同预算图基线，才支持增量。 |
| **LLMLingua: Compressing Prompts for Accelerated Inference of Large Language Models**<br>D13 · F；EMNLP 2023，正式正文<br>[ACL 全文](https://aclanthology.org/2023.emnlp-main.825.pdf) | 按提示组成分配预算，以小模型困惑度筛选示例和 token，迭代更新压缩上下文并做模型分布对齐，研究高压缩下的推理质量。 | GSM8K、BBH、ShareGPT、Arxiv-March23 分别测答案准确率或文本相似度，含预算、迭代、对齐消融；高压缩部分保持质量，BBH 等也出现下降。<br>边界：未证明标识符、数值、字段和关系逐项保全，极端压缩继续失真；压缩器有计算成本。本地记录未列各任务样本数，不能补写为已核分母。 | N08 应证明执行协同选择胜过通用文本压缩，N07 不能把 token 改写视为语义等价证明。text2IFC 应保留所有方法相同的不可删任务事实，最终以 IFC 要求验收而非压缩率评胜负。 |
| **LongLLMLingua: Accelerating and Enhancing LLMs in Long Context Scenarios via Prompt Compression**<br>D14 · F；ACL 2024，正式正文<br>[ACL 全文](https://aclanthology.org/2024.acl-long.91.pdf) | 问题相关的粗细两级压缩、文档重排、动态预算，并从原文恢复输出中的压缩实体；处理长上下文的位置和冗余问题。 | NaturalQuestions、LongBench、ZeroSCROLLS、MuSiQue、LooGLE 上比较检索/压缩，分析答案位置及组件消融；不同任务指标不能简单合成同一种成功率。<br>边界：每个问题重压缩妨碍上下文复用，计算高于 LLMLingua；子串恢复不保证复杂隐含依赖。已核卡没有保留逐数据集分母，本条不填猜测值。 | N08 的问题条件化压缩不是空白，需额外证明知识组合对执行的价值；N07 的实体恢复也不同于参考系正确。text2IFC 应计入压缩时间、缓存变化和失败尝试，不能只报最终输入长度。 |
| **From RAG to Memory: Non-Parametric Continual Learning for Large Language Models**<br>FK01 · F；ICML 2025；核查 arXiv v2，数字不混用正式版<br>[arXiv v2 全文](https://arxiv.org/html/2502.14802v2) | 将 OpenIE 三元组、概念与原始段落共同索引；整条查询匹配三元组，经 LLM 过滤后用 Personalized PageRank 传播并检索段落。贡献在关系检索与非参数记忆，而非让生成的图事实直接取代证据。 | NQ、PopQA、MuSiQue、2Wiki、HotpotQA 各 1,000 查询，LV-Eval 124，NarrativeQA 293 查询/10 文档；统一模型并比较向量检索、RAPTOR、GraphRAG。MuSiQue Recall@5 为 69.7→74.7，QA F1 为 45.7→48.6。<br>边界：连续学习只是四批语料加入；干扰增加时复杂问答仍退化，未证明知识失效处理或可执行技能迁移。检索分数不是任务成功率。 | 冲突 N08 与一般 knowledgebase 叙述：图关系检索和长期记忆已有。text2IFC 需证明实际执行中的知识协同/干扰超出图闭包，或解决版本与适用条件变化；仅把 IFC/API 连成图不构成新方法。 |
| **Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models**<br>FK02 · F；arXiv v1，2025 预印本；未混入后续版本<br>[arXiv v1 全文](https://arxiv.org/html/2510.04618v1) | Generator、Reflector、Curator 维护条目级增量 playbook，记录 helpful/harmful 次数并定期去重，避免整段上下文重写丢失细节。把经验维护作为适配过程，基础模型权重不更新。 | 在 AppWorld normal/challenge、FiNER、Formula 做离线及先预测后更新的在线适配，统一 DeepSeek-V3.1，比较 ICL、GEPA、Dynamic Cheatsheet。AppWorld 平均栏 42.4→59.5 是四个 TGC/SGC 数值均值；已读正文未给各划分绝对分母。<br>边界：FiNER 在线无标签结果 67.3，低于基础模型 70.7；缺乏可靠反思反馈可能负迁移。多轮离线、在线调用不能视作无成本收益。 | 直接冲突 N01/N03 的经验修订叙述。错误本、条目 ID、反思和去重都已有；text2IFC 需用同模型 ACE 对照，证明条件化反例能减少错误迁移及误拒绝，而不是仅换经验格式。 |
| **CRAFT: Customizing LLMs by Creating and Retrieving from Specialized Toolsets**<br>FK03 · F；ICLR 2024 正式全文<br>[ICLR 2024 正式全文](https://proceedings.iclr.cc/paper_files/paper/2024/file/af31604708f3e44b4de9fdfa6dcaa9d1-Paper-Conference.pdf) | 先生成具体 Python 题解，再抽象变量与接口，在原题验证并去重；从题目、函数名和 docstring 三种视角检索工具。无需微调即可把求解经验转成可执行能力库。 | VQA 建库抽样 2,000 题，表格/数学各 500，形成 525/181/282 个工具；评测 VQA、TabMWP、MATH algebra，其中代数 881 题。GPT-4 建库、GPT-3.5 执行。TabMWP 的 BM25 89.2 高于 CRAFT 88.4；VQA 实测分母未明确。<br>边界：主要在原生成题验证，未保证跨参数正确；强模型建库影响归因。CREATOR 对照移除其校验/纠正，只比一次执行。 | 冲突 N01/N02 及“从成功 IFC 脚本提炼工具”。需同模型、同成本建库，并验证适用范围、未见组合及负迁移；工具更多或强模型把知识转给弱模型不能单独归因于新学习机制。 |
| **ExpeL: LLM Agents Are Experiential Learners**<br>FK04 · F；AAAI 2024 正式正文与 arXiv v2 分别核查；两版本分母披露分开保留<br>[AAAI 2024 正式全文](https://ojs.aaai.org/index.php/AAAI/article/download/29936/31635)；[arXiv v2 全文](https://arxiv.org/html/2308.10144v2) | 比较同任务成败轨迹及跨任务成功轨迹，以增加、修订和投票删除方式维护自然语言经验；部署时读取经验并检索成功示例。跨域 fine-tune insights 指经验文本改写，不是参数微调。 | 评测 HotpotQA、ALFWorld、WebShop，并向 FEVER 迁移；GPT-4 提炼、GPT-3.5 执行，比较仅检索、仅经验和 Reflexion。正式正文卡未恢复绝对分母；arXiv v2 附录 D 明示 100/134/100 任务及四折半训练半测试设置，FEVER 另用目标示例适配。<br>边界：不同任务上的经验收益不一致；全部经验进入提示未证明长期扩张效率。离线收集、强模型提炼和重试成本必须计入，跨域并非完全零适配。 | 直接冲突 N03，也约束 N01：总结修复失败帮助下次生成已有。text2IFC 要测试相似但前提不成立的经验，证明有条件复用/拒用/修订优于相同轨迹的 ExpeL，而非把跨工作流连接另算创新。 |
| **SePer: Measure Retrieval Utility Through the Lens of Semantic Perplexity Reduction**<br>FK05 · F；ICLR 2025 正式全文<br>[ICLR 2025 正式全文](https://proceedings.iclr.cc/paper_files/paper/2025/file/c44c4afd77d5ee760e7f4bed0c50f878-Paper-Conference.pdf) | 采样答案并按语义聚类，衡量加入检索材料前后对参考正确答案的信念变化，用来评价材料对特定模型的效用。区分文本相关与实际有用，而非直接提出无需标注的在线检索控制器。 | 三套简单 QA、四套多跳 QA；默认每查询采样 10 次，消融 1/5/10/15/20 次；部分推理分析最多抽取 1,000 题。HotpotQA 效用相关系数为语义熵 0.339、软 SePer 0.660，属于标签相关性，不是任务成功率。<br>边界：需要参考答案；多跳中间材料按步骤均分总效用的假设有限。采样成本不低，不能把私有正确答案放进运行时选择器。 | 直接冲突 N08 的“效用不同于相关性”。text2IFC 需从公开可执行信号判断组合协同/干扰，再以独立隐藏评测核验；仅重命名效用指标或使用 Gold 选择知识不成立。 |
| **Counterfactual Reasoning for Retrieval-Augmented Generation**<br>FK06 · F；ICLR 2026 正式全文<br>[ICLR 2026 正式全文](https://proceedings.iclr.cc/paper_files/paper/2026/file/1c078897dc08d46091d0d361d9955c6b-Paper-Conference.pdf) | 改写角色、时间、实体、类别和范围形成对照问题；检索、分层采样证据并生成候选答案，通过原查询与对照查询的相关性差异评分，不微调基础模型。 | 五套 QA、两个 Llama 模型，默认 3 对照问题、4 证据簇、3 草稿。稳定性在 500 个 HotpotQA 查询重复 5 次，延迟测 1,000 查询/4×A100。49.00→88.58 实为 +39.58 个百分点，非 +80.8 个百分点；使用 Smart EM。<br>边界：主表总分母未明确；Smart EM 含 containment/语义变体，不能混作严格 EM。引用结果与重跑混合；并行延迟接近不代表总 token 一样。 | 冲突 N05/N08 的反事实检索。text2IFC 应以执行探测区分可用规则及前提，并与同预算文本对照比较；使用反事实措辞本身不证明物理因果关系或新增能力。 |
| **ToolChoiceConfusion: Causal Minimal Tool Filtering for Reliable LLM Agents**<br>FK07 · F；arXiv v1，2026-06-04 预印本<br>[arXiv v1 全文](https://arxiv.org/html/2606.06284v1) | 把工具前置变量和产生变量组织成状态依赖图，以 BFS 找目标路径，每步只展示下一工具。causal 指操作依赖，状态表示为变量可用性的单调累积，不是完整环境因果模型。 | 102 个合成任务、100 工具、4 模型、6 策略，共 2,448 运行；固定 mock、最多六步。整条路径与逐步 CMTF 均约 0.99 成功，token 为 2,555/2,405；大幅节省主要相对全工具的 24,569。<br>边界：状态、目标及人工合同已给定，每题一条 gold chain，可能把其他合法路线判错。作者也讨论不确定状态的诊断/恢复工具扩展。 | 直接冲突 N05 与宽泛的必要知识/工具最小化。IFC 中仅把 BFS 图换成实体/API 依赖图不新；剩余问题须是合同不完整、非单调状态或异质未知来源下怎样选择查证，并超过此基线。 |
| **Retrieval as Reasoning: Self-Evolving Agent-Native Retrieval via LLM-Wiki**<br>FK08 · F；arXiv v1，2026-05-25 预印本<br>[arXiv v1 全文](https://arxiv.org/html/2605.25480v1) | 将文档编成带出处和双向链接的 Wiki，Agent 组合 search/read 与链接遍历，按证据充分性停止；Error Book 保存失败原因和规则，结合确定性与 LLM 修补更新知识。 | 三套多跳 QA 各 500 问题，另有 AuthTrace；统一 GLM-5.1 与 Qwen3-Embedding-8B，最多 15 工具调用，比较七基线及结构、遍历、错误本消融。MuSiQue F1 为 0.739，对照 LightRAG 为 0.659。<br>边界：查询延迟不包含所有建库、跨批修复成本；单文档 AuthTrace 低于 HippoRAG 2，重组可能丢失局部细节。单次 top-5 与多轮遍历并非天然同预算。 | 覆盖 N03 的错误经验与 N05/N08 的可组合知识遍历。text2IFC 加 Wiki、错误本或自修正循环不足；需展示执行条件的可靠迁移、选择机制增益与学习成本摊销。 |
| **Design-Specification Tiling for ICL-based CAD Code Generation**<br>FK09 · F；arXiv v1，2026-03-13 预印本<br>[arXiv v1 全文](https://arxiv.org/html/2603.12712v1) | 把设计说明拆成多长度 n-gram，以联合覆盖需求片段为代理目标，贪心选择互补上下文示例。近似保证针对覆盖目标，不针对真实知识充分性、执行正确率或所有组合关系。 | Text2CAD 描述和 GenCAD-Code 均源于 DeepCAD，筛后 151,940 三元组；三复杂度各抽 300、共 900 测试，其余为 ICL 库。三个固定模型，主表 5-shot，对比随机、BM25、编辑距离和多样性选择；hard VSR 均未超过各自最强对照。<br>边界：描述去重与难度抽样不是设计族隔离。API 错误改善明显，几何组合仍难；几何评分可相对 GT 在 96 种变换中择优，不能支持绝对尺寸/方向正确。 | N08 必须正面对照：为组合建模需求挑互补知识已有很近方法。text2IFC 需证明真实执行协同/干扰超出需求词覆盖，并保持同信息、同上下文预算；更多覆盖或 token 压缩不足。  <br>补充核查见[本条更新](#update-10)。 |
| **Voyager: An Open-Ended Embodied Agent with Large Language Models**<br>SK01 · F；核查 arXiv v2<br>[arXiv v2 全文](https://arxiv.org/html/2305.16291v2) | 自动课程提出任务，冻结的 GPT-4 生成 JavaScript，结合执行反馈与自验证迭代；成功程序形成可执行技能库，以描述检索后复用。展示不更新基础模型权重也能积累外部行为能力。 | 探索预算 160 次提示迭代、3 次运行，钻石工具并非每次成功。迁移仅 4 个未见任务，每项 3 次、最多 50 提示迭代；去掉技能库后，3 个任务仍 3/3，钻石镐 2/3，库也主要改善部分求解效率。<br>边界：提示次数不等于所有 token 或技能获得成本；四任务迁移规模有限，基线的课程与环境适配差异影响归因。不能从开放探索展示推出广泛零样本泛化。 | 覆盖 N01/N02 的冻结模型、成功程序记忆和技能复用。text2IFC 应检验适用边界及未见组合，并同预算比较；仅形成更大 IFC 工具库或加 Agent loop 已有明确先例。 |
| **LILO: Learning Interpretable Libraries by Compressing and Documenting Code**<br>SK03 · F；核查 arXiv v2<br>[arXiv v2 全文](https://arxiv.org/html/2310.19791v2) | LLM 与枚举搜索共同找程序，以 Stitch 描述长度目标压缩库，AutoDoc 为抽象命名和写说明；允许重新组织库，而非简单去重。冻结所得库后的无 LLM 求解也用于验证抽象本身的价值。 | 训练/测试为 REGEX 491/500、CLEVR 191/103、LOGO 200/111，三种子。每任务最多 4 提示×4 补全，并有 600/1,000/1,800 秒枚举及多轮学习预算；区分在线与离线求解。<br>边界：较大枚举和建库成本不等同廉价一次调用；主要是输入输出明确的 DSL，未直接验证 IFC 的状态副作用。结果应与库大小、文档和搜索预算共同理解。 | 直接约束 N02：程序抽象、语义重写、命名和未见任务收益已有。不能用机械 AST 去重充作唯一基线；text2IFC 要证明组合表现修订宏边界/参数化的额外作用，并对照 SK15 的关系算子学习。 |
| **Empowering Large Language Model Agents through Action Learning**<br>SK04 · F；COLM 2024；核查 arXiv v2 与会议标注 PDF<br>[arXiv v2 全文](https://arxiv.org/html/2402.15809v2)；[论文 PDF](https://arxiv.org/pdf/2402.15809) | 学习 Python 动作及使用说明，依据训练执行失败更新动作代码或补充注释，从多个候选更新中选择。动作空间可以修订，因此比单纯保存成功轨迹的静态技能库更接近方法对照。 | 每类仅 3 个训练任务，涵盖 4 类规划任务和 6 类 ALFWorld，每类重复 3 次。表 7 消融只采样、不改函数、不改注释；多轮优化也观察到过拟合。现有卡未恢复完整测试实例的统一分母，不反推成功个数。<br>边界：少训练任务不等于少调用，候选采样、评估和多轮更新都有成本。局部失败修复可能过拟合，不能凭最新一例成功证明新任务上的技能提升。 | N01 的最强近邻之一：失败后修代码或改说明已经存在。剩余候选必须是有效比较修实现、收窄条件和拆库，而非再加一段反思提示；应与 LearnAct 加同预算测试的组合直接比较。  <br>补充核查见[本条更新](#update-1)。 |
| **SkillWeaver: Web Agents can Self-Improve by Discovering and Honing Skills**<br>SK05 · F；arXiv v1，2025 预印本<br>[arXiv v1 全文](https://arxiv.org/html/2504.07079v1) | 从探索轨迹生成 Playwright API，自动产生参数测试并调试，文档记录网站前置状态，检索时排除前提不满足的工具。把技能发现、测试、改进及前提过滤连成可执行学习流程。 | 每网站预探索 160 轮、每轮最多 10 步；评测 812 个 WebArena 任务及 4 个真实网站上的 57 任务。表 1 中 GPT-4o WebArena 成功率 22.6%→29.8%；失败分析含 API/参数选择错误与基础 Agent 能力不足。<br>边界：不是完全未接触目标网站的迁移；一次宏可含多底层动作，步数减少不等于全成本节省。需计探索与测试开销，生成测试也可能遗漏要求。 | N01/N02 不能以“可执行技能＋测试＋前提过滤”自称新。text2IFC 需证明修订边界/新宏机制超过相同测试与调试能力，并检查跨场景负迁移，而非仅增加工具包装。 |
| **PolySkill: Learning Generalizable Skills Through Polymorphic Abstraction**<br>SK06 · F；核查 arXiv v1；未合并后续版本结果<br>[arXiv v1 全文](https://arxiv.org/html/2510.15863v1) | 用抽象类表达领域无关目标，用具体子类实现不同网站行为；新技能通过重放原任务验证，跨网站可探索学习新实现。目标接口与具体实现分离使复用超出逐段代码检索。 | Mind2Web 训练 1,009，跨任务/网站/领域测试 252/177/912，另测 WebArena 812。静态库并非全面提升：Qwen 跨领域 37.5%→35.9%，在线版本 39.9%，说明适配方式显著影响结果。<br>边界：跨网站不是零适配；效率只统计成功轨迹且宏计一步。初始抽象、长尾目标和环境变化仍限制泛化，需要额外探索成本与失败分母。 | 直接冲突 N01 的多实现拆分及 N02 的抽象目标/角色复用。text2IFC 要证明用组合失败修订新宏程序比多态目标抽象更有效；仅按目标聚类、换宿主实现或增加类接口不够。 |
| **Memento-Skills: Let Agents Design Agents**<br>SK07 · F；arXiv v1 PDF，2026 预印本；HTML 实验抽取不完整<br>[arXiv v1 PDF](https://arxiv.org/pdf/2603.18743v1) | 冻结基础 LLM，把失败归因到技能并修改其文件，也能新建或重组技能；检索路由器另用对比学习。外部技能可以演进，但基础模型冻结并不等于整个系统没有训练。 | GAIA 165 个任务分 100 训练/65 测试；HLE 子集为 788/342。GAIA 测试报告 66.0%，静态基线 52.3%；每题允许 3 次反思重试。作者还发现大量 GAIA 学得技能未在测试中触发。<br>边界：不能把训练成功率当测试表现，聚合比例也不宜自行换整数成功数。需要单列路由训练、合成测试、重试及技能获得成本；学得技能未必迁移。 | N01/N02 的自改技能及冻结基础模型已有近邻。text2IFC 若主张无需训练应明确作用范围；优势要来自条件/宏修订机制在未见任务的收益，而非额外路由训练或更多试错。 |
| **Contract2Tool: Learning Preconditions and Effects for Reliable Tool-Augmented LLM Agents**<br>SK08 · F；arXiv v1，2026-06 预印本；未假定同行评审<br>[arXiv v1 全文](https://arxiv.org/html/2606.07904v1) | 从元数据、文档或状态轨迹推断工具前提、效果、风险与成本，归一成契约后用于因果过滤。把合同获取从人工标注扩展到证据学习，覆盖“何时可用、会改变什么”而非仅调用格式。 | 固定状态词汇，100 合成工具、102 多步任务，另有 283 黄金决策步。表 V 全工具/学习契约成功率 .775/.980，每任务平均 token 26,172/2,528；主要轨迹为受控模拟中的成功路径。<br>边界：主聚合排除调用兼容性差的一个模型；固定词汇和稀疏成功轨迹可能漏罕见效果。不是开放真实 API 或 IFC 全成本验证，也未证明未知状态下的普遍可靠性。 | 直接覆盖 N01/N05 的契约学习与选工具。text2IFC 仅添加关系前后条件不足；需比较成功契约与成本匹配主动反例，证明联合修程序/修范围/拆库的额外行为。  <br>补充核查见[本条更新](#update-2)。 |
| **SLBench: Evaluating How LLM Agents Follow Logical Relations in Skills**<br>SK09 · F；arXiv v1，2026-07 预印本<br>[arXiv v1 全文](https://arxiv.org/html/2607.09016v1) | 把前后条件、约束、回退、例外、覆盖等八类技能逻辑组织为仓库与产物检查任务，考察 Agent 是否遵守技能关系；另用调用前后检查表缓解违规。逻辑遵循与完成任务分别评价。 | 核心为人工审计 86 例，39 控制/47 违规触发，不能混同大规模构建语料。缓解实验只在选出的 11 个此前违规案例上从 11 降至 4；表中同时报告 unsafe 与 inconclusive。<br>边界：守卫评价把未违规的 inconclusive 合入 safe，不能当整体成功提升。附录约 1.017 亿 token 是流水线估计成本；关系义务不同于 IFC 空间语义，样例也不是违规普遍率估计。 | 约束 N01/N02 的技能合同及 N03 的生成禁忌规则：前后关系检查本身已有。text2IFC 必须同时测误拒绝、未知和完整任务成功，不能用少违规取代能力扩展，或宣称检查表提供全局保证。 |
| **DreamCoder: Growing generalizable, interpretable knowledge with wake-sleep Bayesian program learning**<br>SK10 · F；本地卡核查 arXiv 原始 PDF；未固定该下载链接的修订号<br>[原始论文 PDF](https://arxiv.org/pdf/2006.08381) | 在 wake 阶段搜索程序，sleep 阶段从程序中学习可复用 DSL 抽象，并训练识别网络引导搜索；抽象考虑语义等价重写，形成可解释的组合知识。程序库增长与搜索能力相互促进。 | 列表实验包含 218 个任务，半训练半测试，并覆盖多个其他领域；递归程序展示使用较大 CPU 与时间预算。现有卡核查了搜索、抽象学习及实验，但没有保存所有领域的统一分母和精确配置，不能补猜。<br>边界：识别网络涉及训练，不能称为整个系统完全冻结；不同任务的搜索/学习成本需要核对。有限输入输出样本上的程序正确不代表具有任意 IFC 状态副作用的普遍保证。 | 直接约束 N02：程序压缩、抽象和组合泛化已经成熟，基线必须允许语义重写。text2IFC 需证明组合反馈修订宏程序的额外收益，而非重做宏提取；SK15 又已覆盖关系效果与角色算子。 |
| **Epistemic Exploration for Generalizable Planning and Learning in Non-Stationary Settings**<br>SK11 · F；ICAPS 2024 正式全文<br>[ICAPS 2024 出版商 PDF](https://ojs.aaai.org/index.php/ICAPS/article/download/31489/33649/35546) | 考虑谓词在前提/效果中的正、负、缺省候选，构造能够区分候选行动模型的规划问题，再执行探测更新模型；环境变化时只重新学习相关部分。把信息获取与关系规划结合，减少盲目探索。 | 使用四个规划域、每任务 100,000 步与 10 个种子等条件，比较模型学习和规划/强化学习策略。现有卡已读方法、实验及结论，但没有记录可直接迁用的 IFC 任务分母或同 token 结果。<br>边界：学习对象是行动模型，不是同时编写和修订新宏程序；理论及效率依赖规定的可观察状态、模型和环境条件。不能把领域模拟器的学习结果直接转成开放工具或真实建筑保证。 | 对 N01/N05 是强先例：主动选择区分性探测已有。剩余问题应是程序与适用条件同时可能错误时如何选择修订，或不同信息来源如何统一决策；仅把探测换成 IFC 沙箱不构成创新。 |
| **LLM Agents Making Agent Tools**<br>SK12 · F；ACL 2025 正式全文<br>[ACL 2025 正式全文](https://aclanthology.org/2025.acl-long.1266.pdf) | 给定论文代码库与工具要求，自动建立可重现执行环境，再实现、测试和调试 Python 工具；不只写简单函数，还处理依赖安装与可执行环境，供下游 Agent 重用。 | TM-Bench 为 15 工具任务、42 测试调用、124 单元测试。完整工具通过 12/15，OpenHands 3/15；平均每工具生成成本分别 $0.94/$0.15，动作 21.8/7.5，不能把更高通过率当相同预算收益。<br>边界：输入示例未覆盖特殊情况会影响工具泛化；测试通过只覆盖这些调用。环境设置能力与额外搜索也解释差异，复杂仓库任务不能等同冻结工具池下的抽象学习。 | 覆盖 N02 及能力缺口合成的宽泛故事：需要时自动造工具已有可运行系统。text2IFC 应在相同原语、同预算下证明新宏的迁移与摊销价值；仅增加 API 或安装新库属于能力扩展工程。 |
| **CREATOR: Tool Creation for Disentangling Abstract and Concrete Reasoning of Large Language Models**<br>SK13 · F；Findings of EMNLP 2023 正式全文<br>[EMNLP Findings 2023 全文](https://aclanthology.org/2023.findings-emnlp.462.pdf) | 先创建可复用函数，再为具体实例决定调用，交给解释器执行并根据错误反馈修正；将抽象工具构造与具体问题求解分开，避免所有推理挤在一个程序生成阶段。 | 评测 MATH、TabMWP 与 2K Creation Challenge，前两者只选数字答案，约占原问题 80%，不是完整测试集。比较程序求解、带修正的程序求解、工具使用及不分离阶段的消融，现有卡不提供全子集精确计数。<br>边界：示例与纠错预算影响结果，数字答案筛选限制外推；执行成功不能推出任意输入下正确。不能将不同提示、重试配置合成一次无额外计算的提升。 | 约束 N02 和“先合成缺口再组合”的故事。先写小工具、再决定怎么用已经存在；text2IFC 需证明组合表现能改进宏边界或条件，而非仅把 creation/decision/execution/repair 四阶段换名称。 |
| **AdaPlanner: Adaptive Planning from Feedback with Language Models**<br>SK14 · F；NeurIPS 2023 正式全文<br>[NeurIPS 2023 正式全文](https://papers.nips.cc/paper_files/paper/2023/file/b5c8c1c117618267944b2617add0a766-Paper-Conference.pdf) | 以 Python 计划和子目标断言执行任务，区分符合预期与偏离预期的反馈；必要时修改整个计划并从中间恢复，同时保存成功计划作为后续少样本示例。连接计划修订与经验发现。 | ALFWorld 134 个环境；MiniWoB++ 53 类任务使用 38 个人工示例加 21 个发现示例，部分对照结果引自原论文。正文包含代码接口、闭环修订与技能发现消融，现有卡没有逐项转存成功率。<br>边界：复杂任务仍依赖专家示范；环境、模型版本和示例数不同的结果不能混作同模型收益。成功计划复用不等于已学会适用边界，重试与发现示例也有成本。 | 覆盖 N01/N03 的循环、失败恢复和经验库，也约束普通子目标验证叙述。text2IFC 的方法贡献不能是“多轮 Agent”；应定位可替换的修订选择机制并测未见任务迁移。 |
| **Embodied Active Learning of Relational State Abstractions for Bilevel Planning**<br>SK15 · F；CoLLAs 2023，PMLR 232:358–375；18 页会议版<br>[PMLR 出版记录](https://proceedings.mlr.press/v232/li23a.html)；[CoLLAs 2023 正式全文](https://proceedings.mlr.press/v232/li23a/li23a.pdf) | 按同一控制器且效果在对象替换下等价来分组轨迹，以前态交集学习条件，用变量角色替换对象，再学习参数采样器；神经集合熵驱动提问与前瞻探索，每轮更新谓词、算子及采样器。 | 三个模拟域、六基线；每域 50 示范、1,000 探索转换、50 留出任务、10 种子。Blocks 从 3–4 块迁移至 5–6 块；与 Ask All 成功接近而查询更少，规划限 10 秒，通常每次运行 3–36 小时。<br>边界：给定谓词名、类型、控制器和已知模拟器；脚本专家提供标签。查询效率不等于总训练/模拟成本，也未生成新的宏程序。 | 直接下调 N02：关系效果分组、角色抽象、前提学习及组合不能称新。N01 泛称联合学技能/条件也不足；只剩自生成程序的修补、范围收窄、拆库竞争选择，以及新宏本身的组合反馈修订有待验证。  <br>补充核查见[本条更新](#update-3)。 |
| **Automated Repair of Ambiguous Natural Language Requirements**<br>FR01 · F；arXiv v1，2025 预印本<br>[arXiv v1 全文](https://arxiv.org/html/2505.07270v1) | 采样 20 个程序，用生成测试区分执行行为，再利用公开示例选解释，对比相合与不合的程序来修订自然语言需求，最多三轮。把可执行行为差异用于需求消歧，而非只做语言改写。 | HumanEval+ 164、MBPP+ 378，三个模型、三次重复。DeepSeek-V3 的 HumanEval+ Pass@1 为 87.80→91.99；比较移除隐藏答案辅助的 ClarifyGPT-auto 等，需连同多程序采样和修订成本理解。<br>边界：有限程序和测试只近似解释空间；公开示例不足时，多数解释也可能错。v1 部分形式定义与算法方向表述不一致，不能照抄公式或把一致性当真实意图。 | 直接约束 N06：多采样、发现分歧、补问已存在。text2IFC 要证明按空间后果或修改成本选择可执行对照能减少返工，并与相同图形界面的普通 Agent 比较；两张图本身可能只是交互设计。 |
| **From Errors to Proofs: Minimal-Core-Guided Repair for Neuro-Symbolic Constraint Solving**<br>FR02 · F；arXiv v1；注明 IJCAI-ECAI 2026 LogiSymb workshop poster，非主会<br>[arXiv v1 全文](https://arxiv.org/html/2608.14771v1) | LLM 输出固定结构并由 clingo 求解，用删除过滤找到冲突约束子集，按错误类型反馈修复，最多三轮。将笼统求解失败转成较小冲突证据，支持对不可行性的识别。 | 77 个模板题、七领域，其中 14 不可行；主模型 CoT 98.7%、通用修复 88.3%、冲突核修复 89.6%，不是所有情况下更优。弱模型在不可行题编造解从 11/14 降到 1/14。<br>边界：minimal 是子集极小，不保证数量最少。两修复组的错误类型反馈也不同，需析因分离；每系统 token 未报告。漏编码的真实要求即使形式可满足也不会被求解器发现。 | N03/N04 不能首创冲突核或定向修复。text2IFC 必须研究冲突规则的适用条件、跨任务迁移或接口选择，独立核对用户要求，防止删掉需求后得到形式成功。 |
| **Large Language Models Can Solve Real-World Planning Rigorously with Formal Verification Tools**<br>FR03 · F；NAACL 2025 正式全文；未声称逐页审计全部附录<br>[NAACL 2025 正式记录](https://aclanthology.org/2025.naacl-long.176/)；[NAACL 2025 正式全文](https://aclanthology.org/2025.naacl-long.176.pdf) | 将用户查询转成步骤与 Z3 代码，结合外部 API 与求解器；不可满足时利用冲突核提出约束调整并接受用户反馈，把规划、验证及协商连接为系统流程。 | TravelPlanner 180 验证、1,000 测试题，最佳测试成功率 93.9%。另外 39 和 12 个不可行情景，以模拟用户偏好评估协商，并在四个新规划领域各测 25 题；不同设置不能合成单个统一分母。<br>边界：包含人工示例，不同模型主表不等于同模型增益。协商增加轮数同时增加成本；形式正确约束于实际编码内容，不能自动保证语言转译完整。模拟用户不是实际用户研究。 | 直接覆盖 N04/N06 的求解矛盾与用户协商。text2IFC 需要研究几何/关系跨模块依赖或对照问题选择，并测真实意图；接入 SMT 模块或展示冲突解释不足以构成新方法。 |
| **Know Where You’re Uncertain When Planning with Multimodal Foundation Models: A Formal Framework**<br>FR04 · F；MLSys 2025 正式全文<br>[MLSys 2025 正式全文](https://proceedings.mlsys.org/paper_files/paper/2025/file/703f727ec10190b2fddcf8e24f52df48-Paper-Conference.pdf) | 区分感知不确定与决策不确定，用校准和形式规格估计计划风险，再分别采取主动感知或模型适配。重点是发现风险来自哪里并选择对应干预，而非仅输出一个总置信度。 | 感知校准 542 图/3,000 对象，决策校准 400 场景；另用 800 Carla 图适配，50 测试场景验证规划。校准、适配和测试数据用途不同，不能相加后当作独立测试分母。<br>边界：微调、主动感知和拒绝执行共同影响结果，不是固定参数下纯控制策略收益。校准保证依赖分布等条件；减少错误计划不等于完成所有任务，拒绝率需独立报告。 | N05 仅区分知识/实例/意图缺口仍不够。text2IFC 需设计可执行辨别步骤，证明选资料、实例查询、探测或澄清比同预算通用 Agent 有效；置信度不能代替真实 IFC 检查。 |
| **Relational Decomposition for Program Synthesis**<br>FR05 · F；IJCAI 2025 正式全文<br>[IJCAI 2025 正式全文](https://www.ijcai.org/proceedings/2025/0504.pdf) | 把数组等输入输出展开成关系事实，使用 POPPER 与背景知识综合较小的关系程序，与整体函数表示比较。表示分解改变搜索问题，使某些任务更容易由可组合关系规则解释。 | ARC、一维 ARC、字符串、列表四类任务，多个时间预算、重复实验及留一验证。60 分钟表中字符串关系分解 71±2、整体表示 79±2；列表 52±2/14±1，收益明显依赖任务，现有卡未给全部绝对分母。<br>边界：假定无噪声并借封闭世界生成负例；表示和搜索偏置不完全一致，部分基线引用原结果。IFC 缺失记录不等于关系真实为假，不能直接照搬负例构造。 | N02 不能是“换成关系图再综合”。同时 SK15 已覆盖效果/角色算子学习；text2IFC 剩余候选需修订新宏程序并处理组合干扰，且与同关系输入的强规划/综合器比较。 |
| **Progent: Securing AI Agents with Privilege Control**<br>D15 · F；arXiv 2504.11703v3（2026）；早期版本题名不同<br>[v3 全文](https://arxiv.org/html/2504.11703v3) | 以确定性策略检查工具和参数权限，用 SMT 判断策略是否扩大，区分收窄、扩权与不变量；目的是阻断不被授权的代理操作。 | AgentDojo/ASB 分别评价正常任务效用和注入攻击成功率；主体即使总接受扩权，报告 ASR 39.9%→1.0%、70.3%→3.9%。这些是安全攻击指标。<br>边界：结果依赖策略边界和批准行为，文本输出攻击不在主要范围；有操作权限不代表执行结果满足领域要求，不能转成 IFC 正确率或压缩收益。 | N01/N04 若只是加参数权限或受控扩大操作范围，已有形式方法先例。text2IFC 可将其作为执行基础，但候选创新仍需证明技能适用性/依赖选择对建模成功的作用。 |
| **MiniScope: A Least Privilege Framework for Authorizing Tool Calling Agents**<br>D16 · F；arXiv 2512.11147v1（2025）；完整题名由主任务补核<br>[v1 全文](https://arxiv.org/html/2512.11147v1) | 从服务权限与 API 方法建立层级，以 ILP 为执行计划选择所需权限，经会话 token 和调用检查落实；优化的是权限暴露而非生成上下文。 | 10 个真实应用的合成请求，对照 LLM 权限推断，测过权和延迟；确认负担使用模拟用户/请求，不是真实参与者实验，运行开销不含用户确认时间。<br>边界：最小性相对于给定计划、映射和代价定义，资源级参数约束主要作为后续方向；不能将优化可解直接视为未知任务也具备充分权限。 | N05/N08 的“足够且尽量少”目标有概念先例。text2IFC 必须证明执行假设或知识相互作用带来的新增机制，不能只把 ILP 的权限集合换成知识片段/token 预算。 |
| **Do Coding Agents Understand Least-Privilege Authorization?**<br>D17 · F；arXiv 2605.14859v2（2026）<br>[v2 全文](https://arxiv.org/html/2605.14859v2) | 评测读/写/执行权限推断，提出先保障任务充分性、再审核收窄的两阶段策略；将足够执行与减少暴露分开检验。 | 120 终端任务含 80 常规、40 敏感，以安全轨迹和 strace 标注；固定执行 Agent 比较权限生成模型，同时测匹配、执行成功、安全暴露，增加推理不总有效。<br>边界：参考权限只是一个安全工作流代理，不是唯一最小权限；是否足够还依赖执行 Agent，静态匹配不能替代任务执行。 | N05/N08 的先找足够知识再压缩有相邻思想，N01 限制技能范围也须兼顾可完成性。text2IFC 的方法增量应建立在具体执行假设、反例和关系上，不能只改“权限”为“上下文”。 |
| **Co-Evolving LLM Decision and Skill Bank Agents for Long-Horizon Tasks（COS-PLAY）**<br>补查 · F；[指定版本正文](https://arxiv.org/html/2604.20987v1) | 联合演化决策Agent与带前提/效果的技能库，允许细化、合并、拆分和退役。 | 6游戏，每游戏60教师轨迹；评测回合与多玩家单位分开，训练5个LoRA。 | 技能修订类型不是D2新意；要比较交互效果如何迁移。 [详细核查](#update-4) |
| **Bayesian-Agent: Posterior-Guided Skill Evolution for LLM Agent Harnesses**<br>补查 · F；[指定版本正文](https://arxiv.org/html/2606.08348v1) | 用条件化失败后验选择patch、split、compress、retire等技能修订。 | 三个任务域样本分母20/20/40；部分任务改善、部分退化，无重复误差条。 | 直接覆盖技能修订选择；IFC封装不足以形成新方法。 [详细核查](#update-5) |
| **PURPLE：Optimizing User Profiles via Contextual Bandits for Retrieval-Augmented LLM Personalization**<br>补查 · F；[指定版本正文](https://arxiv.org/html/2601.12078v1) | 冻结LLM，学习集合感知上下文重排，建模条目非加性效用。 | 九种个性化任务，候选20选5、每例32组合；各任务绝对分母未齐。 | 知识协同与集合监督已有；执行任务须再证条件化迁移。 [详细核查](#update-6) |
| **DearICL：Data Efficient Sample Selection for In-Context Learning**<br>补查 · F；[指定版本正文](https://arxiv.org/html/2609.06670v1) | 学习查询与示例子集的收益代理，主动试验边界组合。 | GSM8K1319、AquaRAT254；WMT19分母含糊；主模型3B、5-shot。 | 组合交互、主动试样与新题选择已有，不能只更换IFC奖励。 [详细核查](#update-7) |
| **CAMAB：Context Attribution with Multi-Armed Bandit Optimization**<br>补查 · F；[指定版本正文](https://arxiv.org/html/2506.19977v1) | 以Thompson Sampling选上下文掩码，通过token似然归因。 | SST2/HotpotQA各500、两模型，20/40/60查询预算；本版加性假设。 | 干预式知识归因已有；解释旧回答不等于得到正确答案。 [详细核查](#update-8) |
| **EvoR：Evolving Retrieval for Code Generation**<br>补查 · F；[指定版本正文](https://aclanthology.org/2024.findings-emnlp.143.pdf) | 执行结果共同更新检索查询与代码/错误知识库。 | 四集142/45/107/113，共407；两生成模型，最多30轮，有知识组合消融。 | 执行驱动检索与知识组合已有，需计全部迭代成本。 [详细核查](#update-9) |
| **ClarifyGPT: A Framework for Enhancing LLM-Based Code Generation via Requirements Clarification**<br>补查 · F；[指定版本正文](https://linshi-website.github.io/paper/ClarifyGPT.pdf) | 采样多个程序，用生成测试的执行聚类发现分歧并提问。 | 正式版五基准与10人反馈实验；不能与早期四基准混计。 | 多解分歧驱动澄清已有；编程错误也可能造成分歧。 [详细核查](#update-11) |
| **Active Task Disambiguation with LLMs**<br>补查 · F；[指定版本正文](https://arxiv.org/html/2502.04485v1) | 按候选程序执行划分估计问题的信息增益并考虑成本。 | HumanEval48、APPS47；正文统一48存在不一致；最多4轮提问。 | 信息增益选问题已有，尚不能据此假设用户无误回答。 [详细核查](#update-12) |
| **Clarify Before You Draw: Proactive Agents for Robust Text-to-CAD Generation**<br>补查 · F；[指定版本正文](https://arxiv.org/html/2602.03045v1) | ProCAD分别训练澄清器和代码器，澄清规格后生成CAD。 | 2469测试含1000清晰、1065缺维度、404冲突；模型模拟回答。 | CAD澄清不是空白；多候选预览需隔离呈现与策略收益。 [详细核查](#update-13) |
| **LLM-based Test-driven Interactive Code Generation: User Study and Empirical Evaluation**<br>补查 · F；[指定版本正文](https://arxiv.org/html/2404.10100v1) | TiCoder利用可区分测试向用户提问，筛选/排序生成程序。 | 15人3题研究，另有MBPP427/HumanEval164；时间差未显著。 | 交互式执行反馈已有；评价须容许误答与不确定。 [详细核查](#update-14) |
| **Act or Clarify? Modeling Sensitivity to Uncertainty and Cost in Communication**<br>补查 · F；[指定版本正文](https://arxiv.org/html/2602.02843v1) | 以预期损失和信息价值解释何时澄清。 | 行为实验125人；另一实验120招募、排除2人；并非CAD算法。 | 按返工代价决定提问不是新理论。 [详细核查](#update-15) |
| **VeriAct / Spec-Harness, 2604.00280v1**<br>补查 · F；[指定版本正文](https://arxiv.org/html/2604.00280v1) | 用正确输入输出、输出变异与非法输入检查JML规格并反馈修订。 | 120与筛后662个Java方法；GEPA另有100/50/512划分；有限MVR阈值。 | 验证规格和变异测检查强度已有；开放设计无单一参考行为。 [详细核查](#update-16) |
| **Prompt Coverage Adequacy, 2607.02057v1**<br>补查 · F；[指定版本正文](https://arxiv.org/html/2607.02057v1) | 用attention干预后的概率变化估计测试对请求条款的覆盖并补测试。 | 164 HumanEval+、112 LCB子集；增强实验88/68错误实现；需内部模型访问。 | 需求覆盖已有方法，但代理覆盖不是正确性证明。 [详细核查](#update-17) |
| **Specification Self-Correction, 2507.18742v1**<br>补查 · F；[指定版本正文](https://arxiv.org/html/2507.18742v1) | 通过生成与论证发现rubric缺陷，再修规格并重生成。 | 写作每模型48；coding正文5与表中8不一致；主要格式/关键词诱因。 | 规格自修订已有，不能借修订悄悄放宽用户要求。 [详细核查](#update-18) |
| **Code-A1, 2603.15611v1**<br>补查 · F；[指定版本正文](https://arxiv.org/html/2603.15611v1) | 代码与测试模型对抗训练，用参考正确代码校正测试，记录失败测试。 | 9688训练题，1.5B/3B/7B；代码与测试基准，测试侧含10%子集。 | 生成器/检查器共同学习已有；参考代码依赖不能隐去。 [详细核查](#update-19) |
| **CURE, 2506.03136v2**<br>补查 · F；[指定版本正文](https://arxiv.org/html/2506.03136v2) | 联合训练代码和测试，以区分正确/错误程序奖励测试。 | CodeContests4500训练/200留出，LCB511、CodeForces500；16×16采样、8A100。 | 执行监督不等于无外部真值；改成IFC奖励不自动构成方法。 [详细核查](#update-20) |
| **L1 — CWM: An Open-Weights LLM for Research on Code Generation with World Models**<br>补查 · F；[指定版本正文](https://arxiv.org/html/2510.02387v1) | 训练预测代码执行状态与Agent环境响应。 | 32B训练含120M函数/3M轨迹；8B追踪消融提升执行预测未提升SWE；16候选另计。 | 状态预测不保证任务改善，D2必须测规划收益和所有成本。 [详细核查](#update-28) |
| **L2 — Absolute Zero: Reinforced Self-play Reasoning with Zero Data**<br>补查 · F；[指定版本正文](https://arxiv.org/html/2505.03335v1) | 模型同时出题和解题，执行器验证，多任务强化学习。 | 7B主实验，另3B/14B/8B；3代码/6数学基准；组合课程有负结果。 | 可验证自博弈与非退化检查已有；零题库不等于无先验。 [详细核查](#update-29) |
| **L3 — SWE-smith: Scaling Data for Software Engineering Agents**<br>补查 · F；[指定版本正文](https://arxiv.org/html/2504.21798v1) | 在可测试仓库合成破坏、执行筛选并采集修复训练轨迹。 | 128仓库约50k任务，20k尝试得5016成功轨迹；Verified500、Lite300。 | 破坏—修复训练已有；更难不保证更有训练收益。 [详细核查](#update-30) |
| **L4 — Hybrid-Gym: Training Coding Agents to Generalize Across Tasks**<br>补查 · F；[指定版本正文](https://arxiv.org/html/2602.16819v1) | 通过定位、依赖探索、函数生成等辅助任务训练跨任务能力。 | 4470轨迹/762仓库，7B/32B；部分机制只测Easy50，另两主测试分母未齐。 | 混合任务不是新意；表示、工具与轨迹形式必须控制。 [详细核查](#update-31) |
| **ChopChop — A Programmable Framework for Semantically Constraining the Output of Language Models**<br>补查 · F；[指定版本正文](https://doi.org/10.1145/3776708) | 在可能程序空间上做语义剪枝，约束token前缀的可完成性。 | v1：10等价任务、74个TypeScript子集任务、三模型五温度；400token/150秒。 | 语义约束生成已有；类型任务编译成功不等于功能正确。 [详细核查](#update-33) |
| **SCOPE — Programming over Thinking: Efficient and Robust Multi-Constraint Planning**<br>补查 · F；[指定版本正文](https://aclanthology.org/2026.acl-long.2028.pdf) | 查询特定结构参数与可复用生成/过滤/交付函数分离。 | 五模型，旅行/行程/会议规划；部分Trip半集、部分方法另有全量结果。 | 执行器分工与减少重复代码已有；仍依赖正确形式化。 [详细核查](#update-34) |

### 重点补充核查

<a id="update-1"></a>
#### Empowering Large Language Model Agents through Action Learning（LearnAct）

**[Empowering Large Language Model Agents through Action Learning（LearnAct）](https://arxiv.org/html/2402.15809v2)**：§4、算法1已改 Python 动作和说明，从4个更新候选中选择。§5、表7覆盖4类规划及6类 ALFWorld，每类3训练任务、3次重复；有代码／注释消融及过拟合。完整测试分母尚缺。“多种修订再测试选择”已有。

<a id="update-2"></a>
#### Contract2Tool: Learning Preconditions and Effects for Reliable Tool-Augmented LLM Agents

**[Contract2Tool: Learning Preconditions and Effects for Reliable Tool-Augmented LLM Agents](https://arxiv.org/html/2606.07904v1)**：§III–IX从文档、轨迹学前提和效果，再过滤工具。100合成工具、102任务，表V成功率 .775→.980；固定谓词、主要成功路径，聚合排除一个兼容性差的模型。它覆盖合同学习，未联合改执行程序。

<a id="update-3"></a>
#### Embodied Active Learning of Relational State Abstractions for Bilevel Planning

**[Embodied Active Learning of Relational State Abstractions for Bilevel Planning](https://proceedings.mlr.press/v232/li23a/li23a.pdf)**：§3–5以集合熵主动探索；按控制器和对象替换后的效果分组，联合更新谓词、算子、参数采样器。3域，各50示范、1000转换、50留出任务、10种子；单次3–36小时。控制器已给定，但“主动学条件与技能结构”已有。

<a id="update-4"></a>
#### Co-Evolving LLM Decision and Skill Bank Agents for Long-Horizon Tasks（COS-PLAY）

**[Co-Evolving LLM Decision and Skill Bank Agents for Long-Horizon Tasks（COS-PLAY）](https://arxiv.org/html/2604.20987v1)**：§4.2已有带前提／效果契约的技能，以及 refine、merge、split、retire。§5、表1用6游戏、每游戏60教师轨迹；单人16、多人游戏每玩家10评测回合。技能主要是提示协议，系统训练5个 LoRA；没有独立证明三类修改如何选择。

<a id="update-5"></a>
#### Bayesian-Agent: Posterior-Guided Skill Evolution for LLM Agent Harnesses

**[Bayesian-Agent: Posterior-Guided Skill Evolution for LLM Agent Harnesses](https://arxiv.org/html/2606.08348v1)**：§3.4、表1在冻结 LLM 下，用条件化失败证据选择 patch／split／compress／retire／explore，修订提示技能文本。§4.2的 GA→BA-Full（flash）：SOP 16/20→19/20，Lifelong 18/20→17/20，RealFin 18/40→21/40；无重复试验误差条。采用固定阈值，未比较竞争修订的反事实效果；增量成本只计补救，§4.4另给累计值。**它直接覆盖原 N01 的选择框架。**

<a id="update-6"></a>
#### PURPLE：Optimizing User Profiles via Contextual Bandits for Retrieval-Augmented LLM Personalization

**来源与读取：** [PURPLE：Optimizing User Profiles via Contextual Bandits for Retrieval-Augmented LLM Personalization](https://arxiv.org/html/2601.12078v1)，2026 v1，§3–5、Limitations、附录 D

冻结 LLM，训练集合感知重排器；Transformer 建模条目依赖，Plackett–Luce 采样，每例 32 个组合，以参考回答似然作奖励。九种个性化任务，候选 20 选 5，三种生成模型；多数设置三次，GPT-5-nano 排序基线单次，各任务绝对分母未明列。**非加性、非单调效用及集合监督已直接覆盖**；但各任务分别训练，未测跨任务/域迁移，并非执行正确性实验。

<a id="update-7"></a>
#### DearICL：Data Efficient Sample Selection for In-Context Learning

**来源与读取：** [DearICL：Data Efficient Sample Selection for In-Context Learning](https://arxiv.org/html/2609.06670v1)，2026-09 v1，§3–5、§8、附录 B/E

学非线性“查询＋示例子集→收益”代理；gap-index 主动试边界组合，测试时直接排序。GSM8K 1319、AquaRAT 254；WMT19 分母含糊。主模型 Llama3.2-3B、5-shot；GSM8K 75.66% 对动态 CASE 70.00%。**学组合交互、选择新题上下文、减少试样成本均已有**。奖励是参考答案 BERTScore；理论界有代理偏差等条件，仅覆盖已访问候选池，不是全部子集保证。

<a id="update-8"></a>
#### CAMAB：Context Attribution with Multi-Armed Bandit Optimization

**来源与读取：** [CAMAB：Context Attribution with Multi-Armed Bandit Optimization](https://arxiv.org/html/2506.19977v1)，2025 v1，§3–4、Limitations

Thompson Sampling 选择上下文掩码，以原回答的归一化 token 似然归因。SST2/HotpotQA 各抽 500、两模型，比较 SHAP、ContextCite、leave-one-out 及 20/40/60 查询预算。**按干预收益选择下一次试验也已有**。此版假设加性；解释原回答不等于使回答正确，不能与后续正式版混写。

<a id="update-9"></a>
#### EvoR：Evolving Retrieval for Code Generation

**来源与读取：** [EvoR：Evolving Retrieval for Code Generation](https://aclanthology.org/2024.findings-emnlp.143.pdf)，EMNLP Findings 2024，§2–4、表 1–4、§7

执行结果同时更新检索查询、代码/错误知识库，不训练重排器。四集分别 142/45/107/113 题，共 407；模拟 SciPy/TensorFlow 更新及 Ring/Pony，两生成模型。表 4 已有执行反馈、代码、文档的单独/两两/三者组合消融。**执行驱动知识组合不是空白**；无异常仅作为语法正确信号，最多 30 轮，存在延迟成本。

<a id="update-10"></a>
#### DST：Design-Specification Tiling for ICL-based CAD Code Generation

**来源与读取：** [DST：Design-Specification Tiling for ICL-based CAD Code Generation](https://arxiv.org/html/2603.12712v1)，2026 v1，§2–4、附录 B/E/F

多粒度文本覆盖＋submodular 贪心选示例；900 测试、三模型、主表 5-shot。hard 有效率未超过各模型最强对照。它不学执行交互，但已覆盖“互补建模知识选择”；其近似保证针对文本覆盖，不能移作真实执行保证。

<a id="update-11"></a>
#### ClarifyGPT: A Framework for Enhancing LLM-Based Code Generation via Requirements Clarification

**来源与读取：** [ClarifyGPT: A Framework for Enhancing LLM-Based Code Generation via Requirements Clarification](https://linshi-website.github.io/paper/ClarifyGPT.pdf)，FSE 2024，§3–5、Tables 3–4

多程序采样、生成/变异测试、执行结果聚类，再用不同簇的程序生成问题。10 人反馈实验；正式版自动评价覆盖五个基准，与早期四基准版本不能混用。直接覆盖“执行差异发现歧义”；模型自身错误也可能产生分歧。

<a id="update-12"></a>
#### Active Task Disambiguation with LLMs

**来源与读取：** [Active Task Disambiguation with LLMs](https://arxiv.org/html/2502.04485v1)，ICLR 2025 作者 v1，§2–5、Appendix E/F

从候选解估计问题的信息增益，并扣提问成本。代码实验从 5 个问题选一个，最多 4 轮，按候选程序执行结果分割解空间；HumanEval 表为 48 题、APPS 表为 47 题，正文有统一写 48 的不一致。查询选择本身需更多 LLM 调用，作者将它视为相对用户反馈便宜。用户错误与“不知道”没有纳入主要模型。直接覆盖“执行候选＋信息增益”。

<a id="update-13"></a>
#### Clarify Before You Draw: Proactive Agents for Robust Text-to-CAD Generation

**来源与读取：** [Clarify Before You Draw: Proactive Agents for Robust Text-to-CAD Generation](https://arxiv.org/html/2602.03045v1)，2026 预印本，§3、5.2、6.3、Table 4/7

ProCAD 对澄清器和代码器分别 SFT，先收集一批问题，下一轮接受修订规格；§3 已写几何质量和沟通成本目标，实际训练为轨迹 SFT。Table 7 的 2,469 测试包含 1,000 清晰、1,065 缺维度、404 冲突提示，不能全称歧义测试。用 GPT-5-mini 模拟回答并以另一模型检查迁移；同代码器对照可分离部分澄清收益。固定两轮与正确回答假设限制真实交互结论。

<a id="update-14"></a>
#### LLM-based Test-driven Interactive Code Generation: User Study and Empirical Evaluation

**来源与读取：** [LLM-based Test-driven Interactive Code Generation: User Study and Empirical Evaluation](https://arxiv.org/html/2404.10100v1)，2024 作者 v1，§IV–VII、Table III

TiCoder 按测试的区分能力提问并剪枝/排序代码；15 人、3 题的用户实验另于 MBPP 427 / HumanEval 164 自动实验。通过/失败式反馈下判断正确性较好，但时间差未显著；不同反馈形式出现不同误答。已覆盖用户认知负担、测试驱动意图与可执行反馈，不能声称此前只测代码正确率。

<a id="update-15"></a>
#### Act or Clarify? Modeling Sensitivity to Uncertainty and Cost in Communication

**来源与读取：** [Act or Clarify? Modeling Sensitivity to Uncertainty and Cost in Communication](https://arxiv.org/html/2602.02843v1)，2026 作者 v1，Experiments、Computational Model、Discussion

以 expected regret / 信息价值解释澄清。第一实验 125 人；第二实验招 120 人、排除 2 人，研究不确定程度与错误代价。是语言/行为实验，非 CAD 执行算法；但“预计返工损失高才问”的抽象思想已被覆盖，不能当新理论。

<a id="update-16"></a>
#### VeriAct / Spec-Harness, 2604.00280v1

**来源与读取：** [VeriAct / Spec-Harness, 2604.00280v1](https://arxiv.org/html/2604.00280v1)，§3–7

**方法、实验与限制：** 用已知正确输入输出、变异输出及显式非法输入检查 JML 前后条件，反馈给 CodeAct 式 Agent。120 与筛后 662 个 Java 方法；GEPA 实验另有 100/50/512 划分。MVR 用有限样本与阈值定义，并非完整性证明。检索显示新版本标题为 Spec-Harness，本卡严格使用 v1 标题与结果。

**冲突点：** “验证器也要验证”“用变异测规格强弱”“规格修订闭环”均已有。其输入是假定正确程序的行为，不直接解决开放设计中多个合法结果与自然语言遗漏。

<a id="update-17"></a>
#### Prompt Coverage Adequacy, 2607.02057v1

**来源与读取：** [Prompt Coverage Adequacy, 2607.02057v1](https://arxiv.org/html/2607.02057v1)，§IV–VII、算法1、表III

**方法、实验与限制：** 用 attention spotlighting 后的概率变化估计测试覆盖哪些请求句子，再补测试。164 个 HumanEval+、论文使用的 112 个 LCB v6 子集；测试增强分别用 88/68 个错误实现。需模型内部访问；覆盖是代理指标，正确性仍借助参考实现，未覆盖性能测试。

**冲突点：** “从原始请求独立测需求覆盖”不是全新问题；增加 coverage 数字不等于方法创新。

<a id="update-18"></a>
#### Specification Self-Correction, 2507.18742v1

**来源与读取：** [Specification Self-Correction, 2507.18742v1](https://arxiv.org/html/2507.18742v1)，§2–3、表1–2

**方法、实验与限制：** 先生成、解释如何符合错误 rubric，再修订 rubric 并重生成。写作每模型 48 任务；coding 正文称 5 项、表2称每模型 8 项，分母不一致。主要注入关键词/格式诱因，不能外推空间语义漏检。

**冲突点：** “发现规格有问题就改规格”已有；须区分恢复原始要求与悄悄放宽要求。

<a id="update-19"></a>
#### Code-A1, 2603.15611v1

**来源与读取：** [Code-A1, 2603.15611v1](https://arxiv.org/html/2603.15611v1)，§3–4、附录F

**方法、实验与限制：** 两模型对抗训练代码与测试，测试可看候选，参考正确代码负责校正测试答案。9,688 道训练题、1.5B/3B/7B；评 HumanEval+、MBPP+、BigCodeBench 与测试基准的 10% 子集。维护失败测试记忆，有相应消融。依赖参考代码，两个模型的分离不应被转述为排除一切共谋的证明。

**冲突点：** “生成器与检查器对抗共同进步”“动态测试课程”“失败记忆”均已有。开放 IFC 没有逐请求参考程序时，测试有效性不能照搬。

<a id="update-20"></a>
#### CURE, 2506.03136v2

**来源与读取：** [CURE, 2506.03136v2](https://arxiv.org/html/2506.03136v2)，§3–4、表1

**方法、实验与限制：** 联合提升代码与测试生成，以已知正确/错误程序的区分能力给测试奖励。CodeContests 4.5k 训练、200 留出，另评 LCB 511、CodeForces 500 等；16 代码×16 测试采样，使用 8 A100 训练。并非完全无外部真值。

**冲突点：** 换 IFC 奖励、从执行结果训练小模型本身不新；要证明新的可迁移监督或决策机制。

<a id="update-28"></a>
#### L1 — CWM: An Open-Weights LLM for Research on Code Generation with World Models

[原始全文，2510.02387v1，2025-09-30](https://arxiv.org/html/2510.02387v1)。本轮读 §2、§7.1–7.2、§8.3。

学习对象是代码执行后的状态和工具环境响应。32B 模型的中期训练含 120M 函数追踪、3M Agent 轨迹；后者保留成功和失败，并训练预测动作及环境响应。§7.1 的受控实验使用 8B、总计 7T token：加入执行追踪后 CruxEval-O 从 44.6 到 73.9，但 SWE-bench Verified 从 18.6% 到 18.4%；再加入 ForagerAgent 才到 22.1%。最终 32B 在全部 500 题上单次尝试平均 53.9%，65.8% 是 16 个候选及额外测试选择的结果。

**冲突与启发：**“学执行语义而非代码文本”已被明确提出。更会预测执行，不保证更会完成任务；必须证明所学关系效果实际改善规划或生成。论文未证明小规模 IFC 数据足以重现效果，其大规模训练不能当作本项目已有前提。

<a id="update-29"></a>
#### L2 — Absolute Zero: Reinforced Self-play Reasoning with Zero Data

[原始全文，2505.03335v1，2025-05-06](https://arxiv.org/html/2505.03335v1)。本轮读 §3–4、Appendix C、D.1–D.3。

同一模型同时出题和解题，Python 执行器构造并验证程序、输入、输出三类推理任务；出题奖励偏向部分可解的问题，用多任务 REINFORCE 更新权重。主实验是 Qwen 7B，另有 3B、14B、Llama 8B；评估 3 个代码、6 个数学基准，v1 主表未逐项列出题数，不能把 9 个基准当 9 道题。7B-Coder 综合均分提高 10.2 点。消融中不训练 proposer 只降 1.4 点。

**最相关负结果：**Appendix D.2 已尝试组合旧函数形成课程，未见显著收益，常退化为 `f(g(x)) = g(x)`；论文还提出用执行检查排除捷径。因此“组合课程 + 非退化检查”也不是可直接占据的空白。其零数据指无新增人工题库，仍依赖预训练模型和人工设计的任务/奖励。

<a id="update-30"></a>
#### L3 — SWE-smith: Scaling Data for Software Engineering Agents

[原始全文，2504.21798v1，2025-04-30](https://arxiv.org/html/2504.21798v1)。本轮读 §2–4、§6。

先建立可测试代码环境，再通过模型改写、AST 修改、组合错误、回退 PR 产生训练题；执行确认确实破坏既有测试。128 仓库约 50K 任务，从 20K 次专家尝试得到 5,016 条成功轨迹训练学生。32B 在 SWE-bench Verified 的 500 题上单次成功率 40.2%；另测 Lite 300 题。

**冲突与负证据：**自动破坏—修复、组合错误、执行筛选、成功轨迹训练都已做过。§4 固定每组 500 条训练轨迹，四档难度在 Verified 上为 12.4/10.8/13.6/12.2%，没有“更难即更有效”的趋势。将测试内容放入问题还改变了学生行为。迁移取决于数据分布和监督形式，不只取决于修复题难度。

<a id="update-31"></a>
#### L4 — Hybrid-Gym: Training Coding Agents to Generalize Across Tasks

[原始全文，2602.16819v1，2026-02-18](https://arxiv.org/html/2602.16819v1)；[作者代码及 ICML 2026 标注](https://github.com/Hybrid-Gym/Hybrid-Gym)。本轮读 §2–4、Appendix A.3。

通过函数定位、问题定位、依赖搜索、函数生成等辅助任务，训练与目标任务共用的探索、推理、文件修改能力。4,470 条轨迹、762 仓库；训练 7B/32B，在问题修复、测试生成、库生成上测迁移。32B 的 SWE-bench Verified 从 7.0% 到 32.4%，另两类分别提高 7.85/5.11 点。Table 5 有每种辅助任务 500 条、修复 491 条的对照；§4 部分机制消融仅在筛选的 Easy 50 上完成，不能当完整基准结论。本文未清楚列齐另两个主测试分母，此处不补猜。

**冲突与启发：**跨任务数据混合不是新意；输出接口、真实探索和轨迹结构本身会产生大影响。作者 7B 训练使用 8 张 A6000、32B 使用 2 张 H100，不能假设微调完全没有资源代价。对 text2IFC 必须控制输入表示和动作接口，否则所谓迁移可能只是学会格式。

<a id="update-33"></a>
#### ChopChop — A Programmable Framework for Semantically Constraining the Output of Language Models

**来源与读取：** POPL 2026，DOI [10.1145/3776708](https://doi.org/10.1145/3776708)；机制和实验数字据[arXiv 2509.00360v1](https://arxiv.org/html/2509.00360v1) §2–6、§8，不将v1与定稿差异默认为一致。

**方法与实验：** 语法映射程序空间，语义pruner检查部分token前缀能否补成满足条件的AST。比较无约束、语法约束和语义约束；10个等价改写任务及809个MultiPL-E TypeScript任务中可表达的74个；三个6.7B–13B模型、五种温度，400-token/150秒限制。

**边界与冲突：** 类型任务以编译通过计，并非功能正确；有限类型/语言子集限制适用范围。约束化输出不新，JSON格式约束也不等于此语义机制；token级访问与检查开销须单独评估，不能直接承诺可接所有闭源API。

<a id="update-34"></a>
#### SCOPE — Programming over Thinking: Efficient and Robust Multi-Constraint Planning

**来源与读取：** ACL 2026；[正式PDF](https://aclanthology.org/2026.acl-long.2028.pdf) §3–5、Table 1及§4脚注；未逐项重算附录全部实验。

**方法与实验：** 示例驱动生成结构化组合/约束接口和可复用Combination、Filter、Deliver函数；推理时填参数，不再为每题生成求解代码。五种闭源模型，TravelPlanner和Natural Plan的Trip/Meeting任务；对照CoT、ToT、ToS、CPMPy等，提供同类示例。部分Trip比较只抽半集，Direct/CoT/SCOPE另有全量表，不能混分母。

**边界与冲突：** 依赖形式化覆盖和域内可复用函数，尚非开放IFC多方案编辑。编译器分工、结构化输入和减少重复代码已是先例；“已由执行器承担的内容不再给LLM”不能单独作为AI新方法。

### 阅读位置与来源记录

逐篇原始卡片保留定位细节：[coding-knowledge-and-control](literature-evidence/coding-knowledge-and-control.md)；[frontier-knowledge](literature-evidence/frontier-knowledge.md)；[frontier-skills](literature-evidence/frontier-skills.md)。阅读卡是证据，不是额外研究路线。
