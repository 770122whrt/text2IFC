# 本对话运行目录清理提案

状态：用户已明确批准，实验完成后已执行并核验。路径均相对于 `E:/code for project/bimnet`。

| 拟删除目录 | 文件数 | MiB | 保全依据 |
|---|---:|---:|---|
| `dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910/failure-recovery-rerun-20260910/A-revise/runtime` | 119 | 5.42 | 已验收A/B Proof内有相同字节副本；只退役runtime，保留原脚本、输入、报告和PROOF-LOCATION。 |
| `dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910/failure-recovery-rerun-20260910/B-retain/runtime` | 179 | 10.84 | 已验收A/B Proof内有相同字节副本；只退役runtime，保留原脚本、输入、报告和PROOF-LOCATION。 |
| `dataset/processed/ifc-presentation-validation/two-storey-human-review-20260909` | 533 | 11.92 | 533份文件均有人工验收Proof副本；保持机器blocked原状态。 |
| `.tmp/brief-evidence-core-final` | 767 | 7.71 | 本对话明确创建的pytest/离线夹具目录；非真实Provider产物。相关红绿XML、日志和代码已保留。 |
| `.tmp/brief-evidence-firstfail` | 82 | 0.91 | 本对话明确创建的pytest/离线夹具目录；非真实Provider产物。相关红绿XML、日志和代码已保留。 |
| `.tmp/brief-evidence-green` | 4938 | 55.13 | 本对话明确创建的pytest/离线夹具目录；非真实Provider产物。相关红绿XML、日志和代码已保留。 |
| `.tmp/brief-evidence-red` | 115 | 2.54 | 本对话明确创建的pytest/离线夹具目录；非真实Provider产物。相关红绿XML、日志和代码已保留。 |
| `.tmp/brief-fixture-baseline-output` | 14 | 0.20 | 本对话明确创建的pytest/离线夹具目录；非真实Provider产物。相关红绿XML、日志和代码已保留。 |
| `.tmp/brief-prompt-final` | 589 | 3.33 | 本对话明确创建的pytest/离线夹具目录；非真实Provider产物。相关红绿XML、日志和代码已保留。 |
| `.tmp/brief-registry-final` | 278 | 0.28 | 本对话明确创建的pytest/离线夹具目录；非真实Provider产物。相关红绿XML、日志和代码已保留。 |
| `.tmp/brief-version-verified` | 1753 | 13.63 | 本对话明确创建的pytest/离线夹具目录；非真实Provider产物。相关红绿XML、日志和代码已保留。 |
| `.tmp/cshape-geometry-tests-20260910` | 11 | 0.26 | 本对话明确创建的pytest/离线夹具目录；非真实Provider产物。相关红绿XML、日志和代码已保留。 |

合计12个精确目录，约112.18 MiB。完整文件、大小、SHA-256和Proof副本位置见 [删除清单](deletion-proposal.json)。

保留：A/B运行根目录及测试仍使用的run_branches.py；A/B此前失败尝试；C型失败和成功Brief、最新累计账本、冻结评价器；当前96K实验；所有已验收Proof。

A/B旧runtime删除后，历史报告和admission中的原路径只是冻结的历史记录。实际机器权威位于Proof的evidence/frozen；后续活动脚本与准入必须读取该规范副本，不能通过删除后绕过哈希检查。

双层包此前存在于本地但没有Git跟踪；已重新核对533份源文件副本与人读结构/IFC重开。必须先将该人工review包保全到Git并推送，不能仅因文件夹名叫proof就删源。人工通过不提升机器blocked状态。

pytest目录来自本次对话明确执行的测试命令，可从已提交测试重新生成；红绿日志/XML已收入C型诊断与验证包。未将可重建夹具冒充真实Provider证据。

删除前重新核对绝对路径在仓库内、无junction/symlink、文件集合和哈希未变、没有活动进程使用；若内容变化，停止该项并报告。不会修改Codex会话、账号或数据库。

## 执行结果

用户回复“批准按清单删除”后，等待两次真实Brief实验结束，再核对全部9,378份源文件集合、大小、SHA-256、独占读取、路径包含关系和reparse边界。2026-09-10 15:12:07 UTC完成12目录删除，共117,626,160字节（112.18 MiB）。831份真实运行源文件的规范Proof副本在删除前后哈希一致；A/B与双层人读包重新检查及IFC重开通过。保留A/B脚本的预算回归10项通过，C原始失败与前次诊断冻结证据哈希未变。

第一次检查发现原清单的部分同字节副本指向其他未跟踪集合，第二次按目录推导发现双层request采用人读直放路径；两次均在任何删除之前停止。随后依据各自已提交Proof manifest确定规范映射，源路径/文件集合/哈希与批准清单完全不变。最终去向以[canonical-paths.json](canonical-paths.json)及[retired-paths.json](retired-paths.json)为准，原提案保留当时字节和pending状态，仅作为授权快照。

证据保全已先推送：A/B为4e8a704c，双层为9dfd91b4。双层仍然是人工accepted、机器blocked，不新增机器验收。已验收Proof未改动；测试临时目录不是Provider证据。

[授权](authorization.json)、[删除前核验](pre-deletion-verification.json)、[执行结果](deletion-result.json)、[删除后验证](post-cleanup-validation.json)均已保存。旧admission/FILES中的runtime路径现为历史定位，不改写旧证据，也不能将这些旧准入直接用于新的调用。后续准入须绑定规范Proof；当前额度实验与最新C任务预算完整保留。
