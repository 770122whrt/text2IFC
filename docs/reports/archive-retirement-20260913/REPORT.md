# archive 退役与 Zcode 重构参考收纳

日期：2026-09-13。用户批准按已讨论方向处理根 `archive`，保留 Proof 中的重要内容。当前工作分支为 `codex/workflow-dataset-links`；基线 `d1639232`。本轮不合 main、不做生产重构或 Provider 调用。

后续指示：用户明确要求将有价值的 Zcode 重构实际接入当前代码。接下来逐项实施评估拆分、Proof 包提取和 runner 整理；本报告只记录已完成的 archive 退役，不把参考包保留当作重构实施完成。

## 当前执行状态

**已完成退役。** 保留包提交 `dbb94668734c69075c9a3113e30fbba63fd3b2b8` 已普通推送且远端 SHA 一致，随后按清单删除 18 个旧文件／2,688,981,263 字节和三个空目录，根 archive 已不存在。逐文件回执见 [deletion-result.json](deletion-result.json)。本报告随最终删除／导航收尾提交发布；main 未在本轮同步。

准备完成时轻量包总计 1,935,939 字节（约 1.85 MiB）。移除量是当前工作目录的逻辑文件字节，不包含 `.git/lfs` 存储或另一 main 工作树的副本，也不代表 GitHub LFS 历史占用下降。

## 保留了什么

- 当前所有 Proof 保持原位置和历史状态。针对 archive 的引用搜索未发现 Proof 文本直接引用这六个 ZIP；C1–C5 的现行 manifest 和文件仍使用集合内路径。
- 原 18 个文件共 2,688,981,263 字节；六个大 ZIP 以固定 Git/LFS 修订保留，恢复记录覆盖全部文件，不只成功案例。
- [轻量入口](../../../dataset/processed/experiments/zcode-history-20260913/README.md)保留原历史合同、压缩后的原清单和有价值的重构差异。两个新 ZIP 共 1,833,787 字节，成员均与原来源逐字节核对；不复制全部旧数据和未变化代码。
- 66 份变更 Python 与 37 份文档仅作参考。已被当前导航替代的内容不再引入；生产／benchmark 分离和 Proof 包提取留作后续有界候选，整套旧镜像不再等待合并。
- 原历史 v0.12 Prompt 的字节不变，仅将 `tests/ifc_repair/test_repair_intent_prompt_v012.py` 的读取位置改到新包；当前生产 registry 不变。

## 删除与恢复范围

[准确文件清单](DELETE-LIST.md)与[机器清单](delete-list.json)仅包含根 `archive/zcode-local-20260905/` 的 18 个原文件，以及删除后为空的三级目录。Proof、experiments 既有集合、`.git/lfs`、子模块、其他未跟踪内容和活动 main 工作树不在范围内。

旧路径从新包的 [recovery-index.json](../../../dataset/processed/experiments/zcode-history-20260913/recovery-index.json)定位。固定历史修订为 `d1639232f74e4108f3242c46162bcd91bf0909fe`，已被远端工作分支历史包含。历史报告中的 archive 路径不改写；在固定修订或恢复工作区阅读原记录。

## 验证与边界

| 检查 | 结果 |
|---|---|
| 路径修改前原回归 | 1 passed，1.30 秒；不是新能力实验 |
| 路径修改后同一回归 | [1 passed，1.17 秒](focused-tests.xml)，原有正反断言不变 |
| 原 archive 删除后 | [同一回归 1 passed，1.14 秒](focused-tests-after-deletion.xml)；[C1–C5 五案绑定仍通过](proof-preservation-after.json)，关闭 IFC 重开 |
| C1–C5 现行人读包 | [5 案、20 份展示绑定通过](proof-preservation-before.json)，包含包内冻结字节和角色检查，关闭 IFC 重开；不是完整 curator |
| 原 18 文件与保留材料 | 原 ZIP 对照 Git LFS OID／大小，普通文本对照 Git blob 与既有 CRLF 检出约定；小包字节一致 |
| 六个远端 LFS 对象 | [6/6 可获取](remote-availability.json)，各读取 1 字节，HTTP 206、对象总大小一致 |
| 旧重构与当前代码 | 结构／来源差异核对；没有执行旧镜像，不宣称两套实现等价 |
| Git 格式与历史字节 | 首次全 staged diff 检查提示历史合同 CRLF 和 Prompt 尾空行；保持四份原合同文件字节，只对本轮新写内容执行格式门，不宣称历史字节也通过 whitespace 检查 |
| 最终导航与依赖 | [253 条本地链接通过](final-verification.json)，生产／脚本／测试无旧 archive 直接引用，Proof diff 为零 |

没有重新执行 Full Preflight、完整 curator、真实 Provider、全仓哈希或 Git/LFS 历史压缩。远端范围读取证明对象可用，不冒充重新完整下载校验；历史独立下载与当前六个本地 ZIP 的哈希核对分别保留其真实范围。

ifc-bench 本地修改、用户当前的 RVT 数据目录及两处未跟踪 semantic-appearance 展示目录保持原样。主分支和其 `.tmp/main-integration-20260912` 工作树仍保留当时版本；本轮只整理当前工作分支的根 archive。
