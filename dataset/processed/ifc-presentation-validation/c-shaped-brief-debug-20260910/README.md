# C 型教学楼单阶段 Debug

真实Design Brief重试成功，未继续生成IFC。[中文报告](REPORT.md) · [成功Brief](live-attempt/design-brief/design-brief.json) · [原始响应](live-attempt/design-brief/response.raw.json) · [诊断](diagnosis.json)

`live-attempt`是一次真实响应；`offline-ready`和`offline-truncated`是手工/fake对照。旧C失败包保持不变。最新累计预算位于`live-attempt/generation-budget.json`，共2次调用、147630 token；未来接续不得复用旧的1次调用账本。

本次真实诊断用原v2.7 Prompt；随后只为纠正最终输出版本冲突新增v2.9，尚未真实调用新Prompt。`admission.json`为调用时快照，`run_brief.py`为一次性诊断，不是可直接再次调用的当前入口。
