# text2IFC UI 开发入口

> 更新：2026-10-18。UI 与当前 Repair 整合到同一仓库；支持上传、请求预览、异步进度、澄清续答、刷新恢复、结果下载和前后对照。默认启动只准备请求，真实执行另需有效准入、本机配置与任务预算。

## GitHub 交接入口

原 `codex/ui-development` 分支保留历史，当前整合位置见 [STATE](.planning/STATE.md)；[统一交接页](docs/reports/ui-delivery-20261016/README.md)包含三项真实联调的实际输入/输出、截图、原始记录与预算账本，以及独立重建的检查结果和环境版本。网页与默认 API 不依赖旧目录或本地整树备份。密钥、私有样例和活动数据库的删除边界也写在该页。

## 当前入口

[主计划](docs/plans/repair-ui-plan.md)是唯一范围依据；[真实查看器说明](ui/ifc-viewer/README.md)负责启动与操作；[12份IFC2X3实测](docs/validation/ifc-viewer-ifc2x3-smoke.md)负责实际结果，不能将其当作全库或完整几何认证。

新检出推荐 Node.js 24（此前验证版本24.11.0）和 Python ≥3.12。在本工作树创建独立环境并安装：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[web,web-test]"
```

浏览器 JS/WASM 与许可证已随源码提供，无需 npm 下载。启动器优先本树 `.venv`，也支持 `TEXT2IFC_PYTHON`。环境就绪后双击 `Open-IFC-Viewer.cmd` 启动，使用 `Stop-IFC-Viewer.cmd` 停止；或运行：

```text
node ui/ifc-viewer/launcher.mjs start
node ui/ifc-viewer/launcher.mjs status
```

在运行仓库的同一台电脑访问 `http://127.0.0.1:4178/ifc-viewer/`，API使用4180端口。新检出打开空工作台，点“打开 IFC”选择本地模型，走web-ifc解析。私有174样例、`.artifacts/`、`.tmp/`、`.python/`、`.venv/`和`.env`保持本地，缺少本地样例不代表缺少代码。旧4177只保留历史示意原型，不作为真实渲染入口。

可选的两个本机历史案例需按[查看器说明](ui/ifc-viewer/README.md#可选本机历史案例)恢复三个指定LFS文件，再执行`prepare_local_examples.py`；无需整套数据。浏览器诊断脚本另有Edge/WSL等环境要求，不是日常运行前提。

## 当前已完成和保留的问题

12份现有IFC2X3已通过真实浏览器文件选择入口加载并完成旋转、缩放、点选、单构件隐藏及撤销。11份未发现整件Body缺失；steel少1块板，GNI128/Jasmin有布尔或面片诊断。具体对象与日志见检查报告，不把能打开写成全部几何准确。

导入失败保留当前模型/草稿/参照；适应视图保持当前朝向；换文件的轮廓线设置一致；属性按需打开、基本信息先展示。模型树/搜索、中英切换、多目标与共同参考构件选择均已实现。此前9项浏览器边界检查、15项查看器Node检查及174的18项浏览器回归保留为各自阶段的历史证据；2026-10-16提交前检查另有100项Node和90项Python检查通过，命令及范围见查看器说明，不合并为系统能力指标。

三项新发起DeepSeek联调中，补门和澄清补窗通过独立完整检查；双目标任务各补一窗，但输入原有三条IFC规范问题保留，整文件合规未通过，待合规输入复验。实际结果和原失败见[主计划§5.14](docs/plans/repair-ui-plan.md)。本地打开与源字节下载继续保留，真实Repair不会覆盖源IFC。

整合后继续复用当前 RepairAPI 的有界校验纠错；网页不另外控制返工或重试。剩余工作是合规双目标真实复验、部分模型显示诊断与澄清体验完善；Generation、公网部署、协作及剖切/测量/视图管理未纳入当前完成范围。本次整合只做离线测试，不新增 Provider 调用或重开 Repair 实验。

## 当前开发位置

- 统一目录：`E:\code for project\bimnet`；之前的 `bimnet-ui` 工作树已退役。
- 网页代码：[查看器](ui/ifc-viewer/README.md)与 [Web 接入](src/text2ifc_web/)。
- 原 UI 分支 `codex/ui-development` 保留历史；当前合并位置以 [STATE](.planning/STATE.md)和 Git 为准。

本机运行环境与实验结果不会通过 Git 自动同步。只恢复明确选定的 LFS 模型，不批量拉取整个数据集。

## 下一次接手

先读 AGENTS.md、docs/README.md、STATE、主计划最新记录与查看器 README。保留源 IFC、真实失败与历史证据；按当前用户任务修改，不接续旧 Repair 批次或新增付费任务。旧 UI 独立工作树的权限说明只适用于当时，不能代替当前授权；真实执行必须重新核对当前准入与费用边界。
