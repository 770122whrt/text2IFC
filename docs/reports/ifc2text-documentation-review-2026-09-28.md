# IFC2Text 文档整理与提交范围审核

日期：2026-09-28。此次修改文档与导航，不改产品代码、不调用 Provider、不重新认定实验成功，也不合并 main。

## 文档收口结果

从 [IFC2Text 当前入口](../validation/ifc2text/README.md)进入：结果维护实验数字，维护页记录故障原因与回归，唯一计划 v1.0 维护范围与合同，研究方案维护待验证假设。文献分析和 IFC 门窗结构说明从长文拆出，分别保存一份正文。

11 份历史报告、5 份阶段记录保留短链接入口；原文已固定在整理基线 `a7e0dcd5886610ce9ee45d0f808d7b198c43ec4f`，由[历史索引](../validation/ifc2text/history.md)集中引用。原始失败、旧准入及已接受 JSON 不覆盖。原来的“尚未实现部件”“尚未执行往返”“容差未定”已按现有证据纠正。

按整理前备份的 22 份专题文档及本次新增专题正文统计，文本量从 136,327 字符降至 54,467 字符，约减少 60%；不含通用导航和本报告。研究假设、实际能力与历史状态分别标明，不再复制实验流水账。

## 本次检查

- 31 份变动文档的 261 个本地链接存在；未重新检索论文或检查所有外网链接。文献保留原检索截止日。
- hxp／i5n_1 已接受摘要中 12／14 个证据文件的实际 SHA-256 与摘要一致，合计 26 个；四份 component-v26 JSON 无修改。
- 旧 Proof 被 Git 显示的 426 个删除经沙箱外只读核查确认是权限误报；实际目录和文件仍在，没有真实删除差异，也没有提交删除。
- 对额外的 RVT 脚本进行了源码审阅和定向测试：`tests/dataset/test_rvt_pipeline.py` 为 **33 passed**。这是离线夹具检查，不是实际 RVT 转换或数据集保真认证。
- 没有运行 Full Preflight、完整 Proof curator 或真实转换器；这些不是文档整理的替代检查。

## 额外代码审核发现：空选择返回成功

**P2，尚未修复。** 本地未跟踪脚本 `dataset/external/RVT/height_batch.py` 在选择不到输入时仍创建空 summary／manifest，并返回 0。原因是扫描不到 outcome 时 `selected` 与 `results` 均为空，末尾 `all(...)` 对空集合返回 True；`--ids` 也没有在入口核查未知 ID。

离线复现采用全新临时目录、空资产索引 `{"assets": []}` 和空来源策略 `{"sources": []}`，将模块 BASE 指向该目录后调用：

```text
height_batch.py --runs nonexistent-parent --run-name empty-child
  --ids UNKNOWN --asset-index <temporary assets.json>
```

实测 `exit_code=0`、`outcomes=0`，没有调用转换器。复现文件保留在本地 `.tmp/ifc2text-docs-20260928/rvt-empty-selection-repro/`。修复应区分“无可处理项”与成功：验证父运行、明确 ID 和选择结果，在空选择时返回非成功状态，并覆盖 CLI 负例。现有 33 项通过不能证明该脚本完整 CLI 正确；本次不将这批脚本作为已审通过内容发布。

## 没有随本次推送的内容

沙箱外只读快照有 20,078 个未跟踪条目，包含本次新增文档；仍有实验临时目录不可读取，因此这不是完整磁盘库存，也不是逐文件审核完成数量。未读取或未验证的内容保持原状。

| 类别 | 本次判断与保留原因 |
|---|---|
| `dataset/processed/experiments/` 的模型、响应及失败轨迹 | 已核实本次结果引用的证据链；其余只做分类，不将成千上万的轨迹和测试副本批量发布。完整证据仍在本地，已提交摘要不冒充完整上传 |
| 未跟踪的 Generation／Repair Proof | 保留原字节；未执行安装／重新收纳所需 curator，不能作为新接受包随文档发布 |
| `dataset/external/` 的 IFC、RVT、ZIP、检查输出与资产表 | 包含独立的数据集工作及未解决的来源／发布许可项；本次没有完成逐模型发布审查，不上传原始包或发布修复副本 |
| `dataset/data_organization.md`、`dataset/external/README.md`、`dataset/manifests/README.md`、`dataset/manifests/external-corpora.json`、`dataset/sources/CATALOG.md` | 已检查差异，但新入口依赖尚未收纳的资产表、删除日志及数据审查报告；作为同一数据集变更保留，避免只推导航造成远端证据缺口 |
| `dataset/external/RVT/` 脚本与 `tests/dataset/test_rvt_pipeline.py` | 33 项测试通过，但上述空选择问题已复现；其批处理还依赖本地资产／许可记录，暂留待修 |
| 两个外部 Git 子模块 | 父仓库指向的提交 SHA 未变化，内部存在历史有意删除；暂存父仓库 gitlink 不能发布这些删除。本次不修改或推送上游第三方仓库 |

本次可发布范围为 IFC2Text 文档、通用导航和 STATE 中相关段落。其余内容未删除、未还原、未加入暂存区。后续若处理剩余项，应分别修 RVT 的复现问题、收纳数据集依赖和发布许可、验证新 Proof，不能用一次批量 `git add` 替代审核。
