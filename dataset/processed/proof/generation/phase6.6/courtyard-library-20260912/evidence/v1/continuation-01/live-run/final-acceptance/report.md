# Phase 6.1 Final Acceptance Report

Generated from live trace sidecars and deterministic IFC gates.

## Accepted Live Case

- case_id: `3cd339b0be4fd872`
- source_case_dir: `dataset/processed/ifc-presentation-validation/courtyard-library-20260912/continuation-01/live-run`
- case_report: [3cd339b0be4fd872/report.md](3cd339b0be4fd872/report.md)

## Final IFC

- [output.ifc](output.ifc)
- [ifc-verification.json](ifc-verification.json)
- [geometry-feedback.json](geometry-feedback.json)

## Acceptance Metrics

```json
{
  "audit_evidence_class": "live",
  "audit_response_id": "e6ee79c7-ce98-4caf-96ae-eb3c91b95ae1",
  "audit_strict_output_contract_valid": true,
  "candidate_origin": "model_with_deterministic_attachments",
  "case_id": "3cd339b0be4fd872",
  "compile_reopen_success": true,
  "deterministic_gates_passed": true,
  "geometry_success": true,
  "ifc_path": "output.ifc",
  "live_acceptance_eligible": true,
  "secret_finding_count": 0,
  "source_case_dir": "dataset/processed/ifc-presentation-validation/courtyard-library-20260912/continuation-01/live-run",
  "stage": "final-acceptance",
  "valid": true
}
```

## IFC Verification

```json
{
  "ifc_issues": [],
  "input_issues": [],
  "output_path": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\courtyard-library-20260912\\continuation-01\\live-run\\final-acceptance\\output.ifc",
  "success": true
}
```

## Geometry Feedback

```json
{
  "expectation_source": "design_brief_expected_facts",
  "issues": [],
  "metrics": {
    "case_id": "3cd339b0be4fd872",
    "floor_openings": {
      "roof-opening-light-court": {
        "bbox": {
          "x": [
            8.0,
            16.0
          ],
          "y": [
            6.0,
            12.0
          ],
          "z": [
            7.0,
            7.2
          ]
        },
        "binding_basis": "explicit_identity",
        "host_slab_id": "roof-slab-storey-2",
        "ifc_class": "IfcOpeningElement",
        "resolved_bim_json_id": "roof-opening-light-court",
        "resolved_global_id": "2hC4XahCHPEhnNUkSnulpu"
      },
      "slab-storey-2-opening-light-court": {
        "bbox": {
          "x": [
            8.0,
            16.0
          ],
          "y": [
            6.0,
            12.0
          ],
          "z": [
            3.4,
            3.6
          ]
        },
        "binding_basis": "explicit_identity",
        "host_slab_id": "slab-storey-2-floor",
        "ifc_class": "IfcOpeningElement",
        "resolved_bim_json_id": "slab-storey-2-opening-light-court",
        "resolved_global_id": "2ctQA2XPXIRfrgpg0QrXpQ"
      },
      "slab-storey-2-opening-stair": {
        "bbox": {
          "x": [
            1.0,
            2.5
          ],
          "y": [
            5.0,
            11.0
          ],
          "z": [
            3.4,
            3.6
          ]
        },
        "binding_basis": "explicit_identity",
        "host_slab_id": "slab-storey-2-floor",
        "ifc_class": "IfcOpeningElement",
        "resolved_bim_json_id": "slab-storey-2-opening-stair",
        "resolved_global_id": "0zthKa4rjOKhRJ4XHOKnm$"
      }
    },
    "products": {
      "storey-2-railing-court-east": {
        "bbox": {
          "x": [
            16.0,
            16.020000000000003
          ],
          "y": [
            6.0,
            12.0
          ],
          "z": [
            3.6,
            4.7
          ]
        },
        "ifc_class": "IfcRailing"
      },
      "storey-2-railing-court-north": {
        "bbox": {
          "x": [
            7.9799999999999995,
            16.02
          ],
          "y": [
            12.0,
            12.02
          ],
          "z": [
            3.6,
            4.7
          ]
        },
        "ifc_class": "IfcRailing"
      },
      "storey-2-railing-court-south": {
        "bbox": {
          "x": [
            7.9799999999999995,
            16.02
          ],
          "y": [
            5.98,
            6.0
          ],
          "z": [
            3.6,
            4.7
          ]
        },
        "ifc_class": "IfcRailing"
      },
      "storey-2-railing-court-west": {
        "bbox": {
          "x": [
            7.98,
            8.0
          ],
          "y": [
            6.0,
            12.0
          ],
          "z": [
            3.6,
            4.7
          ]
        },
        "ifc_class": "IfcRailing"
      }
    },
    "roof": {
      "roof-slab-storey-2": {
        "bbox": {
          "x": [
            0.0,
            24.0
          ],
          "y": [
            0.0,
            18.0
          ],
          "z": [
            7.0,
            7.2
          ]
        },
        "ifc_class": "IfcSlab"
      }
    },
    "slabs": {
      "slab-storey-1-floor": {
        "bbox": {
          "x": [
            0.0,
            24.0
          ],
          "y": [
            0.0,
            18.0
          ],
          "z": [
            -0.2,
            0.0
          ]
        },
        "ifc_class": "IfcSlab"
      },
      "slab-storey-2-floor": {
        "bbox": {
          "x": [
            0.0,
            24.0
          ],
          "y": [
            0.0,
            18.0
          ],
          "z": [
            3.4,
            3.6
          ]
        },
        "ifc_class": "IfcSlab"
      }
    },
    "spaces": {
      "space-storey-1-storey-1-space-corridor-east": {
        "bbox": {
          "x": [
            16.0,
            18.02
          ],
          "y": [
            6.0,
            12.0
          ],
          "z": [
            0.0,
            3.4
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-1-storey-1-space-corridor-north": {
        "bbox": {
          "x": [
            5.98,
            18.02
          ],
          "y": [
            12.0,
            14.02
          ],
          "z": [
            0.0,
            3.4
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-1-storey-1-space-corridor-south": {
        "bbox": {
          "x": [
            5.98,
            18.02
          ],
          "y": [
            3.98,
            6.0
          ],
          "z": [
            0.0,
            3.4
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-1-storey-1-space-corridor-west": {
        "bbox": {
          "x": [
            5.98,
            8.0
          ],
          "y": [
            6.0,
            12.0
          ],
          "z": [
            0.0,
            3.4
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-1-storey-1-space-east-shared-reading": {
        "bbox": {
          "x": [
            18.26,
            23.76
          ],
          "y": [
            3.98,
            14.02
          ],
          "z": [
            0.0,
            3.4
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-1-storey-1-space-north-quiet-reading": {
        "bbox": {
          "x": [
            0.24,
            23.76
          ],
          "y": [
            14.26,
            17.76
          ],
          "z": [
            0.0,
            3.4
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-1-storey-1-space-south-reception": {
        "bbox": {
          "x": [
            0.24,
            23.76
          ],
          "y": [
            0.24,
            3.74
          ],
          "z": [
            0.0,
            3.4
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-1-storey-1-space-west-service-stair": {
        "bbox": {
          "x": [
            0.24,
            5.74
          ],
          "y": [
            3.98,
            14.02
          ],
          "z": [
            0.0,
            3.4
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-2-storey-2-space-corridor-east": {
        "bbox": {
          "x": [
            16.0,
            18.02
          ],
          "y": [
            6.0,
            12.0
          ],
          "z": [
            3.6,
            7.0
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-2-storey-2-space-corridor-north": {
        "bbox": {
          "x": [
            5.98,
            18.02
          ],
          "y": [
            12.0,
            14.02
          ],
          "z": [
            3.6,
            7.0
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-2-storey-2-space-corridor-south": {
        "bbox": {
          "x": [
            5.98,
            18.02
          ],
          "y": [
            3.98,
            6.0
          ],
          "z": [
            3.6,
            7.0
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-2-storey-2-space-corridor-west": {
        "bbox": {
          "x": [
            5.98,
            8.0
          ],
          "y": [
            6.0,
            12.0
          ],
          "z": [
            3.6,
            7.0
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-2-storey-2-space-east-shared-reading": {
        "bbox": {
          "x": [
            18.26,
            23.76
          ],
          "y": [
            3.98,
            14.02
          ],
          "z": [
            3.6,
            7.0
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-2-storey-2-space-north-quiet-reading": {
        "bbox": {
          "x": [
            0.24,
            23.76
          ],
          "y": [
            14.26,
            17.76
          ],
          "z": [
            3.6,
            7.0
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-2-storey-2-space-south-reception": {
        "bbox": {
          "x": [
            0.24,
            23.76
          ],
          "y": [
            0.24,
            3.74
          ],
          "z": [
            3.6,
            7.0
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-2-storey-2-space-west-service-stair": {
        "bbox": {
          "x": [
            0.24,
            5.74
          ],
          "y": [
            3.98,
            14.02
          ],
          "z": [
            3.6,
            7.0
          ]
        },
        "ifc_class": "IfcSpace"
      }
    },
    "stairs": {
      "stair-1": {
        "bbox": {
          "x": [
            1.0,
            2.5
          ],
          "y": [
            5.0,
            11.0
          ],
          "z": [
            0.0,
            3.6
          ]
        },
        "flight_ids": [
          "stair-flight-1"
        ],
        "has_stepped_profile": true,
        "wall_intersections": []
      }
    },
    "wall_set_convention": "primary",
    "walls": {
      "wall-storey-1-storey-1-wall-exterior-east": {
        "axis": "y",
        "bbox": {
          "x": [
            23.759999999999998,
            24.0
          ],
          "y": [
            0.2400000000000002,
            17.759999999999998
          ],
          "z": [
            0.0,
            3.4
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-1-storey-1-wall-exterior-north": {
        "axis": "x",
        "bbox": {
          "x": [
            0.0,
            24.0
          ],
          "y": [
            17.759999999999998,
            18.0
          ],
          "z": [
            0.0,
            3.4
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-1-storey-1-wall-exterior-south": {
        "axis": "x",
        "bbox": {
          "x": [
            0.0,
            24.0
          ],
          "y": [
            0.0,
            0.24
          ],
          "z": [
            0.0,
            3.4
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-1-storey-1-wall-exterior-west": {
        "axis": "y",
        "bbox": {
          "x": [
            0.0,
            0.24
          ],
          "y": [
            0.2400000000000002,
            17.759999999999998
          ],
          "z": [
            0.0,
            3.4
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-1-storey-1-wall-partition-east": {
        "axis": "y",
        "bbox": {
          "x": [
            18.02,
            18.26
          ],
          "y": [
            3.9799999999999995,
            14.02
          ],
          "z": [
            0.0,
            3.4
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-1-storey-1-wall-partition-north": {
        "axis": "x",
        "bbox": {
          "x": [
            0.2400000000000002,
            23.759999999999998
          ],
          "y": [
            14.020000000000001,
            14.26
          ],
          "z": [
            0.0,
            3.4
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-1-storey-1-wall-partition-south": {
        "axis": "x",
        "bbox": {
          "x": [
            0.2400000000000002,
            23.759999999999998
          ],
          "y": [
            3.7399999999999998,
            3.98
          ],
          "z": [
            0.0,
            3.4
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-1-storey-1-wall-partition-west": {
        "axis": "y",
        "bbox": {
          "x": [
            5.74,
            5.98
          ],
          "y": [
            3.9799999999999995,
            14.02
          ],
          "z": [
            0.0,
            3.4
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-1-storey-1-wall-stair-east": {
        "axis": "y",
        "bbox": {
          "x": [
            2.5,
            2.74
          ],
          "y": [
            3.9800000000000004,
            12.600000000000001
          ],
          "z": [
            0.0,
            3.4
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-1-storey-1-wall-stair-west": {
        "axis": "y",
        "bbox": {
          "x": [
            0.76,
            1.0
          ],
          "y": [
            3.9800000000000004,
            12.600000000000001
          ],
          "z": [
            0.0,
            3.4
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-2-storey-2-wall-exterior-east": {
        "axis": "y",
        "bbox": {
          "x": [
            23.759999999999998,
            24.0
          ],
          "y": [
            0.2400000000000002,
            17.759999999999998
          ],
          "z": [
            3.6,
            7.0
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-2-storey-2-wall-exterior-north": {
        "axis": "x",
        "bbox": {
          "x": [
            0.0,
            24.0
          ],
          "y": [
            17.759999999999998,
            18.0
          ],
          "z": [
            3.6,
            7.0
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-2-storey-2-wall-exterior-south": {
        "axis": "x",
        "bbox": {
          "x": [
            0.0,
            24.0
          ],
          "y": [
            0.0,
            0.24
          ],
          "z": [
            3.6,
            7.0
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-2-storey-2-wall-exterior-west": {
        "axis": "y",
        "bbox": {
          "x": [
            0.0,
            0.24
          ],
          "y": [
            0.2400000000000002,
            17.759999999999998
          ],
          "z": [
            3.6,
            7.0
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-2-storey-2-wall-partition-east": {
        "axis": "y",
        "bbox": {
          "x": [
            18.02,
            18.26
          ],
          "y": [
            3.9799999999999995,
            14.02
          ],
          "z": [
            3.6,
            7.0
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-2-storey-2-wall-partition-north": {
        "axis": "x",
        "bbox": {
          "x": [
            0.2400000000000002,
            23.759999999999998
          ],
          "y": [
            14.020000000000001,
            14.26
          ],
          "z": [
            3.6,
            7.0
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-2-storey-2-wall-partition-south": {
        "axis": "x",
        "bbox": {
          "x": [
            0.2400000000000002,
            23.759999999999998
          ],
          "y": [
            3.7399999999999998,
            3.98
          ],
          "z": [
            3.6,
            7.0
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-2-storey-2-wall-partition-west": {
        "axis": "y",
        "bbox": {
          "x": [
            5.74,
            5.98
          ],
          "y": [
            3.9799999999999995,
            14.02
          ],
          "z": [
            3.6,
            7.0
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-2-storey-2-wall-stair-east": {
        "axis": "y",
        "bbox": {
          "x": [
            2.5,
            2.74
          ],
          "y": [
            3.9800000000000004,
            12.600000000000001
          ],
          "z": [
            3.6,
            7.0
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-2-storey-2-wall-stair-west": {
        "axis": "y",
        "bbox": {
          "x": [
            0.76,
            1.0
          ],
          "y": [
            3.9800000000000004,
            12.600000000000001
          ],
          "z": [
            3.6,
            7.0
          ]
        },
        "ifc_class": "IfcWallStandardCase"
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
  "scanned_file_count": 8,
  "scanned_path": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\courtyard-library-20260912\\continuation-01\\live-run\\final-acceptance",
  "schema_version": "text2ifc/agent-artifact-scan-v1"
}
```
