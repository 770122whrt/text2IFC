# Phase 12 / 12.1 Beam、Column 与 Property Resolution 最终验证报告

> 2026-09-07 导航更新：证据已集中到 [工作流 Proof](../../../dataset/processed/proof/README.md)，旧路径见集合 manifest 的 legacy_bundles。Plan07 已获用户人工审查通过；下文日期、原运行结论与冻结记录仍表示历史事实。


## 结论

Phase 12 与插入修复阶段 Phase 12.1 已通过冻结验收并闭合。最终依据是连续、未拼接的
genuine run `r1-20260902T152701658266Z`、独立 R1 Proof 0.3、既有合法私有三元组的
IFCCompare/collection 0.2 复核，以及冻结回归。OPS-03、OPS-04 与 RAG-05..07 完成；
Phase 13 未启动。

## 能力边界

闭合声明覆盖：

- Beam/Column 注册操作、确定性 Type 生成或精确已有 Type 复用；
- placement、Storey containment、几何、关系、属性与 preservation 的 L0/L1/L2；
- Window、Door、Wall、Beam、Column occurrence 的 alias-free Property Resolution；
- Stage 1.5 只能从 authoritative Top-K 选择，程序复核 offered-set、class、template、
  value type、unit、scope 后构建 ExactPropertyIntent；
- 多操作原子 apply/publish 和 unsupported whole-transaction guard；
- damaged/source 输入与 pristine/private Gold 隔离。

本报告不把 R1 的 diversity 模型提升为有 private Ground Truth 的 IFCCompare
benchmark；它们合法 triplet 数为 0。也不把一次 live run 解释为全域模型能力提升。

## 运行与 Proof

| Gate | Result |
|---|---|
| Frozen R1 ordered genuine run | 12/12 PASS；40 calls，17/12/11 |
| Final-code Plan 07 compatibility run | 4/4 PASS；11 calls，4/4/3 |
| Repaired outputs | 11；全部独立 reopen，L0/L1/L2 PASS |
| Unsupported H4 | PASS；1/0/0，零 mutation、零 publish、无 repaired IFC |
| Proof validation 0.3 | PASS；12 cases、13 ops、785 files、23 reopens |
| Independent recomputation | 12/12；H4 计为合法 no-output recomputation |
| Proof errors / limitations | 0 / 0 |
| Existing truth-bearing IFCCompare | 12/12 publishable triplet audits |
| R1 IFCCompare | N/A，0 个合法 private triplet，未伪造 Gold |
| Focused final admission | 208 passed；无 failure/skip/timeout/network |

Plan 07 原 validation 0.2 仍是其独立 Proof。最终代码四案没有声明第二份 curated
Proof：curator 对 changed-scope admission 的证据复制尚不兼容，尝试停在
`LIVE_PREFLIGHT_EVIDENCE_MISSING`。该限制只影响归档打包；四案 live contract、三个
repaired IFC 的 reopen/L0/L1/L2 和 unsupported guard 均已通过。

## H3 与 H4 解释

H3 原因是 Window/Door filling 的 overall dimensions 与 hosted opening 的普通
dimensions 使用不同索引键，随后又叠加 exact zero-tolerance 的单位浮点噪声。通用
修复统一了 opening-size 查询读取与毫米清洗；错误尺寸仍被排除，offered-set identity
校验未变。最终 H3 经过候选提供、稳定身份澄清/续跑、Stage 1.5、Stage 2、apply、
reopen 和 Proof，全部通过。

H4 没有 repair 是冻结语义要求，不是执行缺失：同一原子请求中含不支持的结构分析
工作，因此不能只执行支持的 Beam 子操作。系统在 Stage 1 后以
`STRUCTURAL_ANALYSIS_UNSUPPORTED` 停止，Stage 2=0、mutation=false、输出路径为空、
source SHA 不变。任何 repaired IFC 都会反而违反 H4 合同。

## 证据路径

- [最终 12 案 Proof Matrix](../repair-milestone-r1/repair-proof-matrix-2026-09-03.md)
- [R1 执行结果](../../../dataset/processed/proof/repair/phase12.1/r1/evidence/run-original/r1-execution-result.json)
- [Curated Proof 0.3](../../../dataset/processed/proof/repair/phase12.1/r1/evidence/frozen/PROOF-VALIDATION.json)
- [IFCCompare/collection summary](https://github.com/770122whrt/text2IFC/blob/11f29030f3f3b5967535d16c4c4b31085e21ff64/dataset/processed/experiments/phase-history-20260912/ifc-repair-runs--repair-milestone-r1.zip)
- [最终代码 Plan 07 四案](https://github.com/770122whrt/text2IFC/blob/11f29030f3f3b5967535d16c4c4b31085e21ff64/dataset/processed/experiments/phase-history-20260912/ifc-repair-runs--phase12-live.zip)

上方两份已退役运行记录的链接指向原 ZIP；成员分别为 `r1-final-ifccompare-20260903/validation-summary.json` 和 `uat-20260902T180900748385Z/live-uat-result.json`，路径/哈希由[历史映射](../../../dataset/processed/experiments/phase-history-20260912/manifest.json)维护。

历史 Plan 07 顶层 false/pending 字段保持不变。最终资格由上述追加证据闭合，不对旧
Proof 或 genuine attempt 做重标记。

## 历史调试与负面证据（2026-08-24—28）

以下是最终闭合前的独立历史记录，不与上方 R1 或 Plan 07 四案合并计算。旧的
跨对话快照不再承担当前状态或接管规则；当时的完整排查、被拒中间结果和逐案
原始响应分别保留在固定 Git 修订中的[问题记录](https://github.com/770122whrt/text2IFC/blob/48f32bba4c1976178a97267a98e569080f44063e/docs/context-handoff/ISSUE-CONTEXT__2026-08-24__stage15-bge-curator-contract-failures.md)
和[六例失败 dossier](https://github.com/770122whrt/text2IFC/blob/48f32bba4c1976178a97267a98e569080f44063e/docs/context-handoff/ISSUE-EVIDENCE__2026-08-28__stage15-postfix-six-failures.md)。

### 集成问题与被拒证据

- Stage 1.5 接入时，真实 BGE/Qdrant 运行依赖、live transcript 的 Stage 1.5
  身份／调用计数，以及 validator 与 curator 的当前属性证据字段未完整衔接。
  后续分别补齐生产运行时工厂、可注入的离线测试接缝、独立 readiness、真实
  attempt 链和 Proof 字段；离线测试接缝不能代替真实向量运行时或 Provider 证据。
- 曾用 answer-equivalent replay 补足 Stage 1.5 语义 Candidate，该中间准入被
  独立复审拒绝，回放答案表随后移除。另一个早期检索生产器在公开 ledger 持久化
  前打开了含 Gold 的 fixture，因此过程隔离也不成立。最终 Plan 06 改为仅加载
  public fixture、真实检索并先保存 Top-K，之后 scorer 才能打开 Gold；其离线
  Stage 1.5 语义状态明确为 `not_evaluated_offline`。这些纠正不把被拒结果改成有效结果。
- v0.1 真实语义运行 `semantic-20260827T160906604981Z` 为 59/60，包含 `n06`
  的一次 false authorization：模型承认候选只是相关解释，仍确认了该候选。
  原因定位为语义授权越界；后续 Prompt／语义合同 v0.2 要求欠明确但可能可修复的
  目标先澄清，不靠 alias、关键词或个案分支代替模型判断。

### v0.2 后修复验收仍失败

独立运行 `post-fix-semantic-20260828T092301205242Z` 冻结全部 60 条预测后才打开
Gold。严格路由结果为 **54/60，验收 FAILED**；confirmed 的 offered-candidate
选择正确率为 1.0，false authorization 为 0。澄清 1/2、unsupported 1/2、
deterministic-inadmissible 8/12，均保留各自冻结分母。

| 案例 | 冻结预期 | 实际终态与保留的失败事实 |
|---|---|---|
| `n05` | unsupported | Provider 返回 clarification；未知属性被当成可澄清目标 |
| `p12w04` | deterministic inadmissible | Provider 返回 clarification，未进入值类型拒绝 |
| `p12d04` | deterministic inadmissible | Provider 返回 clarification，未进入值类型拒绝 |
| `p12m04` | clarification | Provider 返回 unsupported，未澄清欠明确的可支持目标 |
| `p12b04` | deterministic inadmissible | Top-K 为空，Provider 未调用，直接路由到 unsupported；空集原因未持久化，不能补造归因 |
| `p12c04` | deterministic inadmissible | 所给 Top-K 未含 `LoadBearing`，Provider 返回 unsupported，未进入值类型拒绝 |

六例均未授权写入。五例是真实 Provider 的终态路由不符，一例是未调用 Provider
的检索／路由不符；不能把六例都算成模型选择错误。全轮有 31 次 genuine
`deepseek-v4-flash` 调用，thinking enabled，0 retries；消耗 74,923 prompt、
20,061 completion、共 94,984 token。没有 malformed、unoffered selection、私有
泄漏、false publication 或 IFC 写入。由于硬门失败，当时没有启动四案 E2E、Stage 2、
Proof curation 或 IFCCompare。v0.1 与 v0.2 的合同／分类版本不同，且已观察同一批题；
false authorization 从 1 到 0 不能推导为整体能力提升，后来的 R1 通过也不改写本轮失败。

### 原始机器记录与恢复

预测 ledger 的 SHA-256 为
`bd7d0ed46bdde3febbafa1287c1ec81dfdf1d4e39c3262475b7ee4d38593cadd`，语义报告为
`0d546f49569e800150b248e28b8e8b0794e21f2a85fa5ce021db9594fe5f6f5a`。
[既有历史映射](../../../dataset/processed/experiments/phase-history-20260912/manifest.json)
将旧根 `dataset/processed/ifc-repair-runs/phase12-1-semantic-evaluation` 下的
ledger、报告和逐案 Provider 输入／输出映射到
`ifc-repair-runs--phase12-1-semantic-evaluation.zip` 的原成员，并保留逐文件哈希。
该 ZIP 已按[统一 Git/LFS 恢复说明](../../../dataset/processed/experiments/README.md#repair-旧材料按需从-git-恢复2026-10-10)
退出本地工作目录；完整原包从[固定修订 11f29030](https://github.com/770122whrt/text2IFC/blob/11f29030f3f3b5967535d16c4c4b31085e21ff64/dataset/processed/experiments/phase-history-20260912/ifc-repair-runs--phase12-1-semantic-evaluation.zip)
按需恢复，不把本段摘要当作原始机器证据，也不复用历史准入运行当前代码。
