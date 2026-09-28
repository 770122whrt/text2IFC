# IFC2Text 第一阶段收口

日期：2026-09-18。原方案仍为 `docs/architecture/bim2text-bidirectional-bridge-research.md`。

## 本次执行边界

本次直接执行，不以交接文件代替执行。保留既有 hxp/i5n 的 v0.6 导读和尺寸文本，补齐 1px 同版本导读，逐份核查后提供三份文本及 hxp 实际重建 IFC 的差异报告。现有 hxp 已产生真实 Generator 候选及编译 IFC，但最终状态为 blocked_after_compile，不能标记 accepted。

累计预算仍为 200 万 token，沿用 compact-campaign-v04/budget 的继承账本，不重置此前失败或未知 usage 的保守预留。当前暂停原因 VALIDATION_RETRY_FAILED 属于 hxp 重建；本次经检查后只恢复剩余 1px 描述调用，不继续 hxp 付费重建，也不将未验收 IFC 晋升。

最新授权的 Design Brief 运行上限是 input 131072、output 65536、reasoning 开启。该授权不通过改写历史 hxp-goal-v0.3.json 实施；已恢复历史配置与原运行一致。历史 v0.6 使用过更大输出上限的请求仍按原样保存。本次描述模型继续使用已验证的 v0.6 Prompt 和 8192 输出上限，不发生新的 Design Brief 调用。

## 当前核对发现

旧 Compare 将跨楼层重新归属的三个窗报告为 missing+extra；它们并非真的消失。重叠开口只按中心贪心匹配会互换宿主，材料关联元数据差异也不能概括成材料实质改变。原始报告保留，新审核必须分开位置、尺寸、所属楼层、材料与未评估项。

复用固定代码 4363102b 的阶段准入。执行域配置恢复后，写作生产代码、Prompt 与 Schema 没有变化，不重复 Full Preflight。后续比较器或报告的局部修订只做相应回归。

## 产物与结果

执行后补记真实结果、用量、文件路径及版本。本文不是提前的成功声明。
