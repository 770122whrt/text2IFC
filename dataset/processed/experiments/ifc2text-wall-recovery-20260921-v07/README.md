# IFC2Text 异常墙与源归属整理：交付入口

本目录区分源数据整理、描述补全、真实模型输出和离线反事实，不把它们合并为端到端成功。

## 当前使用的文件

- `hxp-host-normalized.ifc`：仅三窗的楼层包含关系归到宿主墙所在层；原始 hxp 未覆盖。几何、放置、GUID、材料和其他构件归属均保留。
- `source-review.json`、`source-normalization.json`：原始结构审查及逐组件变更清单。整理是显式建模政策，不等于证明源 IFC 非法。
- `closeout-v08/hxp-description.md`：最终整栋说明，异常轮廓显式闭合。导读来自真实 narrator.v0.7；材料与几何数值确定性拼接。
- `closeout-v08/single-wall-description-v08.txt`：下次单墙真实验证的输入；尚未再次调用 Provider。
- `closeout-v08/summary.json`、`closeout-v08/budget.json`：结果、精度核对和累计预算。

## 不应混淆的历史产物

`host-normalized/writing/` 是首次 v0.6 导读，有一处材料措辞错误，已在 `first-pass-review.json` 中拒绝；文件未改写。`host-normalized/writing-v07/` 是修正后的真实导读。

`live-brief/` 返回 ready；`live-generator/` 确实选择 polygon 并传递了轮廓，但缺少末尾闭合点，`OPEN_POLYGON_PROFILE` 导致输出 invalid。没有合法的未经编辑的真实单墙 IFC，也没有通过 Audit/最终接受。

`closeout-v08/offline-closure-counterfactual/` 只在独立副本中为该真实 JSON 追加其已有首点，随后编译比较，用于定位闭合问题。它是离线诊断，不是新真实成功。

源原件与旧整栋 Compare 不变。SQLite、临时测试目录仅留本地，不作为本次 Git 交付文件。完整结论见 `docs/reports/ifc2text-wall-and-source-fixes-2026-09-21.md`。
