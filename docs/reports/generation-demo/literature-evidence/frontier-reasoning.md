# 方法候选证据：规格、约束、关系表示与空间一致性

核查日期：2026-09-15。以下 8 条均取得指定版本正文，核查了方法、主要实验及与选题有关的限制，记为 **F**；F 不表示复现，也不表示所有附录均已逐页读完。未披露的分母不补猜。这里的“对本项目”是我们的推论，与作者结论分开。

| ID | 论文与核查版本 | 阅读位置 | 直接影响的候选 |
|---|---|---|---|
| FR01 | SpecFix，arXiv:2505.07270v1 | §II–V、算法、Table I | 澄清不能仅靠改写提示或比较采样程序 |
| FR02 | Minimal-Core-Guided Repair，arXiv:2608.14771v1 | §3–8、Appendix A | 最小冲突核与定向修复已有先例 |
| FR03 | Formal verification planning，NAACL 2025 | §3–7、Tables 1–4 | 形式化规划、冲突解释、用户协商已有先例 |
| FR04 | Know Where You're Uncertain，MLSys 2025 | §3–6、主要实验表 | 区分不确定性来源并选择干预已有先例 |
| FR05 | Relational Decomposition，IJCAI 2025 | §3–5、主要实验表 | 关系表示＋背景知识＋程序综合已有先例 |
| FR06 | TTL-SR，arXiv:2609.06004v1 | §3–4、Tables 1–2 | 几何自洽驱动测试时学习已有先例 |
| FR07 | LLMorph，arXiv:2603.23611v1 | §II–VI | 变形测试无需逐例 Gold，但存在误报 |
| FR08 | COMFORT，arXiv:2410.17385v2 / ICLR 2025 | §3–5、主要实验表 | 参考系歧义、对称一致性已有直接研究 |

<a id="fr01"></a>
## FR01 — SpecFix

**来源。** Jia 等，*Automated Repair of Ambiguous Natural Language Requirements*，[指定全文](https://arxiv.org/html/2505.07270v1)。按预印本版本记录。

**方法与证据。** 采样 20 个程序，用生成测试区分执行行为，以公开示例选择解释，再对比相合/不合的程序修订需求，最多 3 轮。HumanEval+ 164、MBPP+ 378 题，三个模型、三次重复；DeepSeek-V3 的 HumanEval+ Pass@1 为 87.80→91.99。对照含移除隐藏答案辅助的 ClarifyGPT-auto。

**边界。** 采样程序和有限测试只是解释空间的近似；公开示例不足时，多数解释也可能错误。不能把程序一致当成真实用户意图。v1 的部分形式定义与算法方向表述不一致，引用机制以算法和实际操作为准，不照抄其公式。

**对本项目。** N06 必须超过“多采样、发现分歧、补问一句”。可考察选择什么可执行空间差异让用户判断，以及这种选择是否降低后续修改代价；差异可视化本身仍可能只是交互设计。

<a id="fr02"></a>
## FR02 — Minimal-Core-Guided Repair

**来源。** Sarkar，*From Errors to Proofs: Minimal-Core-Guided Repair for Neuro-Symbolic Constraint Solving*，[v1 全文](https://arxiv.org/html/2608.14771v1)。论文注明 IJCAI-ECAI 2026 LogiSymb workshop poster；不记作主会论文。

**方法与证据。** LLM 输出固定结构，clingo 求解，删除过滤找冲突约束子集，按错误类型反馈，最多 3 轮。77 个模板化题、7 个领域，其中 14 个不可行题。主模型 CoT 98.7%，通用修复 88.3%，冲突核修复 89.6%；弱模型在不可行题的编造解从 11/14 降到 1/14。

**边界。** “minimal”是子集极小，不保证约束数量最少。两修复组还存在错误类型反馈差异，需要析因实验分离作用；每系统 token 未报告。漏掉真实需求但形式程序仍可满足时，求解器不能发现缺失。

**对本项目。** N03/N04 不可声称首创冲突定位。更难的问题是将一次冲突变成在什么条件下可迁移的规则，以及何时应修改表示或分解。独立需求核验必须防止“删掉要求后成功”。

<a id="fr03"></a>
## FR03 — LLM Planning with Formal Verification

**来源。** Hao 等，*Large Language Models Can Solve Real-World Planning Rigorously with Formal Verification Tools*，[NAACL 2025 正式论文](https://aclanthology.org/2025.naacl-long.176/)、[全文](https://aclanthology.org/2025.naacl-long.176.pdf)。核查主要方法、实验与限制，未声称读完全部 50 页附录。

**方法与证据。** LLM 将查询转为步骤与 Z3 代码，借助 API 和求解器；不可满足时用冲突核提出约束调整并接受用户反馈。TravelPlanner 180 验证、1,000 测试题；最佳系统测试成功率 93.9%。另有 39 和 12 个不可行情景，在模拟用户偏好下评估协商，并测试四个新规划领域各 25 题。

**边界。** 方法含人工示例；不同模型的主表不能当作同模型增益。协商实验中增加轮数会提高成功率，也增加成本。形式证明约束于实际编码内容，不能自动保证自然语言转译完整。

**对本项目。** N04/N06 必须把“用求解器处理矛盾并征询用户”列为先例。IFC 的研究问题可落到几何/关系的跨模块依赖及多种合理解，而不是用一个 SMT 模块就称方法创新。

<a id="fr04"></a>
## FR04 — Know Where You're Uncertain

**来源。** Bhatt 等，*Know Where You’re Uncertain When Planning with Multimodal Foundation Models: A Formal Framework*，[MLSys 2025 全文](https://proceedings.mlsys.org/paper_files/paper/2025/file/703f727ec10190b2fddcf8e24f52df48-Paper-Conference.pdf)。

**方法与证据。** 区分感知与决策不确定性，以校准和形式规格估计风险，分别采用主动感知或模型适配。感知校准含 542 图/3,000 对象，决策校准 400 场景，另用 800 Carla 图做适配，50 个测试场景验证规划。

**边界。** 微调、主动感知和拒绝执行共同影响结果，不能直接当成固定参数模型的控制策略收益。校准保证依赖分布等条件；拒绝错误计划不等于完成全部任务。在线置信度不能替代 IFC 的实际验证。

**对本项目。** N05 若仅把错误分为“知识、实例、意图”，仍不足以形成新方法。必须提出可执行的辨别步骤，证明比同预算通用 Agent 或固定诊断流程更好。

<a id="fr05"></a>
## FR05 — Relational Decomposition for Program Synthesis

**来源。** Hocquette、Cropper，[IJCAI 2025 正式全文](https://www.ijcai.org/proceedings/2025/0504.pdf)。

**方法与证据。** 将数组等输入/输出展开为关系事实，使用 POPPER 与背景知识学习较小的关系程序，比较整体函数表示。四类任务涉及 ARC、一维 ARC、字符串和列表，采用多个时间预算、重复实验及留一验证。60 分钟表中字符串关系分解 71±2，整体字符串表示 79±2；列表分别 52±2、14±1，收益依赖任务。

**边界。** 假定无噪声，借助封闭世界生成负例；表示和搜索偏置并非完全相同，部分文献基线引用原报告而非同机重跑。不能把 IFC 中未记录的关系当成真实负例。

**对本项目。** N02 的创新不能是“改成关系图再综合程序”。应测试怎样从轨迹中选择可组合的关系效果、绑定对象角色并处理组合干扰；同关系输入的强规划/综合器必须进入对照。

<a id="fr06"></a>
## FR06 — Geometry-Aware Test-Time Learning / TTL-SR

**来源。** Zhang 等，[arXiv v1 全文](https://arxiv.org/html/2609.06004v1)，2026-09-05 预印本。

**方法与证据。** 将距离、分量、尺度等相关预测置于几何约束下，构造数值伪标签并更新 LoRA。适配参数沿测试流累计，非逐样本重置。比较两个开源 VLM、Tent/COME/TLM，在 Q-Spatial、SPAR 距离与 SpatialRGPT 上评估。Qwen3-VL-4B 的 Q-Spatial-ScanNet 平均准确率 40.00→46.47；正确容差为相对误差 25%。

**边界。** 主文把部分逐类结果说成全面提升，但表中存在退步，例如上述模型水平距离准确率 31.7→28.3。实际运行分母及更多设置转引补充材料，本卡不补猜。需要模型参数访问；几何自洽也可能共同偏离真实尺度。

**对本项目。** N07 可优先考察固定权重下的表示选择，而非直接引入测试时训练。若未来做 LoRA，应单列适配成本、流顺序和分布转移实验；不能因 backbone 冻结便称整个模型没有训练。

<a id="fr07"></a>
## FR07 — LLMorph

**来源。** Cho、Ruberto、Terragni，*LLMorph: Automated Metamorphic Testing of Large Language Models*，[arXiv v1 全文](https://arxiv.org/html/2603.23611v1)。按该工具稿核查；其 §IV 引用的 ICSME 2025 完整评测属于另一篇文章，不合并为两次独立证据。

**方法与证据。** 实现 36 种变形关系，变换输入并检查输出之间的预期关系，支持适用条件验证。四个 NLP 数据集、三个模型，共 561,267 次执行；人工复核 937 个违例，按任务/变形关系误报率为 0%–70%。

**边界。** 一致性违例并不能说明哪一侧正确。LLM 改写可能破坏变换前提，语义相似度也并非正确性判断；执行次数不是独立问题数。

**对本项目。** N01/N07 可使用确定性的单位换算、对象重命名和适用的坐标变换。必须同时变换任务的相关要求，并检查变换是否合法。自洽是诊断信号，最终仍要独立测量几何与关系。

<a id="fr08"></a>
## FR08 — COMFORT

**来源。** Zhang 等，*Do Vision-Language Models Represent Space and How? Evaluating Spatial Frame of Reference under Ambiguities*，[arXiv v2 全文](https://arxiv.org/html/2410.17385v2)、[ICLR 2025 正式记录](https://proceedings.iclr.cc/paper_files/paper/2025/hash/af2d9fb5bcee19ef2dfa70d843520c97-Abstract-Conference.html)。正式 PDF 体积较大导致读取失败，改读作者 v2，明确保留版本。

**方法与证据。** 对物体每 10° 采样，比较相机、观察者、对象参考系及未指明参考系。英文部分 COMFORT-BALL 720、COMFORT-CAR 57,600 个测试条件，评估 9 个 VLM；另扩展 109 种语言。测量准确性、对无关变化的鲁棒性、空间对称与相反关系一致性。

**边界。** 大量测试条件来自少量场景配置，不能当成同等数量独立真实场景。重点是四个方向关系，遮挡有限；接受区域是分析性近似，多语言提示用机器翻译。

**对本项目。** N06/N07 不能宣称首次发现坐标系或视角歧义。值得测的是：面对 IFC 的层级局部坐标，系统能否辨别哪一层绑定出错，或者确认确实需要用户指定参考系；不能以默认多数偏好代替用户选择。

## 使用这些证据时的限制

本页与 [知识证据](frontier-knowledge.md)、[技能证据](frontier-skills.md)、[空间证据](frontier-spatial.md) 共同支持候选筛选。已有论文的不足只说明它证明到哪里，不会自动使我们的组合新颖。下一步若选定一个方向，应对其最接近的程序综合、主动学习或规划方法做定向复查，再决定方法名称和贡献措辞。
