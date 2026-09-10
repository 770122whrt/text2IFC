# 双层 Generation：修复与真实运行报告

当前双层案例尚未成功：第一次真实生成被几何门禁阻断；通用几何合同已补全并通过离线回归。第二次调用在发送前被自动审批拦截，等待具体载荷发送确认。没有将非法候选手工修成 IFC，没有可交付双层 IFC，也未登记为 accepted Proof。

## 实际输入与运行

- [中文请求全文](request.txt)：双层社区阅读活动楼，9×8 米室内范围，两层各净高3米；楼梯及实际楼板洞口；10窗、3门、暖色协调风格。
- [运行前冻结预期](frozen-expectations.json)：材料、尺寸、位置、数量、样式和无请求属性边界；沿用2026-09-08原始冻结字节。
- [原始公共 CLI 终端结果](cli.log)、[执行记录](execution.json)。默认 `legacy_full`，真实模型 `deepseek-v4-flash`，目的地 `api.deepseek.com`。
- [真实 Brief](runtime/runs/148bdf3872e74ccd/design-brief/design-brief.json)、[完整失败候选](runtime/runs/148bdf3872e74ccd/generator/parsed-output.json)、[九项阻断检查](runtime/runs/148bdf3872e74ccd/generator/validation.json)、[累计预算](runtime/runs/148bdf3872e74ccd/generation-budget.json)。候选 JSON 是诊断材料，不是合格输出。

| 环节 | 响应 ID | reported token | Provider活动时间 | 结果 |
|---|---|---:|---:|---|
| Design Brief | cbd4a500-48aa-4d1e-9909-f2fb74d5ebc4 | 50,210 | 261.1 秒 | ready，无额外澄清 |
| Generator | b48255e4-349d-43e9-816b-8600b6fd6450 | 67,710 | 286.2 秒 | JSON完整，9项基础门窗几何约束阻断 |
| Audit | 未调用 | 0 | — | 前置条件未通过 |

本轮两次真实响应合计117,920 token；上次2026-09-08的五次真实响应另行保留，未混入本轮计数。请求由Codex按用户授权编写。这是已揭示开发案例的复验，不是首次成功率或系统能力提升实验。

## 原因和通用修复

旧生成合同提供字段和枚举，但几何编码说明不充分。真实候选把矩形拉伸体的原点当成角点；实际 IFC 矩形截面以原点为中心。这个误解同时影响墙、楼板和开口。部分相对宿主放置的门窗又重复使用世界方向，导致二次旋转。只改报错窗，仍会留下其他构件的位置错误。

新增只读 `text2ifc/generation-authoring-contract/1.1`，明确矩形中心原点、截面与拉伸方向、父子坐标的逆变换、楼层标高只应用一次、门窗底中心和楼板洞口坐标。旧1.0投影哈希保持不变；未改写已注册Prompt或Schema，未放宽几何门禁，未自动改变用户尺寸、宿主或开口。使用同一模板仍不强制共享IFC Type。

前期已经实现的枚举合同、有界字段ChangeSet、按需上下文和持久化总预算继续生效。本次阶段检查另修正旧REPL离线夹具缺少模拟token用量的问题，并增加未知历史用量仍阻断后续调用的反例。

## 验证记录

| 范围 | 结果与实际证据 |
|---|---|
| Generation阶段检查：Agent、compiler、contract_v2、ifc_quality | [首轮905通过、3失败、无跳过](admission/pytest.xml)；失败来自旧REPL夹具缺少模拟usage |
| REPL及预算夹具修正 | [19通过](admission/repl-budget-green.xml)；另[13项预算检查通过](admission/unknown-usage-green.xml)，含缺失／部分usage的拒绝案例 |
| 几何合同先红后绿 | [红测试10失败、8通过](admission/geometry-contract-red.xml)；[公共链路、两策略、几何、恢复67通过](admission/geometry-contract-green02.xml) |
| 上下文、预算、版本兼容 | [25通过](admission/geometry-context.xml)；[旧投影哈希检查1通过](admission/geometry-legacy.xml) |
| 三层离线代表模型 | [公共入口生成且重读通过](admission/scale-public-04/scale-result.json)，约9.3秒、主进程峰值约164MiB；子进程内存未测 |
| 静态检查 | compileall与相关路径diff检查通过，见admission命令日志 |
| 准入 | [初始阶段准入](admission/admission.json)、[几何合同补充准入](admission/geometry-admission.json) |

各组测试有重叠，不相加为独立案例成功率。测量脚本的前几次失败和一次测试命令路径错误均保留；它们未调用网络。离线三层IFC仅用于测试，不能充当本次真实双层请求输出。未运行Full Preflight、全仓库pytest、盲测Baseline/Candidate评测或accepted curator。

## 后续发送与人工检查

[第二次生成载荷预览](geometry-payload-preview/prompt-rendered.md)已在本地生成；包含原中文请求、真实Brief、IFC字段／几何合同和选定上下文，无Repair原始IFC、private Gold或凭据正文。[结构化预览](geometry-payload-preview/provider-payload-preview.json)不执行网络。

自动审批拒绝的是将这次完整新载荷发送至api.deepseek.com，要求对此具体范围明确授权。该拒绝发生在transport前，未新增Provider调用。批准后，沿用累计任务预算，在独立目录继续真实Generation；候选通过自动检查后才进入Audit，并独立重新打开IFC与冻结预期逐项比较。

成功后再生成实际IFC网格的整体、剖开视图和门窗近景；按现有Generation Proof格式整理request.txt、完整generated.ifc、model.json、REPORT.md和evidence，以pending_human_review／unregistered收纳。人工确认前不登记。现有单层Generation和Repair三份IFC待审材料保持不动；Repair工程师语言空间定位尚未实现，不将本次改动冒充该能力已完成。
