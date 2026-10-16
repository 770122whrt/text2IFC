# text2IFC 三维工作台与 Repair 接入

> 更新：2026-10-16。已实现 IFC2X3 查看、模型树搜索、按需属性、中英切换、多目标与共同参考构件选择，并接入现有 RepairAPI 的上传、请求准备、异步执行、澄清续答、刷新恢复、产物下载与结果前后对照。默认启动只允许上传和准备请求，真实执行需另行配置本机 Provider、有效阶段准入和任务预算。

当前代码入口为 `ui/ifc-viewer/`、`src/text2ifc_web/`，原生集成继续复用 RepairAPI；`ui/prototype/core.mjs` 仍由工作台引用。唯一范围与实施记录见[主计划](../../docs/plans/repair-ui-plan.md)。Generation、最终检查失败后的自动返工、公网部署与协作不在当前完成范围。

2026-10-11 的三项新发起 DeepSeek 联调中，补门和澄清后补窗通过独立完整检查；双目标任务在两面所选墙各新增一窗，目标绑定与几何检查通过，但输入原有的三条 IFC 规范问题保留，整文件合规检查未通过，不能计为完整验收。原失败与剩余复验保留在主计划 §5.14；发布准备不会新增模型调用。

模型显示仍有已知限制：既定十二份 IFC2X3 均能打开和操作，一份缺少一个板构件、另两份有局部解析诊断；详见[多模型检查](../../docs/validation/ifc-viewer-ifc2x3-smoke.md)，不据此宣称任意 IFC 完整保真。

## 本次提交前检查（2026-10-16）

网页端与历史交互原型的 100 项 Node 检查通过，Web 接入、直接相关原生终态/澄清路径及网格导出合同的 90 项 Python 检查通过，均无跳过。新增检查覆盖无私有样例的新检出入口和本树虚拟环境优先级；未运行全仓库 Preflight、未新增模型调用。

```powershell
node --test ui/ifc-viewer/tests/*.test.mjs ui/prototype/tests/*.test.mjs
.\.venv\Scripts\python.exe -m pytest tests/web tests/ifc_repair/test_orchestrator_terminal_matrix.py tests/ifc_repair/test_clarification_state.py ui/ifc-viewer/tests/native_geometry_test.py -q --tb=short --basetemp=.tmp/ui-publish-check
```

本次 Python 实际使用已有的 3.12.4 解释器，JUnit 留在本机 `.tmp/ui-publish-20261016-01.xml`。原生集成测试需恢复上述公开案例中各自使用的具体 LFS 输入；仅打开网页不需要这些测试数据。

## 新检出环境与启动

推荐 Node.js 24（此前验证版本为 24.11.0）及 Python 3.12 或更新版本。在当前工作树根目录创建独立环境并安装声明依赖，例如 Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[web,web-test]"
node ui/ifc-viewer/launcher.mjs start
```

启动器优先使用本工作树 `.venv`；也可用 `TEXT2IFC_PYTHON` 指定解释器。浏览器 JS/WASM、Three.js、web-ifc 和许可证随源码提交，正常启动无需 npm 安装或资源下载。准备脚本只供需要重新构建 vendor 时使用。

Windows 可双击根目录 `Open-IFC-Viewer.cmd`，用 `Stop-IFC-Viewer.cmd` 停止。终端也可运行：

```text
node ui/ifc-viewer/launcher.mjs status
node ui/ifc-viewer/launcher.mjs stop
```

访问 `http://127.0.0.1:4178/ifc-viewer/`，Repair API 使用独立的 4180 端口。服务只监听本机，不是系统服务；退出 Windows/WSL 后需重新启动。未带本地样例缓存的新检出打开空工作台，点“打开 IFC”选择自己的模型即可。已有本机 174 缓存可继续作为可选显示样例，缺少该缓存不代表缺少网页代码。

默认不读取或自动启用真实 Provider。配置诊断可显式运行 `python ui/ifc-viewer/api_launcher.py config-status`；使用虚拟环境时替换为对应解释器。真实执行仍需遵守[Agent 准入协议](../../docs/validation/agent-capability-evaluation.md)，不因启动网页或已有密钥而自动放行。

## 可选本机历史案例

“本机案例”展示归档真实结果，不重新执行模型。需要时仅恢复以下三个具体 LFS 文件，再准备独立的展示副本：

```powershell
git lfs pull --include="dataset/processed/experiments/repair-comparison-demo-20261004/scene-b-20261007.zip,dataset/processed/ifc-repair/repair-comparison/development/case-001/public/model.ifc,dataset/processed/ifc-repair/repair-comparison/development/case-002/public/model.ifc" --exclude=""
.\.venv\Scripts\python.exe ui/ifc-viewer/prepare_local_examples.py
```

脚本使用已跟踪的归档索引、公开输入及请求，输出到 `.artifacts/local-examples/`。未准备时案例列表为空；本地打开 IFC 和请求准备仍可使用，不需要下载整套数据。

`.artifacts/`、`.tmp/`、`.python/`、`.venv/`、`.env`、浏览器配置和私有 174 样例均保持本地，不随此代码发布。运行状态、上传与任务输出只写入本工作树。浏览器诊断脚本是可选开发工具，部分依赖 WSL、Windows Edge 和独立测试配置，其他脚本另需 `websocket-client`、Pillow 或 VTK；这些不是日常网页运行依赖，也未声明跨平台浏览器全部验收。

## 历史验证记录：中英界面切换（2026-10-10）

以下保留当时的验证范围与负证据；接入状态以本文顶部和主计划最新实施记录为准。

页首“中文 / EN”立即切换界面，并记住本浏览器的选择；第一次默认中文。浏览器禁用本地存储时，当前会话仍可切换。切换不重新打开或解析 IFC，不改变几何、相机、隐藏、选择、定位/辅助参照、草稿、已提交请求、模型树搜索和展开项。原始 IFC 名称、GlobalId、Pset/Qto/属性名、源字符串、单位、用户文字与原始 JSON 保留；布尔/缺失值只切换可读标签。

覆盖菜单/按钮、模型树辅助说明、属性分组、加载结果、错误提示、占位符和无障碍标签。语言切换不是修改文件，也不让 LLM 翻译用户需求。Property 已加载的数据只重新排版，不再读模型；用户展开的详情仍保持展开。

实测：`node --test ui/ifc-viewer/tests/*.test.mjs` 的31项查看器测试通过（含7项新增语言测试）；`verify_i18n.py --label candidate-1` 的27项真实Edge/WebGL2检查通过，核对完整状态、源/属性原文、语言记忆、失败输入、英文打开另一个IFC和源下载字节一致，以及1366/1024/390宽度的溢出；另重新执行原有18项真实模型旋转/缩放/右键隐藏/恢复/双引用回归，全部通过。此次不重做全库实验。

本次英文/中文截图与记录：`.artifacts/i18n/candidate-1/`，包括 `english-properties.png`、`english-workbench.png`、`english-laptop.png`、`chinese-properties.png`、`checks.json`。验证使用独立测试浏览器配置，不改用户日常浏览器偏好。

用户当时已人工查看多份IFC并认可显示，取消共享版本/Git分支/协作功能。该次语言切换验证发生在 Repair 接线前，没有付费调用；后续接口与真实联调已按主计划实施。旧示意原型的4177不作为当前入口。修改服务路由后先停止再启动，前端更新后 Ctrl+F5 刷新。

## 当前交互：模型树、属性与统一高亮

“打开 IFC”选择电脑中的 `.ifc` 即可读取；失败导入保留原模型和草稿。本轮再次通过原生文件选择器核对12份IFC2X3，均能加载、旋转、缩放、点选隐藏及撤销，模型树的全部类别/数量也与IfcOpenShell只读枚举一致。已知缺板与面片诊断仍在，详见多模型检查，不宣称所有文件完全保真。

左侧模型树以当前文件为根，按实际 Project/Site/Building/Storey/Space 和 Elements→IfcClass→对象分组；与用户参考截图一样提供类别计数，但不复制示例计数。可按名称、类别、GlobalId、STEP ID搜索。点叶子与点三维遵循相同查看/选中提交模式；展开目录不改变请求参照。每项保留编号以区分重名，查看模式的圆形可见性按钮可隐藏/恢复单件。无网格、无几何和洞口/空间等辅助体分开提示；不为无网格对象补画几何。模型树可收起，窄屏以抽屉显示。

点击构件默认仅简卡；“查看属性”才读取可读实例Pset/Qto、Type属性、源单位、材料与楼层，保留源字段名和原值。false、0与未记录分开，原始数据位于二级折叠区。按需属性不是新增LLM调用，也不是屏幕测量功能。

选中高亮使用统一无光照颜色、保留深度测试的微小显示偏置；样例#1895已复现并修正共面深度竞争造成的灰色三角块。所有子网格一起高亮，源顶点和材质不改；真实遮挡物仍可遮挡，取消选中恢复原色/透明度。单独WebGL正负例验证共面选中与前景遮挡，不能把高亮看成IFC材料改变。

本轮67项限定Node回归通过（查看器24、旧交互原型43），17项新增真实浏览器检查、9项失败导入/视图边界及原18项真实模型交互回归通过。新截图与检查位于 `.artifacts/inspection/candidate-2/`；12份文件重新测试位于 `.artifacts/dataset-ifc2x3/tree-properties/`。测试范围分开，不把一次样例修复当作全部IFC认证。

## 显示来源与此前保真记录

本地可选174样例采用 IfcOpenShell 0.8.5 已解析的实际网格，Three.js负责显示。网格和原IFC逐字节绑定，250个Body构件、149378个三角形；web-ifc在该入口读取同一IFC的名字、GUID和属性。`engine=webifc`为独立几何对照。新检出不携带此私有样例缓存；用户打开的本地IFC与修复前后模型走web-ifc直接解析，不复用174网格，也不声称任意新模型已通过同等级验收。

左键拖动旋转、滚轮缩放、右键拖动平移；查看模式右键短点具体构件可隐藏。提供撤销隐藏、显示全部、相机预设、点选名称与按需属性；选中提交支持多个目标和共同参考构件。自然语言经预览确认后进入现有RepairAPI；默认准备模式不执行修复。

源RGBA保留；sRGB解释、光照、透明正向面和可切换边线是显示配置，不写入源IFC。有实际结果时才提供前后模型对照，不伪造修复后结果。

## 已复核与尚未验收

真实Windows Edge headless＋SwiftShader WebGL2的18项检查通过，含旋转、缩放、单构件隐藏/恢复、双引用和同源网格载入；11项Node测试通过。这不是旧示意原型的结果，也不等于模型标准验证。

约223mm的旧包围盒差异已定位为宽松包围盒测量问题。精确顶点计算后，两解析器包围盒最大差异0.06733mm；原生网格到浏览器的Float32坐标误差最大0.000954mm，后者不是全部几何误差。玻璃、光照和共面接缝仍需视觉确认；原生32条材质转换错误记录未抹除。

当前记录在 `.artifacts/sample-174/`：`fidelity-browser-checks.json`、`current-fidelity-comparison.json`、`native-report.json`、`native-geometry.log`。正面/侧面截图为`fidelity-native-front.png`和`fidelity-native-side.png`，不是生成式图片。

范围及详细结论只维护在[主计划](../../docs/plans/repair-ui-plan.md)和[显示保真文档](../../docs/architecture/ifc-viewer-fidelity.md)中。
