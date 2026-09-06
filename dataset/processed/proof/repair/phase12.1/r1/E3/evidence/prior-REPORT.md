# Repair Milestone R1 — E3

## 结论

- 冻结案例结果：**PASS**
- terminal class：`SUCCESS`
- genuine Provider calls（Stage 1 / Property Resolution / Stage 2）：`1/1/1`
- L0 / L1 / L2：`PASS / PASS / PASS`

## 请求与结果

公共输入请求见 [request.txt](request.txt)。

- 语义/模型结果：选择 Beam occurrence 的 Reference=B-204。
- 确定性执行结果：严格按 occurrence scope 写入属性。
- 独立 Proof 结果：IFC2X3 reopen、L0/L1/L2、occurrence scope 与 preservation 均 PASS。

## 直接产物

- [damaged.ifc](damaged.ifc)
- [repaired.ifc](repaired.ifc)

## 证据边界

R1 没有运行前冻结的 case-specific pristine/private Ground Truth；因此 original.ifc 不存在，IFCCompare 为 N/A。

完整 Provider attempts、Prompt/profile、intent、resolution、admissibility、ChangeSet、apply、terminal 与 Proof 文件保持在 append-only 的 [机器权威案例目录](../../r1-20260902T152701658266Z-curated/cases/E3/)。快速导航见 [evidence/README.md](evidence/README.md)。
