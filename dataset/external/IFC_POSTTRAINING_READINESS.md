# IFC2X3 建筑选材与三段式后训练评估

> 本文保留2026-09-24历史评估。当前扩充结果见[2026-09-26报告](_checks/ifc-expand-20260926-v8/REPORT.md)：可用集 196 份 IFC2X3、202 份小于 10 MB；34 份 IFC2X3 建筑专业候选，小型优先描述候选 16 份。旧Type5已改列住宅单元；母族/变体方案在新报告中单独讨论。

更新：2026-09-24。**现有文件足够启动有边界的建筑描述、局部编辑和修复后训练；暂不足以支撑广泛建筑类型的整栋生成泛化。** 这个判断针对IFC场景本身，不是因为文本和标注尚未补齐。最有价值的主线是：从真实建筑提取人类能理解的需求，通过受控调整产生任务，用可执行操作和独立验证记录形成监督。

## 1. 现在真正有哪些建筑

当前总登记379条来源、378份唯一首选内容；技术可用 **211份**，其中 **IFC2X3 186份**。本轮逐一重新核对186份IFC2X3的字节哈希、解析、构件和空间统计；22份做了实际几何外观与俯视审查。既有文件复用哈希一致的规范/完整几何证据；本轮修复文件重新完整检查。

| IFC2X3内容范围 | 文件数 | 怎么用 |
|---|---:|---|
| 整栋建筑专业候选 | 29 | 25份小于10MB；331.945MB。含完整建筑体量/主要建筑构件的候选，非建筑竣工或所有专业完整性认证 |
| BIMNet单层实测场景 | 25 | 很适合楼层布局、空间理解、局部修改；不计作25栋完整建筑 |
| ResBIM合成住宅单元 | 50 | 户型与受控操作扩增；同源生成分布，不计作50种独立建筑 |
| BIM4EEB外壳与公共区域 | 2 | 外壳和公共区域任务；来源主动省略住户内部布局 |
| 房间/走廊片段 | 2 | 局部理解和编辑 |
| 热工分区示例 | 3 | 分区和热工语义，不能直接代表现实完整建筑 |
| 专业模型/局部示例 | 74 | 结构、机电、分包构件、功能回归等任务 |
| 本轮修好的历史木结构建筑 | 1 | 结构与类型/属性关系任务，无IfcSpace，不并入完整室内建筑 |

BIMNet上游明确采用25份single-floor scans，文件下划线表示同一扫描的不同楼层：[官方结构说明](https://github.com/LydJason/BIMNet/blob/main/data_organization.md)。一个文件有多个IfcBuildingStorey节点，不代表它包含相同数量的实际完整楼层。IfcRoof为0也不直接判屋顶缺失：有些屋面用IfcSlab表示；IfcWindow为0还可能由幕墙表示玻璃。

29份中有 **23份**具有按原许可修改后发布的候选依据，6份仍待明确；按现有保守场景标签归为 **18组**。这18组不是已经证实的18栋独立建筑：同项目不同导出、专业变体、课程作业仍须按家族控制。完整逐文件范围见[186份选材登记](_checks/ifc-readiness-20260924-v7/building-readiness-register.csv)和[29份建筑候选](_checks/ifc-readiness-20260924-v7/whole-building-candidates.csv)。

### 优先做高质量人类描述的14份

这14份共 **79.874 MB**、全部小于10MB；13份带IfcSpace和可解释空间名称，Type 5没有IfcSpace。11份CC BY4、3份GPL3+，公开时遵守各自条款。每份都查看了实际建筑类几何，显示颜色仅区分IFC类别。选材标准是技术检查通过、建筑级连贯体量、主要构件齐备、具有描述价值；不等于每个房间/细节均已人工验收。

| 文件 | MB | 空间实体 | 可描述内容 | 许可 |
|---|---:|---:|---|---|
| [Duplex_A_20110907.ifc](<buildingsmart-community/Duplex Apartment/Duplex_A_20110907.ifc>) · [预览](_checks/ifc-readiness-20260924-v7/visual/buildingsmart-community-duplex_a_20110907-b347a2c8aa8f.png) | 2.381 | 21 | 双拼住宅示例：连贯建筑体量，厨房、起居室、卧室、浴室等空间名称；适合整栋层级和室内局部修改。 | CC-BY-4.0 |
| [AC90R1-Jasmin-Sun-105-2x3.ifc](<opensourcebim-testfiles/AC90R1-Jasmin-Sun-105-2x3.ifc>) · [预览](_checks/ifc-readiness-20260924-v7/visual/opensourcebim-testfiles-ac90r1-jasmin-sun-105-2x3-b7244828bfe2.png) | 3.218 | 10 | 坡屋顶住宅，空间含地下室、起居/餐厨、卧室和浴室；适合住宅整体与跨层空间描述。 | GPL-3.0-or-later |
| [AC90R1-niedriha-V2-2x3.ifc](<opensourcebim-testfiles/AC90R1-niedriha-V2-2x3.ifc>) · [预览](_checks/ifc-readiness-20260924-v7/visual/opensourcebim-testfiles-ac90r1-niedriha-v2-2x3-47eb2faed9eb.png) | 2.442 | 19 | 带附属低层体量的坡屋顶住宅，空间标签含厨房、车库及设备间；须核对重复Technik标签。 | GPL-3.0-or-later |
| [AC9R1-Haus-G-H-Ver2-2x3.ifc](<opensourcebim-testfiles/AC9R1-Haus-G-H-Ver2-2x3.ifc>) · [预览](_checks/ifc-readiness-20260924-v7/visual/opensourcebim-testfiles-ac9r1-haus-g-h-ver2-2x3-28648b3db7ed.png) | 4.559 | 26 | 坡屋顶住宅与外部楼梯，卧室、走廊、地下室、卫生间等空间语义较丰富。 | GPL-3.0-or-later |
| [model_123.ifc](<repairs/metadata-v2/gni-bim-dataset-model_123-c9b24fc7b2a4/model_123.ifc>) · [预览](_checks/ifc-readiness-20260924-v7/visual/gni-bim-dataset-model_123-c9b24fc7b2a4.png) | 7.141 | 10 | T形多层建筑，含会议室、办公室、大堂和接待空间；可做功能分区与门窗/幕墙任务。 | CC-BY-4.0 |
| [model_128.ifc](<repairs/metadata-v2/gni-bim-dataset-model_128-790b6cdf4a00/model_128.ifc>) · [预览](_checks/ifc-readiness-20260924-v7/visual/gni-bim-dataset-model_128-790b6cdf4a00.png) | 7.011 | 60 | H形多层建筑，办公室、会议室、走廊和楼梯空间丰富，适合跨层与关系描述。 | CC-BY-4.0 |
| [repaired.ifc](<_checks/ifc-assets-20260913-v4/repairs/gni-bim-dataset-model_148-fa35088eb0e7/repaired.ifc>) · [预览](_checks/ifc-readiness-20260924-v7/visual/gni-bim-dataset-model_148-fa35088eb0e7.png) | 9.985 | 47 | 多翼多层建筑，含卧室、浴室、厨房、走廊与会议室；用途按空间标签描述，不据此擅自命名酒店。 | CC-BY-4.0 |
| [model_160.ifc](<repairs/metadata-v3-round3/gni-bim-dataset-model_160-8b9964f14e60/model_160.ifc>) · [预览](_checks/ifc-readiness-20260924-v7/visual/gni-bim-dataset-model_160-8b9964f14e60.png) | 5.166 | 21 | 多翼和竖向体量组合，入口、接待、会议与办公空间；屋面未独立标为Roof，不能按Roof数量判缺屋顶。 | CC-BY-4.0 |
| [model_174.ifc](<repairs/metadata-v2/gni-bim-dataset-model_174-d7fdca7cce24/model_174.ifc>) · [预览](_checks/ifc-readiness-20260924-v7/visual/gni-bim-dataset-model_174-d7fdca7cce24.png) | 8.574 | 23 | 多翼低层建筑，卧室、浴室、走廊及机电用房标签，可做房间与构件层级任务。 | CC-BY-4.0 |
| [model_203.ifc](<repairs/grid-v6/gni-bim-dataset-model_203-da9fbdc27038/model_203.ifc>) · [预览](_checks/ifc-readiness-20260924-v7/visual/gni-bim-dataset-model_203-da9fbdc27038.png) | 5.250 | 10 | 多翼多层建筑，咖啡区、大堂、画廊、会议室和楼梯；可做混合功能和幕墙任务。 | CC-BY-4.0 |
| [model_39.ifc](<repairs/grid-v6/gni-bim-dataset-model_39-e0eab00c0cab/model_39.ifc>) · [预览](_checks/ifc-readiness-20260924-v7/visual/gni-bim-dataset-model_39-e0eab00c0cab.png) | 6.230 | 21 | T形多层建筑，办公室与卫生间空间明确，适合重复房间和位置关系描述。 | CC-BY-4.0 |
| [model_7_arc.ifc](<repairs/grid-v6/gni-bim-dataset-model_7_arc-a7e1509c0ebe/model_7_arc.ifc>) · [预览](_checks/ifc-readiness-20260924-v7/visual/gni-bim-dataset-model_7_arc-a7e1509c0ebe.png) | 9.580 | 31 | 带锯齿状屋顶的学习空间建筑，含大小学习室、安静学习区、大堂；窗主要通过幕墙表示，零IfcWindow不等于没有玻璃。 | CC-BY-4.0 |
| [model_18.ifc](<repairs/metadata-v2/gni-bim-dataset-model_18-096eb462ed00/model_18.ifc>) · [预览](_checks/ifc-readiness-20260924-v7/visual/gni-bim-dataset-model_18-096eb462ed00.png) | 1.775 | 15 | H形多层建筑，含办公室、大堂、走廊、卫生间和简餐区，适合较小上下文的整栋任务。 | CC-BY-4.0 |
| [Type 5.ifc](<european-lca-typical-buildings/20260916/Type 5.ifc>) · [预览](_checks/ifc-readiness-20260924-v7/visual/european-lca-typical-buildings-v6-Type5.png) | 6.563 | 0 | 紧凑低层住宅原型，墙/楼板/屋面/门窗齐全；没有IfcSpace，只用于体量和构件描述，不虚构房间用途。 | CC-BY-4.0 |

**先选用的顺序：** Duplex与三份住宅模型做整栋/跨层描述；Type 5做简洁体量与构件；GNI 18/123/128/39做办公空间关系，148/174做居住空间，203做混合功能，7_arc做学习空间与复杂屋顶。上述用途基于空间标签和形态，不把推断的用途当设计方正式分类。

14份按当前防泄漏规则只有 **7个保守组**：Duplex、三份住宅、Type 5、GNI同课程组、GNI team7。GNI并非视觉上一模一样，但目前缺少足以拆分课程家族的来源证据，因此先保持整组。BasicHouse、医院建筑、Lakeside等仍在29份备选表；较大体积、许可或描述范围使它们不进入这一轮小型优先表。BIM Whale的简单体量例适合辅助任务，不作为高细节住宅主力。

[优先清单CSV](_checks/ifc-readiness-20260924-v7/priority-buildings.csv) · [机读JSONL](_checks/ifc-readiness-20260924-v7/priority-buildings.jsonl) · [建筑统计](_checks/ifc-readiness-20260924-v7/building-summary.json) · [22份预览图集](_checks/ifc-readiness-20260924-v7/visual/contact-1.png)

## 2. 三段式数据能否做后训练

可以。保留你提出的三段，但把每一段的输入输出角色说清楚：

| 段 | 推荐内容 | 训练中的作用 |
|---|---|---|
| 自然语言 | 人类会说的建筑需求/修改要求；建筑用途、空间功能、相对位置、关键尺寸、材料及应保留内容；允许没有指定的设计自由度 | 模型的任务输入。先解析得到可核对事实，再写人类抽象描述，避免把GUID和STEP记录转成伪自然语言 |
| IFC文件 | 生成任务是目标IFC；编辑/修复任务是输入IFC＋目标IFC这对文件，并保留base/family/hash与差分 | 可执行环境和监督目标；原始IFC保存在文件层，模型优先输出结构化BIM/ChangeSet，由确定性程序应用 |
| 过程记录 | 公开证据下的观察、目标定位、简短操作理由、实际工具调用/ChangeSet、检查结果、返工或澄清、最终状态 | 可复现的过程监督；可以附简短推理说明，但不能把事后编造的长解释称作真实执行轨迹 |

这不是要求你先把全部文本标好才能开始。当前IFC已经可以作为首批母本。需要先定的是母本的场景分组、技术状态和内容范围，这样以后加文字、操作序列和更多变体，不必改基础数据含义。

| 目标 | 当前文件基础是否足够 | 我建议的行动 |
|---|---|---|
| 有范围的编辑/修复后训练、工具使用SFT | 足够启动 | 从优先建筑＋BIMNet楼层＋部分ResBIM覆盖墙、板、门窗、空间、属性关系任务；按授权分别使用 |
| 整栋IFC→人类摘要、建筑问答 | 足够启动小规模研究 | 14份优先＋29份备选，描述范围与可见/可解析事实一致 |
| 自然语言从零生成广泛、高保真整栋建筑 | 目前场景分布不足 | 需要补不同来源、用途、布局与建模习惯的独立家族；不能靠增加同栋变体达到 |
| GUI操作Agent | IFC可作为环境种子 | GUI能力仍要对应软件状态、截图与实际动作轨迹；现有文件不能单独证明交互覆盖 |

**没有一个通用“多少个IFC就够训练”的门槛。** 这里足够是指可构造首轮实验，不是保证训练收益。推荐先以可用的场景家族做逐组学习曲线：逐步加入新家族，保持未见家族评测不变，观察任务成功率、目标改动正确率和非目标保全是否提高。对从零生成，需要检验未见布局和类型；对编辑/修复，需要检验新母本与未见操作组合。不要仅报告训练损失下降。

作为近邻，BIM-Edit有11个真实建筑模型和36个合成场景、324项任务，明确采用输入IFC＋自然语言＋人工目标IFC，并独立核验修改。它支持“现有模型做受控编辑”这条路线，但其数量是评测设计，不是后训练充分性的阈值。[论文方法与构造说明](https://arxiv.org/html/2606.20146v1#S3)。Self-Instruct说明合成指令可以扩充监督，同时需要过滤；不能据此断言同一建筑产生大量变体就具备跨建筑泛化。[原论文](https://aclanthology.org/2023.acl-long.754/)。

自然语言抽象通常对应多个合理IFC，而非唯一STEP文件。训练/评测应检查已表达的空间、关系、尺寸与材料约束；文件哈希只用于来源追踪，不能用作生成正确性的唯一标准。项目最近IFC2Text实验已出现“文本/Audit满足，但原窗百叶/框深等细节未恢复”的情况；这说明需要明确描述保真层级，而不是继续给源模型贴完整标签。见[现有几何诊断](../../docs/validation/ifc2text/history.md)。

## 3. 一个IFC破坏/调整成新文件：可行，而且适合当前数据

建议分成两类任务一起做：

| 类型 | 构造方式 | 例子和判断 |
|---|---|---|
| 意图驱动的调整 | 从可用母本出发，执行真实可验证操作得到目标 | 移动窗及其洞口、修改墙厚并同步材料层、改房间归属；自然语言给出明确意图。修改后的设计不应默认叫“损坏” |
| 受控缺陷修复 | 先确认母本合规和目标事实，再注入单个或组合缺陷 | 删除应有关系、破坏必填属性等；修复输入应仍可解析。原始STEP截断等解析故障另作专项集 |

对编辑任务，输入为“修改前IFC＋请求”，标签为“操作轨迹＋修改后IFC”；对修复任务，输入为“损坏IFC＋修复请求”，标签为“合规目标＋修复轨迹”。同一个母本可以生成很多有效任务，但这些任务仍属于同一个场景家族。

**可识别性是关键。** 如果删除一扇独一无二的门，而输入和请求没有留下尺寸、位置或可引用的样板，就不能要求模型准确恢复私有原件。可改成明确给尺寸的重建任务，或把正确澄清/拒绝猜测作为标签。私有破坏配方、原件与目标身份映射只供训练标签制作及评估，不能泄入评测时的模型输入；同一实体被重新创建时也不强迫无从得知的原GUID。

建议先做小批独立操作，而不是马上生成海量随机坏文件。每个母本覆盖属性、几何、关系和多对象联动，加入无需修改、歧义澄清及不能从输入恢复的对照。先验证真实设计意图，再增加组合难度；错误枚举/空值修补不应占据大多数，否则训练主要学到语法清洗。

划分顺序是 **母本家族先分组，再生成所有破坏/调整、请求改写和过程记录**。同一建筑的楼层、不同专业、重导出、修复副本、合成变体必须留在同一集合。不能将原件放训练、变体放测试；还要检查跨来源Duplex等同族。首次实验可做按场景组留出或轮换评测，另留来源不同的外部集，不在本轮重写已有split。

验证同时检查：请求是否完成、目标语义和几何是否正确、宿主/洞口/空间关系是否保持、无关构件是否变化、schema/EXPRESS、完整相关几何及重开。合成过程本身也要检查，不把自动生成就当正确Gold；抽样由第二个审查者核对人类措辞和目标是否一致。训练使用实际成功或经验证的修复过程，失败作为带状态的纠错/偏好素材；无理由删掉评测失败分母。

建议每条数据最少登记 `sample_id, base_asset_id, family_id, task_kind, request, input_ifc, target_ifc, trace, mutation_recipe_private, validation, source_license, split`。这些是建议字段，本轮没有创建新的正式schema或伪造已完成训练样本。

## 4. 许可、链接与修复公开

**许可不明确的保留链接是正确方案，链接本身不补足授权。** 逐文件记录来源入口、模型/归档位置、许可证据、缺少的授权，以及能公开原件还是修复版；本轮没有取得新许可或对外发布文件。

| 当前186份可用IFC2X3的公开处理 | 数量 |
|---|---:|
| CC BY/MIT等允许按原条件修改公开 | 130 |
| GPL3+，按该许可单独发布修改版 | 5 |
| BIMNet，申请和非商业学术条款约束 | 25 |
| 模型授权未明：只列来源/模型/依据链接 | 25 |
| CC BY-ND：原件可按条款分享，改动模型内容须另确认 | 1 |

因此135份是“具备按原许可修改后发布依据的IFC2X3候选文件”，不是135栋建筑，也不是统一可以换成MIT许可的包。14份优先建筑中的3份GPL住宅和11份CC BY4应分清原许可。

[BIMNet官方申请说明](https://github.com/LydJason/BIMNet#download)要求先获得[Matterport3D](https://niessner.github.io/Matterport/)批准，再申请BIMNet；仓库已有用户确认的本地训练授权记录。当前不把它们列入无门槛公开包。可以公开官方申请入口、来源ID和不带模型私有内容的通用脚本；原件、重建参数、破坏/修复副本及相关训练产物遵循实际授权。修复不会自动消除上游限制。

25份未明文件的每项链接和缺口在[许可证据表](_checks/ifc-readiness-20260924-v7/rights/RIGHTS.md)与[机读未明链接](_checks/ifc-readiness-20260924-v7/rights/unresolved-links.jsonl)。该权益表的210份基线保持不变，本轮新增可用HTSM由[独立补充](_checks/ifc-readiness-20260924-v7/rights/supplemental.md)承接。

### 本轮实际修复登记

| 文件 | 问题与处理 | 结果 |
|---|---|
| HTSM-BIM / Test model.ifc | 48项属性集逆向基数违规；新增258个同内容Pset包装，仅改51个类型引用；全部旧实体/GUID/属性值保留 | IFC2X3，10.717290MB；原生48→0，519/519几何成功，519个表示对象网格完全相同，4项针对性测试通过 |
| BIM4EEB ITA | 9个SpecularColour=128，无唯一可证明的缩放含义 | 未猜值、未生成修复输出；仍保留源文件和问题证据 |

[修复副本](<repairs/v7/htsm-historic-timber-v6-timber-demo/Test model.ifc>) · [简单修复登记CSV](_checks/ifc-readiness-20260924-v7/repair-registration.csv) · [修复报告](_checks/ifc-readiness-20260924-v7/repairs/REPORT.md)。署名按Yakang Wang, HTSM-BIM (2021), Mendeley Data V1, DOI 10.17632/mywtvtvhwc.1，CC BY4；明确指出修复改动与日期。

此次修复增加1份结构类型可用资产，总可用210→211，IFC2X3 185→186；29份建筑专业候选和14份描述优先表数量不变。修复可以把已有场景恢复可用，但不能凭空补出未提供的房间、屋顶或更多独立建筑。下一步扩充应优先增加独立建筑家族及建筑用途，而非重复下载同源变体。

核验依据：[当前统计](_checks/ifc-readiness-20260924-v7/summary.json)、[发布检查](_checks/ifc-readiness-20260924-v7/publication-verification.json)、[建筑语义统计](_checks/ifc-readiness-20260924-v7/building-profiles.jsonl)、[新增修复语义统计](_checks/ifc-readiness-20260924-v7/additional-profiles.jsonl)。原件、既有核心139份、ResBIM50份和split保持不变；未运行真实Provider或训练。
