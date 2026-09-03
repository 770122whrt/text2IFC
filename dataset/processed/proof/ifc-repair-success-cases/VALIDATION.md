# IFC Repair 成功案例集自动验收

**最新执行日期：** 2026-07-29
**命令：**

```powershell
.venv\Scripts\python scripts\ifc_repair\validate_success_cases.py --json
```

## 最新结果

```text
status: passed
cases: 12
operations: 34
FILES artifacts checked: 149
IFC reopened: 36
errors: 0
```

通过案例：

- LargeBuilding 单窗完整语义复刻
- LargeBuilding r22 真实 DeepSeek 重复实验
- vvo 五窗批量修复
- AdvancedProject 五窗大型模型修复
- px4 五窗与上下叠窗修复
- LargeBuilding Door 精确 Type 复用
- vvo Door 精确 Type 复用
- AdvancedProject Door 大模型完整门禁
- LargeBuilding 受控生成 DoorStyle
- vvo 五门原子修复与注入失败回滚
- vvo 两门两窗混合原子修复
- Dental Clinic 两门两窗无名称几何定位与完整墙体重开洞修复

## 自动检查内容

脚本 `scripts/ifc_repair/validate_success_cases.py` 对每个案例执行：

1. 集合 `manifest.json` 的 case 数、唯一 case id 和 accepted 状态；
2. `FILES.json` 对案例证据文件的完整覆盖；
3. 每个 artifact 的文件大小和 SHA-256；
4. original、damaged、repaired 三份 IFC 均可由 IfcOpenShell 重开；
5. 三份 IFC schema 均为 IFC2X3；
6. Bound ChangeSet 的 `base_model_fingerprint` 等于 damaged IFC SHA-256；
7. RepairIntent；或离线 Prompt Profile/few-shot 指纹与 operation 绑定有效；
8. Bound ChangeSet、集合索引与 evaluation 的 operation 数、类型一致；
9. Production evaluation：
   - `status = passed`
   - `complete_repair_success = true`
   - `successful_artifact_publishable = true`
   - application 与 preservation passed
   - 每项 L1/L2 passed
10. 存在 Private Ground Truth evaluation 时，使用相同发布规则复核。
11. 离线 Door Proof 的 `synthetic_fallback_used=false`；注入失败案例必须
    `valid=false`、`published=false`。
12. 两门两窗混合案例的公开 request/RepairIntent 不含 IFC GlobalId；Dental
    Clinic 案例还禁止对象和楼层 Name，只用标高、朝向、墙体长高厚与墙局部
    位置完成 4 项确定性 target-resolution，并保存随后内部绑定的证据。

## pytest 接入

```powershell
.venv\Scripts\python -m pytest tests\ifc_repair\test_success_case_collection.py -q
```

因此以后添加 Door、Opening、Beam 或 Column 案例时，只要把案例按相同目录合同加入
`manifest.json`，同一 Proof gate 会自动拒绝：

- 文件缺失、未索引或哈希漂移；
- IFC 无法重开或 schema 错误；
- ChangeSet 绑定了错误 damaged IFC；
- RepairIntent、ChangeSet、evaluation 的 operation 数不一致；
- evaluation 未通过或 IFC 不可发布。

本 Gate 校验的是冻结 Proof 的完整性与成功证据，不替代 operation family 自己的
Production/Private evaluator。
