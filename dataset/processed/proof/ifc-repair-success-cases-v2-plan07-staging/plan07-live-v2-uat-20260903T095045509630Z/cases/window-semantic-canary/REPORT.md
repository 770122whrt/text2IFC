# window-semantic-canary

证据结论：**通过**。对既有 Window occurrence 写入外窗属性；这是 property repair，所以有 repaired.ifc，但不会创建 Beam 或 Column。

- Provider/model：`deepseek-openai-compatible / deepseek-v4-flash`
- Provider calls：`3`
- Runtime run ID：`repair-dfddefc5afde41b7878505aa10d62519`
- Operations：`1`
- original / damaged / repaired 已独立重开为 `IFC2X3`
- 独立 L1/L2 operations：`1/1`
- `original.ifc` 是评估后引入的共享损伤前来源，未发送给 Provider。
- Phase acceptance 仍由冻结 Plan 12/14 Proof gate 决定。
