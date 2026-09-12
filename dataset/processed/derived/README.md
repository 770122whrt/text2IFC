# 派生数据

本目录合并此前散落在 processed 顶层的数据处理产物。只调整位置，数据内容、授权、划分、模型语义与历史结论保持原样。

| 内容 | 位置 |
|---|---|
| 旧解析 JSON | ifc_parsed_data.json、ifc_parsed_enhanced.json |
| 文本描述与完整 dump | descriptions/、full_dump/ |
| 历史 IFC 回转输出 | roundtrip_json/、roundtrip_ifc/ |
| BIM JSON 1.0 转换及 2.0 提取审计 | bim-json-1.0/、bim-json-2.0/ |
| Phase 4 保真度清单、Phase 6 训练清单 | phase4/、phase6/ |

[迁移映射](../../manifests/processed-layout-20260913.json) 记录旧位置、新位置和原文件 SHA-256。历史数据中的来源路径不改写；训练／评估数据本体继续位于 [text2json](../text2json/README.md)，源 IFC 位于 dataset/external。

对应的转换、提取审计、描述、回转和清单脚本默认读写本目录。不得因为可以重建就自动删除唯一记录或重新生成历史结论。
