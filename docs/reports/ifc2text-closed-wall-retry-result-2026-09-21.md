# IFC2Text：显式闭合单墙真实复验与容差说明

日期：2026-09-21。执行代码先冻结于 `01a52c06`，随后完成两次真实Provider调用。仅处理已经授权的W013扣洞前单墙，没有修改text2IFC生产代码、Prompt、Schema、Compiler或既有20 mm比较阈值。

## 1. 结论

真实公共Brief返回ready；现有Generator输出合法的闭合polygon；原始输出无需人工补点即由现有编译器生成IFC2X3，并重新打开进行几何检查。该次单墙复验通过。旧未闭合失败及离线补点反事实均保留，本轮文件不是它们的改名或复制。

当前结果说明：对于这面单一竖直拉伸多边形墙，把真实轮廓和显式闭合写清楚，既有正向链可以生成所需几何，不必重写编译器或修改Generator系统Prompt。每种描述仅一次真实试验，不能证明统计因果、任意特殊墙支持或整栋重建成功。

## 2. 轮廓合理性与0.055 mm的含义

公开轮廓有5个不同顶点，末尾重复首点；检查确认闭合、无自交、面积大于零、底标高-1140 mm、拉伸高度2160 mm。这里的“合理”指对源墙扣洞前几何的有效描述，不代表原建筑设计或工程合理性获得认证。

此前11条轮廓中最大距离是0.0552060993 mm，报告约写成0.055 mm；它是测量结果，不是容差。对当前W013，本轮源/文本及源/真实重建轮廓距离都是0.0546971478 mm。

坐标以mm保留一位小数时，单轴舍入最多0.05 mm，对应二维顶点位移最多约0.07071 mm（在顶点对应与边连接方式保持时）。因而把0.055 mm当通用阈值会误拒合理的舍入结果，而且原11条最大值本身略超过0.055。拓扑有效性也不能仅靠小距离证明。

本轮在调用前新增0.1 mm的单墙几何诊断检查，依据上述舍入上界与数值余量，不是依据这次结果反调门槛。原20 mm比较口径仍保留。0.1 mm也不等于施工规范容差或IFC RepresentationContext.Precision；后者是几何上下文的数值精度，本轮未修改。

## 3. 真实结果

| 检查 | 结果 |
|---|---:|
| 公共Brief | ready |
| Generator合同 | formal，valid=true |
| 原始多边形点列 | 显式闭合，无人工修正 |
| 编译/重开 | 成功，IFC2X3，1面IfcWall |
| 截面类型 | IfcArbitraryClosedProfileDef |
| 源墙→公开文本轮廓距离 | 0.0546971478 mm |
| 源墙→真实重建轮廓距离 | 0.0546971478 mm |
| 公开文本→真实重建轮廓距离 | 约4.55e-13 mm，数值计算量级 |
| 源/重建包围盒坐标最大差 | 0.0476015334 mm |
| 公开底/顶标高与重建差 | 约2.27e-13 mm |
| 源/重建平面面积 | 100135.0124 / 100143.0400 mm² |
| 面积对称差 | 36.4027 mm² |
| 0.1 mm单墙诊断 | 通过 |

轮廓距离使用加密离散对称Hausdorff（densify=0.1），同时报告面积和包围盒，不将离散度量声称为任意连续曲面精确证明。数值结果显示本例新增的模型/编译几何偏差处于计算误差量级，源/重建约0.0547 mm的差异主要已发生在一位小数公开文本处。

本轮不含源墙洞口、材料、门窗或空间；没有Audit、整栋Final Acceptance或新的全楼Compare，不宣称原整栋12/5/3/34问题全部解决。

## 4. 改动、验证和额度

仅新增受控复验运行器、预算与容差回归测试、计划和结果文件；没有改动正向系统，也没有新增或改写任何生产Prompt。19项针对性离线检查通过，0失败、0跳过、0网络尝试；compileall通过。继承前轮准入，未运行Full Preflight。

本轮新增2次重建侧调用，新增57601 tokens；写作仍21次，重建侧累计14/14次，总占额1400238/2000000，余599762。历史连接失败的293791保守占额继续计入，不当作已确认账单。授权的两次调用已使用完，不再新增真实调用。

新的累计权威入口是本实验的 `budget/goal-budget.json`、`budget/authorization.json`；它继承完整前序1342637占额、21次写作与12次重建，原账本保持暂停未改写。后续不得只读取旧账本或新目录而重置消耗。

## 5. 文件入口

实验根：`dataset/processed/experiments/ifc2text-closed-wall-retry-20260921-v08/`。

- `public-description.txt`：未经改写的显式闭合单墙输入。
- `live-brief/`、`live-generator/generator/`：两次真实请求、响应、解析、校验和Prompt版本。
- `live-generator/single-wall-generated-diagnostic.ifc`：未经人工修改Provider输出生成的单墙IFC。
- `summary.json`：独立重开测量、实际结果、预算和边界。
- `validation/`：19项离线检查与准入，临时目录不纳入Git交付。
- `budget/`、`predecessor-budget.json`：新累计账本与完整前序证据。

下一步先在完整说明中验证异常轮廓与原宿主轴、洞口的协同，不立即改Generator；空间字段衔接和门材料仍是独立待办。整栋调用需单独安排，不能用这次单墙通过代替。

## 6. 度量参考

buildingSMART IFC2x3 TC1 IfcGeometricRepresentationContext：数值Precision与本实验源/重建容差分开。
https://standards.buildingsmart.org/IFC/RELEASE/IFC2x3/TC1/HTML/ifcrepresentationresource/lexical/ifcgeometricrepresentationcontext.htm

Shapely官方hausdorff_distance：离散对称Hausdorff及线段加密。
https://shapely.readthedocs.io/en/latest/reference/shapely.hausdorff_distance.html
