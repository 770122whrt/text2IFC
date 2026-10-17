# text2IFC RVT 与 IFC 数据入口

**当前状态：RVT 工作暂停。** 用户已收缩到 [50 份 ResBIM IFC](IFC/dataset-resbim50-20260913/ResBIM/)，保留 `extracted/01_RVT/ResBIM/` 下对应的 50 份 RVT。其他 RVT、转换输入副本、确认失败的 IFC 及未选模型压缩包已按要求删除。当前指针见 [current-dataset.json](current-dataset.json)，全 dataset 登记与删除日志见 [整理报告](../../manifests/dataset-registration-20260913/README.md)。

下面的 86/136 份获取记录、104/54 份转换集合、命令和“保持原文件”描述是清理前历史，不能再作为当前磁盘库存或恢复指令。原两份 ResBIM 25-model ZIP 仍保留为这 50 份源文件的交接备份；metadata ZIP 和历史参考包仅作记录。当前 active 集合不包含四份补充样本，后者作为成功转换储备保留。本轮保留了所有失败日志、规范化记录、哈希和原始许可/metadata，没有保留被用户要求删除的失败 IFC 字节。

## 清理前的转换与核查历史

所有原始材料、转换工具、过程记录及最终 IFC 均在本目录管理。当前主集合见 [50 份 ResBIM＋4 份补充 IFC](IFC/dataset-resbim50-20260913/README.md)，机器入口为 [current-dataset.json](current-dataset.json)。原 104 份集合保留为历史储备，不与当前集合重复计数。

本轮完成 [22 份许可复查](license-recheck-20260913/README.md) 和 [7 份 IFC 实际视觉抽检](review-visual-20260913/README.md)。全部 54 份重新解析成功，但 4 份补充模型包含局部示例、Proxy 和楼层语义问题，不能当作完整建筑训练样本。完整转换历史见 [REVIEW.md](REVIEW.md)。

## 文件职责

| 路径 | 内容 |
|---|---|
| 根目录 5 个 `Text2IFC_RVT86_*.zip` | 原交接包，4 个模型包加 1 个 metadata 包，保持原字节 |
| `extracted/01_RVT/` | 交接包的 86 份唯一 RVT，保留包内路径 |
| `metadata/` | 原交接 metadata、依赖表、历史参考 IFC ZIP，保持原内容 |
| `additional/ResBIM/` | 从作者公开链接获取的 100 模型包、CRC 日志、RVT 和上游比对结果 |
| `asset-index.json` | 原 86 份 RVT 的本地获取索引；`not_run` 是获取时快照 |
| `asset-index-expanded.json` | 去重后的 136 份 RVT 索引；转换状态由各次运行和最终集合清单记录 |
| `review-20260913/` | 来源许可证据、Git 文件身份比对、现有 IFC 清单核对 |
| `tools/` | 本地 DDC 工具及下载哈希；二进制受专有许可限制，已加入本地 `.gitignore` |
| `runs/<run>/<inventory-id>/` | RVT 输入副本、原始 IFC、规范化版本、验证结果、失败日志 |
| `IFC/<run>/` | 该次运行逐文件通过技术检查的输出 |
| `IFC/dataset-resbim50-20260913/` | 当前集合：ResBIM 50 份，加 4 份明确标注限制的补充示例 |
| `IFC/dataset-20260913/` | 历史 104 份完整转换池，保留为储备，不累计进当前集合 |
| `license-recheck-20260913/` | 剩余 22 份 RVT 的逐项来源、许可及依赖复查 |
| `review-visual-20260913/` | 7 份模型的实际网格渲染、图片、视觉结论和子集提取脚本 |

旧的 `Text2IFC_29RVT_IFC2X3_NoGrid_Full.zip` 和 `ResBIM_IFC2X3_50.zip` 已由用户因质量问题删除。本次没有恢复它们；新集合来自本次实际转换。运行目录和历史参考包中的重复文件不累计为数据量。

## 执行方法

从仓库根目录使用 `.venv/Scripts/python.exe`，IfcOpenShell 版本为 0.8.5。DDC 软件包取自提交 `45498426fd225c36a2a2a3a67993fd39c5d9d0ff`，实际 CLI 自报 Community 18.4.1。以软件包实测帮助为准。

```powershell
# 原包哈希、metadata 一致性、路径安全检查；已存在且相同的文件可复用
.venv\Scripts\python.exe -B dataset/external/RVT/pipeline.py extract

# 每个 run-name 必须是新的目录名称
.venv\Scripts\python.exe -B dataset/external/RVT/batch.py `
  --ids INV-087 INV-088 `
  --asset-index dataset/external/RVT/asset-index-expanded.json `
  --run-name my-conversion-01 `
  --converter dataset/external/RVT/tools/ddc-45498426/DDC_REVIT2IFC_CONVERTER/datadrivenlibs/RVT2IFCconverter.exe

# 对已完成、无其他未决规范化问题的输出，验证栏杆高度的两个源参数和几何证据
.venv\Scripts\python.exe -B dataset/external/RVT/height_batch.py `
  --runs my-conversion-01 --run-name my-height-01 `
  --asset-index dataset/external/RVT/asset-index-expanded.json

# 可独立检查任意候选 IFC，报告路径必须不存在
.venv\Scripts\python.exe -B dataset/external/RVT/pipeline.py validate model.ifc --report new-validation.json
```

DDC 引擎在受限沙箱中曾崩溃，在普通用户环境中可运行。Codex 执行时需要允许该明确命令在沙箱外运行；不需要管理员权限。包装程序和内部 CLI 的真实失败均已保留。崩溃重试要使用新目录，不能覆盖首次失败。

`batch.py` 不自动把失败输出算作可用模型。实际输出 `converted.ifc`、退出码、源 RVT 哈希和独立验证子进程共同决定结果。检查/转换超时也属于失败。带未确认依赖或缺少来源使用依据的输入会在转换前拦截。

## 转换及检查规则

DDC 使用 `--mode custom --config "FileVersion=ifc2x3; FileType=ifc; LevelOfDetail=high; IfcCommonPropSets=y; BimRvPropSets=y; BaseQuantities=y; MaterialPropSets=y"`。没有人为设置 10 MiB 上限，也没有关闭常用属性、Revit 属性、数量和材质。

原始导出后，`normalize.py` 仅处理明确的编码问题：补充实际转换器标识、确定的无前缀 SI 体积单位名、空的可选 Grid 轴集合、完全位于局部 XY 平面的轴线二维表达、重复 Pset GUID、完全相同且类型一致的属性成员，以及多 Type 共用的 Pset 容器。保留原始几何实体和构件 GUID；同名不同值的属性不合并。

`height_normalize.py` 单独处理错误的零栏杆高度，要求每个关联栏杆的 `Construction(Type).Railing Height` 与 `Top Rail(Type).Height` 一致，长度单位明确，局部 Z 轴竖直，几何高度也一致。证据不足、坡道/多层栏杆导致高度不一致等情况保持阻塞。`unit_normalize.py` 可补充明确声明为无前缀 SI 面积/体积单位的缺失名称，不改数值。

每份最终 IFC 均有 Schema＋EXPRESS、所有带表示对象的几何、重新打开及规范化保留检查。这里的“通过”不等于 buildingSMART 产品认证、MVD 认证、建筑设计规范合规或 RVT 内容完整性已证明。原始数据中可能存在的碰撞、设计错误、缺失构件仍需相应领域检查。

## 数据使用

`source-review-expanded.json` 给出来源级使用依据；最终 `manifest.json` 给出逐文件技术状态。不要将公开下载、来源许可支持、文件技术通过、训练切分准入合成一个布尔值。

ResBIM 是合成住宅单元设计数据。UFH 的 house/nowalls 是相关变体；Dynamo 的 host/link 是依赖关系。最终清单使用保守分组防止误当独立建筑，尚未创建 train/test split。Primer 的网站 Apache 声明已找到，但单独模型的训练/再分发范围仍需进一步确认。

原仓库的 `dataset/manifests/ifc-files.jsonl` 等正式 IFC authority 未被本次候选集合改写。本次新增的 manifest 只管理 external/RVT 内的数据。
