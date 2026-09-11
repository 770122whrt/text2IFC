# 三层建筑A/B：人工已验收

用户于2026-09-10确认两份IFC内容无误，现按Generation格式计入Proof。保留用户命名generated-A / generated-B；案例内同时提供标准generated.ifc入口，字节相同。

| 分支 | 用户决定 | 真实运行与独立检查 | 文件 |
|---|---|---|---|
| A | 澄清后调整内部布局 | 3次响应；290/290项，零净空采样0/108 | [IFC](generated-A.ifc) · [报告与输入](A-revise/REPORT.md) |
| B | 明确保留原设计 | 5次响应；一轮受限洞口标高校正；290/290项，零净空采样3/108 | [IFC](generated-B.ifc) · [报告与输入](B-retain/REPORT.md) |

两案各6项补充Type检查通过，仅4个必要门Style；8张原生IFC图片已检查。原始Provider输入/响应、完整loop、独立检查、历史账本和审批均完整保存在[evidence/frozen](evidence/frozen)。本次收纳另对两案运行完整Generation确定性Final Acceptance，复核Schema、语义、编译重读、几何、Audit决定绑定及secret scan，不调用Provider。

**验收含义：忠实建模与呈现获用户认可。B的已知零净空问题仍存在，不表示安全、工程合理或规范通过。** A的采样也不替代结构、疏散、防火、栏杆等完整审查。[人工验收原文](human-review.json) · [完整原始报告](evidence/frozen/REPORT.md)。

原始报告中的pending仅表示验收前历史状态；冻结文件不重写。此次不改变Phase状态、不声称普遍成功率提升。新案例稳定性检验另行保留全部尝试。
