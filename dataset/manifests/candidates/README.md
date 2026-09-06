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
