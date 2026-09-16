# 本轮准确删除清单

本清单不含正式 Proof、真实 Provider 历史、生产测试源码、依赖缓存或活动工作树。现有回归测试保留；这里只删除可重建的测试输出、空目录及已提交的相同日志副本。

| 路径（相对仓库根） | 文件数 | 字节 | 依据 |
|---|---:|---:|---|
| `composite-evidence-setsem-01` | 6 | 43577 | Deterministic fixture Provider outputs; reproduced by tests/ifc_repair/test_draft_authority_set_semantics.py |
| `composite-evidence-setsem-02` | 6 | 43577 | Deterministic fixture Provider outputs; reproduced by tests/ifc_repair/test_draft_authority_set_semantics.py |
| `composite-evidence-setsem-03` | 6 | 43577 | Deterministic fixture Provider outputs; reproduced by tests/ifc_repair/test_draft_authority_set_semantics.py |
| `composite-evidence-setsem-drift-evidence-duplicate-ref` | 6 | 43814 | Deterministic fixture Provider outputs; reproduced by tests/ifc_repair/test_draft_authority_set_semantics.py |
| `composite-evidence-setsem-drift-evidence-extra-ref` | 6 | 43637 | Deterministic fixture Provider outputs; reproduced by tests/ifc_repair/test_draft_authority_set_semantics.py |
| `composite-evidence-setsem-drift-evidence-missing-ref` | 6 | 43518 | Deterministic fixture Provider outputs; reproduced by tests/ifc_repair/test_draft_authority_set_semantics.py |
| `composite-evidence-setsem-drift-scope-duplicate-target` | 6 | 43683 | Deterministic fixture Provider outputs; reproduced by tests/ifc_repair/test_draft_authority_set_semantics.py |
| `composite-evidence-setsem-drift-scope-extra-target` | 6 | 43603 | Deterministic fixture Provider outputs; reproduced by tests/ifc_repair/test_draft_authority_set_semantics.py |
| `composite-evidence-setsem-drift-scope-missing-target` | 6 | 43551 | Deterministic fixture Provider outputs; reproduced by tests/ifc_repair/test_draft_authority_set_semantics.py |
| `.pytest-tmp` | 27 | 3668439 | Rebuildable pytest workspace/cache |
| `.pytest-tmp-ifc-audit-migration` | 7 | 1106 | Rebuildable pytest workspace/cache |
| `.pytest-tmp-incoming-ifc` | 3 | 620 | Rebuildable pytest workspace/cache |
| `.pytest_cache` | 5 | 160567 | Rebuildable pytest workspace/cache |
| `dataset/processed/review` | 0 | 0 | Empty directory |
| `docs/reports/main-integration-20260912/zcode-on-current-baseline.local-preserved.txt` | 1 | 50952 | Byte-identical log retained in committed main report |

共 15 个目标、97 文件、4274221 字节。逐文件尺寸见 deletion-proposal.json；执行前重新检查路径、文件集合、链接及尺寸，变化即停止。
