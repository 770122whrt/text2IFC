# 光庭Proof收纳与工作目录整理

2026-09-12。用户已人工验收第二版敞开光庭。工作分支为codex/workflow-dataset-links，起点af9be18b；本次没有改产品合同、生成策略或IFC成品，也没有Provider调用、Full Preflight、PR或main合并。

## 已完成的收纳

[光庭Proof](../../../dataset/processed/proof/generation/phase6.6/courtyard-library-20260912/README.md)同时提供两版输入、模型、IFC、图片和报告。第二版为人工accepted；第一版为historical_reference，不追加不存在的验收。原待审状态和所有历史报告原字节保留，以新增human-acceptance记录表达这次状态变化。

三组来源共921个有效文件、73,059,228字节已收纳，包含12个一次性test脚本。全量真实尝试、失败归因、Prompt/响应、SQLite、token账本和实验XML都可从evidence入口查找。52个可重建缓存不收纳。未删除失败分母，未把不同设计版本当成同输入盲测。

## 测试整理

正式回归test_filling_relationship_recovery.py曾动态导入光庭运行目录的test_runner.py；退役运行目录会令公共两策略测试失效。现提取为tests/agent/filling_recovery_support.py，仅保留离线夹具和公共链路调用，不携带凭据加载、真实Provider构造器或历史准入。

新旧Brief/candidate夹具逐对象完全相等，原断言保持。改前受影响两例2 passed；改后该模块39 passed，覆盖两种策略、缺关系恢复、冲突拒绝、源文件保全和原子性。没有删除有效通用回归。12个一次性测试脚本归入冻结过程，默认pytest不会从Proof收集。

## 验证

| 项目 | 结果 |
|---|---|
| 完整集合字节/角色/权威路径/IFC重开 | 通过；921个原文件绑定、47个人读文件、2个IFC |
| 第二版按冻结输入独立复算 | 545/545；原严格浮点色值失败与HEX8复算并存 |
| 第一版按原检查器独立复算 | 1084/1084 |
| 最终图片来源 | 两版均绑定对应正式IFC SHA；网格失败0 |
| 脱离旧目录的回归 | 39 passed，123.19秒；改前2例通过，108.08秒 |
| 夹具前后对比 | 完全相等；原测试断言不变 |
| 文本与数据库敏感信息检查 | 727个常规文本、172个额外文本、9个SQLite；2处历史说明引用api_key=config.api_key，已确认变量表达式；未解决发现0 |
| Provider / Full Preflight | 未运行；本次没有产品行为修改 |

复算文件位于Proof/validation，测试原始XML及扫描结果位于本目录。此检查证明迁移和本地回归，不主张系统可靠性或工程合规提升。

## 删除与保留

[准确清单](CLEANUP.md)与[机器清单](retirement.json)已准备：3个完整归档来源目录、72个确认来源的pytest目录、24个逐字节匹配的.tmp重复文件，合计49,563个文件/744,508,756字节（710.02 MiB）。先提交推送归档，明确确认后再退役；当前尚未删除。

其余早期Repair/Generation目录仍有独立来源或消费者，不因名称包含run/failed/test直接清除；C实验已归档，不重复搬迁。25个pytest候选因权限或归属检查未通过保留。原main活动工作树、ifc-bench修改、其他任务未跟踪文件、会话恢复文件与依赖缓存保持。

分支不重写Git历史、不删除分支。真实证据的恢复工具为scripts/proof/materialize_frozen_bundle.py，指定本集合和v1/v2/concept；输出目录必须不存在。pytest缓存可重跑原测试恢复。

## Git

归档、回归夹具整理与目录退役分开提交；仅暂存本任务明确路径，提交前检查staged diff。最终提交和实际删除结果另行追加到本报告。
