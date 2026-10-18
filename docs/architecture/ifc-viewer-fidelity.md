# IFC 显示保真：解析库调研与样例验收

> 更新：2026-10-10｜状态：用户已提供一个 IFC2X3 及正面/侧面截图，开始单模型真实解析与显示验证。本轮不修改 IFC，不运行 Repair 或 LLM；解析成功、显示覆盖与视觉验收分别记录。
> UI 范围与交互仍由 [唯一主计划](../plans/repair-ui-plan.md)维护；本页只负责解析/显示选型和保真检查，不创建第二套 UI 计划。

## 1. 本次目标

让网页看到的模型来自真实、已写出的 IFC，而不是根据 LLM 文本、ChangeSet 或包围盒重新画一个相似建筑。先保证构件存在性、位置、尺寸、洞口、层级变换、原色和透明度对应正确，再优化光照和显示性能。源文件没有的窗框、玻璃、纹理不能为美观补画；源文件有而解析失败的构件不能悄悄消失。

IFC 是 buildingSMART 定义的开放、厂商中立数据标准，不是一个唯一的“官方渲染器”。源建模工具的内部模型、导出的 IFC、不同查看器的显示并不天然相等。“尽可能相同”应指同一 IFC 的几何与外观数据忠实、与指定查看器可核对；不承诺所有软件像素一致，也不把漂亮截图当作标准符合性证明。[S1]

## 2. 已核查的路线

| 路线 | 官方资料确认的能力 | 对本项目的取舍 |
|---|---|---|
| That Open Components + Fragments + web-ifc | IfcLoader 用 web-ifc WASM 将 IFC 转为 Fragments；有 Highlighter、Hider、相机/剖切等组件；推荐一次转换并缓存 | 最适合快速接入原生网页 BIM 交互，但必须检查导入类别、版本组合、布尔几何和材质实际结果。适合作为首个直接解析候选，不等于已经证明保真最好。[S2–S4] |
| IfcOpenShell/IfcConvert → GLB + 构件映射 → Three.js GLTFLoader | 官方 Python 提供几何 iterator、表面样式/每面材质信息、GLB serializer 及 use-element-guids；Three.js 有官方 GLTFLoader | 与现有 Repair 的几何依赖接近，便于固定同一内核版本、参数和输出文件；需要后端/本地转换，不是纯浏览器解析 IFC。映射/属性按需 API 仍需接线。[S5–S8] |
| xeokit BIM Viewer | 成熟浏览器查看器，有对象树、楼层、隐藏、隔离、剖切、BCF，支持 IFC 转换与 XKT/GLB 路径 | 可作为完整浏览器备选；不能把更换 Viewer 直接视为更换了解析内核。xeokit-convert 的直接 IFC 路径依赖 web-ifc，官方提示其限制，另推荐自己的转换器。SDK 仓库标注 AGPLv3/商业许可，锁版后审核适用条件。[S9–S10] |

没有选用旧 web-ifc-three：其官方仓库已经明确标记 deprecated 并推荐 Components。旧教程所谓“official IFC Loader of Three.js”不意味着 buildingSMART 唯一标准实现。[S11]

## 3. 建议：同一文件小型对照，随后只保留一条主渲染链

先用用户提供的一个 IFC，比较：

- A：That Open 官方导入链，关闭非必要美化，显式检查类别与对象覆盖。
- B：固定版本 IfcOpenShell 重新打开同一 IFC，转换 GLB，交给成熟 Three.js loader 显示。

A/B 是解析与显示排查，不是重新启动四组 LLM 修复实验，不需要模型调用。优先判断完整性、几何、颜色/透明度、选择映射，随后比较加载时间和资源消耗。

以“网页显示尽可能对齐现有 Repair 几何内核”为目标时，B 是更可控的起点；这是架构推断，不是已经测得它在所有 IFC 上优于 web-ifc。若 A 对用户样例完整保真且交互成本更低，可以采用 A。正式阶段不同时长期维护两个主 Viewer。

不要把 That Open 的 Hider 直接假定可用于任意 GLB：其接口面向 Fragment 模型。B 路线可以复用 Three.js 的网格拾取和可见性，并增加薄的构件映射适配；不自写 IFC 布尔/拉伸解析器。[S3,S8]

## 4. “所见即所得”的数据链

```text
实际输入 IFC / 通过发布的 repaired.ifc
    → 从磁盘重新解析
    → 生成显示网格、材质与对象映射
    → 网页显示、点选、隐藏、对比
```

下载的正式结果必须就是当前结果版本所绑定的 IFC，不是将网页网格重新导出成另一份 IFC。显示缓存是可重建派生物，不替代源文件和后端检查。每份缓存绑定输入版本、解析器版本、配置和坐标变换；修复后不能复用旧网格。

候选几何与正式结果区分显示。模型未生成时可以有明确标注的落点/轮廓预览，但不能仅根据 ChangeSet 就显示“修复已完成”。隐藏、剖切、高亮都是显示操作；隐藏构件继续存在于 IFC 和 Repair 输入，下载默认仍含完整模型。

## 5. 六类保真检查

| 检查 | 样例上的具体做法 |
|---|---|
| 构件覆盖 | 以具有预期 Body 表示的构件为分母，逐项登记已生成网格/刻意排除/无几何/解析失败。不能把所有 IFC 实体数量当网格数量；也不能静默丢 Proxy、建筑部件或非修复目标。[S2] |
| 洞口与形体 | 检查墙被真正开孔、窗框/玻璃和门位置、梁柱截面及旋转；从多个视角核对。IfcOpenShell 的 disable-opening-subtractions 会关闭洞口扣除，不能为性能随意打开。[S6] |
| 坐标与精度 | 核对单位、嵌套 placement、mapped item、源坐标与显示居中变换；前后共用同一基准。三角化误差与修复几何容差分开记录，不能默认二者相等。大坐标下保留可逆原点偏移，拾取再转换回源坐标。[S5–S6] |
| 材质与透明度 | 核对源 SurfaceStyle、各子部件/各面材质、透明度及缺省值来源；不统一将所有窗染蓝或设透明。GLB serializer 的默认材质需求与源 IFC 材质分开登记，纹理支持/缺失资源需要实测，不承诺全量保留。[S5,S7] |
| 点选与属性 | 网格节点/片段 ID 必须映射当前 IFC 的真实构件；一个构件多个网格应共同高亮/隐藏。GlobalId/STEP ID/前端编号不可混同，Property 按同一模型版本读取。辅助参照不能映射到另一版模型。 |
| 视觉对照 | 同一 IFC 在用户指定查看器中导入，固定相近相机、视图范围和显示过滤后截图；比较结构与材质，不用光照差异误判几何失败。三维视图仍不等于关系/标准检查。[S12] |

IfcOpenShell 的 GLB 示例允许写入元素 GUID，保留对象映射而非合并成无身份的一整栋网格。GLB 不包含完整 IFC 语义，Property 必须从源 IFC/索引获取，不能声称 GLB 可替代 IFC。[S5,S7]

## 6. 首个 IFC 的轻量验收包

用户只需提供一个代表性 IFC；同时注明希望对照的查看器与版本（例如实际使用的 usBIM/Revit/Bonsai），最好附两张同一 IFC 的整体与门窗细节截图。没有参照截图也可以先做 IFC 数据与两条解析链的对照。

交付：一个可打开的真实 IFC 网页、整体/局部对照图、构件覆盖/失败清单、同视角前后切换（有真实前后文件时）、选取/隐藏/主辅助参照的检查记录。先处理一个模型，不批量导入二十题，也不让 LLM 修模以迎合 Viewer。

模型不上传到第三方在线转换网站；可在本地/自有后端使用开源库完成。样例确认后再锁定具体依赖，不在调研阶段安装完整前端生态或用当前文档示例版本当默认生产版本。

## 7. 当前交互补充与正式接线边界

右键隐藏和一个辅助参照在原型中实现时，仍只作用于明确标注的示意几何。它们验证人机交互，不证明真实 IFC 可渲染。正式接线复用对应引擎可见性/拾取能力；当前手绘房屋及 Plotly/兼容显示不作为正式 IFC 解析链。

## 8. 首个用户样例：实施约定（2026-10-10）

用户附件为 `58fe5a29-4d2d-448e-a752-5c244fd713f7.ifc`，8,573,800 字节，文件头声明 IFC2X3；同时提供正面与侧面截图。截图只作为显示对照，不推断或补画源文件中不存在的几何。当前未知截图所用查看器版本，不宣称像素级对齐或“官方认证”。

本轮先打通 web-ifc 原生解析与成熟 Three.js 显示的最小链，不调用整个 That Open Components 应用，也不把它记为两条解析器已完成对比。IfcOpenShell→GLB 的独立对照仍保留为后续检查。网页只读加载用户本地 IFC、保留真实 expressID/GlobalId、源材质和洞口；点选、右键隐藏、双参照继续按主计划工作。只有一份 IFC 时不生成假“修复后”。

此会话的附件导入被 CodexPro 的文件来源校验拒绝，因此不得宣称源 IFC 已复制进工作树。源码和启动说明可写入 `ui/ifc-viewer/`，真实样例在会话容器中测试；本地网页支持通过文件选择器加载用户持有的同一文件。解析资源来自官方已记录构建，不向任何第三方上传 IFC。实际处理与浏览器记录完成后追加结果，并与尚未验证项分开。

## 9. 本轮执行：原生几何与截图对照（2026-10-10）

用户已批准先跑通实际解析、渲染和两视角比对，再接 Repair。本轮确认本机 WSL Python 3.10.12 已安装 IfcOpenShell 0.8.5；仅恢复与上传附件内容一致的 formal-019/private/reference.ifc LFS 文件，作为用户已提供模型的只读副本使用，不访问其他题目或答案。显示研究不进入修复生产路径。

先执行原生几何提取，逐构件登记成功/失败、三角形、材质、包围盒和日志，导出 GLB；再以这些实际网格渲染正面/侧面，比较用户截图。使用项目内隔离 VTK 依赖做离屏截图，不修改 IFC 几何来适配截图。实际结果将在本节补充；在成功运行前不写通过结论。浏览器原生 web-ifc 与 IfcOpenShell 是不同解析器，测试范围分开记录。没有修复后文件时不提供假修复后视图。

## 10. 当前修订：可访问服务与同源显示（2026-10-10）

用户确认继续几何/外观对齐并保留旋转、点选、查看模式右键隐藏及恢复，暂不接 Repair。先完成以下有限修订，再记录实测结果：

1. 4178 当前不可连接；上一轮 capture_browser.py 的临时服务会在退出时关闭。增加用户可主动启动/停止/查询的本地服务入口；兼容 /ifc-viewer 和 /ifc-viewer/，从 Windows 侧复测 HTTP。仅绑定本机回环，不添加系统服务、开机启动或防火墙规则。
2. 上轮 12 个 IfcMember 包围盒差异先按 Three.js 精确顶点包围盒复算。旋转局部包围盒后的宽松范围不得算成真实构件位移；原始测量保留，修订结果单列。
3. 将已有 IfcOpenShell 0.8.5 实际三角网格接入同一查看器。样例缓存与源字节严格绑定；换文件不能套用旧缓存。web-ifc 可继续读取同一 IFC 属性并提供明确标记的直接解析对照，不混称同一个几何内核。
4. 显示设置不改 IFC：源色与 alpha 保留；色彩空间解释、光照、面朝向/透明物体渲染和几何边线作为显示配置记录。以用户原图核对相近相机下的外观，不用改尺寸、删除源构件或补画方式伪造一致。
5. 对真实模型重新检查旋转/缩放、单独隐藏与恢复、双参照冻结、源文件不变；原图和新截图对照后列出仍未确定的差异，不以网格数相同替代全部几何验收。

### 10.1 实际复核结果（2026-10-10）

当前样例入口默认使用 IfcOpenShell 0.8.5 已提取的原生网格，浏览器用 Three.js 显示；web-ifc 在该入口只读取同一 IFC 的语义数据。独立的 web-ifc 几何入口仅用于对照。原生网格缓存通过源文件逐字节核对后才加载，250/250 个 Body 构件、149,378 个三角形保留；坐标转为浏览器 Float32 的最大绝对误差为 0.0009537 mm。这是从已提取网格到显示缓存的数值误差，不是 IFC 几何/三角化精度的总误差。

上轮约223 mm的12个IfcMember包围盒异常是旋转局部包围盒后的宽松测量问题。改为实际变换顶点的精确包围盒后，web-ifc与IfcOpenShell同源对象范围最大差异为0.0673278 mm，250项均在0.1 mm内；原生网格在网页中的范围与原生提取结果最大差异0.0009362 mm。原旧测量保留在parser-comparison.json，当前实测在current-fidelity-comparison.json，不据包围盒相近宣布曲面、内部拓扑或材质全部一致。

Windows Edge headless＋SwiftShader WebGL2实际运行18项检查全部通过：两种解析路径各自的正面/侧面250构件载入、原生缓存字节对应、三角形数量、鼠标拖动旋转、滚轮缩放、真实对象点选、双参照、右键菜单、单独隐藏、相机与引用保留、撤销及显示全部。另11项Node范围/源字节/颜色/本地HTTP检查通过。记录与截图位于ui/ifc-viewer/.artifacts/sample-174/，没有把旧示意原型测试计入本次。

外观已采用明确的sRGB显示解释、源alpha、透明正向面、几何边线及较窄相机裁剪范围；灰色建筑、橙褐门、窗框和栏杆可对照用户截图。仍有玻璃通透效果、光照/描边与部分共面明暗接缝需要视觉复核；原生日志32条材质转换错误及422条Notice保持原样，不标为零错误验收。此次没有改写IFC，没有Repair/LLM调用。

4178采用显式启动的本地独立进程，不随截图脚本关闭。/ifc-viewer和带末尾斜杠的入口均支持；Open-IFC-Viewer.cmd负责启动并打开样例，Stop-IFC-Viewer.cmd负责停止。服务只在本机可访问，关闭Windows/WSL后需重新启动，不安装开机服务。主计划和本页原位维护。

## 11. IFC2X3 多模型加载核查与范围收紧（2026-10-10）

用户决定优先正确显示现有IFC2X3，不开发测量、剖切、截图导出、视图保存或更多BIM管理功能；剖切以后如需增加仅限固定X/Y/Z。上传/正式下载接口后置，当前保留本地文件选择。

已从dataset/external选定12份、10个来源，经实际Windows Edge文件选择器走通web-ifc/Three.js：12/12加载并完成旋转/缩放/点选隐藏撤销，11份无整件Body缺失。GNI128有4条布尔诊断、Jasmin有23条面片/网格诊断、steel少1块IfcPlate；不把可加载算作全量保真通过。具体结果只维护在[多模型检查](../validation/ifc-viewer-ifc2x3-smoke.md)，原始日志和截图保存，不覆盖174历史保真结论。

已修正失败加载清空旧工作区、适应视图切换方向、换文件轮廓设置不一致；名称和基本属性先展示，原始属性二级展开。9项实际浏览器边界检查通过，15项查看器Node测试通过；没有Repair或LLM调用，没有改源IFC。

## 来源（2026-10-09 查阅，均为项目/标准官方资料）

- S1：buildingSMART IFC 介绍 — https://technical.buildingsmart.org/standards/ifc/
- S2：That Open IfcLoader — https://docs.thatopen.com/Tutorials/Components/Core/IfcLoader
- S3：That Open Hider — https://docs.thatopen.com/Tutorials/Components/Core/Hider
- S4：That Open Highlighter — https://docs.thatopen.com/Tutorials/Components/Front/Highlighter
- S5：IfcOpenShell Geometry processing — https://docs.ifcopenshell.org/ifcopenshell-python/geometry_processing.html
- S6：IfcOpenShell Geometry settings — https://docs.ifcopenshell.org/ifcopenshell/geometry_settings.html
- S7：IfcConvert — https://docs.ifcopenshell.org/ifcconvert.html
- S8：Three.js GLTFLoader — https://threejs.org/docs/pages/GLTFLoader.html
- S9：xeokit BIM Viewer — https://github.com/xeokit/xeokit-bim-viewer
- S10：xeokit-convert — https://github.com/xeokit/xeokit-convert
- S11：Deprecated web-ifc-three — https://github.com/ThatOpen/web-ifc-three
- S12：Three.js Color Management — https://threejs.org/manual/en/color-management.html
- S13：web-ifc 原仓库 — https://github.com/ThatOpen/engine_web-ifc
