# Phase 6.1 Final Acceptance Report

Generated from live trace sidecars and deterministic IFC gates.

## Accepted Live Case

- case_id: `corrective-02-binding-revalidation`
- source_case_dir: `dataset/processed/ifc-presentation-validation/live-semantic-20260908-01/generation/corrective-02-general-revalidation`
- case_report: [corrective-02-binding-revalidation/report.md](corrective-02-binding-revalidation/report.md)

## Final IFC

- [output.ifc](output.ifc)
- [ifc-verification.json](ifc-verification.json)
- [geometry-feedback.json](geometry-feedback.json)

## Acceptance Metrics

```json
{
  "audit_evidence_class": "live",
  "audit_response_id": "a7baee6f-658a-4856-8e4c-d9d464c7d67e",
  "audit_strict_output_contract_valid": true,
  "candidate_origin": "legacy_unspecified",
  "case_id": "corrective-02-binding-revalidation",
  "compile_reopen_success": true,
  "deterministic_gates_passed": true,
  "geometry_success": true,
  "ifc_path": "output.ifc",
  "live_acceptance_eligible": true,
  "secret_finding_count": 0,
  "source_case_dir": "dataset/processed/ifc-presentation-validation/live-semantic-20260908-01/generation/corrective-02-general-revalidation",
  "stage": "final-acceptance",
  "valid": true
}
```

## IFC Verification

```json
{
  "ifc_issues": [],
  "input_issues": [],
  "output_path": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\live-semantic-20260908-01\\generation\\corrective-02-general-revalidation\\output.ifc",
  "success": true
}
```

## Geometry Feedback

```json
{
  "expectation_source": "design_brief_expected_facts",
  "issues": [],
  "metrics": {
    "case_id": "corrective-02-binding-revalidation",
    "floor_openings": {},
    "products": {},
    "roof": {},
    "slabs": {
      "slab-ground": {
        "bbox": {
          "x": [
            -3.2,
            3.2
          ],
          "y": [
            -2.2,
            2.2
          ],
          "z": [
            -0.15,
            0.0
          ]
        },
        "ifc_class": "IfcSlab"
      }
    },
    "spaces": {
      "space-storey-1-space-room": {
        "bbox": {
          "x": [
            -3.0,
            3.0
          ],
          "y": [
            -2.0,
            2.0
          ],
          "z": [
            0.0,
            3.0
          ]
        },
        "ifc_class": "IfcSpace"
      }
    },
    "stairs": {},
    "wall_set_convention": "primary",
    "walls": {}
  },
  "success": true
}
```

## Secret Scan

```json
{
  "finding_count": 0,
  "findings": [],
  "scanned_file_count": 68,
  "scanned_path": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\live-semantic-20260908-01\\generation\\corrective-02-general-revalidation",
  "schema_version": "text2ifc/agent-artifact-scan-v1"
}
```
