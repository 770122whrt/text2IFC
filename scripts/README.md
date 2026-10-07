# text2IFC 命令入口

在仓库根目录、Python ≥3.12 环境运行。安装运行依赖：`python -m pip install -r requirements.txt`。
交互入口可用 `--help` 查看参数；底层编译／验证脚本使用表中的位置参数。
真实 Provider 调用仍须符合 [验证协议](../docs/validation/agent-capability-evaluation.md)。

| 工作 | 入口 |
|---|---|
| 自然语言交互生成 | `python scripts/agent/run_text2ifc_chat.py --help` |
| 脚本化生成与会话恢复 | `python scripts/agent/run_phase6_2_cli.py --help` |
| 会话查询 | `python scripts/agent/query_phase6_2_sessions.py --help` |
| 现有 IFC 修复 | `python scripts/ifc_repair/repair.py --help` |
| BIM JSON 编译 IFC | `python scripts/bim_json/compile_ifc.py input.json output.ifc` |
| BIM JSON 验证 | `python scripts/bim_json_v2/validate.py formal input.json`（或 `draft`） |
| IFC2Text 确定性基线与比较 | `python scripts/ifc2text/run_baseline.py --help` |
| 分层建筑描述 | `python scripts/ifc2text/prepare_hierarchical.py --help` |
| 门窗及建筑往返实验 | `python scripts/ifc2text/component_campaign.py --help` |
| 修复证据维护 | [Repair 工具目录](ifc_repair/README.md) |

`ifc_pipeline*`、`dataset`、`text2json`、`ifc_knowledge` 提供数据转换、来源清单和知识维护工具。
`proof` 和 Repair 的 `curators`／`audits` 提供独立证据检查。

精简分支移除了已结束的阶段演示、单次墙体诊断和测试源码。仍被其他入口导入的旧脚本保留，
例如 `rerun_v10.py`、`continue_audit_v12.py`，不能仅凭版本号删除。
验收执行器的 `validate`／preflight 模式依赖测试源码；需要时按
[精简记录](../docs/reports/lean-branch-20261007/REPORT.md)恢复验证检查点。
缺少测试或阶段准入时仍应阻断真实调用，不能用编译成功替代准入。
