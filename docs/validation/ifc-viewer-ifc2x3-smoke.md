# IFC2X3 查看器：现有数据集加载与基础交互检查

> 2026-10-10｜工作树：bimnet-ui / codex/ui-development。此页维护这轮实际结果，不是另一套 UI 计划。范围由 [主计划 §2.1](../plans/repair-ui-plan.md)规定。

## 1. 结论

从现有 dataset/external 预先选定 12 个 IFC2X3、10 个来源集合，18,386–12,109,172 字节。通过 Windows Edge headless + SwiftShader WebGL2 中实际“打开 IFC”文件选择器加载，不使用174预制网格代替这些文件。12/12打开并显示，12/12完成旋转、缩放、实际构件点选、单件隐藏和撤销；所有源文件处理前后逐字节不变。

11/12 没有发现应显示 Body 构件的整件网格缺失；9/12 没有 web-ifc 日志诊断。钢结构文件少1块板；另外两份有布尔/面片诊断。因此“12个都可加载”不等于“12个全部几何/外观正确”。本轮没有运行完整 IFC validator 或逐面形状等价验证，也没有把结果外推为整个库或全部 IFC2X3 支持。

## 2. 固定样本与实际结果

样本选择在运行前写入 [dataset-samples.json](../../ui/ifc-viewer/tests/dataset-samples.json)。原生 IfcOpenShell 只读枚举源 Schema 和应显示 Body 对象；网页实际几何由现有 web-ifc 0.0.79 读取、Three.js r186显示。174原生网格另做已有回归，不计入这12个新样本。

| 样本 | 大小（MB，十进制） | 应显示Body | 网页有网格对象 | 诊断条数 | 结论 |
|---|---:|---:|---:|---:|---|
| Asunisoft builtModel | 0.018 | 9 | 9 | 0 | 可加载；未发现整件缺失 |
| BIM2Modelica MultiZoneBuilding | 2.953 | 63 | 63 | 0 | 可加载；未发现整件缺失 |
| BIMcollab STR | 0.455 | 241 | 241 | 0 | 可加载；未发现整件缺失 |
| BIMNet hxp | 0.315 | 46 | 46 | 0 | 可加载；未发现整件缺失 |
| BIMNet b6b | 8.154 | 493 | 493 | 0 | 可加载；未发现整件缺失 |
| buildingSMART Duplex | 2.381 | 215 | 215 | 0 | 可加载；未发现整件缺失 |
| buildingSMART Esplanades | 12.109 | 1958 | 1958 | 0 | 可加载；未发现整件缺失 |
| GNI model_128 | 6.903 | 1137 | 1137 | 4 | 可加载；有布尔计算诊断 |
| OpenSourceBIM Jasmin | 3.218 | 62 | 62 | 23 | 可加载；有面片/网格类型诊断 |
| IfcOpenHouse | 0.104 | 34 | 35 | 0 | 34个Body齐全，另有源IfcSite地形1个 |
| STEP Tools steel sculpture | 0.316 | 351 | 350 | 1 | 可加载，但少1块IfcPlate，未通过完整显示检查 |
| web-ifc example | 0.414 | 115 | 115 | 0 | 可加载；未发现整件缺失 |

最终轮实际文件载入至报告就绪约0.186–5.970秒。浏览器/系统已有缓存，不能据两轮时间差宣布性能提升；也不是大模型压力测试。

恢复了选定的12个LFS对象，仅对其中本机无内容的10个路径定向下载；没有展开全库或子模块，没有修改数据及许可登记。许可信息仍以dataset原manifest为准；未上传模型到外部转换服务，未发布或再分发样本。

## 3. 发现的渲染边界

**steel / #2942 / IfcPlate / bp6：** web-ifc记录 `GetProfileByLine() unexpected profile type`，没有生成该板网格。独立调用IfcOpenShell对同一对象得到12顶点、14三角形，但仍记录 `IfcCenterLineProfileDef` 转换错误和无材质警告。因此本轮不以另一内核有网格就自动宣布源几何正确，更没有补画一个盒子或修改源IFC。本轮保留这一未解决项，后续围绕该轮廓解释/已认可的原生转换检查，不扩成新产品功能。

**GNI model_128：** 4条 `BoolProcess() bool aborted due to empty source or target`。整件覆盖1137/1137，但布尔结果局部仍需核对。

**Jasmin：** 16条 `TriangulateBounds() No basis found for brep`、7条 `GetMesh() unexpected mesh type`。整件覆盖62/62，不代表所有子面片齐全。

**IfcOpenHouse：** 额外网格为源对象 #24 / IfcSite；不是多画一个建筑。Body枚举和所有可显示网格的分母不同，单独说明。

现在页面把“有解析提示”和“显示不完整”分别提示。缺失ID在详情中可见，不再只显示笼统“加载成功”。未将上述诊断隐藏、删除或从统计中剔除。

## 4. 已修正的基本使用问题

先修改主计划，再运行失败可复现检查，最后修代码并复测。

- 失败导入：新模型在独立临时状态完成解析和有限几何检查后才替换当前模型。无效文本/空IFC失败时保留原模型、草稿、参照、隐藏状态与相机；错误提示明确仍在查看原文件。
- 适应视图：保持当前朝向，按可见对象重新适配，不再自动跳回固定侧面。全部隐藏时提示先恢复显示。
- 轮廓设置：连续换文件时，按钮状态与新模型轮廓线一致。
- 首屏与属性：保留两个模式和短操作提示；按需属性先呈现名称/类别/ID，实例/类型原始数据二级展开。没有增加模型树、搜索、剖切、测量或视图保存。

9项真实浏览器边界检查全通过（修改前有7项失败；首次测试脚本曾遇到可选字段缺失KeyError，修正记录方式后复现，不算产品失败）。15项查看器Node测试通过。174的18项真实浏览器回归通过；测试范围与多模型加载数字分别登记，不混成一个“功能全部通过”指标。

## 5. 证据与复现

- 预选清单：`ui/ifc-viewer/tests/dataset-samples.json`。
- 修改前：`ui/ifc-viewer/.artifacts/dataset-ifc2x3/baseline/`。
- 当前：`ui/ifc-viewer/.artifacts/dataset-ifc2x3/current/results.json`、`summary.json`、逐文件`*-parser.json`和真实浏览器PNG。
- 全部12个截图总览：`ui/ifc-viewer/.artifacts/dataset-ifc2x3/current/contact-sheet.png`。
- 使用边界：`usability-red/checks.json`、`usability-after/checks.json`。
- 已有174回归：`ui/ifc-viewer/.artifacts/sample-174/fidelity-browser-checks.json`。

```text
node ui/ifc-viewer/launcher.mjs start
node --test ui/ifc-viewer/tests/*.test.mjs
python3 ui/ifc-viewer/dataset_smoke.py --run <新的本次记录名>
python3 ui/ifc-viewer/verify_usability.py --label <新的使用检查记录名>
```

脚本从WSL调用独立Windows Edge配置，不使用用户日常浏览器配置。每次记录目录必须不存在，避免覆盖真实失败。源文件必须先恢复成真正IFC而非LFS指针。测试无需LLM、Repair、数据库或新的上传接口。

## 6. 功能范围

本节的模型树安排已由用户后续明确要求更新，当前实际实现见第7节；不扩大其他工具范围。

剖切不做；后续确有必要时只限固定X/Y/Z。测量不做。截图导出/视图保存/BCF不做（上面的PNG只是开发核查材料）。上传及正式结果下载接口后置。真实修复前后显示仍在后续Repair接线阶段，没有用假输出填充。

下一步优先处理上述3份文件的明确解析诊断，并继续保持基本操作，不通过增加工具栏功能代替正确渲染。

## 7. 用户反馈后的模型树／属性／高亮复测（2026-10-10）

按用户截图要求，先更新唯一主计划，再增加失败测试、复现174样例#1895墙体的选中斑驳，最后实现统一选中材质、类别模型树与可读属性。未改源IFC或底层解析几何。选中材质保留深度测试，用有界负偏置解决共面竞争；不使用穿透高亮。关闭选择后恢复源材质、透明度与轮廓设置。

重新执行 `dataset_smoke.py --run tree-properties`，仍是事先选定的12个源文件，真实文件选择器12/12打开，旋转/缩放/单件隐藏撤销12/12；模型树所有类别计数与IfcOpenShell独立枚举12/12相同；每个文件选一个实际可见对象，Property中ID与源对象一致且该次属性读取无错误12/12。后者是抽样属性检查，不是全文件所有稀有属性表达的认证。源文件逐字节不变。结果仍为11份无整件Body缺失、3份有前述诊断；本次UI修改没有消除steel #2942缺网格问题。

专项 `verify_inspection.py --label candidate-2` 在实际Edge/WebGL2通过17项检查：同一墙体选取、可读Pset、原始数据默认收起、树数量、GUID搜索、树三维关联、源IFC下载字节一致；另用受控重叠面WebGL测试验证共面选择色及真实前景遮挡，三种屏幕无横向溢出。真实墙的修正前后截图可人工核对，不以测试平面冒充实际IFC。9项使用边界和已有18项174交互回归通过；限定Node回归67项通过（查看器24＋旧交互原型43），没有全库测试或Repair调用。

证据路径：

- `ui/ifc-viewer/.artifacts/inspection/baseline/`：原始斑驳与旧属性截图，模型树尚无的负例。
- `ui/ifc-viewer/.artifacts/inspection/candidate-2/`：17项专项记录、模型树、修正后墙体、可读属性截图与实际下载文件。
- `ui/ifc-viewer/.artifacts/dataset-ifc2x3/tree-properties/`：12文件复测结果、源码属性/类别独立核对及逐模型截图。
- `ui/ifc-viewer/.artifacts/dataset-ifc2x3/inspection/`：9项使用边界复测记录，脚本 `verify_usability.py --label inspection` 已实际运行通过。

当前模型树按用户给图采用类别组织，非伪造的空间层级：Project/Site/Building/Storey/Space类目录及Elements→类→对象，所有名称、计数与属性来自当前文件。点击目录仅展开，叶子遵循查看/选中提交模式；没有网格的对象仍可看属性，但不会显示一份替代几何。
