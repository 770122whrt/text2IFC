# Phase 12 Plan 07 — window-semantic-canary

## 结论

- final-code frozen contract：**PASS**
- genuine Provider calls（Stage 1 / Property Resolution / Stage 2）：`1/1/1`
- runtime run：`repair-1ee9e411b9fc44308dfb2f9c17c002f8`
- L0 / L1 / L2：`PASS / PASS / PASS`

## 请求与结果

公共请求见 [request.txt](request.txt)。

- 语义/模型结果：从当前 offered set 选择 IsExternal authority，并保持 occurrence-only 语义。
- 确定性执行结果：只修改指定 Window occurrence，不修改 Type 或其他 Window。
- 独立检查：1 operation；IFC2X3 reopen、L0/L1/L2 与 preservation 均 PASS。

## 直接产物

- [damaged.ifc](damaged.ifc)
- [repaired.ifc](repaired.ifc)

## 证据边界

本案没有运行前冻结的 case-specific private property mutation truth；共享 pristine 不能事后改标为本案 Gold，故不复制 original.ifc。

完整 genuine Provider、Prompt/profile、intent、resolution、admissibility、Stage 2、apply、terminal 与 evaluation 证据在 [final-code 机器案例目录](../../uat-20260902T180900748385Z/raw-run/cases/window-semantic-canary/)。快速导航见 [evidence/README.md](evidence/README.md)。
