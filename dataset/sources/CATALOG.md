# External Data Source Catalog

This catalog records sources considered for text2IFC data expansion. A public
download URL alone does not make a source suitable for training. Each source
must have a reviewed license, provenance, validation status, and intended use.

## Approved Sources

### BIMNet

- Repository: https://github.com/LydJason/BIMNet
- Dataset basis: Matterport3D-derived scans with dedicated manually modeled IFC
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
