# formal-019 离线链路核对

**待用户审阅，未冻结。** 下列证据为确定性bound输入，不是模型成绩或正式实验准入。

- [本包链路状态](private/pipeline-readiness.json)。
- [自包含几何证据](private/offline-support/geometry-bound/README.md) · [结果](private/offline-support/geometry-bound/result.json)。
- [相关 containment 家族及旧回归](private/offline-support/related-containment/b-multi-containment-validation.json)：46项家族、62项旧回归通过，原测试日志与receipt在同目录。

几何证据覆盖public resolve → bind → apply → reopen → L0/L1/L2/preservation → terminal publish，原G仅在输出后独立测量。复制的原权威不改写，旧运行路径通过original-path-map.json映射到当前包内文件。

初始请求保留必要未知信息。[预写答复卡](private/answer-card.json)只允许按实际问题逐事实答复，不整卡发送、不临时读取G补事实。
已有bound探针明确给出完整几何事实，证明答复明确后的执行可行性；未生成自然问题，也未测试原会话恢复。

019新增完整检查已通过：[自包含材料](private/offline-support/beam-column-after-answers/README.md) · [主结果](private/offline-support/beam-column-after-answers/result.json) · [补回IFC](private/offline-support/beam-column-after-answers/repair/repaired.ifc)。
两个add操作经现有exact IFC2X3 registry、manifest及binder生成各自LoadBearing赋值；重开后梁和柱均为唯一occurrence_direct IfcBoolean(true)。整个题目使用一个atomic ChangeSet，几何、各自楼层及原件保全通过。
[第二操作失败回滚](private/offline-support/beam-column-after-answers/injected-atomic-rollback.json)是明确注入的离线负例：不发布部分产物，D保持不变。
预写答案作为确定性夹具提供，未观察真实模型提问或真人回答。旧019几何probe未含这两项属性；不回写旧成绩。新检查不证明自然语言属性检索、RAG或完整B实验运行时。

所有路径相对于本包，不依赖外部.tmp链接。当前未完成自然Stage1/3、真实模型调用或正式四组实验。浏览器桥接及CUA不可用，VIEW仅静态脚本/实际网格数据检查通过，未声称WebGL或usBIM视觉核验。
