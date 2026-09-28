# IFC 门窗的几何、类型、材料与部件

本页保留窗结构问答、hxp N001 实例及 2026-09-24 源表示调查。实施范围见[唯一计划 v1.0](../architecture/text2ifc-component-plan-v1.0.md)，当前实验结论见[结果](../validation/ifc2text/component-v26/README.md)。调查中的表示种类不等于系统全部支持。

## 附录 A：IFC 结构与 N001 示例

系统模板是本项目的建模规则；IFC Type 是类型对象；Representation 是形状；Material 是物理材料；SurfaceStyle 是显示外观。IFC2X3 的 IfcWindowStyle 是窗类型，不是颜色 Style。它们通过不同引用连接，不是一个单一上下级目录。

BRep 用面、边界及连接关系围出实体。长方体也可表示为简单 BRep，更一般的 BRep 可包含曲面，不等于密集三角网格。工程师通常用截面、尺寸、挤出、扫掠、切孔和阵列，软件计算边界；导出后不一定保留完整参数历史。首版借鉴参数化构造，不逐面生成。

源为 `dataset/external/bimnet/hxp.ifc`，IFC2X3；SHA-256：`31f8f5a05b1965e2ab11122559385203229f316a4ea8fe15feec31c86d80d942`。N001 是 #2618，GlobalId=`1N$DqFwUP2Cfj_f4x$_L4e`，Name=`单扇百叶窗:高1100宽850:28872`，ObjectType=`单扇百叶窗:高1100宽850`，Tag=`28872`，OwnerHistory=#41，Description 为空。

```text
#2618 IfcWindow
  ObjectPlacement -> #10379
  Representation -> #2611 ProductDefinitionShape
    -> #2609 Body / MappedRepresentation
    -> #2607 IfcMappedItem (source=#2591, target=#2293)
    -> #2591 IfcRepresentationMap (origin=#2590)
    -> #2588 Body / SweptSolid
    -> #2380、#2390 ... #2510：14 个叶片挤出体
       #2536：带孔窗框挤出体
  Type：经 #10114 IfcRelDefinesByType -> #2593 IfcWindowStyle
  Material：经 #10052 IfcRelAssociatesMaterial -> #2597
  Installation：经 #10375 IfcRelFillsElement -> #10369 开口 -> #842 墙
```

类型 #2593 的 RepresentationMaps 包含 #2591，但仅有关联 Type 不够，实例必须通过 MappedItem 实际引用它。映射、比例和实例放置均影响结果；修改 OverallWidth 不会自动重画叶片。本例 #2590／#2293 为单位变换、比例 1。

类型名为“高1100宽850”，ConstructionType／OperationType=NOTDEFINED，ParameterTakesPrecedence=False，Sizeable=False，#2592 LiningProperties 几何参数为空。实例 IsExternal=True，Reference=“高1100宽850”，Manufacturer 为空；未填写不等于已知没有。

以下是设计阶段的人工说明示例；当前公开输出由版本化描述器生成，源 STEP 编号只用于本页解释，不作为生成端额外输入：

> **N001 窗**：名义宽 850、高 1100。局部 X 沿宽、Y 沿深、Z 向上。局部原点的世界坐标为 (6196,3439.305336082839,−285)；X 指向世界 (0,−1,0)，Y 指向 (1,0,0)，Z 指向 (0,0,1)。填充源 #10369 开口，宿主为 #842“基本墙:墙240:7073”。
>
> **N001/frame**：在局部 XZ 平面定义外矩形 X=0…850、Z=0…1100，内孔 X=40…810、Z=40…1060；沿 +Y 挤出 240，Y=0…240，框边宽 40。
>
> **N001/slat-01…14**：每片以居中 60×20 矩形截面沿 +X 挤出 770；起始截面中心为 (40,120,zₖ)，zₖ=90+k×920/13，k=0…13。60 边单位方向为 (0,−1/√2,+1/√2)，20 边方向为 (0,−1/√2,−1/√2)。由此确定倾向、尺寸、间距与首片位置，不能只写“倾斜 45 度”。

排列规则与源解析值最大残差约 `1.38×10⁻¹¹ mm`，仅证明源规律，不是新编译器验证。

材料 #2597 为“金属漆_冷灰”，#10052 同时关联实例、类型及其他对象，不能推断底层合金、涂层厚度或逐项材料。十五项的 StyledItem 指向 #2539 SurfaceStyle／#2538 Rendering：RGB≈(0.24706,0.27843,0.30196)，Transparency=0，SpecularColour=0.5，SpecularExponent=64，ReflectanceMethod=NOTDEFINED。高光仅记录为源事实，首版只承诺颜色／透明度，不能宣称完整外观等价。

源窗在 #132“标高 3”（40 mm），宿主墙在 #126“地板标高”（−1140 mm），存在归层不一致。既有实验在副本中随宿主归层；不得修改源或把归一化结果称为原始关系。

现有 basic_filling/1.0 有 window-single、window-double-vertical、door-left、door-right 四种模板。它们内部能创建多个实体，但不等于支持任意部件输入。“单玻璃窗 850×1100、框宽 40”不能代替十四片百叶描述。

## 附录 B：数据调查与证据

2026-09-24 定向抽查八份文件，七份可读取，一份 IFC2X2 未评估；八份源 hash 前后相同。只做结构读取，未运行生成、完整 schema 校验或保真测试。按 Body 展开映射，以实例计几何项；这些数量不是唯一共享定义数或语义部件数。

| 文件（相对 dataset/external） | 应用／IFC | 窗 | 门 |
|---|---|---|---|
| `bimnet/hxp.ifc` | Revit 2020／2X3 | 3 窗，45 挤出体 | 7 门，50 挤出体＋8 BRep |
| `xbim-essentials-examples/House.ifc` | Renga 2.2／2X3 | 23 个映射面模型 | 19 个映射面模型 |
| `bim-whale-ifc-samples/TallBuilding/IFC/TallBuilding.ifc` | Revit 2021／2X3 | 21 窗，84 挤出体 | 5 门，39 BRep＋12 挤出体 |
| `gni-bim-dataset/2025_BIMfundamentals/model_0.ifc` | Revit 2024／4 | 73 窗，410 面集 | 25 门，194 面集 |
| `scan-vs-bim-quality/20260916/Test model 1.1.ifc` | SketchUp 2015／2X3 | 5 窗，各一 BRep | 3 门，各一 BRep |
| `ifc-bench/projects/fantasy_hotel_1/arc.ifc` | Revit 2024／4 | 73 窗，410 面集 | 25 门，194 面集 |
| `gni-bim-dataset/normalized-ifc4/model_80.ifc` | Revit 2026／4 | 121 窗，786 面集 | 10 门，101 面集 |
| `duraark/SGD_Munkerud/SGD_Munkerud_Arch-1.ifc` | 2X2_FINAL | 未评估 | 当前库不支持，未转换 |

原始证据：[结构统计](../reports/ifc-representation-survey-2026-09-24/source-structure-survey.json)、[实体展开与同源检查](../reports/ifc-representation-survey-2026-09-24/supplementary-inspection.json)。首次在 IFC2X2 文件读取退出的情况保留，未通过改版本字符串绕过。

House 窗 #9143 的一个面模型含 58 个面；TallBuilding 门 #10949 有 39 个 BRep、1,102 个面；GNI 窗 #6843 有五个面集、四十个面；SketchUp 窗 #3677 有一个 BRep、十四个面且无 Type。面数、几何项数和部件数不能混用。

GNI model_0 与 fantasy_hotel 的 98 个门窗 GlobalId 集合相同，文件字节及完整 Body 引用文本不同，尚未证明几何相等；评估时按同源组处理。本次可读门窗实例上未发现 ShapeAspect，不能据此推断 IFC4 类型映射也没有；Renga 门窗使用 MappedItem，但关联 Type 未携带 maps。各关系必须分别读取。

墙板也有多种表示：hxp 为挤出，House 墙含 SweptSolid／Clipping／CSG，TallBuilding 墙为 Clipping，GNI 有 SweptSolid 和 Tessellation。数据证明应区分语义组织与底层表示，不证明当前系统已支持这些形式。

扩展前的历史 hxp 诊断匹配 66 个构件、无缺失或多余，修复后候选仍有 14 个几何超差，Audit 接受不代表保留源细节。仅替换三个开口的离线诊断降为 10 个门窗差异，不是新 LLM 自动成功。D007 的八个 BRep 仅五个已证明可转正棱柱，其余三项仍须返回不支持。首版不能承诺整栋 hxp 完整保真。

## 附录 C：标准与工程依据

- [IFC2X3 IfcWindow](https://standards.buildingsmart.org/IFC/RELEASE/IFC2x3/TC1/HTML/ifcsharedbldgelements/lexical/ifcwindow.htm)、[IfcWindowStyle](https://standards.buildingsmart.org/IFC/RELEASE/IFC2x3/TC1/HTML/ifcsharedbldgelements/lexical/ifcwindowstyle.htm)：实例、类型、参数与形状。
- [IFC2X3 IfcShapeRepresentation](https://standards.buildingsmart.org/IFC/RELEASE/IFC2x3/TC1/HTML/ifcrepresentationresource/lexical/ifcshaperepresentation.htm)、[IfcShapeAspect](https://standards.buildingsmart.org/IFC/RELEASE/IFC2x3/TC1/HTML/ifcrepresentationresource/lexical/ifcshapeaspect.htm)：表示约束与部件分组。
- [IfcOpenShell ShapeAspect API](https://docs.ifcopenshell.org/autoapi/ifcopenshell/api/geometry/add_shape_aspect/index.html)、[几何创建](https://docs.ifcopenshell.org/ifcopenshell-python/geometry_creation.html)：实现基础，不等于项目能力已完成。
- [Autodesk 构造工具](https://help.autodesk.com/cloudhelp/2023/ENU/Revit-Customize/files/GUID-478961FB-DD57-445E-831F-5B83E02F0B78.htm)、[族增量测试](https://help.autodesk.com/cloudhelp/2022/ENU/Revit-Customize/files/GUID-772026BB-2A3E-4193-A339-75E019AA8DCC.htm)、[IFC 导出选项](https://help.autodesk.com/cloudhelp/2025/ENU/Revit-DocumentPresent/files/GUID-E029E3AD-1639-4446-A935-C9796BC34C95.htm)：参数建模与导出是不同层次。
- [IfcFacetedBrep](https://standards.buildingsmart.org/IFC/RELEASE/IFC4_3/HTML/lexical/IfcFacetedBrep.htm)、[IfcAdvancedBrep](https://standards.buildingsmart.org/IFC/RELEASE/IFC4_3/HTML/lexical/IfcAdvancedBrep.htm)、[Khronos 网格说明](https://github.com/KhronosGroup/glTF-Tutorials/blob/main/gltfTutorial/gltfTutorial_009_Meshes.md)：BRep 与网格的区别；实际输出仍以 IFC2X3 合同为准。
