# Phase 6.1 Final Acceptance Report

Generated from live trace sidecars and deterministic IFC gates.

## Accepted Live Case

- case_id: `complete-room`
- source_case_dir: `dataset/processed/agent-demo/phase6.1-mimo-live/complete-room`
- case_report: [complete-room/report.md](complete-room/report.md)

## Final IFC

- [output.ifc](output.ifc)
- [ifc-verification.json](ifc-verification.json)
- [geometry-feedback.json](geometry-feedback.json)

## Acceptance Metrics

```json
{
  "audit_evidence_class": "live",
  "audit_response_id": "msg_7cbe7cb111df4758b0e78786",
  "audit_strict_output_contract_valid": true,
  "case_id": "complete-room",
  "compile_reopen_success": true,
  "geometry_success": true,
  "ifc_path": "output.ifc",
  "secret_finding_count": 0,
  "source_case_dir": "dataset/processed/agent-demo/phase6.1-mimo-live/complete-room",
  "stage": "final-acceptance",
  "valid": true
}
```

## IFC Verification

```json
{
  "ifc_issues": [],
  "input_issues": [],
  "output_path": "C:\\Users\\rt do believe\\.codex\\worktrees\\a542\\bimnet\\dataset\\processed\\agent-demo\\phase6.1-mimo-live\\output.ifc",
  "success": true
}
```

## Geometry Feedback

```json
{
  "issues": [],
  "metrics": {
    "case_id": "complete-room",
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
  "scanned_file_count": 129,
  "scanned_path": "C:\\Users\\rt do believe\\.codex\\worktrees\\a542\\bimnet\\dataset\\processed\\agent-demo\\phase6.1-mimo-live",
  "schema_version": "text2ifc/agent-artifact-scan-v1"
}
```
