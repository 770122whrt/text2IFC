# Phase 6.2-fix Real REPL Acceptance

## REPL Interaction Evidence

- interaction_mode: `human_repl_live`
- input_source: `terminal`
- session_hash: `8c8ef9a111e326d7`

```json
[
  {
    "created_at": "2026-07-16T09:52:56+00:00",
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
    "created_at": "2026-07-16T09:55:45+00:00",
    "event_index": 1,
    "event_type": "generator_completed",
    "payload": {
      "case_id": "8c8ef9a111e326d7",
      "classification": "formal",
      "contract_valid": true,
      "evidence_class": "provider-backed-staged",
      "output_dir": "dataset\\processed\\agent-demo\\phase6.6-medium-live-64k-fix2\\runs\\8c8ef9a111e326d7\\generator",
      "response_id": "27716f2e-14bb-4b23-a8e3-671f1068617a",
      "stage": "generate",
      "status": "formal",
      "strict_output_contract_valid": true,
      "valid": true
    }
  },
  {
    "created_at": "2026-07-16T09:55:45+00:00",
    "event_index": 2,
    "event_type": "semantic_coverage_completed",
    "payload": {
      "blocking_fact_count": 0,
      "capability_profile_hash": "sha256:1a9b5d81e65c07e3b578782744596bd9a56eb1ecf9702c94dbde5fd91681bbb5",
      "capability_profile_id": "text2ifc/semantic-capabilities/ifc2x3-bim-json-2.0/1.0",
      "case_id": "8c8ef9a111e326d7",
      "coverage": {
        "blocking_facts": [],
        "candidate_entity_count": 34,
        "capability_profile_hash": "sha256:1a9b5d81e65c07e3b578782744596bd9a56eb1ecf9702c94dbde5fd91681bbb5",
        "capability_profile_id": "text2ifc/semantic-capabilities/ifc2x3-bim-json-2.0/1.0",
        "case_id": "8c8ef9a111e326d7",
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
                "id": "ground-floor-slab",
                "polygon": [
                  [
                    0,
                    0
                  ],
                  [
                    12000,
                    0
                  ],
                  [
                    12000,
                    6000
                  ],
                  [
                    0,
                    6000
                  ],
                  [
                    0,
                    0
                  ]
                ],
                "storey": "storey-1",
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
                    "host_wall": "wall-corridor-offA",
                    "id": "door-offA",
                    "width_mm": 900
                  },
                  {
                    "alignment": "host_centerline",
                    "height_mm": 2100,
                    "host_wall": "wall-corridor-offB",
                    "id": "door-offB",
                    "width_mm": 900
                  },
                  {
                    "alignment": "host_centerline",
                    "height_mm": 2100,
                    "host_wall": "wall-corridor-offC",
                    "id": "door-offC",
                    "width_mm": 900
                  },
                  {
                    "alignment": "host_centerline",
                    "height_mm": 2200,
                    "host_wall": "wall-south",
                    "id": "door-main",
                    "width_mm": 1600
                  }
                ],
                "elevation_mm": 0,
                "id": "storey-1",
                "net_height_mm": 3200,
                "spaces": [
                  {
                    "bounds": {
                      "x": [
                        0,
                        12000
                      ],
                      "y": [
                        0,
                        2000
                      ]
                    },
                    "id": "space-corridor"
                  },
                  {
                    "bounds": {
                      "x": [
                        0,
                        4000
                      ],
                      "y": [
                        2000,
                        6000
                      ]
                    },
                    "id": "space-officeA"
                  },
                  {
                    "bounds": {
                      "x": [
                        4000,
                        8000
                      ],
                      "y": [
                        2000,
                        6000
                      ]
                    },
                    "id": "space-officeB"
                  },
                  {
                    "bounds": {
                      "x": [
                        8000,
                        12000
                      ],
                      "y": [
                        2000,
                        6000
                      ]
                    },
                    "id": "space-officeC"
                  }
                ],
                "walls": {
                  "exterior": [
                    {
                      "end_mm": [
                        0,
                        6000
                      ],
                      "height_mm": 3200,
                      "id": "wall-west",
                      "start_mm": [
                        0,
                        0
                      ],
                      "thickness_mm": 200
                    },
                    {
                      "end_mm": [
                        12000,
                        6000
                      ],
                      "height_mm": 3200,
                      "id": "wall-east",
                      "start_mm": [
                        12000,
                        0
                      ],
                      "thickness_mm": 200
                    },
                    {
                      "end_mm": [
                        12000,
                        0
                      ],
                      "height_mm": 3200,
                      "id": "wall-south",
                      "start_mm": [
                        0,
                        0
                      ],
                      "thickness_mm": 200
                    },
                    {
                      "end_mm": [
                        4000,
                        6000
                      ],
                      "height_mm": 3200,
                      "id": "wall-north-A",
                      "start_mm": [
                        0,
                        6000
                      ],
                      "thickness_mm": 200
                    },
                    {
                      "end_mm": [
                        8000,
                        6000
                      ],
                      "height_mm": 3200,
                      "id": "wall-north-B",
                      "start_mm": [
                        4000,
                        6000
                      ],
                      "thickness_mm": 200
                    },
                    {
                      "end_mm": [
                        12000,
                        6000
                      ],
                      "height_mm": 3200,
                      "id": "wall-north-C",
                      "start_mm": [
                        8000,
                        6000
                      ],
                      "thickness_mm": 200
                    }
                  ],
                  "interior": [
                    {
                      "connects": [
                        "space-corridor",
                        "space-officeA"
                      ],
                      "end_mm": [
                        4000,
                        2000
                      ],
                      "height_mm": 3200,
                      "id": "wall-corridor-offA",
                      "start_mm": [
                        0,
                        2000
                      ],
                      "thickness_mm": 200
                    },
                    {
                      "connects": [
                        "space-corridor",
                        "space-officeB"
                      ],
                      "end_mm": [
                        8000,
                        2000
                      ],
                      "height_mm": 3200,
                      "id": "wall-corridor-offB",
                      "start_mm": [
                        4000,
                        2000
                      ],
                      "thickness_mm": 200
                    },
                    {
                      "connects": [
                        "space-corridor",
                        "space-officeC"
                      ],
                      "end_mm": [
                        12000,
                        2000
                      ],
                      "height_mm": 3200,
                      "id": "wall-corridor-offC",
                      "start_mm": [
                        8000,
                        2000
                      ],
                      "thickness_mm": 200
                    },
                    {
                      "connects": [
                        "space-officeA",
                        "space-officeB"
                      ],
                      "end_mm": [
                        4000,
                        6000
                      ],
                      "height_mm": 3200,
                      "id": "wall-offA-offB",
                      "start_mm": [
                        4000,
                        2000
                      ],
                      "thickness_mm": 200
                    },
                    {
                      "connects": [
                        "space-officeB",
                        "space-officeC"
                      ],
                      "end_mm": [
                        8000,
                        6000
                      ],
                      "height_mm": 3200,
                      "id": "wall-offB-offC",
                      "start_mm": [
                        8000,
                        2000
                      ],
                      "thickness_mm": 200
                    }
                  ]
                },
                "windows": [
                  {
                    "alignment": "host_centerline",
                    "height_mm": 1200,
                    "host_wall": "wall-north-A",
                    "id": "window-offA",
                    "sill_height_mm": 900,
                    "width_mm": 1800
                  },
                  {
                    "alignment": "host_centerline",
                    "height_mm": 1200,
                    "host_wall": "wall-north-B",
                    "id": "window-offB",
                    "sill_height_mm": 900,
                    "width_mm": 1800
                  },
                  {
                    "alignment": "host_centerline",
                    "height_mm": 1200,
                    "host_wall": "wall-north-C",
                    "id": "window-offC",
                    "sill_height_mm": 900,
                    "width_mm": 1800
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
    "created_at": "2026-07-16T09:55:45+00:00",
    "event_index": 3,
    "event_type": "repair_completed",
    "payload": {
      "case_id": "8c8ef9a111e326d7",
      "evidence_class": "live-derived-no-call",
      "output_dir": "dataset/processed/agent-demo/phase6.6-medium-live-64k-fix2/runs/8c8ef9a111e326d7/repair",
      "provider_call_count": 0,
      "repair_attempts": [],
      "route": "no_repair_needed",
      "source_generator_response_id": "27716f2e-14bb-4b23-a8e3-671f1068617a",
      "stage": "repair",
      "valid": true
    }
  },
  {
    "created_at": "2026-07-16T09:55:47+00:00",
    "event_index": 4,
    "event_type": "candidate_gates_completed",
    "payload": {
      "case_id": "8c8ef9a111e326d7",
      "compile_reopen_success": true,
      "deterministic_gates_passed": true,
      "gate_summary": {
        "artifact_hashes": {
          "dynamic-gates.json": "6365c09a6ca90f70cd0b245c6851ec459c2f08d3eeb219581b4656ad2fdfd7d8",
          "expected-facts.json": "39749bcb3b8fcf042532901f69c1823e1575df805f8507d26da373414249661d",
          "generator/candidate.json": "dc764c0e05a2762c4133ce38609de599d7415e4ffaa3c84777d8fe00d9a3c208",
          "generator/validation.json": "6be6595f4f77090199203073905e3755e4015ff1a83b3412d64571cd872b4c41",
          "geometry-feedback.json": "50e250ce222e0ba6485143241886e5932bf5e29c1aa3b9d6f1216c93a3161df8",
          "ifc-verification.json": "013d1c8bf5fb348c5c120239e1dc80696aff8ad0dab84cc83de8db9640ad9082",
          "repair/route.json": "6f18ada43dcd4eb0b005247e9226d3bb5967443b19e80fdb7cda3bae5be526d4",
          "semantic-coverage.json": "0f4d6bd2b810232c9f57654c06376c3422b70f9781fbebb98220af68817da438"
        },
        "candidate_hash": "dc764c0e05a2762c4133ce38609de599d7415e4ffaa3c84777d8fe00d9a3c208",
        "candidate_path": "generator/candidate.json",
        "case_id": "8c8ef9a111e326d7",
        "evidence": {
          "compile_reopen": {
            "ifc_issues": [],
            "input_issues": [],
            "output_path": "dataset\\processed\\agent-demo\\phase6.6-medium-live-64k-fix2\\runs\\8c8ef9a111e326d7\\output.ifc",
            "success": true
          },
          "geometry": {
            "expectation_source": "design_brief_expected_facts",
            "issues": [],
            "metrics": {
              "case_id": "8c8ef9a111e326d7",
              "floor_openings": {},
              "roof": {},
              "slabs": {
                "ground-floor-slab": {
                  "bbox": {
                    "x": [
                      0.0,
                      12.0
                    ],
                    "y": [
                      0.0,
                      6.0
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
                "space-corridor": {
                  "bbox": {
                    "x": [
                      0.0,
                      12.0
                    ],
                    "y": [
                      0.0,
                      2.0
                    ],
                    "z": [
                      0.0,
                      3.2
                    ]
                  },
                  "ifc_class": "IfcSpace"
                },
                "space-officeA": {
                  "bbox": {
                    "x": [
                      0.0,
                      4.0
                    ],
                    "y": [
                      2.0,
                      6.0
                    ],
                    "z": [
                      0.0,
                      3.2
                    ]
                  },
                  "ifc_class": "IfcSpace"
                },
                "space-officeB": {
                  "bbox": {
                    "x": [
                      4.0,
                      8.0
                    ],
                    "y": [
                      2.0,
                      6.0
                    ],
                    "z": [
                      0.0,
                      3.2
                    ]
                  },
                  "ifc_class": "IfcSpace"
                },
                "space-officeC": {
                  "bbox": {
                    "x": [
                      8.0,
                      12.0
                    ],
                    "y": [
                      2.0,
                      6.0
                    ],
                    "z": [
                      0.0,
                      3.2
                    ]
                  },
                  "ifc_class": "IfcSpace"
                }
              },
              "stairs": {},
              "wall_set_convention": "primary",
              "walls": {
                "wall-corridor-offA": {
                  "axis": "x",
                  "bbox": {
                    "x": [
                      0.0,
                      4.0
                    ],
                    "y": [
                      1.9,
                      2.1
                    ],
                    "z": [
                      0.0,
                      3.2
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-corridor-offB": {
                  "axis": "x",
                  "bbox": {
                    "x": [
                      4.0,
                      8.0
                    ],
                    "y": [
                      1.9,
                      2.1
                    ],
                    "z": [
                      0.0,
                      3.2
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-corridor-offC": {
                  "axis": "x",
                  "bbox": {
                    "x": [
                      8.0,
                      12.0
                    ],
                    "y": [
                      1.9,
                      2.1
                    ],
                    "z": [
                      0.0,
                      3.2
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-east": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      11.9,
                      12.1
                    ],
                    "y": [
                      0.0,
                      6.0
                    ],
                    "z": [
                      0.0,
                      3.2
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-north-A": {
                  "axis": "x",
                  "bbox": {
                    "x": [
                      0.0,
                      4.0
                    ],
                    "y": [
                      5.9,
                      6.1
                    ],
                    "z": [
                      0.0,
                      3.2
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-north-B": {
                  "axis": "x",
                  "bbox": {
                    "x": [
                      4.0,
                      8.0
                    ],
                    "y": [
                      5.9,
                      6.1
                    ],
                    "z": [
                      0.0,
                      3.2
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-north-C": {
                  "axis": "x",
                  "bbox": {
                    "x": [
                      8.0,
                      12.0
                    ],
                    "y": [
                      5.9,
                      6.1
                    ],
                    "z": [
                      0.0,
                      3.2
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-offA-offB": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      3.9,
                      4.1
                    ],
                    "y": [
                      2.0,
                      6.0
                    ],
                    "z": [
                      0.0,
                      3.2
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-offB-offC": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      7.9,
                      8.1
                    ],
                    "y": [
                      2.0,
                      6.0
                    ],
                    "z": [
                      0.0,
                      3.2
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-south": {
                  "axis": "x",
                  "bbox": {
                    "x": [
                      0.0,
                      12.0
                    ],
                    "y": [
                      -0.1,
                      0.1
                    ],
                    "z": [
                      0.0,
                      3.2
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-west": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      -0.1,
                      0.1
                    ],
                    "y": [
                      0.0,
                      6.0
                    ],
                    "z": [
                      0.0,
                      3.2
                    ]
                  },
                  "ifc_class": "IfcWall"
                }
              }
            },
            "success": true
          },
          "repair_history": {
            "case_id": "8c8ef9a111e326d7",
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
            "source_generator_dir": "dataset/processed/agent-demo/phase6.6-medium-live-64k-fix2/runs/8c8ef9a111e326d7/generator",
            "source_generator_response_id": "27716f2e-14bb-4b23-a8e3-671f1068617a",
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
            "candidate_entity_count": 34,
            "capability_profile_hash": "sha256:1a9b5d81e65c07e3b578782744596bd9a56eb1ecf9702c94dbde5fd91681bbb5",
            "capability_profile_id": "text2ifc/semantic-capabilities/ifc2x3-bim-json-2.0/1.0",
            "case_id": "8c8ef9a111e326d7",
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
                    "id": "ground-floor-slab",
                    "polygon": [
                      [
                        0,
                        0
                      ],
                      [
                        12000,
                        0
                      ],
                      [
                        12000,
                        6000
                      ],
                      [
                        0,
                        6000
                      ],
                      [
                        0,
                        0
                      ]
                    ],
                    "storey": "storey-1",
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
                        "host_wall": "wall-corridor-offA",
                        "id": "door-offA",
                        "width_mm": 900
                      },
                      {
                        "alignment": "host_centerline",
                        "height_mm": 2100,
                        "host_wall": "wall-corridor-offB",
                        "id": "door-offB",
                        "width_mm": 900
                      },
                      {
                        "alignment": "host_centerline",
                        "height_mm": 2100,
                        "host_wall": "wall-corridor-offC",
                        "id": "door-offC",
                        "width_mm": 900
                      },
                      {
                        "alignment": "host_centerline",
                        "height_mm": 2200,
                        "host_wall": "wall-south",
                        "id": "door-main",
                        "width_mm": 1600
                      }
                    ],
                    "elevation_mm": 0,
                    "id": "storey-1",
                    "net_height_mm": 3200,
                    "spaces": [
                      {
                        "bounds": {
                          "x": [
                            0,
                            12000
                          ],
                          "y": [
                            0,
                            2000
                          ]
                        },
                        "id": "space-corridor"
                      },
                      {
                        "bounds": {
                          "x": [
                            0,
                            4000
                          ],
                          "y": [
                            2000,
                            6000
                          ]
                        },
                        "id": "space-officeA"
                      },
                      {
                        "bounds": {
                          "x": [
                            4000,
                            8000
                          ],
                          "y": [
                            2000,
                            6000
                          ]
                        },
                        "id": "space-officeB"
                      },
                      {
                        "bounds": {
                          "x": [
                            8000,
                            12000
                          ],
                          "y": [
                            2000,
                            6000
                          ]
                        },
                        "id": "space-officeC"
                      }
                    ],
                    "walls": {
                      "exterior": [
                        {
                          "end_mm": [
                            0,
                            6000
                          ],
                          "height_mm": 3200,
                          "id": "wall-west",
                          "start_mm": [
                            0,
                            0
                          ],
                          "thickness_mm": 200
                        },
                        {
                          "end_mm": [
                            12000,
                            6000
                          ],
                          "height_mm": 3200,
                          "id": "wall-east",
                          "start_mm": [
                            12000,
                            0
                          ],
                          "thickness_mm": 200
                        },
                        {
                          "end_mm": [
                            12000,
                            0
                          ],
                          "height_mm": 3200,
                          "id": "wall-south",
                          "start_mm": [
                            0,
                            0
                          ],
                          "thickness_mm": 200
                        },
                        {
                          "end_mm": [
                            4000,
                            6000
                          ],
                          "height_mm": 3200,
                          "id": "wall-north-A",
                          "start_mm": [
                            0,
                            6000
                          ],
                          "thickness_mm": 200
                        },
                        {
                          "end_mm": [
                            8000,
                            6000
                          ],
                          "height_mm": 3200,
                          "id": "wall-north-B",
                          "start_mm": [
                            4000,
                            6000
                          ],
                          "thickness_mm": 200
                        },
                        {
                          "end_mm": [
                            12000,
                            6000
                          ],
                          "height_mm": 3200,
                          "id": "wall-north-C",
                          "start_mm": [
                            8000,
                            6000
                          ],
                          "thickness_mm": 200
                        }
                      ],
                      "interior": [
                        {
                          "connects": [
                            "space-corridor",
                            "space-officeA"
                          ],
                          "end_mm": [
                            4000,
                            2000
                          ],
                          "height_mm": 3200,
                          "id": "wall-corridor-offA",
                          "start_mm": [
                            0,
                            2000
                          ],
                          "thickness_mm": 200
                        },
                        {
                          "connects": [
                            "space-corridor",
                            "space-officeB"
                          ],
                          "end_mm": [
                            8000,
                            2000
                          ],
                          "height_mm": 3200,
                          "id": "wall-corridor-offB",
                          "start_mm": [
                            4000,
                            2000
                          ],
                          "thickness_mm": 200
                        },
                        {
                          "connects": [
                            "space-corridor",
                            "space-officeC"
                          ],
                          "end_mm": [
                            12000,
                            2000
                          ],
                          "height_mm": 3200,
                          "id": "wall-corridor-offC",
                          "start_mm": [
                            8000,
                            2000
                          ],
                          "thickness_mm": 200
                        },
                        {
                          "connects": [
                            "space-officeA",
                            "space-officeB"
                          ],
                          "end_mm": [
                            4000,
                            6000
                          ],
                          "height_mm": 3200,
                          "id": "wall-offA-offB",
                          "start_mm": [
                            4000,
                            2000
                          ],
                          "thickness_mm": 200
                        },
                        {
                          "connects": [
                            "space-officeB",
                            "space-officeC"
                          ],
                          "end_mm": [
                            8000,
                            6000
                          ],
                          "height_mm": 3200,
                          "id": "wall-offB-offC",
                          "start_mm": [
                            8000,
                            2000
                          ],
                          "thickness_mm": 200
                        }
                      ]
                    },
                    "windows": [
                      {
                        "alignment": "host_centerline",
                        "height_mm": 1200,
                        "host_wall": "wall-north-A",
                        "id": "window-offA",
                        "sill_height_mm": 900,
                        "width_mm": 1800
                      },
                      {
                        "alignment": "host_centerline",
                        "height_mm": 1200,
                        "host_wall": "wall-north-B",
                        "id": "window-offB",
                        "sill_height_mm": 900,
                        "width_mm": 1800
                      },
                      {
                        "alignment": "host_centerline",
                        "height_mm": 1200,
                        "host_wall": "wall-north-C",
                        "id": "window-offC",
                        "sill_height_mm": 900,
                        "width_mm": 1800
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
        "expected_facts_hash": "39749bcb3b8fcf042532901f69c1823e1575df805f8507d26da373414249661d",
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
                "candidate_id": "door-offA",
                "collection": "doors",
                "expected_id": "door-offA",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "door-offB",
                "collection": "doors",
                "expected_id": "door-offB",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "door-offC",
                "collection": "doors",
                "expected_id": "door-offC",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "door-main",
                "collection": "doors",
                "expected_id": "door-main",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "space-corridor",
                "collection": "spaces",
                "expected_id": "space-corridor",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "space-officeA",
                "collection": "spaces",
                "expected_id": "space-officeA",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "space-officeB",
                "collection": "spaces",
                "expected_id": "space-officeB",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "space-officeC",
                "collection": "spaces",
                "expected_id": "space-officeC",
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
                "candidate_id": "wall-south",
                "collection": "walls",
                "expected_id": "wall-south",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-north-A",
                "collection": "walls",
                "expected_id": "wall-north-A",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-north-B",
                "collection": "walls",
                "expected_id": "wall-north-B",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-north-C",
                "collection": "walls",
                "expected_id": "wall-north-C",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-corridor-offA",
                "collection": "walls",
                "expected_id": "wall-corridor-offA",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-corridor-offB",
                "collection": "walls",
                "expected_id": "wall-corridor-offB",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-corridor-offC",
                "collection": "walls",
                "expected_id": "wall-corridor-offC",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-offA-offB",
                "collection": "walls",
                "expected_id": "wall-offA-offB",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-offB-offC",
                "collection": "walls",
                "expected_id": "wall-offB-offC",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "window-offA",
                "collection": "windows",
                "expected_id": "window-offA",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "window-offB",
                "collection": "windows",
                "expected_id": "window-offB",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "window-offC",
                "collection": "windows",
                "expected_id": "window-offC",
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
        "expectation_source": "design_brief_expected_facts",
        "issues": [],
        "metrics": {
          "case_id": "8c8ef9a111e326d7",
          "floor_openings": {},
          "roof": {},
          "slabs": {
            "ground-floor-slab": {
              "bbox": {
                "x": [
                  0.0,
                  12.0
                ],
                "y": [
                  0.0,
                  6.0
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
            "space-corridor": {
              "bbox": {
                "x": [
                  0.0,
                  12.0
                ],
                "y": [
                  0.0,
                  2.0
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "ifc_class": "IfcSpace"
            },
            "space-officeA": {
              "bbox": {
                "x": [
                  0.0,
                  4.0
                ],
                "y": [
                  2.0,
                  6.0
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "ifc_class": "IfcSpace"
            },
            "space-officeB": {
              "bbox": {
                "x": [
                  4.0,
                  8.0
                ],
                "y": [
                  2.0,
                  6.0
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "ifc_class": "IfcSpace"
            },
            "space-officeC": {
              "bbox": {
                "x": [
                  8.0,
                  12.0
                ],
                "y": [
                  2.0,
                  6.0
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "ifc_class": "IfcSpace"
            }
          },
          "stairs": {},
          "wall_set_convention": "primary",
          "walls": {
            "wall-corridor-offA": {
              "axis": "x",
              "bbox": {
                "x": [
                  0.0,
                  4.0
                ],
                "y": [
                  1.9,
                  2.1
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-corridor-offB": {
              "axis": "x",
              "bbox": {
                "x": [
                  4.0,
                  8.0
                ],
                "y": [
                  1.9,
                  2.1
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-corridor-offC": {
              "axis": "x",
              "bbox": {
                "x": [
                  8.0,
                  12.0
                ],
                "y": [
                  1.9,
                  2.1
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-east": {
              "axis": "y",
              "bbox": {
                "x": [
                  11.9,
                  12.1
                ],
                "y": [
                  0.0,
                  6.0
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-north-A": {
              "axis": "x",
              "bbox": {
                "x": [
                  0.0,
                  4.0
                ],
                "y": [
                  5.9,
                  6.1
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-north-B": {
              "axis": "x",
              "bbox": {
                "x": [
                  4.0,
                  8.0
                ],
                "y": [
                  5.9,
                  6.1
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-north-C": {
              "axis": "x",
              "bbox": {
                "x": [
                  8.0,
                  12.0
                ],
                "y": [
                  5.9,
                  6.1
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-offA-offB": {
              "axis": "y",
              "bbox": {
                "x": [
                  3.9,
                  4.1
                ],
                "y": [
                  2.0,
                  6.0
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-offB-offC": {
              "axis": "y",
              "bbox": {
                "x": [
                  7.9,
                  8.1
                ],
                "y": [
                  2.0,
                  6.0
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-south": {
              "axis": "x",
              "bbox": {
                "x": [
                  0.0,
                  12.0
                ],
                "y": [
                  -0.1,
                  0.1
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-west": {
              "axis": "y",
              "bbox": {
                "x": [
                  -0.1,
                  0.1
                ],
                "y": [
                  0.0,
                  6.0
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "ifc_class": "IfcWall"
            }
          }
        },
        "success": true
      },
      "geometry_success": true,
      "ifc_path": "dataset\\processed\\agent-demo\\phase6.6-medium-live-64k-fix2\\runs\\8c8ef9a111e326d7\\output.ifc",
      "ifc_verification": {
        "ifc_issues": [],
        "input_issues": [],
        "output_path": "dataset\\processed\\agent-demo\\phase6.6-medium-live-64k-fix2\\runs\\8c8ef9a111e326d7\\output.ifc",
        "success": true
      },
      "output_dir": "dataset\\processed\\agent-demo\\phase6.6-medium-live-64k-fix2\\runs\\8c8ef9a111e326d7",
      "semantic_geometry_expectation": {
        "case_id": "8c8ef9a111e326d7",
        "complete": true,
        "floor_openings": {},
        "roof": {},
        "schema_version": "text2ifc/design-geometry-expectation/1.0",
        "slabs": {
          "ground-floor-slab": {
            "bbox": {
              "x": [
                0.0,
                12.0
              ],
              "y": [
                0.0,
                6.0
              ],
              "z": [
                -0.15,
                0.0
              ]
            },
            "datum": "slab_top",
            "must_touch_walls": [],
            "source_fact_refs": [
              "/known_facts/floor_slabs/0"
            ]
          }
        },
        "source": "design_brief_expected_facts",
        "spaces": {
          "space-corridor": {
            "bbox": {
              "x": [
                0.0,
                12.0
              ],
              "y": [
                0.0,
                2.0
              ],
              "z": [
                0.0,
                3.2
              ]
            },
            "source_fact_refs": [
              "/known_facts/storeys/0/spaces/0"
            ],
            "storey_id": "storey-1"
          },
          "space-officeA": {
            "bbox": {
              "x": [
                0.0,
                4.0
              ],
              "y": [
                2.0,
                6.0
              ],
              "z": [
                0.0,
                3.2
              ]
            },
            "source_fact_refs": [
              "/known_facts/storeys/0/spaces/1"
            ],
            "storey_id": "storey-1"
          },
          "space-officeB": {
            "bbox": {
              "x": [
                4.0,
                8.0
              ],
              "y": [
                2.0,
                6.0
              ],
              "z": [
                0.0,
                3.2
              ]
            },
            "source_fact_refs": [
              "/known_facts/storeys/0/spaces/2"
            ],
            "storey_id": "storey-1"
          },
          "space-officeC": {
            "bbox": {
              "x": [
                8.0,
                12.0
              ],
              "y": [
                2.0,
                6.0
              ],
              "z": [
                0.0,
                3.2
              ]
            },
            "source_fact_refs": [
              "/known_facts/storeys/0/spaces/3"
            ],
            "storey_id": "storey-1"
          }
        },
        "stairs": {},
        "tolerance": 0.05,
        "units": "METRE",
        "unresolved": [],
        "walls": {
          "wall-corridor-offA": {
            "axis": "x",
            "bbox": {
              "x": [
                0.0,
                4.0
              ],
              "y": [
                1.9,
                2.1
              ],
              "z": [
                0.0,
                3.2
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-corridor-offA",
            "source_fact_refs": [
              "/known_facts/storeys/0/walls/interior/0"
            ]
          },
          "wall-corridor-offB": {
            "axis": "x",
            "bbox": {
              "x": [
                4.0,
                8.0
              ],
              "y": [
                1.9,
                2.1
              ],
              "z": [
                0.0,
                3.2
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-corridor-offB",
            "source_fact_refs": [
              "/known_facts/storeys/0/walls/interior/1"
            ]
          },
          "wall-corridor-offC": {
            "axis": "x",
            "bbox": {
              "x": [
                8.0,
                12.0
              ],
              "y": [
                1.9,
                2.1
              ],
              "z": [
                0.0,
                3.2
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-corridor-offC",
            "source_fact_refs": [
              "/known_facts/storeys/0/walls/interior/2"
            ]
          },
          "wall-east": {
            "axis": "y",
            "bbox": {
              "x": [
                11.9,
                12.1
              ],
              "y": [
                0.0,
                6.0
              ],
              "z": [
                0.0,
                3.2
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-east",
            "source_fact_refs": [
              "/known_facts/walls/1"
            ]
          },
          "wall-north-A": {
            "axis": "x",
            "bbox": {
              "x": [
                0.0,
                4.0
              ],
              "y": [
                5.9,
                6.1
              ],
              "z": [
                0.0,
                3.2
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-north-A",
            "source_fact_refs": [
              "/known_facts/walls/3"
            ]
          },
          "wall-north-B": {
            "axis": "x",
            "bbox": {
              "x": [
                4.0,
                8.0
              ],
              "y": [
                5.9,
                6.1
              ],
              "z": [
                0.0,
                3.2
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-north-B",
            "source_fact_refs": [
              "/known_facts/walls/4"
            ]
          },
          "wall-north-C": {
            "axis": "x",
            "bbox": {
              "x": [
                8.0,
                12.0
              ],
              "y": [
                5.9,
                6.1
              ],
              "z": [
                0.0,
                3.2
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-north-C",
            "source_fact_refs": [
              "/known_facts/walls/5"
            ]
          },
          "wall-offA-offB": {
            "axis": "y",
            "bbox": {
              "x": [
                3.9,
                4.1
              ],
              "y": [
                2.0,
                6.0
              ],
              "z": [
                0.0,
                3.2
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-offA-offB",
            "source_fact_refs": [
              "/known_facts/storeys/0/walls/interior/3"
            ]
          },
          "wall-offB-offC": {
            "axis": "y",
            "bbox": {
              "x": [
                7.9,
                8.1
              ],
              "y": [
                2.0,
                6.0
              ],
              "z": [
                0.0,
                3.2
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-offB-offC",
            "source_fact_refs": [
              "/known_facts/storeys/0/walls/interior/4"
            ]
          },
          "wall-south": {
            "axis": "x",
            "bbox": {
              "x": [
                0.0,
                12.0
              ],
              "y": [
                -0.1,
                0.1
              ],
              "z": [
                0.0,
                3.2
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-south",
            "source_fact_refs": [
              "/known_facts/walls/2"
            ]
          },
          "wall-west": {
            "axis": "y",
            "bbox": {
              "x": [
                -0.1,
                0.1
              ],
              "y": [
                0.0,
                6.0
              ],
              "z": [
                0.0,
                3.2
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-west",
            "source_fact_refs": [
              "/known_facts/walls/0"
            ]
          }
        }
      },
      "stage": "candidate-gates",
      "valid": true
    }
  },
  {
    "created_at": "2026-07-16T09:55:57+00:00",
    "event_index": 5,
    "event_type": "audit_completed",
    "payload": {
      "case_id": "8c8ef9a111e326d7",
      "evidence_class": "live",
      "output_dir": "dataset/processed/agent-demo/phase6.6-medium-live-64k-fix2/runs/8c8ef9a111e326d7",
      "report_path": "dataset/processed/agent-demo/phase6.6-medium-live-64k-fix2/runs/8c8ef9a111e326d7/report.md",
      "response_id": "5f963857-5b06-42ae-98ac-a0432f735566",
      "route_decision": "accept",
      "route_owner_stage": "none",
      "stage": "audit-report",
      "status": "accepted",
      "valid": true
    }
  },
  {
    "created_at": "2026-07-16T09:55:59+00:00",
    "event_index": 6,
    "event_type": "final_acceptance_completed",
    "payload": {
      "case_id": "8c8ef9a111e326d7",
      "compile_reopen_success": true,
      "geometry_success": true,
      "ifc_path": "dataset\\processed\\agent-demo\\phase6.6-medium-live-64k-fix2\\runs\\8c8ef9a111e326d7\\output.ifc",
      "output_dir": "dataset\\processed\\agent-demo\\phase6.6-medium-live-64k-fix2\\runs\\8c8ef9a111e326d7",
      "report_path": "dataset\\processed\\agent-demo\\phase6.6-medium-live-64k-fix2\\runs\\8c8ef9a111e326d7\\report.md",
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
## 3.3.2 Medium 能力边界输入：三间办公室与受支持主入口门

创建一个单层小型办公区。办公区整体为封闭矩形，内部净尺寸为东西方向 12 米、南北方向 6 米。

南侧设置一条东西向公共走廊，净尺寸为 12 米 × 2 米。走廊占据办公区南侧完整宽度，走廊西端由西侧外墙封闭，东端由东侧外墙封闭，不设置开放端。

走廊北侧从西向东依次设置：

- 办公室 A：4 米 × 4 米；
- 办公室 B：4 米 × 4 米；
- 办公室 C：4 米 × 4 米。

三间办公室并排填满办公区北侧：办公室 A 的西侧边界与办公区西侧外墙相接，办公室 C 的东侧边界与办公区东侧外墙相接，三间办公室的北侧外墙连续闭合。办公区的南、北、西、东四侧外墙共同构成完整闭合的外轮廓。

办公区净高为 3.2 米，墙厚为 200 毫米，地板厚为 150 毫米。

每间办公室与走廊之间设置一樘门，门位于对应共享墙中间，门宽 0.9 米、高 2.1 米。

在走廊南侧外墙中间设置一樘主入口门，门宽 1.6 米、高 2.2 米。

每间办公室北侧外墙各设置一扇窗，窗宽 1.8 米、高 1.2 米，窗台高 0.9 米。

分别为走廊和三间办公室生成 `IfcSpace`。走廊与办公室必须位于同一楼层，并完整填充上述 12 米 × 6 米封闭内轮廓。

相邻办公室之间以及办公室与走廊之间必须共用墙体，不得生成重叠墙；外墙在转角处必须相接，不得留出未封闭缺口。
```

## Transcript

```json
[
  {
    "created_at": "2026-07-16T09:52:54+00:00",
    "role": "user",
    "text": "## 3.3.2 Medium 能力边界输入：三间办公室与受支持主入口门\n\n创建一个单层小型办公区。办公区整体为封闭矩形，内部净尺寸为东西方向 12 米、南北方向 6 米。\n\n南侧设置一条东西向公共走廊，净尺寸为 12 米 × 2 米。走廊占据办公区南侧完整宽度，走廊西端由西侧外墙封闭，东端由东侧外墙封闭，不设置开放端。\n\n走廊北侧从西向东依次设置：\n\n- 办公室 A：4 米 × 4 米；\n- 办公室 B：4 米 × 4 米；\n- 办公室 C：4 米 × 4 米。\n\n三间办公室并排填满办公区北侧：办公室 A 的西侧边界与办公区西侧外墙相接，办公室 C 的东侧边界与办公区东侧外墙相接，三间办公室的北侧外墙连续闭合。办公区的南、北、西、东四侧外墙共同构成完整闭合的外轮廓。\n\n办公区净高为 3.2 米，墙厚为 200 毫米，地板厚为 150 毫米。\n\n每间办公室与走廊之间设置一樘门，门位于对应共享墙中间，门宽 0.9 米、高 2.1 米。\n\n在走廊南侧外墙中间设置一樘主入口门，门宽 1.6 米、高 2.2 米。\n\n每间办公室北侧外墙各设置一扇窗，窗宽 1.8 米、高 1.2 米，窗台高 0.9 米。\n\n分别为走廊和三间办公室生成 `IfcSpace`。走廊与办公室必须位于同一楼层，并完整填充上述 12 米 × 6 米封闭内轮廓。\n\n相邻办公室之间以及办公室与走廊之间必须共用墙体，不得生成重叠墙；外墙在转角处必须相接，不得留出未封闭缺口。",
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
- [audit/request.redacted.json](audit/request.redacted.json)
- [audit/response.raw.json](audit/response.raw.json)
- [audit/model-text.txt](audit/model-text.txt)
- [audit/audit-report.json](audit/audit-report.json)
- [audit/validation.json](audit/validation.json)
- [audit/metrics.json](audit/metrics.json)

## Semantic Coverage

- [semantic-capabilities.json](semantic-capabilities.json)
- [semantic-coverage.json](semantic-coverage.json)
- [semantic-geometry-expectation.json](semantic-geometry-expectation.json)

## Deterministic Gates

- [acceptance-metrics.json](acceptance-metrics.json)
- [ifc-verification.json](ifc-verification.json)
- [geometry-feedback.json](geometry-feedback.json)
- [secret-scan.json](secret-scan.json)

```json
{
  "case_id": "8c8ef9a111e326d7",
  "compile_reopen_success": true,
  "geometry_success": true,
  "ifc_path": "dataset\\processed\\agent-demo\\phase6.6-medium-live-64k-fix2\\runs\\8c8ef9a111e326d7\\output.ifc",
  "output_dir": "dataset\\processed\\agent-demo\\phase6.6-medium-live-64k-fix2\\runs\\8c8ef9a111e326d7",
  "report_path": "dataset\\processed\\agent-demo\\phase6.6-medium-live-64k-fix2\\runs\\8c8ef9a111e326d7\\report.md",
  "secret_finding_count": 0,
  "stage": "final-acceptance",
  "valid": true
}
```

## Revision and ChangeSet History

```json
{
  "changed_ids": [
    "door-main",
    "door-offA",
    "door-offB",
    "door-offC",
    "ground-floor-slab",
    "opening-door-main",
    "opening-door-offA",
    "opening-door-offB",
    "opening-door-offC",
    "opening-window-offA",
    "opening-window-offB",
    "opening-window-offC",
    "rel-fills-door-main",
    "rel-fills-door-offA",
    "rel-fills-door-offB",
    "rel-fills-door-offC",
    "rel-fills-window-offA",
    "rel-fills-window-offB",
    "rel-fills-window-offC",
    "rel-voids-door-main",
    "rel-voids-door-offA",
    "rel-voids-door-offB",
    "rel-voids-door-offC",
    "rel-voids-window-offA",
    "rel-voids-window-offB",
    "rel-voids-window-offC",
    "space-corridor",
    "space-officeA",
    "space-officeB",
    "space-officeC",
    "wall-corridor-offA",
    "wall-corridor-offB",
    "wall-corridor-offC",
    "wall-east",
    "wall-north-A",
    "wall-north-B",
    "wall-north-C",
    "wall-offA-offB",
    "wall-offB-offC",
    "wall-south",
    "wall-west",
    "window-offA",
    "window-offB",
    "window-offC"
  ],
  "changesets": [
    {
      "path": "generator-staged/package-01-package-storey-1/changeset.json",
      "payload": {
        "base_candidate_hash": "sha256:ebbb45d31d9bc12dac7461354eda814be9582943be4a2e6c486852199057a379",
        "base_revision_id": "revision-00",
        "changeset_id": "changeset-package-storey-1",
        "expected_facts_hash": "sha256:39749bcb3b8fcf042532901f69c1823e1575df805f8507d26da373414249661d",
        "operations": [
          {
            "evidence_refs": [
              "issue-package-storey-1:/expected"
            ],
            "op": "add_entity",
            "operation_id": "add-wall-west",
            "target_id": "wall-west",
            "value": {
              "attributes": {
                "Name": "West exterior wall",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    0,
                    3000,
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
                  "depth": 3200,
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
                "Name": "East exterior wall",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    12000,
                    3000,
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
                  "depth": 3200,
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
            "operation_id": "add-wall-south",
            "target_id": "wall-south",
            "value": {
              "attributes": {
                "Name": "South exterior wall",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    6000,
                    0,
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
                  "depth": 3200,
                  "direction": [
                    0,
                    0,
                    1
                  ],
                  "kind": "extruded_profile",
                  "profile": {
                    "kind": "rectangle",
                    "x": 12000,
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
            "operation_id": "add-wall-north-A",
            "target_id": "wall-north-A",
            "value": {
              "attributes": {
                "Name": "North exterior wall A",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    2000,
                    6000,
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
                  "depth": 3200,
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
              "id": "wall-north-A",
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
            "operation_id": "add-wall-north-B",
            "target_id": "wall-north-B",
            "value": {
              "attributes": {
                "Name": "North exterior wall B",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    6000,
                    6000,
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
                  "depth": 3200,
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
              "id": "wall-north-B",
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
            "operation_id": "add-wall-north-C",
            "target_id": "wall-north-C",
            "value": {
              "attributes": {
                "Name": "North exterior wall C",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    10000,
                    6000,
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
                  "depth": 3200,
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
              "id": "wall-north-C",
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
            "operation_id": "add-wall-corridor-offA",
            "target_id": "wall-corridor-offA",
            "value": {
              "attributes": {
                "Name": "Corridor-Office A wall",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    2000,
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
                  "depth": 3200,
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
              "id": "wall-corridor-offA",
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
            "operation_id": "add-wall-corridor-offB",
            "target_id": "wall-corridor-offB",
            "value": {
              "attributes": {
                "Name": "Corridor-Office B wall",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    6000,
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
                  "depth": 3200,
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
              "id": "wall-corridor-offB",
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
            "operation_id": "add-wall-corridor-offC",
            "target_id": "wall-corridor-offC",
            "value": {
              "attributes": {
                "Name": "Corridor-Office C wall",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    10000,
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
                  "depth": 3200,
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
              "id": "wall-corridor-offC",
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
            "operation_id": "add-wall-offA-offB",
            "target_id": "wall-offA-offB",
            "value": {
              "attributes": {
                "Name": "Office A-Office B partition",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    4000,
                    4000,
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
                  "depth": 3200,
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
              "id": "wall-offA-offB",
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
            "operation_id": "add-wall-offB-offC",
            "target_id": "wall-offB-offC",
            "value": {
              "attributes": {
                "Name": "Office B-Office C partition",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    8000,
                    4000,
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
                  "depth": 3200,
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
              "id": "wall-offB-offC",
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
            "operation_id": "add-space-corridor",
            "target_id": "space-corridor",
            "value": {
              "attributes": {
                "InteriorOrExteriorSpace": "INTERNAL",
                "Name": "Corridor",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    6000,
                    1000,
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
                  "depth": 3200,
                  "direction": [
                    0,
                    0,
                    1
                  ],
                  "kind": "extruded_profile",
                  "profile": {
                    "kind": "rectangle",
                    "x": 12000,
                    "y": 2000
                  }
                }
              },
              "id": "space-corridor",
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
            "operation_id": "add-space-officeA",
            "target_id": "space-officeA",
            "value": {
              "attributes": {
                "InteriorOrExteriorSpace": "INTERNAL",
                "Name": "Office A",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    2000,
                    4000,
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
                  "depth": 3200,
                  "direction": [
                    0,
                    0,
                    1
                  ],
                  "kind": "extruded_profile",
                  "profile": {
                    "kind": "rectangle",
                    "x": 4000,
                    "y": 4000
                  }
                }
              },
              "id": "space-officeA",
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
            "operation_id": "add-space-officeB",
            "target_id": "space-officeB",
            "value": {
              "attributes": {
                "InteriorOrExteriorSpace": "INTERNAL",
                "Name": "Office B",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    6000,
                    4000,
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
                  "depth": 3200,
                  "direction": [
                    0,
                    0,
                    1
                  ],
                  "kind": "extruded_profile",
                  "profile": {
                    "kind": "rectangle",
                    "x": 4000,
                    "y": 4000
                  }
                }
              },
              "id": "space-officeB",
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
            "operation_id": "add-space-officeC",
            "target_id": "space-officeC",
            "value": {
              "attributes": {
                "InteriorOrExteriorSpace": "INTERNAL",
                "Name": "Office C",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    10000,
                    4000,
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
                  "depth": 3200,
                  "direction": [
                    0,
                    0,
                    1
                  ],
                  "kind": "extruded_profile",
                  "profile": {
                    "kind": "rectangle",
                    "x": 4000,
                    "y": 4000
                  }
                }
              },
              "id": "space-officeC",
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
            "operation_id": "add-opening-door-offA",
            "target_id": "opening-door-offA",
            "value": {
              "attributes": {
                "Name": "Opening for door offA",
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
                  "relative_to": "wall-corridor-offA"
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
              "id": "opening-door-offA",
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
            "operation_id": "add-opening-door-offB",
            "target_id": "opening-door-offB",
            "value": {
              "attributes": {
                "Name": "Opening for door offB",
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
                  "relative_to": "wall-corridor-offB"
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
              "id": "opening-door-offB",
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
            "operation_id": "add-opening-door-offC",
            "target_id": "opening-door-offC",
            "value": {
              "attributes": {
                "Name": "Opening for door offC",
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
                  "relative_to": "wall-corridor-offC"
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
              "id": "opening-door-offC",
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
            "operation_id": "add-opening-door-main",
            "target_id": "opening-door-main",
            "value": {
              "attributes": {
                "Name": "Opening for main entrance door",
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
                  "depth": 2200,
                  "direction": [
                    0,
                    0,
                    1
                  ],
                  "kind": "extruded_profile",
                  "profile": {
                    "kind": "rectangle",
                    "x": 1600,
                    "y": 200
                  }
                }
              },
              "id": "opening-door-main",
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
            "operation_id": "add-opening-window-offA",
            "target_id": "opening-window-offA",
            "value": {
              "attributes": {
                "Name": "Opening for window offA",
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
                  "relative_to": "wall-north-A"
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
                    "x": 1800,
                    "y": 200
                  }
                }
              },
              "id": "opening-window-offA",
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
            "operation_id": "add-opening-window-offB",
            "target_id": "opening-window-offB",
            "value": {
              "attributes": {
                "Name": "Opening for window offB",
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
                  "relative_to": "wall-north-B"
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
                    "x": 1800,
                    "y": 200
                  }
                }
              },
              "id": "opening-window-offB",
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
            "operation_id": "add-opening-window-offC",
            "target_id": "opening-window-offC",
            "value": {
              "attributes": {
                "Name": "Opening for window offC",
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
                  "relative_to": "wall-north-C"
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
                    "x": 1800,
                    "y": 200
                  }
                }
              },
              "id": "opening-window-offC",
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
            "operation_id": "add-door-offA",
            "target_id": "door-offA",
            "value": {
              "attributes": {
                "Name": "Door offA",
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
                  "relative_to": "opening-door-offA"
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
                    "y": 100
                  }
                }
              },
              "id": "door-offA",
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
            "operation_id": "add-door-offB",
            "target_id": "door-offB",
            "value": {
              "attributes": {
                "Name": "Door offB",
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
                  "relative_to": "opening-door-offB"
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
                    "y": 100
                  }
                }
              },
              "id": "door-offB",
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
            "operation_id": "add-door-offC",
            "target_id": "door-offC",
            "value": {
              "attributes": {
                "Name": "Door offC",
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
                  "relative_to": "opening-door-offC"
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
                    "y": 100
                  }
                }
              },
              "id": "door-offC",
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
            "operation_id": "add-door-main",
            "target_id": "door-main",
            "value": {
              "attributes": {
                "Name": "Main entrance door",
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
                  "relative_to": "opening-door-main"
                },
                "OverallHeight": 2200,
                "OverallWidth": 1600,
                "Representation": {
                  "depth": 2200,
                  "direction": [
                    0,
                    0,
                    1
                  ],
                  "kind": "extruded_profile",
                  "profile": {
                    "kind": "rectangle",
                    "x": 1600,
                    "y": 100
                  }
                }
              },
              "id": "door-main",
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
            "operation_id": "add-window-offA",
            "target_id": "window-offA",
            "value": {
              "attributes": {
                "Name": "Window offA",
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
                  "relative_to": "opening-window-offA"
                },
                "OverallHeight": 1200,
                "OverallWidth": 1800,
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
                    "x": 1800,
                    "y": 100
                  }
                }
              },
              "id": "window-offA",
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
            "operation_id": "add-window-offB",
            "target_id": "window-offB",
            "value": {
              "attributes": {
                "Name": "Window offB",
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
                  "relative_to": "opening-window-offB"
                },
                "OverallHeight": 1200,
                "OverallWidth": 1800,
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
                    "x": 1800,
                    "y": 100
                  }
                }
              },
              "id": "window-offB",
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
            "operation_id": "add-window-offC",
            "target_id": "window-offC",
            "value": {
              "attributes": {
                "Name": "Window offC",
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
                  "relative_to": "opening-window-offC"
                },
                "OverallHeight": 1200,
                "OverallWidth": 1800,
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
                    "x": 1800,
                    "y": 100
                  }
                }
              },
              "id": "window-offC",
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
            "operation_id": "add-rel-voids-door-offA",
            "target_id": "rel-voids-door-offA",
            "value": {
              "attributes": {
                "RelatedOpeningElement": "opening-door-offA",
                "RelatingBuildingElement": "wall-corridor-offA"
              },
              "id": "rel-voids-door-offA",
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
            "operation_id": "add-rel-fills-door-offA",
            "target_id": "rel-fills-door-offA",
            "value": {
              "attributes": {
                "RelatedBuildingElement": "door-offA",
                "RelatingOpeningElement": "opening-door-offA"
              },
              "id": "rel-fills-door-offA",
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
            "operation_id": "add-rel-voids-door-offB",
            "target_id": "rel-voids-door-offB",
            "value": {
              "attributes": {
                "RelatedOpeningElement": "opening-door-offB",
                "RelatingBuildingElement": "wall-corridor-offB"
              },
              "id": "rel-voids-door-offB",
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
            "operation_id": "add-rel-fills-door-offB",
            "target_id": "rel-fills-door-offB",
            "value": {
              "attributes": {
                "RelatedBuildingElement": "door-offB",
                "RelatingOpeningElement": "opening-door-offB"
              },
              "id": "rel-fills-door-offB",
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
            "operation_id": "add-rel-voids-door-offC",
            "target_id": "rel-voids-door-offC",
            "value": {
              "attributes": {
                "RelatedOpeningElement": "opening-door-offC",
                "RelatingBuildingElement": "wall-corridor-offC"
              },
              "id": "rel-voids-door-offC",
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
            "operation_id": "add-rel-fills-door-offC",
            "target_id": "rel-fills-door-offC",
            "value": {
              "attributes": {
                "RelatedBuildingElement": "door-offC",
                "RelatingOpeningElement": "opening-door-offC"
              },
              "id": "rel-fills-door-offC",
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
            "operation_id": "add-rel-voids-door-main",
            "target_id": "rel-voids-door-main",
            "value": {
              "attributes": {
                "RelatedOpeningElement": "opening-door-main",
                "RelatingBuildingElement": "wall-south"
              },
              "id": "rel-voids-door-main",
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
            "operation_id": "add-rel-fills-door-main",
            "target_id": "rel-fills-door-main",
            "value": {
              "attributes": {
                "RelatedBuildingElement": "door-main",
                "RelatingOpeningElement": "opening-door-main"
              },
              "id": "rel-fills-door-main",
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
            "operation_id": "add-rel-voids-window-offA",
            "target_id": "rel-voids-window-offA",
            "value": {
              "attributes": {
                "RelatedOpeningElement": "opening-window-offA",
                "RelatingBuildingElement": "wall-north-A"
              },
              "id": "rel-voids-window-offA",
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
            "operation_id": "add-rel-fills-window-offA",
            "target_id": "rel-fills-window-offA",
            "value": {
              "attributes": {
                "RelatedBuildingElement": "window-offA",
                "RelatingOpeningElement": "opening-window-offA"
              },
              "id": "rel-fills-window-offA",
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
            "operation_id": "add-rel-voids-window-offB",
            "target_id": "rel-voids-window-offB",
            "value": {
              "attributes": {
                "RelatedOpeningElement": "opening-window-offB",
                "RelatingBuildingElement": "wall-north-B"
              },
              "id": "rel-voids-window-offB",
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
            "operation_id": "add-rel-fills-window-offB",
            "target_id": "rel-fills-window-offB",
            "value": {
              "attributes": {
                "RelatedBuildingElement": "window-offB",
                "RelatingOpeningElement": "opening-window-offB"
              },
              "id": "rel-fills-window-offB",
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
            "operation_id": "add-rel-voids-window-offC",
            "target_id": "rel-voids-window-offC",
            "value": {
              "attributes": {
                "RelatedOpeningElement": "opening-window-offC",
                "RelatingBuildingElement": "wall-north-C"
              },
              "id": "rel-voids-window-offC",
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
            "operation_id": "add-rel-fills-window-offC",
            "target_id": "rel-fills-window-offC",
            "value": {
              "attributes": {
                "RelatedBuildingElement": "window-offC",
                "RelatingOpeningElement": "opening-window-offC"
              },
              "id": "rel-fills-window-offC",
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
        "base_candidate_hash": "sha256:eb9b715cf6a7f04b2d5f699f3cec78ac5c34e6839490f3cadc9e941f4036273c",
        "base_revision_id": "revision-01",
        "changeset_id": "changeset-package-2",
        "expected_facts_hash": "sha256:39749bcb3b8fcf042532901f69c1823e1575df805f8507d26da373414249661d",
        "operations": [
          {
            "evidence_refs": [
              "issue-package-cross-storey:/expected"
            ],
            "op": "add_entity",
            "operation_id": "add-ground-floor-slab",
            "target_id": "ground-floor-slab",
            "value": {
              "attributes": {
                "Name": "Ground Floor Slab",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    6000,
                    3000,
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
                    "x": 12000,
                    "y": 6000
                  }
                }
              },
              "id": "ground-floor-slab",
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
      "candidate_hash": "sha256:dc764c0e05a2762c4133ce38609de599d7415e4ffaa3c84777d8fe00d9a3c208",
      "deterministic_gates": {
        "case_id": "8c8ef9a111e326d7",
        "compile_reopen_success": true,
        "deterministic_gates_passed": true,
        "gate_summary": {
          "artifact_hashes": {
            "dynamic-gates.json": "6365c09a6ca90f70cd0b245c6851ec459c2f08d3eeb219581b4656ad2fdfd7d8",
            "expected-facts.json": "39749bcb3b8fcf042532901f69c1823e1575df805f8507d26da373414249661d",
            "generator/candidate.json": "dc764c0e05a2762c4133ce38609de599d7415e4ffaa3c84777d8fe00d9a3c208",
            "generator/validation.json": "6be6595f4f77090199203073905e3755e4015ff1a83b3412d64571cd872b4c41",
            "geometry-feedback.json": "50e250ce222e0ba6485143241886e5932bf5e29c1aa3b9d6f1216c93a3161df8",
            "ifc-verification.json": "013d1c8bf5fb348c5c120239e1dc80696aff8ad0dab84cc83de8db9640ad9082",
            "repair/route.json": "6f18ada43dcd4eb0b005247e9226d3bb5967443b19e80fdb7cda3bae5be526d4",
            "semantic-coverage.json": "0f4d6bd2b810232c9f57654c06376c3422b70f9781fbebb98220af68817da438"
          },
          "candidate_hash": "dc764c0e05a2762c4133ce38609de599d7415e4ffaa3c84777d8fe00d9a3c208",
          "candidate_path": "generator/candidate.json",
          "case_id": "8c8ef9a111e326d7",
          "evidence": {
            "compile_reopen": {
              "ifc_issues": [],
              "input_issues": [],
              "output_path": "dataset\\processed\\agent-demo\\phase6.6-medium-live-64k-fix2\\runs\\8c8ef9a111e326d7\\output.ifc",
              "success": true
            },
            "geometry": {
              "expectation_source": "design_brief_expected_facts",
              "issues": [],
              "metrics": {
                "case_id": "8c8ef9a111e326d7",
                "floor_openings": {},
                "roof": {},
                "slabs": {
                  "ground-floor-slab": {
                    "bbox": {
                      "x": [
                        0.0,
                        12.0
                      ],
                      "y": [
                        0.0,
                        6.0
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
                  "space-corridor": {
                    "bbox": {
                      "x": [
                        0.0,
                        12.0
                      ],
                      "y": [
                        0.0,
                        2.0
                      ],
                      "z": [
                        0.0,
                        3.2
                      ]
                    },
                    "ifc_class": "IfcSpace"
                  },
                  "space-officeA": {
                    "bbox": {
                      "x": [
                        0.0,
                        4.0
                      ],
                      "y": [
                        2.0,
                        6.0
                      ],
                      "z": [
                        0.0,
                        3.2
                      ]
                    },
                    "ifc_class": "IfcSpace"
                  },
                  "space-officeB": {
                    "bbox": {
                      "x": [
                        4.0,
                        8.0
                      ],
                      "y": [
                        2.0,
                        6.0
                      ],
                      "z": [
                        0.0,
                        3.2
                      ]
                    },
                    "ifc_class": "IfcSpace"
                  },
                  "space-officeC": {
                    "bbox": {
                      "x": [
                        8.0,
                        12.0
                      ],
                      "y": [
                        2.0,
                        6.0
                      ],
                      "z": [
                        0.0,
                        3.2
                      ]
                    },
                    "ifc_class": "IfcSpace"
                  }
                },
                "stairs": {},
                "wall_set_convention": "primary",
                "walls": {
                  "wall-corridor-offA": {
                    "axis": "x",
                    "bbox": {
                      "x": [
                        0.0,
                        4.0
                      ],
                      "y": [
                        1.9,
                        2.1
                      ],
                      "z": [
                        0.0,
                        3.2
                      ]
                    },
                    "ifc_class": "IfcWall"
                  },
                  "wall-corridor-offB": {
                    "axis": "x",
                    "bbox": {
                      "x": [
                        4.0,
                        8.0
                      ],
                      "y": [
                        1.9,
                        2.1
                      ],
                      "z": [
                        0.0,
                        3.2
                      ]
                    },
                    "ifc_class": "IfcWall"
                  },
                  "wall-corridor-offC": {
                    "axis": "x",
                    "bbox": {
                      "x": [
                        8.0,
                        12.0
                      ],
                      "y": [
                        1.9,
                        2.1
                      ],
                      "z": [
                        0.0,
                        3.2
                      ]
                    },
                    "ifc_class": "IfcWall"
                  },
                  "wall-east": {
                    "axis": "y",
                    "bbox": {
                      "x": [
                        11.9,
                        12.1
                      ],
                      "y": [
                        0.0,
                        6.0
                      ],
                      "z": [
                        0.0,
                        3.2
                      ]
                    },
                    "ifc_class": "IfcWall"
                  },
                  "wall-north-A": {
                    "axis": "x",
                    "bbox": {
                      "x": [
                        0.0,
                        4.0
                      ],
                      "y": [
                        5.9,
                        6.1
                      ],
                      "z": [
                        0.0,
                        3.2
                      ]
                    },
                    "ifc_class": "IfcWall"
                  },
                  "wall-north-B": {
                    "axis": "x",
                    "bbox": {
                      "x": [
                        4.0,
                        8.0
                      ],
                      "y": [
                        5.9,
                        6.1
                      ],
                      "z": [
                        0.0,
                        3.2
                      ]
                    },
                    "ifc_class": "IfcWall"
                  },
                  "wall-north-C": {
                    "axis": "x",
                    "bbox": {
                      "x": [
                        8.0,
                        12.0
                      ],
                      "y": [
                        5.9,
                        6.1
                      ],
                      "z": [
                        0.0,
                        3.2
                      ]
                    },
                    "ifc_class": "IfcWall"
                  },
                  "wall-offA-offB": {
                    "axis": "y",
                    "bbox": {
                      "x": [
                        3.9,
                        4.1
                      ],
                      "y": [
                        2.0,
                        6.0
                      ],
                      "z": [
                        0.0,
                        3.2
                      ]
                    },
                    "ifc_class": "IfcWall"
                  },
                  "wall-offB-offC": {
                    "axis": "y",
                    "bbox": {
                      "x": [
                        7.9,
                        8.1
                      ],
                      "y": [
                        2.0,
                        6.0
                      ],
                      "z": [
                        0.0,
                        3.2
                      ]
                    },
                    "ifc_class": "IfcWall"
                  },
                  "wall-south": {
                    "axis": "x",
                    "bbox": {
                      "x": [
                        0.0,
                        12.0
                      ],
                      "y": [
                        -0.1,
                        0.1
                      ],
                      "z": [
                        0.0,
                        3.2
                      ]
                    },
                    "ifc_class": "IfcWall"
                  },
                  "wall-west": {
                    "axis": "y",
                    "bbox": {
                      "x": [
                        -0.1,
                        0.1
                      ],
                      "y": [
                        0.0,
                        6.0
                      ],
                      "z": [
                        0.0,
                        3.2
                      ]
                    },
                    "ifc_class": "IfcWall"
                  }
                }
              },
              "success": true
            },
            "repair_history": {
              "case_id": "8c8ef9a111e326d7",
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
              "source_generator_dir": "dataset/processed/agent-demo/phase6.6-medium-live-64k-fix2/runs/8c8ef9a111e326d7/generator",
              "source_generator_response_id": "27716f2e-14bb-4b23-a8e3-671f1068617a",
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
              "candidate_entity_count": 34,
              "capability_profile_hash": "sha256:1a9b5d81e65c07e3b578782744596bd9a56eb1ecf9702c94dbde5fd91681bbb5",
              "capability_profile_id": "text2ifc/semantic-capabilities/ifc2x3-bim-json-2.0/1.0",
              "case_id": "8c8ef9a111e326d7",
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
                      "id": "ground-floor-slab",
                      "polygon": [
                        [
                          0,
                          0
                        ],
                        [
                          12000,
                          0
                        ],
                        [
                          12000,
                          6000
                        ],
                        [
                          0,
                          6000
                        ],
                        [
                          0,
                          0
                        ]
                      ],
                      "storey": "storey-1",
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
                          "host_wall": "wall-corridor-offA",
                          "id": "door-offA",
                          "width_mm": 900
                        },
                        {
                          "alignment": "host_centerline",
                          "height_mm": 2100,
                          "host_wall": "wall-corridor-offB",
                          "id": "door-offB",
                          "width_mm": 900
                        },
                        {
                          "alignment": "host_centerline",
                          "height_mm": 2100,
                          "host_wall": "wall-corridor-offC",
                          "id": "door-offC",
                          "width_mm": 900
                        },
                        {
                          "alignment": "host_centerline",
                          "height_mm": 2200,
                          "host_wall": "wall-south",
                          "id": "door-main",
                          "width_mm": 1600
                        }
                      ],
                      "elevation_mm": 0,
                      "id": "storey-1",
                      "net_height_mm": 3200,
                      "spaces": [
                        {
                          "bounds": {
                            "x": [
                              0,
                              12000
                            ],
                            "y": [
                              0,
                              2000
                            ]
                          },
                          "id": "space-corridor"
                        },
                        {
                          "bounds": {
                            "x": [
                              0,
                              4000
                            ],
                            "y": [
                              2000,
                              6000
                            ]
                          },
                          "id": "space-officeA"
                        },
                        {
                          "bounds": {
                            "x": [
                              4000,
                              8000
                            ],
                            "y": [
                              2000,
                              6000
                            ]
                          },
                          "id": "space-officeB"
                        },
                        {
                          "bounds": {
                            "x": [
                              8000,
                              12000
                            ],
                            "y": [
                              2000,
                              6000
                            ]
                          },
                          "id": "space-officeC"
                        }
                      ],
                      "walls": {
                        "exterior": [
                          {
                            "end_mm": [
                              0,
                              6000
                            ],
                            "height_mm": 3200,
                            "id": "wall-west",
                            "start_mm": [
                              0,
                              0
                            ],
                            "thickness_mm": 200
                          },
                          {
                            "end_mm": [
                              12000,
                              6000
                            ],
                            "height_mm": 3200,
                            "id": "wall-east",
                            "start_mm": [
                              12000,
                              0
                            ],
                            "thickness_mm": 200
                          },
                          {
                            "end_mm": [
                              12000,
                              0
                            ],
                            "height_mm": 3200,
                            "id": "wall-south",
                            "start_mm": [
                              0,
                              0
                            ],
                            "thickness_mm": 200
                          },
                          {
                            "end_mm": [
                              4000,
                              6000
                            ],
                            "height_mm": 3200,
                            "id": "wall-north-A",
                            "start_mm": [
                              0,
                              6000
                            ],
                            "thickness_mm": 200
                          },
                          {
                            "end_mm": [
                              8000,
                              6000
                            ],
                            "height_mm": 3200,
                            "id": "wall-north-B",
                            "start_mm": [
                              4000,
                              6000
                            ],
                            "thickness_mm": 200
                          },
                          {
                            "end_mm": [
                              12000,
                              6000
                            ],
                            "height_mm": 3200,
                            "id": "wall-north-C",
                            "start_mm": [
                              8000,
                              6000
                            ],
                            "thickness_mm": 200
                          }
                        ],
                        "interior": [
                          {
                            "connects": [
                              "space-corridor",
                              "space-officeA"
                            ],
                            "end_mm": [
                              4000,
                              2000
                            ],
                            "height_mm": 3200,
                            "id": "wall-corridor-offA",
                            "start_mm": [
                              0,
                              2000
                            ],
                            "thickness_mm": 200
                          },
                          {
                            "connects": [
                              "space-corridor",
                              "space-officeB"
                            ],
                            "end_mm": [
                              8000,
                              2000
                            ],
                            "height_mm": 3200,
                            "id": "wall-corridor-offB",
                            "start_mm": [
                              4000,
                              2000
                            ],
                            "thickness_mm": 200
                          },
                          {
                            "connects": [
                              "space-corridor",
                              "space-officeC"
                            ],
                            "end_mm": [
                              12000,
                              2000
                            ],
                            "height_mm": 3200,
                            "id": "wall-corridor-offC",
                            "start_mm": [
                              8000,
                              2000
                            ],
                            "thickness_mm": 200
                          },
                          {
                            "connects": [
                              "space-officeA",
                              "space-officeB"
                            ],
                            "end_mm": [
                              4000,
                              6000
                            ],
                            "height_mm": 3200,
                            "id": "wall-offA-offB",
                            "start_mm": [
                              4000,
                              2000
                            ],
                            "thickness_mm": 200
                          },
                          {
                            "connects": [
                              "space-officeB",
                              "space-officeC"
                            ],
                            "end_mm": [
                              8000,
                              6000
                            ],
                            "height_mm": 3200,
                            "id": "wall-offB-offC",
                            "start_mm": [
                              8000,
                              2000
                            ],
                            "thickness_mm": 200
                          }
                        ]
                      },
                      "windows": [
                        {
                          "alignment": "host_centerline",
                          "height_mm": 1200,
                          "host_wall": "wall-north-A",
                          "id": "window-offA",
                          "sill_height_mm": 900,
                          "width_mm": 1800
                        },
                        {
                          "alignment": "host_centerline",
                          "height_mm": 1200,
                          "host_wall": "wall-north-B",
                          "id": "window-offB",
                          "sill_height_mm": 900,
                          "width_mm": 1800
                        },
                        {
                          "alignment": "host_centerline",
                          "height_mm": 1200,
                          "host_wall": "wall-north-C",
                          "id": "window-offC",
                          "sill_height_mm": 900,
                          "width_mm": 1800
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
          "expected_facts_hash": "39749bcb3b8fcf042532901f69c1823e1575df805f8507d26da373414249661d",
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
                  "candidate_id": "door-offA",
                  "collection": "doors",
                  "expected_id": "door-offA",
                  "match_basis": "exact_brief_id"
                },
                {
                  "candidate_id": "door-offB",
                  "collection": "doors",
                  "expected_id": "door-offB",
                  "match_basis": "exact_brief_id"
                },
                {
                  "candidate_id": "door-offC",
                  "collection": "doors",
                  "expected_id": "door-offC",
                  "match_basis": "exact_brief_id"
                },
                {
                  "candidate_id": "door-main",
                  "collection": "doors",
                  "expected_id": "door-main",
                  "match_basis": "exact_brief_id"
                },
                {
                  "candidate_id": "space-corridor",
                  "collection": "spaces",
                  "expected_id": "space-corridor",
                  "match_basis": "exact_brief_id"
                },
                {
                  "candidate_id": "space-officeA",
                  "collection": "spaces",
                  "expected_id": "space-officeA",
                  "match_basis": "exact_brief_id"
                },
                {
                  "candidate_id": "space-officeB",
                  "collection": "spaces",
                  "expected_id": "space-officeB",
                  "match_basis": "exact_brief_id"
                },
                {
                  "candidate_id": "space-officeC",
                  "collection": "spaces",
                  "expected_id": "space-officeC",
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
                  "candidate_id": "wall-south",
                  "collection": "walls",
                  "expected_id": "wall-south",
                  "match_basis": "exact_brief_id"
                },
                {
                  "candidate_id": "wall-north-A",
                  "collection": "walls",
                  "expected_id": "wall-north-A",
                  "match_basis": "exact_brief_id"
                },
                {
                  "candidate_id": "wall-north-B",
                  "collection": "walls",
                  "expected_id": "wall-north-B",
                  "match_basis": "exact_brief_id"
                },
                {
                  "candidate_id": "wall-north-C",
                  "collection": "walls",
                  "expected_id": "wall-north-C",
                  "match_basis": "exact_brief_id"
                },
                {
                  "candidate_id": "wall-corridor-offA",
                  "collection": "walls",
                  "expected_id": "wall-corridor-offA",
                  "match_basis": "exact_brief_id"
                },
                {
                  "candidate_id": "wall-corridor-offB",
                  "collection": "walls",
                  "expected_id": "wall-corridor-offB",
                  "match_basis": "exact_brief_id"
                },
                {
                  "candidate_id": "wall-corridor-offC",
                  "collection": "walls",
                  "expected_id": "wall-corridor-offC",
                  "match_basis": "exact_brief_id"
                },
                {
                  "candidate_id": "wall-offA-offB",
                  "collection": "walls",
                  "expected_id": "wall-offA-offB",
                  "match_basis": "exact_brief_id"
                },
                {
                  "candidate_id": "wall-offB-offC",
                  "collection": "walls",
                  "expected_id": "wall-offB-offC",
                  "match_basis": "exact_brief_id"
                },
                {
                  "candidate_id": "window-offA",
                  "collection": "windows",
                  "expected_id": "window-offA",
                  "match_basis": "exact_brief_id"
                },
                {
                  "candidate_id": "window-offB",
                  "collection": "windows",
                  "expected_id": "window-offB",
                  "match_basis": "exact_brief_id"
                },
                {
                  "candidate_id": "window-offC",
                  "collection": "windows",
                  "expected_id": "window-offC",
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
          "expectation_source": "design_brief_expected_facts",
          "issues": [],
          "metrics": {
            "case_id": "8c8ef9a111e326d7",
            "floor_openings": {},
            "roof": {},
            "slabs": {
              "ground-floor-slab": {
                "bbox": {
                  "x": [
                    0.0,
                    12.0
                  ],
                  "y": [
                    0.0,
                    6.0
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
              "space-corridor": {
                "bbox": {
                  "x": [
                    0.0,
                    12.0
                  ],
                  "y": [
                    0.0,
                    2.0
                  ],
                  "z": [
                    0.0,
                    3.2
                  ]
                },
                "ifc_class": "IfcSpace"
              },
              "space-officeA": {
                "bbox": {
                  "x": [
                    0.0,
                    4.0
                  ],
                  "y": [
                    2.0,
                    6.0
                  ],
                  "z": [
                    0.0,
                    3.2
                  ]
                },
                "ifc_class": "IfcSpace"
              },
              "space-officeB": {
                "bbox": {
                  "x": [
                    4.0,
                    8.0
                  ],
                  "y": [
                    2.0,
                    6.0
                  ],
                  "z": [
                    0.0,
                    3.2
                  ]
                },
                "ifc_class": "IfcSpace"
              },
              "space-officeC": {
                "bbox": {
                  "x": [
                    8.0,
                    12.0
                  ],
                  "y": [
                    2.0,
                    6.0
                  ],
                  "z": [
                    0.0,
                    3.2
                  ]
                },
                "ifc_class": "IfcSpace"
              }
            },
            "stairs": {},
            "wall_set_convention": "primary",
            "walls": {
              "wall-corridor-offA": {
                "axis": "x",
                "bbox": {
                  "x": [
                    0.0,
                    4.0
                  ],
                  "y": [
                    1.9,
                    2.1
                  ],
                  "z": [
                    0.0,
                    3.2
                  ]
                },
                "ifc_class": "IfcWall"
              },
              "wall-corridor-offB": {
                "axis": "x",
                "bbox": {
                  "x": [
                    4.0,
                    8.0
                  ],
                  "y": [
                    1.9,
                    2.1
                  ],
                  "z": [
                    0.0,
                    3.2
                  ]
                },
                "ifc_class": "IfcWall"
              },
              "wall-corridor-offC": {
                "axis": "x",
                "bbox": {
                  "x": [
                    8.0,
                    12.0
                  ],
                  "y": [
                    1.9,
                    2.1
                  ],
                  "z": [
                    0.0,
                    3.2
                  ]
                },
                "ifc_class": "IfcWall"
              },
              "wall-east": {
                "axis": "y",
                "bbox": {
                  "x": [
                    11.9,
                    12.1
                  ],
                  "y": [
                    0.0,
                    6.0
                  ],
                  "z": [
                    0.0,
                    3.2
                  ]
                },
                "ifc_class": "IfcWall"
              },
              "wall-north-A": {
                "axis": "x",
                "bbox": {
                  "x": [
                    0.0,
                    4.0
                  ],
                  "y": [
                    5.9,
                    6.1
                  ],
                  "z": [
                    0.0,
                    3.2
                  ]
                },
                "ifc_class": "IfcWall"
              },
              "wall-north-B": {
                "axis": "x",
                "bbox": {
                  "x": [
                    4.0,
                    8.0
                  ],
                  "y": [
                    5.9,
                    6.1
                  ],
                  "z": [
                    0.0,
                    3.2
                  ]
                },
                "ifc_class": "IfcWall"
              },
              "wall-north-C": {
                "axis": "x",
                "bbox": {
                  "x": [
                    8.0,
                    12.0
                  ],
                  "y": [
                    5.9,
                    6.1
                  ],
                  "z": [
                    0.0,
                    3.2
                  ]
                },
                "ifc_class": "IfcWall"
              },
              "wall-offA-offB": {
                "axis": "y",
                "bbox": {
                  "x": [
                    3.9,
                    4.1
                  ],
                  "y": [
                    2.0,
                    6.0
                  ],
                  "z": [
                    0.0,
                    3.2
                  ]
                },
                "ifc_class": "IfcWall"
              },
              "wall-offB-offC": {
                "axis": "y",
                "bbox": {
                  "x": [
                    7.9,
                    8.1
                  ],
                  "y": [
                    2.0,
                    6.0
                  ],
                  "z": [
                    0.0,
                    3.2
                  ]
                },
                "ifc_class": "IfcWall"
              },
              "wall-south": {
                "axis": "x",
                "bbox": {
                  "x": [
                    0.0,
                    12.0
                  ],
                  "y": [
                    -0.1,
                    0.1
                  ],
                  "z": [
                    0.0,
                    3.2
                  ]
                },
                "ifc_class": "IfcWall"
              },
              "wall-west": {
                "axis": "y",
                "bbox": {
                  "x": [
                    -0.1,
                    0.1
                  ],
                  "y": [
                    0.0,
                    6.0
                  ],
                  "z": [
                    0.0,
                    3.2
                  ]
                },
                "ifc_class": "IfcWall"
              }
            }
          },
          "success": true
        },
        "geometry_success": true,
        "ifc_path": "dataset\\processed\\agent-demo\\phase6.6-medium-live-64k-fix2\\runs\\8c8ef9a111e326d7\\output.ifc",
        "ifc_verification": {
          "ifc_issues": [],
          "input_issues": [],
          "output_path": "dataset\\processed\\agent-demo\\phase6.6-medium-live-64k-fix2\\runs\\8c8ef9a111e326d7\\output.ifc",
          "success": true
        },
        "output_dir": "dataset\\processed\\agent-demo\\phase6.6-medium-live-64k-fix2\\runs\\8c8ef9a111e326d7",
        "semantic_geometry_expectation": {
          "case_id": "8c8ef9a111e326d7",
          "complete": true,
          "floor_openings": {},
          "roof": {},
          "schema_version": "text2ifc/design-geometry-expectation/1.0",
          "slabs": {
            "ground-floor-slab": {
              "bbox": {
                "x": [
                  0.0,
                  12.0
                ],
                "y": [
                  0.0,
                  6.0
                ],
                "z": [
                  -0.15,
                  0.0
                ]
              },
              "datum": "slab_top",
              "must_touch_walls": [],
              "source_fact_refs": [
                "/known_facts/floor_slabs/0"
              ]
            }
          },
          "source": "design_brief_expected_facts",
          "spaces": {
            "space-corridor": {
              "bbox": {
                "x": [
                  0.0,
                  12.0
                ],
                "y": [
                  0.0,
                  2.0
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "source_fact_refs": [
                "/known_facts/storeys/0/spaces/0"
              ],
              "storey_id": "storey-1"
            },
            "space-officeA": {
              "bbox": {
                "x": [
                  0.0,
                  4.0
                ],
                "y": [
                  2.0,
                  6.0
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "source_fact_refs": [
                "/known_facts/storeys/0/spaces/1"
              ],
              "storey_id": "storey-1"
            },
            "space-officeB": {
              "bbox": {
                "x": [
                  4.0,
                  8.0
                ],
                "y": [
                  2.0,
                  6.0
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "source_fact_refs": [
                "/known_facts/storeys/0/spaces/2"
              ],
              "storey_id": "storey-1"
            },
            "space-officeC": {
              "bbox": {
                "x": [
                  8.0,
                  12.0
                ],
                "y": [
                  2.0,
                  6.0
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "source_fact_refs": [
                "/known_facts/storeys/0/spaces/3"
              ],
              "storey_id": "storey-1"
            }
          },
          "stairs": {},
          "tolerance": 0.05,
          "units": "METRE",
          "unresolved": [],
          "walls": {
            "wall-corridor-offA": {
              "axis": "x",
              "bbox": {
                "x": [
                  0.0,
                  4.0
                ],
                "y": [
                  1.9,
                  2.1
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
              "bbox_issue_path": "/walls/wall-corridor-offA",
              "source_fact_refs": [
                "/known_facts/storeys/0/walls/interior/0"
              ]
            },
            "wall-corridor-offB": {
              "axis": "x",
              "bbox": {
                "x": [
                  4.0,
                  8.0
                ],
                "y": [
                  1.9,
                  2.1
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
              "bbox_issue_path": "/walls/wall-corridor-offB",
              "source_fact_refs": [
                "/known_facts/storeys/0/walls/interior/1"
              ]
            },
            "wall-corridor-offC": {
              "axis": "x",
              "bbox": {
                "x": [
                  8.0,
                  12.0
                ],
                "y": [
                  1.9,
                  2.1
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
              "bbox_issue_path": "/walls/wall-corridor-offC",
              "source_fact_refs": [
                "/known_facts/storeys/0/walls/interior/2"
              ]
            },
            "wall-east": {
              "axis": "y",
              "bbox": {
                "x": [
                  11.9,
                  12.1
                ],
                "y": [
                  0.0,
                  6.0
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
              "bbox_issue_path": "/walls/wall-east",
              "source_fact_refs": [
                "/known_facts/walls/1"
              ]
            },
            "wall-north-A": {
              "axis": "x",
              "bbox": {
                "x": [
                  0.0,
                  4.0
                ],
                "y": [
                  5.9,
                  6.1
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
              "bbox_issue_path": "/walls/wall-north-A",
              "source_fact_refs": [
                "/known_facts/walls/3"
              ]
            },
            "wall-north-B": {
              "axis": "x",
              "bbox": {
                "x": [
                  4.0,
                  8.0
                ],
                "y": [
                  5.9,
                  6.1
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
              "bbox_issue_path": "/walls/wall-north-B",
              "source_fact_refs": [
                "/known_facts/walls/4"
              ]
            },
            "wall-north-C": {
              "axis": "x",
              "bbox": {
                "x": [
                  8.0,
                  12.0
                ],
                "y": [
                  5.9,
                  6.1
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
              "bbox_issue_path": "/walls/wall-north-C",
              "source_fact_refs": [
                "/known_facts/walls/5"
              ]
            },
            "wall-offA-offB": {
              "axis": "y",
              "bbox": {
                "x": [
                  3.9,
                  4.1
                ],
                "y": [
                  2.0,
                  6.0
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
              "bbox_issue_path": "/walls/wall-offA-offB",
              "source_fact_refs": [
                "/known_facts/storeys/0/walls/interior/3"
              ]
            },
            "wall-offB-offC": {
              "axis": "y",
              "bbox": {
                "x": [
                  7.9,
                  8.1
                ],
                "y": [
                  2.0,
                  6.0
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
              "bbox_issue_path": "/walls/wall-offB-offC",
              "source_fact_refs": [
                "/known_facts/storeys/0/walls/interior/4"
              ]
            },
            "wall-south": {
              "axis": "x",
              "bbox": {
                "x": [
                  0.0,
                  12.0
                ],
                "y": [
                  -0.1,
                  0.1
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
              "bbox_issue_path": "/walls/wall-south",
              "source_fact_refs": [
                "/known_facts/walls/2"
              ]
            },
            "wall-west": {
              "axis": "y",
              "bbox": {
                "x": [
                  -0.1,
                  0.1
                ],
                "y": [
                  0.0,
                  6.0
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
              "bbox_issue_path": "/walls/wall-west",
              "source_fact_refs": [
                "/known_facts/walls/0"
              ]
            }
          }
        },
        "stage": "candidate-gates",
        "valid": true
      },
      "revision_id": "revision-02"
    },
    "issues": [],
    "plan": {
      "changed_ids": [
        "door-main",
        "door-offA",
        "door-offB",
        "door-offC",
        "ground-floor-slab",
        "opening-door-main",
        "opening-door-offA",
        "opening-door-offB",
        "opening-door-offC",
        "opening-window-offA",
        "opening-window-offB",
        "opening-window-offC",
        "rel-fills-door-main",
        "rel-fills-door-offA",
        "rel-fills-door-offB",
        "rel-fills-door-offC",
        "rel-fills-window-offA",
        "rel-fills-window-offB",
        "rel-fills-window-offC",
        "rel-voids-door-main",
        "rel-voids-door-offA",
        "rel-voids-door-offB",
        "rel-voids-door-offC",
        "rel-voids-window-offA",
        "rel-voids-window-offB",
        "rel-voids-window-offC",
        "space-corridor",
        "space-officeA",
        "space-officeB",
        "space-officeC",
        "wall-corridor-offA",
        "wall-corridor-offB",
        "wall-corridor-offC",
        "wall-east",
        "wall-north-A",
        "wall-north-B",
        "wall-north-C",
        "wall-offA-offB",
        "wall-offB-offC",
        "wall-south",
        "wall-west",
        "window-offA",
        "window-offB",
        "window-offC"
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
          "door-main",
          "door-offA",
          "door-offB",
          "door-offC",
          "ground-floor-slab",
          "opening-door-main",
          "opening-door-offA",
          "opening-door-offB",
          "opening-door-offC",
          "opening-window-offA",
          "opening-window-offB",
          "opening-window-offC",
          "rel-fills-door-main",
          "rel-fills-door-offA",
          "rel-fills-door-offB",
          "rel-fills-door-offC",
          "rel-fills-window-offA",
          "rel-fills-window-offB",
          "rel-fills-window-offC",
          "rel-voids-door-main",
          "rel-voids-door-offA",
          "rel-voids-door-offB",
          "rel-voids-door-offC",
          "rel-voids-window-offA",
          "rel-voids-window-offB",
          "rel-voids-window-offC",
          "space-corridor",
          "space-officeA",
          "space-officeB",
          "space-officeC",
          "wall-corridor-offA",
          "wall-corridor-offB",
          "wall-corridor-offC",
          "wall-east",
          "wall-north-A",
          "wall-north-B",
          "wall-north-C",
          "wall-offA-offB",
          "wall-offB-offC",
          "wall-south",
          "wall-west",
          "window-offA",
          "window-offB",
          "window-offC"
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
        "candidate_hash": "sha256:dc764c0e05a2762c4133ce38609de599d7415e4ffaa3c84777d8fe00d9a3c208",
        "expected_facts_hash": "sha256:39749bcb3b8fcf042532901f69c1823e1575df805f8507d26da373414249661d",
        "revision_id": "revision-02"
      },
      "schema_version": "text2ifc/revision-gate-plan/1.0",
      "skipped_local_gates": []
    },
    "schema_version": "text2ifc/revision-gate-evidence/1.0",
    "valid": true
  },
  "geometry_result": {
    "expectation_source": "design_brief_expected_facts",
    "issues": [],
    "metrics": {
      "case_id": "8c8ef9a111e326d7",
      "floor_openings": {},
      "roof": {},
      "slabs": {
        "ground-floor-slab": {
          "bbox": {
            "x": [
              0.0,
              12.0
            ],
            "y": [
              0.0,
              6.0
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
        "space-corridor": {
          "bbox": {
            "x": [
              0.0,
              12.0
            ],
            "y": [
              0.0,
              2.0
            ],
            "z": [
              0.0,
              3.2
            ]
          },
          "ifc_class": "IfcSpace"
        },
        "space-officeA": {
          "bbox": {
            "x": [
              0.0,
              4.0
            ],
            "y": [
              2.0,
              6.0
            ],
            "z": [
              0.0,
              3.2
            ]
          },
          "ifc_class": "IfcSpace"
        },
        "space-officeB": {
          "bbox": {
            "x": [
              4.0,
              8.0
            ],
            "y": [
              2.0,
              6.0
            ],
            "z": [
              0.0,
              3.2
            ]
          },
          "ifc_class": "IfcSpace"
        },
        "space-officeC": {
          "bbox": {
            "x": [
              8.0,
              12.0
            ],
            "y": [
              2.0,
              6.0
            ],
            "z": [
              0.0,
              3.2
            ]
          },
          "ifc_class": "IfcSpace"
        }
      },
      "stairs": {},
      "wall_set_convention": "primary",
      "walls": {
        "wall-corridor-offA": {
          "axis": "x",
          "bbox": {
            "x": [
              0.0,
              4.0
            ],
            "y": [
              1.9,
              2.1
            ],
            "z": [
              0.0,
              3.2
            ]
          },
          "ifc_class": "IfcWall"
        },
        "wall-corridor-offB": {
          "axis": "x",
          "bbox": {
            "x": [
              4.0,
              8.0
            ],
            "y": [
              1.9,
              2.1
            ],
            "z": [
              0.0,
              3.2
            ]
          },
          "ifc_class": "IfcWall"
        },
        "wall-corridor-offC": {
          "axis": "x",
          "bbox": {
            "x": [
              8.0,
              12.0
            ],
            "y": [
              1.9,
              2.1
            ],
            "z": [
              0.0,
              3.2
            ]
          },
          "ifc_class": "IfcWall"
        },
        "wall-east": {
          "axis": "y",
          "bbox": {
            "x": [
              11.9,
              12.1
            ],
            "y": [
              0.0,
              6.0
            ],
            "z": [
              0.0,
              3.2
            ]
          },
          "ifc_class": "IfcWall"
        },
        "wall-north-A": {
          "axis": "x",
          "bbox": {
            "x": [
              0.0,
              4.0
            ],
            "y": [
              5.9,
              6.1
            ],
            "z": [
              0.0,
              3.2
            ]
          },
          "ifc_class": "IfcWall"
        },
        "wall-north-B": {
          "axis": "x",
          "bbox": {
            "x": [
              4.0,
              8.0
            ],
            "y": [
              5.9,
              6.1
            ],
            "z": [
              0.0,
              3.2
            ]
          },
          "ifc_class": "IfcWall"
        },
        "wall-north-C": {
          "axis": "x",
          "bbox": {
            "x": [
              8.0,
              12.0
            ],
            "y": [
              5.9,
              6.1
            ],
            "z": [
              0.0,
              3.2
            ]
          },
          "ifc_class": "IfcWall"
        },
        "wall-offA-offB": {
          "axis": "y",
          "bbox": {
            "x": [
              3.9,
              4.1
            ],
            "y": [
              2.0,
              6.0
            ],
            "z": [
              0.0,
              3.2
            ]
          },
          "ifc_class": "IfcWall"
        },
        "wall-offB-offC": {
          "axis": "y",
          "bbox": {
            "x": [
              7.9,
              8.1
            ],
            "y": [
              2.0,
              6.0
            ],
            "z": [
              0.0,
              3.2
            ]
          },
          "ifc_class": "IfcWall"
        },
        "wall-south": {
          "axis": "x",
          "bbox": {
            "x": [
              0.0,
              12.0
            ],
            "y": [
              -0.1,
              0.1
            ],
            "z": [
              0.0,
              3.2
            ]
          },
          "ifc_class": "IfcWall"
        },
        "wall-west": {
          "axis": "y",
          "bbox": {
            "x": [
              -0.1,
              0.1
            ],
            "y": [
              0.0,
              6.0
            ],
            "z": [
              0.0,
              3.2
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
    "output_path": "dataset\\processed\\agent-demo\\phase6.6-medium-live-64k-fix2\\runs\\8c8ef9a111e326d7\\output.ifc",
    "success": true
  },
  "issues": [],
  "operations": [
    {
      "evidence_refs": [
        "issue-package-storey-1:/expected"
      ],
      "op": "add_entity",
      "operation_id": "add-wall-west",
      "target_id": "wall-west",
      "value": {
        "attributes": {
          "Name": "West exterior wall",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              0,
              3000,
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
            "depth": 3200,
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
          "Name": "East exterior wall",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              12000,
              3000,
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
            "depth": 3200,
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
      "operation_id": "add-wall-south",
      "target_id": "wall-south",
      "value": {
        "attributes": {
          "Name": "South exterior wall",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              6000,
              0,
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
            "depth": 3200,
            "direction": [
              0,
              0,
              1
            ],
            "kind": "extruded_profile",
            "profile": {
              "kind": "rectangle",
              "x": 12000,
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
      "operation_id": "add-wall-north-A",
      "target_id": "wall-north-A",
      "value": {
        "attributes": {
          "Name": "North exterior wall A",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              2000,
              6000,
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
            "depth": 3200,
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
        "id": "wall-north-A",
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
      "operation_id": "add-wall-north-B",
      "target_id": "wall-north-B",
      "value": {
        "attributes": {
          "Name": "North exterior wall B",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              6000,
              6000,
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
            "depth": 3200,
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
        "id": "wall-north-B",
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
      "operation_id": "add-wall-north-C",
      "target_id": "wall-north-C",
      "value": {
        "attributes": {
          "Name": "North exterior wall C",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              10000,
              6000,
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
            "depth": 3200,
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
        "id": "wall-north-C",
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
      "operation_id": "add-wall-corridor-offA",
      "target_id": "wall-corridor-offA",
      "value": {
        "attributes": {
          "Name": "Corridor-Office A wall",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              2000,
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
            "depth": 3200,
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
        "id": "wall-corridor-offA",
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
      "operation_id": "add-wall-corridor-offB",
      "target_id": "wall-corridor-offB",
      "value": {
        "attributes": {
          "Name": "Corridor-Office B wall",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              6000,
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
            "depth": 3200,
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
        "id": "wall-corridor-offB",
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
      "operation_id": "add-wall-corridor-offC",
      "target_id": "wall-corridor-offC",
      "value": {
        "attributes": {
          "Name": "Corridor-Office C wall",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              10000,
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
            "depth": 3200,
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
        "id": "wall-corridor-offC",
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
      "operation_id": "add-wall-offA-offB",
      "target_id": "wall-offA-offB",
      "value": {
        "attributes": {
          "Name": "Office A-Office B partition",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              4000,
              4000,
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
            "depth": 3200,
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
        "id": "wall-offA-offB",
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
      "operation_id": "add-wall-offB-offC",
      "target_id": "wall-offB-offC",
      "value": {
        "attributes": {
          "Name": "Office B-Office C partition",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              8000,
              4000,
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
            "depth": 3200,
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
        "id": "wall-offB-offC",
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
      "operation_id": "add-space-corridor",
      "target_id": "space-corridor",
      "value": {
        "attributes": {
          "InteriorOrExteriorSpace": "INTERNAL",
          "Name": "Corridor",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              6000,
              1000,
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
            "depth": 3200,
            "direction": [
              0,
              0,
              1
            ],
            "kind": "extruded_profile",
            "profile": {
              "kind": "rectangle",
              "x": 12000,
              "y": 2000
            }
          }
        },
        "id": "space-corridor",
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
      "operation_id": "add-space-officeA",
      "target_id": "space-officeA",
      "value": {
        "attributes": {
          "InteriorOrExteriorSpace": "INTERNAL",
          "Name": "Office A",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              2000,
              4000,
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
            "depth": 3200,
            "direction": [
              0,
              0,
              1
            ],
            "kind": "extruded_profile",
            "profile": {
              "kind": "rectangle",
              "x": 4000,
              "y": 4000
            }
          }
        },
        "id": "space-officeA",
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
      "operation_id": "add-space-officeB",
      "target_id": "space-officeB",
      "value": {
        "attributes": {
          "InteriorOrExteriorSpace": "INTERNAL",
          "Name": "Office B",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              6000,
              4000,
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
            "depth": 3200,
            "direction": [
              0,
              0,
              1
            ],
            "kind": "extruded_profile",
            "profile": {
              "kind": "rectangle",
              "x": 4000,
              "y": 4000
            }
          }
        },
        "id": "space-officeB",
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
      "operation_id": "add-space-officeC",
      "target_id": "space-officeC",
      "value": {
        "attributes": {
          "InteriorOrExteriorSpace": "INTERNAL",
          "Name": "Office C",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              10000,
              4000,
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
            "depth": 3200,
            "direction": [
              0,
              0,
              1
            ],
            "kind": "extruded_profile",
            "profile": {
              "kind": "rectangle",
              "x": 4000,
              "y": 4000
            }
          }
        },
        "id": "space-officeC",
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
      "operation_id": "add-opening-door-offA",
      "target_id": "opening-door-offA",
      "value": {
        "attributes": {
          "Name": "Opening for door offA",
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
            "relative_to": "wall-corridor-offA"
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
        "id": "opening-door-offA",
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
      "operation_id": "add-opening-door-offB",
      "target_id": "opening-door-offB",
      "value": {
        "attributes": {
          "Name": "Opening for door offB",
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
            "relative_to": "wall-corridor-offB"
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
        "id": "opening-door-offB",
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
      "operation_id": "add-opening-door-offC",
      "target_id": "opening-door-offC",
      "value": {
        "attributes": {
          "Name": "Opening for door offC",
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
            "relative_to": "wall-corridor-offC"
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
        "id": "opening-door-offC",
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
      "operation_id": "add-opening-door-main",
      "target_id": "opening-door-main",
      "value": {
        "attributes": {
          "Name": "Opening for main entrance door",
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
            "depth": 2200,
            "direction": [
              0,
              0,
              1
            ],
            "kind": "extruded_profile",
            "profile": {
              "kind": "rectangle",
              "x": 1600,
              "y": 200
            }
          }
        },
        "id": "opening-door-main",
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
      "operation_id": "add-opening-window-offA",
      "target_id": "opening-window-offA",
      "value": {
        "attributes": {
          "Name": "Opening for window offA",
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
            "relative_to": "wall-north-A"
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
              "x": 1800,
              "y": 200
            }
          }
        },
        "id": "opening-window-offA",
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
      "operation_id": "add-opening-window-offB",
      "target_id": "opening-window-offB",
      "value": {
        "attributes": {
          "Name": "Opening for window offB",
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
            "relative_to": "wall-north-B"
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
              "x": 1800,
              "y": 200
            }
          }
        },
        "id": "opening-window-offB",
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
      "operation_id": "add-opening-window-offC",
      "target_id": "opening-window-offC",
      "value": {
        "attributes": {
          "Name": "Opening for window offC",
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
            "relative_to": "wall-north-C"
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
              "x": 1800,
              "y": 200
            }
          }
        },
        "id": "opening-window-offC",
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
      "operation_id": "add-door-offA",
      "target_id": "door-offA",
      "value": {
        "attributes": {
          "Name": "Door offA",
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
            "relative_to": "opening-door-offA"
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
              "y": 100
            }
          }
        },
        "id": "door-offA",
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
      "operation_id": "add-door-offB",
      "target_id": "door-offB",
      "value": {
        "attributes": {
          "Name": "Door offB",
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
            "relative_to": "opening-door-offB"
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
              "y": 100
            }
          }
        },
        "id": "door-offB",
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
      "operation_id": "add-door-offC",
      "target_id": "door-offC",
      "value": {
        "attributes": {
          "Name": "Door offC",
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
            "relative_to": "opening-door-offC"
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
              "y": 100
            }
          }
        },
        "id": "door-offC",
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
      "operation_id": "add-door-main",
      "target_id": "door-main",
      "value": {
        "attributes": {
          "Name": "Main entrance door",
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
            "relative_to": "opening-door-main"
          },
          "OverallHeight": 2200,
          "OverallWidth": 1600,
          "Representation": {
            "depth": 2200,
            "direction": [
              0,
              0,
              1
            ],
            "kind": "extruded_profile",
            "profile": {
              "kind": "rectangle",
              "x": 1600,
              "y": 100
            }
          }
        },
        "id": "door-main",
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
      "operation_id": "add-window-offA",
      "target_id": "window-offA",
      "value": {
        "attributes": {
          "Name": "Window offA",
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
            "relative_to": "opening-window-offA"
          },
          "OverallHeight": 1200,
          "OverallWidth": 1800,
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
              "x": 1800,
              "y": 100
            }
          }
        },
        "id": "window-offA",
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
      "operation_id": "add-window-offB",
      "target_id": "window-offB",
      "value": {
        "attributes": {
          "Name": "Window offB",
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
            "relative_to": "opening-window-offB"
          },
          "OverallHeight": 1200,
          "OverallWidth": 1800,
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
              "x": 1800,
              "y": 100
            }
          }
        },
        "id": "window-offB",
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
      "operation_id": "add-window-offC",
      "target_id": "window-offC",
      "value": {
        "attributes": {
          "Name": "Window offC",
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
            "relative_to": "opening-window-offC"
          },
          "OverallHeight": 1200,
          "OverallWidth": 1800,
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
              "x": 1800,
              "y": 100
            }
          }
        },
        "id": "window-offC",
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
      "operation_id": "add-rel-voids-door-offA",
      "target_id": "rel-voids-door-offA",
      "value": {
        "attributes": {
          "RelatedOpeningElement": "opening-door-offA",
          "RelatingBuildingElement": "wall-corridor-offA"
        },
        "id": "rel-voids-door-offA",
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
      "operation_id": "add-rel-fills-door-offA",
      "target_id": "rel-fills-door-offA",
      "value": {
        "attributes": {
          "RelatedBuildingElement": "door-offA",
          "RelatingOpeningElement": "opening-door-offA"
        },
        "id": "rel-fills-door-offA",
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
      "operation_id": "add-rel-voids-door-offB",
      "target_id": "rel-voids-door-offB",
      "value": {
        "attributes": {
          "RelatedOpeningElement": "opening-door-offB",
          "RelatingBuildingElement": "wall-corridor-offB"
        },
        "id": "rel-voids-door-offB",
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
      "operation_id": "add-rel-fills-door-offB",
      "target_id": "rel-fills-door-offB",
      "value": {
        "attributes": {
          "RelatedBuildingElement": "door-offB",
          "RelatingOpeningElement": "opening-door-offB"
        },
        "id": "rel-fills-door-offB",
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
      "operation_id": "add-rel-voids-door-offC",
      "target_id": "rel-voids-door-offC",
      "value": {
        "attributes": {
          "RelatedOpeningElement": "opening-door-offC",
          "RelatingBuildingElement": "wall-corridor-offC"
        },
        "id": "rel-voids-door-offC",
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
      "operation_id": "add-rel-fills-door-offC",
      "target_id": "rel-fills-door-offC",
      "value": {
        "attributes": {
          "RelatedBuildingElement": "door-offC",
          "RelatingOpeningElement": "opening-door-offC"
        },
        "id": "rel-fills-door-offC",
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
      "operation_id": "add-rel-voids-door-main",
      "target_id": "rel-voids-door-main",
      "value": {
        "attributes": {
          "RelatedOpeningElement": "opening-door-main",
          "RelatingBuildingElement": "wall-south"
        },
        "id": "rel-voids-door-main",
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
      "operation_id": "add-rel-fills-door-main",
      "target_id": "rel-fills-door-main",
      "value": {
        "attributes": {
          "RelatedBuildingElement": "door-main",
          "RelatingOpeningElement": "opening-door-main"
        },
        "id": "rel-fills-door-main",
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
      "operation_id": "add-rel-voids-window-offA",
      "target_id": "rel-voids-window-offA",
      "value": {
        "attributes": {
          "RelatedOpeningElement": "opening-window-offA",
          "RelatingBuildingElement": "wall-north-A"
        },
        "id": "rel-voids-window-offA",
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
      "operation_id": "add-rel-fills-window-offA",
      "target_id": "rel-fills-window-offA",
      "value": {
        "attributes": {
          "RelatedBuildingElement": "window-offA",
          "RelatingOpeningElement": "opening-window-offA"
        },
        "id": "rel-fills-window-offA",
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
      "operation_id": "add-rel-voids-window-offB",
      "target_id": "rel-voids-window-offB",
      "value": {
        "attributes": {
          "RelatedOpeningElement": "opening-window-offB",
          "RelatingBuildingElement": "wall-north-B"
        },
        "id": "rel-voids-window-offB",
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
      "operation_id": "add-rel-fills-window-offB",
      "target_id": "rel-fills-window-offB",
      "value": {
        "attributes": {
          "RelatedBuildingElement": "window-offB",
          "RelatingOpeningElement": "opening-window-offB"
        },
        "id": "rel-fills-window-offB",
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
      "operation_id": "add-rel-voids-window-offC",
      "target_id": "rel-voids-window-offC",
      "value": {
        "attributes": {
          "RelatedOpeningElement": "opening-window-offC",
          "RelatingBuildingElement": "wall-north-C"
        },
        "id": "rel-voids-window-offC",
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
      "operation_id": "add-rel-fills-window-offC",
      "target_id": "rel-fills-window-offC",
      "value": {
        "attributes": {
          "RelatedBuildingElement": "window-offC",
          "RelatingOpeningElement": "opening-window-offC"
        },
        "id": "rel-fills-window-offC",
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
      "operation_id": "add-ground-floor-slab",
      "target_id": "ground-floor-slab",
      "value": {
        "attributes": {
          "Name": "Ground Floor Slab",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              6000,
              3000,
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
              "x": 12000,
              "y": 6000
            }
          }
        },
        "id": "ground-floor-slab",
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
      "artifact_dir": "package-01-package-storey-1",
      "attempt_count": 1,
      "candidate_hash": "sha256:eb9b715cf6a7f04b2d5f699f3cec78ac5c34e6839490f3cadc9e941f4036273c",
      "classification": "changeset",
      "frozen_component_count": 7,
      "gate_issue_count": 0,
      "package_id": "package-storey-1",
      "pre_apply_status": "partial_not_formal",
      "response_id": "0265527a-42e7-47f8-8a9c-a6fa405a0f2b",
      "revision_id": "revision-01",
      "status": "accepted"
    },
    {
      "artifact_dir": "package-02-package-cross-storey",
      "attempt_count": 1,
      "candidate_hash": "sha256:dc764c0e05a2762c4133ce38609de599d7415e4ffaa3c84777d8fe00d9a3c208",
      "classification": "changeset",
      "frozen_component_count": 50,
      "gate_issue_count": 0,
      "package_id": "package-cross-storey",
      "pre_apply_status": "partial_not_formal",
      "response_id": "27716f2e-14bb-4b23-a8e3-671f1068617a",
      "revision_id": "revision-02",
      "status": "accepted"
    }
  ],
  "preservation": {
    "changed_ids": [
      "door-main",
      "door-offA",
      "door-offB",
      "door-offC",
      "ground-floor-slab",
      "opening-door-main",
      "opening-door-offA",
      "opening-door-offB",
      "opening-door-offC",
      "opening-window-offA",
      "opening-window-offB",
      "opening-window-offC",
      "rel-fills-door-main",
      "rel-fills-door-offA",
      "rel-fills-door-offB",
      "rel-fills-door-offC",
      "rel-fills-window-offA",
      "rel-fills-window-offB",
      "rel-fills-window-offC",
      "rel-voids-door-main",
      "rel-voids-door-offA",
      "rel-voids-door-offB",
      "rel-voids-door-offC",
      "rel-voids-window-offA",
      "rel-voids-window-offB",
      "rel-voids-window-offC",
      "space-corridor",
      "space-officeA",
      "space-officeB",
      "space-officeC",
      "wall-corridor-offA",
      "wall-corridor-offB",
      "wall-corridor-offC",
      "wall-east",
      "wall-north-A",
      "wall-north-B",
      "wall-north-C",
      "wall-offA-offB",
      "wall-offB-offC",
      "wall-south",
      "wall-west",
      "window-offA",
      "window-offB",
      "window-offC"
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
    "candidate_hash": "sha256:dc764c0e05a2762c4133ce38609de599d7415e4ffaa3c84777d8fe00d9a3c208",
    "component_hashes": {
      "aggregate-building-storeys": "sha256:65533f589d3960284939c18a5b6948d97fecb2094dc0b461825c0f40d57076bf",
      "aggregate-project-site": "sha256:456b0a2ec791c6c20d7efdda199726d8f9df127fd2739962aceb07dacb1f2567",
      "aggregate-site-building": "sha256:9ccdeec022f78745ceb756d48903226706f909c0db1992457f23fffca5da02d4",
      "building-main": "sha256:d2fac45e699944c2dd75aeb376ce156232c45dac25ab318fdc2a4593028a14ad",
      "door-main": "sha256:7f200c7c306b1f27c226593b90c6dd2b36b41fe4f34eb2452ec9811aab26f417",
      "door-offA": "sha256:f6dc5d13886795f05a32acfdf9dd83c1c84720dfea1989ee6accf004ed3f4405",
      "door-offB": "sha256:e0e0ada225eedf922c1ee264c0d4c9618fe0c0b556fab1fdb762a110e6dbc446",
      "door-offC": "sha256:dfd6fbecb7b2d99a8f7f76e5151153a6b1e05f10787359079105262ca71493f0",
      "ground-floor-slab": "sha256:435ffcf5ef63bcd9b65f5a0e222afc6ce95529e3932c53d747922ac9335ab809",
      "opening-door-main": "sha256:7aaef3d91036c1d53149a7b82979a15c2dedfca3acccaba5270fae7b1b973916",
      "opening-door-offA": "sha256:4729d536e6bb69f918409eeccda5ebd9d6782b111622682d717573d3ef2d5a38",
      "opening-door-offB": "sha256:8a9f7a8af27599de4c4eabd862505203caa58a3b637ccad6f789df269726d5de",
      "opening-door-offC": "sha256:2113b43e613196a944b33e9e49cdbed0246c01c229264247d2200a8304a90012",
      "opening-window-offA": "sha256:a643a3674996818383c9314c0333e50849afb1f151bc90cea87b39b856c49cd9",
      "opening-window-offB": "sha256:6893414065fd20d60ee55f7cc19fa9fbb3e773501c0802ed4472c013f89a28c4",
      "opening-window-offC": "sha256:59b7287ac6ecf19574a8a2a999e842576bd1296baf84eac7c0c08966d5aff815",
      "project-main": "sha256:9b165163ddbb7d9c4ae8832db8391cf20e41cb9bdd4b1d99f6a3e6cb78a071d1",
      "rel-fills-door-main": "sha256:76fc7b0c10a937f4c952de1bf1d949192382cc7dce75b7d14c37d5ce9afe7d61",
      "rel-fills-door-offA": "sha256:35e5089d09d1a69cbd386c3d6ecd15bdd4186101988d7a776082b2bacd7c82b7",
      "rel-fills-door-offB": "sha256:bec2f50d20e837c60debe28489c95071df1df1bdebe5a43fd35c651e044589d4",
      "rel-fills-door-offC": "sha256:0fc61b35de3c70e4afb24e652104324033c1bf42804ef916d785541c12e9bf5c",
      "rel-fills-window-offA": "sha256:63a48acbdfb0866e6ad9c5d5084f47eb8602b71506c0122a8d9aa2b8a037d825",
      "rel-fills-window-offB": "sha256:83376f546cdc1bd950854a5c8ef7407d685bc510e496d34bcada5872d99797dd",
      "rel-fills-window-offC": "sha256:18055f5eef53db4cdd92d0105b7fee0ca1921716f5b4203c3800d41d5d7e41d7",
      "rel-voids-door-main": "sha256:b864ab6d46a53155cbdfa06815f213c6a9a1629b832e7083672dbb183c0b0cab",
      "rel-voids-door-offA": "sha256:9f99c545a9a53b857d7fb15a270d760e1ffacfd8a3c9642f2bb15aa2e386347d",
      "rel-voids-door-offB": "sha256:fbde6ce2949f895bcd39b8bff606d9775f90cb3ebb5c950da21c05860bde00e2",
      "rel-voids-door-offC": "sha256:387e824bbb63826560066993841794fb727a6590377d48b495b161e853ec54ea",
      "rel-voids-window-offA": "sha256:468f008b29d11a173ba622acf89df4fd9fcfd2a6573cfd756c667f727ff59101",
      "rel-voids-window-offB": "sha256:850cd42c05fbf1544d0e7d007aa7a08e5899eb2b8a2d7b453897345bd4780f3e",
      "rel-voids-window-offC": "sha256:969867741bcad095f6be8c07eb2563669c2cded1836f82a96eed6885871e889f",
      "site-main": "sha256:d5dfa3ad348be9625c631e2a45e4f77a67a485791c961139b0c18d37314ff3e5",
      "space-corridor": "sha256:17c25a9c8df1eadc2b1c218dccc0b8afd3e024e7fc7c0c3acc0dde6debda1f25",
      "space-officeA": "sha256:b12cda116d31e294be1e36b5d03d25a0fbc453df47326746711a96057883a8bb",
      "space-officeB": "sha256:ddf0935887a8733030bff4872e21498efdcd9c80eee186df584ed719c88ce4b1",
      "space-officeC": "sha256:bdbfb7937c4c27705eea874eca028c3c1d43348bbfa16ade05acf40f5261a031",
      "storey-1": "sha256:445101f943e94fa6b4db23df291698553632cc8a788eb9273420c21e3fa05f9d",
      "wall-corridor-offA": "sha256:baf343028051dd092e6afc75b50910fdfc8f68bf3fb23dd9855b0ad15c126d74",
      "wall-corridor-offB": "sha256:243a691f811781a526953e81d079aa3bf7468e9ea7a79f51b15ab05f4b080eda",
      "wall-corridor-offC": "sha256:dd18279a4a658c4e9577ceb9e2f35116b6356d8f74968e058e81e2bf25180332",
      "wall-east": "sha256:283cfcda84d5d248bd5fb0e797b3f99df3091514811b7b8c7e571bf9474917f6",
      "wall-north-A": "sha256:ce713aa85a10cd200b6cd866db88294bdae622c34a51fb536da65cf421c740ff",
      "wall-north-B": "sha256:37940d14d7bb0cfd52758557daf21d9a0ff1f53b55fed371412a507de12162b7",
      "wall-north-C": "sha256:72ba7902c40cc8eab3da2f11d779acfc87f7adf38131352915fbef022f9c41a6",
      "wall-offA-offB": "sha256:8a8f46c6eecd93a6d709dc7d82aec15f053c665a6d236f010e931bff6edc823c",
      "wall-offB-offC": "sha256:532254c6bfaa9110f68e11cb8bd38242fd604d917c789c24adbaf7b20483bf4c",
      "wall-south": "sha256:57f4d952d41df14f3e98e95e1d1d89cdf5ffb0856629732ac0b4a79fd0e81f95",
      "wall-west": "sha256:bc6eaccd2c4f6af643e182f5696ef1d3f6d5524e16ab24a2b62f36f9f52c0749",
      "window-offA": "sha256:5ad41188e3db2ce66ba5472d0d92d89e8ca22105763b618582f0f53357e11f4d",
      "window-offB": "sha256:189f66f4571b909db67922a704359762bde3e48c5c62c398921becfe1e56c759",
      "window-offC": "sha256:e32845d9be96e64c4c046a780c5b417cfff532e275ec3ea7227038d603bad5cd"
    },
    "expected_facts_hash": "sha256:39749bcb3b8fcf042532901f69c1823e1575df805f8507d26da373414249661d",
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

- [runs/8c8ef9a111e326d7/session-export.json](runs/8c8ef9a111e326d7/session-export.json)

## Session DB Evidence

### Events

```json
[
  {
    "created_at": "2026-07-16T09:52:56+00:00",
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
    "created_at": "2026-07-16T09:55:45+00:00",
    "event_index": 1,
    "event_type": "generator_completed",
    "payload": {
      "case_id": "8c8ef9a111e326d7",
      "classification": "formal",
      "contract_valid": true,
      "evidence_class": "provider-backed-staged",
      "output_dir": "dataset\\processed\\agent-demo\\phase6.6-medium-live-64k-fix2\\runs\\8c8ef9a111e326d7\\generator",
      "response_id": "27716f2e-14bb-4b23-a8e3-671f1068617a",
      "stage": "generate",
      "status": "formal",
      "strict_output_contract_valid": true,
      "valid": true
    }
  },
  {
    "created_at": "2026-07-16T09:55:45+00:00",
    "event_index": 2,
    "event_type": "semantic_coverage_completed",
    "payload": {
      "blocking_fact_count": 0,
      "capability_profile_hash": "sha256:1a9b5d81e65c07e3b578782744596bd9a56eb1ecf9702c94dbde5fd91681bbb5",
      "capability_profile_id": "text2ifc/semantic-capabilities/ifc2x3-bim-json-2.0/1.0",
      "case_id": "8c8ef9a111e326d7",
      "coverage": {
        "blocking_facts": [],
        "candidate_entity_count": 34,
        "capability_profile_hash": "sha256:1a9b5d81e65c07e3b578782744596bd9a56eb1ecf9702c94dbde5fd91681bbb5",
        "capability_profile_id": "text2ifc/semantic-capabilities/ifc2x3-bim-json-2.0/1.0",
        "case_id": "8c8ef9a111e326d7",
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
                "id": "ground-floor-slab",
                "polygon": [
                  [
                    0,
                    0
                  ],
                  [
                    12000,
                    0
                  ],
                  [
                    12000,
                    6000
                  ],
                  [
                    0,
                    6000
                  ],
                  [
                    0,
                    0
                  ]
                ],
                "storey": "storey-1",
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
                    "host_wall": "wall-corridor-offA",
                    "id": "door-offA",
                    "width_mm": 900
                  },
                  {
                    "alignment": "host_centerline",
                    "height_mm": 2100,
                    "host_wall": "wall-corridor-offB",
                    "id": "door-offB",
                    "width_mm": 900
                  },
                  {
                    "alignment": "host_centerline",
                    "height_mm": 2100,
                    "host_wall": "wall-corridor-offC",
                    "id": "door-offC",
                    "width_mm": 900
                  },
                  {
                    "alignment": "host_centerline",
                    "height_mm": 2200,
                    "host_wall": "wall-south",
                    "id": "door-main",
                    "width_mm": 1600
                  }
                ],
                "elevation_mm": 0,
                "id": "storey-1",
                "net_height_mm": 3200,
                "spaces": [
                  {
                    "bounds": {
                      "x": [
                        0,
                        12000
                      ],
                      "y": [
                        0,
                        2000
                      ]
                    },
                    "id": "space-corridor"
                  },
                  {
                    "bounds": {
                      "x": [
                        0,
                        4000
                      ],
                      "y": [
                        2000,
                        6000
                      ]
                    },
                    "id": "space-officeA"
                  },
                  {
                    "bounds": {
                      "x": [
                        4000,
                        8000
                      ],
                      "y": [
                        2000,
                        6000
                      ]
                    },
                    "id": "space-officeB"
                  },
                  {
                    "bounds": {
                      "x": [
                        8000,
                        12000
                      ],
                      "y": [
                        2000,
                        6000
                      ]
                    },
                    "id": "space-officeC"
                  }
                ],
                "walls": {
                  "exterior": [
                    {
                      "end_mm": [
                        0,
                        6000
                      ],
                      "height_mm": 3200,
                      "id": "wall-west",
                      "start_mm": [
                        0,
                        0
                      ],
                      "thickness_mm": 200
                    },
                    {
                      "end_mm": [
                        12000,
                        6000
                      ],
                      "height_mm": 3200,
                      "id": "wall-east",
                      "start_mm": [
                        12000,
                        0
                      ],
                      "thickness_mm": 200
                    },
                    {
                      "end_mm": [
                        12000,
                        0
                      ],
                      "height_mm": 3200,
                      "id": "wall-south",
                      "start_mm": [
                        0,
                        0
                      ],
                      "thickness_mm": 200
                    },
                    {
                      "end_mm": [
                        4000,
                        6000
                      ],
                      "height_mm": 3200,
                      "id": "wall-north-A",
                      "start_mm": [
                        0,
                        6000
                      ],
                      "thickness_mm": 200
                    },
                    {
                      "end_mm": [
                        8000,
                        6000
                      ],
                      "height_mm": 3200,
                      "id": "wall-north-B",
                      "start_mm": [
                        4000,
                        6000
                      ],
                      "thickness_mm": 200
                    },
                    {
                      "end_mm": [
                        12000,
                        6000
                      ],
                      "height_mm": 3200,
                      "id": "wall-north-C",
                      "start_mm": [
                        8000,
                        6000
                      ],
                      "thickness_mm": 200
                    }
                  ],
                  "interior": [
                    {
                      "connects": [
                        "space-corridor",
                        "space-officeA"
                      ],
                      "end_mm": [
                        4000,
                        2000
                      ],
                      "height_mm": 3200,
                      "id": "wall-corridor-offA",
                      "start_mm": [
                        0,
                        2000
                      ],
                      "thickness_mm": 200
                    },
                    {
                      "connects": [
                        "space-corridor",
                        "space-officeB"
                      ],
                      "end_mm": [
                        8000,
                        2000
                      ],
                      "height_mm": 3200,
                      "id": "wall-corridor-offB",
                      "start_mm": [
                        4000,
                        2000
                      ],
                      "thickness_mm": 200
                    },
                    {
                      "connects": [
                        "space-corridor",
                        "space-officeC"
                      ],
                      "end_mm": [
                        12000,
                        2000
                      ],
                      "height_mm": 3200,
                      "id": "wall-corridor-offC",
                      "start_mm": [
                        8000,
                        2000
                      ],
                      "thickness_mm": 200
                    },
                    {
                      "connects": [
                        "space-officeA",
                        "space-officeB"
                      ],
                      "end_mm": [
                        4000,
                        6000
                      ],
                      "height_mm": 3200,
                      "id": "wall-offA-offB",
                      "start_mm": [
                        4000,
                        2000
                      ],
                      "thickness_mm": 200
                    },
                    {
                      "connects": [
                        "space-officeB",
                        "space-officeC"
                      ],
                      "end_mm": [
                        8000,
                        6000
                      ],
                      "height_mm": 3200,
                      "id": "wall-offB-offC",
                      "start_mm": [
                        8000,
                        2000
                      ],
                      "thickness_mm": 200
                    }
                  ]
                },
                "windows": [
                  {
                    "alignment": "host_centerline",
                    "height_mm": 1200,
                    "host_wall": "wall-north-A",
                    "id": "window-offA",
                    "sill_height_mm": 900,
                    "width_mm": 1800
                  },
                  {
                    "alignment": "host_centerline",
                    "height_mm": 1200,
                    "host_wall": "wall-north-B",
                    "id": "window-offB",
                    "sill_height_mm": 900,
                    "width_mm": 1800
                  },
                  {
                    "alignment": "host_centerline",
                    "height_mm": 1200,
                    "host_wall": "wall-north-C",
                    "id": "window-offC",
                    "sill_height_mm": 900,
                    "width_mm": 1800
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
    "created_at": "2026-07-16T09:55:45+00:00",
    "event_index": 3,
    "event_type": "repair_completed",
    "payload": {
      "case_id": "8c8ef9a111e326d7",
      "evidence_class": "live-derived-no-call",
      "output_dir": "dataset/processed/agent-demo/phase6.6-medium-live-64k-fix2/runs/8c8ef9a111e326d7/repair",
      "provider_call_count": 0,
      "repair_attempts": [],
      "route": "no_repair_needed",
      "source_generator_response_id": "27716f2e-14bb-4b23-a8e3-671f1068617a",
      "stage": "repair",
      "valid": true
    }
  },
  {
    "created_at": "2026-07-16T09:55:47+00:00",
    "event_index": 4,
    "event_type": "candidate_gates_completed",
    "payload": {
      "case_id": "8c8ef9a111e326d7",
      "compile_reopen_success": true,
      "deterministic_gates_passed": true,
      "gate_summary": {
        "artifact_hashes": {
          "dynamic-gates.json": "6365c09a6ca90f70cd0b245c6851ec459c2f08d3eeb219581b4656ad2fdfd7d8",
          "expected-facts.json": "39749bcb3b8fcf042532901f69c1823e1575df805f8507d26da373414249661d",
          "generator/candidate.json": "dc764c0e05a2762c4133ce38609de599d7415e4ffaa3c84777d8fe00d9a3c208",
          "generator/validation.json": "6be6595f4f77090199203073905e3755e4015ff1a83b3412d64571cd872b4c41",
          "geometry-feedback.json": "50e250ce222e0ba6485143241886e5932bf5e29c1aa3b9d6f1216c93a3161df8",
          "ifc-verification.json": "013d1c8bf5fb348c5c120239e1dc80696aff8ad0dab84cc83de8db9640ad9082",
          "repair/route.json": "6f18ada43dcd4eb0b005247e9226d3bb5967443b19e80fdb7cda3bae5be526d4",
          "semantic-coverage.json": "0f4d6bd2b810232c9f57654c06376c3422b70f9781fbebb98220af68817da438"
        },
        "candidate_hash": "dc764c0e05a2762c4133ce38609de599d7415e4ffaa3c84777d8fe00d9a3c208",
        "candidate_path": "generator/candidate.json",
        "case_id": "8c8ef9a111e326d7",
        "evidence": {
          "compile_reopen": {
            "ifc_issues": [],
            "input_issues": [],
            "output_path": "dataset\\processed\\agent-demo\\phase6.6-medium-live-64k-fix2\\runs\\8c8ef9a111e326d7\\output.ifc",
            "success": true
          },
          "geometry": {
            "expectation_source": "design_brief_expected_facts",
            "issues": [],
            "metrics": {
              "case_id": "8c8ef9a111e326d7",
              "floor_openings": {},
              "roof": {},
              "slabs": {
                "ground-floor-slab": {
                  "bbox": {
                    "x": [
                      0.0,
                      12.0
                    ],
                    "y": [
                      0.0,
                      6.0
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
                "space-corridor": {
                  "bbox": {
                    "x": [
                      0.0,
                      12.0
                    ],
                    "y": [
                      0.0,
                      2.0
                    ],
                    "z": [
                      0.0,
                      3.2
                    ]
                  },
                  "ifc_class": "IfcSpace"
                },
                "space-officeA": {
                  "bbox": {
                    "x": [
                      0.0,
                      4.0
                    ],
                    "y": [
                      2.0,
                      6.0
                    ],
                    "z": [
                      0.0,
                      3.2
                    ]
                  },
                  "ifc_class": "IfcSpace"
                },
                "space-officeB": {
                  "bbox": {
                    "x": [
                      4.0,
                      8.0
                    ],
                    "y": [
                      2.0,
                      6.0
                    ],
                    "z": [
                      0.0,
                      3.2
                    ]
                  },
                  "ifc_class": "IfcSpace"
                },
                "space-officeC": {
                  "bbox": {
                    "x": [
                      8.0,
                      12.0
                    ],
                    "y": [
                      2.0,
                      6.0
                    ],
                    "z": [
                      0.0,
                      3.2
                    ]
                  },
                  "ifc_class": "IfcSpace"
                }
              },
              "stairs": {},
              "wall_set_convention": "primary",
              "walls": {
                "wall-corridor-offA": {
                  "axis": "x",
                  "bbox": {
                    "x": [
                      0.0,
                      4.0
                    ],
                    "y": [
                      1.9,
                      2.1
                    ],
                    "z": [
                      0.0,
                      3.2
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-corridor-offB": {
                  "axis": "x",
                  "bbox": {
                    "x": [
                      4.0,
                      8.0
                    ],
                    "y": [
                      1.9,
                      2.1
                    ],
                    "z": [
                      0.0,
                      3.2
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-corridor-offC": {
                  "axis": "x",
                  "bbox": {
                    "x": [
                      8.0,
                      12.0
                    ],
                    "y": [
                      1.9,
                      2.1
                    ],
                    "z": [
                      0.0,
                      3.2
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-east": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      11.9,
                      12.1
                    ],
                    "y": [
                      0.0,
                      6.0
                    ],
                    "z": [
                      0.0,
                      3.2
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-north-A": {
                  "axis": "x",
                  "bbox": {
                    "x": [
                      0.0,
                      4.0
                    ],
                    "y": [
                      5.9,
                      6.1
                    ],
                    "z": [
                      0.0,
                      3.2
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-north-B": {
                  "axis": "x",
                  "bbox": {
                    "x": [
                      4.0,
                      8.0
                    ],
                    "y": [
                      5.9,
                      6.1
                    ],
                    "z": [
                      0.0,
                      3.2
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-north-C": {
                  "axis": "x",
                  "bbox": {
                    "x": [
                      8.0,
                      12.0
                    ],
                    "y": [
                      5.9,
                      6.1
                    ],
                    "z": [
                      0.0,
                      3.2
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-offA-offB": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      3.9,
                      4.1
                    ],
                    "y": [
                      2.0,
                      6.0
                    ],
                    "z": [
                      0.0,
                      3.2
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-offB-offC": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      7.9,
                      8.1
                    ],
                    "y": [
                      2.0,
                      6.0
                    ],
                    "z": [
                      0.0,
                      3.2
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-south": {
                  "axis": "x",
                  "bbox": {
                    "x": [
                      0.0,
                      12.0
                    ],
                    "y": [
                      -0.1,
                      0.1
                    ],
                    "z": [
                      0.0,
                      3.2
                    ]
                  },
                  "ifc_class": "IfcWall"
                },
                "wall-west": {
                  "axis": "y",
                  "bbox": {
                    "x": [
                      -0.1,
                      0.1
                    ],
                    "y": [
                      0.0,
                      6.0
                    ],
                    "z": [
                      0.0,
                      3.2
                    ]
                  },
                  "ifc_class": "IfcWall"
                }
              }
            },
            "success": true
          },
          "repair_history": {
            "case_id": "8c8ef9a111e326d7",
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
            "source_generator_dir": "dataset/processed/agent-demo/phase6.6-medium-live-64k-fix2/runs/8c8ef9a111e326d7/generator",
            "source_generator_response_id": "27716f2e-14bb-4b23-a8e3-671f1068617a",
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
            "candidate_entity_count": 34,
            "capability_profile_hash": "sha256:1a9b5d81e65c07e3b578782744596bd9a56eb1ecf9702c94dbde5fd91681bbb5",
            "capability_profile_id": "text2ifc/semantic-capabilities/ifc2x3-bim-json-2.0/1.0",
            "case_id": "8c8ef9a111e326d7",
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
                    "id": "ground-floor-slab",
                    "polygon": [
                      [
                        0,
                        0
                      ],
                      [
                        12000,
                        0
                      ],
                      [
                        12000,
                        6000
                      ],
                      [
                        0,
                        6000
                      ],
                      [
                        0,
                        0
                      ]
                    ],
                    "storey": "storey-1",
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
                        "host_wall": "wall-corridor-offA",
                        "id": "door-offA",
                        "width_mm": 900
                      },
                      {
                        "alignment": "host_centerline",
                        "height_mm": 2100,
                        "host_wall": "wall-corridor-offB",
                        "id": "door-offB",
                        "width_mm": 900
                      },
                      {
                        "alignment": "host_centerline",
                        "height_mm": 2100,
                        "host_wall": "wall-corridor-offC",
                        "id": "door-offC",
                        "width_mm": 900
                      },
                      {
                        "alignment": "host_centerline",
                        "height_mm": 2200,
                        "host_wall": "wall-south",
                        "id": "door-main",
                        "width_mm": 1600
                      }
                    ],
                    "elevation_mm": 0,
                    "id": "storey-1",
                    "net_height_mm": 3200,
                    "spaces": [
                      {
                        "bounds": {
                          "x": [
                            0,
                            12000
                          ],
                          "y": [
                            0,
                            2000
                          ]
                        },
                        "id": "space-corridor"
                      },
                      {
                        "bounds": {
                          "x": [
                            0,
                            4000
                          ],
                          "y": [
                            2000,
                            6000
                          ]
                        },
                        "id": "space-officeA"
                      },
                      {
                        "bounds": {
                          "x": [
                            4000,
                            8000
                          ],
                          "y": [
                            2000,
                            6000
                          ]
                        },
                        "id": "space-officeB"
                      },
                      {
                        "bounds": {
                          "x": [
                            8000,
                            12000
                          ],
                          "y": [
                            2000,
                            6000
                          ]
                        },
                        "id": "space-officeC"
                      }
                    ],
                    "walls": {
                      "exterior": [
                        {
                          "end_mm": [
                            0,
                            6000
                          ],
                          "height_mm": 3200,
                          "id": "wall-west",
                          "start_mm": [
                            0,
                            0
                          ],
                          "thickness_mm": 200
                        },
                        {
                          "end_mm": [
                            12000,
                            6000
                          ],
                          "height_mm": 3200,
                          "id": "wall-east",
                          "start_mm": [
                            12000,
                            0
                          ],
                          "thickness_mm": 200
                        },
                        {
                          "end_mm": [
                            12000,
                            0
                          ],
                          "height_mm": 3200,
                          "id": "wall-south",
                          "start_mm": [
                            0,
                            0
                          ],
                          "thickness_mm": 200
                        },
                        {
                          "end_mm": [
                            4000,
                            6000
                          ],
                          "height_mm": 3200,
                          "id": "wall-north-A",
                          "start_mm": [
                            0,
                            6000
                          ],
                          "thickness_mm": 200
                        },
                        {
                          "end_mm": [
                            8000,
                            6000
                          ],
                          "height_mm": 3200,
                          "id": "wall-north-B",
                          "start_mm": [
                            4000,
                            6000
                          ],
                          "thickness_mm": 200
                        },
                        {
                          "end_mm": [
                            12000,
                            6000
                          ],
                          "height_mm": 3200,
                          "id": "wall-north-C",
                          "start_mm": [
                            8000,
                            6000
                          ],
                          "thickness_mm": 200
                        }
                      ],
                      "interior": [
                        {
                          "connects": [
                            "space-corridor",
                            "space-officeA"
                          ],
                          "end_mm": [
                            4000,
                            2000
                          ],
                          "height_mm": 3200,
                          "id": "wall-corridor-offA",
                          "start_mm": [
                            0,
                            2000
                          ],
                          "thickness_mm": 200
                        },
                        {
                          "connects": [
                            "space-corridor",
                            "space-officeB"
                          ],
                          "end_mm": [
                            8000,
                            2000
                          ],
                          "height_mm": 3200,
                          "id": "wall-corridor-offB",
                          "start_mm": [
                            4000,
                            2000
                          ],
                          "thickness_mm": 200
                        },
                        {
                          "connects": [
                            "space-corridor",
                            "space-officeC"
                          ],
                          "end_mm": [
                            12000,
                            2000
                          ],
                          "height_mm": 3200,
                          "id": "wall-corridor-offC",
                          "start_mm": [
                            8000,
                            2000
                          ],
                          "thickness_mm": 200
                        },
                        {
                          "connects": [
                            "space-officeA",
                            "space-officeB"
                          ],
                          "end_mm": [
                            4000,
                            6000
                          ],
                          "height_mm": 3200,
                          "id": "wall-offA-offB",
                          "start_mm": [
                            4000,
                            2000
                          ],
                          "thickness_mm": 200
                        },
                        {
                          "connects": [
                            "space-officeB",
                            "space-officeC"
                          ],
                          "end_mm": [
                            8000,
                            6000
                          ],
                          "height_mm": 3200,
                          "id": "wall-offB-offC",
                          "start_mm": [
                            8000,
                            2000
                          ],
                          "thickness_mm": 200
                        }
                      ]
                    },
                    "windows": [
                      {
                        "alignment": "host_centerline",
                        "height_mm": 1200,
                        "host_wall": "wall-north-A",
                        "id": "window-offA",
                        "sill_height_mm": 900,
                        "width_mm": 1800
                      },
                      {
                        "alignment": "host_centerline",
                        "height_mm": 1200,
                        "host_wall": "wall-north-B",
                        "id": "window-offB",
                        "sill_height_mm": 900,
                        "width_mm": 1800
                      },
                      {
                        "alignment": "host_centerline",
                        "height_mm": 1200,
                        "host_wall": "wall-north-C",
                        "id": "window-offC",
                        "sill_height_mm": 900,
                        "width_mm": 1800
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
        "expected_facts_hash": "39749bcb3b8fcf042532901f69c1823e1575df805f8507d26da373414249661d",
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
                "candidate_id": "door-offA",
                "collection": "doors",
                "expected_id": "door-offA",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "door-offB",
                "collection": "doors",
                "expected_id": "door-offB",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "door-offC",
                "collection": "doors",
                "expected_id": "door-offC",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "door-main",
                "collection": "doors",
                "expected_id": "door-main",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "space-corridor",
                "collection": "spaces",
                "expected_id": "space-corridor",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "space-officeA",
                "collection": "spaces",
                "expected_id": "space-officeA",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "space-officeB",
                "collection": "spaces",
                "expected_id": "space-officeB",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "space-officeC",
                "collection": "spaces",
                "expected_id": "space-officeC",
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
                "candidate_id": "wall-south",
                "collection": "walls",
                "expected_id": "wall-south",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-north-A",
                "collection": "walls",
                "expected_id": "wall-north-A",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-north-B",
                "collection": "walls",
                "expected_id": "wall-north-B",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-north-C",
                "collection": "walls",
                "expected_id": "wall-north-C",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-corridor-offA",
                "collection": "walls",
                "expected_id": "wall-corridor-offA",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-corridor-offB",
                "collection": "walls",
                "expected_id": "wall-corridor-offB",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-corridor-offC",
                "collection": "walls",
                "expected_id": "wall-corridor-offC",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-offA-offB",
                "collection": "walls",
                "expected_id": "wall-offA-offB",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "wall-offB-offC",
                "collection": "walls",
                "expected_id": "wall-offB-offC",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "window-offA",
                "collection": "windows",
                "expected_id": "window-offA",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "window-offB",
                "collection": "windows",
                "expected_id": "window-offB",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "window-offC",
                "collection": "windows",
                "expected_id": "window-offC",
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
        "expectation_source": "design_brief_expected_facts",
        "issues": [],
        "metrics": {
          "case_id": "8c8ef9a111e326d7",
          "floor_openings": {},
          "roof": {},
          "slabs": {
            "ground-floor-slab": {
              "bbox": {
                "x": [
                  0.0,
                  12.0
                ],
                "y": [
                  0.0,
                  6.0
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
            "space-corridor": {
              "bbox": {
                "x": [
                  0.0,
                  12.0
                ],
                "y": [
                  0.0,
                  2.0
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "ifc_class": "IfcSpace"
            },
            "space-officeA": {
              "bbox": {
                "x": [
                  0.0,
                  4.0
                ],
                "y": [
                  2.0,
                  6.0
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "ifc_class": "IfcSpace"
            },
            "space-officeB": {
              "bbox": {
                "x": [
                  4.0,
                  8.0
                ],
                "y": [
                  2.0,
                  6.0
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "ifc_class": "IfcSpace"
            },
            "space-officeC": {
              "bbox": {
                "x": [
                  8.0,
                  12.0
                ],
                "y": [
                  2.0,
                  6.0
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "ifc_class": "IfcSpace"
            }
          },
          "stairs": {},
          "wall_set_convention": "primary",
          "walls": {
            "wall-corridor-offA": {
              "axis": "x",
              "bbox": {
                "x": [
                  0.0,
                  4.0
                ],
                "y": [
                  1.9,
                  2.1
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-corridor-offB": {
              "axis": "x",
              "bbox": {
                "x": [
                  4.0,
                  8.0
                ],
                "y": [
                  1.9,
                  2.1
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-corridor-offC": {
              "axis": "x",
              "bbox": {
                "x": [
                  8.0,
                  12.0
                ],
                "y": [
                  1.9,
                  2.1
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-east": {
              "axis": "y",
              "bbox": {
                "x": [
                  11.9,
                  12.1
                ],
                "y": [
                  0.0,
                  6.0
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-north-A": {
              "axis": "x",
              "bbox": {
                "x": [
                  0.0,
                  4.0
                ],
                "y": [
                  5.9,
                  6.1
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-north-B": {
              "axis": "x",
              "bbox": {
                "x": [
                  4.0,
                  8.0
                ],
                "y": [
                  5.9,
                  6.1
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-north-C": {
              "axis": "x",
              "bbox": {
                "x": [
                  8.0,
                  12.0
                ],
                "y": [
                  5.9,
                  6.1
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-offA-offB": {
              "axis": "y",
              "bbox": {
                "x": [
                  3.9,
                  4.1
                ],
                "y": [
                  2.0,
                  6.0
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-offB-offC": {
              "axis": "y",
              "bbox": {
                "x": [
                  7.9,
                  8.1
                ],
                "y": [
                  2.0,
                  6.0
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-south": {
              "axis": "x",
              "bbox": {
                "x": [
                  0.0,
                  12.0
                ],
                "y": [
                  -0.1,
                  0.1
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "ifc_class": "IfcWall"
            },
            "wall-west": {
              "axis": "y",
              "bbox": {
                "x": [
                  -0.1,
                  0.1
                ],
                "y": [
                  0.0,
                  6.0
                ],
                "z": [
                  0.0,
                  3.2
                ]
              },
              "ifc_class": "IfcWall"
            }
          }
        },
        "success": true
      },
      "geometry_success": true,
      "ifc_path": "dataset\\processed\\agent-demo\\phase6.6-medium-live-64k-fix2\\runs\\8c8ef9a111e326d7\\output.ifc",
      "ifc_verification": {
        "ifc_issues": [],
        "input_issues": [],
        "output_path": "dataset\\processed\\agent-demo\\phase6.6-medium-live-64k-fix2\\runs\\8c8ef9a111e326d7\\output.ifc",
        "success": true
      },
      "output_dir": "dataset\\processed\\agent-demo\\phase6.6-medium-live-64k-fix2\\runs\\8c8ef9a111e326d7",
      "semantic_geometry_expectation": {
        "case_id": "8c8ef9a111e326d7",
        "complete": true,
        "floor_openings": {},
        "roof": {},
        "schema_version": "text2ifc/design-geometry-expectation/1.0",
        "slabs": {
          "ground-floor-slab": {
            "bbox": {
              "x": [
                0.0,
                12.0
              ],
              "y": [
                0.0,
                6.0
              ],
              "z": [
                -0.15,
                0.0
              ]
            },
            "datum": "slab_top",
            "must_touch_walls": [],
            "source_fact_refs": [
              "/known_facts/floor_slabs/0"
            ]
          }
        },
        "source": "design_brief_expected_facts",
        "spaces": {
          "space-corridor": {
            "bbox": {
              "x": [
                0.0,
                12.0
              ],
              "y": [
                0.0,
                2.0
              ],
              "z": [
                0.0,
                3.2
              ]
            },
            "source_fact_refs": [
              "/known_facts/storeys/0/spaces/0"
            ],
            "storey_id": "storey-1"
          },
          "space-officeA": {
            "bbox": {
              "x": [
                0.0,
                4.0
              ],
              "y": [
                2.0,
                6.0
              ],
              "z": [
                0.0,
                3.2
              ]
            },
            "source_fact_refs": [
              "/known_facts/storeys/0/spaces/1"
            ],
            "storey_id": "storey-1"
          },
          "space-officeB": {
            "bbox": {
              "x": [
                4.0,
                8.0
              ],
              "y": [
                2.0,
                6.0
              ],
              "z": [
                0.0,
                3.2
              ]
            },
            "source_fact_refs": [
              "/known_facts/storeys/0/spaces/2"
            ],
            "storey_id": "storey-1"
          },
          "space-officeC": {
            "bbox": {
              "x": [
                8.0,
                12.0
              ],
              "y": [
                2.0,
                6.0
              ],
              "z": [
                0.0,
                3.2
              ]
            },
            "source_fact_refs": [
              "/known_facts/storeys/0/spaces/3"
            ],
            "storey_id": "storey-1"
          }
        },
        "stairs": {},
        "tolerance": 0.05,
        "units": "METRE",
        "unresolved": [],
        "walls": {
          "wall-corridor-offA": {
            "axis": "x",
            "bbox": {
              "x": [
                0.0,
                4.0
              ],
              "y": [
                1.9,
                2.1
              ],
              "z": [
                0.0,
                3.2
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-corridor-offA",
            "source_fact_refs": [
              "/known_facts/storeys/0/walls/interior/0"
            ]
          },
          "wall-corridor-offB": {
            "axis": "x",
            "bbox": {
              "x": [
                4.0,
                8.0
              ],
              "y": [
                1.9,
                2.1
              ],
              "z": [
                0.0,
                3.2
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-corridor-offB",
            "source_fact_refs": [
              "/known_facts/storeys/0/walls/interior/1"
            ]
          },
          "wall-corridor-offC": {
            "axis": "x",
            "bbox": {
              "x": [
                8.0,
                12.0
              ],
              "y": [
                1.9,
                2.1
              ],
              "z": [
                0.0,
                3.2
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-corridor-offC",
            "source_fact_refs": [
              "/known_facts/storeys/0/walls/interior/2"
            ]
          },
          "wall-east": {
            "axis": "y",
            "bbox": {
              "x": [
                11.9,
                12.1
              ],
              "y": [
                0.0,
                6.0
              ],
              "z": [
                0.0,
                3.2
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-east",
            "source_fact_refs": [
              "/known_facts/walls/1"
            ]
          },
          "wall-north-A": {
            "axis": "x",
            "bbox": {
              "x": [
                0.0,
                4.0
              ],
              "y": [
                5.9,
                6.1
              ],
              "z": [
                0.0,
                3.2
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-north-A",
            "source_fact_refs": [
              "/known_facts/walls/3"
            ]
          },
          "wall-north-B": {
            "axis": "x",
            "bbox": {
              "x": [
                4.0,
                8.0
              ],
              "y": [
                5.9,
                6.1
              ],
              "z": [
                0.0,
                3.2
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-north-B",
            "source_fact_refs": [
              "/known_facts/walls/4"
            ]
          },
          "wall-north-C": {
            "axis": "x",
            "bbox": {
              "x": [
                8.0,
                12.0
              ],
              "y": [
                5.9,
                6.1
              ],
              "z": [
                0.0,
                3.2
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-north-C",
            "source_fact_refs": [
              "/known_facts/walls/5"
            ]
          },
          "wall-offA-offB": {
            "axis": "y",
            "bbox": {
              "x": [
                3.9,
                4.1
              ],
              "y": [
                2.0,
                6.0
              ],
              "z": [
                0.0,
                3.2
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-offA-offB",
            "source_fact_refs": [
              "/known_facts/storeys/0/walls/interior/3"
            ]
          },
          "wall-offB-offC": {
            "axis": "y",
            "bbox": {
              "x": [
                7.9,
                8.1
              ],
              "y": [
                2.0,
                6.0
              ],
              "z": [
                0.0,
                3.2
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-offB-offC",
            "source_fact_refs": [
              "/known_facts/storeys/0/walls/interior/4"
            ]
          },
          "wall-south": {
            "axis": "x",
            "bbox": {
              "x": [
                0.0,
                12.0
              ],
              "y": [
                -0.1,
                0.1
              ],
              "z": [
                0.0,
                3.2
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-south",
            "source_fact_refs": [
              "/known_facts/walls/2"
            ]
          },
          "wall-west": {
            "axis": "y",
            "bbox": {
              "x": [
                -0.1,
                0.1
              ],
              "y": [
                0.0,
                6.0
              ],
              "z": [
                0.0,
                3.2
              ]
            },
            "bbox_issue_code": "WALL_SEGMENT_MISMATCH",
            "bbox_issue_path": "/walls/wall-west",
            "source_fact_refs": [
              "/known_facts/walls/0"
            ]
          }
        }
      },
      "stage": "candidate-gates",
      "valid": true
    }
  },
  {
    "created_at": "2026-07-16T09:55:57+00:00",
    "event_index": 5,
    "event_type": "audit_completed",
    "payload": {
      "case_id": "8c8ef9a111e326d7",
      "evidence_class": "live",
      "output_dir": "dataset/processed/agent-demo/phase6.6-medium-live-64k-fix2/runs/8c8ef9a111e326d7",
      "report_path": "dataset/processed/agent-demo/phase6.6-medium-live-64k-fix2/runs/8c8ef9a111e326d7/report.md",
      "response_id": "5f963857-5b06-42ae-98ac-a0432f735566",
      "route_decision": "accept",
      "route_owner_stage": "none",
      "stage": "audit-report",
      "status": "accepted",
      "valid": true
    }
  },
  {
    "created_at": "2026-07-16T09:55:59+00:00",
    "event_index": 6,
    "event_type": "final_acceptance_completed",
    "payload": {
      "case_id": "8c8ef9a111e326d7",
      "compile_reopen_success": true,
      "geometry_success": true,
      "ifc_path": "dataset\\processed\\agent-demo\\phase6.6-medium-live-64k-fix2\\runs\\8c8ef9a111e326d7\\output.ifc",
      "output_dir": "dataset\\processed\\agent-demo\\phase6.6-medium-live-64k-fix2\\runs\\8c8ef9a111e326d7",
      "report_path": "dataset\\processed\\agent-demo\\phase6.6-medium-live-64k-fix2\\runs\\8c8ef9a111e326d7\\report.md",
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
    "created_at": "2026-07-16T09:54:00+00:00",
    "kind": "design_brief",
    "path": "runs/8c8ef9a111e326d7/design-brief.json"
  },
  {
    "created_at": "2026-07-16T09:54:00+00:00",
    "kind": "session_export",
    "path": "runs/8c8ef9a111e326d7/session-export.json"
  },
  {
    "created_at": "2026-07-16T09:54:00+00:00",
    "kind": "expected_facts",
    "path": "runs/8c8ef9a111e326d7/expected-facts.json"
  },
  {
    "created_at": "2026-07-16T09:55:45+00:00",
    "kind": "candidate",
    "path": "runs/8c8ef9a111e326d7/candidate.json"
  },
  {
    "created_at": "2026-07-16T09:55:45+00:00",
    "kind": "candidate_revision",
    "path": "runs/8c8ef9a111e326d7/candidate-revision.json"
  },
  {
    "created_at": "2026-07-16T09:55:45+00:00",
    "kind": "component_preservation",
    "path": "runs/8c8ef9a111e326d7/component-preservation.json"
  },
  {
    "created_at": "2026-07-16T09:55:45+00:00",
    "kind": "semantic_coverage",
    "path": "runs/8c8ef9a111e326d7/semantic-coverage.json"
  },
  {
    "created_at": "2026-07-16T09:55:59+00:00",
    "kind": "issues",
    "path": "runs/8c8ef9a111e326d7/issues.json"
  },
  {
    "created_at": "2026-07-16T09:55:59+00:00",
    "kind": "route_decision",
    "path": "runs/8c8ef9a111e326d7/route-decision.json"
  },
  {
    "created_at": "2026-07-16T09:55:59+00:00",
    "kind": "feedback_rounds",
    "path": "runs/8c8ef9a111e326d7/feedback-rounds.json"
  },
  {
    "created_at": "2026-07-16T09:55:59+00:00",
    "kind": "ifc",
    "path": "runs/8c8ef9a111e326d7/output.ifc"
  },
  {
    "created_at": "2026-07-16T09:55:59+00:00",
    "kind": "report",
    "path": "runs/8c8ef9a111e326d7/report.md"
  },
  {
    "created_at": "2026-07-16T09:55:59+00:00",
    "kind": "session_export",
    "path": "runs/8c8ef9a111e326d7/session-export.json"
  }
]
```
