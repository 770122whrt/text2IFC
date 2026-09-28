# BIM 创作、布局与相关综述：原文证据卡

核验日期：2026-09-15。范围为调查稿 2A 对应的 A01–A14；调查稿只用于找文献，以下判断来自论文原文、原始出版商预览、作者仓库及机构书目。本文服务于 text2IFC 的候选研究问题：**可执行 IFC 接口与理解编译器约束的任务知识，在给定 token 预算下是否改善生成能力与成本。** 这是待验证的问题，不是已经成立的创新声明。

读取等级：**FULLTEXT** 表示实际读到方法、实验及讨论/局限的原始全文；不代表逐字阅读全部参考文献、复现实验或取得全部数据。**PARTIAL** 表示只读到原始出版商的部分正文预览，尚未取得完整论文。**FULL TEXT UNAVAILABLE** 表示只取得书目/摘要，不能核验方法与结果。下列页码优先使用论文页码；arXiv HTML 用章节、表号定位。仓库“已检查”仅指实际打开 README/目录，不代表运行代码或核对完整数据内容。

## 原文证据卡

<a id="a01"></a>

### A01 — Interactive Design

**书目与读取：FULLTEXT（作者预印本）。** Suhyung Jang; Ghang Lee. *Interactive Design by Integrating a Large Pre-Trained Language Model and Building Information Modeling*. arXiv:2306.14165v1，2023-06-25。[作者全文](https://arxiv.org/pdf/2306.14165v1)；实际读 Research Method、Case Study、Results and Discussion、Conclusion，PDF pp.2–8，Tables 1–2。正式条目属于 *Computing in Civil Engineering 2023*，pp.291–299，[ASCE 条目](https://ascelibrary.org/doi/10.1061/9780784485231.035)于 2024 年上线；正式全文未取得。预印本中间模块名为 GAIA，不能直接套用后续 NADIA 版本的所有细节。

**原文证据。** 输入已有 Revit 模型与细化要求；BIM2XML 用 C# 抽取任务相关属性/拓扑，GPT 修改 XML，XML2BIM 写回。论文已明确以 IFC STEP 的 token 负担解释选择性 XML；实验仍有人工复制提示/输出。单一 Villa Savoye 案例含 48 面墙、五类细化标签，比较 GPT-3/3.5/4，每个提示预测五次，以众数评价；Table 1 中 GPT-4 accuracy=0.83、F1=0.62。作者承认单案例及稀少类别限制；不能把墙分类准确率当整栋建模成功率。原文未给出已核实的公开代码/评测数据仓库。

**本次判断。** 紧凑任务表示、属性选择和确定性 BIM 重建已有先例，且节省上下文的动机早于本项目。可研究的差异必须落在 IFC 实体/关系的具体执行语义、编译前可判定约束和受控成本收益上；“XML 换成另一种 JSON/DSL”本身不足以建立方法贡献。

<a id="a02"></a>

### A02 — BIM Copilot

**书目与读取：FULLTEXT。** Changyu Du; Stavros Nousias; André Borrmann. *Towards a copilot in BIM authoring tool using a large language model-based agent for intelligent human-machine interaction*. EG-ICE 2024，pp.403–412；arXiv:2406.16903。[作者全文](https://arxiv.org/pdf/2406.16903)；[机构会议书目](https://portal.fis.tum.de/en/publications/towards-a-copilot-in-bim-authoring-tool-using-a-large-language-mo/)。实际读 §§3–5、结论，PDF pp.2–10，Tables 1–2、Fig.6。

**原文证据。** 自然语言/Whisper 语音驱动 Python 调用 Vectorworks 封装工具；建楼工具包裹 Marionette 参数流程。知识包括工具说明和软件文档 RAG；1911 份 HTML 转 Markdown 后检索，返回前两项。解释器错误、对话变量及人工反馈进入记忆。建模验证是连续编辑与独立生成示例；另有 20 个问答题的 RAGAs 评价，faithfulness 99.5%，不能移作建模成功率。作者指出工具覆盖、选择幻觉与环境感知限制；§5 明确提倡简洁高层工具内封装工程逻辑。未核实本论文专属公开代码/实验数据；SDK 示例链接不等于论文实现开源。

**本次判断。** 高层执行接口、工具文档、领域逻辑和运行反馈的组合已有直接先例。text2IFC 应把通用 API 文档、工程常识、编译器特定约束分开消融，并检验同一编码模型在相同工具权限和预算下的收益；本研究的问答指标不能充当其生成能力基线。

<a id="a03"></a>

### A03 — Text2BIM（版本分开）

**书目与读取：FULLTEXT（arXiv v1、v2）；期刊定稿全文未取得。** Changyu Du; Sebastian Esser; Stavros Nousias; André Borrmann. *Text2BIM: Generating Building Models Using a Large Language Model-based Multi-Agent Framework*. [v1 全文](https://arxiv.org/html/2408.08054v1)，2024-08-15；[v2 全文](https://arxiv.org/html/2408.08054v2)，2025-07-11。[正式 DOI](https://doi.org/10.1061/JCCEE5.CPENG-6386) 对应 *Journal of Computing in Civil Engineering* 40(2), 04025142，2026；卷期经[作者机构报告](https://www.mdsi.tum.de/fileadmin/w00cet/gni/pdf/TUM_GNI_Report26_linkedPW_R.pdf)核对，不假定 v2 与定稿完全相同。实际读 v1 方法与 §5 实验；v2 §§2、4–6、8、10、工具/提示附录，Tables 2–7。

**原文证据。** 四代理处理需求增强、建筑方案、编程、审阅；文档化高层工具调用 Vectorworks，内层使用执行异常修码，外层把导出 IFC 的 Solibri 规则问题反馈给代理。v2 说明导出/保存仍有少量人工操作。v1 为 10 提示×3 模型×5 次，即按设计计算 150 次运行，391 份 IFC 包含中间输出；v2 为 25×3×3=225 次，534 份同样包含中间输出。两版模型组不同，不能合并分母。v2 评价 30 条检查、问题数、四位专家对 75 个模型的评价及 CodeBERTScore；例如 Table 4 的 prompt 7，Gemini 平均规则通过比例 0.9222，SD 0.1347，分母不是“成功运行数”。作者在 §8.3 记录重建导致重复冲突、删墙降低问题数却伤害结构完整性；范围限早期基本构件，非完整规范符合性。

**开放性。** [作者代码仓库](https://github.com/dcy0577/Text2BIM)的 README、目录和依赖说明已检查，包含工具代理、Web 面板及不同实验环境；需商业 BIM 软件。未运行；391/534 全部输出未逐一核对。论文 §10 说明部分数据/模型需向作者索取。

**本次判断。** 这是最近的创新碰撞：可执行 BIM 工具、压缩表示、领域检查反馈已共同存在。必须比较 IFC 编译器知识的增量，而不能把“工具+规则+自修复”整体称首创。优化目标还应同时约束需求保留与模型完整性，避免以少生成/删除构件换取更低错误数；定预算的每次最终成功成本应包含失败与修订调用。

<a id="a04"></a>

### A04 — BIMgent

**书目与读取：FULLTEXT（v2）。** Zihan Deng; Changyu Du; Stavros Nousias; André Borrmann. *BIMgent: Towards Autonomous Building Modeling via Computer-use Agents*. arXiv:2506.07217v2，2025-06-30；ICML 2025 Workshop on Computer Use Agents，以[作者书目](https://arxiv.org/abs/2506.07217)的 workshop 说明为准，不标成 ICML 主会论文。[全文](https://arxiv.org/html/2506.07217v2)；实际读 §§3–6、Table 1 及误差/消融分析。

**原文证据。** 文本或平面图经过方案/分割与层级规划，通过 GUI 在 Vectorworks 建模；软件文档检索提供操作知识，截图、界面定位和监督代理反馈支持执行。混合系统使用多个模型，包含动作批处理。25 项任务分五组，每组五项；总体完成 8/25=32%，两种通用代理基线均为 0%。论文另统计两千余动作及构件子任务；这些不是独立建筑样本。作者指出操作效率、跨软件及评价规模限制；Table 1 的 opening 成功率 95.12% 与 §5.1 的 92.68% 不一致。已检查[作者仓库](https://github.com/ZihanDDD/BIMgent) README/目录，可见 benchmark 与 prompts；未运行或下载基准资产。

**本次判断。** 该文证明专门规划和软件知识对 GUI 工作流有价值，但混合模型与基线模型不同，32% 对 0% 不能单独归因为某一知识模块。与 text2IFC 的主要差异是 GUI 操作而非 IFC 编译接口；仍应保留为完整任务与动作级评价分层的对照，而非只比较最终视觉效果。

<a id="a05"></a>

### A05 — Trestle-bridge 多代理建模

**书目与读取：FULLTEXT（正式全文）。** Fuju Wu; Jianwen Huang; Guanran Luo; Jingqi Gao; Qingqiang Wu. *Large language model driven BIM collaborative automatic trestle-bridge modeling technology*. *Journal of Engineering and Applied Science* 73, 272，2026。[出版商全文](https://link.springer.com/article/10.1186/s44147-026-01130-3)；[PDF](https://link.springer.com/content/pdf/10.1186/s44147-026-01130-3.pdf)。实际读三个代理的方法、输入与反馈、实验/失败模式/结论、Data availability；PDF pp.28–34 的 Tables 7–11。

**原文证据。** 文本及平面/纵断/地质表经参数合同校验、默认补全、几何基准与布置计划，生成 Revit 函数调用并局部纠错；工程规则与族库提供知识。200 案例含 50 实际与 150 模板模拟，各重复三次；比较启发式工程规则 HE、规则脚本 ROS、单代理 LLM。Table 9 中多代理 API 成功率 95.1%、规则符合率 92.4%，单代理分别 86.4%、82.6%；平均用时 15 对 13 分钟。Table 10 去工程规则后符合率为 55.3%；77 案例触发纠错，65 成功。作者讨论缺失族、文件不一致等拒绝/人工处理条件。数据声明为按要求索取；未核实公开代码仓库。

**本次判断。** 此文已明确用参数化几何基准降低密集坐标带来的 token 与时间负担，且有校验合同、工程知识、确定性执行、反馈及工程规则消融，碰撞程度高。HE 不能随意译成“人工专家基线”。目前结果也不是定 token 预算比较，工程符合率不等于 IFC 语义/结构或全面力学验算通过；本项目应提出更具体、可区分的编译器约束知识表示与代价证据。

<a id="a06"></a>

### A06 — AutoBIM

**书目与读取：FULLTEXT（正式全文）。** Fei Huang; Dapeng Mei; Canwen Yang; Chuanhai Su; Runping Ma. *Knowledge-driven automated prefabricated bridge modeling from natural language using LLM and RAG*. *Scientific Reports* 16, 23838，2026。[出版商全文](https://www.nature.com/articles/s41598-026-53765-0)；[PDF](https://www.nature.com/articles/s41598-026-53765-0.pdf)。实际读 Methodology、实验设置、Results、Limitations、Outlook、Data availability；PDF pp.10–18、Tables 1–6。

**原文证据。** GLM-4-9B、M3E-base 检索人工核验的标准图集知识，结构化提示抽参数，Rhino/Grasshopper 生成装配并可导出 `.3dm` 与 `.ifc`。核心实验是一座广州标准预制小箱梁桥及 A/B 两种指令，200+ 是参考参数而非案例数。基线含纯 LLM、关键词检索、两位工程师；Table 1 参数准确率为 100% 对纯 LLM 44.5%，用时约 210 秒对人工四小时；Table 5 去 RAG/结构提示降为 54.8%/77.6%。作者承认标准体系、知识库及规模限制；提及额外鲁棒性测试但未明确其样本总量。数据按要求索取，无已核实公开代码。

**本次判断。** 不能写成“不输出 IFC”，也不能把图集内参数匹配解读为泛化建筑设计。表中纯 LLM 即使参数错误仍记 100% task success，说明该指标与工程正确性应分开。人工知识整理成本、同图集的知识与参考答案来源、未报告的重试/预算均需控制；运行耗时不能替代 token 节约。交互反馈在 Outlook 中仍属后续工作，不能仅凭“闭环”措辞推定已有持续执行修复。

<a id="a07"></a>

### A07 — Early-Stage Building Layout Planning

**书目与读取：FULL TEXT UNAVAILABLE。** Haolan Zhang; Ruichuan Zhang. *A Multiagent Large Language Model–Based System for Early-Stage Building Layout Planning*. *Journal of Computing in Civil Engineering* 40(6)，2026；[原始出版商条目](https://ascelibrary.com/doi/10.1061/JCCEE5.CPENG-7723)显示 2026-08-07 在线发表，不能因卷期对应较晚月份断言尚未发表。取得的是书目和摘要，未读到完整 Methods、Results 或表格。

**可用范围与获取记录。** 摘要描述需求解释、多角色规划、气泡图执行、规则/LLM 评价及导演模块，并提到多模态 RAG、扩散式布局和 Tell2Design 对比。这些只用于标识研究对象；实验大小、划分、指标定义、结果及作者局限均未核验，不填推测值。已尝试 DOI/ASCE 页、完整标题与两位作者的 PDF/机构仓储/arXiv 路线；原页访问受限，检索到的索取全文页面不能补足证据。未核实论文专属代码或数据链接。

**本次判断。** 多代理布局规划应保留在矩阵里，但不能根据摘要给它赋予原生 IFC、可执行 BIM 关系或预算控制能力，也不能据未取得全文推断它缺少这些机制。它可能与高层空间规划竞争；与 IFC 编译接口的精确重合需要全文后续核实。相关作者的其他可读论文和综述转述不能替代本篇证据。

<a id="a08"></a>

### A08 — AI BIM Coordinator

**书目与读取：PARTIAL；完整全文未取得。** Yaxian Dong; Zijun Zhan; Yuqing Hu; Daniel Mawunyo Doe; Zhu Han. *AI BIM coordinator for non-expert interaction in building design using LLM-driven multi-agent systems*. *Automation in Construction* 180, 106563，2025。[原始出版商预览](https://www.sciencedirect.com/science/article/abs/pii/S092658052500603X)；[机构书目](https://pure.psu.edu/en/publications/ai-bim-coordinator-for-non-expert-interaction-in-building-design-/)。实际取得 Highlights、Introduction 与摘要层面的系统描述，未取得完整方法、实验表及局限。

**可用范围与获取记录。** 原始预览将系统置于 AutoGen/Revit，列出 assistant、checker、sender、executor、terminator 五类代理，涉及自然语言、代码执行、视图/日志和语义几何拓扑知识。不能据此补写实验 N、模型配置、通过率或知识构建细节。尝试 DOI/出版商、作者机构及标题 PDF/arXiv 搜索，未取得作者全文或已核实代码/数据。检索到同作者的 [AHFE 2024 前作](https://openaccess-api.cms-conferences.org/articles/download/978-1-964867-35-9_188)，但其执行/准确率数字不能移植到这篇 2025 年论文。

**本次判断。** 多代理工具执行和 BIM 任务知识至少在作者公开的系统定位中已经出现，因此应作为近邻保留，不能宣称此前只有通用聊天。其是否已有编译器特定的约束供给、怎样评价修正保留性和成本，均保持未知；未知不是本项目创新成立的证据。

<a id="a09"></a>

### A09 — Worksite Trailers

**书目与读取：FULLTEXT（正式会议全文）。** Pan Chao-Hsu; Li Ren-Jie; Tsai Liang-Ting; Yang Cheng-Hsuan; Tsai Meng-Han（沿用官方作者排列）。*An LLM-Integrated BIM Workflow for Rapid Early-Stage Layout Generation of Worksite Trailers*. ISARC 2026，pp.2481–2487，DOI 10.22260/ISARC2026/0317。[官方书目](https://www.iaarc.org/publications/2026_proceedings_of_the_43rd_isarc_singapore/an_llm_integrated_bim_workflow_for_rapid_early_stage_layout_generation_of_worksite_trailers.html)；[全文](https://www.iaarc.org/publications/fulltext/ISARC2026_1215.pdf)。实际读 §§2–5，PDF pp.2–7 的流程、原型、演示、讨论与结论。

**原文证据。** GPT-4o-mini 把语言和尺寸约束转换成统一 JSON 数据层，经 Revit API 生成边界、房间、隔墙、洞口及标签。历史案例按属性匹配检索、人工选择并复用空间单元；模型视图支持用户迭代。文章展示功能原型和示例，§4 明确未作定量时间效率对比；没有可用于统计的任务/案例库 N、控制基线或正式成功率。作者限制包括正交模块、小型案例覆盖及尚未集成的规范/下游工程检验。原文未给出已核实的公开代码或案例数据包。

**本次判断。** 任务提示、结构化参数、案例知识和 BIM 执行已经组合。适合用于 Demo 定位及实现路线比较，却不能作为性能优势的量化依据。text2IFC 若主张知识收益，需区分“检索复用一个旧方案”与“依据编译约束生成新方案”，并明确最终 IFC 的语义验证及未见任务划分。

<a id="a10"></a>

### A10 — BIMVLM

**书目与读取：PARTIAL；完整全文未取得。** Hao Zhang; Junwei Yan; Quan Liu; Jun Yang; Yiwen Su; Zhewen Li; Shujie Chen. *BIMVLM: A vision-language model for iterative generation of component BIM models*. *Expert Systems with Applications* 315, 131765，2026。[原始出版商页面](https://www.sciencedirect.com/science/article/pii/S0957417426006780)，DOI 10.1016/j.eswa.2026.131765。实际取得出版商可检索的 Method、数据/评价与 Conclusion 片段，未读完整表格及局限段落。

**可用范围与获取记录。** 原始片段描述 LLaVA/LoRA、自然语言与多视图输入、建模动作序列、提示转可执行代码及迭代优化；数据准备涉及 DeepCAD、Text-to-CAD 和将 CAD 序列转换为文字说明。完整训练/测试数量、隔离方式、基线、量化结果及修订准则均未核验。已尝试 DOI/ScienceDirect、作者标题 PDF、机构/arXiv/GitHub 路线，未取得作者全文或已确认的专属代码/数据。外部 DeepCAD 的存在不等于本论文处理后的评测集已公开。

**本次判断。** 研究粒度是构件；不能由“BIM models”名称推定具有整栋空间关系或 IFC 实体语义，也不能直接当成整栋生成的同任务基线。精确的数据监督和可执行动作定义仍待全文核验。其几何与多模态能力可与本项目互补，但不是免除同任务、同预算编码基线的理由。

<a id="a11"></a>

### A11 — NADIA 外墙细化

**书目与读取：PARTIAL；完整全文未取得。** Suhyung Jang; Ghang Lee; Jiseok Oh; Junghun Lee; Bonsang Koo. *Automated detailing of exterior walls using NADIA: Natural-language-based architectural detailing through interaction with AI*. *Advanced Engineering Informatics* 61, 102532，2024。[原始出版商预览](https://www.sciencedirect.com/science/article/pii/S1474034624001800)；[机构书目](https://pure.seoultech.ac.kr/en/publications/automated-detailing-of-exterior-walls-using-nadia-natural-languag/)。实际取得 Introduction、Validation、Results/Discussion 与 Conclusion 的部分预览，未读完整实验表和局限。

**可用范围与获取记录。** 预览确认以外墙层次细化连接 LLM 与 BIM，将要求/材料/厚度及隐含性能知识转换为建模内容，区分 assistant 与 consultant 功能。摘要中的 240/1920 与 83.33%/98.54% 未经完整方法和分母定义复核，故不采作本卡的已核验结果。尝试出版商、机构仓储及[作者 SSRN 条目](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4674577)（相关 DOI 10.2139/ssrn.4674577），未成功取得全文；未核实代码或原始实验记录。A12 对前作的描述只能验证 A12 的比较口径，不能替代 A11 全文。

**本次判断。** 按细化任务组织知识、把规范要求映射成可执行参数已有先例；应避免把早期 GAIA、此篇 NADIA 与 NADIA-S 的样本或结果混写。是否可支持本项目的特定约束知识设计，需要核清其提示、匹配、执行与验证职责；现有读取范围不足以评价其完整泛化或 token 成本。

<a id="a12"></a>

### A12 — Generalized LLM-Augmented BIM Framework / NADIA-S

**书目与读取：FULLTEXT（正式会议作者全文）。** Ghang Lee; Suhyung Jang; Seokho Hyun. *A Generalized LLM-Augmented BIM Framework: Application to a Speech-to-BIM system*. CIB W78 2024，Marrakesh；arXiv:2409.18345。[CIB/Scix 全文](https://eres.scix.net/pdfs/w78-2024-paper_155.pdf)。实际读 §§3–5，PDF pp.3–7，Figs.1、3 与实验结果段。

**原文证据。** 框架为解释、补全、匹配、结构化、执行、检查六步：术语匹配、单位/JSON 参数及预定义 Revit 函数连接语言与模型。NADIA-S 原型使用 Revit 2024、Whisper、微调 GPT-3.5 与 GPT-4。八类既有墙细化提示各 30 次，共 240 次；材料与最小结构厚度检查后反复 Execute 直至通过，最终 100%，前作比较数为 92.50%/91.66%。作者称原型仍初步，复杂规则/RAG 为扩展方向；未核实公开代码或逐次日志，原文未报告该循环的固定重试或 token 上限。

**本次判断。** 这是“结构化可执行接口+术语/任务知识+规则反馈”的直接先例。100% 是允许反复执行后的条件结果，不能当作单次成功或定预算可靠性；检查器变化也需同口径重评。text2IFC 应把首次生成、每轮修订、最终验证和累计 token 分开记录，并报告预算耗尽的失败，才能建立相对于该路径的可比较进步。

<a id="a13"></a>

### A13 — BIM–LLM Integration in AECO Workflows（综述）

**书目与读取：PARTIAL；完整全文未取得。** Ingeon Park; Yije Kim; Kyoungmin Kim; Sangyoon Chin. *BIM–LLM integration in AECO workflows: Applications, validation, and future directions*. *Automation in Construction* 187, 106905，2026。[原始出版商预览](https://www.sciencedirect.com/science/article/abs/pii/S0926580526001469)；[作者机构书目](https://pure.skku.edu/en/publications/bim-llm-integration-in-aeco-workflows-applications-validation-and/)。实际取得 Methodology 与 Results 的章节预览及摘要，未取得完整检索/编码表。

**可用范围与获取记录。** 预览列出 PRISMA 筛选、文献计量及应用分析，结果按应用、生命周期、技术/工业验证和 LLM/BIM 数据分类。摘要称纳入 61 篇，但数据库查询式、检索截止日、排除标准、验证比例的编码规则及分母未核验；不能把 70.5%/44.3% 移作已复核统计。已试 DOI/出版商、[SKKU 仓储](https://scholarx.skku.edu/item/334375a8-db06-42a8-9cfd-be40d42c3af0)、作者实验室及标题 PDF 路线，仍为书目/预览。未核实开放提取表或代码。

**本次判断。** 该综述可以扩展文献索引，但不能替代 A01–A12 的原始系统证据，也不能以“综述未提到”证明本项目首创。实际检索截止范围尚未知，全文缺失应作为信息缺口保留。技术验证、真实工业验证与固定预算下生成能力是不同问题，需在本项目自己的实验设计中分别定义。

<a id="a14"></a>

### A14 — Bridging BIM and NLP（系统综述）

**书目与读取：FULLTEXT（正式会议全文）。** Tessa Marie Oberhoff; Julian Cloos; Sven Mackenbach; Katharina Klemt-Albert. *Bridging Building Information Modelling and Natural Language Processing: A Systematic Review on Current Applications and Limitations*. ISARC 2026，pp.1888–1895，DOI 10.22260/ISARC2026/0241。[全文](https://www.iaarc.org/publications/fulltext/ISARC2026_1081.pdf)。实际读 §3 方法、§4 分类、§§5–6 讨论与结论，Tables 1–3；PDF p.1890 的 Fig.2 筛选图另经本地渲染目视核对。

**原文证据。** Fink 方法；六库为 Compendex、IEEE Xplore、Scopus、Taylor & Francis、Wiley、Web of Science；BIM 同义词与 NLP 同义词组合，覆盖截止 2025 年 5 月。430 条初始记录最终纳入 92 篇，含 78 研究、11 综述、3 案例；任务分析使用 85 篇，NLP 类型分析排除综述后为 81 篇且允许多标签，Modify 为 12/81。作者承认时间范围及解释性分类限制，讨论概率语言与结构化 BIM 的衔接、规则验证和人工 QA。未核实公开的逐篇编码数据文件；综述不提供可复现生成基准。

**本次判断。** 不能用 2026 年出版日期推断它覆盖 2026 年系统，亦不能以 92 作所有分类表的共同分母。它提出 schema-aware 模型和规则结合的方向，说明“语言与严格结构桥接”已是公开议题；这不是某个具体 IFC 实现或预算收益的原始证据。text2IFC 的贡献仍须来自具体机制、可判定边界与受控比较。

## 可直接并入总矩阵的短行

下表是上述证据卡的索引，不增加独立证据。数字跨论文不可直接排名；任务、指标、模型与停止条件不同。

| ID / 原文等级 | 任务与输出 | 接口、知识、反馈 | 实验单位与已核验结果 | 对候选创新的影响 |
| --- | --- | --- | --- | --- |
| [A01](#a01) FULLTEXT 预印本 | 已有模型墙细化；Revit | 选择性 XML，任务属性，C# 写回 | 1 模型/48 墙；GPT-4 accuracy 0.83 | 紧凑表示及 token 动机已有先例 |
| [A02](#a02) FULLTEXT | 建模/编辑与软件问答；Vectorworks | 高层工具、文档 RAG、解释器/人工反馈 | 建模演示；20 QA 的 faithfulness 99.5% | 工具内封装工程知识并非新概念 |
| [A03](#a03) FULLTEXT v1/v2 | 早期建筑；原生 BIM 与检查用 IFC | 四代理、工具文档、Solibri 规则反馈 | 设计计数 v1 150 运行/391 输出；v2 225/534；30 规则比例 | 最接近；须隔离编译器知识的预算收益 |
| [A04](#a04) FULLTEXT v2 | 文本/图到 GUI 建模 | 多模型规划、文档检索、截图监督 | 25 任务；完整成功 8/25 | 软件知识有效性对照；不是直接 IFC API |
| [A05](#a05) FULLTEXT | 栈桥 Revit 建模 | 参数合同、工程基准、函数计划/纠错 | 200 案例各三次；API 95.1% | 合同、工程知识与 token 动机接近 |
| [A06](#a06) FULLTEXT | 标准桥参数建模；含 IFC 导出 | 图集 RAG、结构提示、参数化建模 | 1 核心桥例 A/B 指令；200+ 参数；准确率 100% | 不得声称已有工作不能输出 IFC |
| [A07](#a07) UNAVAILABLE | 摘要称布局规划/扩散输出 | 摘要称 RAG/多代理/评价 | 全文 N、指标、结果未知 | 近邻待核；不能据未知证明差异 |
| [A08](#a08) PARTIAL | BIM 非专家交互；Revit | 预览称 AutoGen/知识技能/执行检查 | 未核验 | 不移用 AHFE 前作数字 |
| [A09](#a09) FULLTEXT | 临建集装箱初步布局；Revit | JSON、案例检索复用、人工迭代 | 原型示例；无定量时间对比 | 接口+任务知识已组合，适合 Demo 对照 |
| [A10](#a10) PARTIAL | 构件建模；动作/代码 | 预览称 VLM 微调、多视图与迭代 | 未核验 | 不把 CAD/构件提升为整栋 IFC 证据 |
| [A11](#a11) PARTIAL | 外墙细化；BIM | 预览称要求/知识到建模参数 | 完整分母与结果表未核验 | 不混写 GAIA、NADIA、NADIA-S |
| [A12](#a12) FULLTEXT | 语音到墙细化；Revit | 六步结构化/匹配/执行/检查 | 8×30 次；循环到通过后 100% | 无界重试后的通过率不是预算内可靠性 |
| [A13](#a13) PARTIAL 综述 | AECO 中 BIM/LLM 研究分类 | PRISMA/应用/验证预览 | 摘要称 61 篇；检索和编码未核验 | 只作索引，不代替系统原文 |
| [A14](#a14) FULLTEXT 综述 | BIM/NLP 应用分类 | 六库 Fink 检索，截止 2025-05 | 92 纳入；NLP 多标签分母 81 | 年份/分母校正；不覆盖 2026 系统 |

## 关键更正与研究边界

- **表示与输出要分层。** LLM 生成 XML、JSON、Python 或动作序列，不意味着最终产物不含 BIM/IFC；反过来，导出 IFC 也不证明已验证全部实体、关系、几何或工程约束。A03、A06 必须保留这一层次。
- **实验分母要分层。** Text2BIM 的中间 IFC、BIMgent 的动作、AutoBIM 的参数、墙细化任务的重复预测和独立建筑案例，均不是同一种样本；A14 不同表也采用不同纳入分母。
- **成功率不能脱离停止条件。** NADIA-S 的执行到通过、Text2BIM 的规则通过比例、BIMgent 的整任务完成率和 AutoBIM 的参数正确率回答不同问题。应保留失败及重试，报告固定预算内完整且满足需求的输出。
- **广义创新已有碰撞。** A01/A02/A03/A05/A06/A09/A12 足以否定“此前没有紧凑可执行接口或建模任务知识”的宽泛前提。A05 与 A01 还明确涉及 token 负担；成本动机本身也不是新颖性。
- **仍可检验的命题应具体。** 对相同编码模型、工具权限、任务和预算，拆分通用 API 文档、工程/布局知识、编译器约束知识，检验各自增量；同步检查 IFC 语义与关系、需求保留、几何、累计成本及预算耗尽。现有证据尚不能判定这一具体命题已被解决，也不能判定本项目已经解决。
- **付费缺口保留。** 9 个条目取得指定版本全文、4 个只有原始正文预览、1 个没有全文；不是 14 篇全部完成全文复核。A03 正式定稿与 arXiv 的一致性未核实。没有借助综述、前作或机构摘要填补结果。

本轮仅记录研究证据与比较边界；没有复现论文、执行作者代码、调用真实 LLM、下载评测数据或改变本项目数据准入。原始论文不复制入仓库。
