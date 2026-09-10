# Phase 6.1 Final Acceptance Report

Generated from live trace sidecars and deterministic IFC gates.

## Accepted Live Case

- case_id: `8b3add702299a50f`
- source_case_dir: `dataset/processed/proof/generation/phase6.6/three-storey-clarification-ab-20260910/evidence/frozen/B-retain/runtime/runs/8b3add702299a50f`
- case_report: [8b3add702299a50f/report.md](8b3add702299a50f/report.md)

## Final IFC

- [output.ifc](output.ifc)
- [ifc-verification.json](ifc-verification.json)
- [geometry-feedback.json](geometry-feedback.json)

## Acceptance Metrics

```json
{
  "audit_evidence_class": "live",
  "audit_response_id": "1c906436-e70a-49e7-9743-884edae234d4",
  "audit_strict_output_contract_valid": true,
  "candidate_origin": "changeset_revision",
  "case_id": "8b3add702299a50f",
  "compile_reopen_success": true,
  "deterministic_gates_passed": true,
  "geometry_success": true,
  "ifc_path": "output.ifc",
  "live_acceptance_eligible": true,
  "secret_finding_count": 0,
  "source_case_dir": "dataset/processed/proof/generation/phase6.6/three-storey-clarification-ab-20260910/evidence/frozen/B-retain/runtime/runs/8b3add702299a50f",
  "stage": "final-acceptance",
  "valid": true
}
```

## IFC Verification

```json
{
  "ifc_issues": [],
  "input_issues": [],
  "output_path": "E:\\code for project\\bimnet\\dataset\\processed\\proof\\generation\\phase6.6\\three-storey-clarification-ab-20260910\\validation\\B-retain\\output.ifc",
  "success": true
}
```

## Geometry Feedback

```json
{
  "expectation_source": "design_brief_expected_facts",
  "issues": [],
  "metrics": {
    "case_id": "8b3add702299a50f",
    "floor_openings": {
      "slab-storey-2-opening-stair": {
        "bbox": {
          "x": [
            8.0,
            9.600000000000001
          ],
          "y": [
            1.5,
            6.9
          ],
          "z": [
            3.0,
            3.15
          ]
        },
        "binding_basis": "explicit_identity",
        "host_slab_id": "slab-storey-2",
        "ifc_class": "IfcOpeningElement",
        "resolved_bim_json_id": "slab-storey-2-opening-stair",
        "resolved_global_id": "0WKeTbtWbI2O3zqN4nzkr0"
      },
      "slab-storey-3-opening-stair": {
        "bbox": {
          "x": [
            8.0,
            9.600000000000001
          ],
          "y": [
            1.5,
            6.9
          ],
          "z": [
            6.150000000000001,
            6.300000000000002
          ]
        },
        "binding_basis": "explicit_identity",
        "host_slab_id": "slab-storey-3",
        "ifc_class": "IfcOpeningElement",
        "resolved_bim_json_id": "slab-storey-3-opening-stair",
        "resolved_global_id": "3VGC770UTOXPgqn7oTcfhU"
      }
    },
    "products": {},
    "roof": {
      "roof-slab": {
        "bbox": {
          "x": [
            -0.20000000000000018,
            10.2
          ],
          "y": [
            -0.20000000000000018,
            8.600000000000001
          ],
          "z": [
            9.3,
            9.450000000000001
          ]
        },
        "ifc_class": "IfcRoof"
      }
    },
    "slabs": {
      "slab-ground": {
        "bbox": {
          "x": [
            -0.20000000000000018,
            10.2
          ],
          "y": [
            -0.20000000000000018,
            8.600000000000001
          ],
          "z": [
            -0.15,
            0.0
          ]
        },
        "ifc_class": "IfcSlab"
      },
      "slab-storey-2": {
        "bbox": {
          "x": [
            -0.20000000000000018,
            10.2
          ],
          "y": [
            -0.20000000000000018,
            8.600000000000001
          ],
          "z": [
            3.0,
            3.15
          ]
        },
        "ifc_class": "IfcSlab"
      },
      "slab-storey-3": {
        "bbox": {
          "x": [
            -0.20000000000000018,
            10.2
          ],
          "y": [
            -0.20000000000000018,
            8.600000000000001
          ],
          "z": [
            6.150000000000001,
            6.300000000000002
          ]
        },
        "ifc_class": "IfcSlab"
      }
    },
    "spaces": {
      "space-storey-1-space-hall-1": {
        "bbox": {
          "x": [
            0.0,
            7.6000000000000005
          ],
          "y": [
            0.0,
            8.4
          ],
          "z": [
            0.0,
            3.0
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-1-space-stairwell-1": {
        "bbox": {
          "x": [
            7.8,
            10.0
          ],
          "y": [
            0.0,
            8.4
          ],
          "z": [
            0.0,
            3.0
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-2-space-hall-2": {
        "bbox": {
          "x": [
            0.0,
            7.6000000000000005
          ],
          "y": [
            0.0,
            8.4
          ],
          "z": [
            3.15,
            6.15
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-2-space-landing-north-2": {
        "bbox": {
          "x": [
            7.8,
            10.0
          ],
          "y": [
            6.9,
            8.4
          ],
          "z": [
            3.15,
            6.15
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-3-space-hall-3": {
        "bbox": {
          "x": [
            0.0,
            7.6000000000000005
          ],
          "y": [
            0.0,
            8.4
          ],
          "z": [
            6.3,
            9.3
          ]
        },
        "ifc_class": "IfcSpace"
      },
      "space-storey-3-space-landing-south-3": {
        "bbox": {
          "x": [
            7.8,
            10.0
          ],
          "y": [
            0.0,
            1.5
          ],
          "z": [
            6.3,
            9.3
          ]
        },
        "ifc_class": "IfcSpace"
      }
    },
    "stairs": {
      "stair-1": {
        "bbox": {
          "x": [
            8.2,
            9.399999999999999
          ],
          "y": [
            1.5,
            6.9
          ],
          "z": [
            0.0,
            3.15
          ]
        },
        "flight_ids": [
          "stair-flight-1"
        ],
        "has_stepped_profile": true,
        "wall_intersections": []
      },
      "stair-2": {
        "bbox": {
          "x": [
            8.200000000000001,
            9.4
          ],
          "y": [
            1.5,
            6.9
          ],
          "z": [
            3.15,
            6.3
          ]
        },
        "flight_ids": [
          "stair-flight-2"
        ],
        "has_stepped_profile": true,
        "wall_intersections": []
      }
    },
    "wall_set_convention": "primary",
    "walls": {
      "wall-storey-1-storey-1-wall-east": {
        "axis": "y",
        "bbox": {
          "x": [
            10.0,
            10.2
          ],
          "y": [
            -0.20000000000000018,
            8.600000000000001
          ],
          "z": [
            0.0,
            3.0
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-1-storey-1-wall-north": {
        "axis": "x",
        "bbox": {
          "x": [
            -0.20000000000000018,
            10.2
          ],
          "y": [
            8.4,
            8.6
          ],
          "z": [
            0.0,
            3.0
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-1-storey-1-wall-partition": {
        "axis": "y",
        "bbox": {
          "x": [
            7.6000000000000005,
            7.8
          ],
          "y": [
            0.0,
            8.4
          ],
          "z": [
            0.0,
            3.0
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-1-storey-1-wall-south": {
        "axis": "x",
        "bbox": {
          "x": [
            -0.20000000000000018,
            10.2
          ],
          "y": [
            -0.2,
            0.0
          ],
          "z": [
            0.0,
            3.0
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-1-storey-1-wall-west": {
        "axis": "y",
        "bbox": {
          "x": [
            -0.2,
            0.0
          ],
          "y": [
            -0.20000000000000018,
            8.600000000000001
          ],
          "z": [
            0.0,
            3.0
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-2-storey-2-wall-east": {
        "axis": "y",
        "bbox": {
          "x": [
            10.0,
            10.2
          ],
          "y": [
            -0.20000000000000018,
            8.600000000000001
          ],
          "z": [
            3.15,
            6.15
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-2-storey-2-wall-north": {
        "axis": "x",
        "bbox": {
          "x": [
            -0.20000000000000018,
            10.2
          ],
          "y": [
            8.4,
            8.6
          ],
          "z": [
            3.15,
            6.15
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-2-storey-2-wall-partition": {
        "axis": "y",
        "bbox": {
          "x": [
            7.6000000000000005,
            7.8
          ],
          "y": [
            0.0,
            8.4
          ],
          "z": [
            3.15,
            6.15
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-2-storey-2-wall-south": {
        "axis": "x",
        "bbox": {
          "x": [
            -0.20000000000000018,
            10.2
          ],
          "y": [
            -0.2,
            0.0
          ],
          "z": [
            3.15,
            6.15
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-2-storey-2-wall-west": {
        "axis": "y",
        "bbox": {
          "x": [
            -0.2,
            0.0
          ],
          "y": [
            -0.20000000000000018,
            8.600000000000001
          ],
          "z": [
            3.15,
            6.15
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-3-storey-3-wall-east": {
        "axis": "y",
        "bbox": {
          "x": [
            10.0,
            10.2
          ],
          "y": [
            -0.20000000000000018,
            8.600000000000001
          ],
          "z": [
            6.3,
            9.3
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-3-storey-3-wall-north": {
        "axis": "x",
        "bbox": {
          "x": [
            -0.20000000000000018,
            10.2
          ],
          "y": [
            8.4,
            8.6
          ],
          "z": [
            6.3,
            9.3
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-3-storey-3-wall-partition": {
        "axis": "y",
        "bbox": {
          "x": [
            7.6000000000000005,
            7.8
          ],
          "y": [
            0.0,
            8.4
          ],
          "z": [
            6.3,
            9.3
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-3-storey-3-wall-south": {
        "axis": "x",
        "bbox": {
          "x": [
            -0.20000000000000018,
            10.2
          ],
          "y": [
            -0.2,
            0.0
          ],
          "z": [
            6.3,
            9.3
          ]
        },
        "ifc_class": "IfcWallStandardCase"
      },
      "wall-storey-3-storey-3-wall-west": {
        "axis": "y",
        "bbox": {
          "x": [
            -0.2,
            0.0
          ],
          "y": [
            -0.20000000000000018,
            8.600000000000001
          ],
          "z": [
            6.3,
            9.3
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
  "scanned_path": "E:\\code for project\\bimnet\\dataset\\processed\\proof\\generation\\phase6.6\\three-storey-clarification-ab-20260910\\validation\\B-retain",
  "schema_version": "text2ifc/agent-artifact-scan-v1"
}
```
