# C 型教学楼：人工已验收

用户于2026-09-11确认本次模型可以收入Proof。保留用户命名 [generated-C.ifc](generated-C.ifc)，案例内的标准 generated.ifc 与它逐字节一致。

- [案例报告、输入与图片](C-teaching/REPORT.md) · [人工验收记录](human-review.json)
- 真实运行 `05c6de3a19ed20f9`：Brief、Generator、Audit 共3次调用，首次通过，无修复loop；本轮220,720 token。
- 独立重开IFC检查485/485；三层、每层3个空间、21窗、7门、2梯段。入口按用户澄清位于西墙距南侧4.2米。
- 本次收纳重新执行完整Generation确定性Final Acceptance，检查Schema、语义、几何、编译重读、Audit绑定及secret scan；未调用Provider。

历史报告和JSON中的pending是验收前快照，原字节保存在 [冻结证据](evidence/frozen/REPORT.md)。当前人工状态以本集合human-review.json为准。重编译只用于复核，展示IFC保持用户验收字节。

Audit原文“每层9个空间”为叙述错误；实际每层3个、全楼9个。人工验收不代表结构、消防、楼梯净高或可施工性全面认证，不改变Phase状态，也不证明系统成功率提升。
