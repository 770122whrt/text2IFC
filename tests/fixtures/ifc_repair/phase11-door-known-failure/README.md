# Phase 11 Door known-failure fixture

本目录永久保留 2026-07-29 审计前的 supplied vvo 三方文件，用于证明旧
Evaluator 的假阳性已经被回归测试封住。它不是成功案例，也不得作为生产
Target、Type、ChangeSet 或修复事实来源。

| 文件 | SHA-256 | 角色 |
|---|---|---|
| `01-original.ifc` | `b6c435be955aeb6b2998f42a62f4ebf8c3f91eb7d373ca71a2dcedfeb95b3fdc` | 私有 benchmark Ground Truth |
| `02-damaged.ifc` | `6824086b4171cce034acaa23ad51c3020d87ed44c0aead62979a4b4ad17c4db3` | 生产修复输入 |
| `03-known-failing-repaired.ifc` | `0d30005fa91360f186a6c539206aa1c229db03f69ac4d2e183a42c53db91a76e` | 旧 diagnostic candidate；不可发布 |

已确认的阻塞问题：

- 800×2480 Door 的世界几何中心相对 original 偏移
  `[+800,+160,0] mm`，只建立了 IFC fill 关系，没有正确填入洞口；
- 两个 repaired Door 均从应属的 `标高2` 错放到 `标高0`；
- occurrence Pset/Qto/material provenance 与 original 存在私有 fidelity
  差异，且旧报告没有把这些差异与生产 Manifest 要求分开。

自动回归入口：

```powershell
.venv\Scripts\python -m pytest tests\ifc_repair\test_door_geometry_regression.py -q
```

新的权威成功 proof 位于：

- `dataset/processed/proof/ifc-repair-success-cases/mixed/door-window/`
  `vvo-authority-triplet-public-repair/`，repaired SHA-256 为
  `9f5200e39accb3b496ac07c2f8d6079852acc871a7675014135afca6821f429d`；
- `dataset/processed/proof/ifc-repair-success-cases/door/batch/`
  `vvo-five-door-authority-public-repair/`，repaired SHA-256 为
  `a7e085242452f8b312173eb8aa11b08115971a4140f0a724e9850f5550270e03`。

两案的生产进程只接收 damaged IFC 与几何公开请求包；original 和本目录
private mapping 只在 repaired IFC 已生成后进入 comparator。不得与本目录的
旧 candidate 混用。
