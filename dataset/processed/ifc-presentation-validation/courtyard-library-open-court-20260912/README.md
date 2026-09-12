# 光庭阅读馆第二版：待真实运行

本目录为独立新案例，不是accepted Proof。第一版IFC及Provider尝试保存在courtyard-library-20260912，完整保留包532a4a4c已推送；第二版重新从中文请求进入pipeline。

- 输入：request.txt。由Agent在用户委托设计范围内细化，不称为用户逐字原话；两层开敞U形、外露楼梯、20柱、6梁、14段细杆护栏、44窗及6门，无家具植物。
- 冻结评价：expected-independent.json、check_ifc.py，在新候选出现前建立，仅本地使用。prepare_design.py保留委托几何来源。
- 通用修复：7df706b2梁柱冻结预期；4df9ae0d有界护栏、新合同路由及空间聚合回归修复。
- 阶段准入：admission.json，641个依赖/输入路径冻结；stage-02为504通过2失败，stage-03相关75项全部通过并覆盖两处失败。新增注册检查11通过，完整新运行包装器离线1通过。详见railing-debug/REPORT.md；集合重叠不累加为成功率。
- 运行：`.venv/Scripts/python.exe -X utf8 dataset/processed/ifc-presentation-validation/courtyard-library-open-court-20260912/run_case.py --live`。先验证admission与具体载荷，继承9次/750000 token账本，共享32次/200万token/3600秒上限。首次运行目录必须不存在；不覆盖旧attempt。
- Audit通过design-review-context保留开敞边界、外露楼梯和可见细杆栏杆三个已提出问题，要求修改不等于自动确认解决。最终IFC仍需独立重开和实际视图检查，再交人工验收。

当前尚无第二版真实IFC，尚未登记Proof。本阶段未运行仓库Full Preflight，没有宣称盲测能力提升、实际token节省或施工合规。
