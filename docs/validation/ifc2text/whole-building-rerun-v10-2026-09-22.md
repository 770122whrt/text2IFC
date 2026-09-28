# 修复后的 hxp 整栋单次重跑

2026-09-22 已明确要求“先重跑一次看看”，并追问几何和材料误差来源。本次运行使用新目录 `dataset/processed/experiments/ifc2text-rerun-20260922/`，保留旧源、响应、失败与账本。

一次流程依次运行：源 IFC → 描述 0.8／导读 Prompt 0.7 → 公共 Brief 2.7 → 公共 Generation BIM JSON 2.4 → 编译、Audit／终态 → Compare 1.0。重建端只接收设计说明；源 IFC、提取事实及已揭示差异仅供描述端和比较端读取。

额度继承旧单墙复验的全部消耗：写作 21 次、重建 14 次、累计 1,400,238 token。此次只增加一次写作和最多三次重建侧调用，总 token 上限仍为 2,000,000；没有外层自动重试，没有覆盖或重置旧账本。Brief 或生成失败时保留真实失败，不能把修改过的响应作为本次成功。

前一轮变更涉及公开接口和 schema，需重新进行本阶段准入。运行器 `scripts/ifc2text/rerun_v10.py validate` 在阻断网络的条件下验证 IFC2Text、公共 Generation 2.4、Provider 异常、澄清恢复、ChangeSet 原子应用、持久化终态、编译重开与几何门。测试矩阵、准确命令、退出码、跳过、日志哈希与 Python／依赖写入 `validation/admission.json`。不运行仓库 Full Preflight。

工作树保留已有未提交改动。此次准入采用当前 commit 加完整执行范围的文件 SHA-256 快照，包含新增文件；每次真实阶段开始前和结束后重核文件、配置和源 IFC。任何快照变更、失败测试、跳过或网络访问都会阻止准入。此方式记录实际执行字节，不将未提交代码冒充 HEAD，也不为了运行而提交无关工作。

主要离线覆盖：

| 范围 | 测试 |
|---|---|
| IFC→描述→公共生成→IFC／Compare | `tests/ifc2text/test_compact_public_v04.py`（旧路线及显式 2.4）、`test_offline_public_bridge.py` |
| 新合同与最终接受 | `tests/agent/test_generation_v24_route.py` |
| 传输、截断、无效响应与 Brief 失败保存 | `test_phase6_2_openai_compat.py`、`test_public_brief_failure_evidence.py` |
| 澄清、恢复与终态发布 | `test_clarification_resume_preservation.py`、`test_interactive_cli_generation.py` |
| 原子应用 | `test_phase6_5_changeset_apply.py` |
| 空间、特殊墙与开洞 | `test_space_geometry_projection_v12.py`、`test_polygon_wall_hosts_v24.py`、`test_floor_opening_identity.py`、相关既有几何门测试 |
| 源文件不变、预算继承、精度、材料及描述覆盖 | `tests/ifc2text/` |

即使生成终态通过，仍以原 IFC 的独立 Compare 检查忠实重建。此次是已揭示 hxp 案例的复验，不作为未知建筑或系统能力提升证据。所有线性容差固定为 0.1 mm；不得为了通过而放宽。
