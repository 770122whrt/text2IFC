# Phase 6.1 Final Acceptance Report

Generated from live trace sidecars and deterministic IFC gates.

## Accepted Live Case

- case_id: `f1fe46de77a6ce07`
- source_case_dir: `dataset/processed/agent-demo/phase6.2-interactive-cli/runs/f1fe46de77a6ce07`
- case_report: [f1fe46de77a6ce07/report.md](f1fe46de77a6ce07/report.md)

## Final IFC

- [output.ifc](output.ifc)
- [ifc-verification.json](ifc-verification.json)
- [geometry-feedback.json](geometry-feedback.json)

## Acceptance Metrics

```json
{
  "audit_evidence_class": "live",
  "audit_response_id": "c7a319a9ff3c4caea19719cfef4052c0",
  "audit_strict_output_contract_valid": true,
  "case_id": "f1fe46de77a6ce07",
  "compile_reopen_success": true,
  "geometry_success": false,
  "ifc_path": "output.ifc",
  "secret_finding_count": 0,
  "source_case_dir": "dataset/processed/agent-demo/phase6.2-interactive-cli/runs/f1fe46de77a6ce07",
  "stage": "final-acceptance",
  "valid": false
}
```

## IFC Verification

```json
{
  "ifc_issues": [],
  "input_issues": [],
  "output_path": "dataset\\processed\\agent-demo\\phase6.2-interactive-cli\\runs\\f1fe46de77a6ce07\\output.ifc",
  "success": true
}
```

## Geometry Feedback

```json
{
  "issues": [
    {
      "code": "WALL_ORIENTATION_MISMATCH",
      "message": "Wall 'wall-west' has dominant plan axis 'x'; expected 'y'.",
      "path": "/walls/wall-west/axis"
    },
    {
      "code": "WALL_BBOX_MISMATCH",
      "message": "Wall 'wall-west' world bounding box is outside tolerance.",
      "path": "/walls/wall-west/bbox"
    },
    {
      "code": "WALL_ORIENTATION_MISMATCH",
      "message": "Wall 'wall-east' has dominant plan axis 'x'; expected 'y'.",
      "path": "/walls/wall-east/axis"
    },
    {
      "code": "WALL_BBOX_MISMATCH",
      "message": "Wall 'wall-east' world bounding box is outside tolerance.",
      "path": "/walls/wall-east/bbox"
    },
    {
      "code": "ROOM_ENCLOSURE_OPEN",
      "message": "Expected wall geometry does not form the required room enclosure.",
      "path": "/walls"
    }
  ],
  "metrics": {
    "case_id": "f1fe46de77a6ce07",
    "walls": {
      "wall-east": {
        "axis": "x",
        "bbox": {
          "x": [
            4.0,
            8.0
          ],
          "y": [
            1.85,
            2.15
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
        "axis": "x",
        "bbox": {
          "x": [
            -2.0,
            2.0
          ],
          "y": [
            1.85,
            2.15
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
  "success": false
}
```

## Secret Scan

```json
{
  "finding_count": 0,
  "findings": [],
  "scanned_file_count": 77,
  "scanned_path": "dataset\\processed\\agent-demo\\phase6.2-interactive-cli\\runs\\f1fe46de77a6ce07",
  "schema_version": "text2ifc/agent-artifact-scan-v1"
}
```
