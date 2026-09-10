# 新场景：三层 C 型教学活动楼

当前状态：用户已授权并执行一次真实调用，Design Brief 因 Provider 截断停止；没有最终 IFC，没有进入人工验收或 Proof。详见 [本次报告](REPORT.md) 与 [暂停说明](RUN-HOLD.md)。原准入是运行前快照，不再授权继续调用。以下离线准备记录不代表真实结果。

[中文输入](request.txt) · [载荷预览](payload-preview.json) · [冻结独立预期](frozen-expectations.json) · [准入](admission.json)

外包络13.2×16.8米，向东敞开，三层同形；六间教学活动室、三层西侧交通空间、两段错开的直跑楼梯、21窗、7门。沿用现有暖色主题、砖墙、混凝土板屋面和基础门窗模板，不新增产品能力。

输入由助手按人类工程语言编写，作为预先冻结的测试请求，不能描述为自发外部用户对话。本次不提供参考IFC、不预置已知设计concern，也不预填用户澄清答案。普通Brief 2.3可以提出缺失/歧义；若需要澄清，应暂停取得真实用户回答。未绑定已知决定时使用普通Audit；不能伪造一个设计审查context来强行进入Audit 3.0。

## 观察方式

- 保留第一候选、每次修复、问题类型、调用数及终态；首轮成功和有界修复成功分开记。
- 分别记录模型自行提出的问题、现行确定性gate检出、事后独立IFC检查检出。
- 独立检查器读取最终IFC，核对485项：数量、楼层、空间、材料、Type、门窗关系/尺寸/分色、楼梯方向、C形板屋面体积及缺口覆盖等。它不发送给Provider，不以Agent自报覆盖率评分。
- 人工查看最终IFC和原生视图后，才决定本案例是否登记Proof。不存在最终IFC时，报告失败/澄清，不提供手工模型替代。
- 一次新场景观察不构成稳定成功率估计；本次没有Baseline/Candidate配对统计实验或完整规范审查。

## 已有离线证据

11项凹形几何/原有几何测试通过，C/U/L轮廓覆盖缩放与镜像。新runner的完整公共Brief→Generation→Audit→IFC路径使用3个fake响应完成，485项原生IFC检查通过；另有5个错误模型对照均被评价器拒绝（缺口被填、洞口缺失、材料错误、门开启错误、未请求属性）。

[公共runner结果](offline-runner/execution.json) · [独立检查](offline-runner/independent-checks.json) · [评价器反例](checker-controls/result.json) · [测试XML](geometry-tests.xml)

`offline-*`与`checker-controls`均是手工夹具/fake/评价器测试，不是Provider结果、正式设计或Proof。前3次夹具调试失败也保留：门窗轴线/非当前formal支持的显式containment、第二段楼梯原点、洞口未使用宿主局部坐标；第4次完整公共夹具通过。测试期间没有修改产品代码，没有把这些修正加入真实输入的候选答案。

## 运行入口

离线核实：`.venv/Scripts/python.exe .../c-shaped-teaching-building-20260910/run_case.py`。

真实运行需有效`authorization.json`后显式加`--live`。只有本案例`request.txt`及该运行产生的允许上下文进入Provider；整份offline目录、冻结预期与评价器不进入生产输入。一次输出固定为`live-run`，已有目录会拒绝重复启动，预算在Brief及后续完整loop间共用。遇澄清或确定性缺陷暂停，不自动代答或扩大预算。
