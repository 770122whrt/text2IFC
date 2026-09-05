# Zcode 整合与本地恢复核查

日期：2026-09-05。目标分支仅为 `Zcode`，没有合并或推送到 `main`。

## 来源与提交

| 提交 | 内容 |
| --- | --- |
| `45813810` | 原根目录 106 个并行代码、测试、Prompt/Profile、项目指引和资料文件的检查点 |
| `c2871971` | 5 个阻止合并的同路径历史离线证据，先保存本地版本 |
| `a2c64a0a` | 合并 `codex/c2-c5-restoration-fix` 的 26 个提交，来源 tip 为 `68879c40` |
| `28eb1540` | 恢复归档、子模块数据快照、检查记录；去掉自动合并产生的同值重复字典键 |

代码及恢复归档已在 `28eb1540` 推送至 `origin/Zcode`。本报告、最终离线日志和修正版验证工具随收尾提交推送至同一分支；最终提交号及推送后核对结果见本任务回执。

根目录开始时为 `8bfcfe07`，`w` 为 `68879c40`。根目录的 4 个既有删除没有暂存或提交：

- `Liu 等 - 2025 - Dataset and benchmark for as-built BIM reconstruction from real-world point cloud.pdf`
- `MP_TOS.pdf`
- `MP_TOS_翻译.md`
- `requirements-phase6.2.txt`

前三项的资料副本同时位于 `dataset/sources/`；四项原路径均仍能从 Git 历史恢复。
没有执行 `git clean`、`reset --hard`、批量 restore、`git add -A` 或 worktree 删除。

## 兼容性处理

- 18 个冲突文件、102 个冲突块分别处理，记录见 [merge-decisions.json](merge-decisions.json)。
- 保留根目录 Door/Window 新版本 Profile、Door 语义授权、语义 bundle 展开、mixed manifest 绑定和标识集合比较。
- 保留 `w` 的几何/Type 修复、R1 合同与资源边界、Stage 1 v0.12、正式 C1–C5 工具和证据。
- scope/evidence 顺序冲突采用根目录已冻结的集合语义：等价重排允许，缺失、额外、重复标识仍拒绝。更新了 `w` 的一条矛盾旧测试，未重写已注册 Prompt。
- 同路径的历史运行和冻结文件不拼接：当前路径使用 `w` 的后继记录，根目录原版保存在前置提交中。
- 自动合并的同值重复字典键已移除；AST 检查未发现生产模块和 repair 脚本中的重复常量字典键。

**重构副本仅归档，未完成生产兼容整合。** `refactor-workspace.zip` 保留 8,755 个文件，包含独有的生产/benchmark 评估拆分、`text2ifc_proof` 包、runner 分组、新文档体系，以及 `tmp/source-snapshot`。这些成果仍基于较早实现；后续采纳需要迁移后续修复、保持旧入口并重新验证。当前 root 没有通过整个旧镜像覆盖这些模块。

## 正式 Proof

最终路径：`dataset/processed/proof/repair-damage-restoration/c1-c5-live-20260904-combined`。

对 `w` 与根目录的全部 142 个文件进行了路径集合及 SHA-256 比较，完全一致。保留 original/damaged/repaired IFC、REPORT、损伤与重建 GUID、IFCcompare 结果和来源记录。详见 [proof-byte-verification.json](proof-byte-verification.json)。本次没有重新运行真实 Provider、重新 curate 或改写正式 Proof；不重新判断用户已接受的 C1–C5 结果。

## 离线验证

本次 Python 回归包装入口禁用 socket 连接，并将保护带入 multiprocessing 子进程；测试使用独立且此前不存在的 basetemp。验证使用离线夹具，没有发起真实 Provider 调用。

| 检查 | 当前结果 |
| --- | --- |
| 第一轮合同/授权/runner 回归 | 112 passed，1 failed；失败为两分支 scope 顺序预期冲突 |
| 冲突处理后集合语义与 mixed Stage 2 回归 | 33 passed，0 failed |
| `compileall`：src/scripts/tests | 通过 |
| source diff whitespace 检查 | 通过；历史 Prompt 的 EOF 空行及证据的 CRLF 按原字节保留；新增 pytest 原始日志/XML 的尾随空格也保留，因此不声称全量 evidence diff --check 通过 |
| Windows 子进程包装缺陷修正后的两个 Proof 兼容目标 | 2 passed；修正测试包装脚本，不修改产品行为 |
| 40 个变更模块 + 3 个事务/发布模块，共 557 项 | 556 passed、1 failed、0 errors、0 skipped，耗时 1144.01 秒；唯一失败为验证父目录命名与路径断言冲突 |
| 唯一路径断言的 v3 最小重测 | 1 passed，1.55 秒；仅调整一次性验证脚本的临时目录，未改产品或测试 |

两条广泛命令先后被停止：先排除直接 C1–C5 重建模块，随后发现旧 `p0p2_smoke` 间接导入该模块，于是排除整个 composite 目录。期间运行的是隔离 scratch 中的离线测试，不改写正式 Proof，不能算作新验收。停止的运行不计作通过。

第一次 557 项命令还暴露了本次一次性包装脚本缺少 `__main__` 保护：Windows multiprocessing 重入 pytest，导致 Proof 夹具和属性重放出现 `not_evaluable`。该轮无效，不用于生产兼容结论。添加 main 保护和 `freeze_support()` 后，两个最小目标均通过，随后重新运行相同 557 项范围。首次错误日志保留，未将验证工具缺陷归为产品缺陷。

原始一次性验证脚本保存在 `integration-tools.zip` 中，包含首次有缺陷的包装入口，属于历史记录。修正版及精确命令保存在 `integration-tools-v2.zip` 和 `offline-validation-summary.json`；其中 `offline_tests.py` 为整批运行的 v2，`offline_tests_v3.py` 另调整验证临时目录。解压回新的仓库 `.tmp/zcode-integration/` 可检查原命令。Junit、日志和首次红例均保留，不掩盖失败。

v2 整批运行中的 preflight 路径断言禁止任何命令参数包含 `.pytest-tmp`，与本次包装脚本的父目录 `.pytest-tmp-zcode-*` 冲突。最小重现确认失败仅来自此断言；v3 将验证目录改为 `.tmp/zcode-integration/test-runs/` 后，单项通过，未改产品代码或测试。第一次 v3 尝试还因父目录尚未创建报错，补上父目录创建后通过；两次记录均保留。没有因验证目录调整重复整批测试，因此不将整批日志表述为全部一次通过。

## 恢复副本

归档位置：[`archive/zcode-local-20260905`](../../../archive/zcode-local-20260905/README.md)。

- 根目录、`w` 和重构成果：28,784 个文件按原始路径、大小和 SHA-256 归档；真实失败尝试保留。
- 补充：15 个 JSONfix/编译产物归档；另 3 个文件按哈希确认与已存子模块文件相同。
- 子模块：bim-whale 的 59 个文件和 ifc-bench 的 170 个文件均保留实际文件内容快照。
- 归档完整性：前述文件均逐文件重新解压读取并核对 SHA-256，无差异。
- 3,190 个新增来源 Git blob 的密钥扫描未发现问题；归档和补充包也分别扫描通过。
- 最终报告、日志及 ZIP 内脚本共 58 个内容条目再次扫描，未发现已知真实密钥或密钥格式匹配。
- 所有其他本地分支的提交都已被当前 Zcode 历史或既有 origin 引用覆盖，没有额外仅本地的分支提交。

`ifc-bench` 固定提交从 Hugging Face 独立抓取两次返回 HTTP 500，不能声称上游正常恢复。它的文件快照提供独立恢复路径，保留实际 IFC/LFS 文件；该快照不包含子模块 Git 历史。bim-whale 上游 fetch 成功，固定提交可达。

在全新目录浅克隆远程 Zcode，克隆 HEAD、本地 HEAD、`origin/Zcode` 均为 `28eb1540`，`git fsck --full` 通过。从最初为空的独立 LFS 存储下载 166 个对象，共 3,635,727,877 字节，逐对象 SHA-256 无差异，`git lfs fsck --objects HEAD` 通过。原有 `.git/lfs/objects` 没有作为这个恢复检查的数据来源。记录见 [remote-recovery-verification.json](remote-recovery-verification.json)。最后的报告提交将在完成后再次推送并核对。

## 排除项和用户授权清理

- 根目录 `.env`：用户明确表示不需保存；未打印、未提交。
- `.venv/`、`.deps/`、模型/检索缓存、生成的 target SQLite、EXPRESS parser cache、egg-info 和 pytest 临时产物不进入恢复归档。它们需要依赖安装或索引重建。
- 曾无法读取的 `w/.pytest-tmp/` 下 10 个目录，已通过 UAC 管理员只读检查。共 23 个文件均为生成测试输入/输出、临时数据库或零字节占位文件，没有真实 Provider 记录。
- 用户随后明确作出条件性测试内容清理授权。仅删除这 10 个目录；删除前再次校验绝对路径、完整文件集与 SHA-256。记录见 [admin-directory-inspection.json](admin-directory-inspection.json) 和 [authorized-test-cleanup.json](authorized-test-cleanup.json)。生成物未备份，检查内容和哈希已保留。
- 除上述明确授权的测试目录外，没有删除源文件、证据、worktree 或本地仓库。

## 本地删除结论及恢复边界

代码、原始来源、正式 Proof 和识别出的有价值证据已具备远程恢复副本，离线兼容检查已完成。没有发现仍需另行指定备份位置的有价值文件。最终报告推送并核对分支一致后，可以由用户亲自删除整个本地 `E:\code for project\bimnet-zcode`；本任务不会删除该文件夹。

这一结论是文件恢复结论：不表示旧重构架构已经兼容整合，也不表示真实 Provider 或全仓能力重新验收通过。恢复时需要重新安装依赖、重建缓存；`.env` 按用户决定不保留。ifc-bench 上游 Git 历史抓取仍受 HTTP 500 影响，必要工作文件通过本仓库的字节校验快照恢复。原始未跟踪归档来源和四项未提交删除仍保留在当前工作区，工作区并非干净，不能把它当作恢复是否完整的判断依据。
