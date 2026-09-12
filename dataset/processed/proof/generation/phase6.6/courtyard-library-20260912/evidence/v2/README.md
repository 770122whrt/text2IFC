# 光庭阅读馆第二版：完整真实生成，待人工验收

最新交付：[中文报告](rerun-03/REPORT.md) · [最终IFC](rerun-03/generated-open-court.ifc) · [中文输入](rerun-03/request.txt) · [实际整体图](rerun-03/views-final/overall.png) · [交互查看](rerun-03/views-final/viewer.html)。

rerun-03为全新真实Brief/Generator/Audit，3次调用317,533 token，无候选修复调用；正式IFC545项独立复核通过，111个构件成功网格化。Agent视觉检查完成，用户尚未人工验收，未登记accepted Proof。配色为暖米白、浅砂、深青灰和暖木色。

- 第一版保留包：../courtyard-library-20260912，已推送532a4a4c，未改成第二版成功证据。
- 本目录root输入/预算/准入及live-run：第二版最初失败；保持原字节。
- rerun-01：属性与外观目标问题的真实Brief/Generator/Repair，失败保留。
- rerun-02：矩形轮廓格式问题的真实Brief，失败保留。
- rerun-03：最新完整成功，报告解释原浮点颜色检查与HEX评价修订、统一重算及Audit文字勘误。
- brief-envelope-debug与property-debug：通用问题的失败族、修复、原始失败检查及最终离线验证。property-debug中的IFC仅用于被拒候选离线诊断，不是交付。
- railing-debug与structural-debug：此前梁柱/护栏合同与API检查。历史局部结果不等同于整栋真实运行。

保留全部真实attempt及账本：累计17次、1,591,587 token、2723.014活动秒。没有清理历史目录，没有运行仓库Full Preflight，没有声称已完成工程合规或系统级能力提升。复核入口优先使用rerun-03，不重跑已存在的运行目录。
