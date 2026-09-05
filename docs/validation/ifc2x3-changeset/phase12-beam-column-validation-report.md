# Phase 12 / 12.1 Beam、Column 与 Property Resolution 最终验证报告

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
- [R1 执行结果](../../../dataset/processed/ifc-repair-runs/repair-milestone-r1/r1-20260902T152701658266Z/r1-execution-result.json)
- [Curated Proof 0.3](../../../dataset/processed/proof/repair-milestone-r1/r1-20260902T152701658266Z-curated/PROOF-VALIDATION.json)
- [IFCCompare/collection summary](../../../dataset/processed/ifc-repair-runs/repair-milestone-r1/r1-final-ifccompare-20260903/validation-summary.json)
- [最终代码 Plan 07 四案](../../../dataset/processed/ifc-repair-runs/phase12-live/uat-20260902T180900748385Z/live-uat-result.json)

历史 Plan 07 顶层 false/pending 字段保持不变。最终资格由上述追加证据闭合，不对旧
Proof 或 genuine attempt 做重标记。
