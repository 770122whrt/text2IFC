# IFC Candidate Pool Provenance

This directory is discovery and screening infrastructure. It is not canonical IFC admission authority.

## Files

- `ifc-candidate-pool.jsonl`: unified discovery pool across Archiset, BIMData, buildingSMART Community, IFC-Bench V2 references, ThatOpen tests, and directly verified manual discoveries.
- `ifc-candidate-screen.jsonl`: uniform retention screening. `retain_candidate` means IFC2X3, below the current 10 MiB target, non-single-component, and not an exact duplicate when the file has been scanned. It does not by itself mean canonical admission.
- `source-registry.json`: source-level provenance, license/rights classification, attribution requirements, and evidence locations.
- `bimdata-rd-source-evidence.jsonl`: file-level BIMData discovery records resolved to their upstream source family where possible.
- `bimdata-rd-package-evidence.jsonl`: cryptographic package evidence and IFC member inventories for BIMData/DURAARK packages scanned specifically during candidate resolution.
- `bimdata-rd-package-reconciliation.jsonl`: reconciliation of BIMData-reported names/sizes against observed source-package members. Size reconciliation is not identity proof.
- `bimdata-rd-url-probe.jsonl`: current availability classification of unique BIMData upstream URLs.
- `bimdata-rd-resolution.jsonl`: final file-level BIMData provenance resolution and recommended next action.

## Evidence levels

BIMData R&D is treated only as a discovery index. A BIMData row does not grant model rights and does not prove that the reported file name or size matches the linked source.

Evidence is classified as:

- `direct_source_package_scanned`: the original linked package was downloaded and its IFC members were inventoried.
- `source_url_indexed`: BIMData supplies an upstream URL, but the source artifact has not been cryptographically tied to the indexed file.
- `index_only_unresolved`: no usable upstream source URL is available.

Package reconciliation is further classified as:

- `package_scanned_unique_size_match`
- `package_scanned_ambiguous_size_match`
- `package_scanned_no_size_match`

These are source-resolution signals only. Exact file identity requires SHA256 equality.

## Admission rule

A file can move from this candidate layer to canonical source manifests only after provenance/rights review appropriate to the source and the project technical certification pipeline. Dataset-level or repository-level licenses must not be silently promoted to model-level rights when the source does not explicitly provide that grant.

## 2026-09-07 repository handoff

当前池含 396 条记录、6 个来源族；筛选结果为 167 retain_candidate、105 pending_fetch、103 existing_reference、21 exclude。BIMData 来源证据与 resolution 各 107 条，只读 provenance audit 无缺失项。候选数字不能相加到 canonical manifest，也不表示已取得训练或再分发许可。

buildingSMART Community 的早期获取记录见 `../acquisitions/buildingsmart-community.json`（81 个发现、0 个获取，包含 LFS pointer 拒绝）；它是历史获取尝试，不覆盖当前统一 manifest 中的 74 条 Community 登记。

下一步优先处理 167 个保留候选的上游字节、来源权利、SHA 去重、IFC2X3 reopen 与技术准入，再处理 105 个待获取项。统一来源 manifest 的 BIMNet split loader 只选择 BIMNet 记录，继续保持原 scene-family 划分；不把外部来源混入 BIMNet 训练划分。
