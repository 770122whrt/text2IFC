# formal-020 答复明确后的组合执行检查

这是离线确定性检查，未调用模型、未生成问题、未观察真人回复；不证明自然澄清、检索、恢复或四组准入。

输入只有本目录damaged.ifc、原request-initial.txt和明确模拟的simulated-answer.json。选择身份从公开D实际几何获得，不用私有目标Name/GUID；source G首次解析在发布后，只供独立比较。

主结果result.json；真实既有exact resolver、semantic-manifests.json、bound-draft.json、changeset.json和application/evaluation/comparison记录完整保留；最终repaired.ifc仅在生产评价及保全通过后发布。

independent-public-requirements.json核对洞口世界位置/高度、名义尺寸、实际参照网格、楼层及唯一IfcBoolean(true)。injected-atomic-rollback.json为明确注入的第二操作失败，不发布部分补窗。

[主结果](result.json) · [实际几何和属性核验](independent-public-requirements.json) · [R 原生格式检查](native-validation.json) · [注入失败回滚](injected-atomic-rollback.json) · [全部原有属性保全](existing-property-preservation.json) · [原始日志](run.log) · [进程收据](run-receipt.json) · [材料索引](evidence-index.json)。

所有必要输入、清单、绑定产物、应用/评价、实际 D 网格基线和 R 已随本目录保留。源 G 沿本题的 ../../reference.ifc 仅供发布后评价，完整 role/fingerprint 见记录；机器日志中的绝对路径是原运行定位，不是唯一材料入口。

临时 helper 的 [版本选择失败](failed-helper-binding/README.md) 和 [指纹前缀比较失败](failed-helper-index-prefix/README.md) 均保留原源码/错误/log/receipt。修正没有改变生产契约；这些记录不是模型成绩。
