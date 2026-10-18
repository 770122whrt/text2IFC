# text2IFC 批量损伤数据集

母模型与损坏类型的交叉统计、原模型来源及模型级许可登记见[数据集双表](../../reports/repair-dataset-1200-summary-20261015/README.md)，含Excel与CSV下载。

当前制作和交接入口为[40母本批次报告](../../../dataset/processed/ifc-repair/formal-40-pairs-25-20261010/REPORT.md)，实际数量、缺口与交付终态由同目录的 `summary.json` 和报告说明。按用户追加要求，已有母本各再补5题，上限由25改为30；40个有效母本的目标为1,200个IFC＋请求对。目录名保留首轮日期和配额，所有新增内容继续保存在同一个根目录中。未填满时按实际通过数量交付，并逐母本说明缺额；交付完成与配额填满分别记录。本轮生成题标注机器校验、人工待审，不运行修复系统。

最新[抽样审核报告](../../../dataset/processed/ifc-repair/formal-40-pairs-25-20261010/private/reviews/spot-20261011-final/REPORT.md)汇合首轮、补充轮及追加轮的固定样本，分别记录重新执行的native检查、公开请求独立重建、最终交接文件字节、原始关系差异及删除合同复核。它是固定分层便利样本，不能据此估算总体成功率。[此前8份损伤、11条请求的审核](../../../dataset/processed/ifc-repair/formal-40-pairs-25-20261010/private/reviews/spot-20261010T152852Z/REPORT.md)和其中的失败证据保留。

[新增20母本、每母本2题的历史40题报告](../../../dataset/processed/ifc-repair/external-20-pilot-40-20261010/REPORT.md)保留来源审核、小批试制和失败历史。生成题保留冻结的请求1.3；本轮最终公开交接使用新版本1.4，在原正文前明确放置基点、坐标单位、局部轴及旋转顺序。目标、参照、坐标及属性正文保持原字节，不从私有Gold补充答案。“单一定位＋同形参照”、最多三位小数及暂不采用楼层局部定位的约定继续有效。

**制作母本总数已为40：原formal-001～020的20份完整母本＋新增20份。** 上面的“40题”是新增20母本各2份损伤样本，不是母本总数。制作前的轻量复核确认40份私有参考的源哈希、STEP schema声明及大小：40个不同SHA-256，均声明IFC2X3，193,472～14,126,095字节，无哈希变化；这一复核未重复运行40份母本的原生校验。正式生成另对每个进入制作的母本执行原生校验并保存可复用回执。新增部分映射为formal-021～040的母本编号，保留原external/reserve登记、来源及审核记录；编号不改变机器/人工审核状态，也不重命名既有Proof或母本文件。

**最新数量约定：首轮每母本25对，已有母本各追加5对，上限30对。** 用户已明确，同一份损伤IFC配墙定位、世界坐标两种适用请求，可以分别算两题。追加轮可收录已通过损伤中尚未选用的适用定位变体，也可生成新的损伤；同一损伤、同一模式不得重复计题。不同损伤IFC数与题目对数分别报告；旧批次及既有交接包的冻结计数不改写。历史新增40份损伤保存40条world和21条host_wall请求，共61个适用配对，当时公开导出只收录40条主请求配对。这些历史数不代表当前批次的题数。

## 数据集脚本说明：统一编排与实验交付

首轮按配对计数的入口是 `python -m scripts.ifc_repair.dataset_pairs`，在仓库根目录使用现有 `.venv`。它从固定40母本自动构建清单，遍历不同目标、轻中重组合、实例属性和混合损伤，复用冻结的损伤算法、请求1.3及校验器；本次追加和最终交付使用下文的独立追加轮与冻结交付入口。源IFC、已有40题、人工审核标记和旧失败证据均不改写；不运行修复系统或Provider。

历史小批生成、收录及主请求导出的入口 `dataset_operator` 继续可用，下文保留其命令。其 `--cases-per-ifc` 仍按独立损伤计数，不能拿新配对配额直接替换。

### 集中目录与首轮入口

默认批次根为 `dataset/processed/ifc-repair/formal-40-pairs-25-20261010/`。只使用这一个根目录，子目录如下；首轮目标1,000对，追加后的目标1,200对，独立损伤IFC份数另外统计。

```text
formal-40-pairs-25-20261010/
  REPORT.md                         当前可读报告
  summary.json                      数量、终态、缺口和检查范围
  public/                           仅此目录提供给实验系统
    inputs.csv                      固定六列，路径相对public
    cases/<formal-NNN-dNNN-mode>/
      model.ifc
      request.txt
  private/
    production/
      mother-sources.json           40母本别名、原登记、许可及审核证据
      build.json                    配额、种子、源码/版本和预算边界
      pairs.json                    全部通过的配对映射
      sources/<formal-NNN>/
        private/reference.ifc       不变的源字节副本
        private/progress.json       本母本当前计数
        private/checkpoint.json     游标、预算、终态和已接受配对的原子检查点
        cases/damage-NNN/           实际损伤、请求、完整封存与校验
        result.json                 本母本终态与失败历史
    supplement-r1/                  独立补充轮、冻结代码及失败历史
    extension-r2/                   每母本追加5题；新替补母本独立准入
    property-tail-r3/               仅替补母本041的剩余属性配对；独立预算和checkpoint
    delivery-runtime-v3/            追加轮实际执行的冻结代码与runtime.json
    delivery-runtime-v2/            已通过导入核对的抽样审核代码
    delivery-runtime-v4/            三轮合并的历史冻结代码；本次四轮另派生运行时
    delivery-runtime-v5/            属性尾轮/三轮核对首次启动红的冻结运行时
    delivery-runtime-v6/            严格核对种子规则后的实际尾轮和四轮交付
    finalization/                   合并题目映射、交付检查和机器数量回执
    evaluation/export.json          公开文件哈希及私有配对映射
    reviews/                        抽样、缺题诊断和上下文检查
```

原formal-001～020使用其 `private/reference.ifc`；新增20份按既有 `sources.json` 的固定选择顺序映射为formal-021～040，保留external/reserve原ID、来源族及许可证据。40份母本的SHA-256必须互异。此别名不会改变审核状态或重命名已存在的Proof。`prepare_pair_mothers.py` 提供同样的清单构建函数及独立CLI；正式生成默认在新根内自动写清单，不需要先创建根目录。

```powershell
# 默认固定40母本；每母本25对、最多30次实际损伤尝试、并发2。
.\.venv\Scripts\python.exe -B -m scripts.ifc_repair.dataset_pairs generate

# 只读脚本汇总，不扫描所有IFC。
.\.venv\Scripts\python.exe -B -m scripts.ifc_repair.dataset_pairs status

# 失败或中断后从同一目录继续；复用已封存题，失败尝试仍占原预算。
.\.venv\Scripts\python.exe -B -m scripts.ifc_repair.dataset_pairs resume

# 完成后核对公开CSV、白名单、字节与保存的导出映射；不重复native或网格。
.\.venv\Scripts\python.exe -B -m scripts.ifc_repair.dataset_pairs check
```

可用 `--sources` 指定含 `.sources` 的私有清单，`--output` 指定另一个新根，`--pairs-per-ifc 1..25` 控制每母本配对上限，`--max-attempts 1..30` 控制每母本实际落盘尝试，`--workers 1..2` 和 `--seed` 控制并发与可重复选取。目标数计配对，不把不适用的墙定位算题。两种模式均合格时按world、host_wall顺序录入；只余一题时固定取world，不复制同模式凑数。

### 独立补充轮与按实际数量交付

`dataset_supplement` 为缺额母本建立独立的 `private/supplement-r1/`，复用原来按母本保存游标、失败预算及原子接受记录的调度器。它不重置首轮30次尝试，不改首轮已接受题、结果或checkpoint。补充轮每母本另有最多30次尝试；重复运行同一命令从本轮checkpoint继续，预算仍累计，代码、输入或配置变化则拒绝续跑。根目录的 `PAUSE` 仍用于协作停止。

补充版本显式使用 `dataset_geometry_guard_v2`，仅将无独立STEP实体编号的内联值排除出几何所有权/保护ID集合，继续保留共享几何、layer/style及独占几何清理合同。冻结的旧guard、原算法文件和请求1.3均不重写。只重试此修复针对的旧内联值异常；已知且规则未变的补墙/请求失败跳过，失败证据保留。候选目录再补同一实例的2～4项已有属性的非连续组合，沿用原错值并按真实recipe和损伤字节去重，不添加源模型不存在的属性。

```powershell
# 独立补充，或继续同一补充轮；不会重置首轮或本轮已用预算。
.\.venv\Scripts\python.exe -X utf8 -B -m scripts.ifc_repair.dataset_supplement run `
  --batch dataset/processed/ifc-repair/formal-40-pairs-25-20261010 --workers 2 --max-attempts 30

.\.venv\Scripts\python.exe -X utf8 -B -m scripts.ifc_repair.dataset_supplement status
```

补充题的请求、原生schema＋EXPRESS、精确保全、补墙、保留网格及封存检查与首轮相同；每题另外封存补充版本与首轮输入绑定。首轮报告快照在 `private/history/first-pass-20261011/`，两个回合的失败均计入最终报告。此补充轮仍以同一母本25对为上限。后续追加配额由独立的 `extension-r2` 编排，不能通过改写此补充轮的冻结配置来提高。定位不唯一、无可用既存属性或缺少合格形状参照的母本可以保留零题，这不等于源IFC原生校验失败。

### 每母本再补5题：独立追加轮

`dataset_extension` 在同根的 `private/extension-r2/` 保存新编排。已有母本从25对追加到最多30对：先核对已通过题包里尚未选用的适用定位模式，再按剩余配额生成不同损伤。例如补录1条既有墙定位后，只需再生成4个配对；报告分别计算补录变体、新损伤配对及新损伤IFC份数，不把补录算成新损伤。此前同一损伤、同一定位、已接受配方和原规则下确定失败的配方都不能重复凑数。

每母本本轮另有最多30次落盘尝试，复用原调度器的互斥锁、原子checkpoint、游标、失败日志和 `PAUSE`。旧两轮的预算与记录保持原样，本轮中断后重跑同一冻结命令即可继续；配置、程序、母本缓存或已通过题包发生变化时拒绝恢复。普通旧母本复用哈希绑定的原生准入和库存，不重复执行40份母本的native；新增替补母本必须重新执行schema＋EXPRESS及库存提取。每份新损伤仍从完整母本独立生成，并执行原请求、原生、保全及适用补墙/网格检查。

formal-028的84根柱并非几何重叠：它们的 `ObjectPlacement` 原点相同，实际位置存于各自Body内部偏移。当前公开定位合同仅用构件放置原点，因此不能唯一指向这些柱。原IFC已通过native，但在此合同下没有可收录题。获准替换后另用formal-041编号，不改写formal-028及其零题历史。来源目录保留41份历史记录，有效集合仍为40份；替补文件需核对许可、源SHA、既有建筑族及构件几何重合，已知无法证明补墙的目标单独排除。

追加轮从 `private/delivery-runtime-v3/` 的实际冻结程序执行，启动前核对原87个生成程序、追加后的90个程序及实际加载模块的文件路径和SHA，并检查Windows子进程启动。第三方运行库可来自仓库 `.venv`；项目程序不得回落到主工作区。实际代码根与来源数据根分别记录，不因其他任务改了主工作区源码而重写原生成证据。

属性尾轮与四轮交付从 `private/delivery-runtime-v6/` 执行：v5保留首次启动配置红，新加 `dataset_deliver_v4` 统一入口。首轮随机种子按 `build.seed + mother-sources.json清单索引` 分派，补充轮继承同一母本首轮种子；旧核对器误用统一种子，新包装按冻结调度语法独立计算预期值，再交原校验器完整比对配置。旧检查点、代码及失败记录不改写。尾轮 authoring 集合为92个文件，完整运行时为126个项目程序；两者分别核对。启动前实际加载检查64个项目模块均来自冻结运行时，回落主工作区为零。执行函数入口与新增dispatch入口分别绑定。最终机器交付协议为 `text2ifc/dataset-offline-delivery/1.3`；旧1.1/1.2保持原版本。

替补母本041在追加轮的30次尝试中通过28题：10份纯属性、2份删门和2份删门＋属性修改损伤，均有两种适用定位；另16次补墙检查未确认，不收录。39个旧有效母本均已从25达到30题。041的属性候选仍有余量，缺口来自配方排序和该轮尝试预算，不能解释为IFC不合规或容量耗尽。`dataset_property_tail` 因此仅按041剩余2题开独立属性尾轮，跳过此前已试和已接受配方，复用哈希绑定的041准入缓存；原预算、失败和28题终态保留。尾轮仍执行同样的原生、请求、保全、适用补墙及网格检查，并独立记录游标和失败点。

最终交付合并四个回合的实际通过题。它核对母本源哈希、相同IfcOpenShell版本的schema＋EXPRESS缓存、各回合冻结程序、checkpoint终态、每题封存、真实配方和损伤字节去重及每有效母本30对上限，再将新增成功题原样复制到制作目录的独立子目录。原结果、checkpoint、题包和失败现场不覆盖；合并后的映射只写 `private/finalization/`。已有完整交付可只读复查；不完整交付保留失败回执，拒绝覆盖重试。最终入口命令以下文实际冻结交付版本为准，不能用旧两轮或三轮控制器处理本次四轮结果。

最终公开导出由 `dataset_pair_export_v2` 复用原1.3题包的全部检查门槛，再验证1.4固定前缀、原正文与最终请求的逐字节绑定。IFC原样复制；请求为UTF-8、原body行尾保留，不能把新请求误称为1.3原文件的字节副本。CSV仍是六列，public仍只含CSV和各题IFC/TXT。交付复查重验哈希、封存和既有回执，不重新执行全部native/网格，也不启动修复实验。

如果主工作区另有并发代码变更，以各回合冻结快照及已验证运行时建立新执行目录。它保持原生成程序SHA，再加入单独版本的编排辅助程序；实际执行模块必须从其目录加载，`--repository` 仅指出来源数据所在仓库。代码根与数据根分别核对，主工作区漂移另存，不声称主工作区已匹配旧快照。最初的 `delivery-runtime` 未通过全部依赖隔离检查，其失败记录保留；不能使用这个旧目录绕过实际加载检查，也不要通过重登记当前SHA、恢复无关文件或关闭校验来交付。

```powershell
$datasetBatch = 'dataset/processed/ifc-repair/formal-40-pairs-25-20261010'
$extensionSpec = "$datasetBatch/private/reviews/replacement-intake-20261011/formal-041-source-spec.json"

# 从已核验的祖先运行时派生新的追加轮运行时；已有目录只核对，不覆盖。
.\.venv\Scripts\python.exe -X utf8 -B -m scripts.ifc_repair.dataset_deliver_runtime_v2 prepare `
  --batch $datasetBatch --repository 'E:/code for project/bimnet' `
  --base-runtime "$datasetBatch/private/delivery-runtime-v2" `
  --runtime "$datasetBatch/private/delivery-runtime-v3" `
  --extra-module scripts.ifc_repair.dataset_extension

# 只读Windows子进程检查；不解析IFC或调用native。
.\.venv\Scripts\python.exe -X utf8 -B "$datasetBatch/private/delivery-runtime-v3/bootstrap.py" `
  --module scripts.ifc_repair.dataset_extension probe --batch $datasetBatch

# 正式追加或同版本继续；新题独立校验，原题和失败预算保留。
.\.venv\Scripts\python.exe -X utf8 -B "$datasetBatch/private/delivery-runtime-v3/bootstrap.py" `
  --module scripts.ifc_repair.dataset_extension run `
  --batch $datasetBatch --repository 'E:/code for project/bimnet' `
  --replacement-source $extensionSpec --workers 2 --max-attempts 30

# 只读本轮summary。
.\.venv\Scripts\python.exe -X utf8 -B "$datasetBatch/private/delivery-runtime-v3/bootstrap.py" `
  --module scripts.ifc_repair.dataset_extension status --batch $datasetBatch

# 派生三轮控制器祖先；本次最终交付使用下方新四轮控制器。
.\.venv\Scripts\python.exe -X utf8 -B -m scripts.ifc_repair.dataset_deliver_runtime_v2 prepare `
  --batch $datasetBatch --repository 'E:/code for project/bimnet' `
  --base-runtime "$datasetBatch/private/delivery-runtime-v3" `
  --runtime "$datasetBatch/private/delivery-runtime-v4" `
  --extra-module scripts.ifc_repair.dataset_deliver_v2

# 从v4派生属性尾轮及四轮交付；原目录不覆盖。
.\.venv\Scripts\python.exe -X utf8 -B -m scripts.ifc_repair.dataset_deliver_runtime_v2 prepare `
  --batch $datasetBatch --repository 'E:/code for project/bimnet' `
  --base-runtime "$datasetBatch/private/delivery-runtime-v4" `
  --runtime "$datasetBatch/private/delivery-runtime-v5" `
  --extra-module scripts.ifc_repair.dataset_property_tail `
  --extra-module scripts.ifc_repair.dataset_deliver_v3

# 派生严格种子核对入口；v5的启动红与程序保留。
.\.venv\Scripts\python.exe -X utf8 -B -m scripts.ifc_repair.dataset_deliver_runtime_v2 prepare `
  --batch $datasetBatch --repository 'E:/code for project/bimnet' `
  --base-runtime "$datasetBatch/private/delivery-runtime-v5" `
  --runtime "$datasetBatch/private/delivery-runtime-v6" `
  --extra-module scripts.ifc_repair.dataset_deliver_v4

# 首次入口先做真实三轮只读准入，复用缓存，不运行native或解析IFC。
.\.venv\Scripts\python.exe -X utf8 -B "$datasetBatch/private/delivery-runtime-v6/bootstrap.py" `
  --module scripts.ifc_repair.dataset_deliver_v4 preflight `
  --batch $datasetBatch --repository 'E:/code for project/bimnet' `
  --code-root "$datasetBatch/private/delivery-runtime-v6"

# 仅处理041实际缺口，或按相同配置从尾轮checkpoint继续。
.\.venv\Scripts\python.exe -X utf8 -B "$datasetBatch/private/delivery-runtime-v6/bootstrap.py" `
  --module scripts.ifc_repair.dataset_deliver_v4 run-tail `
  --batch $datasetBatch --repository 'E:/code for project/bimnet' `
  --code-root "$datasetBatch/private/delivery-runtime-v6" --max-attempts 30

# 合并四轮、保留028历史与041替补，导出六列CSV和公开IFC/TXT。
.\.venv\Scripts\python.exe -X utf8 -B "$datasetBatch/private/delivery-runtime-v6/bootstrap.py" `
  --module scripts.ifc_repair.dataset_deliver_v4 deliver `
  --batch $datasetBatch --repository 'E:/code for project/bimnet' `
  --code-root "$datasetBatch/private/delivery-runtime-v6"

# 完成交付后只读复查权威、封存及公开文件；不重复native/网格。
.\.venv\Scripts\python.exe -X utf8 -B "$datasetBatch/private/delivery-runtime-v6/bootstrap.py" `
  --module scripts.ifc_repair.dataset_deliver_v4 check `
  --batch $datasetBatch --repository 'E:/code for project/bimnet' `
  --code-root "$datasetBatch/private/delivery-runtime-v6"
```

交付脚本只追加机器权威回执，不改根报告。当前可读报告与 `summary.json` 在所有最终交接/抽样检查完成后引用这些回执；首轮快照继续保留。目标未填满但实际交接通过时，交付终态为complete、`quota_complete=false`，并逐母本报告缺题原因。

`dataset_reports` 只读不可变交付summary、抽样及旧文件保全回执，先交叉核对总数、逐母本30题上限和各回合计数，再更新唯一的根报告与summary投影。它不解析IFC、不重跑native或网格，不改变原交付权威；缺少通过的抽样/保全回执时拒绝写入完成报告。

```powershell
.\.venv\Scripts\python.exe -X utf8 -B -m scripts.ifc_repair.dataset_reports `
  --batch $datasetBatch `
  --sample-review "$datasetBatch/private/reviews/spot-20261011-final/summary.json" `
  --preservation-review "$datasetBatch/private/reviews/extension-preservation-20261011/after.json"
```

候选元数据预筛不扣落盘预算；进入损伤函数前先持久化attempt，异常也占用一次。每母本独立达到配额才算完成，不能用其他母本多产题补缺口。报告区分候选穷尽、30次预算耗尽、工作进程异常及主动暂停，保留失败配方、日志和未完成暂存目录。generate只接受新根；resume使用已有根，在母本、种子、配额、核心/控制器及直接执行依赖版本一致时继续。原生校验与库存有哈希绑定的缓存，可复用；已通过case核对原封存SHA后保持字节。started记录说明中断前已预留一次预算，恢复将其记为失败并跳过该候选，不靠落盘文件存在补认成功。游标也在每次候选拒绝后保存，避免重复消耗预筛工作。整批和每母本均持有操作系统互斥锁，进程退出会释放；同一批次不能并发运行generate/resume。

根目录的 `PAUSE` 文件供协作暂停：完成当前损伤后停止新尝试和新母本派发。resume会先把暂停标记保存在private/history中再继续。源码/配置漂移、参考或已通过题封存变化时拒绝续跑，保留记录供排查；不会覆盖成功题或静默重置30次预算。已有公开导出完好时直接复用；失败或不完整的公开副本留到同根private/history后重新导出，制作题包不重做。

新入口没有放宽请求1.3的参照存活、基本形状证书、坐标唯一性或墙体补全规则。冻结库存对匿名同形参照的保守限制仍保留；保守排除及容量不足是脚本筛选范围的证据，不能直接说母本不合格。通过题逐份执行schema＋EXPRESS、实际公开请求信息核对、适用补墙和最多三个保留网格检查，然后追加回执并封存。导出先核对完整封存及原生/请求/补墙/保全回执，再复制通过输入字节并重新核对所有绑定。check只检查公开交接和保存映射，不重新验证上游封存、native或网格。同一损伤的定位变体按同一damage分组，母本/建筑族仍须在开发与评估间隔离。

`.gitignore` 已覆盖 `/dataset/processed/ifc-repair/*`，本批IFC、请求及私有产物不会被自动加入Git；新脚本和测试保持Git可见。产物仍是机器校验、人工待审，1,200对的目标数不代表实际通过数量，更不代表系统修复成功率。

流程为：**来源清单 → 有限生成 → 机器检查 → 按需收录 → 公开导出 → 实验侧prepare**。已有完整集合可直接从公开导出开始。前五步由数据集脚本负责，最后一步按[实验侧接口要求](../repair-comparison/README.md#给数据集侧的接口要求)执行。

|命令|职责与底层复用|运行后得到什么|
|---|---|---|
|`generate`|调用 `generate_damage_pilot.py`，批量损伤、自动写请求并执行原有检查|完整制作题包、`summary.json`、`cases.csv`、`REPORT.md`及私有证据|
|`collect`|调用 `collect_damage_pilot.py`，从多个生成批次挑选完整通过的母本|合并制作题包，原IFC、请求及回执按字节复制；失败历史留在原批次|
|`check`|复用 `inspect_source` 与实验侧 `load_candidates`|核对完整状态、索引、源/参考/题目哈希、封存和现有校验回执；不重复运行原生或网格检查|
|`export`|先执行上述检查，再白名单复制，通过实验侧 `load_pair_candidates`回读|只含公开输入的目录，另有独立的评估侧导出回执|
|`status`|只读取已有 `summary.json`|一条现有数量与报告入口摘要，不生成或复验题目|

正常操作最终只向终端输出一行JSON，`event="summary"`；失败退出码为2并给出原因。生成和收录的底层详细输出保存到结果的 `private/operator.log`，启动失败时日志留在 `.tmp/dataset-operator-logs/`。脚本负责进程等待与汇总，Codex只读摘要、异常及必要抽样。

子程序失败但已写出 `summary.json` 时，终端失败摘要同时给出 `dataset_status`、目标/通过/缺口、尝试/失败数、`worker_error_count`、原退出码及报告/日志路径，仍返回2；没有有效汇总时不猜数量。母本工作进程异常与配方失败分别记录，不能只用 `failed_attempts` 计算全部失败。

### 控制每个IFC的数量

`--cases-per-ifc` 在现有代码中仍是每母本不同损伤IFC的目标通过数，统一入口默认2，范围1～8；不同配方不足时报告数量不足，不复制同题凑数。`--workers` 只用于生成，范围1～2，默认2；`--seed` 默认20261010；`--request-profile` 默认1.3，1.2仅用于显式复现历史规则。每份损伤仍从完整母本独立生成；旧CLI只按主请求计case，附加定位变体未进入题数。最新需求的配对编排已由上文 dataset_pairs 实现，不能把20～25对直接代入旧数量参数。旧全量 `dataset_batch build` 保留为历史入口，不是本轮推荐编排。

```powershell
# 一个母本；输入路径示意，需替换为实际IFC。
.\.venv\Scripts\python.exe -B -m scripts.ifc_repair.dataset_operator generate `
  --input path/to/intact.ifc --cases-per-ifc 2 --workers 1 `
  --output .tmp/my-damage-pilot

# 多个母本；来源清单含 input_path/source_id/source_sha256，可保留许可及建筑族记录。
.\.venv\Scripts\python.exe -B -m scripts.ifc_repair.dataset_operator generate `
  --sources path/to/source-selection.json --cases-per-ifc 2 --workers 2 `
  --output .tmp/my-multi-source-pilot

.\.venv\Scripts\python.exe -B -m scripts.ifc_repair.dataset_operator check `
  --dataset .tmp/my-multi-source-pilot
.\.venv\Scripts\python.exe -B -m scripts.ifc_repair.dataset_operator status `
  --dataset .tmp/my-multi-source-pilot
```

`generate`、`collect`、`export` 的输出必须是新目录；失败现场保留，重试使用新目录。统一入口不恢复已经停止的全量批次，也不重写已有报告。后面保留的独立脚本命令仍可用于诊断和历史复现。

若需要把多个生成批次中的完整母本汇成一个集合，显式给出批次和母本ID；不同请求版本不能混收。数量参数须与所选母本已通过的题数一致：

```powershell
.\.venv\Scripts\python.exe -B -m scripts.ifc_repair.dataset_operator collect `
  --origin .tmp/round-one --origin .tmp/round-two `
  --source-id external-001 --source-id external-002 `
  --cases-per-ifc 2 --output .tmp/my-collected-dataset
```

### 制作题包与被测输入分开

制作集合包含来源、损伤记录和参考IFC，供制作者及评分器使用；不能把整个集合目录当作被测系统的挂载目录。`export` 固定复制每题的 `public/model.ifc` 和已有主请求 `public/request.txt`，不改写文本、不附加解题方法，也不复制其他模板变体。

```text
my-public-inputs/                  被测系统仅接收这一目录
  inputs.csv                      UTF-8，六个接口字段
  cases/<source-qualified-case>/
    model.ifc                     损伤IFC的原样副本
    request.txt                   已审核主请求的原样副本

my-export-evaluation/              评估侧保管，不交给被测系统
  export.json                     公开文件哈希、题包映射、回执范围
```

三个目录——原制作集合、公开导出、评估侧回执——必须互不包含。公开目录只允许CSV及指定IFC/TXT，不含 `case.json`、来源说明、原件、Gold、配方、损伤映射、删去对象名单或答复卡；这些仍留在制作/评估侧。目录中采用实际复制文件，拒绝符号链接、junction/reparse及硬链接。导出会复核上游私有证据，但运行时从公开目录无法取得这些材料。

CSV六列为 `case_id,ifc_path,request_path,level,primary_target_count,task_kind`。ID增加来源前缀，大小写不敏感唯一、最多101字符，并避开Windows保留名；路径使用目录内 `/` 相对路径。大小、格式和许可条件沿用上游集合；这一步是本地实验输入导出，未建立公开发布或训练准入。

CSV不承载建筑族或盲测分组。评估侧回执保留母本和原题包映射，来源、同族及已揭示状态仍以原集合记录为准；导出不自动把开发审核题变成未见测试题。

预算及题型复用实验侧规则：主要删除构件数＋独立属性目标数得到 `primary_target_count`；同一构件的多项属性修改只算一个目标，附属洞口和关系不计。1个→S1/1.5M token，2个→S2/2M，≥3个→S3/2.5M。`task_kind` 中 `geometry` 表示构件缺失，`property` 表示只有属性修改，`mixed` 表示同时缺失与改属性；门窗梁柱四类同时缺失仍是 `geometry`。配方的轻/中/重损伤等级不直接作为预算档位。多项属性写入须有明确的独立目标数，不能按写入次数猜测。

导出当前40题，无须重新损伤：

```powershell
.\.venv\Scripts\python.exe -B -m scripts.ifc_repair.dataset_operator export `
  --dataset dataset/processed/ifc-repair/external-20-pilot-40-20261010 `
  --output .tmp/external40-public-inputs-20261010 `
  --evaluation-output .tmp/external40-export-evaluation-20261010

# 对照评估侧回执复查公开导出的哈希、文件白名单和CSV。
.\.venv\Scripts\python.exe -B -m scripts.ifc_repair.dataset_operator check `
  --dataset .tmp/external40-public-inputs-20261010 `
  --evaluation-output .tmp/external40-export-evaluation-20261010
```

机器校验状态仍在原题包与评估侧回执，不把公开CSV的声明当作人工审核或真实调用准入。CSV配对回读不解析IFC、不证明请求语义无泄漏，也不重复执行schema＋EXPRESS；生成时的原生、保全和prompt/wall/mesh回执须完整有效。实验侧 `prepare --input-format pairs` 仍会按自身合同核验格式并冻结输入，真实运行需另完成适用离线准入。

下面只展示交接命令，本轮不执行实验准备或模型调用：

```powershell
.\.venv\Scripts\python.exe -B -m scripts.ifc_repair.repair_comparison.batch_operator prepare `
  --root .tmp/my-repair-batch --dataset .tmp/external40-public-inputs-20261010 `
  --input-format pairs --scope full --concurrency 2
```

编排与交付边界的聚焦测试在 `tests/ifc_repair/dataset_batch/test_operator.py`；原生成、收录及实验配对接口的既有测试继续适用。具体本轮验收回执和实际导出入口见本节末尾的完成记录。

### 本次完成记录（2026-10-10）

统一入口已从现有完整集合导出[公开inputs.csv](../../../.tmp/external40-public-inputs-20261010/inputs.csv)，实验侧配对解析及独立CLI回读通过：40对，公开目录仅81个文件；S1/S2/S3为22/17/1，geometry/mixed/property为31/8/1。公开输入字节与原题包一致，详细来源映射及检查范围只在[评估侧导出回执](../../../.tmp/external40-export-evaluation-20261010/export.json)。没有执行实验侧prepare或真实模型调用。

[聚焦验收汇总](../../../.tmp/external40-export-evaluation-20261010/verification.json)合并原检查与限定复查，共79项通过、1项环境跳过；保留全部红记录。Windows实机symlink测试因缺少权限跳过，硬链接创建也被本机限制；硬链接计数与文件/祖先reparse拒绝另用模拟元数据检查，不能据此宣称实机链接创建已验证。两份真实合成IFC题包验证了生成检查→公开导出的路径，其余边界夹具为明确标注的模拟输入。复核阶段没有重复已充分通过的原生检查，也没有用测试数代表系统修复能力。

### 再次交叉审核：扩量与交接范围（2026-10-10）

**现有40题可以按上述实验接口交接；40份母本已经齐备。以下记录诊断的是升级前试点编排，最新配对入口见上文。** 本次重新检查制作集合封存/索引及公开包：40对、81文件、120,786,258字节损伤IFC，原公开输入和私有回执哈希有效。复用既有独立40/40请求审核、8题schema＋EXPRESS重验零findings及3题墙几何检查，没有重复原生/网格，也没有启动新损伤或修复系统。

扩量限制已由独立代码审核和只读元数据探针确认：

- 当前20个新母本各有2条显式 `pilot_cases`；提高cap只截取原计划，不会补新配方。当前统一入口的目标数范围仍为1～8。
- 自动选择对同一损伤族反复使用排序后的前6候选。30个不同窗配方、请求8题的负例，候选并集只有6；后续候选不会被尝试。含超过12个删除对象的族还可能在选择时直接被拒绝。
- 按现有库存和原种子试算、假设移除显式计划后，只有15/20母本在当前自动选择及完整形状准备下有机会凑足4题，13/20有机会凑足8题。这是不同操作的乐观容量，未执行新题写出、原生、公开请求、补墙或保全检查，不能当成已通过题数，也不代表改换种子/目标后仍只有这些容量。
- 旧 `dataset_batch build --cases 25` 使用默认请求1.1，缺少当前逐例1.3信息、补墙和保留网格检查；不能用这个历史入口绕过现有准入。当前pilot的30是候选池数量，每个槽最多6次候选尝试，尚不是每母本统一的30次尝试总上限。

这些历史结果诊断的是升级前试点选择器；15/20并不说明另外5份IFC不合格，也不证明其全部可用目标不足。不需要重新寻找40份母本，或把80/160题小批次作为强制前置阶段。正式批量应对已有40份完整母本自动盘点，跳过缺少合格同形存活参照且不能用基本形状充分描述的目标，继续选择其他支持的门、窗、梁、柱或实例属性。删洞口后无法确认补墙的目标同样跳过；每份候选仍需损伤记录、公开请求、写出后的原生校验及适用补墙/保全检查。数量与支持目标检查应由批量脚本执行，不需要逐母本人工补一轮准入报告。

目前需要修改的是正式数量参数、扩展计划、候选遍历/去重及尝试上限，并将数量调度切换为用户新确认的IFC＋请求对。800～1000题对应40母本各20～25对，不要求800～1000种不同损伤；实际交付数以不同的合格损伤/定位配对为准。未达目标必须报告缺口、替选目标或替补允许更换的新增母本，不能用同一定位的重复文本凑数。下面80/160只是可选规模示例，不是强制阶段；此前用户暂停的40×25批次不会因本次口径核对而自动恢复。

|规模|题数|当前状态|
|---|---:|---|
|新增20母本×2|40|已完成，已有本节的规范交接包|
|既有5母本×4|20|独立历史试点，未混入新增40题CSV|
|新增20母本×4对|80|可选规模；需先扩配方规划及配对计数并逐题验收|
|全部40母本×4对|160|可选规模；生成时检查各母本的支持目标|
|全部40母本×20／25对|800／1000|最新配对入口支持此目标；实际通过数以新批次summary为准|

每道题是一份损伤IFC＋一份具体定位请求。同一损伤在两种定位均合格时形成两对；只有world适用时只形成一对，不虚构墙定位。新编排需记录损伤ID及定位模式，分别报告不同损伤数、配对数及两种模式分布；去重分两层：不同损伤配方/结果不重复，同一损伤/同一定位不重复，两个定位之间允许复用IFC字节。同一损伤及同母本变体的关联保留在评估侧，不能拆到不同训练/测试分组。

采用当前每对独立复制IFC/TXT的交付布局，公开包有 `Q` 对时为 `2Q+1` 个文件；80对为161文件，160对为321文件，1000对为2001文件。其中IFC文件可能按配对需要重复字节，报告不得将这些副本称为不同损伤。全部派生题仍标机器校验、人工待审；母本的人审不继承给派生题。来源、同族映射、许可及失败历史留在制作/评估侧。原40份不同损伤的历史仍为56次尝试、11次失败、45次通过、5个通过输出未收录，不能把筛选后的40/40解释为未筛选生成率。

本轮仅修正了统一入口的失败数量摘要：先保留[2项红复现](../../../.tmp/pytest/dataset-readiness-red-20261010.xml)，再执行[4项聚焦检查](../../../.tmp/pytest/dataset-readiness-green-20261010.xml)全部通过（2个新增失败分支及原生成/状态控制），独立只读复核未发现新的阻塞缺陷。损伤核心指纹、模板版本和已有IFC/请求没有改动。

完整只读容量与交接结论见[本轮机器记录](../../../.tmp/dataset-readiness-cross-review-20261010/final.json)。1105个历史快照文件中，1104个关键文件哈希不变，唯一变化为后来更新交叉审核导航的人读 `REPORT.md`；本轮记录保留该字节差异及首次严格快照结果，没有宣称整份历史快照完全不变。公开/私有绑定184项和独立坐标输入141项全部有效。代码审核及候选容量结果只支持本地制作与交接，尚未建立公开发布、盲测、系统修复成绩或大量生成吞吐量结论。

## 历史试点入口

先前5个IFC、每母本4题的[20题结果与升级历史](../../../dataset/processed/ifc-repair/pilot-20-v2-checked-20261010/REPORT.md)保留：19份损伤IFC字节不变；formal-007/case-003-a01换掉无合格参照的复杂门，原窗目标保留，旧版本归档在其 `private/history`。40 × 25全量生成仍停止，原产物及 `STOPPED-BY-USER.json` 保留；[首批校验报告](../../../dataset/processed/ifc-repair/first-batch-validation-v1/REPORT.md)仍是历史入口。

门窗优先采用完整同形参照，没有可用参照时只描述经完整网格核验的基本长方体，复杂目标另选。多边形是否保留的依据见[当前 Harness 几何边界核验](../../../dataset/processed/ifc-repair/harness-geometry-scope-20261010-r03/REPORT.md)：公开类型映射及安装参照能够支持完整形状复用；合规输出和 Harness 成功状态不能代替同形检查。两个无类型映射的负例仍排除。这些数据的信息检查不是 Harness 或真实 Provider 解答成功率；本轮没有运行系统修复或调用 Provider。

## 来源约束与暂停的全量规划

保留 formal-001～020 的母 IFC 原字节，另选约 20 个可修改、来源及许可有证据的 IFC2X3，实际文件严格小于 20,000,000 字节。来源从仓库现有开放语料登记表筛选，先复核原文件、SHA-256、许可证据、最新资产权利记录，再逐个执行当前版本的原生校验和可生成数量检查。候选不合格时替补新增来源；formal 母本不自动替换。

历史全量计划为每母本25个互相独立的损伤副本，该暂停记录按原义保留；随后首轮按每母本25个IFC＋请求对执行，本次再追加5对、上限30对，采用上文独立追加轮。每份新损伤从完整母本重新生成，不连续叠加上一次损伤。每母本每轮最多尝试30个不同配方，原轮预算不重置。副本SHA-256去重。同一建筑的不同导出版本、参数场景和教学变体仍保留共同建筑族标识；40个不同文件不代表40个独立建筑，也尚未划分训练集和测试集。

来源许可、署名、源 URL、证据文件哈希、建筑族及已有审核记录保存到 `sources.json` 和每母本的 `private/source.json`。原有 `accepted_by_delegation` 与 `human_viewed=false` 按实保留；用户认可母本和派生样本人审是两个事实。许可筛选支持本轮本地研究和修改，不建立训练准入或正式 Proof 验收。

## 损伤与 prompt

操作包括门、窗、门窗、梁、柱、梁柱、门窗梁柱七种删除族，以及实例属性更改。可同时删除和改属性；模型不存在的类别不强行补造。轻度每类删除 1 个，中度每类最多 3 个，重度按可用数量约 30% 取样，每例合计最多删除 30 个主构件。数量允许时纳入“全删可挖窗＋更改保留门属性”。随机种子固定，实际选取及前后值逐项记录。

属性更改保持原 IFC 值类型，只改变已有 `IfcPropertySingleValue` 实例属性。版本 1.3 的修改候选和配方检查均限定门、窗、梁、柱；不修改墙属性。墙仍会被读取，用于宿主定位、补洞与保全检查。共享 Pset、共享属性以及 Type 同时持有的 Pset 会先隔离当前实例，再改值。不会把继承的 Type 属性批量改成全类型损伤。

当前实验版本 `text2ifc/dataset-request/1.3` 自动生成以下两种请求投影，1.1 和 1.2 的实现及既有冻结源码不改写：

|模板|定位方式|适用条件|
|---|---|---|
|`host_wall`|楼层、Wall 的 Name、大体方位；基点距墙长度起端、厚度负向侧和墙底的相对距离；参照按楼层＋Name 找到|全部目标均有命名墙宿主，名称及形状参照可唯一定位|
|`world`|墙未扣洞口的整体范围、目标及参照世界基点；同朝向直接沿用参照|目标与公开坐标参照可计算且能唯一定位|

墙名模板不带世界坐标或楼层坐标点；世界模板不用墙名、构件名、类型名或参照名称定位，楼层名称允许出现。检查涵盖整份实际请求，包括形状参照和洞口；不能在后文重新混入其他定位方式。世界坐标指模型放置坐标，不是地理经纬度。版本 1.1 的三种投影、对应源码快照与旧字节记录属于历史，不改写为新版本结果。

版本 1.3 优先引用损伤后仍存在、按当前定位方式能唯一找到且完整局部网格相同的构件，不再公开逐实体的截面和拉伸配方。门窗参照还必须有公开安装见证或独立基本形状证书。没有可用参照时，只有经单一矩形拉伸及完整长方体网格证书确认的基础目标可按尺寸、基点偏移和朝向描述；不会把复杂形状外包盒当作答案。完整几何继续保存在私有记录和参考 IFC 中。参照自身或其所填洞口也被删除的配方会被拒绝。

墙模板不适用于普通梁柱或没有宿主墙的属性对象，此时记录 `applicable=false`，不生成虚构墙定位。版本 1.3 的通过题必须有世界坐标请求，生成了墙名变体时也须通过其信息检查。每题挑选一份主请求写入 `public/request.txt`；定位变体不能算作独立损伤样本。公开数值最多三位小数，原 IFC 名称和属性字符串按原文保留。世界坐标按每轴约 0.5 毫米舍入检查；相对毫米值按约 0.0005 毫米舍入检查；旋转角误差独立传播，不修改旧版检查器的精度。

删除门窗时记录是否保留原洞口；不保留时连同 void/fill 关系清理。版本 1.3 在参照洞口的完整形状、相对门窗的位置及朝向均相同的情况下，直接要求复制参照所填洞口及相对安装关系；保留洞口则定位实际空洞并建立新 fill 关系。不能默认复制门窗外包盒。

删除构件时先记录引用它的关系。删除后，必须引用该构件的关系、以及成员数量低于 schema 下限的关系一并清理；共享关系仍保留其他成员，类型、材料、覆层和空间对象不跟随关系整批删除。几何清理先固定其他对象仍在使用的节点及完整后代图，保护共享面、环、点、样式和放置基准，只移除目标独占的几何。该保护同时拒绝独占几何残留，避免把已删构件的完整形状留作孤立答案。

补墙有明确支持边界：墙的完整 Body 通过 `IfcRelVoidsElement` 扣洞时，删除洞口及该关系后，必须实测洞口位置已恢复为墙体。洞已固化进 `IfcFacetedBrep` 的墙，仅删 IFC 洞口并不能填实；当前生成器会拒绝这类不能确认补全的目标，选取其他支持目标，并保留失败记录。局部实体填孔的内存试验不等于已写出、原生校验和保全通过的损伤 IFC；不能据此标记自动补墙已支持。

历史版本 1.1 曾为旧请求补足独立洞口形状、位置、轴和 void/fill 关系，并明确宿主墙。这些旧模板、源码快照与旧损伤 IFC 按原版本保留；当前简化请求的信息检查不借用旧模板或私有几何补答案。

## 记录与校验

每个来源目录只保留一份私有参考 IFC，每个损伤题含以下文件：

```text
sources/<source-id>/
  SOURCE.md                    来源、许可和修改声明
  private/reference.ifc        损伤前固定参考，源文件的字节副本
  private/source.json          来源和原有审核证据
  private/progress.json         脚本进度
  result.json                  母本汇总
  cases/case-001/
    public/model.ifc           损伤 IFC
    public/request.txt         本例主请求；与 IFC 构成一对样本
    public/request-*.txt       适用的修复请求
    private/recipe.json        精确配方
    private/mutation.json      删除对象、位置、类型、洞口及属性前后值
    private/validation.json    IfcOpenShell schema＋EXPRESS 结果
    private/preservation.json  指定损伤及其余数据保全结果
    private/prompt-check.json  实际公开文本的信息充分性检查
    private/wall-check.json    墙体补全或保留洞口检查
    private/mesh-check.json    最多三个保留构件的世界网格抽查
    private/seal.json          所有题目文件和记录的完整哈希集合
    case.json                  机器通过、人工待审及模板适用状态
```

`ifcopenshell.validate.validate(..., express_rules=True)` 对母本和每份输出使用同一版本。每份输出写出后重开校验；只有零原生 findings、损伤符合配方、保全通过、源哈希未变及公开请求未泄露删除身份，才标记 `machine_validated=true`。

保全检查覆盖所有保留 `IfcProduct` 的前向引用图、实例属性的真实值/IFC 类型/Unit、类型与材料、空间包含、void/fill 关系，以及 Project、Context 和单位的前向图。候选几何准入网格化可挖构件、可改属性构件和相关墙；没有宣称对母本所有产品逐项独立网格验收。原生语法通过也不等于几何、工程性能或修复能力通过。

本轮每例均执行实际文本、墙体（适用时）及最多 3 个保留构件的网格检查；Codex 仅阅读脚本汇总和少量文本、诊断抽样。旧批次的楼层局部矩阵与分层抽样属于历史检查。任何机器或 Agent 检查均不新增用户人工审核。

首批另用 `scripts/ifc_repair/audit_initial_dataset.py` 从实际公开文本独立解析坐标、方向、截面与拉伸，重建受支持几何；无法参数化的构件，在损伤 IFC 内解析公开参照并比对局部三角网格。还独立检查宿主墙、楼层、洞口及属性定位。它分别报告 IFC 合规性、损伤交叉检查、prompt 信息是否足够，不用原生校验通过替代后两项。该信息检查的范围是明确要求的几何、放置、包含、void/fill 和指定属性，不是原构件全部语义字段的精确复刻，也不是系统成功率。

`summary.json` 是数量入口，`cases.csv` 是通过案例检索表；本轮每例检查记录留在其 `private` 下，旧批次另有 `sampling.json`。失败配方、准入失败、异常日志均保留，不能充当通过样本。收录脚本复核源文件、封存、索引与完整检查记录；跨源码版本复用必须有与原生成指纹匹配的冻结快照。

未来向系统提供一份 `public/model.ifc` 和一份公开 request。参考 IFC、删除 GUID、STEP ID、配方、损伤映射和评价答案留在 private。公开 request 是在损伤前指定的修复任务要求；不会把整个原模型或私有评价文件作为修复输入。本轮没有执行修复，所以数据集通过数不是系统成功率。

## 执行

在仓库根目录使用现有虚拟环境；脚本负责排队、并行、等待、准入替补、日志和最终报告，Codex 阅读汇总与少量抽样记录。

新版独立入口会自动提取目标和完整几何、选损伤、写 prompt、写损伤 IFC，再运行原生校验、实际文本几何/定位/关系/属性检查、墙体补全检查与保留网格抽查。不是由 Codex 逐题撰写。可直接提供一个完整 IFC2X3：

```powershell
.\.venv\Scripts\python.exe scripts/ifc_repair/generate_damage_pilot.py `
  --input path/to/intact.ifc --cases-per-ifc 4 --workers 1 `
  --output .tmp/my-new-damage-pilot
```

自动提取不等于任何 IFC 都能生成足量题目：非 IFC2X3、原生校验失败、无法恢复完整几何、坐标或名称歧义、参照无法存活、无足量独立配方等均记录为失败或数量不足。输出目录必须是新目录，源 IFC 从不原位修改。

自动生成入口默认请求 1.3，可显式用 `--request-profile 1.2` 复现旧规则。`update_damage_pilot.py` 用于此次用户授权的既有 1.2 活动实验集合原位升级：先在新暂存目录完成所有信息与 IFC 检查，再核对并归档旧字节，最后写回原目录。对未变 IFC 复用经旧封存绑定的原生/保全/墙体/网格记录，对换目标题重新生成并重新检查。它拒绝已登记到 Git 的集合，也不接受把当前 1.3 集合重复当作旧 1.2 输入。已接受的正式 Proof 不走此更新入口。

多个母本可用来源清单输入。每例仍从当前 IFC 重新提取几何和属性；清单里的预选操作不代替实时几何提取。首轮选择与替补来源、具体生成命令及源码版本都记录在结果的 `build.json` 与 `summary.json.history`：

```powershell
.\.venv\Scripts\python.exe scripts/ifc_repair/generate_damage_pilot.py `
  --sources path/to/source-selection.json --cases-per-ifc 4 --workers 2 `
  --output .tmp/my-new-multi-source-pilot
```

新试点的每题增加 `private/prompt-check.json`、`wall-check.json`、`mesh-check.json`；主请求与这些检查都加入题目封存。删除洞口时，不只确认 IFC 实体消失，还比较仅取消目标 void 的对照墙、体积及有限洞口内部点占据；保留洞口时验证空洞与关联仍在。不能确认的几何不准入。该检查是几何证据，不是实际模型修复成功率。

世界坐标定位允许跨层墙作为宿主：构件自身楼层归属与墙的空间归属分别检查，不能要求两者相同。墙名定位仍要求在给定楼层中以名称唯一找到墙，跨层名称不足时标为不适用。严格三角网格比较可能保守拒绝仅剖分不同的同形几何；本轮保留这种拒绝，并在报告说明已确认及未解释的原因。

`scripts/ifc_repair/collect_damage_pilot.py` 收录完整通过的母本结果，复制原 IFC、prompt 和封存记录，随后复核完整性；不重写 IFC、不重新封存旧记录、不重复调用原生校验。正式收录后仍标为机器校验、人工待审，本轮不运行修复系统或 Provider。

## 历史首批检查与停止记录

下面是旧首批脚本的复验用法，本轮不续跑这些历史批次。每行给出 `case_folder`、`case_id`，私有参考不在该来源标准目录时另给 `reference`。审计输出目录必须是新的目录，避免覆盖原检查记录：

```powershell
.\.venv\Scripts\python.exe scripts/ifc_repair/audit_initial_dataset.py `
  --inputs .tmp/ifc-initial-audit-inputs.json `
  --output .tmp/first-batch-fresh-audit
```

IfcOpenShell 的构件删除接口可能遗留 `RelatedObjects` 已为空的分类等关联。这种 IFC 会被原生校验挡下。已有收尾函数仅对因此被拦下、且保全通过的失败题，移除损伤清单已记录的空 `IfcRelAssociates`，重新执行同一原生和保全检查；不会处理已有通过题。旧 IFC、旧 findings、旧题目记录与封存保留在该题的 `private/normalization/`，原母本和成功副本不改写。本轮只查验一个独立探针和相应离线测试；不运行全量收尾或补齐生成。

同一配置和源码版本可续跑，但本轮不会续跑暂停的全量批。修改生成代码或配置后须用新的输出目录，保留旧结果。首批修正复验只用一个母本和少量新损伤：

```powershell
.\.venv\Scripts\python.exe -m scripts.ifc_repair.dataset_batch build `
  --output .tmp/ifc-dataset-prototype-v3 `
  --additional-sources 0 --source-ids formal-001 `
  --cases 6 --workers 1 --samples 6
```

只查看或重建报告，不重跑损伤：

```powershell
.\.venv\Scripts\python.exe -m scripts.ifc_repair.dataset_batch status .tmp/ifc-dataset-prototype-v3
.\.venv\Scripts\python.exe scripts/ifc_repair/inspect_batch_dataset.py .tmp/ifc-dataset-prototype-v3
```

最后一个命令生成 `integrity.json`，逐一核对母本/参考副本 SHA、完整题目封存、索引与题目状态、同版本零 findings 原生记录、每母本数量与去重，以及生成代码指纹。它不重新加载 IFC 或重跑网格验证。

实现与范围回归测试位于 `scripts/ifc_repair/dataset_batch/` 与 `tests/ifc_repair/dataset_batch/`。这批数据不是已接受 Repair Proof 安装；没有改写 formal 母本、既有 Proof 或实验历史。
