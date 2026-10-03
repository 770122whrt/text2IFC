# 开发样例的来源与许可

核对日期：2026-09-29。本文随私有制题材料保存；公开运行投影不是独立的对外发布包。对外分发任何 IFC 时，应连同适用的许可、署名和修改说明提供，不能只拿运行目录作为发布物。

## LargeBuilding

- 来源：[André “MG” Wisén 的 bim-whale-ifc-samples](https://github.com/andrewisen/bim-whale-ifc-samples)。
- 许可：[MIT 原文](https://github.com/andrewisen/bim-whale-ifc-samples/blob/main/LICENSE)，Copyright (c) 2020 André “MG” Wisén；本题另外附本地 LICENSE 原文。
- 原始登记文件：`LargeBuilding/IFC/LargeBuilding.ifc`，SHA-256 `102f8123f85eae5e237d7f6a9dcbc364bd5f1c0cfb94b40a7eeb2d7eac9bb725`。
- 本题 G 是现有数据登记采用的历史修复副本，SHA-256 `5a0c3abcd22689dd6a4537339aadce4af17678cbc9d6f5cf26742156e0f25262`。不是上游下载原件，不把旧数据修复算成本次 Repair 成绩。
- 本次派生修改：移除指定中间窗及其洞口，供开发题审阅；源与参考字节保留，改动由私有 mutation 记录描述。

## Duplex Apartment

- 来源：[buildingSMART Community Sample & Test Files](https://github.com/buildingsmart-community/Community-Sample-Test-Files)，文件 `IFC 2.3.0.1 (IFC 2x3)/Duplex Apartment/Duplex_A_20110907.ifc`。
- 上游 [README](https://github.com/buildingsmart-community/Community-Sample-Test-Files#readme)声明贡献文件采用 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)；[上游 LICENSE](https://github.com/buildingsmart-community/Community-Sample-Test-Files/blob/main/LICENSE)。本地资产登记记录为 CC-BY-4.0、research-evaluation、allowed_with_attribution。
- 署名保留上游提供者、模型名称、原 IFC 文件头和来源链接；不编造未核实的个人作者或声称 buildingSMART 背书。
- 本题 G 保留原始登记字节，SHA-256 `b347a2c8aa8fff6db896a4417a9c50c22ac0ccd7c5cfc22b99b8d29336c606ed`。
- 本次派生修改：移除一扇门、保留洞口及墙关联，供开发题审阅；修改记录与原始文件头保留。

## 样本计数

两个开发文件分别属于 LargeBuilding 与 Duplex Apartment 场景族，均已进入开发上下文。后续约 20 个不同 IFC 的选取优先有明确许可、不同建筑／场景；同一模型的损坏版、历史修复版、导出版本不增加独立样本数。开发与正式未见样本分别登记，不把已看过的同族模型包装成未见场景。
