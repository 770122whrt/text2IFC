# 项目研究思路与 Pipeline 总结文档

## 1. 项目一句话概括

text2IFC 项目希望把中文或自然语言建筑需求转化为可验证的 BIM JSON，再由确定性的编译器生成 IFC2X3 模型文件，并在信息缺失、结构不完整或模型输出不可靠时，通过多轮 Agent、验证门禁和审计记录给出可追踪的中间证据。

## 2. 项目背景与研究目标

本项目面向自然语言到 BIM/IFC 的生成问题。项目的核心判断是：不直接让大模型生成原始 IFC STEP 文本，而是让模型生成更高层、更可验证的 BIM JSON；再由程序把 BIM JSON 编译为 IFC2X3 文件。

这个设计的背景主要有三点。

第一，IFC 文件本身包含大量底层实体、引用关系和几何实现细节，例如 `IfcCartesianPoint`、`IfcDirection`、`IfcOwnerHistory`、STEP ID 等。这些内容不适合直接由语言模型稳定生成。

第二，建筑需求经常缺少必要事实，例如墙厚、层高、门窗尺寸、门窗宿主墙、空间位置、楼层归属等。如果模型静默补全，会导致最终 IFC 看起来能打开，但语义与用户意图不一致。因此项目要求缺失事实进入 Draft 或追问流程，而不是被自动编造。

第三，IFC 是否可打开只是最低要求。项目还需要检查空间关系、构件完整性、门窗嵌入关系、楼层归属、属性保真、几何门禁、语义审计和 trace/report 证据。

当前研究目标可以概括为：

- 建立从文本到 BIM JSON 再到 IFC 的可运行链路。
- 建立 BIM JSON Schema，作为结构唯一真相。
- 建立 IFC2X3 编译器和验证门禁。
- 建立中文优先的多轮澄清 Agent。
- 建立多 Agent 流程，包括 Design Brief、Generator、Repair、Audit、Gate、Report。
- 支持真实模型供应商调用，目前项目中出现过 Mimo 和 DeepSeek 的 OpenAI-compatible/Anthropic-compatible 接入探索。
- 对 BIMNet/Matterport3D 授权数据进行本地训练和评估准备，同时保持训练集、验证集和测试集分离。

## 3. 当前研究思路梳理

### 3.1 为什么不是直接 Text -> IFC

项目当前没有采用“自然语言直接生成 IFC STEP 文本”的路线。

主要原因是 IFC STEP 文本的自由度过高，错误空间过大。即便模型生成的文本在语法上看起来像 IFC，也可能存在实体引用错误、空间关系错误、门窗宿主错误、楼层归属错误或几何不闭合等问题。

因此项目采用中间表示：

```text
自然语言
  -> Design Brief
  -> BIM JSON 2.0 或 Draft
  -> 验证和门禁
  -> IFC2X3
```

这里 BIM JSON 负责表达用户语义层面的建筑事实，例如：

- 建筑、楼层、空间。
- 墙、门、窗、板、楼梯等构件。
- 尺寸、位置、标高、厚度。
- 构件与楼层、空间、宿主墙之间的关系。
- 支持范围内的属性和类型信息。

底层 IFC 实体由编译器生成，而不是由模型直接输出。

### 3.2 为什么需要 BIM JSON

BIM JSON 是项目中连接大模型和 IFC 编译器的结构化中间层。它不是 IFC Schema 的完整复制，也不是任意 JSON，而是项目定义的受控建筑语义表示。

当前项目中 BIM JSON 的关键原则是：

- JSON Schema 是 BIM JSON 的唯一结构真相。
- 模型输出应是 BIM JSON 2.0 或 Draft，不应输出原始 IFC、STEP 文本、低层 IFC 辅助实体或编译器内部对象。
- 不能静默补全必要事实。
- 不能覆盖原始输入事实。
- 不能丢弃无法表达或无法迁移的源 IFC 事实，相关内容应进入 sidecar、loss accounting 或 Draft 记录。
- 对于当前 JSON/编译器不能表达的事实，应明确记录，而不是伪装成已经支持。

从已读代码和文档看，BIM JSON 经历过两个主要阶段：

- BIM JSON 1.0：用于建立最小闭环，重点是楼层、构件、基本尺寸和属性。
- BIM JSON 2.0：增加语义图、IFC 类、关系、Draft、capability、loss accounting 和更明确的支持边界。

### 3.3 为什么需要多 Agent

项目引入多 Agent，不是为了增加复杂度，而是为了把不同职责拆开。

当前设计中，各个 Agent 或模块的大致职责如下：

- Design Brief Agent：把用户自然语言整理成更清楚的设计说明；如果信息不足，提出 1 到 3 个中文问题。
- BIM JSON Generator：根据设计说明生成 BIM JSON 2.0 或 Draft。
- Repair Agent：在生成结果可修复时，根据验证反馈尝试修复。
- Audit Agent：对候选结果进行语义审计，判断是否与原始需求和中间设计说明一致。
- Deterministic Gates：用代码做硬性验证，例如 Schema、编译、重开 IFC、几何、实体完整性、门窗嵌入、哈希绑定、secret scan 等。
- Report Generator：把真实 trace 中的输入、输出、验证、审计、路径和指标汇总为 Markdown 报告。

项目中已经明确：Audit Agent 可以帮助判断语义是否合理，但不能覆盖 deterministic gate 的硬性结果。Gate 和 Audit 的目标是一体的：一个负责确定性检查，一个负责动态语义审查。

## 4. Pipeline / Workflow 总览

当前项目存在两条主要链路。

第一条是面向数据集和评估的离线链路：

```text
授权 IFC2X3 源文件
  -> IFC 解析和抽取
  -> BIM JSON 2.0 / Draft / loss sidecar
  -> Text / JSON 数据对
  -> Baseline
  -> Evaluation Harness
  -> 报告和指标
```

第二条是面向用户交互和生成的在线链路：

```text
中文建筑需求
  -> Design Brief Agent
  -> 追问或确认需求明确
  -> BIM JSON Generator
  -> JSON Schema / semantic validation
  -> IFC2X3 compiler
  -> compile / reopen / geometry / semantic gates
  -> Audit Agent
  -> route decision
  -> output.ifc / Draft / blocked report
```

在线链路中，最终产物不只是 IFC 文件，还包括：

- `output.ifc`
- `report.md`
- `session-export.json`
- `final-acceptance.json`
- `geometry-feedback.json`
- `gate-summary.json`
- `route-decision.json`
- `expected-facts.json`
- 原始模型输出、解析结果和审计结果

部分阶段正在讨论减少冗余 trace 文件，以提高生成速度和人工审阅效率。

## 5. Pipeline / Workflow 分阶段说明

### 5.1 Phase 1：BIM JSON 1.0 Contract and Validator

Phase 1 的目标是建立最小 BIM JSON 合同和验证器。

这一阶段完成的核心内容包括：

- 定义 BIM JSON 1.0 的结构。
- 建立 JSON Schema 验证。
- 把 Schema 作为唯一结构真相。
- 明确不能在代码中维护第二套独立结构模型。
- 建立基本测试，确保错误 JSON 会被拒绝，合法 JSON 能通过。

这一阶段解决的是“什么样的 JSON 才算项目接受的 BIM JSON”。

### 5.2 Phase 2：BIM JSON -> IFC2X3 最小编译器

Phase 2 的目标是把 BIM JSON 编译为真实 IFC2X3 文件。

这一阶段完成的核心内容包括：

- 使用 IfcOpenShell 生成 IFC。
- 生成可打开的 IFC2X3 文件。
- 建立建筑、楼层、墙、门窗、基本板件等最小构件闭环。
- 在写出 IFC 后重新打开验证。
- 把复杂位置、洞口关系和更高保真内容放到后续阶段。

这一阶段解决的是“JSON 到 IFC 是否能跑通”。

### 5.3 Phase 2.5：BIM JSON 2.0、IFC2X3 Schema 和信息差检查

Phase 2.5 的目标是把 BIM JSON 从最小结构扩展为更明确的语义表示，并以 IFC2X3 为基础检查 JSON 表达能力。

这一阶段完成的核心内容包括：

- 引入 BIM JSON 2.0。
- 支持明确的 `ifc_class`，例如 `IfcWall`、`IfcWallStandardCase`。
- 不要求模型生成底层 IFC 实体。
- 保留更精确 IFC 类，并把部分低层实现交给编译器生成。
- 引入 Draft Envelope，用于表达信息不完整或暂不支持的内容。
- 使用官方 IFC2X3 schema 文件作为本地依据。
- 引入 capability、supported scope、loss accounting。
- 检查从源 IFC 到 BIM JSON 时哪些信息能表达，哪些会损失。

这一阶段解决的是“BIM JSON 和真实 IFC 之间差了什么”。

### 5.4 Phase 3：Text-to-JSON Dataset and Baseline

Phase 3 的目标是建立文本到 BIM JSON 的数据集、baseline 和评估工具。

这一阶段完成的核心内容包括：

- 从授权 BIMNet IFC2X3 源文件构造 BIM JSON 2.0 目标。
- 建立 scene-family split，避免训练、验证、测试泄漏。
- 生成 Text / JSON 数据对。
- 建立 structured-output baseline。
- 建立 evaluation harness。
- 跑通 Natural Language -> BIM JSON 2.0 -> IFC2X3 的端到端 demo。

根据现有文档，Phase 3 中记录过：

- 25 个 formal BIM JSON 目标。
- 100 条 Text / JSON pair。
- 数据切分为 68 / 20 / 12。
- fake validation smoke 的相关指标。

需要注意：fake provider 是确定性测试工具，不代表真实模型质量。

### 5.5 Phase 4：Generated IFC Correctness Gates

Phase 4 的目标是检查生成 IFC 的正确性，而不仅仅检查 IFC 是否能打开。

这一阶段完成的核心内容包括：

- 建立 generated IFC correctness gates。
- 增加空间关系、墙体闭合、门窗嵌入、几何、属性等检查。
- 建立 all-25 fidelity inventory。
- 对材料、类型、拓扑、复杂几何损失进行记录。
- 生成与评估相关的报告和指标。

根据 `docs/architecture/phase-4-summary.md` 和规划文档记录，Phase 4 中曾统计：

- entities：4444 / 5308 represented。
- relationships：15046 / 16926 represented。
- properties：17607 / 18758 represented。
- representations：4509 / 6382 represented。
- materials：1533 / 2554 represented。
- types：154 / 1012 represented。
- connections：2263 / 2263 represented。

这一阶段解决的是“生成的 IFC 是否在结构和语义上足够可信”。

### 5.6 Phase 5：Multi-turn Clarification Agent

Phase 5 的目标是建立中文优先的多轮澄清 Agent。

这一阶段完成的核心内容包括：

- 用户输入中文自然语言需求。
- 如果必要信息缺失，Agent 每轮提出 1 到 3 个关键问题。
- 用户回答后合并信息。
- 信息完整时进入 Formal BIM JSON。
- 信息仍缺失时保留 Draft。
- 不使用默认模板静默补全。
- 最终 demo 可写出 IFC。

已知验收产物包括：

```text
dataset/processed/agent-demo/simple-room/output.ifc
```

这一阶段解决的是“用户说得不完整时，系统如何继续问，而不是乱猜”。

### 5.7 Phase 6：Multi-agent Prompt Reliability, Data Expansion, Fine-tuning, Deployment

Phase 6 的目标是把多 Agent、prompt registry、trace、report、实验和服务化能力组合起来。

这一阶段完成或规划过的内容包括：

- Prompt registry。
- Design Brief、Generator、Repair、Audit 的多 Agent 分工。
- Fake/file provider，用于确定性测试。
- Mimo 真实调用的实验。
- 生成 `report.md`，作为人工审核入口。
- 服务化接口雏形。
- 数据扩展和模型选择讨论。

根据 `docs/architecture/phase-6-model-decision.md`，当前阶段不把 fine-tuning 作为立即优先路径；原因是人工审核数据不足，现有训练规模和质量还不足以支撑可靠微调结论。

### 5.8 Phase 6.1：Mimo Live Workflow

Phase 6.1 的目标是用真实 Mimo provider 跑通多 Agent workflow。

已知产物包括：

```text
dataset/processed/agent-demo/phase6.1-mimo-live/output.ifc
dataset/processed/agent-demo/phase6.1-mimo-live/report.md
```

相关 API 文档被整理到：

```text
docs/reference/mimo-anthropic-api.md
docs/reference/mimo-openai-api.md
```

这一阶段的重点是区分真实 provider evidence 和 fake provider evidence。只有真实模型调用才能支持“真实 workflow 已跑通”的结论。

### 5.9 Phase 6.2：Interactive CLI and Session DB

Phase 6.2 的目标是建立用户可运行的交互式 CLI。

当前 CLI 入口包括：

```text
scripts/agent/run_text2ifc_chat.py
```

这一阶段的核心内容包括：

- 用户在命令行输入中文建筑需求。
- 系统创建 `session_hash`。
- 对话保存在共享 SQLite DB。
- Agent 可以继续追问。
- 用户回答后继续梳理。
- 需求明确后生成 BIM JSON。
- 通过验证后编译 IFC。
- 输出 IFC、report 和会话导出。

已知产物路径包括：

```text
dataset/processed/agent-demo/phase6.2-interactive-cli/sessions.sqlite
dataset/processed/agent-demo/phase6.2-interactive-cli/final-acceptance.json
dataset/processed/agent-demo/phase6.2-interactive-cli/runs/<session_hash>/output.ifc
dataset/processed/agent-demo/phase6.2-interactive-cli/runs/<session_hash>/report.md
dataset/processed/agent-demo/phase6.2-interactive-cli/runs/<session_hash>/session-export.json
```

从当前记录看，Phase 6.2 后续又经历了针对 REPL 的修复，包括：

- 空回答时提示重新输入。
- 用户回答后给出反馈。
- 修复 Design Brief artifact 缺失。
- 修复 Draft 或 invalid formal 的处理。
- 修复 gate 和 audit 的显示顺序。
- 增加更明确的 CLI 输出路径。

### 5.10 Phase 6.3：Gate/Audit Fusion, Dynamic Routing, Compact Trace

Phase 6.3 的目标是提高复杂多楼层建筑的处理能力，并整理 Gate 和 Audit 的关系。

当前设计重点包括：

- Gate 和 Audit 是同一个审核目标的两种手段。
- Gate 负责硬性、确定性检查。
- Audit 负责语义、意图和动态判断。
- Audit 不能覆盖 Gate 的硬性失败。
- Gate 的结果应能作为 Audit 的输入。
- Audit 发现问题后，应能形成 route decision。
- route decision 应能决定回到 Design、Generator、Repair，或者保持 blocked。
- 对复杂建筑应支持更清晰的失败路径，而不是只给出最终失败。
- 生成过程应支持 compact trace，减少无必要文件。

当前 Phase 6.3 已经存在验证矩阵和部分 live 运行记录，但复杂两层住宅输入仍未得到最终 accepted IFC。现有记录显示，系统能够阻止错误结果被误判为成功。

## 6. 当前 Pipeline / Workflow 的实际输出

### 6.1 数据集与 Text/JSON 输出

当前仓库中存在以下与数据集和 text/json 相关的目录：

```text
dataset/external
dataset/ifc
dataset/manifests
dataset/processed
dataset/sources
dataset/splits
```

`dataset/processed` 下包含：

```text
agent-demo
bim-json-1.0
bim-json-2.0
descriptions
full_dump
phase4
roundtrip_ifc
roundtrip_json
text2json
```

这些目录说明项目已经不只是手写 demo，而是有围绕 IFC、BIM JSON、自然语言描述、roundtrip 和评估输出的处理链路。

### 6.2 端到端 demo 输出

已知存在以下端到端 demo 产物：

```text
dataset/processed/text2json/e2e-demo/output.ifc
dataset/processed/text2json/e2e-demo/report.md
```

该类产物用于证明自然语言或文本描述可以进入 BIM JSON，再由编译器生成 IFC。

### 6.3 Agent demo 输出

已知存在以下 Agent demo 产物：

```text
dataset/processed/agent-demo/simple-room/output.ifc
dataset/processed/agent-demo/geometry-gate/simple-room-fixed
dataset/processed/agent-demo/geometry-gate/two-room-suite
dataset/processed/agent-demo/phase6-multiagent/output.ifc
dataset/processed/agent-demo/phase6.1-mimo-live/output.ifc
dataset/processed/agent-demo/phase6.2-interactive-cli
```

这些产物对应不同阶段的 Agent、Gate、Mimo live、CLI 和报告能力。

### 6.4 Phase 6.3 复杂建筑运行记录

当前复杂两层建筑相关运行记录包括：

```text
dataset/processed/agent-demo/phase6.3-live-two-storey-scaffold-v13
dataset/processed/agent-demo/phase6.3-live-two-storey-scaffold-v14
```

根据已读记录：

- v13 中 deterministic gates 曾经通过，但 Audit 发现候选结果缺少 `IfcSpace`、`IfcDoor`、`IfcWindow`、`IfcSlab`、`IfcRoof` 等关键实体，并指出墙体和楼梯细节不完整。
- v14 中 Generator 输出 Draft，schema/contract 检查发现未解决的 Draft path，例如楼层空间位置和楼梯尺寸；scaffold route 因关键数值别名缺失而 blocked。

这说明当前系统对复杂输入有一定识别和阻断能力，但还没有稳定生成可接受的复杂两层住宅 IFC。

### 6.5 报告与 trace 输出

当前项目要求 `report.md` 不是手写说明，而应由真实 trace 生成。

报告中应包含：

- 原始输入。
- Design Brief。
- prompt 引用。
- 原始模型输出引用。
- parsed BIM JSON 或 Draft。
- validation feedback。
- geometry feedback。
- repair route。
- audit result。
- metrics。
- final IFC path。
- sidecar 路径。

实际仓库中多个阶段已经存在 `report.md`、`metrics.json`、`gate-summary.json`、`route-decision.json`、`expected-facts.json` 等文件。

## 7. 当前已经实现的功能

当前项目已经实现或已有代码支撑的功能包括：

- BIM JSON 1.0 Schema 和验证。
- BIM JSON 2.0 Schema 和验证。
- Draft Envelope。
- IFC2X3 schema 文件本地化。
- IFC2X3 编译器。
- 使用 IfcOpenShell 写出和重新打开 IFC。
- 从 BIM JSON 生成 IFC 的基础构件。
- 从 IFC 源文件抽取 BIM JSON 的数据处理链路。
- Text / JSON pair 生成。
- scene-family split。
- baseline evaluation harness。
- generated IFC correctness gates。
- 简单房间和双房间 demo。
- 中文多轮澄清 Agent。
- session DB。
- REPL/CLI 入口。
- fake/file provider。
- Mimo live provider 接入记录。
- DeepSeek/OpenAI-compatible provider 接入探索。
- Prompt registry。
- Design Brief、Generator、Repair、Audit 多 Agent 分工。
- report.md 生成。
- final-acceptance.json。
- secret scan 和 trace 中避免泄露密钥的约束。
- 动态 gate、route decision、semantic coverage 和 expected facts 相关模块。

从代码结构看，相关模块主要位于：

```text
src/text2ifc_agent
src/text2ifc_compiler
src/text2ifc_contract
src/text2ifc_extractor
src/text2ifc_quality
src/text2ifc_service
src/text2ifc_text
scripts/agent
schemas
prompts
tests
```

## 8. 当前预留但尚未完全实现的功能

以下功能在文档、规划或代码结构中已有预留，但从当前记录看尚未完全成熟。

第一，复杂多楼层建筑的稳定生成。

简单房间和双房间已经基本可用，但复杂两层住宅仍会触发 Audit blocked、Draft blocked 或 scaffold blocked。当前系统能识别部分失败，但还不能稳定从复杂自然语言生成 accepted IFC。

第二，Audit 反馈回 Design 或 Generator 的闭环。

当前系统已有 Audit、Repair、route decision 和 gate 结果，但复杂案例中仍在讨论如何让 Audit 的问题更清楚地回到 Design Brief、Generator 或 Repair，而不是只形成最终 blocked。

第三，复杂空间布局的分层生成。

文档中已经讨论过复杂建筑可能需要分层、分区或模块化生成。是否需要修改第一个环节、JSON 接口或 scaffold 策略，仍属于当前讨论中的问题。

第四，RAG 或知识库。

项目已经讨论过需要根据 IFC2X3、BuildingSMART、BIM JSON capability、示例和 few-shot 构建知识支持，但当前无法从代码中确定已经形成完整可用的 RAG 系统。

第五，fine-tuning。

当前项目已有数据集和 baseline，但根据已读模型决策文档，现阶段还没有足够的人审数据支撑微调作为优先路线。

第六，部署服务。

`src/text2ifc_service` 中存在服务相关代码，Phase 6 也包含 deployable service 目标。但当前主要工作仍围绕 CLI、trace、provider 和复杂建筑 workflow。

第七，完整 IFC 保真。

Phase 4 已经做了 fidelity inventory，但复杂 representation、BRep、tessellation、boolean、surface geometry、材料、类型等仍有 loss accounting。

第八，trace 文件瘦身。

当前运行会产生较多 JSON、报告和中间文件。Phase 6.3 已经把 compact trace 作为目标之一，但具体裁剪策略仍在推进中。

## 9. 当前遇到的问题整理

### 9.1 复杂建筑生成能力不足

简单房间和双房间已经能基本跑通，但复杂两层住宅仍然不稳定。

已经观察到的情况包括：

- deterministic gates 可能通过，但 Audit 发现语义实体缺失。
- Generator 可能输出 Draft，而不是 Formal BIM JSON。
- scaffold 可能因为别名或必要字段缺失而 blocked。
- 输出 IFC 可能存在可打开但语义不完整的情况。

因此当前复杂建筑的核心问题不是单一 bug，而是复杂语义、空间布局、构件完整性、Agent 输出和 gate 审计之间的协同还不够成熟。

### 9.2 Gate 和 Audit 的职责边界仍在调整

当前项目已经明确：

- Gate 是硬性约束。
- Audit 是动态语义审查。
- 两者目标一致，但不能互相替代。

当前还在讨论的问题是：

- Gate 的失败报告应如何喂给 Audit。
- Audit 应如何判断问题属于 Design、Generator、Repair 还是不可自动恢复。
- Audit blocked 后是否应自动回到上游。
- 什么情况下可以 repair，什么情况下必须回到 Design Brief 或追问用户。

### 9.3 多轮交互的用户体验仍在修复

当前 CLI 已经能够提出问题、接收回答、保存 session 并继续流程。但历史调试中出现过：

- 空回答导致异常。
- 用户回答后缺少即时反馈。
- Design Brief artifact 缺失。
- 模型输出 Draft 后 CLI 没有继续追问。
- `original_request` 保护过严导致合理回答被误判为 changed original request。
- 生成阶段被截断或 schema validation 失败。

这些问题已有部分修复，但最终稳定性仍需要更多真实 CLI UAT。

### 9.4 Provider 与模型输出格式不稳定

项目中出现过 Mimo 和 DeepSeek 的接入。

当前需要注意：

- provider base URL、API key、模型名必须来自环境变量。
- token、headers、私有 base URL 不应写入代码、trace、report 或 git。
- OpenAI-compatible 和 Anthropic-compatible 的响应格式不同。
- `finish_reason=length` 会导致输出被截断，当前应阻断验收。
- 模型有时会返回 Markdown 代码块、额外说明、Draft 版本错误或 JSON schema 不匹配内容。

因此 provider 层需要继续保持严格解析和证据记录。

### 9.5 数据、编码和运行环境问题

当前项目中还存在一些环境层面的注意点。

第一，Windows 终端和中文输入可能导致编码问题。规划文档中已经提到现有脚本和中文文档存在 encoding inconsistency。近期复杂运行中也观察到过 stdin 或 wrapper 导致的乱码。

第二，`.pytest-tmp` 在 Windows 上曾出现 ACL 风险记录。

第三，数据集来源需要授权和明确许可证。当前用户已经说明取得 Matterport3D/BIMNet 授权，但项目仍应在文档和产物中保持 provenance。

第四，fake provider、scripted stdin、replay 和 live provider 必须区分。fake provider 可以用于回归测试，但不能证明真实模型 workflow 成功。

## 10. 当前项目状态概览

截至当前仓库可见状态，项目已经从最小 JSON -> IFC demo 发展到多 Agent、真实 provider、CLI、session DB、Gate/Audit 和复杂建筑调试阶段。

当前比较稳定的能力包括：

- BIM JSON 验证。
- 简单 BIM JSON 编译为 IFC。
- 简单房间 demo。
- 双房间 demo。
- 中文澄清流程的基本能力。
- 真实 provider 的最小调用和部分 live workflow。
- 报告和 trace 生成。
- deterministic gates 和 Audit 的基础组合。

当前仍在推进的能力包括：

- 复杂两层或多层建筑的 accepted IFC 生成。
- Audit 反馈到上游 Agent 的闭环。
- Gate/Audit 融合后的 route decision。
- trace 文件瘦身。
- 更稳定的 DeepSeek/Mimo provider 输出约束。
- 更明确的复杂建筑 BIM JSON 表达边界。

从 `ROADMAP.md` 和 `.planning/STATE.md` 的关系看，部分阶段在文档上已经完成验证矩阵或基础实现，但复杂 live provider IFC 的最终验收仍被记录为后续工作。这一点需要在后续讨论中继续区分：

- “系统能正确阻断错误结果”已经有证据。
- “系统能稳定生成复杂 accepted IFC”当前仍未完全达成。

## 11. 后续讨论时值得重点看的问题

后续讨论可以重点围绕以下问题展开。

第一，复杂建筑是否需要分层生成。

如果一个 prompt 同时包含多楼层、多房间、楼梯、门窗、楼板和屋面，直接一次生成完整 BIM JSON 的难度很高。需要讨论是否先生成建筑总体、楼层、空间，再逐层生成构件和开口。

第二，BIM JSON 2.0 是否足够表达复杂建筑。

当前需要继续检查：

- 多楼层空间如何表达。
- 空间相邻关系如何表达。
- 共用墙如何表达。
- 门窗宿主和相邻空间如何表达。
- 楼梯和楼层连接如何表达。
- 屋面、楼板和外轮廓覆盖如何表达。

如果 Schema 表达能力不足，应先扩展 Schema 和编译器，而不是强迫 Agent 编造不受支持的字段。

第三，Audit blocked 后应该回到哪里。

需要把问题类型分类得更清楚：

- 用户输入缺事实：回到追问。
- Design Brief 理解错：回到 Design Brief。
- Generator 漏实体或漏关系：回到 Generator。
- JSON 小错误：进入 Repair。
- 编译器不支持：进入 Draft 或 blocked。
- Gate 规则过严或误判：记录 gate issue，不应让模型绕过。

第四，Gate 规则需要避免写死。

项目要支持更复杂建筑，因此 Gate 不应只适配单房间、双房间或固定两层案例。Gate 应基于 expected facts、Schema、源输入和实际候选结果动态判断。

第五，报告是否能成为人工审核主入口。

当前用户希望不用打开很多 JSON 文件，而是在一个 Markdown 报告中看到原始输入、中间输出、模型输出、验证结果、Audit、route 和最终 IFC 路径。后续应继续检查 `report.md` 是否真正从 trace 自动生成，并且是否足够可读。

第六，真实 provider 的实验记录如何组织。

Mimo token、DeepSeek token、base URL 和 provider headers 不能进入 git 或报告。但真实模型调用的 response id、finish reason、parsed output、validation error 和 route decision 应保留，以便复现和审查。

第七，什么时候引入 RAG、few-shot 或专家 Agent。

目前已经讨论过专家 Agent、RAG、few-shot 和知识库。更合理的时机可能是在 Schema、Gate、Audit、复杂建筑表达边界明确之后，再把 IFC2X3/BIM JSON capability、成功案例、失败案例和修复案例放入知识层。

第八，fine-tuning 是否真的必要。

当前数据规模和人审标注还有限。后续需要先积累可靠的 text -> BIM JSON -> IFC 成功案例、失败案例、Audit 反馈和人工审核记录，再决定是否微调。

第九，如何定义“合适的 IFC 文件”。

后续验收不应只看 IFC 是否能打开。至少需要同时检查：

- IFC 文件能写出并重新打开。
- 楼层数量正确。
- 空间数量正确。
- 墙、门、窗、楼板、屋面、楼梯等实体数量合理。
- 构件楼层归属正确。
- 门窗嵌入正确。
- 空间关系与用户输入一致。
- geometry gate 通过。
- Audit 不存在 blocking finding。
- report.md 能解释完整过程。

第十，哪些内容当前无法从代码中确定。

当前无法从代码中确定完整 RAG 系统是否已经实现。

当前无法从代码中确定 fine-tuned 模型是否已经训练并部署。

当前无法从代码中确定复杂多层建筑 accepted IFC 是否已经由真实 provider 稳定生成。

当前无法从代码中确定所有 BIMNet 25 个 IFC 是否已经用于最终训练，而不是仅用于抽取、baseline 或评估准备。
