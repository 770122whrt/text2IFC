# C3 损坏与修复对照

本案为Zcode已接受的历史真实Provider结果，本次只整理展示，不重新调用模型、不改变验收状态。历史机器结果为 `passed`，真实调用记录为 2 次；本次调用为0次。

先读 [用户输入](request.txt)，再对照 [原始模型](01-original.ifc)、[损坏输入](02-damaged.ifc)、[修复输出](03-repaired.ifc)。原始模型是运行前冻结的损坏基准，仅供事后评价，未作为Provider输入。

细节和构件GUID对应见 [原报告](../evidence/frozen/C3/REPORT.md) 与 [完整证据入口](evidence/README.md)。原focused IFCcompare通过，整个模型GlobalId并非完全相同；不能据本案声称系统级能力提升。本轮完整curator复核与历史验收分开记录。
