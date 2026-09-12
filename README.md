# text2IFC

text2IFC 是一个自然语言生成与修复 IFC 的研究项目：在受支持的构件和合同范围内，将中文建筑需求转换为可检查的 IFC2X3，也支持按用户要求局部修复已有 IFC。模型负责理解需求和提出结构化候选，确定性代码负责合同校验、编译／应用、重开检查和最终发布。`bimnet` 只是本地仓库目录名，`BIMNet` 在数据文档中指外部数据来源。

## 首次接手

| 需要了解什么 | 从哪里开始 |
|---|---|
| 仓库结构、代码入口、工作规则 | [接管指南](docs/how-to/agent-takeover.md) |
| 本轮整理、分支整合、保留项和下一步 | [2026-09-13 交接快照](docs/handoffs/repository-handoff-2026-09-13.md)（历史定位，接手时重新核实 Git） |
| 最新执行位置 | [STATE](.planning/STATE.md) 顶部；下方保留历史检查点 |
| 产品边界和阶段安排 | [PROJECT](.planning/PROJECT.md)、[ROADMAP](.planning/ROADMAP.md) |
| 所有重要文档 | [文档索引](docs/README.md) |
| 已生成 IFC、用户输入和验收报告 | [Proof 入口](dataset/processed/proof/README.md) |

开始修改前阅读 [AGENTS.md](AGENTS.md)，确认 Git root、分支和已有修改。指南与交接快照提供导航，具体行为仍以适用合同、实际代码和当前用户授权为准。

## 两条产品链路

**Generation：** 用户请求／澄清 → Design Brief → 冻结需求预期 → BIM JSON 候选 → 编译并重开 IFC → 确定性检查、Audit 与有界返工 → 最终发布。`legacy_full` 保持默认，`staged` 需显式选择；已注册的新版本不代表所有入口自动使用该版本。

**Repair：** 原 IFC 与公开请求 → 索引和目标／Type／属性解析 → 必要澄清 → 有界 ChangeSet → 副本上原子应用 → 重开、L0/L1/L2 与保全检查 → 发布修复结果或明确阻断。源 IFC 和未请求修改的内容须保留。

| 入口 | 用途 |
|---|---|
| [run_text2ifc_chat.py](scripts/agent/run_text2ifc_chat.py) | Generation 人机 REPL，显式选择生成策略 |
| [run_phase6_2_cli.py](scripts/agent/run_phase6_2_cli.py) | Generation 脚本化输入、恢复及 Design Brief 版本选择 |
| [Repair API](src/text2ifc_ifc_repair/api.py)、[CLI](src/text2ifc_ifc_repair/cli.py) | 已有 IFC 的 start／continue／result 等公共调用 |

Python 要求见 [pyproject.toml](pyproject.toml)（当前为 ≥3.12），本地优先使用 `.venv`。详细链路和相关测试位置见接管指南。真实 Provider 调用前需有对应授权及[阶段准入](docs/validation/agent-capability-evaluation.md)；本页不是一次运行授权。

## 仓库结构

| 目录 | 职责 |
|---|---|
| [src/](src/) | Generation Agent、IFC Repair、合同、编译、质量检查、数据和知识模块 |
| [scripts/](scripts/) | CLI、离线验证、实验执行和 Proof 工具 |
| [tests/](tests/) | 可复用回归测试与夹具；调试输出不写进仓库根目录 |
| [schemas/](schemas/)、[prompts/](prompts/) | 版本化机器合同与 Prompt；已注册版本不原地重写 |
| [dataset/](dataset/data_organization.md) | 数据来源、授权／路径清单、派生数据、运行基线与 Proof |
| [docs/](docs/README.md) | 架构、操作指南、参考、验证、报告和专项交接 |
| [.planning/](.planning/STATE.md) | 当前执行状态、里程碑与 Phase SPEC／PLAN／VALIDATION |
| [archive/](archive/) | 历史归档，包括 Zcode 重构工作区；不等于已接入的生产实现 |

`dataset/processed/` 按用途保留七个目录：

- [proof/](dataset/processed/proof/README.md)：按 Generation／Repair → Phase → 集合查看成品和完整证据，人工状态与机器状态分别记录。
- [experiments/](dataset/processed/experiments/README.md)：实验、失败归因、token 账本及退役运行的保留材料。
- [derived/](dataset/processed/derived/README.md)：提取、转换、描述与回转派生数据。
- [text2json/](dataset/processed/text2json/README.md)：文本训练／评估配对、Gold、划分和 sidecar。
- [agent-demo/](dataset/processed/agent-demo/)：仍被消费的 few-shot、离线夹具及运行工作区。
- [ifc-repair/](dataset/processed/ifc-repair/README.md)：Repair 案例和离线输入，另有待核实权限的保留项。
- [ifc-repair-runs/](dataset/processed/ifc-repair-runs/)：现有 Plan07 测试和运行器依赖的源基线。

旧路径从 [processed 说明](dataset/processed/README.md)与[迁移映射](dataset/manifests/processed-layout-20260913.json)查找。临时测试用 `tmp_path`，一次性诊断用 `.tmp/`；该目录也可能含活动 Git 工作树，不能整目录删除。

## 当前设计与验证入口

- [语义与外观计划](docs/architecture/semantic-appearance-plan.md)：Type、材料、属性、颜色和基础门窗模板的范围权威。
- [光庭设计](docs/architecture/courtyard-library-design.md)与[两版 Proof](dataset/processed/proof/generation/phase6.6/courtyard-library-20260912/REPORT.md)：第二版人工已验收，第一版保留为历史参考。
- [Token 效率计划](docs/architecture/token-efficiency-plan.md)：已有小步实验及后续质量保全对照，不将单例收益推广为系统能力。
- [Repair 架构](docs/architecture/ifc-repair-pipeline-status-and-roadmap.md)、[Generation 工作流历史基线](docs/architecture/current-workflow-and-data-flow.md)：详细模块职责，当前实现增量见接管指南与 STATE。
- [Agent 验证协议](docs/validation/agent-capability-evaluation.md)、[Proof 格式](docs/validation/ifc-repair-proof-format.md)、[GitHub 发布指南](docs/how-to/publish-to-github.md)。

有 IFC 文件不等于已经通过发布；人工认可不替代机器门禁。已验收 Proof、真实失败与原始响应保持其历史结论，新验证另行记录。
