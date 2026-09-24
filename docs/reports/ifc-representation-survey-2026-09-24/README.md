# 现有 IFC 如何保存门窗和建筑几何

日期：2026-09-24。为[门窗部件计划 v0.2](../../architecture/component-described-door-window-plan.md)进行的只读调查。检查现有数据，不生成模型、不转换或修复源文件、不调用 LLM。

## 结论

**部件描述是合理的上层组织方式，但“每个部件必须是一个挤出体”不足以覆盖现有数据。** 同一扇门可以有多个挤出体，也可以有几十个 BRep；另一份文件可能把整扇窗放进一个面模型。表示项的数量不是建筑部件的数量，源文件也不一定标明“这块就是把手”。

建议沿工程建模思路保留“构件→部件→几何与放置”的层次。首版按已确认范围做挤出、旋转放置和重复排列；后续按实际缺项增加扫掠、旋转体、布尔或边界几何，不逐个添加窗型模板。**旋转已有实体的位置，与绕轴生成一个旋转体，是不同能力；后者未纳入首版。**

## 1. 样本和测量方法

按不同来源、导出软件与 IFC 版本有目的地选取八个现有文件，七个可打开，一份 IFC2X2 未评估。这不是随机抽样，不能推算整个数据集的比例。目录名是数据来源，实际建模软件以 IfcApplication 为准；例如 xBIM 示例里的 House 是 Renga 导出，不是 xBIM 建模。

使用仓库环境的 IfcOpenShell 读取门、窗、墙、板；只统计 Body 表示，递归展开 IfcMappedItem，记录实际表示项类别、挤出截面、类型映射和 ShapeAspect。映射按每个实例展开计数；布尔结果按顶层项统计，未展开为独立建筑部件。类型／ShapeAspect 计数限定为拥有 Body 的这些对象。

八份文件的前后 SHA-256 一致。精确路径、hash、应用版本、单位、实体号和例子见 [source-structure-survey.json](source-structure-survey.json)；单窗／单门进一步展开与同源检查见 [supplementary-inspection.json](supplementary-inspection.json)。此次没有完整 schema 校验、曲面距离测量或跨软件显示验证，因此“读到某种表示”不等于“已验证文件完全合法”或“我们的编译器已经支持”。

首次读取在第四份文件因 `Unsupported schema: IFC2X2_FINAL` 退出；随后增加头部版本识别，保留其未评估状态并完成其他文件。没有修改源版本字符串让它假装成为 IFC2X3。

## 2. 文件中实际采用什么表示

表中几何项数量是按所有门窗实例展开后的总量，不是唯一共享定义数。

| 文件／软件 | IFC | 窗 | 门 | 墙／板的补充观察 |
|---|---|---|---|---|
| [hxp](../../../dataset/external/bimnet/hxp.ifc)，Revit 2020 | 2X3 | 3 扇，映射到 45 个挤出体 | 7 扇，映射到 50 个挤出体＋8 个 faceted BRep | 34 墙、1 板的 Body 均为挤出；洞口关系另计 |
| [House](../../../dataset/external/xbim-essentials-examples/House.ifc)，Renga Architecture 2.2 | 2X3 | 23 扇，映射到 23 个 FaceBasedSurfaceModel | 19 扇，映射到 19 个 FaceBasedSurfaceModel | 46 墙中 27 SweptSolid、15 Clipping、4 CSG；13 板为挤出 |
| [TallBuilding](../../../dataset/external/bim-whale-ifc-samples/TallBuilding/IFC/TallBuilding.ifc)，Revit 2021 | 2X3 | 21 扇，映射到 84 个挤出体 | 5 扇，合计 39 个 faceted BRep＋12 个挤出体 | 24 墙为 Clipping，5 板为挤出 |
| [GNI model_0](../../../dataset/external/gni-bim-dataset/2025_BIMfundamentals/model_0.ifc)，Revit 2024 | 4 | 73 扇，410 个 PolygonalFaceSet | 25 扇，194 个 PolygonalFaceSet | 墙同时有 SweptSolid 与 Tessellation；板主要是挤出 |
| [Test model 1.1](<../../../dataset/external/scan-vs-bim-quality/20260916/Test model 1.1.ifc>)，SketchUp Pro 2015 | 2X3 | 5 扇，各一个直接 Brep | 3 扇，各一个直接 Brep | 6 墙、2 板也直接采用 Brep |
| [fantasy_hotel_1](../../../dataset/external/ifc-bench/projects/fantasy_hotel_1/arc.ifc)，Revit 2024 | 4 | 73 扇，410 个 PolygonalFaceSet | 25 扇，194 个 PolygonalFaceSet | 与 GNI model_0 的门窗 GlobalId 集合相同，不能当作独立新建筑证据 |
| [GNI normalized model_80](../../../dataset/external/gni-bim-dataset/normalized-ifc4/model_80.ifc)，Revit 2026 | 4 | 121 扇，786 个 PolygonalFaceSet | 10 扇，101 个 PolygonalFaceSet | 55 墙中 47 Tessellation、8 SweptSolid；板混合采用两种表示 |
| [DURAARK Arch-1](../../../dataset/external/duraark/SGD_Munkerud/SGD_Munkerud_Arch-1.ifc) | 2X2_FINAL | 未评估 | 未评估 | 当前读取库不支持；未转换 |

GNI model_0 与 fantasy_hotel 的文件 hash 不同，但 98 个门窗的 GlobalId 集合相同、示例与表示数量一致。完整 Body 前向引用文本并非完全一致，尚不能宣称几何相等；评估时保守放进同一来源组，避免派生副本泄入独立测试集。

### 几个具体例子

- House 的 `#9143 IfcWindow`：Body→MappedItem→SurfaceModel→一个 IfcFaceBasedSurfaceModel→一个 connected face set，含 58 个 IfcFace。这个“一个项”不代表窗只有一个建筑部件；也不能把 58 个面叫作 58 个部件。
- TallBuilding 的 `#10949 IfcDoor`：一扇双扇玻璃门映射到 **39 个 IfcFacetedBrep**，向前遍历含 1,102 个 IfcFace。它不是三十九扇门；逐面文字描述会很长，且未必恢复参数化设计意图。
- GNI model_0 的 `#6843 IfcWindow`：映射后的 Tessellation 含五个 IfcPolygonalFaceSet，遍历到四十个 IfcIndexedPolygonalFace。IFC4 的这个实体不能直接写进当前 IFC2X3 输出。
- SketchUp 文件的 `#3677 IfcWindow`：直接 Body/Brep，一个 IfcFacetedBrep，十四个面，没有关联 Type。可见“没有 Type”本身不等于“没有门窗几何”；形状准确性仍需独立检查。

本次可读样本中的门窗，在实例 ProductDefinitionShape 上都没有 ShapeAspect；GNI 某些板有。hxp、TallBuilding 和 GNI 门窗的关联类型带 RepresentationMaps；Renga House 虽使用 MappedItem，但其关联类型未携带 maps。**MappedItem 的源引用、Type 关联与 ShapeAspect 应分别读取，不能由其中一个推断另两个存在。** 本调查没有穷尽 IFC4 类型 maps 上的所有 ShapeAspect，不将实例缺失扩大为全文件不存在。

## 3. 官方标准和工程软件怎样做

### IFC 输出不是唯一的建模方法

IFC2X3 对窗的 Body 给出 SweptSolid、SurfaceModel、Brep 及映射形式。这意味着同一类建筑对象可以使用不同几何表示；表示类型要与内部项匹配。不能仅凭文件来自工程软件就忽略 schema 或交换视图要求。[IFC2X3 IfcWindow](https://standards.buildingsmart.org/IFC/RELEASE/IFC2x3/TC1/HTML/ifcsharedbldgelements/lexical/ifcwindow.htm)

SweptSolid 通过截面和生成方式表达形状；Brep 通过包围实体的面和拓扑表达形状；SurfaceModel 表达面集合，不能未经检查当作封闭有体积的实体。通用 SolidModel 可容纳扫掠、布尔和 BRep，但“schema 可表达”不保证所有门窗交换视图和软件接受混合方式。[IFC2X3 IfcShapeRepresentation](https://standards.buildingsmart.org/IFC/RELEASE/IFC2x3/TC1/HTML/ifcrepresentationresource/lexical/ifcshaperepresentation.htm)

ShapeAspect 是标准提供的部件分组机制。IFC2X3 的 PartOfProductDefinitionShape 指向实例 ProductDefinitionShape；不能照搬 IFC4 的用法把它挂在 RepresentationMap 上。首版实例几何＋ShapeAspect 的方向合适，但我们的部件编号仍是项目约定，不等于第三方软件自动理解这些编号。[IFC2X3 IfcShapeAspect](https://standards.buildingsmart.org/IFC/RELEASE/IFC2x3/TC1/HTML/ifcrepresentationresource/lexical/ifcshapeaspect.htm)、[IfcOpenShell add_shape_aspect](https://docs.ifcopenshell.org/autoapi/ifcopenshell/api/geometry/add_shape_aspect/index.html)

### 工程师在编辑器中定义形状，再导出表示

Revit 的族几何工具包含挤出、放样、旋转体、扫掠、扫掠放样及空体切割。其建议是逐步构建参数化几何，并在每次增量中改变参数进行检验。我们可借鉴这种做法：用构造步骤和尺寸定义部件，先对单门／单窗验证，再放进建筑，而不要求 LLM 编写全部三维顶点。[Autodesk 几何工具](https://help.autodesk.com/cloudhelp/2023/ENU/Revit-Customize/files/GUID-478961FB-DD57-445E-831F-5B83E02F0B78.htm)、[族几何与增量测试](https://help.autodesk.com/cloudhelp/2022/ENU/Revit-Customize/files/GUID-772026BB-2A3E-4193-A339-75E019AA8DCC.htm)

不过，工程软件的内部建模过程与导出 IFC 并非一一对应。Revit 导出选项允许不同几何细节及混合 Solid Model；本次文件也实际出现挤出、BRep 和面集。由此只能推断导出表达具有多样性，不能根据一个 BRep 倒推原作者一定使用了某种建模命令。[Revit IFC 导出选项](https://help.autodesk.com/cloudhelp/2025/ENU/Revit-DocumentPresent/files/GUID-E029E3AD-1639-4446-A935-C9796BC34C95.htm)

IfcOpenShell 提供原生几何、网格、映射和形状分组 API，说明工程实现存在可复用基础。它并不会自动替本项目完成从中文语义到截面、拓扑和尺寸的推导，也不证明导出的形状满足 1 mm。[几何创建](https://docs.ifcopenshell.org/ifcopenshell-python/geometry_creation.html)、[网格表示 API](https://docs.ifcopenshell.org/autoapi/ifcopenshell/api/geometry/add_mesh_representation/index.html)

## 4. 对 hxp 重建路线的判断

| 路线 | 能做什么 | 代价及与当前任务的关系 |
|---|---|---|
| 部件＋参数化构造 | 用框截面、叶片尺寸、间距、放置等形成形状；易读、易修改 | 最适合当前首版。源未保留参数时仍须可靠识别，不能凭名义尺寸猜测 |
| 部件＋更多构造操作 | 用扫掠做弯曲杆件、旋转体做轴对称件、布尔做切口 | 沿当前架构逐步扩展，需逐项定义输入、拓扑和比较；首版不承诺实现 |
| 部件＋直接 BRep／面集 | 对不适合参数化的形状直接表达面和拓扑，或确定性编码源几何 | 保留源形状潜力较高，但文本可能退化为大量顶点和面；可编辑性及纯文本任务价值需另评估 |
| 工程软件参数族／外部构件库 | 引用已存在的详细门窗，由软件生成或放置 | 有工程价值，但依赖库、软件版本与精确匹配；公开输入增加资源引用，不能与当前纯文本重建结果混算 |

推荐保留部件层，逐步丰富几何表达，而不是推翻现有架构。当前 hxp 大部分门窗是挤出体，适合先验证；D007 三个未证明可转单挤出的 BRep 仍需返回人工讨论。**“先做门和窗”可降低定位成本，但不能因此宣称已经能完整复现 hxp。**

对源为平面 BRep 的对象，准确保留其平面边界不必一定近似；对真实曲面离散成多边形则存在近似误差。是否满足 1 mm 要看源表示、编译结果和测量，不由表示名称决定。先保留原生解析圆和截面，避免无理由地把所有形状网格化。

本次调查没有决定引入新 CAD 后端、迁移 IFC4 或使用外部构件库。上述路线是后续遇到具体不支持项时可讨论的选择。
