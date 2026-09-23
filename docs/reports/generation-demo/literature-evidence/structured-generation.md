# 结构化生成、CAD 与模型驱动工程：逐篇正文证据

核查日期：2026-09-15。范围为分工清单 C01–C16；外部 v2.1 调查稿只作线索。`FULL` 表示已取得原始全文并阅读列出的主要方法、实验和局限，不表示复现了结果或逐行审计代码；`PARTIAL` 表示仅有摘要、程序页或部分正文。结果均为作者报告。数据及代码只检查公开入口，没有下载数据集或运行 Provider。页码优先使用 PDF 自身页码。

本轮16篇均有记录：FULL 12篇（C01–C06、C11–C16），PARTIAL 4篇（C07–C10）。C16是二级综述，不能计作生成系统实验。

<a id="c01"></a>
## C01 — SceneCraft

**身份与阅读：FULL。** Ziniu Hu 等，*SceneCraft: An LLM Agent for Synthesizing 3D Scenes as Blender Code*，ICML 2024，PMLR 235:19252–19282。已读[正式全文](https://raw.githubusercontent.com/mlresearch/v235/main/assets/hu24g/hu24g.pdf) §2–3、表1–3、§5，以及附录 C/E/F/G 的关系函数、成本、评估示例与提示。

- **机制与知识：** GPT-4V 将文本拆成子场景，检索现成资产，构建资产—关系二部图，再生成数值约束函数交给求解器；渲染后由视觉反馈修订函数/关系。外层从多例修订归纳可复用空间技能库，无参数微调。这已覆盖分解、结构中间表示、编码、反馈和知识复用的组合。
- **实验证据：** 40 个手写合成查询，20 个用于学习技能库、20 个评估；改造的 BlenderGPT 也得到视觉反馈。表1约束分数 88.9 对 5.6；移除学习库为64.5，再移除内循环为26.1，属于递进消融。另有 Sintel 场景/视频实验和22份人工响应。附录 E 报告平均约6k、最高约15k token/场景，不是同任务 IFC 成本比较。
- **边界与可用性：** 作者指出超过20个资产的子问题效果变差，扩展仍依赖分解；资产本身是检索输入。附录公开函数与提示，[论文页](https://proceedings.mlr.press/v235/hu24g.html)未给出完整独立实现入口。**本次判断：** 强知识库/求解器基线；软评分最大化与可视化满意度不能替代 IFC 关系验收、固定状态保全或写权限证明。

<a id="c02"></a>
## C02 — Text2CAD

**身份与阅读：FULL。** Mohammad Sadil Khan 等，*Text2CAD: Generating Sequential CAD Designs from Beginner-to-Expert Level Text Prompts*，NeurIPS 2024，37:7552–7579。已读[正式全文](https://proceedings.neurips.cc/paper_files/paper/2024/file/0e5b96f97c1813bb75f6c28532c2ecc7-Paper-Conference.pdf) §3–6、表1–2、补充§9/12/13。

- **机制与知识：** LLaVA-NeXT/Mistral 为 DeepCAD 标注四档文本；BERT 编码、领域适配层和8层自回归解码器输出量化的 sketch/extrude 参数序列，形成可编辑 CAD 历史。领域知识主要进入监督语料和表示设计；并非通用 Coding Agent 加检索、执行后自修复。
- **实验证据：** 约170k模型、660k文本；约150k训练模型，测试/验证各约8k。表1只用最详尽的 L3 提示：无效输出率0.93%，文本适配 DeepCAD为10%；中位 Chamfer×1000 为0.37对32.82。四档各1000例视觉比较、各100例人工比较；L1的VLM偏好并未胜过基线，不能把L3结果推广到所有自然文本。
- **边界与可用性：** 作者指出数值分词、透视引起的错误标注及矩形/圆柱数据偏置；补充区分“不能生成”与更常见的“生成了但不符合描述”。已查[作者 README](https://github.com/SadilKhan/Text2CAD)，列有训练/推理/评估代码、[数据和权重](https://huggingface.co/datasets/SadilKhan/Text2CAD)。**本次判断：** 可编辑表示及领域训练已有先例，但不是整栋 IFC 或知识供给方式的公平直接比较；低无效率不等于需求完整率。

<a id="c03"></a>
## C03 — CADCodeVerify

**身份与阅读：FULL。** Kamel Alrashedy 等，正式题名 *Generating CAD Code with Vision-Language Models for 3D Designs*，ICLR 2025；CADCodeVerify是方法名。已读[arXiv v2全文](https://arxiv.org/pdf/2410.05340v2) §3–7、表1–4、附录B.3/C/D，并核对[会议版](https://proceedings.iclr.cc/paper_files/paper/2025/file/81a934cd364e18ea6fdeaf57a93c17d4-Paper-Conference.pdf)身份。

- **机制与知识：** 文本生成 CadQuery，执行并用报错修代码；随后从需求产生2–5个问题，以四视图回答 Yes/No/Unclear，针对未满足项修订，实验做两轮。比较直接视觉反馈3D-Premise及读取GT几何的求解器上界；后者明确不是无GT生产基线。
- **实验证据：** CADPrompt含200个专家标注对象。表2 GPT-4 few-shot：相对3D-Premise，点云距离0.137→0.127，编译率91%→96.5%，即**5.5个百分点**；不能沿摘要页写5.0%。100例消融、50例人工反馈/问答检查；问答正确率仅64.6%/68.2%。附录模型标识有粗糙之处，不能据摘要的Gemini名称推定精确API版本。
- **边界与可用性：** 作者承认点云距离会漏掉腿与桌面脱离等逻辑缺陷，初始提示也影响结果。已查[作者仓库](https://github.com/Kamel773/CAD_Code_Generation)的CADPrompt说明：文本、专家代码、STL/OBJ/命令JSON。**本次判断：** 需求分解驱动的产物自验证已有明确先例；其视觉判定不是确定性关系验证，也没有证明全局保全。比较 IFC Coding Agent 时应包含执行反馈和此类视觉反馈版本。

<a id="c04"></a>
## C04 — LLM4CAD

**身份与阅读：FULL（作者稿）。** Xingang Li、Yuewan Sun、Zhenghui Sha，*LLM4CAD: Multimodal Large Language Models for Three-Dimensional Computer-Aided Design Generation*，JCISE 2025，[DOI](https://doi.org/10.1115/1.4067085)。已读[作者实验室全文](https://sidilab.net/wp-content/uploads/2025/01/llm4cad_jcise_preprint.pdf) §3–5.4、图7–9、表2/4及数据附录；图7和表2另做PDF图像核对。

- **机制与知识：** GPT-4/GPT-4V零样本生成 CadQuery 2.3.1代码并输出STL，错误反馈连同历史对话最多修3次。输入为含尺寸文本，或加渲染图/草图；没有检索知识库。构造五类机械零件各1000个参数模型，众包清洗后3331条文本；不能把模型总数直接当各实验条件的独立样本分母。
- **实验证据：** 文本条件下GPT-4解析率0.517→0.711，GPT-4V为0.525→0.710。§4.2同时报告总体IoU下降，且文本平均优于多模态；复杂零件有不同趋势。IoU仅在解析成功后计算，调试改变入选样本集合，**不能由此直接推断同一对象经调试变差**。
- **边界与可用性：** 作者限于五类零件、零样本和合成单视图；尺寸只出现在文本中，影响模态比较。公开作者稿已访问，稿内未找到可确认的代码/数据仓库，不把后续 *LLM4CAD Fine-Tuned* 的资源混入本篇。**本次判断：** 这是“编码接口能做什么、何种信息有效”的直接实验先例；需同时报告可执行率和需求/几何质量，并固定成功条件与成本分母。

<a id="c05"></a>
## C05 — Building-Diffusion

**身份与阅读：FULL。** Mohammed El Amine Sehaba 等，*Building-Diffusion: Graph Discrete Diffusion Model For Architectural Volumetric Design Generation*，CVPRW 2026，CV4AEC。已读[CVF正式全文](https://openaccess.thecvf.com/content/CVPR2026W/CV4AEC/papers/Sehaba_Building-Diffusion_Graph_Discrete_Diffusion_Model_For_Architectural_Volumetric_Design_Generation_CVPRW_2026_paper.pdf) §3–6、算法1–2、表1–3、用户研究。

- **机制与知识：** program graph编码房间功能、楼层、面积、邻接；自监督编码器提供条件，离散扩散恢复七类voxel标签。架构师初始化voxel图，邻接固定，只扰动节点标签。领域知识来自图表示、训练数据和楼层位置编码，无LLM编码或RAG。
- **实验证据：** 使用120k合成、1–11层的Building-GAN语料；正文未明确测试集数量。表1五次采样：GIN的FAR误差0.1966优于GAN的0.2305，但TPR和FGW更差（0.9448/0.3763 对0.9800/0.2386）。表2多样本按**相对GT的FGW**择优；20位建筑师各比较30对，偏好本法对GAN为41.5%对31%。不能写全面优胜或无GT选样收益。
- **边界与可用性：** 作者承认单次采样波动、部分配置过拟合和指标取舍。已查[作者仓库](https://github.com/Sehaba95/building_diffusion)：仅README/LICENSE且仍标“code release coming soon”，不能记为代码已发布。**本次判断：** 固定voxel邻接不等于保持已生成IFC实体/宿主/containment关系；它是拓扑条件生成的相邻先例，非whole-IFC提交隔离实证。

<a id="c06"></a>
## C06 — MANSION

**身份与阅读：FULL。** Lirong Che 等，*MANSION: Multi-floor lANguage-to-3D Scene generatIOn for loNg-horizon tasks*，CVPR 2026。已读[CVF全文](https://openaccess.thecvf.com/content/CVPR2026/papers/Che_MANSION_Multi-floor_lANguage-to-3D_Scene_generatIOn_for_loNg-horizon_tasks_CVPR_2026_paper.pdf) §3–4、表2–4及[补充材料](https://openaccess.thecvf.com/content/CVPR2026/supplemental/Che_MANSION_Multi-floor_lANguage-to-3D_CVPR_2026_supplemental.pdf) C.2算法1–3、G/H、提示模板。

- **机制与知识：** 多Agent将整栋程序分为楼层关系图，再由MLLM给局部切分种子；求解器先过滤破坏已实现拓扑的候选，再按面积等能量择优。物体用anchor/member关系组及matrix/paired原语压缩重复约束，按约束优先级构造并检查碰撞、可达性；无解时会缩小阵列或丢弃对象。输出为AI2-THOR交互场景，数据集含1000栋、2–10层、逾万房间。
- **实验证据：** ResPlan的1000例零样本测试，Gemini-2.5-Pro下本法micro-IoU为63.56，对ChatHouseDiffusion（CHD）29.36；但T2D上本法69.98低于CHD的76.34。MA条件使用GT面积/质心，不能视为纯文本性能。放置另与LayoutGPT/Holodeck比较，四类房间各10次；52人评估。可达性100%应结合对象覆盖率阅读。
- **边界与可用性：** 作者承认重复场景多样性不足；跨楼层交互通过卸载/加载楼层完成。已查[代码README](https://github.com/AgibotGeneral/MANSION)和其[MansionWorld链接](https://huggingface.co/datasets/superbigsaw/MansionWorld)，未运行。**本次判断：** “关系分组＋确定性求解＋保留既成拓扑”已经明确出现，是高优先级近邻；尚不能替代IFC实体关系、交换文件、全流程token成本的验证。

<a id="c07"></a>
## C07 — LLM-Based Instance Model Generation via Code Synthesis

**身份与阅读：PARTIAL。** Javier Polo Gambín、José Antonio Hernández López、José Antonio Ruipérez-Valiente；MODELS 2026 Research Papers / FT，当前[官方节目页](https://conf.researchr.org/details/models-2026/models-2026-research-papers/16/LLM-Based-Instance-Model-Generation-via-Code-Synthesis)列入10月8日议程，尚未取得论文全文。实际阅读材料为完整官方摘要、[作者主页及论文列表](https://antolin1.github.io/)和[作者GitHub](https://github.com/Antolin1)。精确题名结合PDF、preprint、作者和代码检索仍未发现可访问正文。

- **摘要明确陈述：** 元模型编码为Pydantic类、良构约束编码为验证器；LLM生成构造实例模型的可执行代码，验证失败后反馈修正。作者称在两用例、三个LLM上与Refinery比较扩展性、一致性、多样性、真实性，程序循环可构造逾2000元素；随规模增大，多样性下降，真实性依赖领域。
- **尚未核实：** 两种元模型、三个模型的确切版本、用例/重复次数、约束满足率分母、验证失败是否计入、运行与token预算、Refinery配置及数据独立性。未找到可确认对应本篇的代码和数据；不能把“2000元素”记成2000独立测试例，也不能写一致性已全面胜过传统求解器。
- **本次判断：** 这是“让强编码模型调用承载领域知识的类型/API，而非直接吐原生文件”的高度直接先例。足以要求收紧宽泛表述；但摘要不足以判断是否实现编译器保证与剩余Agent义务的分离、关系依赖保留或提交隔离，不能据此确认或排除细分创新。

<a id="c08"></a>
## C08 — Well-Formed Executable Suggestions for Continuous Model-Driven Engineering

**身份与阅读：PARTIAL。** Bastien Sultan、Ludovic Apvrille，MODELS 2026 Research Papers / FT。已读[官方完整摘要](https://conf.researchr.org/details/models-2026/models-2026-research-papers/7/Well-Formed-Executable-Suggestions-for-Continuous-Model-Driven-Engineering)及[TTool-AI说明](https://ttool.telecom-paris.fr/ttoolai.html)、工具参考页；精确题名检索及作者出版入口未取得正文，作者旧出版URL返回404。没有可以列出的方法页、主实验表或论文限制节。

- **摘要明确陈述：** γμS以形式化mutation语言、MCP暴露的规则验证、外部验证工具和反馈循环生成可执行建议；另设LLM语义oracle评估建议相关性。实例化对象为SysML block和state-machine图，强调多视图一致性及不限于添加的编辑操作，TTool案例作为初步评估。
- **实现线索与缺口：** 工具页列出suggestion/mutation MCP入口；公开[ExecutableSuggestions合并请求550](https://gitlab.telecom-paris.fr/mbe-tools/TTool/-/merge_requests/550)提供代码存在的线索。它们不能代替本文的形式保证、实验配置或复现版本；模型、案例数量、基线、成功率、token和人工干预均未核实。也不能借用作者其他TTool论文的数字填补。
- **本次判断：** “通过受限变更语言和确定性检查保证良构，再用LLM判断语义”与当前方向直接相邻。必须比较保证究竟覆盖哪些不变量、失败怎么处理，以及跨视图依赖是否完整；“有MCP/可执行编辑/验证反馈”本身不宜作创新。全文未取得，保留为高优先级待核实碰撞项。

<a id="c09"></a>
## C09 — Software Model Slicing

**身份与阅读：PARTIAL。** Alisa Carla Welter、Benedict Bliem、Omer Iqbal、Sven Apel，*The impact of Software Model Slicing on Software Model Completion with Large Language Models*，MODELS 2026 Research Papers / FT。已读[官方摘要](https://conf.researchr.org/details/models-2026/models-2026-research-papers/15/The-impact-of-Software-Model-Slicing-on-Software-Model-Completion-with-Large-Language)及[作者出版列表](https://www.se.cs.uni-saarland.de/publications/lists/welter.html)：本篇列为to appear且无PDF链接。同列表C13/C15有全文，已另读；精确题名/作者全文检索与[se-sic仓库](https://github.com/se-sic)检查未找到本篇。

- **摘要明确陈述：** 用图表示给出任务无关、元模型无关的切片，实例化半径、模块化和LLM引导策略。作者称使用两个公开数据集的1000个真实模型、开源LLM，对照identity与random切片；半径和模块化改善结构/语义补全且降低token。
- **尚未核实：** 数据集名称、模型版本、移除/补全任务、单位和重复数、半径/模块定义、关系依赖闭包、选择器本身成本、总输入输出token、统计及失败分母。上述1000与效果均是摘要中的作者报告，不能填成正文已验证结果；未定位代码/数据工件。未取得作者限制节。
- **本次判断：** 它直接覆盖“选择较小模型上下文，同时降成本、提质量”的研究问题，是最应优先核对的方法碰撞。现阶段可比较的差异只能表述为待检验假设：先界定编译器保证之外的义务，再验证依赖组保留是否比通用切片更有效。不能因未拿到全文，就宣称此前没有研究关系或知识选择。

<a id="c10"></a>
## C10 — Agent-based generation of valid SysML v2 models

**身份与阅读：PARTIAL。** Eduardo Cibrián、Jose Olivert-Iserte、Juan Llorens、Jose María Álvarez-Rodríguez，*An agent-based approach for the automatic generation of valid SysMLv2 Models in industrial contexts*，Computers in Industry 172 (2025), 104350，[DOI](https://doi.org/10.1016/j.compind.2025.104350)。实际读到出版方摘要/亮点与大学开放稿首屏索引；未取得正文方法、实验表和限制节。

- **可访问材料陈述：** 自然语言生成SysML v2文本，结合领域示例检索和官方ANTLR语法校验，再迭代修正；作者报告20个提示实现100%语法有效。**这不是本次已核实的语义正确率或工业可靠性。** 模型精确版本、RAG库大小和构建、循环上限、基线与统计均留空；作者所称“数据按请求提供”也不等于公开数据集。
- **全文路线与阻塞：** 已尝试[出版方](https://www.sciencedirect.com/science/article/pii/S0166361525001150)、[大学永久入口](https://hdl.handle.net/10016/48940)、[大学开放稿API](https://e-archivo.uc3m.es/rest/api/core/bitstreams/44c9142f-1165-4fe6-8e0d-ebaddb6a489c/content)和bitstream下载入口。分别遇到403、网页解析失败、30/55秒下载超时；未获取可读完整文件，未确认公开代码。没有继续循环重试同一入口。
- **本次判断：** 是“知识检索＋语法验证＋Agent重试”的直接SysML先例，应纳入近邻而非遗漏。判断其与IFC编译义务分工的距离，需要语法以外的约束范围、全局关系检查及真实失败分母；当前证据不足以支撑更强比较，也不能把无法访问写成论文没有这些机制。

<a id="c11"></a>
## C11 — MCeT

**身份与阅读：FULL。** Khaled Ahmed 等，*MCeT: Behavioral Model Correctness Evaluation using Large Language Models*，MODELS 2025；已读[arXiv v2全文，2025-08-30](https://arxiv.org/pdf/2508.00630v2) §III–VII、表I–III。

- **机制与知识：** 对需求文本/PlantUML序列图分别做整体、图原子和需求原子检查，五次投票合并；MCeT-X用较高精度的需求原子判定交叉过滤其他检查。所谓高/低authority是LLM提示中证据优先级，不是对模型的写权限。它输出问题解释，非生成器或形式证明器。
- **实验证据：** FBench的28份需求含87变体，排除错误图种等后用76例；两个作者人工判问题，前20%双评κ=0.79。GPT-4o-mini表II：整体精确率0.58、已有人工问题召回34.1%；MCeT-A为0.72/68.1%，X为0.81/65.2%。X删除211假阳性的同时删158真阳性。其他三个模型只复测8图；表III mini总token/图为12k→80.5k，不能声称原子化节省总token。
- **边界与可用性：** 作者承认人工判定、8图外推和图种限制；16图前期分析来自同一评估语料，属开发性证据。[仓库](https://github.com/Huawei-TTE/MCeT)README可见提示、实现、Ferrari图与配置，未运行。**本次判断：** 应借鉴“语法通过后，仍逐项检查需求覆盖”，同时保留精确率/召回/成本三者；它不能证实确定性IFC关系保证。

<a id="c12"></a>
## C12 — Event-B Agent

**身份与阅读：FULL。** Hongshu Wang 等，*Event-B Agent: Towards LLM Agent for Formal Model Synthesis and Repair*，Proc. ACM Softw. Eng. 3/FSE, FSE211 (2026)，[DOI](https://doi.org/10.1145/3808218)。已读[arXiv v1全文](https://arxiv.org/pdf/2605.17475v1) §4–5、表2–6、§7–9（方法pp7–12、实验pp12–18、限制p20）。

- **机制与知识：** 先规划需求refinement及gluing invariants；JSON schema约束结构，编译器检查类型，再以ProB、SMT和定理证明反馈修复。七类proof-state规则指导LLM选择原子修复函数；每次模型改变重放全部proof。其保留对象是已形式化性质，不等于实体字节不可变。
- **实验证据：** 27系统、三复杂度各9；统一GPT-5 2025-08-07 medium，对照LLM+prover、Cursor（禁网页检索）和适配PAT-Agent。表3总体证明义务解除PDR/需求覆盖RC/满足RF为97.86/97.13/93.79%，Cursor为90.07/89.28/68.86%，并非整模型通过率。但refinement PDR仅92.56%；作者明确RC/RF依赖跨层保留假设，属于近似。表6均值74.45分钟、57.33调用、约165.8万token/系统。
- **边界与可用性：** 假设需求内部一致；标签格式由人工纠正；规则/函数库有限。已查[公开实现](https://github.com/HongshuW/EventB_Agent)包含两个基线适配、数据和分析目录，未复跑。**本次判断：** “编译器排除一类问题、Agent处理剩余义务、原子修改后重验”已有强近邻且有编码Agent对照。text2IFC需证明自己的义务筛选、关系上下文及预算优势，不能只换领域声称首次。

<a id="c13"></a>
## C13 — Software Model Evolution with Large Language Models / RaMc

**身份与阅读：FULL（含作者附录）。** Christof Tinnes、Alisa Welter、Sven Apel，*Software Model Evolution with Large Language Models: Experiments on Simulated, Public, and Industrial Datasets*，ICSE 2025，pp950–962。已读[24页作者全文](https://www.se.cs.uni-saarland.de/publications/docs/TWA%2B25.pdf) §IV–VI、表I–V、附录的序列化/基线复现与工业失败分析。

- **机制与知识：** SiDiff计算模型差异，simple change graph保留变化元素及其直接相连的既有元素，EdgeList序列化；MiniLM语义检索历史完整变更，最多12个多样化示例交给GPT-4-0613补全边。支持增加、删除、属性变更；未把整个模型图提供给LLM。
- **实验证据：** 工业/RepairVision/合成语料分别8/42/24模型；75/25切分后的测试补全122/221/210例。工业格式/类型结构/语义正确率92.62/76.23/62.30%。随机检索类型50%，语义优越性的显著性使用上界而非直接随机语义评分。51例既有方法比较中，对方使用GPT-3 text-davinci-002，不能把全部增益归于RAG。增加示例数无显著关系；相关示例重要。
- **边界与可用性：** 作者见到ID冲突、错误父节点、层级摊平及复制错误；附录承认难以引用切片外既有节点，并截断属性至200字符、排除超窗口变化图。代码/公开数据见[仓库](https://github.com/se-sic/icse_model_completion)，工业数据不公开。**本次判断：** 它已将关系局部表示和项目知识纳入补全；应借鉴固定模型/预算的检索消融，并以跨范围关系正确性验证我们的上下文设计。

<a id="c14"></a>
## C14 — Tell2Design

**身份与阅读：FULL。** Sicong Leng 等，*Tell2Design: A Dataset for Language-Guided Floor Plan Generation*，ACL 2023，pp14680–14697。已读[ACL正式全文](https://aclanthology.org/2023.acl-long.820.pdf) §3–5、表1–4、Limitations、附录A实现和D案例。

- **机制与知识：** 将房间类型/框坐标编码为可解析序列，T5-base自回归生成；边界以包围框减外部框编码进输入。知识来自标注、模板和训练，输出是二维房间布局，不含IFC语义关系。没有求解器或编译反馈循环。
- **实验证据：** RPLAN筛选80,788图；其中5,051人工描述、75,737模板描述。先在模板上warm-up，再以2,743人工描述微调，2,308人工测试且标注者不重叠。表2micro/macro-IoU54.34/53.30；去边界35.95/29.95。100例、5名评估者的全部要求满足率38%，GT85%；房间关系得分3.65/5。只用模板训练在人工测试上明显失效。
- **边界与可用性：** 作者指出英语、平面领域、未优化多样性；同一需求可有多个正确布局，所以IoU非语义正确的充分指标。已查[代码与数据README](https://github.com/LengSicong/Tell2Design)，仅检查资源与训练评测入口，未下载数据。**本次判断：** 可借其标注者隔离、人工需求对齐与边界消融；不能把80k全记为人工需求，也不应用像素指标替代IFC关系及提交成功率。

<a id="c15"></a>
## C15 — Multi-Location Software Model Completion / NextFocus

**身份与阅读：FULL（作者稿及补充稿）。** Alisa Welter、Christof Tinnes、Sven Apel，ICSE 2026；[arXiv 2601.13894](https://arxiv.org/abs/2601.13894)。已读[作者全文](https://www.se.cs.uni-saarland.de/publications/docs/WTA26.pdf) §4–5、图5/10、表1及[仓库补充稿](https://raw.githubusercontent.com/se-sic/modelcompletion_multilocations/master/Multi-Location_Software_Model_Completion.pdf) Appendix A.1–A.4/表6。作者PDF含模板会议信息占位，不用其“Conference'17”作为书目信息。

- **机制与知识：** 以1536维embedding和attention网络学习历史共同变更，预测下个focus，再局部LLM补全、更新并迭代10次。改版RaMc′使用两跳切片、可表达孤立节点的JSON、GPT-5-mini和两条检索示例；相较GPT-4-0613原版同时改变多个因素。
- **实验证据：** RepairVision从41项目912 commits筛到32项目，按commit时间切分，末次变更测试；跨项目实验抽10项目。0.98是节点排序汇总，且其Precision@k分母为min(k,实际正例数)。项目平均同项目0.58降至跨项目0.36。表1类型结构正确率：RaMc12.19%、NextFocus+RaMc8.48%、NextFocus+RaMc′16.11%；正确focus不等于正确补全。
- **边界与可用性：** 作者承认共变噪声、罕见/层级变更较弱、每项目只取最后模式；附录还排除了过大项目。已查[代码/数据/中间结果](https://github.com/se-sic/modelcompletion_multilocations)，未运行。**本次判断：** 关注点选择、关系结构和语义正确必须分开计分；关系依赖组若有价值，需超过已有两跳/历史共变方案，并避免把选择成功率写成整模型能力。

<a id="c16"></a>
## C16 — LLMs in MDE: systematic mapping study

**身份与阅读：FULL（综述）。** Weixing Zhang 等，*Large language models in model-driven engineering: a systematic mapping study*，Empirical Software Engineering 32, article3 **(2027)**，2026-07-16在线发表。已读[出版社全文](https://link.springer.com/article/10.1007/s10664-026-10921-4) §3.1–3.5检索/筛选/抽取/综合、§4.1/4.4结果、§5讨论与效度威胁；[67页PDF](https://link.springer.com/content/pdf/10.1007/s10664-026-10921-4.pdf)作为同版入口。

- **方法与单位：** 2025-09在五库检索2020年起作品，1666条经去重/初筛余1358，由一人筛选、另一人复核、争议第三人裁定，纳入45篇；2026-02一轮前后向滚雪球增加44，合并扩展版本后86篇。纳入英语、同行评审且有经验评价的LLM-MDE研究；排除无全文、综述和外围用途。43字段抽取后做频数/共现，非效果量元分析。
- **结果与边界：** 62篇涉及模型生成；36/86缺基线，21/86报告成本。作者给出多维工件有效性和透明评估建议，也承认单轮滚雪球、分类主观性、发表偏差及早期2026截面。没有细拆提示结构和LLM错误类型，不能由分类空白推出方法空白。
- **资源与本次判断：** 论文提供[OSF复现包](https://osf.io/g5by9/overview?view_only=5c10c1e56be3480d8d25e017b4276f7a)，本次入口解析失败，未检查包内文件。可用于定义矩阵和评价维度；不作为任何系统实现或“没人研究token/类型知识/上下文”的一手证明，更不覆盖2026年后续新论文。

## 可直接进入主矩阵的行

此处“近邻”表示问题或机制重合程度，不是方法被完全覆盖的裁定。未复跑任何论文。

| ID | 阅读 | 输出/任务 | 知识与检查 | 最重要的比较边界 | text2IFC优先用途 |
|---|---|---|---|---|---|
| [C01](#c01) | FULL | Blender场景程序 | 可复用空间技能、约束函数、优化/视觉反馈 | 20/20训练测试提示；无硬IFC保证 | 强知识＋求解器编码对照 |
| [C02](#c02) | FULL | 参数化CAD序列 | 领域训练、离散IR | L3失效率0.93%；语义吻合另算 | 可执行与满足需求分离 |
| [C03](#c03) | FULL | CadQuery代码 | 编译修复、逐项视觉QA | 200例；QA判断不完全正确；GT solver上界 | 可检验要求与反馈对照 |
| [C04](#c04) | FULL | CadQuery→STL | 零样本、编译调试 | 解析率升不保证条件IoU升 | 编码可行性、指标分母 |
| [C05](#c05) | FULL | 多层体素建筑 | 条件图、固定体素邻接、扩散 | TPR/FGW不全面占优；GT择样oracle | 拓扑条件与语义保留区别 |
| [C06](#c06) | FULL＋supp | 多层交互场景 | 拓扑分解、关系组、硬约束求解 | 难放对象可丢弃；不是IFC文件 | 关系组＋既成拓扑保留强近邻 |
| [C07](#c07) | PARTIAL | 代码构造元模型实例 | Pydantic元模型/验证器、反馈 | 仅摘要及资源检索；无主表 | 类型知识＋编码直接碰撞待核 |
| [C08](#c08) | PARTIAL | SysML可执行编辑建议 | mutation语言、MCP验证、语义oracle | 有工具/MR线索，无论文全文 | 编译保证与语义义务分工待核 |
| [C09](#c09) | PARTIAL | 软件模型切片与补全 | 半径/模块/LLM引导切片 | 1000/2库及成本收益仅摘要报告 | 上下文/成本主张首要碰撞待核 |
| [C10](#c10) | PARTIAL | SysML v2文本 | 示例RAG、ANTLR、迭代 | 开放稿下载失败；100%仅语法摘要声称 | 检索＋校验先例，保留未知 |
| [C11](#c11) | FULL | 序列图问题检测 | 原子需求检查、交叉过滤 | 76例；召回/精确率取舍且总token增 | 义务粒度与成本计量 |
| [C12](#c12) | FULL | Event-B模型/证明 | schema、编译器、PO、原子修复 | 有Cursor对照；跨层正确性近似 | 编译器/Agent责任分工强近邻 |
| [C13](#c13) | FULL＋appendix | 历史变更图补全 | SCG、EdgeList、历史RAG | 工业122例62.30%；旧基线模型不同 | 关系局部表示＋领域知识强近邻 |
| [C14](#c14) | FULL | 二维房间布局 | T5、边界IR、训练标注 | 人工仅5051；全部需求满足38% | 语义评价、标注与划分 |
| [C15](#c15) | FULL＋appendix | 多位置补全 | 共变focus、两跳切片、JSON | 0.98非补全率；最终类型结构仅16.11% | 选择质量与关系生成分开测 |
| [C16](#c16) | FULL，secondary | 86篇映射综述 | 系统检索、双人抽取、频数综合 | 截面止早期2026；不是系统实证 | 评价维度、报告规范 |

## 对候选研究表述的约束

1. **不要以“编码＋领域类型/API＋验证反馈”作为单独新颖性。** C01/C03/C04已有代码与反馈，C12已有schema、编译器、proof义务和原子修改；C07/C08又提供直接MDE碰撞线索。PARTIAL不能作为排除先例的依据。
2. **不要以“缩小上下文并保留关系”作为已经成立的创新。** C13已有变化图及既有邻居，C15有focus预测、两跳切片和JSON，C06有anchor/member关系组及既成拓扑检查；C09直接研究切片正确率与token。需要明确本方法额外保留的义务/关系是什么，并做同模型、同工具权限、同总预算对照。
3. **可检验的假设仍有空间，但本轮不裁定创新成立。** 在明确编译器可保证的性质后，Agent究竟还需要哪些信息，关系依赖组是否优于通用图切片，应作为待验证问题。按任务难度与关系类型分层，比较完整上下文、通用半径/模块切片、历史或语义检索、义务筛选及依赖组；费用应含选择器、检索、重试、验证与最终失败。
4. **矩阵必须保留负向条件。** C05的oracle选样、C06的丢弃策略、C11的召回损失/总token增长、C13的基线模型差异、C15的排序/生成落差都影响结论。语法成功、局部结构正确、需求覆盖、全模型合法和最终可交付文件是不同指标。
