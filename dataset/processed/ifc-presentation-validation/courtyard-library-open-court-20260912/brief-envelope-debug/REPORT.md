# 开敞布局与闭合墙环：有界修复

真实失败 run `f6ff16398bbd1f6e` 停在 Brief，78,490 token，stop 正常，未生成 IFC。原请求明确南侧敞开，模型却为两层都声明 inside_wall_envelope；原确定性检查分别报告 gap。此前完整闭合要求属于旧方案；本次请求未带入旧 IFC/Brief。直接证据是 Prompt 将轮廓内、不重叠和外围覆盖捆绑，Schema 2.6 没有单独表达前两项的 kind。

假设和修改前案例族见 failure-family.json。frozen-response-diagnosis.json 原样重放真实输出仍有两处 gap；离线副本只改约束声明与目标版本，全部墙坐标不变即可通过。该副本未作为 Provider 或生成输入，不能冒充真实成功。

新增 Brief 2.7：保留 inside_wall_envelope 原语义；wall_layout 的 checks 只选择 inside_outline / non_overlapping，不暗含外围全覆盖。检查所有指定楼层墙的实际平面范围，支持正交凹多边形、平移/镜像/旋转；两项分别启用时互不干扰。新版本沿用 BIM JSON 2.3，保留梁柱、细杆护栏及门窗部件样式能力。CLI 默认版本和 legacy_full 默认策略不变。

新增 Prompt 2.22/2.23、平面修正1.1及语义修正1.5，旧文件与 registry 既有条目不改。几何修正仍只改 derived_wall_ids 对应 bounds，不能删 checks、改变约束适用性或挪动明确墙。整套来源/变更生命周期管理留待下一小步；source_turns 的存在性检查不能证明语言蕴含。

验证证据：

- red.xml：17失败/7通过，新合同尚未实现；实际旧合同失败另保留于 live-run。
- green-01.xml：55通过/14失败；新 Prompt 开发稿登记了 Windows 原始换行哈希，registry 要求规范化换行，导致渲染前拒绝；未有真实调用。
- green-02.xml：修正仅新增未发布条目的登记哈希后，69通过，旧闭合、开敞正反例及原子修正均通过。
- stage-01.xml：303通过，无跳过；包含新旧合同、两种生成策略、实际 IFC 编译重开、部件保全、澄清恢复、非法/截断响应、尝试保留、来源和 registry。
- runner-01.xml：1通过，第二版新运行包装器完整 fake Brief→Generator→Audit3.0→最终 IFC，继承预算及旧账本不变。

测试集合重叠，不能相加为能力样本。没有仓库 Full Preflight、盲测或系统能力提升声明。真实重试使用 rerun-01 冻结输入：用户委托微调颜色，几何/材料/数量不变。旧失败和累计10次/828,490 token账本完整保留。
