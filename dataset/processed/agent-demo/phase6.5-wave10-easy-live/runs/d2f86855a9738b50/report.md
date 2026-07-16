# Phase 6.2-fix Real REPL Acceptance

## REPL Interaction Evidence

- interaction_mode: `human_repl_live`
- input_source: `terminal`
- session_hash: `d2f86855a9738b50`

```json
[
  {
    "created_at": "2026-07-16T07:57:25+00:00",
    "event_index": 0,
    "event_type": "repl_session_started",
    "payload": {
      "input_source": "terminal",
      "interaction_mode": "human_repl_live",
      "terminal_encoding": {
        "stderr_encoding": "utf-8",
        "stdin_encoding": "utf-8",
        "stdout_encoding": null
      }
    }
  },
  {
    "created_at": "2026-07-16T08:00:15+00:00",
    "event_index": 1,
    "event_type": "generator_completed",
    "payload": {
      "case_id": "d2f86855a9738b50",
      "classification": "formal",
      "contract_valid": true,
      "evidence_class": "provider-backed-staged",
      "output_dir": "dataset\\processed\\agent-demo\\phase6.5-wave10-easy-live\\runs\\d2f86855a9738b50\\generator",
      "response_id": "d042331c-8b80-49c3-859d-ce9306667a8f",
      "stage": "generate",
      "status": "formal",
      "strict_output_contract_valid": true,
      "valid": true
    }
  },
  {
    "created_at": "2026-07-16T08:00:15+00:00",
    "event_index": 2,
    "event_type": "semantic_coverage_completed",
    "payload": {
      "blocking_fact_count": 0,
      "capability_profile_hash": "sha256:1a9b5d81e65c07e3b578782744596bd9a56eb1ecf9702c94dbde5fd91681bbb5",
      "capability_profile_id": "text2ifc/semantic-capabilities/ifc2x3-bim-json-2.0/1.0",
      "case_id": "d2f86855a9738b50",
      "coverage": {
        "blocking_facts": [],
        "candidate_entity_count": 14,
        "capability_profile_hash": "sha256:1a9b5d81e65c07e3b578782744596bd9a56eb1ecf9702c94dbde5fd91681bbb5",
        "capability_profile_id": "text2ifc/semantic-capabilities/ifc2x3-bim-json-2.0/1.0",
        "case_id": "d2f86855a9738b50",
        "custom_property_policy": {
          "counts_as_semantic_support": false,
          "state": "preserved_text_only"
        },
        "facts": [
          {
            "coverage_state": "represented",
            "path": "/known_facts/floor_slabs",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": [
              {
                "id": "floor-slab-1",
                "owning_storey": "storey-1",
                "thickness_mm": 150,
                "top_elevation_mm": 0
              }
            ]
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/storeys",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": [
              {
                "doors": [
                  {
                    "alignment": "host_centerline",
                    "height_mm": 2100,
                    "host_wall": "wall-south",
                    "id": "door-south",
                    "open_direction": "inside",
                    "width_mm": 900
                  }
                ],
                "elevation_mm": 0,
                "id": "storey-1",
                "net_height_mm": 3000,
                "spaces": [
                  {
                    "bounds": {
                      "x": [
                        0,
                        6000
                      ],
                      "y": [
                        0,
                        4000
                      ]
                    },
                    "id": "space-room",
                    "shape": "rectangle"
                  }
                ],
                "walls": {
                  "exterior": [
                    {
                      "height_mm": 3000,
                      "id": "wall-south",
                      "side": "south",
                      "thickness_mm": 200
                    },
                    {
                      "height_mm": 3000,
                      "id": "wall-north",
                      "side": "north",
                      "thickness_mm": 200
                    },
                    {
                      "height_mm": 3000,
                      "id": "wall-west",
                      "side": "west",
                      "thickness_mm": 200
                    },
                    {
                      "height_mm": 3000,
                      "id": "wall-east",
                      "side": "east",
                      "thickness_mm": 200
                    }
                  ],
                  "interior": []
                },
                "windows": [
                  {
                    "alignment": "host_centerline",
                    "height_mm": 1200,
                    "host_wall": "wall-north",
                    "id": "window-north",
                    "sill_height_mm": 900,
                    "width_mm": 1500
                  }
                ]
              }
            ]
          }
        ],
        "schema_version": "text2ifc/semantic-coverage/1.0",
        "valid": true
      },
      "fact_count": 2,
      "stage": "semantic-coverage",
      "valid": true
    }
  },
  {
    "created_at": "2026-07-16T08:00:15+00:00",
    "event_index": 3,
    "event_type": "repair_completed",
    "payload": {
      "case_id": "d2f86855a9738b50",
      "evidence_class": "live-derived-no-call",
      "output_dir": "dataset/processed/agent-demo/phase6.5-wave10-easy-live/runs/d2f86855a9738b50/repair",
      "provider_call_count": 0,
      "repair_attempts": [],
      "route": "no_repair_needed",
      "source_generator_response_id": "d042331c-8b80-49c3-859d-ce9306667a8f",
      "stage": "repair",
      "valid": true
    }
  },
  {
    "created_at": "2026-07-16T08:00:18+00:00",
    "event_index": 4,
    "event_type": "candidate_gates_completed",
    "payload": {
      "case_id": "d2f86855a9738b50",
      "compile_reopen_success": true,
      "deterministic_gates_passed": true,
      "gate_summary": {
        "artifact_hashes": {
          "dynamic-gates.json": "3fb3a31b0b2af57fd31cbaf917b1f05e35b22b19616b38fb6a13011d387a9a8d",
          "expected-facts.json": "6dcfd1caa280cbc5ab0c125125d2b001f23fc7983f6d560a3e1cd8a41c605fe2",
          "generator/candidate.json": "10e6e5de23aa2e7d2401840751b4bdfd230ae15234df7d78aef7afd9966a24ce",
          "generator/validation.json": "6be6595f4f77090199203073905e3755e4015ff1a83b3412d64571cd872b4c41",
          "geometry-feedback.json": "e32a6ad439f4b85c72f3b350af6091371d3fa1c83edbaae34defa8c177cda56e",
          "ifc-verification.json": "dbf5ddd78f247ccb44a4ad6675b5721c23893e57d28b125e1f40d2f2da2896b6",
          "repair/route.json": "07df707a8b4e65e31d777ee7cefc8ca2bd9046a1c5010ff8bb1f4504e1fce644",
          "semantic-coverage.json": "a548ae303fbedb18cc9203661bfffa06dc06a4f87a72591794ae2c9701add15c"
        },
        "candidate_hash": "10e6e5de23aa2e7d2401840751b4bdfd230ae15234df7d78aef7afd9966a24ce",
        "candidate_path": "generator/candidate.json",
        "case_id": "d2f86855a9738b50",
        "evidence": {
          "compile_reopen": {
            "ifc_issues": [],
            "input_issues": [],
            "output_path": "dataset\\processed\\agent-demo\\phase6.5-wave10-easy-live\\runs\\d2f86855a9738b50\\output.ifc",
            "success": true
          },
          "geometry": {
            "expectation_source": "candidate",
            "issues": [],
            "metrics": {
              "case_id": "d2f86855a9738b50",
              "floor_openings": {},
              "roof": {},
              "slabs": {},
              "spaces": {},
              "stairs": {},
              "wall_set_convention": "primary",
              "walls": {
                "wall-east": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      6.000000000000001,
                      6.2
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
                      3.9999999999999996,
                      4.199999999999999
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
                      -0.2,
                      0.0
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
                      -0.2,
                      0.0
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
          },
          "repair_history": {
            "case_id": "d2f86855a9738b50",
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
            "source_generator_dir": "dataset/processed/agent-demo/phase6.5-wave10-easy-live/runs/d2f86855a9738b50/generator",
            "source_generator_response_id": "d042331c-8b80-49c3-859d-ce9306667a8f",
            "valid": true,
            "validation_issue_count": 0
          },
          "schema_validation": {
            "issue_count": 0,
            "issues": [],
            "valid": true
          },
          "semantic_coverage": {
            "blocking_facts": [],
            "candidate_entity_count": 14,
            "capability_profile_hash": "sha256:1a9b5d81e65c07e3b578782744596bd9a56eb1ecf9702c94dbde5fd91681bbb5",
            "capability_profile_id": "text2ifc/semantic-capabilities/ifc2x3-bim-json-2.0/1.0",
            "case_id": "d2f86855a9738b50",
            "custom_property_policy": {
              "counts_as_semantic_support": false,
              "state": "preserved_text_only"
            },
            "facts": [
              {
                "coverage_state": "represented",
                "path": "/known_facts/floor_slabs",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": [
                  {
                    "id": "floor-slab-1",
                    "owning_storey": "storey-1",
                    "thickness_mm": 150,
                    "top_elevation_mm": 0
                  }
                ]
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/storeys",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": [
                  {
                    "doors": [
                      {
                        "alignment": "host_centerline",
                        "height_mm": 2100,
                        "host_wall": "wall-south",
                        "id": "door-south",
                        "open_direction": "inside",
                        "width_mm": 900
                      }
                    ],
                    "elevation_mm": 0,
                    "id": "storey-1",
                    "net_height_mm": 3000,
                    "spaces": [
                      {
                        "bounds": {
                          "x": [
                            0,
                            6000
                          ],
                          "y": [
                            0,
                            4000
                          ]
                        },
                        "id": "space-room",
                        "shape": "rectangle"
                      }
                    ],
                    "walls": {
                      "exterior": [
                        {
                          "height_mm": 3000,
                          "id": "wall-south",
                          "side": "south",
                          "thickness_mm": 200
                        },
                        {
                          "height_mm": 3000,
                          "id": "wall-north",
                          "side": "north",
                          "thickness_mm": 200
                        },
                        {
                          "height_mm": 3000,
                          "id": "wall-west",
                          "side": "west",
                          "thickness_mm": 200
                        },
                        {
                          "height_mm": 3000,
                          "id": "wall-east",
                          "side": "east",
                          "thickness_mm": 200
                        }
                      ],
                      "interior": []
                    },
                    "windows": [
                      {
                        "alignment": "host_centerline",
                        "height_mm": 1200,
                        "host_wall": "wall-north",
                        "id": "window-north",
                        "sill_height_mm": 900,
                        "width_mm": 1500
                      }
                    ]
                  }
                ]
              }
            ],
            "schema_version": "text2ifc/semantic-coverage/1.0",
            "valid": true
          }
        },
        "expected_facts_hash": "6dcfd1caa280cbc5ab0c125125d2b001f23fc7983f6d560a3e1cd8a41c605fe2",
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
                "candidate_id": "door-south",
                "collection": "doors",
                "expected_id": "door-south",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "space-room",
                "collection": "spaces",
                "expected_id": "space-room",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-south",
                "collection": "walls",
                "expected_id": "wall-south",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-north",
                "collection": "walls",
                "expected_id": "wall-north",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-west",
                "collection": "walls",
                "expected_id": "wall-west",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-east",
                "collection": "walls",
                "expected_id": "wall-east",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "window-north",
                "collection": "windows",
                "expected_id": "window-north",
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
            "applicability": "not_applicable",
            "basis": "expected facts contain fewer than two unique explicit storey names",
            "issue_codes": [],
            "issue_count": 0,
            "issues": [],
            "name": "dynamic_storey_name_consistency",
            "source_paths": [
              "expected-facts.json",
              "generator/candidate.json"
            ],
            "status": "skipped"
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
          "case_id": "d2f86855a9738b50",
          "floor_openings": {},
          "roof": {},
          "slabs": {},
          "spaces": {},
          "stairs": {},
          "wall_set_convention": "primary",
          "walls": {
            "wall-east": {
              "axis": "y",
              "bbox": {
                "x": [
                  6.000000000000001,
                  6.2
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
                  3.9999999999999996,
                  4.199999999999999
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
                  -0.2,
                  0.0
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
                  -0.2,
                  0.0
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
      },
      "geometry_success": true,
      "ifc_path": "dataset\\processed\\agent-demo\\phase6.5-wave10-easy-live\\runs\\d2f86855a9738b50\\output.ifc",
      "ifc_verification": {
        "ifc_issues": [],
        "input_issues": [],
        "output_path": "dataset\\processed\\agent-demo\\phase6.5-wave10-easy-live\\runs\\d2f86855a9738b50\\output.ifc",
        "success": true
      },
      "output_dir": "dataset\\processed\\agent-demo\\phase6.5-wave10-easy-live\\runs\\d2f86855a9738b50",
      "semantic_geometry_expectation": null,
      "stage": "candidate-gates",
      "valid": true
    }
  },
  {
    "created_at": "2026-07-16T08:00:37+00:00",
    "event_index": 5,
    "event_type": "audit_completed",
    "payload": {
      "case_id": "d2f86855a9738b50",
      "evidence_class": "live",
      "output_dir": "dataset/processed/agent-demo/phase6.5-wave10-easy-live/runs/d2f86855a9738b50",
      "report_path": "dataset/processed/agent-demo/phase6.5-wave10-easy-live/runs/d2f86855a9738b50/report.md",
      "response_id": "d4b9c09e-2dae-4093-a5f1-ed743de504a3",
      "route_decision": "accept",
      "route_owner_stage": "none",
      "stage": "audit-report",
      "status": "accepted",
      "valid": true
    }
  },
  {
    "created_at": "2026-07-16T08:00:39+00:00",
    "event_index": 6,
    "event_type": "final_acceptance_completed",
    "payload": {
      "case_id": "d2f86855a9738b50",
      "compile_reopen_success": true,
      "geometry_success": true,
      "ifc_path": "dataset\\processed\\agent-demo\\phase6.5-wave10-easy-live\\runs\\d2f86855a9738b50\\output.ifc",
      "output_dir": "dataset\\processed\\agent-demo\\phase6.5-wave10-easy-live\\runs\\d2f86855a9738b50",
      "report_path": "dataset\\processed\\agent-demo\\phase6.5-wave10-easy-live\\runs\\d2f86855a9738b50\\report.md",
      "secret_finding_count": 0,
      "stage": "final-acceptance",
      "valid": true
    }
  }
]
```
# Phase 6.2 Interactive CLI Run Report

Generated from SQLite session records and linked trace artifacts.

## Original Input

```text
## 2.2 Easy：单个矩形房间

创建一个单层矩形房间，房间净尺寸为东西方向 6 米、南北方向 4 米，净高 3 米。

墙厚 200 毫米，地板厚 150 毫米。

在南侧外墙中央设置一樘外门，门宽 0.9 米、高 2.1 米，向室内开启。

在北侧外墙中央设置一扇窗，窗宽 1.5 米、高 1.2 米，窗台距地面 0.9 米。

生成楼层、房间空间、四面墙、地板、门和窗，并确保门窗正确依附在对应墙体中。房间应生成对应的 `IfcSpace`。
```

## Transcript

```json
[
  {
    "created_at": "2026-07-16T07:57:23+00:00",
    "role": "user",
    "text": "## 2.2 Easy：单个矩形房间\n\n创建一个单层矩形房间，房间净尺寸为东西方向 6 米、南北方向 4 米，净高 3 米。\n\n墙厚 200 毫米，地板厚 150 毫米。\n\n在南侧外墙中央设置一樘外门，门宽 0.9 米、高 2.1 米，向室内开启。\n\n在北侧外墙中央设置一扇窗，窗宽 1.5 米、高 1.2 米，窗台距地面 0.9 米。\n\n生成楼层、房间空间、四面墙、地板、门和窗，并确保门窗正确依附在对应墙体中。房间应生成对应的 `IfcSpace`。",
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
  "case_id": "d2f86855a9738b50",
  "compile_reopen_success": true,
  "geometry_success": true,
  "ifc_path": "dataset\\processed\\agent-demo\\phase6.5-wave10-easy-live\\runs\\d2f86855a9738b50\\output.ifc",
  "output_dir": "dataset\\processed\\agent-demo\\phase6.5-wave10-easy-live\\runs\\d2f86855a9738b50",
  "report_path": "dataset\\processed\\agent-demo\\phase6.5-wave10-easy-live\\runs\\d2f86855a9738b50\\report.md",
  "secret_finding_count": 0,
  "stage": "final-acceptance",
  "valid": true
}
```

## Revision and ChangeSet History

```json
{
  "changed_ids": [
    "door-south",
    "floor-slab-1",
    "opening-door-south",
    "opening-window-north",
    "rel-fills-door-south",
    "rel-fills-window-north",
    "rel-voids-door-south",
    "rel-voids-window-north",
    "space-room",
    "wall-east",
    "wall-north",
    "wall-south",
    "wall-west",
    "window-north"
  ],
  "changesets": [
    {
      "path": "generator-staged/package-01-package-storey-1/attempt-02/changeset.json",
      "payload": {
        "base_candidate_hash": "sha256:ebbb45d31d9bc12dac7461354eda814be9582943be4a2e6c486852199057a379",
        "base_revision_id": "revision-00",
        "changeset_id": "changeset-package-storey-1",
        "expected_facts_hash": "sha256:6dcfd1caa280cbc5ab0c125125d2b001f23fc7983f6d560a3e1cd8a41c605fe2",
        "operations": [
          {
            "evidence_refs": [
              "issue-package-storey-1:/expected"
            ],
            "op": "add_entity",
            "operation_id": "add-wall-south",
            "target_id": "wall-south",
            "value": {
              "attributes": {
                "Name": "South wall",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    3000,
                    -100,
                    0
                  ],
                  "ref_direction": [
                    1,
                    0,
                    0
                  ],
                  "relative_to": "storey-1"
                },
                "Representation": {
                  "depth": 3000,
                  "direction": [
                    0,
                    0,
                    1
                  ],
                  "kind": "extruded_profile",
                  "profile": {
                    "kind": "rectangle",
                    "x": 6000,
                    "y": 200
                  }
                }
              },
              "id": "wall-south",
              "ifc_class": "IfcWall",
              "property_sets": {},
              "provenance": {
                "source": "issue-package-storey-1"
              }
            }
          },
          {
            "evidence_refs": [
              "issue-package-storey-1:/expected"
            ],
            "op": "add_entity",
            "operation_id": "add-wall-north",
            "target_id": "wall-north",
            "value": {
              "attributes": {
                "Name": "North wall",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    3000,
                    4100,
                    0
                  ],
                  "ref_direction": [
                    1,
                    0,
                    0
                  ],
                  "relative_to": "storey-1"
                },
                "Representation": {
                  "depth": 3000,
                  "direction": [
                    0,
                    0,
                    1
                  ],
                  "kind": "extruded_profile",
                  "profile": {
                    "kind": "rectangle",
                    "x": 6000,
                    "y": 200
                  }
                }
              },
              "id": "wall-north",
              "ifc_class": "IfcWall",
              "property_sets": {},
              "provenance": {
                "source": "issue-package-storey-1"
              }
            }
          },
          {
            "evidence_refs": [
              "issue-package-storey-1:/expected"
            ],
            "op": "add_entity",
            "operation_id": "add-wall-west",
            "target_id": "wall-west",
            "value": {
              "attributes": {
                "Name": "West wall",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    -100,
                    2000,
                    0
                  ],
                  "ref_direction": [
                    0,
                    1,
                    0
                  ],
                  "relative_to": "storey-1"
                },
                "Representation": {
                  "depth": 3000,
                  "direction": [
                    0,
                    0,
                    1
                  ],
                  "kind": "extruded_profile",
                  "profile": {
                    "kind": "rectangle",
                    "x": 4000,
                    "y": 200
                  }
                }
              },
              "id": "wall-west",
              "ifc_class": "IfcWall",
              "property_sets": {},
              "provenance": {
                "source": "issue-package-storey-1"
              }
            }
          },
          {
            "evidence_refs": [
              "issue-package-storey-1:/expected"
            ],
            "op": "add_entity",
            "operation_id": "add-wall-east",
            "target_id": "wall-east",
            "value": {
              "attributes": {
                "Name": "East wall",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    6100,
                    2000,
                    0
                  ],
                  "ref_direction": [
                    0,
                    1,
                    0
                  ],
                  "relative_to": "storey-1"
                },
                "Representation": {
                  "depth": 3000,
                  "direction": [
                    0,
                    0,
                    1
                  ],
                  "kind": "extruded_profile",
                  "profile": {
                    "kind": "rectangle",
                    "x": 4000,
                    "y": 200
                  }
                }
              },
              "id": "wall-east",
              "ifc_class": "IfcWall",
              "property_sets": {},
              "provenance": {
                "source": "issue-package-storey-1"
              }
            }
          },
          {
            "evidence_refs": [
              "issue-package-storey-1:/expected"
            ],
            "op": "add_entity",
            "operation_id": "add-space-room",
            "target_id": "space-room",
            "value": {
              "attributes": {
                "InteriorOrExteriorSpace": "INTERNAL",
                "Name": "Room",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    3000,
                    2000,
                    0
                  ],
                  "ref_direction": [
                    1,
                    0,
                    0
                  ],
                  "relative_to": "storey-1"
                },
                "Representation": {
                  "depth": 3000,
                  "direction": [
                    0,
                    0,
                    1
                  ],
                  "kind": "extruded_profile",
                  "profile": {
                    "kind": "rectangle",
                    "x": 6000,
                    "y": 4000
                  }
                }
              },
              "id": "space-room",
              "ifc_class": "IfcSpace",
              "property_sets": {},
              "provenance": {
                "source": "issue-package-storey-1"
              }
            }
          },
          {
            "evidence_refs": [
              "issue-package-storey-1:/expected"
            ],
            "op": "add_entity",
            "operation_id": "add-opening-door-south",
            "target_id": "opening-door-south",
            "value": {
              "attributes": {
                "Name": "Door opening",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    0,
                    0,
                    0
                  ],
                  "ref_direction": [
                    1,
                    0,
                    0
                  ],
                  "relative_to": "wall-south"
                },
                "Representation": {
                  "depth": 2100,
                  "direction": [
                    0,
                    0,
                    1
                  ],
                  "kind": "extruded_profile",
                  "profile": {
                    "kind": "rectangle",
                    "x": 900,
                    "y": 200
                  }
                }
              },
              "id": "opening-door-south",
              "ifc_class": "IfcOpeningElement",
              "property_sets": {},
              "provenance": {
                "source": "issue-package-storey-1"
              }
            }
          },
          {
            "evidence_refs": [
              "issue-package-storey-1:/expected"
            ],
            "op": "add_entity",
            "operation_id": "add-door-south",
            "target_id": "door-south",
            "value": {
              "attributes": {
                "Name": "South door",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    0,
                    0,
                    0
                  ],
                  "ref_direction": [
                    1,
                    0,
                    0
                  ],
                  "relative_to": "opening-door-south"
                },
                "OverallHeight": 2100,
                "OverallWidth": 900,
                "Representation": {
                  "depth": 2100,
                  "direction": [
                    0,
                    0,
                    1
                  ],
                  "kind": "extruded_profile",
                  "profile": {
                    "kind": "rectangle",
                    "x": 900,
                    "y": 200
                  }
                }
              },
              "id": "door-south",
              "ifc_class": "IfcDoor",
              "property_sets": {},
              "provenance": {
                "source": "issue-package-storey-1"
              }
            }
          },
          {
            "evidence_refs": [
              "issue-package-storey-1:/expected"
            ],
            "op": "add_entity",
            "operation_id": "add-opening-window-north",
            "target_id": "opening-window-north",
            "value": {
              "attributes": {
                "Name": "Window opening",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    0,
                    0,
                    900
                  ],
                  "ref_direction": [
                    1,
                    0,
                    0
                  ],
                  "relative_to": "wall-north"
                },
                "Representation": {
                  "depth": 1200,
                  "direction": [
                    0,
                    0,
                    1
                  ],
                  "kind": "extruded_profile",
                  "profile": {
                    "kind": "rectangle",
                    "x": 1500,
                    "y": 200
                  }
                }
              },
              "id": "opening-window-north",
              "ifc_class": "IfcOpeningElement",
              "property_sets": {},
              "provenance": {
                "source": "issue-package-storey-1"
              }
            }
          },
          {
            "evidence_refs": [
              "issue-package-storey-1:/expected"
            ],
            "op": "add_entity",
            "operation_id": "add-window-north",
            "target_id": "window-north",
            "value": {
              "attributes": {
                "Name": "North window",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    0,
                    0,
                    0
                  ],
                  "ref_direction": [
                    1,
                    0,
                    0
                  ],
                  "relative_to": "opening-window-north"
                },
                "OverallHeight": 1200,
                "OverallWidth": 1500,
                "Representation": {
                  "depth": 1200,
                  "direction": [
                    0,
                    0,
                    1
                  ],
                  "kind": "extruded_profile",
                  "profile": {
                    "kind": "rectangle",
                    "x": 1500,
                    "y": 200
                  }
                }
              },
              "id": "window-north",
              "ifc_class": "IfcWindow",
              "property_sets": {},
              "provenance": {
                "source": "issue-package-storey-1"
              }
            }
          },
          {
            "evidence_refs": [
              "issue-package-storey-1:/expected"
            ],
            "op": "add_relationship",
            "operation_id": "add-rel-voids-door-south",
            "target_id": "rel-voids-door-south",
            "value": {
              "attributes": {
                "RelatedOpeningElement": "opening-door-south",
                "RelatingBuildingElement": "wall-south"
              },
              "id": "rel-voids-door-south",
              "ifc_class": "IfcRelVoidsElement",
              "provenance": {
                "source": "issue-package-storey-1"
              }
            }
          },
          {
            "evidence_refs": [
              "issue-package-storey-1:/expected"
            ],
            "op": "add_relationship",
            "operation_id": "add-rel-fills-door-south",
            "target_id": "rel-fills-door-south",
            "value": {
              "attributes": {
                "RelatedBuildingElement": "door-south",
                "RelatingOpeningElement": "opening-door-south"
              },
              "id": "rel-fills-door-south",
              "ifc_class": "IfcRelFillsElement",
              "provenance": {
                "source": "issue-package-storey-1"
              }
            }
          },
          {
            "evidence_refs": [
              "issue-package-storey-1:/expected"
            ],
            "op": "add_relationship",
            "operation_id": "add-rel-voids-window-north",
            "target_id": "rel-voids-window-north",
            "value": {
              "attributes": {
                "RelatedOpeningElement": "opening-window-north",
                "RelatingBuildingElement": "wall-north"
              },
              "id": "rel-voids-window-north",
              "ifc_class": "IfcRelVoidsElement",
              "provenance": {
                "source": "issue-package-storey-1"
              }
            }
          },
          {
            "evidence_refs": [
              "issue-package-storey-1:/expected"
            ],
            "op": "add_relationship",
            "operation_id": "add-rel-fills-window-north",
            "target_id": "rel-fills-window-north",
            "value": {
              "attributes": {
                "RelatedBuildingElement": "window-north",
                "RelatingOpeningElement": "opening-window-north"
              },
              "id": "rel-fills-window-north",
              "ifc_class": "IfcRelFillsElement",
              "provenance": {
                "source": "issue-package-storey-1"
              }
            }
          }
        ],
        "schema_version": "text2ifc/bim-json-changeset/1.0",
        "scope_id": "scope-package-1",
        "source_issue_ids": [
          "issue-package-storey-1"
        ]
      }
    },
    {
      "path": "generator-staged/package-01-package-storey-1/changeset.json",
      "payload": {
        "base_candidate_hash": "sha256:ebbb45d31d9bc12dac7461354eda814be9582943be4a2e6c486852199057a379",
        "base_revision_id": "revision-00",
        "changeset_id": "changeset-package-storey-1",
        "expected_facts_hash": "sha256:6dcfd1caa280cbc5ab0c125125d2b001f23fc7983f6d560a3e1cd8a41c605fe2",
        "operations": [
          {
            "evidence_refs": [
              "issue-package-storey-1:/expected"
            ],
            "op": "add_entity",
            "operation_id": "operation-add-wall-south",
            "target_id": "wall-south",
            "value": {
              "attributes": {
                "Name": "South Wall",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    3000,
                    -100,
                    0
                  ],
                  "ref_direction": [
                    1,
                    0,
                    0
                  ],
                  "relative_to": "storey-1"
                },
                "Representation": {
                  "depth": 3000,
                  "direction": [
                    0,
                    0,
                    1
                  ],
                  "kind": "extruded_profile",
                  "profile": {
                    "kind": "rectangle",
                    "x": 6000,
                    "y": 200
                  }
                }
              },
              "id": "wall-south",
              "ifc_class": "IfcWall",
              "property_sets": {},
              "provenance": {
                "source": "issue-package-storey-1"
              }
            }
          },
          {
            "evidence_refs": [
              "issue-package-storey-1:/expected"
            ],
            "op": "add_entity",
            "operation_id": "operation-add-wall-north",
            "target_id": "wall-north",
            "value": {
              "attributes": {
                "Name": "North Wall",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    3000,
                    4100,
                    0
                  ],
                  "ref_direction": [
                    1,
                    0,
                    0
                  ],
                  "relative_to": "storey-1"
                },
                "Representation": {
                  "depth": 3000,
                  "direction": [
                    0,
                    0,
                    1
                  ],
                  "kind": "extruded_profile",
                  "profile": {
                    "kind": "rectangle",
                    "x": 6000,
                    "y": 200
                  }
                }
              },
              "id": "wall-north",
              "ifc_class": "IfcWall",
              "property_sets": {},
              "provenance": {
                "source": "issue-package-storey-1"
              }
            }
          },
          {
            "evidence_refs": [
              "issue-package-storey-1:/expected"
            ],
            "op": "add_entity",
            "operation_id": "operation-add-wall-west",
            "target_id": "wall-west",
            "value": {
              "attributes": {
                "Name": "West Wall",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    -100,
                    2000,
                    0
                  ],
                  "ref_direction": [
                    0,
                    1,
                    0
                  ],
                  "relative_to": "storey-1"
                },
                "Representation": {
                  "depth": 3000,
                  "direction": [
                    0,
                    0,
                    1
                  ],
                  "kind": "extruded_profile",
                  "profile": {
                    "kind": "rectangle",
                    "x": 4000,
                    "y": 200
                  }
                }
              },
              "id": "wall-west",
              "ifc_class": "IfcWall",
              "property_sets": {},
              "provenance": {
                "source": "issue-package-storey-1"
              }
            }
          },
          {
            "evidence_refs": [
              "issue-package-storey-1:/expected"
            ],
            "op": "add_entity",
            "operation_id": "operation-add-wall-east",
            "target_id": "wall-east",
            "value": {
              "attributes": {
                "Name": "East Wall",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    6100,
                    2000,
                    0
                  ],
                  "ref_direction": [
                    0,
                    1,
                    0
                  ],
                  "relative_to": "storey-1"
                },
                "Representation": {
                  "depth": 3000,
                  "direction": [
                    0,
                    0,
                    1
                  ],
                  "kind": "extruded_profile",
                  "profile": {
                    "kind": "rectangle",
                    "x": 4000,
                    "y": 200
                  }
                }
              },
              "id": "wall-east",
              "ifc_class": "IfcWall",
              "property_sets": {},
              "provenance": {
                "source": "issue-package-storey-1"
              }
            }
          },
          {
            "evidence_refs": [
              "issue-package-storey-1:/expected"
            ],
            "op": "add_entity",
            "operation_id": "operation-add-space-room",
            "target_id": "space-room",
            "value": {
              "attributes": {
                "InteriorOrExteriorSpace": "INTERNAL",
                "Name": "Room",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    3000,
                    2000,
                    0
                  ],
                  "ref_direction": [
                    1,
                    0,
                    0
                  ],
                  "relative_to": "storey-1"
                },
                "Representation": {
                  "depth": 3000,
                  "direction": [
                    0,
                    0,
                    1
                  ],
                  "kind": "extruded_profile",
                  "profile": {
                    "kind": "rectangle",
                    "x": 6000,
                    "y": 4000
                  }
                }
              },
              "id": "space-room",
              "ifc_class": "IfcSpace",
              "property_sets": {},
              "provenance": {
                "source": "issue-package-storey-1"
              }
            }
          },
          {
            "evidence_refs": [
              "issue-package-storey-1:/expected"
            ],
            "op": "add_entity",
            "operation_id": "operation-add-door-south",
            "target_id": "door-south",
            "value": {
              "attributes": {
                "Name": "South Door",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    0,
                    0,
                    0
                  ],
                  "ref_direction": [
                    1,
                    0,
                    0
                  ],
                  "relative_to": "opening-door-south"
                },
                "OverallHeight": 2100,
                "OverallWidth": 900
              },
              "id": "door-south",
              "ifc_class": "IfcDoor",
              "property_sets": {},
              "provenance": {
                "source": "issue-package-storey-1"
              }
            }
          },
          {
            "evidence_refs": [
              "issue-package-storey-1:/expected"
            ],
            "op": "add_entity",
            "operation_id": "operation-add-opening-door-south",
            "target_id": "opening-door-south",
            "value": {
              "attributes": {
                "Name": "Opening for South Door",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    0,
                    0,
                    0
                  ],
                  "ref_direction": [
                    1,
                    0,
                    0
                  ],
                  "relative_to": "wall-south"
                },
                "Representation": {
                  "depth": 2100,
                  "direction": [
                    0,
                    0,
                    1
                  ],
                  "kind": "extruded_profile",
                  "profile": {
                    "kind": "rectangle",
                    "x": 900,
                    "y": 200
                  }
                }
              },
              "id": "opening-door-south",
              "ifc_class": "IfcOpeningElement",
              "property_sets": {},
              "provenance": {
                "source": "issue-package-storey-1"
              }
            }
          },
          {
            "evidence_refs": [
              "issue-package-storey-1:/expected"
            ],
            "op": "add_entity",
            "operation_id": "operation-add-window-north",
            "target_id": "window-north",
            "value": {
              "attributes": {
                "Name": "North Window",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    0,
                    0,
                    0
                  ],
                  "ref_direction": [
                    1,
                    0,
                    0
                  ],
                  "relative_to": "opening-window-north"
                },
                "OverallHeight": 1200,
                "OverallWidth": 1500
              },
              "id": "window-north",
              "ifc_class": "IfcWindow",
              "property_sets": {},
              "provenance": {
                "source": "issue-package-storey-1"
              }
            }
          },
          {
            "evidence_refs": [
              "issue-package-storey-1:/expected"
            ],
            "op": "add_entity",
            "operation_id": "operation-add-opening-window-north",
            "target_id": "opening-window-north",
            "value": {
              "attributes": {
                "Name": "Opening for North Window",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    0,
                    0,
                    900
                  ],
                  "ref_direction": [
                    1,
                    0,
                    0
                  ],
                  "relative_to": "wall-north"
                },
                "Representation": {
                  "depth": 1200,
                  "direction": [
                    0,
                    0,
                    1
                  ],
                  "kind": "extruded_profile",
                  "profile": {
                    "kind": "rectangle",
                    "x": 1500,
                    "y": 200
                  }
                }
              },
              "id": "opening-window-north",
              "ifc_class": "IfcOpeningElement",
              "property_sets": {},
              "provenance": {
                "source": "issue-package-storey-1"
              }
            }
          },
          {
            "evidence_refs": [
              "issue-package-storey-1:/expected"
            ],
            "op": "add_relationship",
            "operation_id": "operation-add-void-door-south",
            "target_id": "rel-voids-door-south",
            "value": {
              "attributes": {
                "RelatedOpeningElement": "opening-door-south",
                "RelatingBuildingElement": "wall-south"
              },
              "id": "rel-voids-door-south",
              "ifc_class": "IfcRelVoidsElement",
              "provenance": {
                "source": "issue-package-storey-1"
              }
            }
          },
          {
            "evidence_refs": [
              "issue-package-storey-1:/expected"
            ],
            "op": "add_relationship",
            "operation_id": "operation-add-fill-door-south",
            "target_id": "rel-fills-door-south",
            "value": {
              "attributes": {
                "RelatedBuildingElement": "door-south",
                "RelatingOpeningElement": "opening-door-south"
              },
              "id": "rel-fills-door-south",
              "ifc_class": "IfcRelFillsElement",
              "provenance": {
                "source": "issue-package-storey-1"
              }
            }
          },
          {
            "evidence_refs": [
              "issue-package-storey-1:/expected"
            ],
            "op": "add_relationship",
            "operation_id": "operation-add-void-window-north",
            "target_id": "rel-voids-window-north",
            "value": {
              "attributes": {
                "RelatedOpeningElement": "opening-window-north",
                "RelatingBuildingElement": "wall-north"
              },
              "id": "rel-voids-window-north",
              "ifc_class": "IfcRelVoidsElement",
              "provenance": {
                "source": "issue-package-storey-1"
              }
            }
          },
          {
            "evidence_refs": [
              "issue-package-storey-1:/expected"
            ],
            "op": "add_relationship",
            "operation_id": "operation-add-fill-window-north",
            "target_id": "rel-fills-window-north",
            "value": {
              "attributes": {
                "RelatedBuildingElement": "window-north",
                "RelatingOpeningElement": "opening-window-north"
              },
              "id": "rel-fills-window-north",
              "ifc_class": "IfcRelFillsElement",
              "provenance": {
                "source": "issue-package-storey-1"
              }
            }
          }
        ],
        "schema_version": "text2ifc/bim-json-changeset/1.0",
        "scope_id": "scope-package-1",
        "source_issue_ids": [
          "issue-package-storey-1"
        ]
      }
    },
    {
      "path": "generator-staged/package-02-package-cross-storey/changeset.json",
      "payload": {
        "base_candidate_hash": "sha256:f5647d469ca56fbb75d62adbe47d0a652dbd9be921cebff7a15639f3d28cc33d",
        "base_revision_id": "revision-01",
        "changeset_id": "changeset-package-cross-storey-floor-slab",
        "expected_facts_hash": "sha256:6dcfd1caa280cbc5ab0c125125d2b001f23fc7983f6d560a3e1cd8a41c605fe2",
        "operations": [
          {
            "evidence_refs": [
              "issue-package-cross-storey:/expected"
            ],
            "op": "add_entity",
            "operation_id": "add-floor-slab-1",
            "target_id": "floor-slab-1",
            "value": {
              "attributes": {
                "Name": "Floor Slab",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    3000,
                    2000,
                    -150
                  ],
                  "ref_direction": [
                    1,
                    0,
                    0
                  ],
                  "relative_to": "storey-1"
                },
                "Representation": {
                  "depth": 150,
                  "direction": [
                    0,
                    0,
                    1
                  ],
                  "kind": "extruded_profile",
                  "profile": {
                    "kind": "rectangle",
                    "x": 6000,
                    "y": 4000
                  }
                }
              },
              "id": "floor-slab-1",
              "ifc_class": "IfcSlab",
              "property_sets": {},
              "provenance": {
                "source": "issue-package-cross-storey"
              }
            }
          }
        ],
        "schema_version": "text2ifc/bim-json-changeset/1.0",
        "scope_id": "scope-package-2",
        "source_issue_ids": [
          "issue-package-cross-storey"
        ]
      }
    }
  ],
  "dependency_ids": [],
  "gate_evidence": {
    "gate_results": {
      "candidate_hash": "sha256:10e6e5de23aa2e7d2401840751b4bdfd230ae15234df7d78aef7afd9966a24ce",
      "deterministic_gates": {
        "case_id": "d2f86855a9738b50",
        "compile_reopen_success": true,
        "deterministic_gates_passed": true,
        "gate_summary": {
          "artifact_hashes": {
            "dynamic-gates.json": "3fb3a31b0b2af57fd31cbaf917b1f05e35b22b19616b38fb6a13011d387a9a8d",
            "expected-facts.json": "6dcfd1caa280cbc5ab0c125125d2b001f23fc7983f6d560a3e1cd8a41c605fe2",
            "generator/candidate.json": "10e6e5de23aa2e7d2401840751b4bdfd230ae15234df7d78aef7afd9966a24ce",
            "generator/validation.json": "6be6595f4f77090199203073905e3755e4015ff1a83b3412d64571cd872b4c41",
            "geometry-feedback.json": "e32a6ad439f4b85c72f3b350af6091371d3fa1c83edbaae34defa8c177cda56e",
            "ifc-verification.json": "dbf5ddd78f247ccb44a4ad6675b5721c23893e57d28b125e1f40d2f2da2896b6",
            "repair/route.json": "07df707a8b4e65e31d777ee7cefc8ca2bd9046a1c5010ff8bb1f4504e1fce644",
            "semantic-coverage.json": "a548ae303fbedb18cc9203661bfffa06dc06a4f87a72591794ae2c9701add15c"
          },
          "candidate_hash": "10e6e5de23aa2e7d2401840751b4bdfd230ae15234df7d78aef7afd9966a24ce",
          "candidate_path": "generator/candidate.json",
          "case_id": "d2f86855a9738b50",
          "evidence": {
            "compile_reopen": {
              "ifc_issues": [],
              "input_issues": [],
              "output_path": "dataset\\processed\\agent-demo\\phase6.5-wave10-easy-live\\runs\\d2f86855a9738b50\\output.ifc",
              "success": true
            },
            "geometry": {
              "expectation_source": "candidate",
              "issues": [],
              "metrics": {
                "case_id": "d2f86855a9738b50",
                "floor_openings": {},
                "roof": {},
                "slabs": {},
                "spaces": {},
                "stairs": {},
                "wall_set_convention": "primary",
                "walls": {
                  "wall-east": {
                    "axis": "y",
                    "bbox": {
                      "x": [
                        6.000000000000001,
                        6.2
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
                        3.9999999999999996,
                        4.199999999999999
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
                        -0.2,
                        0.0
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
                        -0.2,
                        0.0
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
            },
            "repair_history": {
              "case_id": "d2f86855a9738b50",
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
              "source_generator_dir": "dataset/processed/agent-demo/phase6.5-wave10-easy-live/runs/d2f86855a9738b50/generator",
              "source_generator_response_id": "d042331c-8b80-49c3-859d-ce9306667a8f",
              "valid": true,
              "validation_issue_count": 0
            },
            "schema_validation": {
              "issue_count": 0,
              "issues": [],
              "valid": true
            },
            "semantic_coverage": {
              "blocking_facts": [],
              "candidate_entity_count": 14,
              "capability_profile_hash": "sha256:1a9b5d81e65c07e3b578782744596bd9a56eb1ecf9702c94dbde5fd91681bbb5",
              "capability_profile_id": "text2ifc/semantic-capabilities/ifc2x3-bim-json-2.0/1.0",
              "case_id": "d2f86855a9738b50",
              "custom_property_policy": {
                "counts_as_semantic_support": false,
                "state": "preserved_text_only"
              },
              "facts": [
                {
                  "coverage_state": "represented",
                  "path": "/known_facts/floor_slabs",
                  "reason": "Fact is inside the current supported semantic profile.",
                  "value": [
                    {
                      "id": "floor-slab-1",
                      "owning_storey": "storey-1",
                      "thickness_mm": 150,
                      "top_elevation_mm": 0
                    }
                  ]
                },
                {
                  "coverage_state": "represented",
                  "path": "/known_facts/storeys",
                  "reason": "Fact is inside the current supported semantic profile.",
                  "value": [
                    {
                      "doors": [
                        {
                          "alignment": "host_centerline",
                          "height_mm": 2100,
                          "host_wall": "wall-south",
                          "id": "door-south",
                          "open_direction": "inside",
                          "width_mm": 900
                        }
                      ],
                      "elevation_mm": 0,
                      "id": "storey-1",
                      "net_height_mm": 3000,
                      "spaces": [
                        {
                          "bounds": {
                            "x": [
                              0,
                              6000
                            ],
                            "y": [
                              0,
                              4000
                            ]
                          },
                          "id": "space-room",
                          "shape": "rectangle"
                        }
                      ],
                      "walls": {
                        "exterior": [
                          {
                            "height_mm": 3000,
                            "id": "wall-south",
                            "side": "south",
                            "thickness_mm": 200
                          },
                          {
                            "height_mm": 3000,
                            "id": "wall-north",
                            "side": "north",
                            "thickness_mm": 200
                          },
                          {
                            "height_mm": 3000,
                            "id": "wall-west",
                            "side": "west",
                            "thickness_mm": 200
                          },
                          {
                            "height_mm": 3000,
                            "id": "wall-east",
                            "side": "east",
                            "thickness_mm": 200
                          }
                        ],
                        "interior": []
                      },
                      "windows": [
                        {
                          "alignment": "host_centerline",
                          "height_mm": 1200,
                          "host_wall": "wall-north",
                          "id": "window-north",
                          "sill_height_mm": 900,
                          "width_mm": 1500
                        }
                      ]
                    }
                  ]
                }
              ],
              "schema_version": "text2ifc/semantic-coverage/1.0",
              "valid": true
            }
          },
          "expected_facts_hash": "6dcfd1caa280cbc5ab0c125125d2b001f23fc7983f6d560a3e1cd8a41c605fe2",
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
                  "candidate_id": "door-south",
                  "collection": "doors",
                  "expected_id": "door-south",
                  "match_basis": "exact_brief_id"
                },
                {
                  "candidate_id": "space-room",
                  "collection": "spaces",
                  "expected_id": "space-room",
                  "match_basis": "exact_brief_id"
                },
                {
                  "candidate_id": "wall-south",
                  "collection": "walls",
                  "expected_id": "wall-south",
                  "match_basis": "exact_brief_id"
                },
                {
                  "candidate_id": "wall-north",
                  "collection": "walls",
                  "expected_id": "wall-north",
                  "match_basis": "exact_brief_id"
                },
                {
                  "candidate_id": "wall-west",
                  "collection": "walls",
                  "expected_id": "wall-west",
                  "match_basis": "exact_brief_id"
                },
                {
                  "candidate_id": "wall-east",
                  "collection": "walls",
                  "expected_id": "wall-east",
                  "match_basis": "exact_brief_id"
                },
                {
                  "candidate_id": "window-north",
                  "collection": "windows",
                  "expected_id": "window-north",
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
              "applicability": "not_applicable",
              "basis": "expected facts contain fewer than two unique explicit storey names",
              "issue_codes": [],
              "issue_count": 0,
              "issues": [],
              "name": "dynamic_storey_name_consistency",
              "source_paths": [
                "expected-facts.json",
                "generator/candidate.json"
              ],
              "status": "skipped"
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
            "case_id": "d2f86855a9738b50",
            "floor_openings": {},
            "roof": {},
            "slabs": {},
            "spaces": {},
            "stairs": {},
            "wall_set_convention": "primary",
            "walls": {
              "wall-east": {
                "axis": "y",
                "bbox": {
                  "x": [
                    6.000000000000001,
                    6.2
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
                    3.9999999999999996,
                    4.199999999999999
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
                    -0.2,
                    0.0
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
                    -0.2,
                    0.0
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
        },
        "geometry_success": true,
        "ifc_path": "dataset\\processed\\agent-demo\\phase6.5-wave10-easy-live\\runs\\d2f86855a9738b50\\output.ifc",
        "ifc_verification": {
          "ifc_issues": [],
          "input_issues": [],
          "output_path": "dataset\\processed\\agent-demo\\phase6.5-wave10-easy-live\\runs\\d2f86855a9738b50\\output.ifc",
          "success": true
        },
        "output_dir": "dataset\\processed\\agent-demo\\phase6.5-wave10-easy-live\\runs\\d2f86855a9738b50",
        "semantic_geometry_expectation": null,
        "stage": "candidate-gates",
        "valid": true
      },
      "revision_id": "revision-02"
    },
    "issues": [],
    "plan": {
      "changed_ids": [
        "door-south",
        "floor-slab-1",
        "opening-door-south",
        "opening-window-north",
        "rel-fills-door-south",
        "rel-fills-window-north",
        "rel-voids-door-south",
        "rel-voids-window-north",
        "space-room",
        "wall-east",
        "wall-north",
        "wall-south",
        "wall-west",
        "window-north"
      ],
      "dependency_ids": [],
      "global_gates": [
        "bim_json_schema",
        "bim_json_semantics",
        "relationship_integrity",
        "expected_fact_coverage",
        "unrelated_component_preservation",
        "ifc_compile",
        "ifc_reopen",
        "generated_ifc_geometry",
        "audit",
        "secret_scan"
      ],
      "global_gates_mandatory": true,
      "local_gates": [
        "opening_filling_relationships",
        "opening_filling_geometry",
        "wall_host_geometry",
        "room_enclosure",
        "stair_vertical_connection",
        "slab_wall_vertical_alignment",
        "storey_ownership"
      ],
      "mode": "final_acceptance",
      "preservation": {
        "changed_ids": [
          "door-south",
          "floor-slab-1",
          "opening-door-south",
          "opening-window-north",
          "rel-fills-door-south",
          "rel-fills-window-north",
          "rel-voids-door-south",
          "rel-voids-window-north",
          "space-room",
          "wall-east",
          "wall-north",
          "wall-south",
          "wall-west",
          "window-north"
        ],
        "dependency_ids": [],
        "forbidden_drift_ids": [],
        "mode": "initial_staged_composition",
        "schema_version": "text2ifc/component-preservation/1.0",
        "unchanged_ids": [
          "aggregate-building-storeys",
          "aggregate-project-site",
          "aggregate-site-building",
          "building-main",
          "project-main",
          "site-main",
          "storey-1"
        ],
        "unrelated_component_count": 0,
        "unrelated_component_preservation_rate": 1.0
      },
      "revision_binding": {
        "candidate_hash": "sha256:10e6e5de23aa2e7d2401840751b4bdfd230ae15234df7d78aef7afd9966a24ce",
        "expected_facts_hash": "sha256:6dcfd1caa280cbc5ab0c125125d2b001f23fc7983f6d560a3e1cd8a41c605fe2",
        "revision_id": "revision-02"
      },
      "schema_version": "text2ifc/revision-gate-plan/1.0",
      "skipped_local_gates": []
    },
    "schema_version": "text2ifc/revision-gate-evidence/1.0",
    "valid": true
  },
  "geometry_result": {
    "expectation_source": "candidate",
    "issues": [],
    "metrics": {
      "case_id": "d2f86855a9738b50",
      "floor_openings": {},
      "roof": {},
      "slabs": {},
      "spaces": {},
      "stairs": {},
      "wall_set_convention": "primary",
      "walls": {
        "wall-east": {
          "axis": "y",
          "bbox": {
            "x": [
              6.000000000000001,
              6.2
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
              3.9999999999999996,
              4.199999999999999
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
              -0.2,
              0.0
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
              -0.2,
              0.0
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
  },
  "ifc_result": {
    "ifc_issues": [],
    "input_issues": [],
    "output_path": "dataset\\processed\\agent-demo\\phase6.5-wave10-easy-live\\runs\\d2f86855a9738b50\\output.ifc",
    "success": true
  },
  "issues": [],
  "operations": [
    {
      "evidence_refs": [
        "issue-package-storey-1:/expected"
      ],
      "op": "add_entity",
      "operation_id": "add-wall-south",
      "target_id": "wall-south",
      "value": {
        "attributes": {
          "Name": "South wall",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              3000,
              -100,
              0
            ],
            "ref_direction": [
              1,
              0,
              0
            ],
            "relative_to": "storey-1"
          },
          "Representation": {
            "depth": 3000,
            "direction": [
              0,
              0,
              1
            ],
            "kind": "extruded_profile",
            "profile": {
              "kind": "rectangle",
              "x": 6000,
              "y": 200
            }
          }
        },
        "id": "wall-south",
        "ifc_class": "IfcWall",
        "property_sets": {},
        "provenance": {
          "source": "issue-package-storey-1"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-storey-1:/expected"
      ],
      "op": "add_entity",
      "operation_id": "add-wall-north",
      "target_id": "wall-north",
      "value": {
        "attributes": {
          "Name": "North wall",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              3000,
              4100,
              0
            ],
            "ref_direction": [
              1,
              0,
              0
            ],
            "relative_to": "storey-1"
          },
          "Representation": {
            "depth": 3000,
            "direction": [
              0,
              0,
              1
            ],
            "kind": "extruded_profile",
            "profile": {
              "kind": "rectangle",
              "x": 6000,
              "y": 200
            }
          }
        },
        "id": "wall-north",
        "ifc_class": "IfcWall",
        "property_sets": {},
        "provenance": {
          "source": "issue-package-storey-1"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-storey-1:/expected"
      ],
      "op": "add_entity",
      "operation_id": "add-wall-west",
      "target_id": "wall-west",
      "value": {
        "attributes": {
          "Name": "West wall",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              -100,
              2000,
              0
            ],
            "ref_direction": [
              0,
              1,
              0
            ],
            "relative_to": "storey-1"
          },
          "Representation": {
            "depth": 3000,
            "direction": [
              0,
              0,
              1
            ],
            "kind": "extruded_profile",
            "profile": {
              "kind": "rectangle",
              "x": 4000,
              "y": 200
            }
          }
        },
        "id": "wall-west",
        "ifc_class": "IfcWall",
        "property_sets": {},
        "provenance": {
          "source": "issue-package-storey-1"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-storey-1:/expected"
      ],
      "op": "add_entity",
      "operation_id": "add-wall-east",
      "target_id": "wall-east",
      "value": {
        "attributes": {
          "Name": "East wall",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              6100,
              2000,
              0
            ],
            "ref_direction": [
              0,
              1,
              0
            ],
            "relative_to": "storey-1"
          },
          "Representation": {
            "depth": 3000,
            "direction": [
              0,
              0,
              1
            ],
            "kind": "extruded_profile",
            "profile": {
              "kind": "rectangle",
              "x": 4000,
              "y": 200
            }
          }
        },
        "id": "wall-east",
        "ifc_class": "IfcWall",
        "property_sets": {},
        "provenance": {
          "source": "issue-package-storey-1"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-storey-1:/expected"
      ],
      "op": "add_entity",
      "operation_id": "add-space-room",
      "target_id": "space-room",
      "value": {
        "attributes": {
          "InteriorOrExteriorSpace": "INTERNAL",
          "Name": "Room",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              3000,
              2000,
              0
            ],
            "ref_direction": [
              1,
              0,
              0
            ],
            "relative_to": "storey-1"
          },
          "Representation": {
            "depth": 3000,
            "direction": [
              0,
              0,
              1
            ],
            "kind": "extruded_profile",
            "profile": {
              "kind": "rectangle",
              "x": 6000,
              "y": 4000
            }
          }
        },
        "id": "space-room",
        "ifc_class": "IfcSpace",
        "property_sets": {},
        "provenance": {
          "source": "issue-package-storey-1"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-storey-1:/expected"
      ],
      "op": "add_entity",
      "operation_id": "add-opening-door-south",
      "target_id": "opening-door-south",
      "value": {
        "attributes": {
          "Name": "Door opening",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              0,
              0,
              0
            ],
            "ref_direction": [
              1,
              0,
              0
            ],
            "relative_to": "wall-south"
          },
          "Representation": {
            "depth": 2100,
            "direction": [
              0,
              0,
              1
            ],
            "kind": "extruded_profile",
            "profile": {
              "kind": "rectangle",
              "x": 900,
              "y": 200
            }
          }
        },
        "id": "opening-door-south",
        "ifc_class": "IfcOpeningElement",
        "property_sets": {},
        "provenance": {
          "source": "issue-package-storey-1"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-storey-1:/expected"
      ],
      "op": "add_entity",
      "operation_id": "add-door-south",
      "target_id": "door-south",
      "value": {
        "attributes": {
          "Name": "South door",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              0,
              0,
              0
            ],
            "ref_direction": [
              1,
              0,
              0
            ],
            "relative_to": "opening-door-south"
          },
          "OverallHeight": 2100,
          "OverallWidth": 900,
          "Representation": {
            "depth": 2100,
            "direction": [
              0,
              0,
              1
            ],
            "kind": "extruded_profile",
            "profile": {
              "kind": "rectangle",
              "x": 900,
              "y": 200
            }
          }
        },
        "id": "door-south",
        "ifc_class": "IfcDoor",
        "property_sets": {},
        "provenance": {
          "source": "issue-package-storey-1"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-storey-1:/expected"
      ],
      "op": "add_entity",
      "operation_id": "add-opening-window-north",
      "target_id": "opening-window-north",
      "value": {
        "attributes": {
          "Name": "Window opening",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              0,
              0,
              900
            ],
            "ref_direction": [
              1,
              0,
              0
            ],
            "relative_to": "wall-north"
          },
          "Representation": {
            "depth": 1200,
            "direction": [
              0,
              0,
              1
            ],
            "kind": "extruded_profile",
            "profile": {
              "kind": "rectangle",
              "x": 1500,
              "y": 200
            }
          }
        },
        "id": "opening-window-north",
        "ifc_class": "IfcOpeningElement",
        "property_sets": {},
        "provenance": {
          "source": "issue-package-storey-1"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-storey-1:/expected"
      ],
      "op": "add_entity",
      "operation_id": "add-window-north",
      "target_id": "window-north",
      "value": {
        "attributes": {
          "Name": "North window",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              0,
              0,
              0
            ],
            "ref_direction": [
              1,
              0,
              0
            ],
            "relative_to": "opening-window-north"
          },
          "OverallHeight": 1200,
          "OverallWidth": 1500,
          "Representation": {
            "depth": 1200,
            "direction": [
              0,
              0,
              1
            ],
            "kind": "extruded_profile",
            "profile": {
              "kind": "rectangle",
              "x": 1500,
              "y": 200
            }
          }
        },
        "id": "window-north",
        "ifc_class": "IfcWindow",
        "property_sets": {},
        "provenance": {
          "source": "issue-package-storey-1"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-storey-1:/expected"
      ],
      "op": "add_relationship",
      "operation_id": "add-rel-voids-door-south",
      "target_id": "rel-voids-door-south",
      "value": {
        "attributes": {
          "RelatedOpeningElement": "opening-door-south",
          "RelatingBuildingElement": "wall-south"
        },
        "id": "rel-voids-door-south",
        "ifc_class": "IfcRelVoidsElement",
        "provenance": {
          "source": "issue-package-storey-1"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-storey-1:/expected"
      ],
      "op": "add_relationship",
      "operation_id": "add-rel-fills-door-south",
      "target_id": "rel-fills-door-south",
      "value": {
        "attributes": {
          "RelatedBuildingElement": "door-south",
          "RelatingOpeningElement": "opening-door-south"
        },
        "id": "rel-fills-door-south",
        "ifc_class": "IfcRelFillsElement",
        "provenance": {
          "source": "issue-package-storey-1"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-storey-1:/expected"
      ],
      "op": "add_relationship",
      "operation_id": "add-rel-voids-window-north",
      "target_id": "rel-voids-window-north",
      "value": {
        "attributes": {
          "RelatedOpeningElement": "opening-window-north",
          "RelatingBuildingElement": "wall-north"
        },
        "id": "rel-voids-window-north",
        "ifc_class": "IfcRelVoidsElement",
        "provenance": {
          "source": "issue-package-storey-1"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-storey-1:/expected"
      ],
      "op": "add_relationship",
      "operation_id": "add-rel-fills-window-north",
      "target_id": "rel-fills-window-north",
      "value": {
        "attributes": {
          "RelatedBuildingElement": "window-north",
          "RelatingOpeningElement": "opening-window-north"
        },
        "id": "rel-fills-window-north",
        "ifc_class": "IfcRelFillsElement",
        "provenance": {
          "source": "issue-package-storey-1"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-storey-1:/expected"
      ],
      "op": "add_entity",
      "operation_id": "operation-add-wall-south",
      "target_id": "wall-south",
      "value": {
        "attributes": {
          "Name": "South Wall",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              3000,
              -100,
              0
            ],
            "ref_direction": [
              1,
              0,
              0
            ],
            "relative_to": "storey-1"
          },
          "Representation": {
            "depth": 3000,
            "direction": [
              0,
              0,
              1
            ],
            "kind": "extruded_profile",
            "profile": {
              "kind": "rectangle",
              "x": 6000,
              "y": 200
            }
          }
        },
        "id": "wall-south",
        "ifc_class": "IfcWall",
        "property_sets": {},
        "provenance": {
          "source": "issue-package-storey-1"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-storey-1:/expected"
      ],
      "op": "add_entity",
      "operation_id": "operation-add-wall-north",
      "target_id": "wall-north",
      "value": {
        "attributes": {
          "Name": "North Wall",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              3000,
              4100,
              0
            ],
            "ref_direction": [
              1,
              0,
              0
            ],
            "relative_to": "storey-1"
          },
          "Representation": {
            "depth": 3000,
            "direction": [
              0,
              0,
              1
            ],
            "kind": "extruded_profile",
            "profile": {
              "kind": "rectangle",
              "x": 6000,
              "y": 200
            }
          }
        },
        "id": "wall-north",
        "ifc_class": "IfcWall",
        "property_sets": {},
        "provenance": {
          "source": "issue-package-storey-1"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-storey-1:/expected"
      ],
      "op": "add_entity",
      "operation_id": "operation-add-wall-west",
      "target_id": "wall-west",
      "value": {
        "attributes": {
          "Name": "West Wall",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              -100,
              2000,
              0
            ],
            "ref_direction": [
              0,
              1,
              0
            ],
            "relative_to": "storey-1"
          },
          "Representation": {
            "depth": 3000,
            "direction": [
              0,
              0,
              1
            ],
            "kind": "extruded_profile",
            "profile": {
              "kind": "rectangle",
              "x": 4000,
              "y": 200
            }
          }
        },
        "id": "wall-west",
        "ifc_class": "IfcWall",
        "property_sets": {},
        "provenance": {
          "source": "issue-package-storey-1"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-storey-1:/expected"
      ],
      "op": "add_entity",
      "operation_id": "operation-add-wall-east",
      "target_id": "wall-east",
      "value": {
        "attributes": {
          "Name": "East Wall",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              6100,
              2000,
              0
            ],
            "ref_direction": [
              0,
              1,
              0
            ],
            "relative_to": "storey-1"
          },
          "Representation": {
            "depth": 3000,
            "direction": [
              0,
              0,
              1
            ],
            "kind": "extruded_profile",
            "profile": {
              "kind": "rectangle",
              "x": 4000,
              "y": 200
            }
          }
        },
        "id": "wall-east",
        "ifc_class": "IfcWall",
        "property_sets": {},
        "provenance": {
          "source": "issue-package-storey-1"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-storey-1:/expected"
      ],
      "op": "add_entity",
      "operation_id": "operation-add-space-room",
      "target_id": "space-room",
      "value": {
        "attributes": {
          "InteriorOrExteriorSpace": "INTERNAL",
          "Name": "Room",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              3000,
              2000,
              0
            ],
            "ref_direction": [
              1,
              0,
              0
            ],
            "relative_to": "storey-1"
          },
          "Representation": {
            "depth": 3000,
            "direction": [
              0,
              0,
              1
            ],
            "kind": "extruded_profile",
            "profile": {
              "kind": "rectangle",
              "x": 6000,
              "y": 4000
            }
          }
        },
        "id": "space-room",
        "ifc_class": "IfcSpace",
        "property_sets": {},
        "provenance": {
          "source": "issue-package-storey-1"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-storey-1:/expected"
      ],
      "op": "add_entity",
      "operation_id": "operation-add-door-south",
      "target_id": "door-south",
      "value": {
        "attributes": {
          "Name": "South Door",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              0,
              0,
              0
            ],
            "ref_direction": [
              1,
              0,
              0
            ],
            "relative_to": "opening-door-south"
          },
          "OverallHeight": 2100,
          "OverallWidth": 900
        },
        "id": "door-south",
        "ifc_class": "IfcDoor",
        "property_sets": {},
        "provenance": {
          "source": "issue-package-storey-1"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-storey-1:/expected"
      ],
      "op": "add_entity",
      "operation_id": "operation-add-opening-door-south",
      "target_id": "opening-door-south",
      "value": {
        "attributes": {
          "Name": "Opening for South Door",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              0,
              0,
              0
            ],
            "ref_direction": [
              1,
              0,
              0
            ],
            "relative_to": "wall-south"
          },
          "Representation": {
            "depth": 2100,
            "direction": [
              0,
              0,
              1
            ],
            "kind": "extruded_profile",
            "profile": {
              "kind": "rectangle",
              "x": 900,
              "y": 200
            }
          }
        },
        "id": "opening-door-south",
        "ifc_class": "IfcOpeningElement",
        "property_sets": {},
        "provenance": {
          "source": "issue-package-storey-1"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-storey-1:/expected"
      ],
      "op": "add_entity",
      "operation_id": "operation-add-window-north",
      "target_id": "window-north",
      "value": {
        "attributes": {
          "Name": "North Window",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              0,
              0,
              0
            ],
            "ref_direction": [
              1,
              0,
              0
            ],
            "relative_to": "opening-window-north"
          },
          "OverallHeight": 1200,
          "OverallWidth": 1500
        },
        "id": "window-north",
        "ifc_class": "IfcWindow",
        "property_sets": {},
        "provenance": {
          "source": "issue-package-storey-1"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-storey-1:/expected"
      ],
      "op": "add_entity",
      "operation_id": "operation-add-opening-window-north",
      "target_id": "opening-window-north",
      "value": {
        "attributes": {
          "Name": "Opening for North Window",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              0,
              0,
              900
            ],
            "ref_direction": [
              1,
              0,
              0
            ],
            "relative_to": "wall-north"
          },
          "Representation": {
            "depth": 1200,
            "direction": [
              0,
              0,
              1
            ],
            "kind": "extruded_profile",
            "profile": {
              "kind": "rectangle",
              "x": 1500,
              "y": 200
            }
          }
        },
        "id": "opening-window-north",
        "ifc_class": "IfcOpeningElement",
        "property_sets": {},
        "provenance": {
          "source": "issue-package-storey-1"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-storey-1:/expected"
      ],
      "op": "add_relationship",
      "operation_id": "operation-add-void-door-south",
      "target_id": "rel-voids-door-south",
      "value": {
        "attributes": {
          "RelatedOpeningElement": "opening-door-south",
          "RelatingBuildingElement": "wall-south"
        },
        "id": "rel-voids-door-south",
        "ifc_class": "IfcRelVoidsElement",
        "provenance": {
          "source": "issue-package-storey-1"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-storey-1:/expected"
      ],
      "op": "add_relationship",
      "operation_id": "operation-add-fill-door-south",
      "target_id": "rel-fills-door-south",
      "value": {
        "attributes": {
          "RelatedBuildingElement": "door-south",
          "RelatingOpeningElement": "opening-door-south"
        },
        "id": "rel-fills-door-south",
        "ifc_class": "IfcRelFillsElement",
        "provenance": {
          "source": "issue-package-storey-1"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-storey-1:/expected"
      ],
      "op": "add_relationship",
      "operation_id": "operation-add-void-window-north",
      "target_id": "rel-voids-window-north",
      "value": {
        "attributes": {
          "RelatedOpeningElement": "opening-window-north",
          "RelatingBuildingElement": "wall-north"
        },
        "id": "rel-voids-window-north",
        "ifc_class": "IfcRelVoidsElement",
        "provenance": {
          "source": "issue-package-storey-1"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-storey-1:/expected"
      ],
      "op": "add_relationship",
      "operation_id": "operation-add-fill-window-north",
      "target_id": "rel-fills-window-north",
      "value": {
        "attributes": {
          "RelatedBuildingElement": "window-north",
          "RelatingOpeningElement": "opening-window-north"
        },
        "id": "rel-fills-window-north",
        "ifc_class": "IfcRelFillsElement",
        "provenance": {
          "source": "issue-package-storey-1"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-cross-storey:/expected"
      ],
      "op": "add_entity",
      "operation_id": "add-floor-slab-1",
      "target_id": "floor-slab-1",
      "value": {
        "attributes": {
          "Name": "Floor Slab",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              3000,
              2000,
              -150
            ],
            "ref_direction": [
              1,
              0,
              0
            ],
            "relative_to": "storey-1"
          },
          "Representation": {
            "depth": 150,
            "direction": [
              0,
              0,
              1
            ],
            "kind": "extruded_profile",
            "profile": {
              "kind": "rectangle",
              "x": 6000,
              "y": 4000
            }
          }
        },
        "id": "floor-slab-1",
        "ifc_class": "IfcSlab",
        "property_sets": {},
        "provenance": {
          "source": "issue-package-cross-storey"
        }
      }
    }
  ],
  "packages": [
    {
      "artifact_dir": "package-01-package-storey-1/attempt-02",
      "attempt_count": 2,
      "candidate_hash": "sha256:f5647d469ca56fbb75d62adbe47d0a652dbd9be921cebff7a15639f3d28cc33d",
      "classification": "changeset",
      "frozen_component_count": 7,
      "gate_issue_count": 0,
      "package_id": "package-storey-1",
      "pre_apply_status": "partial_not_formal",
      "response_id": "a8bd5abf-24b5-4e32-9bd7-6cade636869d",
      "revision_id": "revision-01",
      "status": "accepted"
    },
    {
      "artifact_dir": "package-02-package-cross-storey",
      "attempt_count": 1,
      "candidate_hash": "sha256:10e6e5de23aa2e7d2401840751b4bdfd230ae15234df7d78aef7afd9966a24ce",
      "classification": "changeset",
      "frozen_component_count": 20,
      "gate_issue_count": 0,
      "package_id": "package-cross-storey",
      "pre_apply_status": "partial_not_formal",
      "response_id": "d042331c-8b80-49c3-859d-ce9306667a8f",
      "revision_id": "revision-02",
      "status": "accepted"
    }
  ],
  "preservation": {
    "changed_ids": [
      "door-south",
      "floor-slab-1",
      "opening-door-south",
      "opening-window-north",
      "rel-fills-door-south",
      "rel-fills-window-north",
      "rel-voids-door-south",
      "rel-voids-window-north",
      "space-room",
      "wall-east",
      "wall-north",
      "wall-south",
      "wall-west",
      "window-north"
    ],
    "dependency_ids": [],
    "forbidden_drift_ids": [],
    "mode": "initial_staged_composition",
    "schema_version": "text2ifc/component-preservation/1.0",
    "unchanged_ids": [
      "aggregate-building-storeys",
      "aggregate-project-site",
      "aggregate-site-building",
      "building-main",
      "project-main",
      "site-main",
      "storey-1"
    ],
    "unrelated_component_count": 0,
    "unrelated_component_preservation_rate": 1.0
  },
  "revision": {
    "artifacts": {
      "candidate": "package-02-package-cross-storey/workspace-after.json"
    },
    "candidate_hash": "sha256:10e6e5de23aa2e7d2401840751b4bdfd230ae15234df7d78aef7afd9966a24ce",
    "component_hashes": {
      "aggregate-building-storeys": "sha256:65533f589d3960284939c18a5b6948d97fecb2094dc0b461825c0f40d57076bf",
      "aggregate-project-site": "sha256:456b0a2ec791c6c20d7efdda199726d8f9df127fd2739962aceb07dacb1f2567",
      "aggregate-site-building": "sha256:9ccdeec022f78745ceb756d48903226706f909c0db1992457f23fffca5da02d4",
      "building-main": "sha256:d2fac45e699944c2dd75aeb376ce156232c45dac25ab318fdc2a4593028a14ad",
      "door-south": "sha256:cd3ef8d3ab43dd411bc7eaa1f63d84753f921d7c6a6dc323e9051fcc3c3a7e89",
      "floor-slab-1": "sha256:5801316838e167ef998084e3daf3986e5052ac06515f0bc8f70a82f693d858bd",
      "opening-door-south": "sha256:1bfccd452b93c0c92834df19e74b288c6f099c8c03a184334a9620f85266cd23",
      "opening-window-north": "sha256:79243a6f57d9a39ed2a8302eeb37d9d51b87aea9dbece4b21101ecf16808e5d8",
      "project-main": "sha256:9b165163ddbb7d9c4ae8832db8391cf20e41cb9bdd4b1d99f6a3e6cb78a071d1",
      "rel-fills-door-south": "sha256:fb8c5dc2b880e30945a0965c911fbf2290bc19907b0114fd2fbbb22012a54b9a",
      "rel-fills-window-north": "sha256:e5cc66d77501af1a246a3a723ff3da27852e0fd42a439c3aef74f32f0b05bff4",
      "rel-voids-door-south": "sha256:5d149f44c626c166d22b16192398235b6c04353293400df95f35bd3d8f22674f",
      "rel-voids-window-north": "sha256:402de016bb29e433bce72b826a29a032540b58281a950868803565277eb09049",
      "site-main": "sha256:d5dfa3ad348be9625c631e2a45e4f77a67a485791c961139b0c18d37314ff3e5",
      "space-room": "sha256:acb65519d35ac4ede89770d8513a26e87d151193166dbe4327f6ba83a412d398",
      "storey-1": "sha256:445101f943e94fa6b4db23df291698553632cc8a788eb9273420c21e3fa05f9d",
      "wall-east": "sha256:510e31a3e231894a85f204176ef374317be1352df4d6443e1bca76fa30f49d0c",
      "wall-north": "sha256:27381bd118cd4443b66f18e3165f93c1326357eef1e93923937d8dd183a65763",
      "wall-south": "sha256:1f362fd1c4addda65f3b878629f27a17e2adc4d74e7cbe0263d9b0381145a4b7",
      "wall-west": "sha256:06b2360f522c082675810746553adf1e33efd1f1c9e6dc2352b0585fb74465ba",
      "window-north": "sha256:460b1bf9cff1cc445728f49442c45ed5737b40087f7e0f4196a9e0aef48a2291"
    },
    "expected_facts_hash": "sha256:6dcfd1caa280cbc5ab0c125125d2b001f23fc7983f6d560a3e1cd8a41c605fe2",
    "parent_revision_id": "revision-01",
    "revision_id": "revision-02",
    "schema_version": "text2ifc/bim-json-revision/1.0",
    "sequence": 2,
    "source_route": "staged_composition"
  },
  "scopes": [],
  "source_issue_ids": [
    "issue-package-cross-storey",
    "issue-package-storey-1"
  ],
  "status": "bound"
}
```

- [candidate-revision.json](candidate-revision.json)
- [component-preservation.json](component-preservation.json)
- [revision-gates.json](revision-gates.json)
- [generator-staged/package-records.json](generator-staged/package-records.json)

## Final Artifacts

- [output.ifc](output.ifc)
- [candidate.json](candidate.json)
- [report.md](report.md)

## Session Export

- [runs/d2f86855a9738b50/session-export.json](runs/d2f86855a9738b50/session-export.json)

## Session DB Evidence

### Events

```json
[
  {
    "created_at": "2026-07-16T07:57:25+00:00",
    "event_index": 0,
    "event_type": "repl_session_started",
    "payload": {
      "input_source": "terminal",
      "interaction_mode": "human_repl_live",
      "terminal_encoding": {
        "stderr_encoding": "utf-8",
        "stdin_encoding": "utf-8",
        "stdout_encoding": null
      }
    }
  },
  {
    "created_at": "2026-07-16T08:00:15+00:00",
    "event_index": 1,
    "event_type": "generator_completed",
    "payload": {
      "case_id": "d2f86855a9738b50",
      "classification": "formal",
      "contract_valid": true,
      "evidence_class": "provider-backed-staged",
      "output_dir": "dataset\\processed\\agent-demo\\phase6.5-wave10-easy-live\\runs\\d2f86855a9738b50\\generator",
      "response_id": "d042331c-8b80-49c3-859d-ce9306667a8f",
      "stage": "generate",
      "status": "formal",
      "strict_output_contract_valid": true,
      "valid": true
    }
  },
  {
    "created_at": "2026-07-16T08:00:15+00:00",
    "event_index": 2,
    "event_type": "semantic_coverage_completed",
    "payload": {
      "blocking_fact_count": 0,
      "capability_profile_hash": "sha256:1a9b5d81e65c07e3b578782744596bd9a56eb1ecf9702c94dbde5fd91681bbb5",
      "capability_profile_id": "text2ifc/semantic-capabilities/ifc2x3-bim-json-2.0/1.0",
      "case_id": "d2f86855a9738b50",
      "coverage": {
        "blocking_facts": [],
        "candidate_entity_count": 14,
        "capability_profile_hash": "sha256:1a9b5d81e65c07e3b578782744596bd9a56eb1ecf9702c94dbde5fd91681bbb5",
        "capability_profile_id": "text2ifc/semantic-capabilities/ifc2x3-bim-json-2.0/1.0",
        "case_id": "d2f86855a9738b50",
        "custom_property_policy": {
          "counts_as_semantic_support": false,
          "state": "preserved_text_only"
        },
        "facts": [
          {
            "coverage_state": "represented",
            "path": "/known_facts/floor_slabs",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": [
              {
                "id": "floor-slab-1",
                "owning_storey": "storey-1",
                "thickness_mm": 150,
                "top_elevation_mm": 0
              }
            ]
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/storeys",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": [
              {
                "doors": [
                  {
                    "alignment": "host_centerline",
                    "height_mm": 2100,
                    "host_wall": "wall-south",
                    "id": "door-south",
                    "open_direction": "inside",
                    "width_mm": 900
                  }
                ],
                "elevation_mm": 0,
                "id": "storey-1",
                "net_height_mm": 3000,
                "spaces": [
                  {
                    "bounds": {
                      "x": [
                        0,
                        6000
                      ],
                      "y": [
                        0,
                        4000
                      ]
                    },
                    "id": "space-room",
                    "shape": "rectangle"
                  }
                ],
                "walls": {
                  "exterior": [
                    {
                      "height_mm": 3000,
                      "id": "wall-south",
                      "side": "south",
                      "thickness_mm": 200
                    },
                    {
                      "height_mm": 3000,
                      "id": "wall-north",
                      "side": "north",
                      "thickness_mm": 200
                    },
                    {
                      "height_mm": 3000,
                      "id": "wall-west",
                      "side": "west",
                      "thickness_mm": 200
                    },
                    {
                      "height_mm": 3000,
                      "id": "wall-east",
                      "side": "east",
                      "thickness_mm": 200
                    }
                  ],
                  "interior": []
                },
                "windows": [
                  {
                    "alignment": "host_centerline",
                    "height_mm": 1200,
                    "host_wall": "wall-north",
                    "id": "window-north",
                    "sill_height_mm": 900,
                    "width_mm": 1500
                  }
                ]
              }
            ]
          }
        ],
        "schema_version": "text2ifc/semantic-coverage/1.0",
        "valid": true
      },
      "fact_count": 2,
      "stage": "semantic-coverage",
      "valid": true
    }
  },
  {
    "created_at": "2026-07-16T08:00:15+00:00",
    "event_index": 3,
    "event_type": "repair_completed",
    "payload": {
      "case_id": "d2f86855a9738b50",
      "evidence_class": "live-derived-no-call",
      "output_dir": "dataset/processed/agent-demo/phase6.5-wave10-easy-live/runs/d2f86855a9738b50/repair",
      "provider_call_count": 0,
      "repair_attempts": [],
      "route": "no_repair_needed",
      "source_generator_response_id": "d042331c-8b80-49c3-859d-ce9306667a8f",
      "stage": "repair",
      "valid": true
    }
  },
  {
    "created_at": "2026-07-16T08:00:18+00:00",
    "event_index": 4,
    "event_type": "candidate_gates_completed",
    "payload": {
      "case_id": "d2f86855a9738b50",
      "compile_reopen_success": true,
      "deterministic_gates_passed": true,
      "gate_summary": {
        "artifact_hashes": {
          "dynamic-gates.json": "3fb3a31b0b2af57fd31cbaf917b1f05e35b22b19616b38fb6a13011d387a9a8d",
          "expected-facts.json": "6dcfd1caa280cbc5ab0c125125d2b001f23fc7983f6d560a3e1cd8a41c605fe2",
          "generator/candidate.json": "10e6e5de23aa2e7d2401840751b4bdfd230ae15234df7d78aef7afd9966a24ce",
          "generator/validation.json": "6be6595f4f77090199203073905e3755e4015ff1a83b3412d64571cd872b4c41",
          "geometry-feedback.json": "e32a6ad439f4b85c72f3b350af6091371d3fa1c83edbaae34defa8c177cda56e",
          "ifc-verification.json": "dbf5ddd78f247ccb44a4ad6675b5721c23893e57d28b125e1f40d2f2da2896b6",
          "repair/route.json": "07df707a8b4e65e31d777ee7cefc8ca2bd9046a1c5010ff8bb1f4504e1fce644",
          "semantic-coverage.json": "a548ae303fbedb18cc9203661bfffa06dc06a4f87a72591794ae2c9701add15c"
        },
        "candidate_hash": "10e6e5de23aa2e7d2401840751b4bdfd230ae15234df7d78aef7afd9966a24ce",
        "candidate_path": "generator/candidate.json",
        "case_id": "d2f86855a9738b50",
        "evidence": {
          "compile_reopen": {
            "ifc_issues": [],
            "input_issues": [],
            "output_path": "dataset\\processed\\agent-demo\\phase6.5-wave10-easy-live\\runs\\d2f86855a9738b50\\output.ifc",
            "success": true
          },
          "geometry": {
            "expectation_source": "candidate",
            "issues": [],
            "metrics": {
              "case_id": "d2f86855a9738b50",
              "floor_openings": {},
              "roof": {},
              "slabs": {},
              "spaces": {},
              "stairs": {},
              "wall_set_convention": "primary",
              "walls": {
                "wall-east": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      6.000000000000001,
                      6.2
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
                      3.9999999999999996,
                      4.199999999999999
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
                      -0.2,
                      0.0
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
                      -0.2,
                      0.0
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
          },
          "repair_history": {
            "case_id": "d2f86855a9738b50",
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
            "source_generator_dir": "dataset/processed/agent-demo/phase6.5-wave10-easy-live/runs/d2f86855a9738b50/generator",
            "source_generator_response_id": "d042331c-8b80-49c3-859d-ce9306667a8f",
            "valid": true,
            "validation_issue_count": 0
          },
          "schema_validation": {
            "issue_count": 0,
            "issues": [],
            "valid": true
          },
          "semantic_coverage": {
            "blocking_facts": [],
            "candidate_entity_count": 14,
            "capability_profile_hash": "sha256:1a9b5d81e65c07e3b578782744596bd9a56eb1ecf9702c94dbde5fd91681bbb5",
            "capability_profile_id": "text2ifc/semantic-capabilities/ifc2x3-bim-json-2.0/1.0",
            "case_id": "d2f86855a9738b50",
            "custom_property_policy": {
              "counts_as_semantic_support": false,
              "state": "preserved_text_only"
            },
            "facts": [
              {
                "coverage_state": "represented",
                "path": "/known_facts/floor_slabs",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": [
                  {
                    "id": "floor-slab-1",
                    "owning_storey": "storey-1",
                    "thickness_mm": 150,
                    "top_elevation_mm": 0
                  }
                ]
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/storeys",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": [
                  {
                    "doors": [
                      {
                        "alignment": "host_centerline",
                        "height_mm": 2100,
                        "host_wall": "wall-south",
                        "id": "door-south",
                        "open_direction": "inside",
                        "width_mm": 900
                      }
                    ],
                    "elevation_mm": 0,
                    "id": "storey-1",
                    "net_height_mm": 3000,
                    "spaces": [
                      {
                        "bounds": {
                          "x": [
                            0,
                            6000
                          ],
                          "y": [
                            0,
                            4000
                          ]
                        },
                        "id": "space-room",
                        "shape": "rectangle"
                      }
                    ],
                    "walls": {
                      "exterior": [
                        {
                          "height_mm": 3000,
                          "id": "wall-south",
                          "side": "south",
                          "thickness_mm": 200
                        },
                        {
                          "height_mm": 3000,
                          "id": "wall-north",
                          "side": "north",
                          "thickness_mm": 200
                        },
                        {
                          "height_mm": 3000,
                          "id": "wall-west",
                          "side": "west",
                          "thickness_mm": 200
                        },
                        {
                          "height_mm": 3000,
                          "id": "wall-east",
                          "side": "east",
                          "thickness_mm": 200
                        }
                      ],
                      "interior": []
                    },
                    "windows": [
                      {
                        "alignment": "host_centerline",
                        "height_mm": 1200,
                        "host_wall": "wall-north",
                        "id": "window-north",
                        "sill_height_mm": 900,
                        "width_mm": 1500
                      }
                    ]
                  }
                ]
              }
            ],
            "schema_version": "text2ifc/semantic-coverage/1.0",
            "valid": true
          }
        },
        "expected_facts_hash": "6dcfd1caa280cbc5ab0c125125d2b001f23fc7983f6d560a3e1cd8a41c605fe2",
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
                "candidate_id": "door-south",
                "collection": "doors",
                "expected_id": "door-south",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "space-room",
                "collection": "spaces",
                "expected_id": "space-room",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-south",
                "collection": "walls",
                "expected_id": "wall-south",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-north",
                "collection": "walls",
                "expected_id": "wall-north",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-west",
                "collection": "walls",
                "expected_id": "wall-west",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-east",
                "collection": "walls",
                "expected_id": "wall-east",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "window-north",
                "collection": "windows",
                "expected_id": "window-north",
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
            "applicability": "not_applicable",
            "basis": "expected facts contain fewer than two unique explicit storey names",
            "issue_codes": [],
            "issue_count": 0,
            "issues": [],
            "name": "dynamic_storey_name_consistency",
            "source_paths": [
              "expected-facts.json",
              "generator/candidate.json"
            ],
            "status": "skipped"
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
          "case_id": "d2f86855a9738b50",
          "floor_openings": {},
          "roof": {},
          "slabs": {},
          "spaces": {},
          "stairs": {},
          "wall_set_convention": "primary",
          "walls": {
            "wall-east": {
              "axis": "y",
              "bbox": {
                "x": [
                  6.000000000000001,
                  6.2
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
                  3.9999999999999996,
                  4.199999999999999
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
                  -0.2,
                  0.0
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
                  -0.2,
                  0.0
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
      },
      "geometry_success": true,
      "ifc_path": "dataset\\processed\\agent-demo\\phase6.5-wave10-easy-live\\runs\\d2f86855a9738b50\\output.ifc",
      "ifc_verification": {
        "ifc_issues": [],
        "input_issues": [],
        "output_path": "dataset\\processed\\agent-demo\\phase6.5-wave10-easy-live\\runs\\d2f86855a9738b50\\output.ifc",
        "success": true
      },
      "output_dir": "dataset\\processed\\agent-demo\\phase6.5-wave10-easy-live\\runs\\d2f86855a9738b50",
      "semantic_geometry_expectation": null,
      "stage": "candidate-gates",
      "valid": true
    }
  },
  {
    "created_at": "2026-07-16T08:00:37+00:00",
    "event_index": 5,
    "event_type": "audit_completed",
    "payload": {
      "case_id": "d2f86855a9738b50",
      "evidence_class": "live",
      "output_dir": "dataset/processed/agent-demo/phase6.5-wave10-easy-live/runs/d2f86855a9738b50",
      "report_path": "dataset/processed/agent-demo/phase6.5-wave10-easy-live/runs/d2f86855a9738b50/report.md",
      "response_id": "d4b9c09e-2dae-4093-a5f1-ed743de504a3",
      "route_decision": "accept",
      "route_owner_stage": "none",
      "stage": "audit-report",
      "status": "accepted",
      "valid": true
    }
  },
  {
    "created_at": "2026-07-16T08:00:39+00:00",
    "event_index": 6,
    "event_type": "final_acceptance_completed",
    "payload": {
      "case_id": "d2f86855a9738b50",
      "compile_reopen_success": true,
      "geometry_success": true,
      "ifc_path": "dataset\\processed\\agent-demo\\phase6.5-wave10-easy-live\\runs\\d2f86855a9738b50\\output.ifc",
      "output_dir": "dataset\\processed\\agent-demo\\phase6.5-wave10-easy-live\\runs\\d2f86855a9738b50",
      "report_path": "dataset\\processed\\agent-demo\\phase6.5-wave10-easy-live\\runs\\d2f86855a9738b50\\report.md",
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
    "created_at": "2026-07-16T07:57:58+00:00",
    "kind": "design_brief",
    "path": "runs/d2f86855a9738b50/design-brief.json"
  },
  {
    "created_at": "2026-07-16T07:57:58+00:00",
    "kind": "session_export",
    "path": "runs/d2f86855a9738b50/session-export.json"
  },
  {
    "created_at": "2026-07-16T07:57:58+00:00",
    "kind": "expected_facts",
    "path": "runs/d2f86855a9738b50/expected-facts.json"
  },
  {
    "created_at": "2026-07-16T08:00:15+00:00",
    "kind": "candidate",
    "path": "runs/d2f86855a9738b50/candidate.json"
  },
  {
    "created_at": "2026-07-16T08:00:15+00:00",
    "kind": "candidate_revision",
    "path": "runs/d2f86855a9738b50/candidate-revision.json"
  },
  {
    "created_at": "2026-07-16T08:00:15+00:00",
    "kind": "component_preservation",
    "path": "runs/d2f86855a9738b50/component-preservation.json"
  },
  {
    "created_at": "2026-07-16T08:00:15+00:00",
    "kind": "semantic_coverage",
    "path": "runs/d2f86855a9738b50/semantic-coverage.json"
  },
  {
    "created_at": "2026-07-16T08:00:39+00:00",
    "kind": "issues",
    "path": "runs/d2f86855a9738b50/issues.json"
  },
  {
    "created_at": "2026-07-16T08:00:39+00:00",
    "kind": "route_decision",
    "path": "runs/d2f86855a9738b50/route-decision.json"
  },
  {
    "created_at": "2026-07-16T08:00:39+00:00",
    "kind": "feedback_rounds",
    "path": "runs/d2f86855a9738b50/feedback-rounds.json"
  },
  {
    "created_at": "2026-07-16T08:00:39+00:00",
    "kind": "ifc",
    "path": "runs/d2f86855a9738b50/output.ifc"
  },
  {
    "created_at": "2026-07-16T08:00:39+00:00",
    "kind": "report",
    "path": "runs/d2f86855a9738b50/report.md"
  },
  {
    "created_at": "2026-07-16T08:00:39+00:00",
    "kind": "session_export",
    "path": "runs/d2f86855a9738b50/session-export.json"
  }
]
```
