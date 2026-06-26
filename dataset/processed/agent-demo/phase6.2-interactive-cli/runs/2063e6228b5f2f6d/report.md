# Phase 6.1 Final Acceptance Report

Generated from live trace sidecars and deterministic IFC gates.

## Accepted Live Case

- case_id: `2063e6228b5f2f6d`
- source_case_dir: `dataset/processed/agent-demo/phase6.2-interactive-cli/runs/2063e6228b5f2f6d`
- case_report: [2063e6228b5f2f6d/report.md](2063e6228b5f2f6d/report.md)

## Final IFC

- [output.ifc](output.ifc)
- [ifc-verification.json](ifc-verification.json)
- [geometry-feedback.json](geometry-feedback.json)

## Acceptance Metrics

```json
{
  "audit_evidence_class": "live",
  "audit_response_id": "d00ea640a9c9465c9d1e384196135706",
  "audit_strict_output_contract_valid": true,
  "case_id": "2063e6228b5f2f6d",
  "compile_reopen_success": true,
  "geometry_success": true,
  "ifc_path": "output.ifc",
  "secret_finding_count": 0,
  "source_case_dir": "dataset/processed/agent-demo/phase6.2-interactive-cli/runs/2063e6228b5f2f6d",
  "stage": "final-acceptance",
  "valid": true
}
```

## IFC Verification

```json
{
  "ifc_issues": [],
  "input_issues": [],
  "output_path": "dataset\\processed\\agent-demo\\phase6.2-interactive-cli\\runs\\2063e6228b5f2f6d\\output.ifc",
  "success": true
}
```

## Geometry Feedback

```json
{
  "issues": [],
  "metrics": {
    "case_id": "2063e6228b5f2f6d",
    "walls": {
      "wall-east": {
        "axis": "y",
        "bbox": {
          "x": [
            5.85,
            6.15
          ],
          "y": [
            0.0,
            4.0
          ],
          "z": [
            0.0,
            3.0
          ]
        },
        "ifc_class": "IfcWall"
      },
      "wall-north": {
        "axis": "x",
        "bbox": {
          "x": [
            0.0,
            6.0
          ],
          "y": [
            3.85,
            4.15
          ],
          "z": [
            0.0,
            3.0
          ]
        },
        "ifc_class": "IfcWall"
      },
      "wall-south": {
        "axis": "x",
        "bbox": {
          "x": [
            0.0,
            6.0
          ],
          "y": [
            -0.15,
            0.15
          ],
          "z": [
            0.0,
            3.0
          ]
        },
        "ifc_class": "IfcWall"
      },
      "wall-west": {
        "axis": "y",
        "bbox": {
          "x": [
            -0.15,
            0.15
          ],
          "y": [
            0.0,
            4.0
          ],
          "z": [
            0.0,
            3.0
          ]
        },
        "ifc_class": "IfcWall"
      }
    }
  },
  "success": true
}
```

## Secret Scan

```json
{
  "finding_count": 0,
  "findings": [],
  "scanned_file_count": 77,
  "scanned_path": "dataset\\processed\\agent-demo\\phase6.2-interactive-cli\\runs\\2063e6228b5f2f6d",
  "schema_version": "text2ifc/agent-artifact-scan-v1"
}
```
