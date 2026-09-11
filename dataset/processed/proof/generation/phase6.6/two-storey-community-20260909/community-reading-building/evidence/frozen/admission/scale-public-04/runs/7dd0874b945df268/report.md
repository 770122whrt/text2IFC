# Phase 6.2 Interactive CLI Run Report

Generated from SQLite session records and linked trace artifacts.

## Original Input

```text
创建一个三层矩形建筑，每层包含一个办公室和一个楼梯间，并生成两段竖向楼梯、各层楼板、屋面、门窗和正确楼层归属。
```

## Transcript

```json
[
  {
    "created_at": "2026-09-09T03:32:37+00:00",
    "role": "user",
    "text": "创建一个三层矩形建筑，每层包含一个办公室和一个楼梯间，并生成两段竖向楼梯、各层楼板、屋面、门窗和正确楼层归属。",
    "turn_index": 0
  }
]
```

## Design Brief Agent

- [design-brief/input.txt](design-brief/input.txt)
- [design-brief/conversation.json](design-brief/conversation.json)
- [design-brief/prompt-rendered.md](design-brief/prompt-rendered.md)
- [design-brief/request.redacted.json](design-brief/request.redacted.json)
- [design-brief/response.raw.json](design-brief/response.raw.json)
- [design-brief/model-text.txt](design-brief/model-text.txt)
- [design-brief/design-brief.json](design-brief/design-brief.json)
- [design-brief/validation.json](design-brief/validation.json)
- [design-brief/metrics.json](design-brief/metrics.json)

## BIM JSON Generator

- [generator/prompt-rendered.md](generator/prompt-rendered.md)
- [generator/request.redacted.json](generator/request.redacted.json)
- [generator/response.raw.json](generator/response.raw.json)
- [generator/model-text.txt](generator/model-text.txt)
- [generator/candidate.json](generator/candidate.json)
- [generator/validation.json](generator/validation.json)
- [generator/metrics.json](generator/metrics.json)

## Repair Route

- [repair/route.json](repair/route.json)
- [repair/repair-attempts.json](repair/repair-attempts.json)
- [repair/source-validation.json](repair/source-validation.json)
- [repair/metrics.json](repair/metrics.json)

## Audit Agent

- [audit/prompt-rendered.md](audit/prompt-rendered.md)
- [audit/request.redacted.json](audit/request.redacted.json)
- [audit/response.raw.json](audit/response.raw.json)
- [audit/model-text.txt](audit/model-text.txt)
- [audit/audit-report.json](audit/audit-report.json)
- [audit/validation.json](audit/validation.json)
- [audit/metrics.json](audit/metrics.json)

## Semantic Coverage

- [semantic-capabilities.json](semantic-capabilities.json)
- [semantic-coverage.json](semantic-coverage.json)

## Deterministic Gates

- [acceptance-metrics.json](acceptance-metrics.json)
- [ifc-verification.json](ifc-verification.json)
- [geometry-feedback.json](geometry-feedback.json)
- [secret-scan.json](secret-scan.json)

```json
{
  "case_id": "7dd0874b945df268",
  "compile_reopen_success": true,
  "geometry_success": true,
  "ifc_path": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\two-storey-human-review-20260909\\admission\\scale-public-04\\runs\\7dd0874b945df268\\output.ifc",
  "output_dir": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\two-storey-human-review-20260909\\admission\\scale-public-04\\runs\\7dd0874b945df268",
  "report_path": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\two-storey-human-review-20260909\\admission\\scale-public-04\\runs\\7dd0874b945df268\\report.md",
  "secret_finding_count": 0,
  "stage": "final-acceptance",
  "valid": true
}
```

## Revision and ChangeSet History

```json
{
  "issues": [],
  "reason": "No candidate revision sidecar exists for this legacy run.",
  "status": "not_applicable"
}
```


## Final Artifacts

- [output.ifc](output.ifc)
- [candidate.json](candidate.json)
- [report.md](report.md)

## Session Export

- [runs/7dd0874b945df268/session-export.json](runs/7dd0874b945df268/session-export.json)

## Session DB Evidence

### Events

```json
[
  {
    "created_at": "2026-09-09T03:32:37+00:00",
    "event_index": 0,
    "event_type": "generator_completed",
    "payload": {
      "case_id": "7dd0874b945df268",
      "classification": "formal",
      "contract_valid": true,
      "evidence_class": "unit_test_fixture",
      "output_dir": "dataset/processed/ifc-presentation-validation/two-storey-human-review-20260909/admission/scale-public-04/runs/7dd0874b945df268/generator",
      "response_id": "response-package-1",
      "stage": "generate",
      "status": "formal",
      "strict_output_contract_valid": true,
      "valid": true
    }
  },
  {
    "created_at": "2026-09-09T03:32:37+00:00",
    "event_index": 1,
    "event_type": "semantic_coverage_completed",
    "payload": {
      "blocking_fact_count": 0,
      "capability_profile_hash": "sha256:1a9b5d81e65c07e3b578782744596bd9a56eb1ecf9702c94dbde5fd91681bbb5",
      "capability_profile_id": "text2ifc/semantic-capabilities/ifc2x3-bim-json-2.0/1.0",
      "case_id": "7dd0874b945df268",
      "coverage": {
        "blocking_facts": [],
        "candidate_entity_count": 48,
        "capability_profile_hash": "sha256:1a9b5d81e65c07e3b578782744596bd9a56eb1ecf9702c94dbde5fd91681bbb5",
        "capability_profile_id": "text2ifc/semantic-capabilities/ifc2x3-bim-json-2.0/1.0",
        "case_id": "7dd0874b945df268",
        "custom_property_policy": {
          "counts_as_semantic_support": false,
          "state": "preserved_text_only"
        },
        "facts": [
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/depth_y_mm",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 6000
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/slab_thickness_mm",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 150
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/storey_height_mm",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 3000
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/wall_thickness_mm",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 200
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/width_x_mm",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 8000
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/doors",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": [
              {
                "height_mm": 2100,
                "host_wall": "storey-1-south",
                "id": "door-storey-1",
                "storey": "storey-1",
                "width_mm": 900
              },
              {
                "height_mm": 2100,
                "host_wall": "storey-2-south",
                "id": "door-storey-2",
                "storey": "storey-2",
                "width_mm": 900
              },
              {
                "height_mm": 2100,
                "host_wall": "storey-3-south",
                "id": "door-storey-3",
                "storey": "storey-3",
                "width_mm": 900
              }
            ]
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/roof/elevation_mm",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 9300
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/roof/id",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": "roof-main"
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/roof/thickness_mm",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 150
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/slabs",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": [
              {
                "elevation_mm": 0,
                "id": "slab-ground",
                "storey": "storey-1",
                "thickness_mm": 150
              },
              {
                "elevation_mm": 3150,
                "id": "slab-storey-2",
                "storey": "storey-2",
                "thickness_mm": 150
              },
              {
                "elevation_mm": 6300,
                "id": "slab-storey-3",
                "storey": "storey-3",
                "thickness_mm": 150
              }
            ]
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/spaces",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": [
              {
                "dimensions_mm": [
                  6000,
                  6000
                ],
                "height_mm": 3000,
                "id": "space-storey-1-office",
                "name": "首层办公室",
                "origin_mm": [
                  0,
                  0,
                  0
                ],
                "storey": "storey-1"
              },
              {
                "dimensions_mm": [
                  2000,
                  6000
                ],
                "height_mm": 3000,
                "id": "space-storey-1-stair",
                "name": "首层楼梯间",
                "origin_mm": [
                  6000,
                  0,
                  0
                ],
                "storey": "storey-1"
              },
              {
                "dimensions_mm": [
                  6000,
                  6000
                ],
                "height_mm": 3000,
                "id": "space-storey-2-office",
                "name": "二层办公室",
                "origin_mm": [
                  0,
                  0,
                  0
                ],
                "storey": "storey-2"
              },
              {
                "dimensions_mm": [
                  2000,
                  6000
                ],
                "height_mm": 3000,
                "id": "space-storey-2-stair",
                "name": "二层楼梯间",
                "origin_mm": [
                  6000,
                  0,
                  0
                ],
                "storey": "storey-2"
              },
              {
                "dimensions_mm": [
                  6000,
                  6000
                ],
                "height_mm": 3000,
                "id": "space-storey-3-office",
                "name": "三层办公室",
                "origin_mm": [
                  0,
                  0,
                  0
                ],
                "storey": "storey-3"
              },
              {
                "dimensions_mm": [
                  2000,
                  6000
                ],
                "height_mm": 3000,
                "id": "space-storey-3-stair",
                "name": "三层楼梯间",
                "origin_mm": [
                  6000,
                  0,
                  0
                ],
                "storey": "storey-3"
              }
            ]
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/stairs",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": [
              {
                "end_elevation_mm": 3150,
                "id": "stair-1-2",
                "start_elevation_mm": 150,
                "storey": "storey-1",
                "width_mm": 1000
              },
              {
                "end_elevation_mm": 6300,
                "id": "stair-2-3",
                "start_elevation_mm": 3300,
                "storey": "storey-2",
                "width_mm": 1000
              }
            ]
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/storeys",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": [
              {
                "elevation_mm": 0,
                "id": "storey-1",
                "name": "首层"
              },
              {
                "elevation_mm": 3150,
                "id": "storey-2",
                "name": "二层"
              },
              {
                "elevation_mm": 6300,
                "id": "storey-3",
                "name": "三层"
              }
            ]
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/windows",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": [
              {
                "height_mm": 1000,
                "host_wall": "storey-1-north",
                "id": "window-storey-1",
                "sill_height_mm": 900,
                "storey": "storey-1",
                "width_mm": 1200
              },
              {
                "height_mm": 1000,
                "host_wall": "storey-2-north",
                "id": "window-storey-2",
                "sill_height_mm": 900,
                "storey": "storey-2",
                "width_mm": 1200
              },
              {
                "height_mm": 1000,
                "host_wall": "storey-3-north",
                "id": "window-storey-3",
                "sill_height_mm": 900,
                "storey": "storey-3",
                "width_mm": 1200
              }
            ]
          }
        ],
        "schema_version": "text2ifc/semantic-coverage/1.0",
        "valid": true
      },
      "fact_count": 14,
      "stage": "semantic-coverage",
      "valid": true
    }
  },
  {
    "created_at": "2026-09-09T03:32:38+00:00",
    "event_index": 2,
    "event_type": "repair_completed",
    "payload": {
      "case_id": "7dd0874b945df268",
      "evidence_class": "live-derived-no-call",
      "output_dir": "dataset/processed/ifc-presentation-validation/two-storey-human-review-20260909/admission/scale-public-04/runs/7dd0874b945df268/repair",
      "provider_call_count": 0,
      "repair_attempts": [],
      "route": "no_repair_needed",
      "source_generator_response_id": "response-package-1",
      "stage": "repair",
      "valid": true
    }
  },
  {
    "created_at": "2026-09-09T03:32:41+00:00",
    "event_index": 3,
    "event_type": "candidate_gates_completed",
    "payload": {
      "case_id": "7dd0874b945df268",
      "compile_reopen_success": true,
      "deterministic_gates_passed": true,
      "gate_summary": {
        "artifact_hashes": {
          "dynamic-gates.json": "54be3b4fb4784d832246685d27bccfddd404701e1cb7ad1902b3ea33a29a1281",
          "expected-facts.json": "a6ace16e82f96fdaabbfc75b6905a513349c44ca09ddb030425d3991af395088",
          "generator/candidate.json": "98485b6f6c12da889cf003f59d51419a2c935ce05bd730222271971b4d81f25e",
          "generator/validation.json": "6be6595f4f77090199203073905e3755e4015ff1a83b3412d64571cd872b4c41",
          "geometry-feedback.json": "37de66b3c369d266ff88c3d4531da45dd8b0fd18a28fb49b4af1b53f813363ca",
          "ifc-verification.json": "adbcfd111c7806c2b838314af583e9a59cd90dea79eda23cfbed9d7ca1138f24",
          "repair/route.json": "de3b5816a1c81654c2676959899706ab00dc696fab1ef461ad563d59e1fd7db3",
          "request-semantics.json": "114facfc0987c9bfd9363cfa4f21600909962838257ca88c35e11e8fba0d02a9",
          "semantic-coverage.json": "077ebc53c68d91d984efb8f5e413f640dbc6f285634ab823aa12726187734bdf",
          "semantic-verification.json": "4aafeaaacf14e0f93801e8e05d57f4951c3e6bec67c3e0d3f47f37d9bf5a3d2e"
        },
        "candidate_hash": "98485b6f6c12da889cf003f59d51419a2c935ce05bd730222271971b4d81f25e",
        "candidate_path": "generator/candidate.json",
        "case_id": "7dd0874b945df268",
        "evidence": {
          "compile_reopen": {
            "ifc_issues": [],
            "input_issues": [],
            "output_path": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\two-storey-human-review-20260909\\admission\\scale-public-04\\runs\\7dd0874b945df268\\output.ifc",
            "success": true
          },
          "geometry": {
            "expectation_source": "candidate",
            "issues": [],
            "metrics": {
              "case_id": "7dd0874b945df268",
              "floor_openings": {},
              "products": {},
              "roof": {},
              "slabs": {},
              "spaces": {},
              "stairs": {},
              "wall_set_convention": "primary",
              "walls": {}
            },
            "success": true
          },
          "repair_history": {
            "case_id": "7dd0874b945df268",
            "fact_delta": null,
            "geometry_issue_count": 0,
            "provider_call_count": 0,
            "repair_attempts": [],
            "repair_diagnostics": [],
            "repair_source_artifact": "candidate.json",
            "route": "no_repair_needed",
            "schema_version": "text2ifc/repair-route/1.0",
            "source_document_kind": "candidate",
            "source_document_path": "candidate.json",
            "source_generator_dir": "dataset/processed/ifc-presentation-validation/two-storey-human-review-20260909/admission/scale-public-04/runs/7dd0874b945df268/generator",
            "source_generator_response_id": "response-package-1",
            "valid": true,
            "validation_issue_count": 0
          },
          "request_semantics": {
            "basis": "request expectations independently compared with reopened IFC before atomic publication",
            "expectations": [],
            "issues": [],
            "schema_version": "text2ifc/request-semantic-verification/1.0",
            "valid": true
          },
          "schema_validation": {
            "issue_count": 0,
            "issues": [],
            "valid": true
          },
          "semantic_coverage": {
            "blocking_facts": [],
            "candidate_entity_count": 48,
            "capability_profile_hash": "sha256:1a9b5d81e65c07e3b578782744596bd9a56eb1ecf9702c94dbde5fd91681bbb5",
            "capability_profile_id": "text2ifc/semantic-capabilities/ifc2x3-bim-json-2.0/1.0",
            "case_id": "7dd0874b945df268",
            "custom_property_policy": {
              "counts_as_semantic_support": false,
              "state": "preserved_text_only"
            },
            "facts": [
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/depth_y_mm",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 6000
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/slab_thickness_mm",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 150
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/storey_height_mm",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 3000
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/wall_thickness_mm",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 200
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/width_x_mm",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 8000
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/doors",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": [
                  {
                    "height_mm": 2100,
                    "host_wall": "storey-1-south",
                    "id": "door-storey-1",
                    "storey": "storey-1",
                    "width_mm": 900
                  },
                  {
                    "height_mm": 2100,
                    "host_wall": "storey-2-south",
                    "id": "door-storey-2",
                    "storey": "storey-2",
                    "width_mm": 900
                  },
                  {
                    "height_mm": 2100,
                    "host_wall": "storey-3-south",
                    "id": "door-storey-3",
                    "storey": "storey-3",
                    "width_mm": 900
                  }
                ]
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/roof/elevation_mm",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 9300
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/roof/id",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": "roof-main"
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/roof/thickness_mm",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 150
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/slabs",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": [
                  {
                    "elevation_mm": 0,
                    "id": "slab-ground",
                    "storey": "storey-1",
                    "thickness_mm": 150
                  },
                  {
                    "elevation_mm": 3150,
                    "id": "slab-storey-2",
                    "storey": "storey-2",
                    "thickness_mm": 150
                  },
                  {
                    "elevation_mm": 6300,
                    "id": "slab-storey-3",
                    "storey": "storey-3",
                    "thickness_mm": 150
                  }
                ]
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/spaces",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": [
                  {
                    "dimensions_mm": [
                      6000,
                      6000
                    ],
                    "height_mm": 3000,
                    "id": "space-storey-1-office",
                    "name": "首层办公室",
                    "origin_mm": [
                      0,
                      0,
                      0
                    ],
                    "storey": "storey-1"
                  },
                  {
                    "dimensions_mm": [
                      2000,
                      6000
                    ],
                    "height_mm": 3000,
                    "id": "space-storey-1-stair",
                    "name": "首层楼梯间",
                    "origin_mm": [
                      6000,
                      0,
                      0
                    ],
                    "storey": "storey-1"
                  },
                  {
                    "dimensions_mm": [
                      6000,
                      6000
                    ],
                    "height_mm": 3000,
                    "id": "space-storey-2-office",
                    "name": "二层办公室",
                    "origin_mm": [
                      0,
                      0,
                      0
                    ],
                    "storey": "storey-2"
                  },
                  {
                    "dimensions_mm": [
                      2000,
                      6000
                    ],
                    "height_mm": 3000,
                    "id": "space-storey-2-stair",
                    "name": "二层楼梯间",
                    "origin_mm": [
                      6000,
                      0,
                      0
                    ],
                    "storey": "storey-2"
                  },
                  {
                    "dimensions_mm": [
                      6000,
                      6000
                    ],
                    "height_mm": 3000,
                    "id": "space-storey-3-office",
                    "name": "三层办公室",
                    "origin_mm": [
                      0,
                      0,
                      0
                    ],
                    "storey": "storey-3"
                  },
                  {
                    "dimensions_mm": [
                      2000,
                      6000
                    ],
                    "height_mm": 3000,
                    "id": "space-storey-3-stair",
                    "name": "三层楼梯间",
                    "origin_mm": [
                      6000,
                      0,
                      0
                    ],
                    "storey": "storey-3"
                  }
                ]
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/stairs",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": [
                  {
                    "end_elevation_mm": 3150,
                    "id": "stair-1-2",
                    "start_elevation_mm": 150,
                    "storey": "storey-1",
                    "width_mm": 1000
                  },
                  {
                    "end_elevation_mm": 6300,
                    "id": "stair-2-3",
                    "start_elevation_mm": 3300,
                    "storey": "storey-2",
                    "width_mm": 1000
                  }
                ]
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/storeys",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": [
                  {
                    "elevation_mm": 0,
                    "id": "storey-1",
                    "name": "首层"
                  },
                  {
                    "elevation_mm": 3150,
                    "id": "storey-2",
                    "name": "二层"
                  },
                  {
                    "elevation_mm": 6300,
                    "id": "storey-3",
                    "name": "三层"
                  }
                ]
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/windows",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": [
                  {
                    "height_mm": 1000,
                    "host_wall": "storey-1-north",
                    "id": "window-storey-1",
                    "sill_height_mm": 900,
                    "storey": "storey-1",
                    "width_mm": 1200
                  },
                  {
                    "height_mm": 1000,
                    "host_wall": "storey-2-north",
                    "id": "window-storey-2",
                    "sill_height_mm": 900,
                    "storey": "storey-2",
                    "width_mm": 1200
                  },
                  {
                    "height_mm": 1000,
                    "host_wall": "storey-3-north",
                    "id": "window-storey-3",
                    "sill_height_mm": 900,
                    "storey": "storey-3",
                    "width_mm": 1200
                  }
                ]
              }
            ],
            "schema_version": "text2ifc/semantic-coverage/1.0",
            "valid": true
          }
        },
        "expected_facts_hash": "a6ace16e82f96fdaabbfc75b6905a513349c44ca09ddb030425d3991af395088",
        "expected_facts_path": "expected-facts.json",
        "gates": [
          {
            "applicability": "applicable",
            "basis": "generator validation sidecar",
            "issue_codes": [],
            "issue_count": 0,
            "issues": [],
            "name": "bim_json_validation",
            "source_paths": [
              "generator/validation.json"
            ],
            "status": "passed"
          },
          {
            "applicability": "applicable",
            "basis": "expected-facts total_counts compared with candidate entities",
            "issue_codes": [],
            "issue_count": 0,
            "issues": [],
            "name": "dynamic_entity_completeness",
            "source_paths": [
              "expected-facts.json",
              "generator/candidate.json"
            ],
            "status": "passed"
          },
          {
            "applicability": "applicable",
            "basis": "expected storey and host-wall facts compared with candidate placement/void-fill graph",
            "entity_matches": [
              {
                "candidate_id": "space-storey-1-office",
                "collection": "spaces",
                "expected_id": "space-storey-1-office",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "space-storey-1-stair",
                "collection": "spaces",
                "expected_id": "space-storey-1-stair",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "space-storey-2-office",
                "collection": "spaces",
                "expected_id": "space-storey-2-office",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "space-storey-2-stair",
                "collection": "spaces",
                "expected_id": "space-storey-2-stair",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "space-storey-3-office",
                "collection": "spaces",
                "expected_id": "space-storey-3-office",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "space-storey-3-stair",
                "collection": "spaces",
                "expected_id": "space-storey-3-stair",
                "match_basis": "exact_brief_id"
              }
            ],
            "issue_codes": [],
            "issue_count": 0,
            "issues": [],
            "name": "dynamic_storey_containment",
            "source_paths": [
              "expected-facts.json",
              "generator/candidate.json"
            ],
            "status": "passed"
          },
          {
            "applicability": "applicable",
            "basis": "explicit component storey labels compared with placement-derived ownership",
            "issue_codes": [],
            "issue_count": 0,
            "issues": [],
            "name": "dynamic_storey_name_consistency",
            "source_paths": [
              "expected-facts.json",
              "generator/candidate.json"
            ],
            "status": "passed"
          },
          {
            "applicability": "applicable",
            "basis": "expected opening/fill obligations compared with IfcRelVoidsElement and IfcRelFillsElement",
            "issue_codes": [],
            "issue_count": 0,
            "issues": [],
            "name": "dynamic_opening_fill",
            "source_paths": [
              "expected-facts.json",
              "generator/candidate.json"
            ],
            "status": "passed"
          },
          {
            "applicability": "applicable",
            "basis": "semantic coverage sidecar",
            "issue_codes": [],
            "issue_count": 0,
            "issues": [],
            "name": "semantic_coverage",
            "source_paths": [
              "semantic-coverage.json"
            ],
            "status": "passed"
          },
          {
            "applicability": "applicable",
            "basis": "independent reopened IFC/request comparison",
            "issue_codes": [],
            "issue_count": 0,
            "issues": [],
            "name": "request_semantics",
            "source_paths": [
              "semantic-verification.json"
            ],
            "status": "passed"
          },
          {
            "applicability": "applicable",
            "basis": "IFC compile/reopen sidecar",
            "issue_codes": [],
            "issue_count": 0,
            "issues": [],
            "name": "ifc_compile_reopen",
            "source_paths": [
              "ifc-verification.json"
            ],
            "status": "passed"
          },
          {
            "applicability": "applicable",
            "basis": "geometry feedback sidecar",
            "issue_codes": [],
            "issue_count": 0,
            "issues": [],
            "name": "geometry",
            "source_paths": [
              "geometry-feedback.json"
            ],
            "status": "passed"
          },
          {
            "applicability": "applicable",
            "basis": "repair route is no_repair_needed",
            "issue_codes": [],
            "issue_count": 0,
            "issues": [],
            "name": "repair_route",
            "source_paths": [
              "repair/route.json"
            ],
            "status": "passed"
          }
        ],
        "overall_status": "passed",
        "schema_version": "text2ifc/gate-summary/1.0"
      },
      "geometry_feedback": {
        "expectation_source": "candidate",
        "issues": [],
        "metrics": {
          "case_id": "7dd0874b945df268",
          "floor_openings": {},
          "products": {},
          "roof": {},
          "slabs": {},
          "spaces": {},
          "stairs": {},
          "wall_set_convention": "primary",
          "walls": {}
        },
        "success": true
      },
      "geometry_success": true,
      "ifc_path": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\two-storey-human-review-20260909\\admission\\scale-public-04\\runs\\7dd0874b945df268\\output.ifc",
      "ifc_verification": {
        "ifc_issues": [],
        "input_issues": [],
        "output_path": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\two-storey-human-review-20260909\\admission\\scale-public-04\\runs\\7dd0874b945df268\\output.ifc",
        "success": true
      },
      "output_dir": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\two-storey-human-review-20260909\\admission\\scale-public-04\\runs\\7dd0874b945df268",
      "semantic_geometry_expectation": null,
      "semantic_verification": {
        "basis": "request expectations independently compared with reopened IFC before atomic publication",
        "expectations": [],
        "issues": [],
        "schema_version": "text2ifc/request-semantic-verification/1.0",
        "valid": true
      },
      "stage": "candidate-gates",
      "valid": true
    }
  },
  {
    "created_at": "2026-09-09T03:32:42+00:00",
    "event_index": 4,
    "event_type": "audit_completed",
    "payload": {
      "case_id": "7dd0874b945df268",
      "evidence_class": "unit_test_fixture",
      "output_dir": "dataset/processed/ifc-presentation-validation/two-storey-human-review-20260909/admission/scale-public-04/runs/7dd0874b945df268",
      "report_path": "dataset/processed/ifc-presentation-validation/two-storey-human-review-20260909/admission/scale-public-04/runs/7dd0874b945df268/report.md",
      "response_id": "response-package-2",
      "route_decision": "accept",
      "route_owner_stage": "none",
      "stage": "audit-report",
      "status": "accepted",
      "valid": true
    }
  },
  {
    "created_at": "2026-09-09T03:32:46+00:00",
    "event_index": 5,
    "event_type": "final_acceptance_completed",
    "payload": {
      "case_id": "7dd0874b945df268",
      "compile_reopen_success": true,
      "geometry_success": true,
      "ifc_path": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\two-storey-human-review-20260909\\admission\\scale-public-04\\runs\\7dd0874b945df268\\output.ifc",
      "output_dir": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\two-storey-human-review-20260909\\admission\\scale-public-04\\runs\\7dd0874b945df268",
      "report_path": "E:\\code for project\\bimnet\\dataset\\processed\\ifc-presentation-validation\\two-storey-human-review-20260909\\admission\\scale-public-04\\runs\\7dd0874b945df268\\report.md",
      "secret_finding_count": 0,
      "stage": "final-acceptance",
      "valid": true
    }
  }
]
```

### Artifact Index

```json
[
  {
    "created_at": "2026-09-09T03:32:37+00:00",
    "kind": "expected_facts",
    "path": "runs/7dd0874b945df268/expected-facts.json"
  },
  {
    "created_at": "2026-09-09T03:32:37+00:00",
    "kind": "candidate",
    "path": "runs/7dd0874b945df268/candidate.json"
  },
  {
    "created_at": "2026-09-09T03:32:37+00:00",
    "kind": "semantic_capabilities",
    "path": "runs/7dd0874b945df268/semantic-capabilities.json"
  },
  {
    "created_at": "2026-09-09T03:32:37+00:00",
    "kind": "semantic_coverage",
    "path": "runs/7dd0874b945df268/semantic-coverage.json"
  },
  {
    "created_at": "2026-09-09T03:32:46+00:00",
    "kind": "issues",
    "path": "runs/7dd0874b945df268/issues.json"
  },
  {
    "created_at": "2026-09-09T03:32:46+00:00",
    "kind": "route_decision",
    "path": "runs/7dd0874b945df268/route-decision.json"
  },
  {
    "created_at": "2026-09-09T03:32:46+00:00",
    "kind": "feedback_rounds",
    "path": "runs/7dd0874b945df268/feedback-rounds.json"
  },
  {
    "created_at": "2026-09-09T03:32:46+00:00",
    "kind": "ifc",
    "path": "runs/7dd0874b945df268/output.ifc"
  },
  {
    "created_at": "2026-09-09T03:32:46+00:00",
    "kind": "report",
    "path": "runs/7dd0874b945df268/report.md"
  },
  {
    "created_at": "2026-09-09T03:32:46+00:00",
    "kind": "session_export",
    "path": "runs/7dd0874b945df268/session-export.json"
  }
]
```
