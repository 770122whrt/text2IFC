# text2IFC

将自然语言建筑需求转成可检查的 IFC2X3；也支持已有 IFC 的局部修复，以及 IFC → 文本 → IFC 的往返研究。
模型提出结构化候选，确定性代码负责合同校验、编译／应用、重开检查和发布。

当前整合 Repair、实验依据与仓库精简；执行位置见 [STATE](.planning/STATE.md)。开发历史保留在 Git 中，接管时从下方当前入口开始。
本地整理与恢复见[当前清理记录](docs/reports/workspace-cleanup-20261017/README.md)，此前 main 的精简检查点见[历史记录](docs/reports/lean-branch-20261007/REPORT.md)。

## 开始使用

Python ≥3.12。在仓库根目录运行：

```sh
python -m venv .venv
# 激活环境后：
python -m pip install -r requirements.txt
python scripts/agent/run_text2ifc_chat.py --help
python scripts/ifc_repair/repair.py --help
python scripts/ifc2text/run_baseline.py --help
```

本项目以源码 checkout 运行；`schemas/`、`prompts/` 和所需数据必须可访问。
IFC、大型档案等使用 Git LFS，按任务获取相应对象；LFS 指针文本不是真实 IFC。
真实 Provider 和向量检索还需对应配置；见 `.env.example`、[验证协议](docs/validation/agent-capability-evaluation.md)。

## 三条流程

| 流程 | 数据路径 | 入口 |
|---|---|---|
| Generation | 需求／澄清 → Design Brief → BIM JSON → IFC → Gate／Audit | [交互入口](scripts/agent/run_text2ifc_chat.py)、[脚本入口](scripts/agent/run_phase6_2_cli.py) |
| Repair | 原 IFC＋请求 → 解析／澄清 → ChangeSet → 副本应用 → L0/L1/L2／保全 | [Repair CLI](scripts/ifc_repair/repair.py)、[API](src/text2ifc_ifc_repair/api.py) |
| IFC2Text | IFC → 建筑事实 → 设计说明 → 公共生成流程 → 独立比较 | [基线入口](scripts/ifc2text/run_baseline.py)、[当前结果](docs/validation/ifc2text/README.md) |

Generation 保留默认 `legacy_full` 与显式 `staged`。旧 Schema／Prompt 版本仍是兼容合同，不因精简被替换。

## 接管与导航

| 目的 | 入口 |
|---|---|
| 行为约束与快速接管 | [AGENTS.md](AGENTS.md)、[接管指南](docs/how-to/agent-takeover.md) |
| 当前状态与边界 | [STATE](.planning/STATE.md)、[PROJECT](.planning/PROJECT.md)、[ROADMAP](.planning/ROADMAP.md) |
| 架构、参考与研究正文 | [文档索引](docs/README.md) |
| 命令地图 | [scripts/README.md](scripts/README.md) |
| 模型、来源与证据 | [Dataset](dataset/data_organization.md)、[Proof](dataset/processed/proof/README.md) |

生产代码在 `src/`；机器合同在 `schemas/`、`prompts/`；数据来源、运行基线和冻结证据在 `dataset/`。
保留当前 Repair 的必要回归及其依赖；此前退役的历史测试按精简记录恢复。
开发验证工具另用 `requirements-dev.txt` 安装。专项 preflight 仍须真实执行适用测试，缺失测试不代表通过。
