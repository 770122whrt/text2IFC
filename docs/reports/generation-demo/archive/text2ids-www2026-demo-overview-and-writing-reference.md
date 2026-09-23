# text2IDS / WWW 2026 Demo：Overview 与 text2IFC 仿写参考

> **2026-09-21 阅读状态更新：**用户已上传四页 PDF，当前以 [SGSS 全文 Overview 与 Repair 后作边界](../../repair-demo/sgss-fulltext-review-20260921.md)为准。本页“未获得全文”等内容仅保留当时访问状态，不再代表当前阅读进度。新稿区分作者架构主张、已展示平台、未来 Validate 功能与尚缺定量对照的效果主张。

> 更新：2026-09-18  
> 目标：确认 text2IDS 的论文类型、建立可核实的 overview，并提炼适合 text2IFC WWW Demo Paper 的写作结构。  
> 证据边界：严格区分“已核实出版事实”“由标题/标准背景支持的定位判断”和“给 text2IFC 的写作建议”。

## 1. 结论：它确实是 WWW 2026 Demo Paper

论文：**LLM-Powered Structurer: Normalizing Natural Language to Information Delivery Specification for Industrial Data Exchange**

作者：Jiqian Yang, Sujie Yan, Zhi Li, Mingyu Liu, Yousheng Wang, Wei He

已核实出版信息：

- The Web Conference 2026 — **Demo Track**
- 收录于 Companion Proceedings of the ACM Web Conference 2026
- 页码：212–215
- DOI：https://doi.org/10.1145/3774905.3793139
- WWW 2026 官方 Accepted Demo ID：des1028
- 官方 accepted demos：https://www2026.thewebconf.org/accepted/demo.html
- 官方 Session 5：https://www2026.thewebconf.org/program/full-schedule.html
- DBLP：https://dblp.org/rec/conf/www/YangYLLWH26

因此它不是“看起来像 Demo 的短论文”，而是被 WWW 2026 正式 Demo Track 接收并进入 Companion Proceedings 的论文。

## 2. 当前全文读取状态

本轮尝试了用户提供的 ACM PDF、ACM Proceedings、DBLP、Google Scholar、ResearchGate，以及当前 text2IFC 仓库 dataset/sources/PAPERS。

当前结果：

- ACM PDF 在当前访问环境返回 403 Forbidden；
- DBLP 标注 access: closed；
- ResearchGate 页面只提供 Request Full-text PDF；
- 当前仓库没有该论文 PDF 或正文副本。

因此本文件不会伪造论文的具体模型、Prompt、系统模块、数据规模、实验数字、实际章节顺序或作者没有公开可核实的 novelty claim。

如果后续获得 PDF，应把本文件升级为 full-text verified overview，并用原文页码替换目前的定位判断。

## 3. 已经可以可靠理解的研究定位

论文标题明确给出三个核心对象：

Natural Language  
→ LLM-Powered Structurer  
→ Information Delivery Specification (IDS)  
→ Industrial Data Exchange

因此，可以安全地把它理解为：

> 一个面向信息交付/交换需求的结构化系统，将自然语言形式的要求规范化到 Information Delivery Specification（IDS）这一机器可解释的标准形式。

这里最重要的不是“让 LLM 输出一段 XML/JSON”，而是：

> 把开放语言放进一个标准化、可被下游软件消费的工程数据合同中。

这与 text2IFC 的思想谱系高度一致。

## 4. 为什么 IDS 是重要输出，而不是普通结构化文本

buildingSMART 的 IDS 是面向 IFC 信息要求定义与自动检查的开放标准：

https://www.buildingsmart.org/standards/bsi-standards/information-delivery-specification-ids/

它的核心作用可概括为：

human / project information requirement  
→ machine-interpretable specification  
→ automatic checking of IFC information

因此 text2IDS 的“结构化”更适合被理解为连接自然语言和 OpenBIM 可执行验证生态，而不是普通的信息抽取任务。

对 text2IFC 的直接启发是：不要把贡献写成“LLM 生成 IFC JSON”，而要强调结构化中间产物后面的 deterministic downstream semantics。

## 5. Evidence-bounded Overview

### 5.1 一句话

**text2IDS 展示了如何使用 LLM 将非结构化自然语言信息需求规范化为标准化 IDS，使人类表达能够进入机器可解释的工业数据交换与 IFC 信息验证流程。**

### 5.2 问题

BIM / IFC 工作流中的信息需求往往首先由人以自然语言表达，而自动检查工具需要结构化、机器可解释的要求。两者之间存在明显的表示鸿沟。

如果依赖人工把文本要求重新编码为 IDS，就会产生额外的人力和专业门槛。

### 5.3 系统定位

从题名和 Demo Track 身份可以确认，它的核心展示对象是一个 LLM-powered structuring interface：

自然语言要求  
→ 语义结构化 / normalization  
→ IDS  
→ 标准化信息交换 / IFC checking ecosystem

核心系统价值是让 LLM 位于“自然语言 ↔ 标准规范”之间，而不是让 LLM 取代标准。

### 5.4 Demo 价值

这一题目非常适合 WWW Demo：

- 输入天然适合交互；
- 输出是可直接展示的标准化 artifact；
- 用户可以观察“自然语言如何被规范化”；
- 下游标准工具可以消费结果；
- 系统具有清楚的 before / after。

其价值来自可运行的 end-to-end transformation，而不必在四页中承担完整 Research Track 论文的实验规模。

### 5.5 当前无法从全文核实的部分

在取得 PDF 前，以下内容必须保持未知：

- 是否使用 retrieval / ontology / schema grounding；
- 是否按 IDS facets 分阶段生成；
- 是否使用多 Agent；
- 是否支持 clarification；
- 是否验证生成 IDS 的 schema validity；
- 是否真实调用 IfcTester / IDS checker；
- 是否有人工或自动评价；
- 是否比较多个 LLM；
- 是否开源代码、数据或 Web Demo。

不能根据我们自己的 text2IFC 系统反向补全这些内容。

## 6. 为什么它的风格很适合 text2IFC

两项工作可以形成非常自然的同一家族故事。

### text2IDS

human natural-language information requirement  
→ LLM semantic structuring  
→ standard IDS artifact  
→ machine-readable IFC information checking

### text2IFC Repair

human natural-language modification request + existing/damaged IFC  
→ LLM semantic interpretation  
→ deterministically authorized ChangeSet  
→ IFC mutation  
→ reopen + independent L0/L1/L2/preservation

二者共同体现：

> **LLM 处理人类语言，开放标准和确定性程序承担工程执行语义。**

但 Repair 比 IDS 生成多了一层风险：错误 IDS 主要导致规格表达错误，而错误 Repair 会直接改变工程 artifact。

所以 text2IFC 更应该强调：

> **interpretation is not mutation authority.**

## 7. WWW Demo Track 官方要求对我们意味着什么

WWW 2026 Demo CFP 明确要求：

- Demo 必须基于 implemented and tested system；
- 鼓励 conference attendees 进行 hands-on interaction；
- 论文要说明 demonstration 的 context 和 contributions；
- 要说明 conference venue 中如何 instantiate / deploy；
- 最多 4 页，包含 references；
- 鼓励 repository、demo video 或 Web system；
- accepted paper 进入 Companion Proceedings，并进行现场 Demo + poster。

官方 CFP：

https://www2026.thewebconf.org/calls/demos.html

所以 text2IDS 的 212–215 四页形式不是“缩水 research paper”，而是符合 Demo Track 的 system-centered paper。

对 text2IFC 来说，四页最重要的不是塞满消融，而是让 reviewer 快速确认：

1. 问题真实；
2. 系统确实已经实现并测试；
3. 设计不是普通 LLM tool calling 的简单包装；
4. Demo 可以现场交互；
5. 成功、澄清和拒绝路径都能演示；
6. 输出是可验证 IFC，而不是漂亮截图。

## 8. text2IFC 推荐仿写结构：4 页 Demo Paper

这不是对 text2IDS 原文章节的伪复原，而是结合其 Demo 定位和 WWW 官方要求为 text2IFC 设计的结构。

### Page 1：Problem + System Idea

#### Title

建议沿用“系统名：系统完成什么转换”的标题风格。

候选：

**text2IFC: Bounded Natural-Language Repair of IFC Models with Verified Semantic ChangeSets**

或：

**text2IFC: From Natural-Language Building Edits to Verified IFC ChangeSets**

#### Abstract

只回答四件事：

1. 为什么安全修改 IFC 很难；
2. 普通 LLM IFC editing 的风险是什么；
3. text2IFC 如何分离 interpretation 和 mutation authority；
4. Demo 能让用户现场看到什么。

#### Introduction

保持一条逻辑：

IFC editing is hard  
→ natural language lowers the interaction barrier  
→ unconstrained LLM edits are unreliable  
→ engineering mutation needs bounded authority and verification  
→ text2IFC

贡献只保留 2–3 点：

1. IFC2X3 + natural-language bounded repair workflow；
2. deterministic target/property authority + atomic ChangeSet；
3. reopened IFC verification + preservation + fail-closed interactive demo。

第一页应放一张主流程图，而不是完整工程架构。

### Page 2：System Overview

只讲四个逻辑 block：

**A. Understand**  
LLM Stage 1 提取 operation、target description 和 requested values。

**B. Authorize**  
程序解析 target occurrence / Type、property candidate、exact Pset / Property / value type / scope，并在必要时 clarification。

一句话重点：

> Retrieval proposes candidates; it does not grant mutation authority.

**C. Apply**  
Stage 2 生成 Draft；Binder 重建确定性 authority；所有 operation 进入一个 atomic ChangeSet；只写 staging IFC，不原地修改 source。

**D. Verify**  
重新打开文件；执行 L0、L1、L2 和 preservation；最后 publish 或 fail closed。

这一页建议放 architecture figure + 一个很小的 capability table。

### Page 3：Demonstration Scenarios

不要只展示 happy path。

推荐固定六个场景：

| Demo | 用户看到的行为 |
|---|---|
| Property edit | natural-language property → standard IFC property → verified output |
| Invalid value | candidate 正确但 value type 不兼容 → stop → clarification → resume |
| Ambiguous target | 多候选 → bounded choice → stable resume |
| Beam / Column add | geometry + Type + semantic property |
| Cross-family ChangeSet | 多 operation 同一原子事务 |
| Unsupported mixed request | 整个事务 fail closed，source unchanged |

每个 Demo 都使用相同 UI：

Request  
→ Resolved authority  
→ Bound ChangeSet  
→ Before / After model  
→ Verification result

这样现场观众不需要先理解全部 IFC schema，也能理解系统为什么比聊天机器人安全。

### Page 4：Evidence + Related Work + Deployment + Conclusion

#### Evidence

使用紧凑的 frozen evidence：

- R1：12/12 frozen cases；
- 13 operations；
- 23 IFC reopens；
- 12 independent recomputations；
- 1 correct intentional no-output；
- L0/L1/L2/preservation；
- 0 Proof errors / limitations。

这些数字应明确写成 coverage-oriented frozen acceptance evidence，而不是统计成功概率。

#### Related Work

四组就够：

1. Natural-language BIM generation/editing；
2. IFC agent/tool systems；
3. BIM editing benchmarks；
4. verification / compliance / automatic alteration。

重点点名 Text2BIM、MCP4IFC/IFC-Copilot、BIM-Edit、BIBIMBAP、Self-Verification、Wu et al. 2026。

#### Demo Deployment

WWW CFP 要求说明现场部署。

建议：

browser / local UI  
→ RepairAPI  
→ LLM Provider + local IFC index/property runtime  
→ IfcOpenShell  
→ viewer + evidence panel

最好预置六个稳定 fixture，避免现场网络或超大 IFC 让演示失控。

#### Limitations

主动写：

- IFC2X3；
- bounded component families；
- occurrence scalar property scope；
- no shared-Type mutation；
- no general Wall geometry editing；
- no structural-analysis operations；
- Phase 13 large-IFC context not claimed。

Demo Paper 主动写边界会增强可信度。

## 9. 一个适合我们后续论文的 Overview 草稿

下面不是 text2IDS 原文，而是参照其“自然语言 → 标准化工程 artifact”的风格，为 text2IFC 生成的研究概述参考。

### 中文版

text2IFC 是一个面向 IFC 建筑模型的自然语言生成与修复系统。本 Demo 聚焦已有 IFC2X3 模型的受控修改：用户以自然语言描述需要新增或修改的构件及属性，LLM 负责解析操作与语义意图，而目标实体、IFC 属性权威和最终执行范围由确定性程序解析并绑定为统一 ChangeSet。系统随后通过 IfcOpenShell 在 staging 模型中原子执行修改，重新打开产出的 IFC，并对目标结果、BIM 语义及非目标内容保全进行独立验证。对于目标歧义、属性值不兼容或包含不支持操作的请求，系统会进入澄清或 fail-closed 状态，而不是发布部分修改或伪成功模型。Demo 将展示属性修改、结构构件新增、澄清恢复、跨构件事务以及正确拒绝修改等场景，使用户能够从自然语言请求一路观察到可审计的 IFC 变更与验证结果。

### English reference

text2IFC is an interactive system for natural-language generation and repair of IFC building models. This demonstration focuses on bounded modifications to existing IFC2X3 artifacts. Users describe desired component or property changes in natural language, while an LLM interprets the requested operation and semantic intent. Rather than allowing model output to directly authorize mutations, text2IFC deterministically resolves target identities and IFC property authority, and binds the requested modifications into a unified semantic ChangeSet. The ChangeSet is atomically applied to a staging model with IfcOpenShell; the resulting IFC is then reopened and independently checked for the requested geometry, relationships, semantic facts, and non-target preservation. Ambiguous targets, incompatible values, or requests containing unsupported operations trigger clarification or fail-closed termination instead of partial or misleading output. The demo exposes the full path from user intent to an auditable IFC artifact through property edits, structural additions, clarification and resume, cross-family transactions, and correct no-output guards.

## 10. 我们最值得模仿 text2IDS 的不是“方法细节”，而是论文包装

目前没有全文证据支持逐章模仿 text2IDS 的具体模型设计，但其题目和 Demo 形态已经给出一个很适合我们的模板：

text2IDS：natural language → normalized open-standard specification

text2IFC：natural language → authorized open-standard model mutation

共同表达：

Human language  
→ LLM interpretation  
→ bounded standard artifact  
→ deterministic engineering behavior

这比“我们用了某个更强 LLM / Agent / RAG”更适合 WWW Demo。

## 11. Full-text 获取后必须补做的核查

拿到 text2IDS PDF 后，下一版应逐页补：

1. Abstract：作者真正的 problem / method / contribution；
2. Introduction：作者如何定义 IDS 生成难点；
3. System architecture：到底有哪些组件；
4. Figure：哪张图最代表系统；
5. Demo workflow：用户如何输入、查看和修改结果；
6. Evaluation：数据量、模型、指标、baseline；
7. Limitations；
8. 开源 / URL / demo video；
9. 四页实际版面比例；
10. 哪些句式/结构适合 text2IFC，哪些只是 text2IDS 特有。

在此之前，本文件应作为 **verified publication overview + text2IFC writing reference** 使用，而不是标记为“已全文精读”。
