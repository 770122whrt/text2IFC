# IFC Repair Proof 人类可读收纳规范

本文定义 BimNet 已接受 IFC repair Proof 的标准展示格式。它解决两个问题：人应当能在几次点击内找到请求、输入、输出和结论；机器仍应能从不可变的权威包复算完整证据。

本规范不替代 phase SPEC、冻结 acceptance contract、Proof validator 或 `docs/validation/agent-capability-evaluation.md`。发生冲突时，适用的冻结合同和验证协议优先。

## 1. 两层证据模型

每个正式集合分为两层：

1. **人类可读视图**：集合根目录的 `README.md`、`REPORT.md`、`manifest.json` 和 `accepted-cases/`。它负责导航、解释、直接展示必要 IFC。
2. **机器权威包**：既有 curator/proof/run package。它保存 Provider attempts、Prompt/profile、intent、resolution、candidate/admissibility、ChangeSet、apply、terminal、evaluation、hash 和独立复算结果。

人类视图是 additive discovery layer，不移动、不重命名、不改写 accepted machine authority。二者若有差异，必须停止发布并调查；不能靠修改报告掩盖差异。

## 2. 标准目录

```text
<collection>/
├── README.md
├── REPORT.md
├── manifest.json
├── accepted-cases/
│   └── <case-id>/
│       ├── REPORT.md
│       ├── request.txt
│       ├── damaged.ifc
│       ├── repaired.ifc          # 仅成功修复案
│       ├── original.ifc          # 仅在角色合法且明确时
│       ├── NO-REPAIR.md          # 仅预期无输出案
│       └── evidence/
│           └── README.md         # 指向完整机器权威
└── <machine-authority>/
    └── ...
```

案例根目录只放审阅者首先需要的文件。庞大的 Provider/runtime 树不再复制到 `accepted-cases/`，而由 `evidence/README.md` 给出短路径。

## 3. 文件角色

### 集合级文件

- `README.md`：最短阅读路径、权威包位置、最重要的边界说明。
- `REPORT.md`：面向人的总结、逐案矩阵、失败或 no-output 解释、限制。
- `manifest.json`：机器可读的人类视图索引；schema 为 `text2ifc/human-proof-collection/0.1`。

### 案例级文件

- `REPORT.md`：结论、Provider call count、语义结果、确定性执行、产物、Proof 结论和限制。
- `request.txt`：实际公共 repair request；不含 private Gold、mutation truth 或 pristine-only facts。
- `damaged.ifc`：实际进入 production repair path 的输入。
- `repaired.ifc`：成功发布并可 reopen 的修复输出。成功案必须直接可见。
- `original.ifc`：可选。只有在 original 角色在运行前已经合法定义时才允许出现。
- `NO-REPAIR.md`：预期无输出案必须解释为什么没有 repaired IFC，以及零 mutation/零 publish 的证据。
- `evidence/README.md`：连接到完整 append-only authority，不建立新的真值。

## 4. original 与三元组规则

`original.ifc` 必须声明下列角色之一：

- `private_ground_truth`：运行前冻结、evaluator-only、具有合法 pristine/damaged/repaired truth，可用于相应 IFCCompare。
- `physical_fixture_non_private_audit`：三份物理 IFC 均存在，便于人工或结构审计，但不能声称 private triplet-audit publishable。

如果没有运行前冻结的 case-specific private truth，就不复制 `original.ifc`，并把 IFCCompare 明确写为 N/A。不能在看到 repaired 后再把共享 pristine、相似文件或人工挑选文件改标为 Gold。

## 5. no-output 案例

guard、unsupported 或原子回滚案例的正确结果可能是没有 repaired IFC。这类案例必须：

- `outcome=no_output`；
- 存在 `damaged.ifc` 与 `NO-REPAIR.md`；
- 不存在 `repaired.ifc`；
- 报告 Stage 2/apply/publish 是否为零、source 是否不变，以及适用的 reason code；
- 将 L0/L1/L2 标为 N/A，而不是伪造 PASS。

如果 no-output 案目录出现 repaired IFC，应当 fail closed。

## 6. 报告的最小内容

每份案例报告至少回答：

1. 用户请求是什么；
2. Provider/模型做了什么选择，调用次数是多少；
3. 确定性代码实际应用或阻止了什么；
4. repaired IFC 在哪里，或者为什么必须没有；
5. reopen、L0/L1/L2、authority、atomicity、preservation 的结果；
6. IFCCompare 是否适用；若不适用，缺少哪一种合法 truth；
7. 完整机器权威在哪里。

报告以人能管理和阅读为首要目标。JSON 用于索引和自动化，不应成为理解案例结论的唯一入口。

## 7. 风险对应的验证

验证应针对本次变化可能引入的真实失败，而不是看到 Proof 就普遍重复全部 curator。

| 变化 | 最小必要验证 |
|---|---|
| 仅改报告文字或导航链接 | 链接/声明路径存在；不需要 curator |
| 新增或刷新 human view | human-layout validator：必需文件、角色、authority path、IFC reopen、成功/no-output 互斥 |
| 修改 repaired/original/damaged 文件或角色 | human-layout validator，加适用的 source/triplet/Proof artifact check |
| 修改 production repair 行为 | 冻结失败族、聚焦回归、适用 full-chain offline、phase validation contract |
| 新 live Provider acceptance run | 完整 live admission/preflight 与保留所有 attempts |
| 安装或重新整理 accepted machine collection | 对应 curator 与独立 Proof validator |
| 修改 curator、Proof schema、evidence semantics | curator/validator 回归和受影响 collection 重验 |
| 明确 release/milestone audit 要求 | 按冻结计划运行完整门槛 |

full curator 的典型触发条件只有：新 accepted run 安装、re-curation、curator/schema/evidence semantics 变化，或冻结计划明确要求的 release audit。它不因 README、案例导航或人类报告更新而自动触发。

风险对应不等于降低门槛。成功案缺 repaired、no-output 案出现 repaired、original 角色不明、authority 不可达、IFC 无法 reopen、source mutation 或适用冻结安全门失败，都必须阻止发布。

## 8. 当前验证入口

```powershell
.venv\Scripts\python scripts\ifc_repair\validate_human_proof_layout.py --root dataset\processed\proof\repair-milestone-r1 --json
.venv\Scripts\python scripts\ifc_repair\validate_human_proof_layout.py --root dataset\processed\proof\phase12-plan07-final --json
.venv\Scripts\python -m pytest tests\ifc_repair\test_human_proof_layout.py -q
```

这些命令验证人类视图的可发现性和角色安全，不冒充 semantic capability evaluation，也不替代原机器包已经要求的独立 Proof。
