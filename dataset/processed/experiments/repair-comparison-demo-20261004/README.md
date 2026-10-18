# Repair 两个 demo 的真实终止记录

本集合保存 2026-10-04 开发联调中已经终止的六个任务，包含真实失败与两个格式不合格的提交。[当前联调结果](../../../../docs/validation/repair-comparison/demo-results.md)是统一阅读入口；本集合不属于 accepted Proof，也不代表四组都已修复成功。

[INDEX.json](INDEX.json)记录每包成员数、大小和归档核对结果。七个 ZIP 共约 10.8 MiB、372 个成员，逐项解压字节与原记录一致。主机 `.env` 密钥值检查通过，没有收纳 `.env`、私有 G 或损伤配方。原本地工作区仍保留。

| 归档 | 内容 |
|---|---|
| [common.zip](common.zip) | 两道公共输入、开发配置、原始及当前阶段准入、离线检查日志、追加计账说明和归档脚本 |
| [case-001-A.zip](case-001-A.zip) | 原账本、5 次 HTTP、工具轨迹、工作文件及非法 JSON 失败 |
| [case-001-C.zip](case-001-C.zip) | 原账本、20 次 HTTP、唯一提交及 24 条 EXPRESS 错误 |
| [case-001-D.zip](case-001-D.zip) | 原账本、23 次 HTTP、原生 DSH 会话与 STREAM_CLOSED；最后一次用量未知 |
| [case-002-A.zip](case-002-A.zip) | 原账本、49 次 HTTP、工作文件和追加预算诊断；原 runtime_error 终态不改 |
| [case-002-C.zip](case-002-C.zip) | 原账本、20 次 HTTP、唯一提交及 1 条关系基数错误 |
| [case-002-D.zip](case-002-D.zip) | 原账本、7 次 HTTP、原生 DSH 会话与截断失败；最后一次用量未知 |

每个任务包中的 `artifact/result.ifc` 才是显式提交；`workspace/` 内的 IFC 只是原工作区记录，不能据此补造正式产物。`ledger/events.original.json` 保留原事件，`calls.with-current-accounting.json` 在原调用旁附加修正后的协议计账；原 HTTP 字节不改。

DSH 实际返回的思考文本已保存。窗题 23 次请求中 22 次包含 thinking，共 92,087 个字符；门题 7 次均包含，共 4,312 个字符。可读导出在 [dsh-returned-reasoning.jsonl](dsh-returned-reasoning.jsonl)，逐次索引在 [dsh-reasoning-audit.json](dsh-reasoning-audit.json)。每条导出对应原 ZIP 的 SSE 字节；原生 `session.v4.jsonl` 也保留在各任务 ZIP 中。字符数不是 token 数，两题末次响应均缺 `message_stop`，只能保留收到的片段，不能称为完整最终思考。没有重构未返回的内部推理。

两项 B 仍等待用户答复，没有收入终止归档。它们的原 Linux 状态卷、本地账本和只读导出保留，答复后继续原任务。此处的 `pending_at_curation` 只表示归档时状态，不是以后运行的当前状态。

Git 修订字段表示归档前的仓库位置；最初准入另留真实调用前的文件绑定。两者不能代替每次调用时所有源码的冻结快照。后续 B 终止记录另行追加，不覆盖本集合已冻结字节。

随 IFC 的[来源、署名与修改说明](SOURCE-NOTICES.md)及 [MIT 原文](LICENSE-MIT.txt)保留。损坏输入和模型的工作／提交版本是派生修改，修改过程可在各包工具轨迹中检查。

## 新 B 场景方法的两题开发记录（2026-10-07 追加）

[scene-b-20261007.zip](scene-b-20261007.zip)与独立的[索引](scene-b-20261007-index.json)保存代码 `fe4a09b2` 的两次真实 B 尝试，未覆盖原 ZIP 或 INDEX。新方法原公开请求不变、没有人工答复；窗题8次请求309657 token，门题4次请求55004 token。两份唯一产物的固定开发评分全部通过，schema＋EXPRESS零诊断。旧B待答记录仍在原运行区，不把本次成功改写成原任务恢复成功。

新包约7.78 MiB、638成员，保存唯一IFC、公共D和请求、全量原始HTTP、账本、Linux原生状态、实际执行代码与准入；压缩后逐成员字节核对通过，主机密钥与私有G未收纳。独立[推理导出](scene-b-returned-reasoning.jsonl)保留12次实际返回的 `reasoning_content`，共206082字符，不推算未返回内部推理。

用户随后批准的覆盖核验优化另有 `offline-coverage-replay/` 与 `offline-coverage-tools/` 证据；它们属于冻结响应重放／假HTTP，不是新的真实模型尝试。这个集合仍属于开发实验记录，不是 accepted Proof，也不证明正式四组能力改善。
