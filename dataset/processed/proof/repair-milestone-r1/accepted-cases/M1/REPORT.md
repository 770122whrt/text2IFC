# Repair Milestone R1 — M1

## 结论

- 冻结案例结果：**PASS**
- terminal class：`INADMISSIBLE_VALUE_OR_CLARIFICATION`
- genuine Provider calls（Stage 1 / Property Resolution / Stage 2）：`3/2/1`
- L0 / L1 / L2：`PASS / PASS / PASS`

## 请求与结果

公共输入请求见 [request.txt](request.txt)。

- 语义/模型结果：非法 Boolean 值先被阻止；补充用户信息后以 EI60 和稳定 property identity 恢复。
- 确定性执行结果：失败路径零 mutation，resume 路径成功写入。
- 独立 Proof 结果：IFC2X3 reopen、L0/L1/L2、clarification lineage、admissibility 与 preservation 均 PASS。

## 直接产物

- [damaged.ifc](damaged.ifc)
- [repaired.ifc](repaired.ifc)

## 证据边界

R1 没有运行前冻结的 case-specific pristine/private Ground Truth；因此 original.ifc 不存在，IFCCompare 为 N/A。

完整 Provider attempts、Prompt/profile、intent、resolution、admissibility、ChangeSet、apply、terminal 与 Proof 文件保持在 append-only 的 [机器权威案例目录](../../r1-20260902T152701658266Z-curated/cases/M1/)。快速导航见 [evidence/README.md](evidence/README.md)。
