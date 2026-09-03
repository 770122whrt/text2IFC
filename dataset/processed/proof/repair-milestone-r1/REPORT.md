# Repair Milestone R1 最终人类评估

## 总结

- 最终连续 acceptance run：`r1-20260902T152701658266Z`
- 冻结案例：`12/12 PASS`
- genuine Provider calls：`40`（Stage 1=`17`，Property Resolution=`12`，Stage 2=`11`）
- repaired IFC：`11`
- 正确的 no-output guard：`1`（H4）
- 独立 Proof：`proof-validation 0.3` PASS；12 个 case、13 个 operations、785 个文件、23 次 IFC reopen、12 次独立复算
- R1 IFCCompare：`N/A (0/12)`，因为没有运行前冻结的 case-specific private pristine/damaged/repaired truth；不事后制造 Gold

## 12 案矩阵

| 案例 | Calls S1/PR/S2 | terminal class | 直接产物 | 独立 Proof |
|---|---:|---|---|---|
| [E1](accepted-cases/E1/REPORT.md) | 1/1/1 | SUCCESS | repaired.ifc | PASS |
| [E2](accepted-cases/E2/REPORT.md) | 2/1/1 | SUCCESS | repaired.ifc | PASS |
| [E3](accepted-cases/E3/REPORT.md) | 1/1/1 | SUCCESS | repaired.ifc | PASS |
| [E4](accepted-cases/E4/REPORT.md) | 1/1/1 | SUCCESS | repaired.ifc | PASS |
| [M1](accepted-cases/M1/REPORT.md) | 3/2/1 | INADMISSIBLE_VALUE_OR_CLARIFICATION | repaired.ifc | PASS |
| [M2](accepted-cases/M2/REPORT.md) | 1/1/1 | SUCCESS | repaired.ifc | PASS |
| [M3](accepted-cases/M3/REPORT.md) | 2/1/1 | SUCCESS | repaired.ifc | PASS |
| [H1](accepted-cases/H1/REPORT.md) | 1/1/1 | SUCCESS | repaired.ifc | PASS |
| [H2](accepted-cases/H2/REPORT.md) | 1/2/1 | SUCCESS | repaired.ifc | PASS |
| [H3](accepted-cases/H3/REPORT.md) | 1/1/1 | CLARIFICATION_THEN_SUCCESS | repaired.ifc | PASS |
| [H4](accepted-cases/H4/REPORT.md) | 1/0/0 | UNSUPPORTED_ATOMIC_GUARD | no output（按合同） | PASS |
| [A1](accepted-cases/A1/REPORT.md) | 2/0/1 | SUCCESS | repaired.ifc | PASS |

## H3 修复说明

H3 的失败不是 frozen fixture 错误，也不是 clarification identity 绑定器放松。根因是 opening/filling 目标索引在 hosted-opening dimension 缺失时，没有使用 filling occurrence 的 OverallWidth/OverallHeight，导致合法 Window 被几何过滤器排除，offered candidate set 为空。

生产修复让 opening width/height predicate 在 hosted-opening key 缺失时读取 filling overall-dimension，并统一通过 `_clean_mm` 处理毫米浮点噪声。它是通用的 filling geometry fallback：错误尺寸仍排除、已有 hosted-opening 行为不变、currently-offered candidate 校验不变；生产代码中没有 H3 GlobalId、冻结尺寸、case id 或 phrase 特判。

## H4 与没有 repaired IFC 的含义

H4 同时请求可支持的 Beam 编辑和不支持的 structural-analysis node。冻结合同要求原子处理，不能只发布一半。因此零 mutation、零 publish、无 repaired IFC 是 PASS 条件。详细证据见 [H4 报告](accepted-cases/H4/REPORT.md)。

## 证据与限制

每案的人类目录只放最必要的输入、输出和说明；完整过程证据继续由 append-only 机器包承载。R1 证明 live Provider 语义、确定性执行、产物、preservation 与 evidence contract；它不提供不存在的 private triplet truth，也不把 curator/terminal self-report 当成独立验证。
