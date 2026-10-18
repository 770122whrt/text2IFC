# External Data Source Catalog

最新文件资产视图为 [387 个来源资产登记](../external/ifc-asset-register.csv)（2026-09-26）。本批建筑来源、修复与许可见[执行报告](../external/_checks/ifc-expand-20260926-v8/REPORT.md)与[逐模型许可证据](../external/_checks/ifc-expand-20260926-v8/rights/RIGHTS.md)。新增Tafraout与欧洲LCA均CC BY4；IfcOpenHouse仍许可未明。139个核心场景与训练准入保留；来源登记不等于统一开放许可。此前许可矩阵仍见[9月24日复核](../external/_checks/ifc-readiness-20260924-v7/rights/RIGHTS.md)。

原 [324 份 IFC 清理登记](../manifests/dataset-registration-20260913/active-ifc-register.csv)保留为扩充前基线：原 274 份与 50 份 ResBIM。ResBIM 的 MIT 声明、RVT 哈希和转换验证报告保留在 [RVT 管理目录](../external/RVT/README.md)，仍为合成住宅单元；RVT 扩充与转换继续暂停。

本页下方是来源历史说明。BIM Whale 的五个 RVT 已于 2026-09-13 经用户明确批准删除，六个 IFC 保留；IFC-Bench 本地为 48 个 IFC，上游历史的 50 个不代表现存数量。

既有 canonical 来源登记以 [ifc-sources.json](../manifests/ifc-sources.json) 与 [ifc-files.jsonl](../manifests/ifc-files.jsonl) 为入口；新增资产与修复首选版本以本页顶部 external 登记为准。下文保留初始来源审查记录。新增来源的存在不自动意味着训练或再分发许可。BIMNet 当前位置为 `dataset/external/bimnet/`，授权边界不变。

This catalog records sources considered for text2IFC data expansion. A public
download URL alone does not make a source suitable for training. Each source
must have a reviewed license, provenance, validation status, and intended use.

## Approved Sources

### BIMNet

- Repository: https://github.com/LydJason/BIMNet
- Dataset basis: Matterport3D-derived scans with dedicated manually modeled IFC
- Local paper: `dataset/sources/PAPERS/Liu-et-al-2025-BIM-reconstruction-dataset-benchmark.pdf`
- Local Matterport terms: `dataset/sources/LICENSES/Matterport/MP_TOS.pdf`
- Chinese reference translation: `dataset/sources/LICENSES/Matterport/MP_TOS.zh-CN.md`
  (non-authoritative; consult the original PDF for legal interpretation)
- Local content: 25 IFC2X3 files
- Authorization: User confirmed Matterport3D/BIMNet authorization for local
  training on 2026-06-11.
- Status: Approved for local extraction, train/validation/test construction,
  baseline evaluation, and local model training.
- Split rule: Group by the base Matterport scene ID before generating any
  text variants. Different floors of one scene must remain in one split.
- Redistribution: Not inferred from local training authorization. Raw or
  derived redistribution must follow the source terms and documented grant.
- Manifest requirement: Phase 2.5 must add file hashes, scene-family IDs,
  authorization status, and approved uses before pair generation.

### buildingSMART Sample-Test-Files

- Repository: https://github.com/buildingSMART/Sample-Test-Files
- Publisher: buildingSMART International
- License: Creative Commons Attribution 4.0 International
- Local license: `dataset/sources/LICENSES/buildingSMART-Sample-Test-Files.txt`
- Status: Approved for local testing and derived-data experiments with
  attribution.
- Content: Official simple PCERT and ISO specification sample IFC files.
- Current schemas: IFC4 and IFC4X3.
- Use in text2IFC:
  - cross-schema parser tests
  - validator tests
  - future schema compatibility research
  - derived text/JSON pairs only when the target contract and attribution
    policy explicitly support the source schema
- Restriction: Do not mix these files into the IFC2X3 Phase 1/2 truth set.

## Review-required Sources

### BIM Whale IFC Samples

- Repository: https://github.com/andrewisen/bim-whale-ifc-samples
- Pinned revision: `595fa90e3af7120d004fcb37a79d8657f1d1c9c2`
- License: MIT, retained in the linked corpus.
- Local form: Git submodule at
  `dataset/external/bim-whale-ifc-samples`.
- Content: Six dummy IFC2X3 sample models plus authoring and screenshot files.
- Current use: parser, compiler, and geometry robustness research.
- Training status: Not admitted. Selected files still require individual raw
  manifest records, provenance, and split assignment.

### IFC-Bench

- Repository: https://huggingface.co/datasets/sylvainHellin/ifc-bench
- Pinned revision: `fa301cfbff5bcc0a27a5e8ef7714fea48b123208`
- Dataset license: CC BY 4.0 for the benchmark content. Included IFC models
  retain project-specific licenses, including GPLv3, MIT, CC BY 3.0, and
  CC BY 4.0 variants.
- Local form: Git submodule at `dataset/external/ifc-bench`.
- Content: 22 projects, 50 IFC files, and 1,027 question-answer records.
- Current use: evaluation and schema/spatial reasoning research only.
- Training status: Not admitted. Each selected IFC model requires a
  project-level license decision, an individual raw manifest record, and a
  leak-free split assignment.

### buildingSMART Community-Sample-Test-Files

- Repository:
  https://github.com/buildingsmart-community/Community-Sample-Test-Files
- License: Creative Commons Attribution 4.0 International
- Status: License approved, data quality review required.
- Reason: The repository states that many files do not pass the buildingSMART
  validation service.
- Planned use:
  - negative and robustness samples
  - schema diversity
  - selected valid files after automated validation and manual review
- Acquisition policy: Build an inventory and screening report before copying
  selected files into `dataset/external/`.

### IFCNet

- Repository: https://github.com/RWTH-E3D/ifcnet-models
- Code license: MIT
- Data form: Processed IFC entity classification artifacts such as PNG, PLY,
  and NPZ.
- Status: Auxiliary research source, not a building-level IFC/Text dataset.
- Restriction: Review dataset-specific terms separately from the code license
  before using data.

### Text2MBL

- Repository: https://github.com/CI3LAB/Text2MBL
- Content claim: Text and BIM-code data for modular building layouts.
- Status: Research only.
- Restriction: No repository LICENSE was found during the 2026-06-11 review.
  Do not copy data into training sets without explicit licensing clarification.

## Required Provenance Fields

Every file admitted to `dataset/external/` must have a record in
`dataset/manifests/raw-files.jsonl` containing:

- stable local ID
- source repository and source path
- source revision
- retrieval date
- license identifier
- local path
- SHA256
- declared IFC schema
- validation status
- approved uses
- training eligibility
