# C 型教学楼：交付与 Token 观察

状态：离线验证进行中，真实调用尚未开始；无新 IFC，未登记 Proof。

本轮沿用原C中文请求和独立评价器，修正Brief将交通空间包含楼梯洞口一概当冲突的规则。普通Prompt升级为v2.10、审查Prompt为v2.11；旧版本与Schema不变。新运行继承4次调用、300,540 token、886.717秒活动时间，不回退失败消耗。

实验随交付推进：先走默认legacy_full完整公共链路；如果到达可审查候选，对同一份Audit输入做去重可行性检查，有实际缩减才追加一次副本Audit，单独记录其花费。原格式与去重判断、独立重读IFC、外观检查分别记录，不能用模型自报或一次配对证明质量非劣效。真正的新歧义等待用户，输入和已接受Proof不改。

当前验证：原规则2项红测试，新增规则相关64项通过；新运行器3项通过，覆盖完整C公共链路与独立IFC检查、澄清停止和已存在目录保护。fake数据只用于离线验证。其余公共路径回归进行中，未运行Full Preflight。

- [原始请求](../c-shaped-teaching-building-20260910/request.txt)
- [冻结独立预期](../c-shaped-teaching-building-20260910/frozen-expectations.json)
- [修改前案例族](../../../../docs/validation/brief-space-opening/family.json)
- [本次载荷范围](payload-preview.json)
- [授权记录](authorization.json)
