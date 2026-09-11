# phase12-plan07-live-window-property-repair

## 结论

本案例通过。真实 DeepSeek Provider 输出经过确定性解析、绑定、apply、发布并重新打开 repaired IFC。

- Provider/model：deepseek-openai-compatible / deepseek-v4-flash
- Provider calls：3
- Runtime run ID：repair-dfddefc5afde41b7878505aa10d62519
- Operations：1
- Operation types：set_occurrence_properties
- L0/L1/L2：True / True / True
- Evidence validation：passed

## 最短检查路径

1. 打开 01-original.ifc、02-damaged.ifc、03-repaired.ifc。
2. 阅读 input/request.txt；澄清案例另有 input/clarification-answer.txt。
3. 查看 agent/repair-intent.json、agent/target-resolution.json 与 agent/provider-attempts.json。
4. 查看 changeset/bound-changeset.json。
5. 查看 validation/evidence-decision.json、validation/production-evaluation.json；结构案例另看 validation/structural-restoration-audit.json。
6. 通过 [evidence/README.md](../evidence/README.md) 回到完整机器权威包。

## original 与 IFCCompare 边界

01-original.ifc 的角色是 physical_fixture_non_private_audit：它用于人工结构/物理对照，未发送给 Provider，也不被事后改称 case-specific private Ground Truth。因此本案例不声称 publishable private IFCCompare。当前目录证明 genuine Provider execution 和 case-local L0/L1/L2；Plan 07 是否最终接受等待本次人工检查，R1 不在此目录范围内。
