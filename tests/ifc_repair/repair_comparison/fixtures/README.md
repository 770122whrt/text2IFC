# B 米制门尺寸错误：修复前离线证据

`door-metre-before-fix.json` 保留 2026-09-29、生产修复前的原生失败记录原字节。输入是开发 case-002 的公开 D，使用固定假 Intent 和由原生公共投影生成的 Stage2 响应；没有真实模型调用，也没有读取私有 G。

当时生产基线为 `d2e74160`，`semantic_authoring.py` 尚未修改。证据来自 `RepairAPI` 的终态 `terminal/evidence.json`，保留 `UNIFIED_TRANSACTION_FAILED` 对应的应用检查：几何门宽864mm，但语义写回把名义门宽变为864000mm，宽偏差863136mm；失败回滚，源IFC哈希前后一致。此文件是诊断回归证据，不是模型成绩、accepted Proof或完整原生运行目录。

对应当前测试为 `test_ours_adapter.py::test_native_real_metre_door_repair_and_preserved_before_fix_evidence`：同时保留旧失败事实，并检验修复后的相同米制D可以由原生API发布、回读0.864m×2.032m。不要用后续成功覆盖本文件。
