# Phase 6.2-fix Real REPL Acceptance

## REPL Interaction Evidence

- interaction_mode: `human_repl_live`
- input_source: `terminal`
- session_hash: `d9fda4e730f9971d`

```json
[
  {
    "created_at": "2026-07-12T14:56:42+00:00",
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
    "created_at": "2026-07-12T15:00:54+00:00",
    "event_index": 1,
    "event_type": "generator_completed",
    "payload": {
      "case_id": "d9fda4e730f9971d",
      "classification": "formal",
      "contract_valid": true,
      "evidence_class": "provider-backed-staged",
      "output_dir": "dataset\\processed\\agent-demo\\phase6.5-live-two-storey-diagnostic-21\\runs\\d9fda4e730f9971d\\generator",
      "response_id": "079413f1-adec-4c43-bfeb-5957c0daa357",
      "stage": "generate",
      "status": "formal",
      "strict_output_contract_valid": true,
      "valid": true
    }
  },
  {
    "created_at": "2026-07-12T15:00:54+00:00",
    "event_index": 2,
    "event_type": "semantic_coverage_completed",
    "payload": {
      "blocking_fact_count": 0,
      "capability_profile_hash": "sha256:1a9b5d81e65c07e3b578782744596bd9a56eb1ecf9702c94dbde5fd91681bbb5",
      "capability_profile_id": "text2ifc/semantic-capabilities/ifc2x3-bim-json-2.0/1.0",
      "case_id": "d9fda4e730f9971d",
      "coverage": {
        "blocking_facts": [],
        "candidate_entity_count": 31,
        "capability_profile_hash": "sha256:1a9b5d81e65c07e3b578782744596bd9a56eb1ecf9702c94dbde5fd91681bbb5",
        "capability_profile_id": "text2ifc/semantic-capabilities/ifc2x3-bim-json-2.0/1.0",
        "case_id": "d9fda4e730f9971d",
        "custom_property_policy": {
          "counts_as_semantic_support": false,
          "state": "preserved_text_only"
        },
        "facts": [
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/floor_slab_thickness_mm",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 150
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/outline/x_max",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 8000
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/outline/x_min",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 0
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/outline/y_max",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 6000
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/outline/y_min",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 0
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/roof_slab_thickness_mm",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 150
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/storey_count",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 2
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/wall_thickness_mm",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 200
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/floor_slabs",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": [
              {
                "id": "ground-floor-slab",
                "opening": null,
                "storey": "storey-1",
                "thickness_mm": 150,
                "top_elevation_mm": 0
              },
              {
                "id": "first-floor-slab",
                "opening": {
                  "bounds": {
                    "x_max": 8000,
                    "x_min": 6000,
                    "y_max": 6000,
                    "y_min": 1000
                  }
                },
                "storey": "storey-2",
                "thickness_mm": 150,
                "top_elevation_mm": 3150
              }
            ]
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/roof_slab/bottom_elevation_mm",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 6150
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/roof_slab/id",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": "roof-slab"
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/roof_slab/thickness_mm",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 150
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/stairs",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": [
              {
                "bounds": {
                  "x_max": 7500,
                  "x_min": 6500,
                  "y_max": 5000,
                  "y_min": 1500
                },
                "end_elevation_mm": 3150,
                "from_storey": "storey-1",
                "id": "stair-1",
                "run_direction": "+Y",
                "start_elevation_mm": 150,
                "to_storey": "storey-2",
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
                "doors": [
                  {
                    "alignment": "horizontal_center",
                    "height_mm": 2100,
                    "host_wall": "storey-1-wall-south",
                    "id": "door-storey-1-south",
                    "sill_height_mm": 0,
                    "width_mm": 900
                  }
                ],
                "elevation_mm": 0,
                "id": "storey-1",
                "name": "首层",
                "net_height_mm": 3000,
                "spaces": [
                  {
                    "bounds": {
                      "x_max": 6000,
                      "x_min": 0,
                      "y_max": 6000,
                      "y_min": 0
                    },
                    "id": "space-office-1",
                    "name": "办公室"
                  },
                  {
                    "bounds": {
                      "x_max": 8000,
                      "x_min": 6000,
                      "y_max": 6000,
                      "y_min": 0
                    },
                    "id": "space-stair-hall",
                    "name": "楼梯间"
                  }
                ],
                "walls": [
                  {
                    "id": "storey-1-wall-south",
                    "side": "south",
                    "thickness_mm": 200
                  },
                  {
                    "id": "storey-1-wall-north",
                    "side": "north",
                    "thickness_mm": 200
                  },
                  {
                    "id": "storey-1-wall-east",
                    "side": "east",
                    "thickness_mm": 200
                  },
                  {
                    "id": "storey-1-wall-west",
                    "side": "west",
                    "thickness_mm": 200
                  }
                ],
                "windows": [
                  {
                    "alignment": "horizontal_center",
                    "height_mm": 1000,
                    "host_wall": "storey-1-wall-north",
                    "id": "window-storey-1-north",
                    "sill_height_mm": 900,
                    "width_mm": 1200
                  }
                ]
              },
              {
                "doors": [
                  {
                    "alignment": "horizontal_center",
                    "height_mm": 2100,
                    "host_wall": "storey-2-wall-south",
                    "id": "door-storey-2-south",
                    "sill_height_mm": 0,
                    "width_mm": 900
                  }
                ],
                "elevation_mm": 3150,
                "id": "storey-2",
                "name": "二层",
                "net_height_mm": 3000,
                "spaces": [
                  {
                    "bounds": {
                      "x_max": 6000,
                      "x_min": 0,
                      "y_max": 6000,
                      "y_min": 0
                    },
                    "id": "space-office-2",
                    "name": "办公室"
                  },
                  {
                    "bounds": {
                      "x_max": 8000,
                      "x_min": 6000,
                      "y_max": 1000,
                      "y_min": 0
                    },
                    "id": "space-stair-landing",
                    "name": "楼梯平台"
                  }
                ],
                "walls": [
                  {
                    "id": "storey-2-wall-south",
                    "side": "south",
                    "thickness_mm": 200
                  },
                  {
                    "id": "storey-2-wall-north",
                    "side": "north",
                    "thickness_mm": 200
                  },
                  {
                    "id": "storey-2-wall-east",
                    "side": "east",
                    "thickness_mm": 200
                  },
                  {
                    "id": "storey-2-wall-west",
                    "side": "west",
                    "thickness_mm": 200
                  }
                ],
                "windows": [
                  {
                    "alignment": "horizontal_center",
                    "height_mm": 1000,
                    "host_wall": "storey-2-wall-north",
                    "id": "window-storey-2-north",
                    "sill_height_mm": 900,
                    "width_mm": 1200
                  }
                ]
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
    "created_at": "2026-07-12T15:00:54+00:00",
    "event_index": 3,
    "event_type": "repair_completed",
    "payload": {
      "case_id": "d9fda4e730f9971d",
      "evidence_class": "live-derived-no-call",
      "output_dir": "dataset/processed/agent-demo/phase6.5-live-two-storey-diagnostic-21/runs/d9fda4e730f9971d/repair",
      "provider_call_count": 0,
      "repair_attempts": [],
      "route": "no_repair_needed",
      "source_generator_response_id": "079413f1-adec-4c43-bfeb-5957c0daa357",
      "stage": "repair",
      "valid": true
    }
  },
  {
    "created_at": "2026-07-12T15:00:55+00:00",
    "event_index": 4,
    "event_type": "candidate_gates_completed",
    "payload": {
      "case_id": "d9fda4e730f9971d",
      "compile_reopen_success": true,
      "deterministic_gates_passed": true,
      "gate_summary": {
        "artifact_hashes": {
          "dynamic-gates.json": "028e025df4ab44cf2cc7c5cfc6bdb0cf5bd59abd060de18ca11ea44fab10fe9e",
          "expected-facts.json": "7f0c68e025ea61fb2fde45a1a0eb165c578a210b34ec8a2e39a5ce18238ed0ec",
          "generator/candidate.json": "03380dd3abd632d83e3b13b61b55031825d41a5d9c15903279a0cbef1a330ec4",
          "generator/validation.json": "6be6595f4f77090199203073905e3755e4015ff1a83b3412d64571cd872b4c41",
          "geometry-feedback.json": "498b01952d4749c457b5e209d9882c2b9a76ef6b16ba51be683ba44a39af72a0",
          "ifc-verification.json": "a2ad80151ac1c71fff97622e2069774e7f3991f4fd5e1aad0a92210a42cc8a62",
          "repair/route.json": "2d41407cb9d38c14a5d1478f0a2ea7e27612d6ef8e9ba2508349c3cfc8dcf91c",
          "semantic-coverage.json": "f31466552b29cdcf78ccf65223797e082a7723fa43d9554662d0b195a0da2ff6"
        },
        "candidate_hash": "03380dd3abd632d83e3b13b61b55031825d41a5d9c15903279a0cbef1a330ec4",
        "candidate_path": "generator/candidate.json",
        "case_id": "d9fda4e730f9971d",
        "evidence": {
          "compile_reopen": {
            "ifc_issues": [],
            "input_issues": [],
            "output_path": "dataset\\processed\\agent-demo\\phase6.5-live-two-storey-diagnostic-21\\runs\\d9fda4e730f9971d\\output.ifc",
            "success": true
          },
          "geometry": {
            "expectation_source": "design_brief_expected_facts",
            "issues": [],
            "metrics": {
              "case_id": "d9fda4e730f9971d",
              "floor_openings": {
                "opening-first-floor-slab-stair": {
                  "bbox": {
                    "x": [
                      6.0,
                      8.0
                    ],
                    "y": [
                      1.0,
                      6.0
                    ],
                    "z": [
                      3.0,
                      3.15
                    ]
                  },
                  "ifc_class": "IfcOpeningElement"
                }
              },
              "roof": {
                "roof-slab": {
                  "bbox": {
                    "x": [
                      0.0,
                      8.0
                    ],
                    "y": [
                      0.0,
                      6.0
                    ],
                    "z": [
                      6.15,
                      6.300000000000001
                    ]
                  },
                  "ifc_class": "IfcSlab"
                }
              },
              "slabs": {
                "first-floor-slab": {
                  "bbox": {
                    "x": [
                      0.0,
                      8.0
                    ],
                    "y": [
                      0.0,
                      6.0
                    ],
                    "z": [
                      3.0,
                      3.15
                    ]
                  },
                  "ifc_class": "IfcSlab"
                },
                "ground-floor-slab": {
                  "bbox": {
                    "x": [
                      0.0,
                      8.0
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
              "stairs": {
                "stair-1": {
                  "bbox": {
                    "x": [
                      6.5,
                      7.5
                    ],
                    "y": [
                      1.5,
                      5.0
                    ],
                    "z": [
                      0.15,
                      3.15
                    ]
                  },
                  "flight_ids": [
                    "stair-flight-1"
                  ],
                  "has_stepped_profile": true
                }
              },
              "wall_set_convention": "primary",
              "walls": {}
            },
            "success": true
          },
          "repair_history": {
            "case_id": "d9fda4e730f9971d",
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
            "source_generator_dir": "dataset/processed/agent-demo/phase6.5-live-two-storey-diagnostic-21/runs/d9fda4e730f9971d/generator",
            "source_generator_response_id": "079413f1-adec-4c43-bfeb-5957c0daa357",
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
            "candidate_entity_count": 31,
            "capability_profile_hash": "sha256:1a9b5d81e65c07e3b578782744596bd9a56eb1ecf9702c94dbde5fd91681bbb5",
            "capability_profile_id": "text2ifc/semantic-capabilities/ifc2x3-bim-json-2.0/1.0",
            "case_id": "d9fda4e730f9971d",
            "custom_property_policy": {
              "counts_as_semantic_support": false,
              "state": "preserved_text_only"
            },
            "facts": [
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/floor_slab_thickness_mm",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 150
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/outline/x_max",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 8000
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/outline/x_min",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 0
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/outline/y_max",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 6000
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/outline/y_min",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 0
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/roof_slab_thickness_mm",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 150
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/storey_count",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 2
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/wall_thickness_mm",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 200
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/floor_slabs",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": [
                  {
                    "id": "ground-floor-slab",
                    "opening": null,
                    "storey": "storey-1",
                    "thickness_mm": 150,
                    "top_elevation_mm": 0
                  },
                  {
                    "id": "first-floor-slab",
                    "opening": {
                      "bounds": {
                        "x_max": 8000,
                        "x_min": 6000,
                        "y_max": 6000,
                        "y_min": 1000
                      }
                    },
                    "storey": "storey-2",
                    "thickness_mm": 150,
                    "top_elevation_mm": 3150
                  }
                ]
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/roof_slab/bottom_elevation_mm",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 6150
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/roof_slab/id",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": "roof-slab"
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/roof_slab/thickness_mm",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 150
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/stairs",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": [
                  {
                    "bounds": {
                      "x_max": 7500,
                      "x_min": 6500,
                      "y_max": 5000,
                      "y_min": 1500
                    },
                    "end_elevation_mm": 3150,
                    "from_storey": "storey-1",
                    "id": "stair-1",
                    "run_direction": "+Y",
                    "start_elevation_mm": 150,
                    "to_storey": "storey-2",
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
                    "doors": [
                      {
                        "alignment": "horizontal_center",
                        "height_mm": 2100,
                        "host_wall": "storey-1-wall-south",
                        "id": "door-storey-1-south",
                        "sill_height_mm": 0,
                        "width_mm": 900
                      }
                    ],
                    "elevation_mm": 0,
                    "id": "storey-1",
                    "name": "首层",
                    "net_height_mm": 3000,
                    "spaces": [
                      {
                        "bounds": {
                          "x_max": 6000,
                          "x_min": 0,
                          "y_max": 6000,
                          "y_min": 0
                        },
                        "id": "space-office-1",
                        "name": "办公室"
                      },
                      {
                        "bounds": {
                          "x_max": 8000,
                          "x_min": 6000,
                          "y_max": 6000,
                          "y_min": 0
                        },
                        "id": "space-stair-hall",
                        "name": "楼梯间"
                      }
                    ],
                    "walls": [
                      {
                        "id": "storey-1-wall-south",
                        "side": "south",
                        "thickness_mm": 200
                      },
                      {
                        "id": "storey-1-wall-north",
                        "side": "north",
                        "thickness_mm": 200
                      },
                      {
                        "id": "storey-1-wall-east",
                        "side": "east",
                        "thickness_mm": 200
                      },
                      {
                        "id": "storey-1-wall-west",
                        "side": "west",
                        "thickness_mm": 200
                      }
                    ],
                    "windows": [
                      {
                        "alignment": "horizontal_center",
                        "height_mm": 1000,
                        "host_wall": "storey-1-wall-north",
                        "id": "window-storey-1-north",
                        "sill_height_mm": 900,
                        "width_mm": 1200
                      }
                    ]
                  },
                  {
                    "doors": [
                      {
                        "alignment": "horizontal_center",
                        "height_mm": 2100,
                        "host_wall": "storey-2-wall-south",
                        "id": "door-storey-2-south",
                        "sill_height_mm": 0,
                        "width_mm": 900
                      }
                    ],
                    "elevation_mm": 3150,
                    "id": "storey-2",
                    "name": "二层",
                    "net_height_mm": 3000,
                    "spaces": [
                      {
                        "bounds": {
                          "x_max": 6000,
                          "x_min": 0,
                          "y_max": 6000,
                          "y_min": 0
                        },
                        "id": "space-office-2",
                        "name": "办公室"
                      },
                      {
                        "bounds": {
                          "x_max": 8000,
                          "x_min": 6000,
                          "y_max": 1000,
                          "y_min": 0
                        },
                        "id": "space-stair-landing",
                        "name": "楼梯平台"
                      }
                    ],
                    "walls": [
                      {
                        "id": "storey-2-wall-south",
                        "side": "south",
                        "thickness_mm": 200
                      },
                      {
                        "id": "storey-2-wall-north",
                        "side": "north",
                        "thickness_mm": 200
                      },
                      {
                        "id": "storey-2-wall-east",
                        "side": "east",
                        "thickness_mm": 200
                      },
                      {
                        "id": "storey-2-wall-west",
                        "side": "west",
                        "thickness_mm": 200
                      }
                    ],
                    "windows": [
                      {
                        "alignment": "horizontal_center",
                        "height_mm": 1000,
                        "host_wall": "storey-2-wall-north",
                        "id": "window-storey-2-north",
                        "sill_height_mm": 900,
                        "width_mm": 1200
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
        "expected_facts_hash": "7f0c68e025ea61fb2fde45a1a0eb165c578a210b34ec8a2e39a5ce18238ed0ec",
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
                "candidate_id": "door-storey-1-south",
                "collection": "doors",
                "expected_id": "door-storey-1-south",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "door-storey-2-south",
                "collection": "doors",
                "expected_id": "door-storey-2-south",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "space-office-1",
                "collection": "spaces",
                "expected_id": "space-office-1",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "space-stair-hall",
                "collection": "spaces",
                "expected_id": "space-stair-hall",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "space-office-2",
                "collection": "spaces",
                "expected_id": "space-office-2",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "space-stair-landing",
                "collection": "spaces",
                "expected_id": "space-stair-landing",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "window-storey-1-north",
                "collection": "windows",
                "expected_id": "window-storey-1-north",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "window-storey-2-north",
                "collection": "windows",
                "expected_id": "window-storey-2-north",
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
          "case_id": "d9fda4e730f9971d",
          "floor_openings": {
            "opening-first-floor-slab-stair": {
              "bbox": {
                "x": [
                  6.0,
                  8.0
                ],
                "y": [
                  1.0,
                  6.0
                ],
                "z": [
                  3.0,
                  3.15
                ]
              },
              "ifc_class": "IfcOpeningElement"
            }
          },
          "roof": {
            "roof-slab": {
              "bbox": {
                "x": [
                  0.0,
                  8.0
                ],
                "y": [
                  0.0,
                  6.0
                ],
                "z": [
                  6.15,
                  6.300000000000001
                ]
              },
              "ifc_class": "IfcSlab"
            }
          },
          "slabs": {
            "first-floor-slab": {
              "bbox": {
                "x": [
                  0.0,
                  8.0
                ],
                "y": [
                  0.0,
                  6.0
                ],
                "z": [
                  3.0,
                  3.15
                ]
              },
              "ifc_class": "IfcSlab"
            },
            "ground-floor-slab": {
              "bbox": {
                "x": [
                  0.0,
                  8.0
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
          "stairs": {
            "stair-1": {
              "bbox": {
                "x": [
                  6.5,
                  7.5
                ],
                "y": [
                  1.5,
                  5.0
                ],
                "z": [
                  0.15,
                  3.15
                ]
              },
              "flight_ids": [
                "stair-flight-1"
              ],
              "has_stepped_profile": true
            }
          },
          "wall_set_convention": "primary",
          "walls": {}
        },
        "success": true
      },
      "geometry_success": true,
      "ifc_path": "dataset\\processed\\agent-demo\\phase6.5-live-two-storey-diagnostic-21\\runs\\d9fda4e730f9971d\\output.ifc",
      "ifc_verification": {
        "ifc_issues": [],
        "input_issues": [],
        "output_path": "dataset\\processed\\agent-demo\\phase6.5-live-two-storey-diagnostic-21\\runs\\d9fda4e730f9971d\\output.ifc",
        "success": true
      },
      "output_dir": "dataset\\processed\\agent-demo\\phase6.5-live-two-storey-diagnostic-21\\runs\\d9fda4e730f9971d",
      "semantic_geometry_expectation": {
        "case_id": "d9fda4e730f9971d",
        "floor_openings": {
          "opening-first-floor-slab-stair": {
            "bbox": {
              "x": [
                6.0,
                8.0
              ],
              "y": [
                1.0,
                6.0
              ],
              "z": [
                3.0,
                3.15
              ]
            },
            "host_slab_id": "first-floor-slab",
            "source_fact_refs": [
              "/known_facts/floor_slabs/1/openings/0"
            ]
          }
        },
        "roof": {
          "roof-slab": {
            "bbox": {
              "x": [
                0.0,
                8.0
              ],
              "y": [
                0.0,
                6.0
              ],
              "z": [
                6.15,
                6.3
              ]
            },
            "datum": "roof_bottom",
            "source_fact_refs": [
              "/known_facts/roof_slab"
            ]
          }
        },
        "schema_version": "text2ifc/design-geometry-expectation/1.0",
        "slabs": {
          "first-floor-slab": {
            "bbox": {
              "x": [
                0.0,
                8.0
              ],
              "y": [
                0.0,
                6.0
              ],
              "z": [
                3.0,
                3.15
              ]
            },
            "datum": "slab_top",
            "must_touch_walls": [],
            "source_fact_refs": [
              "/known_facts/floor_slabs/1"
            ]
          },
          "ground-floor-slab": {
            "bbox": {
              "x": [
                0.0,
                8.0
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
        "stairs": {
          "stair-1": {
            "bbox": {
              "x": [
                6.5,
                7.5
              ],
              "y": [
                1.5,
                5.0
              ],
              "z": [
                0.15,
                3.15
              ]
            },
            "flight_ids": [
              "stair-flight-1"
            ],
            "require_steps": true,
            "source_fact_refs": [
              "/known_facts/stairs/0"
            ]
          }
        },
        "tolerance": 0.05,
        "units": "METRE",
        "unresolved": [],
        "walls": {}
      },
      "stage": "candidate-gates",
      "valid": true
    }
  },
  {
    "created_at": "2026-07-12T15:01:02+00:00",
    "event_index": 5,
    "event_type": "audit_completed",
    "payload": {
      "case_id": "d9fda4e730f9971d",
      "evidence_class": "live",
      "output_dir": "dataset/processed/agent-demo/phase6.5-live-two-storey-diagnostic-21/runs/d9fda4e730f9971d",
      "report_path": "dataset/processed/agent-demo/phase6.5-live-two-storey-diagnostic-21/runs/d9fda4e730f9971d/report.md",
      "response_id": "7aab01cf-ef1c-4753-b196-de07633c7d07",
      "route_decision": "accept",
      "route_owner_stage": "none",
      "stage": "audit-report",
      "status": "accepted",
      "valid": true
    }
  },
  {
    "created_at": "2026-07-12T15:01:04+00:00",
    "event_index": 6,
    "event_type": "final_acceptance_completed",
    "payload": {
      "case_id": "d9fda4e730f9971d",
      "compile_reopen_success": true,
      "geometry_success": true,
      "ifc_path": "dataset\\processed\\agent-demo\\phase6.5-live-two-storey-diagnostic-21\\runs\\d9fda4e730f9971d\\output.ifc",
      "output_dir": "dataset\\processed\\agent-demo\\phase6.5-live-two-storey-diagnostic-21\\runs\\d9fda4e730f9971d",
      "report_path": "dataset\\processed\\agent-demo\\phase6.5-live-two-storey-diagnostic-21\\runs\\d9fda4e730f9971d\\report.md",
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
创建一个两层矩形建筑，单位毫米。建筑外轮廓为X方向8000、Y方向6000，西南角为原点，X向东、Y向北、Z向上。首层标高0，二层标高3150，每层净高3000，墙厚200，楼板厚150。每层必须分别生成南、东、北、西四面独立外墙，不得跨楼层复用。首层有办公室和楼梯间：办公室范围x=0..6000、y=0..6000，楼梯间范围x=6000..8000、y=0..6000。二层有办公室和楼梯平台：办公室范围x=0..6000、y=0..6000，楼梯平台范围x=6000..8000、y=0..1000；二层楼梯洞口范围x=6000..8000、y=1000..6000，该洞口不是IfcSpace。生成首层地板，顶面标高0；生成二层楼板，顶面标高3150、并保留上述楼梯洞口；生成屋面板，底标高6150、厚150。生成一段宽1000的直跑楼梯，平面范围x=6500..7500、y=1500..5000，沿+Y方向上升，从首层Z=150连接到二层Z=3150，楼梯属于首层并连接二层。首层南外墙和二层南外墙各设置一扇900宽、2100高的门，门在各自宿主墙上水平居中；首层北外墙和二层北外墙各设置一扇1200宽、1000高、窗台高900的窗，窗在各自宿主墙上水平居中。门窗必须嵌入同一楼层的宿主墙，洞口与填充构件必须重合。生成IfcBuilding、两个IfcBuildingStorey、四个IfcSpace、各层墙体、楼板、屋面、楼梯、门、窗、洞口及关系；所有构件必须归属正确楼层。
```

## Transcript

```json
[
  {
    "created_at": "2026-07-12T14:56:41+00:00",
    "role": "user",
    "text": "创建一个两层矩形建筑，单位毫米。建筑外轮廓为X方向8000、Y方向6000，西南角为原点，X向东、Y向北、Z向上。首层标高0，二层标高3150，每层净高3000，墙厚200，楼板厚150。每层必须分别生成南、东、北、西四面独立外墙，不得跨楼层复用。首层有办公室和楼梯间：办公室范围x=0..6000、y=0..6000，楼梯间范围x=6000..8000、y=0..6000。二层有办公室和楼梯平台：办公室范围x=0..6000、y=0..6000，楼梯平台范围x=6000..8000、y=0..1000；二层楼梯洞口范围x=6000..8000、y=1000..6000，该洞口不是IfcSpace。生成首层地板，顶面标高0；生成二层楼板，顶面标高3150、并保留上述楼梯洞口；生成屋面板，底标高6150、厚150。生成一段宽1000的直跑楼梯，平面范围x=6500..7500、y=1500..5000，沿+Y方向上升，从首层Z=150连接到二层Z=3150，楼梯属于首层并连接二层。首层南外墙和二层南外墙各设置一扇900宽、2100高的门，门在各自宿主墙上水平居中；首层北外墙和二层北外墙各设置一扇1200宽、1000高、窗台高900的窗，窗在各自宿主墙上水平居中。门窗必须嵌入同一楼层的宿主墙，洞口与填充构件必须重合。生成IfcBuilding、两个IfcBuildingStorey、四个IfcSpace、各层墙体、楼板、屋面、楼梯、门、窗、洞口及关系；所有构件必须归属正确楼层。",
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
- [semantic-geometry-expectation.json](semantic-geometry-expectation.json)

## Deterministic Gates

- [acceptance-metrics.json](acceptance-metrics.json)
- [ifc-verification.json](ifc-verification.json)
- [geometry-feedback.json](geometry-feedback.json)
- [secret-scan.json](secret-scan.json)

```json
{
  "case_id": "d9fda4e730f9971d",
  "compile_reopen_success": true,
  "geometry_success": true,
  "ifc_path": "dataset\\processed\\agent-demo\\phase6.5-live-two-storey-diagnostic-21\\runs\\d9fda4e730f9971d\\output.ifc",
  "output_dir": "dataset\\processed\\agent-demo\\phase6.5-live-two-storey-diagnostic-21\\runs\\d9fda4e730f9971d",
  "report_path": "dataset\\processed\\agent-demo\\phase6.5-live-two-storey-diagnostic-21\\runs\\d9fda4e730f9971d\\report.md",
  "secret_finding_count": 0,
  "stage": "final-acceptance",
  "valid": true
}
```

## Revision and ChangeSet History

```json
{
  "changed_ids": [
    "aggregate-stair-1-flight",
    "door-storey-1-south",
    "door-storey-2-south",
    "first-floor-slab",
    "ground-floor-slab",
    "opening-door-storey-1-south",
    "opening-door-storey-2-south",
    "opening-first-floor-slab-stair",
    "opening-window-storey-1-north",
    "opening-window-storey-2-north",
    "rel-fills-door-storey-1-south",
    "rel-fills-door-storey-2-south",
    "rel-fills-window-storey-1-north",
    "rel-fills-window-storey-2-north",
    "rel-voids-door-storey-1-south",
    "rel-voids-door-storey-2-south",
    "rel-voids-first-floor-slab",
    "rel-voids-window-storey-1-north",
    "rel-voids-window-storey-2-north",
    "roof-slab",
    "space-office-1",
    "space-office-2",
    "space-stair-hall",
    "space-stair-landing",
    "stair-1",
    "stair-flight-1",
    "storey-1-wall-east",
    "storey-1-wall-north",
    "storey-1-wall-south",
    "storey-1-wall-west",
    "storey-2-wall-east",
    "storey-2-wall-north",
    "storey-2-wall-south",
    "storey-2-wall-west",
    "window-storey-1-north",
    "window-storey-2-north"
  ],
  "changesets": [
    {
      "path": "generator-staged/package-01-package-storey-1/changeset.json",
      "payload": {
        "base_candidate_hash": "sha256:e10db4c1a74bf594bcd35b15218367a5606ccdfffa65a7e7af29ce5c6695a439",
        "base_revision_id": "revision-00",
        "changeset_id": "changeset-package-storey-1",
        "expected_facts_hash": "sha256:7f0c68e025ea61fb2fde45a1a0eb165c578a210b34ec8a2e39a5ce18238ed0ec",
        "operations": [
          {
            "evidence_refs": [
              "issue-package-storey-1:/expected"
            ],
            "op": "add_entity",
            "operation_id": "add-wall-south",
            "target_id": "storey-1-wall-south",
            "value": {
              "attributes": {
                "Name": "南墙",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    4000,
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
                  "depth": 3000,
                  "direction": [
                    0,
                    0,
                    1
                  ],
                  "kind": "extruded_profile",
                  "profile": {
                    "kind": "rectangle",
                    "x": 8000,
                    "y": 200
                  }
                }
              },
              "id": "storey-1-wall-south",
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
            "target_id": "storey-1-wall-north",
            "value": {
              "attributes": {
                "Name": "北墙",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    4000,
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
                  "depth": 3000,
                  "direction": [
                    0,
                    0,
                    1
                  ],
                  "kind": "extruded_profile",
                  "profile": {
                    "kind": "rectangle",
                    "x": 8000,
                    "y": 200
                  }
                }
              },
              "id": "storey-1-wall-north",
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
            "target_id": "storey-1-wall-east",
            "value": {
              "attributes": {
                "Name": "东墙",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    8000,
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
              "id": "storey-1-wall-east",
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
            "target_id": "storey-1-wall-west",
            "value": {
              "attributes": {
                "Name": "西墙",
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
              "id": "storey-1-wall-west",
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
            "operation_id": "add-space-office-1",
            "target_id": "space-office-1",
            "value": {
              "attributes": {
                "InteriorOrExteriorSpace": "INTERNAL",
                "Name": "办公室",
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
                    "y": 6000
                  }
                }
              },
              "id": "space-office-1",
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
            "operation_id": "add-space-stair-hall",
            "target_id": "space-stair-hall",
            "value": {
              "attributes": {
                "InteriorOrExteriorSpace": "INTERNAL",
                "Name": "楼梯间",
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
                  "depth": 3000,
                  "direction": [
                    0,
                    0,
                    1
                  ],
                  "kind": "extruded_profile",
                  "profile": {
                    "kind": "rectangle",
                    "x": 2000,
                    "y": 6000
                  }
                }
              },
              "id": "space-stair-hall",
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
            "operation_id": "add-opening-door",
            "target_id": "opening-door-storey-1-south",
            "value": {
              "attributes": {
                "Name": "门洞",
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
                  "relative_to": "storey-1-wall-south"
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
              "id": "opening-door-storey-1-south",
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
            "operation_id": "add-door",
            "target_id": "door-storey-1-south",
            "value": {
              "attributes": {
                "Name": "门",
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
                  "relative_to": "opening-door-storey-1-south"
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
                    "y": 50
                  }
                }
              },
              "id": "door-storey-1-south",
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
            "operation_id": "add-opening-window",
            "target_id": "opening-window-storey-1-north",
            "value": {
              "attributes": {
                "Name": "窗洞",
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
                  "relative_to": "storey-1-wall-north"
                },
                "Representation": {
                  "depth": 1000,
                  "direction": [
                    0,
                    0,
                    1
                  ],
                  "kind": "extruded_profile",
                  "profile": {
                    "kind": "rectangle",
                    "x": 1200,
                    "y": 200
                  }
                }
              },
              "id": "opening-window-storey-1-north",
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
            "operation_id": "add-window",
            "target_id": "window-storey-1-north",
            "value": {
              "attributes": {
                "Name": "窗",
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
                  "relative_to": "opening-window-storey-1-north"
                },
                "OverallHeight": 1000,
                "OverallWidth": 1200,
                "Representation": {
                  "depth": 1000,
                  "direction": [
                    0,
                    0,
                    1
                  ],
                  "kind": "extruded_profile",
                  "profile": {
                    "kind": "rectangle",
                    "x": 1200,
                    "y": 50
                  }
                }
              },
              "id": "window-storey-1-north",
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
            "operation_id": "add-void-door",
            "target_id": "rel-voids-door-storey-1-south",
            "value": {
              "attributes": {
                "RelatedOpeningElement": "opening-door-storey-1-south",
                "RelatingBuildingElement": "storey-1-wall-south"
              },
              "id": "rel-voids-door-storey-1-south",
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
            "operation_id": "add-fill-door",
            "target_id": "rel-fills-door-storey-1-south",
            "value": {
              "attributes": {
                "RelatedBuildingElement": "door-storey-1-south",
                "RelatingOpeningElement": "opening-door-storey-1-south"
              },
              "id": "rel-fills-door-storey-1-south",
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
            "operation_id": "add-void-window",
            "target_id": "rel-voids-window-storey-1-north",
            "value": {
              "attributes": {
                "RelatedOpeningElement": "opening-window-storey-1-north",
                "RelatingBuildingElement": "storey-1-wall-north"
              },
              "id": "rel-voids-window-storey-1-north",
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
            "operation_id": "add-fill-window",
            "target_id": "rel-fills-window-storey-1-north",
            "value": {
              "attributes": {
                "RelatedBuildingElement": "window-storey-1-north",
                "RelatingOpeningElement": "opening-window-storey-1-north"
              },
              "id": "rel-fills-window-storey-1-north",
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
      "path": "generator-staged/package-02-package-storey-2/changeset.json",
      "payload": {
        "base_candidate_hash": "sha256:ccccf772954121e071f21971746ed38df40e51932da032e8cadc8a3b498a3461",
        "base_revision_id": "revision-01",
        "changeset_id": "changeset-package-storey-2",
        "expected_facts_hash": "sha256:7f0c68e025ea61fb2fde45a1a0eb165c578a210b34ec8a2e39a5ce18238ed0ec",
        "operations": [
          {
            "evidence_refs": [
              "issue-package-storey-2:/expected"
            ],
            "op": "add_entity",
            "operation_id": "operation-add-storey-2-wall-south",
            "target_id": "storey-2-wall-south",
            "value": {
              "attributes": {
                "Name": "首层南外墙",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    4000,
                    100,
                    0
                  ],
                  "ref_direction": [
                    1,
                    0,
                    0
                  ],
                  "relative_to": "storey-2"
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
                    "x": 8000,
                    "y": 200
                  }
                }
              },
              "id": "storey-2-wall-south",
              "ifc_class": "IfcWall",
              "property_sets": {},
              "provenance": {
                "source": "issue-package-storey-2"
              }
            }
          },
          {
            "evidence_refs": [
              "issue-package-storey-2:/expected"
            ],
            "op": "add_entity",
            "operation_id": "operation-add-storey-2-wall-north",
            "target_id": "storey-2-wall-north",
            "value": {
              "attributes": {
                "Name": "首层北外墙",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    4000,
                    5900,
                    0
                  ],
                  "ref_direction": [
                    1,
                    0,
                    0
                  ],
                  "relative_to": "storey-2"
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
                    "x": 8000,
                    "y": 200
                  }
                }
              },
              "id": "storey-2-wall-north",
              "ifc_class": "IfcWall",
              "property_sets": {},
              "provenance": {
                "source": "issue-package-storey-2"
              }
            }
          },
          {
            "evidence_refs": [
              "issue-package-storey-2:/expected"
            ],
            "op": "add_entity",
            "operation_id": "operation-add-storey-2-wall-east",
            "target_id": "storey-2-wall-east",
            "value": {
              "attributes": {
                "Name": "首层东外墙",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    7900,
                    3000,
                    0
                  ],
                  "ref_direction": [
                    0,
                    1,
                    0
                  ],
                  "relative_to": "storey-2"
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
              "id": "storey-2-wall-east",
              "ifc_class": "IfcWall",
              "property_sets": {},
              "provenance": {
                "source": "issue-package-storey-2"
              }
            }
          },
          {
            "evidence_refs": [
              "issue-package-storey-2:/expected"
            ],
            "op": "add_entity",
            "operation_id": "operation-add-storey-2-wall-west",
            "target_id": "storey-2-wall-west",
            "value": {
              "attributes": {
                "Name": "首层西外墙",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    100,
                    3000,
                    0
                  ],
                  "ref_direction": [
                    0,
                    1,
                    0
                  ],
                  "relative_to": "storey-2"
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
              "id": "storey-2-wall-west",
              "ifc_class": "IfcWall",
              "property_sets": {},
              "provenance": {
                "source": "issue-package-storey-2"
              }
            }
          },
          {
            "evidence_refs": [
              "issue-package-storey-2:/expected"
            ],
            "op": "add_entity",
            "operation_id": "operation-add-space-office-2",
            "target_id": "space-office-2",
            "value": {
              "attributes": {
                "InteriorOrExteriorSpace": "INTERNAL",
                "Name": "办公室",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    3000,
                    3000,
                    0
                  ],
                  "ref_direction": [
                    1,
                    0,
                    0
                  ],
                  "relative_to": "storey-2"
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
                    "y": 6000
                  }
                }
              },
              "id": "space-office-2",
              "ifc_class": "IfcSpace",
              "property_sets": {},
              "provenance": {
                "source": "issue-package-storey-2"
              }
            }
          },
          {
            "evidence_refs": [
              "issue-package-storey-2:/expected"
            ],
            "op": "add_entity",
            "operation_id": "operation-add-space-stair-landing",
            "target_id": "space-stair-landing",
            "value": {
              "attributes": {
                "InteriorOrExteriorSpace": "INTERNAL",
                "Name": "楼梯平台",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    7000,
                    500,
                    0
                  ],
                  "ref_direction": [
                    1,
                    0,
                    0
                  ],
                  "relative_to": "storey-2"
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
                    "x": 2000,
                    "y": 1000
                  }
                }
              },
              "id": "space-stair-landing",
              "ifc_class": "IfcSpace",
              "property_sets": {},
              "provenance": {
                "source": "issue-package-storey-2"
              }
            }
          },
          {
            "evidence_refs": [
              "issue-package-storey-2:/expected"
            ],
            "op": "add_entity",
            "operation_id": "operation-add-opening-door-storey-2-south",
            "target_id": "opening-door-storey-2-south",
            "value": {
              "attributes": {
                "Name": "Opening for door-storey-2-south",
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
                  "relative_to": "storey-2-wall-south"
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
              "id": "opening-door-storey-2-south",
              "ifc_class": "IfcOpeningElement",
              "property_sets": {},
              "provenance": {
                "source": "issue-package-storey-2"
              }
            }
          },
          {
            "evidence_refs": [
              "issue-package-storey-2:/expected"
            ],
            "op": "add_entity",
            "operation_id": "operation-add-door-storey-2-south",
            "target_id": "door-storey-2-south",
            "value": {
              "attributes": {
                "Name": "首层南门",
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
                  "relative_to": "opening-door-storey-2-south"
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
                    "y": 40
                  }
                }
              },
              "id": "door-storey-2-south",
              "ifc_class": "IfcDoor",
              "property_sets": {},
              "provenance": {
                "source": "issue-package-storey-2"
              }
            }
          },
          {
            "evidence_refs": [
              "issue-package-storey-2:/expected"
            ],
            "op": "add_entity",
            "operation_id": "operation-add-opening-window-storey-2-north",
            "target_id": "opening-window-storey-2-north",
            "value": {
              "attributes": {
                "Name": "Opening for window-storey-2-north",
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
                  "relative_to": "storey-2-wall-north"
                },
                "Representation": {
                  "depth": 1000,
                  "direction": [
                    0,
                    0,
                    1
                  ],
                  "kind": "extruded_profile",
                  "profile": {
                    "kind": "rectangle",
                    "x": 1200,
                    "y": 200
                  }
                }
              },
              "id": "opening-window-storey-2-north",
              "ifc_class": "IfcOpeningElement",
              "property_sets": {},
              "provenance": {
                "source": "issue-package-storey-2"
              }
            }
          },
          {
            "evidence_refs": [
              "issue-package-storey-2:/expected"
            ],
            "op": "add_entity",
            "operation_id": "operation-add-window-storey-2-north",
            "target_id": "window-storey-2-north",
            "value": {
              "attributes": {
                "Name": "首层北窗",
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
                  "relative_to": "opening-window-storey-2-north"
                },
                "OverallHeight": 1000,
                "OverallWidth": 1200,
                "Representation": {
                  "depth": 1000,
                  "direction": [
                    0,
                    0,
                    1
                  ],
                  "kind": "extruded_profile",
                  "profile": {
                    "kind": "rectangle",
                    "x": 1200,
                    "y": 100
                  }
                }
              },
              "id": "window-storey-2-north",
              "ifc_class": "IfcWindow",
              "property_sets": {},
              "provenance": {
                "source": "issue-package-storey-2"
              }
            }
          },
          {
            "evidence_refs": [
              "issue-package-storey-2:/expected"
            ],
            "op": "add_relationship",
            "operation_id": "operation-add-rel-voids-door-storey-2-south",
            "target_id": "rel-voids-door-storey-2-south",
            "value": {
              "attributes": {
                "RelatedOpeningElement": "opening-door-storey-2-south",
                "RelatingBuildingElement": "storey-2-wall-south"
              },
              "id": "rel-voids-door-storey-2-south",
              "ifc_class": "IfcRelVoidsElement",
              "provenance": {
                "source": "issue-package-storey-2"
              }
            }
          },
          {
            "evidence_refs": [
              "issue-package-storey-2:/expected"
            ],
            "op": "add_relationship",
            "operation_id": "operation-add-rel-fills-door-storey-2-south",
            "target_id": "rel-fills-door-storey-2-south",
            "value": {
              "attributes": {
                "RelatedBuildingElement": "door-storey-2-south",
                "RelatingOpeningElement": "opening-door-storey-2-south"
              },
              "id": "rel-fills-door-storey-2-south",
              "ifc_class": "IfcRelFillsElement",
              "provenance": {
                "source": "issue-package-storey-2"
              }
            }
          },
          {
            "evidence_refs": [
              "issue-package-storey-2:/expected"
            ],
            "op": "add_relationship",
            "operation_id": "operation-add-rel-voids-window-storey-2-north",
            "target_id": "rel-voids-window-storey-2-north",
            "value": {
              "attributes": {
                "RelatedOpeningElement": "opening-window-storey-2-north",
                "RelatingBuildingElement": "storey-2-wall-north"
              },
              "id": "rel-voids-window-storey-2-north",
              "ifc_class": "IfcRelVoidsElement",
              "provenance": {
                "source": "issue-package-storey-2"
              }
            }
          },
          {
            "evidence_refs": [
              "issue-package-storey-2:/expected"
            ],
            "op": "add_relationship",
            "operation_id": "operation-add-rel-fills-window-storey-2-north",
            "target_id": "rel-fills-window-storey-2-north",
            "value": {
              "attributes": {
                "RelatedBuildingElement": "window-storey-2-north",
                "RelatingOpeningElement": "opening-window-storey-2-north"
              },
              "id": "rel-fills-window-storey-2-north",
              "ifc_class": "IfcRelFillsElement",
              "provenance": {
                "source": "issue-package-storey-2"
              }
            }
          }
        ],
        "schema_version": "text2ifc/bim-json-changeset/1.0",
        "scope_id": "scope-package-2",
        "source_issue_ids": [
          "issue-package-storey-2"
        ]
      }
    },
    {
      "path": "generator-staged/package-03-package-cross-storey/changeset.json",
      "payload": {
        "base_candidate_hash": "sha256:af7edb67931195bae237814de9df39bacd354e5db6f5cb4090647f73ba58e312",
        "base_revision_id": "revision-02",
        "changeset_id": "changeset-package-cross-storey",
        "expected_facts_hash": "sha256:7f0c68e025ea61fb2fde45a1a0eb165c578a210b34ec8a2e39a5ce18238ed0ec",
        "operations": [
          {
            "evidence_refs": [
              "issue-package-cross-storey:/expected"
            ],
            "op": "add_entity",
            "operation_id": "operation-add-ground-floor-slab",
            "target_id": "ground-floor-slab",
            "value": {
              "attributes": {
                "Name": "Ground floor slab",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    4000,
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
                    "x": 8000,
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
          },
          {
            "evidence_refs": [
              "issue-package-cross-storey:/expected"
            ],
            "op": "add_entity",
            "operation_id": "operation-add-first-floor-slab",
            "target_id": "first-floor-slab",
            "value": {
              "attributes": {
                "Name": "First floor slab",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    4000,
                    3000,
                    -150
                  ],
                  "ref_direction": [
                    1,
                    0,
                    0
                  ],
                  "relative_to": "storey-2"
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
                    "x": 8000,
                    "y": 6000
                  }
                }
              },
              "id": "first-floor-slab",
              "ifc_class": "IfcSlab",
              "property_sets": {},
              "provenance": {
                "source": "issue-package-cross-storey"
              }
            }
          },
          {
            "evidence_refs": [
              "issue-package-cross-storey:/expected"
            ],
            "op": "add_entity",
            "operation_id": "operation-add-opening-first-floor-slab-stair",
            "target_id": "opening-first-floor-slab-stair",
            "value": {
              "attributes": {
                "Name": "Stair opening in first floor slab",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    3000,
                    500,
                    0
                  ],
                  "ref_direction": [
                    1,
                    0,
                    0
                  ],
                  "relative_to": "first-floor-slab"
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
                    "x": 2000,
                    "y": 5000
                  }
                }
              },
              "id": "opening-first-floor-slab-stair",
              "ifc_class": "IfcOpeningElement",
              "property_sets": {},
              "provenance": {
                "source": "issue-package-cross-storey"
              }
            }
          },
          {
            "evidence_refs": [
              "issue-package-cross-storey:/expected"
            ],
            "op": "add_entity",
            "operation_id": "operation-add-stair-1",
            "target_id": "stair-1",
            "value": {
              "attributes": {
                "Name": "Main stair",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    6500,
                    1500,
                    150
                  ],
                  "ref_direction": [
                    1,
                    0,
                    0
                  ],
                  "relative_to": "storey-1"
                },
                "ShapeType": "STRAIGHT_RUN_STAIR"
              },
              "id": "stair-1",
              "ifc_class": "IfcStair",
              "property_sets": {},
              "provenance": {
                "source": "issue-package-cross-storey"
              }
            }
          },
          {
            "evidence_refs": [
              "issue-package-cross-storey:/expected"
            ],
            "op": "add_entity",
            "operation_id": "operation-add-stair-flight-1",
            "target_id": "stair-flight-1",
            "value": {
              "attributes": {
                "Name": "Stepped flight",
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
                  "relative_to": "stair-1"
                },
                "Representation": {
                  "depth": 1000,
                  "direction": [
                    1,
                    0,
                    0
                  ],
                  "kind": "extruded_profile",
                  "profile": {
                    "kind": "polygon",
                    "points": [
                      [
                        0,
                        0
                      ],
                      [
                        0,
                        1000
                      ],
                      [
                        1200,
                        1000
                      ],
                      [
                        1200,
                        2000
                      ],
                      [
                        2400,
                        2000
                      ],
                      [
                        2400,
                        3000
                      ],
                      [
                        3500,
                        3000
                      ],
                      [
                        3500,
                        0
                      ],
                      [
                        0,
                        0
                      ]
                    ]
                  }
                }
              },
              "id": "stair-flight-1",
              "ifc_class": "IfcStairFlight",
              "property_sets": {},
              "provenance": {
                "source": "issue-package-cross-storey"
              }
            }
          },
          {
            "evidence_refs": [
              "issue-package-cross-storey:/expected"
            ],
            "op": "add_entity",
            "operation_id": "operation-add-roof-slab",
            "target_id": "roof-slab",
            "value": {
              "attributes": {
                "Name": "Roof slab",
                "ObjectPlacement": {
                  "axis": [
                    0,
                    0,
                    1
                  ],
                  "origin": [
                    4000,
                    3000,
                    3000
                  ],
                  "ref_direction": [
                    1,
                    0,
                    0
                  ],
                  "relative_to": "storey-2"
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
                    "x": 8000,
                    "y": 6000
                  }
                }
              },
              "id": "roof-slab",
              "ifc_class": "IfcSlab",
              "property_sets": {},
              "provenance": {
                "source": "issue-package-cross-storey"
              }
            }
          },
          {
            "evidence_refs": [
              "issue-package-cross-storey:/expected"
            ],
            "op": "add_relationship",
            "operation_id": "operation-add-void-first-floor-slab",
            "target_id": "rel-voids-first-floor-slab",
            "value": {
              "attributes": {
                "RelatedOpeningElement": "opening-first-floor-slab-stair",
                "RelatingBuildingElement": "first-floor-slab"
              },
              "id": "rel-voids-first-floor-slab",
              "ifc_class": "IfcRelVoidsElement",
              "provenance": {
                "source": "issue-package-cross-storey"
              }
            }
          },
          {
            "evidence_refs": [
              "issue-package-cross-storey:/expected"
            ],
            "op": "add_relationship",
            "operation_id": "operation-add-aggregate-stair-1-flight",
            "target_id": "aggregate-stair-1-flight",
            "value": {
              "attributes": {
                "RelatedObjects": [
                  "stair-flight-1"
                ],
                "RelatingObject": "stair-1"
              },
              "id": "aggregate-stair-1-flight",
              "ifc_class": "IfcRelAggregates",
              "provenance": {
                "source": "issue-package-cross-storey"
              }
            }
          }
        ],
        "schema_version": "text2ifc/bim-json-changeset/1.0",
        "scope_id": "scope-package-3",
        "source_issue_ids": [
          "issue-package-cross-storey"
        ]
      }
    }
  ],
  "dependency_ids": [],
  "gate_evidence": {
    "gate_results": {
      "candidate_hash": "sha256:03380dd3abd632d83e3b13b61b55031825d41a5d9c15903279a0cbef1a330ec4",
      "deterministic_gates": {
        "case_id": "d9fda4e730f9971d",
        "compile_reopen_success": true,
        "deterministic_gates_passed": true,
        "gate_summary": {
          "artifact_hashes": {
            "dynamic-gates.json": "028e025df4ab44cf2cc7c5cfc6bdb0cf5bd59abd060de18ca11ea44fab10fe9e",
            "expected-facts.json": "7f0c68e025ea61fb2fde45a1a0eb165c578a210b34ec8a2e39a5ce18238ed0ec",
            "generator/candidate.json": "03380dd3abd632d83e3b13b61b55031825d41a5d9c15903279a0cbef1a330ec4",
            "generator/validation.json": "6be6595f4f77090199203073905e3755e4015ff1a83b3412d64571cd872b4c41",
            "geometry-feedback.json": "498b01952d4749c457b5e209d9882c2b9a76ef6b16ba51be683ba44a39af72a0",
            "ifc-verification.json": "a2ad80151ac1c71fff97622e2069774e7f3991f4fd5e1aad0a92210a42cc8a62",
            "repair/route.json": "2d41407cb9d38c14a5d1478f0a2ea7e27612d6ef8e9ba2508349c3cfc8dcf91c",
            "semantic-coverage.json": "f31466552b29cdcf78ccf65223797e082a7723fa43d9554662d0b195a0da2ff6"
          },
          "candidate_hash": "03380dd3abd632d83e3b13b61b55031825d41a5d9c15903279a0cbef1a330ec4",
          "candidate_path": "generator/candidate.json",
          "case_id": "d9fda4e730f9971d",
          "evidence": {
            "compile_reopen": {
              "ifc_issues": [],
              "input_issues": [],
              "output_path": "dataset\\processed\\agent-demo\\phase6.5-live-two-storey-diagnostic-21\\runs\\d9fda4e730f9971d\\output.ifc",
              "success": true
            },
            "geometry": {
              "expectation_source": "design_brief_expected_facts",
              "issues": [],
              "metrics": {
                "case_id": "d9fda4e730f9971d",
                "floor_openings": {
                  "opening-first-floor-slab-stair": {
                    "bbox": {
                      "x": [
                        6.0,
                        8.0
                      ],
                      "y": [
                        1.0,
                        6.0
                      ],
                      "z": [
                        3.0,
                        3.15
                      ]
                    },
                    "ifc_class": "IfcOpeningElement"
                  }
                },
                "roof": {
                  "roof-slab": {
                    "bbox": {
                      "x": [
                        0.0,
                        8.0
                      ],
                      "y": [
                        0.0,
                        6.0
                      ],
                      "z": [
                        6.15,
                        6.300000000000001
                      ]
                    },
                    "ifc_class": "IfcSlab"
                  }
                },
                "slabs": {
                  "first-floor-slab": {
                    "bbox": {
                      "x": [
                        0.0,
                        8.0
                      ],
                      "y": [
                        0.0,
                        6.0
                      ],
                      "z": [
                        3.0,
                        3.15
                      ]
                    },
                    "ifc_class": "IfcSlab"
                  },
                  "ground-floor-slab": {
                    "bbox": {
                      "x": [
                        0.0,
                        8.0
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
                "stairs": {
                  "stair-1": {
                    "bbox": {
                      "x": [
                        6.5,
                        7.5
                      ],
                      "y": [
                        1.5,
                        5.0
                      ],
                      "z": [
                        0.15,
                        3.15
                      ]
                    },
                    "flight_ids": [
                      "stair-flight-1"
                    ],
                    "has_stepped_profile": true
                  }
                },
                "wall_set_convention": "primary",
                "walls": {}
              },
              "success": true
            },
            "repair_history": {
              "case_id": "d9fda4e730f9971d",
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
              "source_generator_dir": "dataset/processed/agent-demo/phase6.5-live-two-storey-diagnostic-21/runs/d9fda4e730f9971d/generator",
              "source_generator_response_id": "079413f1-adec-4c43-bfeb-5957c0daa357",
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
              "candidate_entity_count": 31,
              "capability_profile_hash": "sha256:1a9b5d81e65c07e3b578782744596bd9a56eb1ecf9702c94dbde5fd91681bbb5",
              "capability_profile_id": "text2ifc/semantic-capabilities/ifc2x3-bim-json-2.0/1.0",
              "case_id": "d9fda4e730f9971d",
              "custom_property_policy": {
                "counts_as_semantic_support": false,
                "state": "preserved_text_only"
              },
              "facts": [
                {
                  "coverage_state": "represented",
                  "path": "/known_facts/building/floor_slab_thickness_mm",
                  "reason": "Fact is inside the current supported semantic profile.",
                  "value": 150
                },
                {
                  "coverage_state": "represented",
                  "path": "/known_facts/building/outline/x_max",
                  "reason": "Fact is inside the current supported semantic profile.",
                  "value": 8000
                },
                {
                  "coverage_state": "represented",
                  "path": "/known_facts/building/outline/x_min",
                  "reason": "Fact is inside the current supported semantic profile.",
                  "value": 0
                },
                {
                  "coverage_state": "represented",
                  "path": "/known_facts/building/outline/y_max",
                  "reason": "Fact is inside the current supported semantic profile.",
                  "value": 6000
                },
                {
                  "coverage_state": "represented",
                  "path": "/known_facts/building/outline/y_min",
                  "reason": "Fact is inside the current supported semantic profile.",
                  "value": 0
                },
                {
                  "coverage_state": "represented",
                  "path": "/known_facts/building/roof_slab_thickness_mm",
                  "reason": "Fact is inside the current supported semantic profile.",
                  "value": 150
                },
                {
                  "coverage_state": "represented",
                  "path": "/known_facts/building/storey_count",
                  "reason": "Fact is inside the current supported semantic profile.",
                  "value": 2
                },
                {
                  "coverage_state": "represented",
                  "path": "/known_facts/building/wall_thickness_mm",
                  "reason": "Fact is inside the current supported semantic profile.",
                  "value": 200
                },
                {
                  "coverage_state": "represented",
                  "path": "/known_facts/floor_slabs",
                  "reason": "Fact is inside the current supported semantic profile.",
                  "value": [
                    {
                      "id": "ground-floor-slab",
                      "opening": null,
                      "storey": "storey-1",
                      "thickness_mm": 150,
                      "top_elevation_mm": 0
                    },
                    {
                      "id": "first-floor-slab",
                      "opening": {
                        "bounds": {
                          "x_max": 8000,
                          "x_min": 6000,
                          "y_max": 6000,
                          "y_min": 1000
                        }
                      },
                      "storey": "storey-2",
                      "thickness_mm": 150,
                      "top_elevation_mm": 3150
                    }
                  ]
                },
                {
                  "coverage_state": "represented",
                  "path": "/known_facts/roof_slab/bottom_elevation_mm",
                  "reason": "Fact is inside the current supported semantic profile.",
                  "value": 6150
                },
                {
                  "coverage_state": "represented",
                  "path": "/known_facts/roof_slab/id",
                  "reason": "Fact is inside the current supported semantic profile.",
                  "value": "roof-slab"
                },
                {
                  "coverage_state": "represented",
                  "path": "/known_facts/roof_slab/thickness_mm",
                  "reason": "Fact is inside the current supported semantic profile.",
                  "value": 150
                },
                {
                  "coverage_state": "represented",
                  "path": "/known_facts/stairs",
                  "reason": "Fact is inside the current supported semantic profile.",
                  "value": [
                    {
                      "bounds": {
                        "x_max": 7500,
                        "x_min": 6500,
                        "y_max": 5000,
                        "y_min": 1500
                      },
                      "end_elevation_mm": 3150,
                      "from_storey": "storey-1",
                      "id": "stair-1",
                      "run_direction": "+Y",
                      "start_elevation_mm": 150,
                      "to_storey": "storey-2",
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
                      "doors": [
                        {
                          "alignment": "horizontal_center",
                          "height_mm": 2100,
                          "host_wall": "storey-1-wall-south",
                          "id": "door-storey-1-south",
                          "sill_height_mm": 0,
                          "width_mm": 900
                        }
                      ],
                      "elevation_mm": 0,
                      "id": "storey-1",
                      "name": "首层",
                      "net_height_mm": 3000,
                      "spaces": [
                        {
                          "bounds": {
                            "x_max": 6000,
                            "x_min": 0,
                            "y_max": 6000,
                            "y_min": 0
                          },
                          "id": "space-office-1",
                          "name": "办公室"
                        },
                        {
                          "bounds": {
                            "x_max": 8000,
                            "x_min": 6000,
                            "y_max": 6000,
                            "y_min": 0
                          },
                          "id": "space-stair-hall",
                          "name": "楼梯间"
                        }
                      ],
                      "walls": [
                        {
                          "id": "storey-1-wall-south",
                          "side": "south",
                          "thickness_mm": 200
                        },
                        {
                          "id": "storey-1-wall-north",
                          "side": "north",
                          "thickness_mm": 200
                        },
                        {
                          "id": "storey-1-wall-east",
                          "side": "east",
                          "thickness_mm": 200
                        },
                        {
                          "id": "storey-1-wall-west",
                          "side": "west",
                          "thickness_mm": 200
                        }
                      ],
                      "windows": [
                        {
                          "alignment": "horizontal_center",
                          "height_mm": 1000,
                          "host_wall": "storey-1-wall-north",
                          "id": "window-storey-1-north",
                          "sill_height_mm": 900,
                          "width_mm": 1200
                        }
                      ]
                    },
                    {
                      "doors": [
                        {
                          "alignment": "horizontal_center",
                          "height_mm": 2100,
                          "host_wall": "storey-2-wall-south",
                          "id": "door-storey-2-south",
                          "sill_height_mm": 0,
                          "width_mm": 900
                        }
                      ],
                      "elevation_mm": 3150,
                      "id": "storey-2",
                      "name": "二层",
                      "net_height_mm": 3000,
                      "spaces": [
                        {
                          "bounds": {
                            "x_max": 6000,
                            "x_min": 0,
                            "y_max": 6000,
                            "y_min": 0
                          },
                          "id": "space-office-2",
                          "name": "办公室"
                        },
                        {
                          "bounds": {
                            "x_max": 8000,
                            "x_min": 6000,
                            "y_max": 1000,
                            "y_min": 0
                          },
                          "id": "space-stair-landing",
                          "name": "楼梯平台"
                        }
                      ],
                      "walls": [
                        {
                          "id": "storey-2-wall-south",
                          "side": "south",
                          "thickness_mm": 200
                        },
                        {
                          "id": "storey-2-wall-north",
                          "side": "north",
                          "thickness_mm": 200
                        },
                        {
                          "id": "storey-2-wall-east",
                          "side": "east",
                          "thickness_mm": 200
                        },
                        {
                          "id": "storey-2-wall-west",
                          "side": "west",
                          "thickness_mm": 200
                        }
                      ],
                      "windows": [
                        {
                          "alignment": "horizontal_center",
                          "height_mm": 1000,
                          "host_wall": "storey-2-wall-north",
                          "id": "window-storey-2-north",
                          "sill_height_mm": 900,
                          "width_mm": 1200
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
          "expected_facts_hash": "7f0c68e025ea61fb2fde45a1a0eb165c578a210b34ec8a2e39a5ce18238ed0ec",
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
                  "candidate_id": "door-storey-1-south",
                  "collection": "doors",
                  "expected_id": "door-storey-1-south",
                  "match_basis": "exact_brief_id"
                },
                {
                  "candidate_id": "door-storey-2-south",
                  "collection": "doors",
                  "expected_id": "door-storey-2-south",
                  "match_basis": "exact_brief_id"
                },
                {
                  "candidate_id": "space-office-1",
                  "collection": "spaces",
                  "expected_id": "space-office-1",
                  "match_basis": "exact_brief_id"
                },
                {
                  "candidate_id": "space-stair-hall",
                  "collection": "spaces",
                  "expected_id": "space-stair-hall",
                  "match_basis": "exact_brief_id"
                },
                {
                  "candidate_id": "space-office-2",
                  "collection": "spaces",
                  "expected_id": "space-office-2",
                  "match_basis": "exact_brief_id"
                },
                {
                  "candidate_id": "space-stair-landing",
                  "collection": "spaces",
                  "expected_id": "space-stair-landing",
                  "match_basis": "exact_brief_id"
                },
                {
                  "candidate_id": "window-storey-1-north",
                  "collection": "windows",
                  "expected_id": "window-storey-1-north",
                  "match_basis": "exact_brief_id"
                },
                {
                  "candidate_id": "window-storey-2-north",
                  "collection": "windows",
                  "expected_id": "window-storey-2-north",
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
            "case_id": "d9fda4e730f9971d",
            "floor_openings": {
              "opening-first-floor-slab-stair": {
                "bbox": {
                  "x": [
                    6.0,
                    8.0
                  ],
                  "y": [
                    1.0,
                    6.0
                  ],
                  "z": [
                    3.0,
                    3.15
                  ]
                },
                "ifc_class": "IfcOpeningElement"
              }
            },
            "roof": {
              "roof-slab": {
                "bbox": {
                  "x": [
                    0.0,
                    8.0
                  ],
                  "y": [
                    0.0,
                    6.0
                  ],
                  "z": [
                    6.15,
                    6.300000000000001
                  ]
                },
                "ifc_class": "IfcSlab"
              }
            },
            "slabs": {
              "first-floor-slab": {
                "bbox": {
                  "x": [
                    0.0,
                    8.0
                  ],
                  "y": [
                    0.0,
                    6.0
                  ],
                  "z": [
                    3.0,
                    3.15
                  ]
                },
                "ifc_class": "IfcSlab"
              },
              "ground-floor-slab": {
                "bbox": {
                  "x": [
                    0.0,
                    8.0
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
            "stairs": {
              "stair-1": {
                "bbox": {
                  "x": [
                    6.5,
                    7.5
                  ],
                  "y": [
                    1.5,
                    5.0
                  ],
                  "z": [
                    0.15,
                    3.15
                  ]
                },
                "flight_ids": [
                  "stair-flight-1"
                ],
                "has_stepped_profile": true
              }
            },
            "wall_set_convention": "primary",
            "walls": {}
          },
          "success": true
        },
        "geometry_success": true,
        "ifc_path": "dataset\\processed\\agent-demo\\phase6.5-live-two-storey-diagnostic-21\\runs\\d9fda4e730f9971d\\output.ifc",
        "ifc_verification": {
          "ifc_issues": [],
          "input_issues": [],
          "output_path": "dataset\\processed\\agent-demo\\phase6.5-live-two-storey-diagnostic-21\\runs\\d9fda4e730f9971d\\output.ifc",
          "success": true
        },
        "output_dir": "dataset\\processed\\agent-demo\\phase6.5-live-two-storey-diagnostic-21\\runs\\d9fda4e730f9971d",
        "semantic_geometry_expectation": {
          "case_id": "d9fda4e730f9971d",
          "floor_openings": {
            "opening-first-floor-slab-stair": {
              "bbox": {
                "x": [
                  6.0,
                  8.0
                ],
                "y": [
                  1.0,
                  6.0
                ],
                "z": [
                  3.0,
                  3.15
                ]
              },
              "host_slab_id": "first-floor-slab",
              "source_fact_refs": [
                "/known_facts/floor_slabs/1/openings/0"
              ]
            }
          },
          "roof": {
            "roof-slab": {
              "bbox": {
                "x": [
                  0.0,
                  8.0
                ],
                "y": [
                  0.0,
                  6.0
                ],
                "z": [
                  6.15,
                  6.3
                ]
              },
              "datum": "roof_bottom",
              "source_fact_refs": [
                "/known_facts/roof_slab"
              ]
            }
          },
          "schema_version": "text2ifc/design-geometry-expectation/1.0",
          "slabs": {
            "first-floor-slab": {
              "bbox": {
                "x": [
                  0.0,
                  8.0
                ],
                "y": [
                  0.0,
                  6.0
                ],
                "z": [
                  3.0,
                  3.15
                ]
              },
              "datum": "slab_top",
              "must_touch_walls": [],
              "source_fact_refs": [
                "/known_facts/floor_slabs/1"
              ]
            },
            "ground-floor-slab": {
              "bbox": {
                "x": [
                  0.0,
                  8.0
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
          "stairs": {
            "stair-1": {
              "bbox": {
                "x": [
                  6.5,
                  7.5
                ],
                "y": [
                  1.5,
                  5.0
                ],
                "z": [
                  0.15,
                  3.15
                ]
              },
              "flight_ids": [
                "stair-flight-1"
              ],
              "require_steps": true,
              "source_fact_refs": [
                "/known_facts/stairs/0"
              ]
            }
          },
          "tolerance": 0.05,
          "units": "METRE",
          "unresolved": [],
          "walls": {}
        },
        "stage": "candidate-gates",
        "valid": true
      },
      "revision_id": "revision-03"
    },
    "issues": [],
    "plan": {
      "changed_ids": [
        "aggregate-stair-1-flight",
        "door-storey-1-south",
        "door-storey-2-south",
        "first-floor-slab",
        "ground-floor-slab",
        "opening-door-storey-1-south",
        "opening-door-storey-2-south",
        "opening-first-floor-slab-stair",
        "opening-window-storey-1-north",
        "opening-window-storey-2-north",
        "rel-fills-door-storey-1-south",
        "rel-fills-door-storey-2-south",
        "rel-fills-window-storey-1-north",
        "rel-fills-window-storey-2-north",
        "rel-voids-door-storey-1-south",
        "rel-voids-door-storey-2-south",
        "rel-voids-first-floor-slab",
        "rel-voids-window-storey-1-north",
        "rel-voids-window-storey-2-north",
        "roof-slab",
        "space-office-1",
        "space-office-2",
        "space-stair-hall",
        "space-stair-landing",
        "stair-1",
        "stair-flight-1",
        "storey-1-wall-east",
        "storey-1-wall-north",
        "storey-1-wall-south",
        "storey-1-wall-west",
        "storey-2-wall-east",
        "storey-2-wall-north",
        "storey-2-wall-south",
        "storey-2-wall-west",
        "window-storey-1-north",
        "window-storey-2-north"
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
          "aggregate-stair-1-flight",
          "door-storey-1-south",
          "door-storey-2-south",
          "first-floor-slab",
          "ground-floor-slab",
          "opening-door-storey-1-south",
          "opening-door-storey-2-south",
          "opening-first-floor-slab-stair",
          "opening-window-storey-1-north",
          "opening-window-storey-2-north",
          "rel-fills-door-storey-1-south",
          "rel-fills-door-storey-2-south",
          "rel-fills-window-storey-1-north",
          "rel-fills-window-storey-2-north",
          "rel-voids-door-storey-1-south",
          "rel-voids-door-storey-2-south",
          "rel-voids-first-floor-slab",
          "rel-voids-window-storey-1-north",
          "rel-voids-window-storey-2-north",
          "roof-slab",
          "space-office-1",
          "space-office-2",
          "space-stair-hall",
          "space-stair-landing",
          "stair-1",
          "stair-flight-1",
          "storey-1-wall-east",
          "storey-1-wall-north",
          "storey-1-wall-south",
          "storey-1-wall-west",
          "storey-2-wall-east",
          "storey-2-wall-north",
          "storey-2-wall-south",
          "storey-2-wall-west",
          "window-storey-1-north",
          "window-storey-2-north"
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
          "storey-1",
          "storey-2"
        ],
        "unrelated_component_count": 0,
        "unrelated_component_preservation_rate": 1.0
      },
      "revision_binding": {
        "candidate_hash": "sha256:03380dd3abd632d83e3b13b61b55031825d41a5d9c15903279a0cbef1a330ec4",
        "expected_facts_hash": "sha256:7f0c68e025ea61fb2fde45a1a0eb165c578a210b34ec8a2e39a5ce18238ed0ec",
        "revision_id": "revision-03"
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
      "case_id": "d9fda4e730f9971d",
      "floor_openings": {
        "opening-first-floor-slab-stair": {
          "bbox": {
            "x": [
              6.0,
              8.0
            ],
            "y": [
              1.0,
              6.0
            ],
            "z": [
              3.0,
              3.15
            ]
          },
          "ifc_class": "IfcOpeningElement"
        }
      },
      "roof": {
        "roof-slab": {
          "bbox": {
            "x": [
              0.0,
              8.0
            ],
            "y": [
              0.0,
              6.0
            ],
            "z": [
              6.15,
              6.300000000000001
            ]
          },
          "ifc_class": "IfcSlab"
        }
      },
      "slabs": {
        "first-floor-slab": {
          "bbox": {
            "x": [
              0.0,
              8.0
            ],
            "y": [
              0.0,
              6.0
            ],
            "z": [
              3.0,
              3.15
            ]
          },
          "ifc_class": "IfcSlab"
        },
        "ground-floor-slab": {
          "bbox": {
            "x": [
              0.0,
              8.0
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
      "stairs": {
        "stair-1": {
          "bbox": {
            "x": [
              6.5,
              7.5
            ],
            "y": [
              1.5,
              5.0
            ],
            "z": [
              0.15,
              3.15
            ]
          },
          "flight_ids": [
            "stair-flight-1"
          ],
          "has_stepped_profile": true
        }
      },
      "wall_set_convention": "primary",
      "walls": {}
    },
    "success": true
  },
  "ifc_result": {
    "ifc_issues": [],
    "input_issues": [],
    "output_path": "dataset\\processed\\agent-demo\\phase6.5-live-two-storey-diagnostic-21\\runs\\d9fda4e730f9971d\\output.ifc",
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
      "target_id": "storey-1-wall-south",
      "value": {
        "attributes": {
          "Name": "南墙",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              4000,
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
            "depth": 3000,
            "direction": [
              0,
              0,
              1
            ],
            "kind": "extruded_profile",
            "profile": {
              "kind": "rectangle",
              "x": 8000,
              "y": 200
            }
          }
        },
        "id": "storey-1-wall-south",
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
      "target_id": "storey-1-wall-north",
      "value": {
        "attributes": {
          "Name": "北墙",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              4000,
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
            "depth": 3000,
            "direction": [
              0,
              0,
              1
            ],
            "kind": "extruded_profile",
            "profile": {
              "kind": "rectangle",
              "x": 8000,
              "y": 200
            }
          }
        },
        "id": "storey-1-wall-north",
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
      "target_id": "storey-1-wall-east",
      "value": {
        "attributes": {
          "Name": "东墙",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              8000,
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
        "id": "storey-1-wall-east",
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
      "target_id": "storey-1-wall-west",
      "value": {
        "attributes": {
          "Name": "西墙",
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
        "id": "storey-1-wall-west",
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
      "operation_id": "add-space-office-1",
      "target_id": "space-office-1",
      "value": {
        "attributes": {
          "InteriorOrExteriorSpace": "INTERNAL",
          "Name": "办公室",
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
              "y": 6000
            }
          }
        },
        "id": "space-office-1",
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
      "operation_id": "add-space-stair-hall",
      "target_id": "space-stair-hall",
      "value": {
        "attributes": {
          "InteriorOrExteriorSpace": "INTERNAL",
          "Name": "楼梯间",
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
            "depth": 3000,
            "direction": [
              0,
              0,
              1
            ],
            "kind": "extruded_profile",
            "profile": {
              "kind": "rectangle",
              "x": 2000,
              "y": 6000
            }
          }
        },
        "id": "space-stair-hall",
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
      "operation_id": "add-opening-door",
      "target_id": "opening-door-storey-1-south",
      "value": {
        "attributes": {
          "Name": "门洞",
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
            "relative_to": "storey-1-wall-south"
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
        "id": "opening-door-storey-1-south",
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
      "operation_id": "add-door",
      "target_id": "door-storey-1-south",
      "value": {
        "attributes": {
          "Name": "门",
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
            "relative_to": "opening-door-storey-1-south"
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
              "y": 50
            }
          }
        },
        "id": "door-storey-1-south",
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
      "operation_id": "add-opening-window",
      "target_id": "opening-window-storey-1-north",
      "value": {
        "attributes": {
          "Name": "窗洞",
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
            "relative_to": "storey-1-wall-north"
          },
          "Representation": {
            "depth": 1000,
            "direction": [
              0,
              0,
              1
            ],
            "kind": "extruded_profile",
            "profile": {
              "kind": "rectangle",
              "x": 1200,
              "y": 200
            }
          }
        },
        "id": "opening-window-storey-1-north",
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
      "operation_id": "add-window",
      "target_id": "window-storey-1-north",
      "value": {
        "attributes": {
          "Name": "窗",
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
            "relative_to": "opening-window-storey-1-north"
          },
          "OverallHeight": 1000,
          "OverallWidth": 1200,
          "Representation": {
            "depth": 1000,
            "direction": [
              0,
              0,
              1
            ],
            "kind": "extruded_profile",
            "profile": {
              "kind": "rectangle",
              "x": 1200,
              "y": 50
            }
          }
        },
        "id": "window-storey-1-north",
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
      "operation_id": "add-void-door",
      "target_id": "rel-voids-door-storey-1-south",
      "value": {
        "attributes": {
          "RelatedOpeningElement": "opening-door-storey-1-south",
          "RelatingBuildingElement": "storey-1-wall-south"
        },
        "id": "rel-voids-door-storey-1-south",
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
      "operation_id": "add-fill-door",
      "target_id": "rel-fills-door-storey-1-south",
      "value": {
        "attributes": {
          "RelatedBuildingElement": "door-storey-1-south",
          "RelatingOpeningElement": "opening-door-storey-1-south"
        },
        "id": "rel-fills-door-storey-1-south",
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
      "operation_id": "add-void-window",
      "target_id": "rel-voids-window-storey-1-north",
      "value": {
        "attributes": {
          "RelatedOpeningElement": "opening-window-storey-1-north",
          "RelatingBuildingElement": "storey-1-wall-north"
        },
        "id": "rel-voids-window-storey-1-north",
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
      "operation_id": "add-fill-window",
      "target_id": "rel-fills-window-storey-1-north",
      "value": {
        "attributes": {
          "RelatedBuildingElement": "window-storey-1-north",
          "RelatingOpeningElement": "opening-window-storey-1-north"
        },
        "id": "rel-fills-window-storey-1-north",
        "ifc_class": "IfcRelFillsElement",
        "provenance": {
          "source": "issue-package-storey-1"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-storey-2:/expected"
      ],
      "op": "add_entity",
      "operation_id": "operation-add-storey-2-wall-south",
      "target_id": "storey-2-wall-south",
      "value": {
        "attributes": {
          "Name": "首层南外墙",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              4000,
              100,
              0
            ],
            "ref_direction": [
              1,
              0,
              0
            ],
            "relative_to": "storey-2"
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
              "x": 8000,
              "y": 200
            }
          }
        },
        "id": "storey-2-wall-south",
        "ifc_class": "IfcWall",
        "property_sets": {},
        "provenance": {
          "source": "issue-package-storey-2"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-storey-2:/expected"
      ],
      "op": "add_entity",
      "operation_id": "operation-add-storey-2-wall-north",
      "target_id": "storey-2-wall-north",
      "value": {
        "attributes": {
          "Name": "首层北外墙",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              4000,
              5900,
              0
            ],
            "ref_direction": [
              1,
              0,
              0
            ],
            "relative_to": "storey-2"
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
              "x": 8000,
              "y": 200
            }
          }
        },
        "id": "storey-2-wall-north",
        "ifc_class": "IfcWall",
        "property_sets": {},
        "provenance": {
          "source": "issue-package-storey-2"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-storey-2:/expected"
      ],
      "op": "add_entity",
      "operation_id": "operation-add-storey-2-wall-east",
      "target_id": "storey-2-wall-east",
      "value": {
        "attributes": {
          "Name": "首层东外墙",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              7900,
              3000,
              0
            ],
            "ref_direction": [
              0,
              1,
              0
            ],
            "relative_to": "storey-2"
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
        "id": "storey-2-wall-east",
        "ifc_class": "IfcWall",
        "property_sets": {},
        "provenance": {
          "source": "issue-package-storey-2"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-storey-2:/expected"
      ],
      "op": "add_entity",
      "operation_id": "operation-add-storey-2-wall-west",
      "target_id": "storey-2-wall-west",
      "value": {
        "attributes": {
          "Name": "首层西外墙",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              100,
              3000,
              0
            ],
            "ref_direction": [
              0,
              1,
              0
            ],
            "relative_to": "storey-2"
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
        "id": "storey-2-wall-west",
        "ifc_class": "IfcWall",
        "property_sets": {},
        "provenance": {
          "source": "issue-package-storey-2"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-storey-2:/expected"
      ],
      "op": "add_entity",
      "operation_id": "operation-add-space-office-2",
      "target_id": "space-office-2",
      "value": {
        "attributes": {
          "InteriorOrExteriorSpace": "INTERNAL",
          "Name": "办公室",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              3000,
              3000,
              0
            ],
            "ref_direction": [
              1,
              0,
              0
            ],
            "relative_to": "storey-2"
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
              "y": 6000
            }
          }
        },
        "id": "space-office-2",
        "ifc_class": "IfcSpace",
        "property_sets": {},
        "provenance": {
          "source": "issue-package-storey-2"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-storey-2:/expected"
      ],
      "op": "add_entity",
      "operation_id": "operation-add-space-stair-landing",
      "target_id": "space-stair-landing",
      "value": {
        "attributes": {
          "InteriorOrExteriorSpace": "INTERNAL",
          "Name": "楼梯平台",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              7000,
              500,
              0
            ],
            "ref_direction": [
              1,
              0,
              0
            ],
            "relative_to": "storey-2"
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
              "x": 2000,
              "y": 1000
            }
          }
        },
        "id": "space-stair-landing",
        "ifc_class": "IfcSpace",
        "property_sets": {},
        "provenance": {
          "source": "issue-package-storey-2"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-storey-2:/expected"
      ],
      "op": "add_entity",
      "operation_id": "operation-add-opening-door-storey-2-south",
      "target_id": "opening-door-storey-2-south",
      "value": {
        "attributes": {
          "Name": "Opening for door-storey-2-south",
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
            "relative_to": "storey-2-wall-south"
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
        "id": "opening-door-storey-2-south",
        "ifc_class": "IfcOpeningElement",
        "property_sets": {},
        "provenance": {
          "source": "issue-package-storey-2"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-storey-2:/expected"
      ],
      "op": "add_entity",
      "operation_id": "operation-add-door-storey-2-south",
      "target_id": "door-storey-2-south",
      "value": {
        "attributes": {
          "Name": "首层南门",
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
            "relative_to": "opening-door-storey-2-south"
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
              "y": 40
            }
          }
        },
        "id": "door-storey-2-south",
        "ifc_class": "IfcDoor",
        "property_sets": {},
        "provenance": {
          "source": "issue-package-storey-2"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-storey-2:/expected"
      ],
      "op": "add_entity",
      "operation_id": "operation-add-opening-window-storey-2-north",
      "target_id": "opening-window-storey-2-north",
      "value": {
        "attributes": {
          "Name": "Opening for window-storey-2-north",
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
            "relative_to": "storey-2-wall-north"
          },
          "Representation": {
            "depth": 1000,
            "direction": [
              0,
              0,
              1
            ],
            "kind": "extruded_profile",
            "profile": {
              "kind": "rectangle",
              "x": 1200,
              "y": 200
            }
          }
        },
        "id": "opening-window-storey-2-north",
        "ifc_class": "IfcOpeningElement",
        "property_sets": {},
        "provenance": {
          "source": "issue-package-storey-2"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-storey-2:/expected"
      ],
      "op": "add_entity",
      "operation_id": "operation-add-window-storey-2-north",
      "target_id": "window-storey-2-north",
      "value": {
        "attributes": {
          "Name": "首层北窗",
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
            "relative_to": "opening-window-storey-2-north"
          },
          "OverallHeight": 1000,
          "OverallWidth": 1200,
          "Representation": {
            "depth": 1000,
            "direction": [
              0,
              0,
              1
            ],
            "kind": "extruded_profile",
            "profile": {
              "kind": "rectangle",
              "x": 1200,
              "y": 100
            }
          }
        },
        "id": "window-storey-2-north",
        "ifc_class": "IfcWindow",
        "property_sets": {},
        "provenance": {
          "source": "issue-package-storey-2"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-storey-2:/expected"
      ],
      "op": "add_relationship",
      "operation_id": "operation-add-rel-voids-door-storey-2-south",
      "target_id": "rel-voids-door-storey-2-south",
      "value": {
        "attributes": {
          "RelatedOpeningElement": "opening-door-storey-2-south",
          "RelatingBuildingElement": "storey-2-wall-south"
        },
        "id": "rel-voids-door-storey-2-south",
        "ifc_class": "IfcRelVoidsElement",
        "provenance": {
          "source": "issue-package-storey-2"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-storey-2:/expected"
      ],
      "op": "add_relationship",
      "operation_id": "operation-add-rel-fills-door-storey-2-south",
      "target_id": "rel-fills-door-storey-2-south",
      "value": {
        "attributes": {
          "RelatedBuildingElement": "door-storey-2-south",
          "RelatingOpeningElement": "opening-door-storey-2-south"
        },
        "id": "rel-fills-door-storey-2-south",
        "ifc_class": "IfcRelFillsElement",
        "provenance": {
          "source": "issue-package-storey-2"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-storey-2:/expected"
      ],
      "op": "add_relationship",
      "operation_id": "operation-add-rel-voids-window-storey-2-north",
      "target_id": "rel-voids-window-storey-2-north",
      "value": {
        "attributes": {
          "RelatedOpeningElement": "opening-window-storey-2-north",
          "RelatingBuildingElement": "storey-2-wall-north"
        },
        "id": "rel-voids-window-storey-2-north",
        "ifc_class": "IfcRelVoidsElement",
        "provenance": {
          "source": "issue-package-storey-2"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-storey-2:/expected"
      ],
      "op": "add_relationship",
      "operation_id": "operation-add-rel-fills-window-storey-2-north",
      "target_id": "rel-fills-window-storey-2-north",
      "value": {
        "attributes": {
          "RelatedBuildingElement": "window-storey-2-north",
          "RelatingOpeningElement": "opening-window-storey-2-north"
        },
        "id": "rel-fills-window-storey-2-north",
        "ifc_class": "IfcRelFillsElement",
        "provenance": {
          "source": "issue-package-storey-2"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-cross-storey:/expected"
      ],
      "op": "add_entity",
      "operation_id": "operation-add-ground-floor-slab",
      "target_id": "ground-floor-slab",
      "value": {
        "attributes": {
          "Name": "Ground floor slab",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              4000,
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
              "x": 8000,
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
    },
    {
      "evidence_refs": [
        "issue-package-cross-storey:/expected"
      ],
      "op": "add_entity",
      "operation_id": "operation-add-first-floor-slab",
      "target_id": "first-floor-slab",
      "value": {
        "attributes": {
          "Name": "First floor slab",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              4000,
              3000,
              -150
            ],
            "ref_direction": [
              1,
              0,
              0
            ],
            "relative_to": "storey-2"
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
              "x": 8000,
              "y": 6000
            }
          }
        },
        "id": "first-floor-slab",
        "ifc_class": "IfcSlab",
        "property_sets": {},
        "provenance": {
          "source": "issue-package-cross-storey"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-cross-storey:/expected"
      ],
      "op": "add_entity",
      "operation_id": "operation-add-opening-first-floor-slab-stair",
      "target_id": "opening-first-floor-slab-stair",
      "value": {
        "attributes": {
          "Name": "Stair opening in first floor slab",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              3000,
              500,
              0
            ],
            "ref_direction": [
              1,
              0,
              0
            ],
            "relative_to": "first-floor-slab"
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
              "x": 2000,
              "y": 5000
            }
          }
        },
        "id": "opening-first-floor-slab-stair",
        "ifc_class": "IfcOpeningElement",
        "property_sets": {},
        "provenance": {
          "source": "issue-package-cross-storey"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-cross-storey:/expected"
      ],
      "op": "add_entity",
      "operation_id": "operation-add-stair-1",
      "target_id": "stair-1",
      "value": {
        "attributes": {
          "Name": "Main stair",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              6500,
              1500,
              150
            ],
            "ref_direction": [
              1,
              0,
              0
            ],
            "relative_to": "storey-1"
          },
          "ShapeType": "STRAIGHT_RUN_STAIR"
        },
        "id": "stair-1",
        "ifc_class": "IfcStair",
        "property_sets": {},
        "provenance": {
          "source": "issue-package-cross-storey"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-cross-storey:/expected"
      ],
      "op": "add_entity",
      "operation_id": "operation-add-stair-flight-1",
      "target_id": "stair-flight-1",
      "value": {
        "attributes": {
          "Name": "Stepped flight",
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
            "relative_to": "stair-1"
          },
          "Representation": {
            "depth": 1000,
            "direction": [
              1,
              0,
              0
            ],
            "kind": "extruded_profile",
            "profile": {
              "kind": "polygon",
              "points": [
                [
                  0,
                  0
                ],
                [
                  0,
                  1000
                ],
                [
                  1200,
                  1000
                ],
                [
                  1200,
                  2000
                ],
                [
                  2400,
                  2000
                ],
                [
                  2400,
                  3000
                ],
                [
                  3500,
                  3000
                ],
                [
                  3500,
                  0
                ],
                [
                  0,
                  0
                ]
              ]
            }
          }
        },
        "id": "stair-flight-1",
        "ifc_class": "IfcStairFlight",
        "property_sets": {},
        "provenance": {
          "source": "issue-package-cross-storey"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-cross-storey:/expected"
      ],
      "op": "add_entity",
      "operation_id": "operation-add-roof-slab",
      "target_id": "roof-slab",
      "value": {
        "attributes": {
          "Name": "Roof slab",
          "ObjectPlacement": {
            "axis": [
              0,
              0,
              1
            ],
            "origin": [
              4000,
              3000,
              3000
            ],
            "ref_direction": [
              1,
              0,
              0
            ],
            "relative_to": "storey-2"
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
              "x": 8000,
              "y": 6000
            }
          }
        },
        "id": "roof-slab",
        "ifc_class": "IfcSlab",
        "property_sets": {},
        "provenance": {
          "source": "issue-package-cross-storey"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-cross-storey:/expected"
      ],
      "op": "add_relationship",
      "operation_id": "operation-add-void-first-floor-slab",
      "target_id": "rel-voids-first-floor-slab",
      "value": {
        "attributes": {
          "RelatedOpeningElement": "opening-first-floor-slab-stair",
          "RelatingBuildingElement": "first-floor-slab"
        },
        "id": "rel-voids-first-floor-slab",
        "ifc_class": "IfcRelVoidsElement",
        "provenance": {
          "source": "issue-package-cross-storey"
        }
      }
    },
    {
      "evidence_refs": [
        "issue-package-cross-storey:/expected"
      ],
      "op": "add_relationship",
      "operation_id": "operation-add-aggregate-stair-1-flight",
      "target_id": "aggregate-stair-1-flight",
      "value": {
        "attributes": {
          "RelatedObjects": [
            "stair-flight-1"
          ],
          "RelatingObject": "stair-1"
        },
        "id": "aggregate-stair-1-flight",
        "ifc_class": "IfcRelAggregates",
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
      "candidate_hash": "sha256:ccccf772954121e071f21971746ed38df40e51932da032e8cadc8a3b498a3461",
      "classification": "changeset",
      "frozen_component_count": 8,
      "gate_issue_count": 0,
      "package_id": "package-storey-1",
      "pre_apply_status": "partial_not_formal",
      "response_id": "05b39a07-177c-4d86-9d09-7b23dde05221",
      "revision_id": "revision-01",
      "status": "accepted"
    },
    {
      "artifact_dir": "package-02-package-storey-2",
      "attempt_count": 1,
      "candidate_hash": "sha256:af7edb67931195bae237814de9df39bacd354e5db6f5cb4090647f73ba58e312",
      "classification": "changeset",
      "frozen_component_count": 22,
      "gate_issue_count": 0,
      "package_id": "package-storey-2",
      "pre_apply_status": "partial_not_formal",
      "response_id": "687e2831-3f13-429f-83a6-9ea2fd622142",
      "revision_id": "revision-02",
      "status": "accepted"
    },
    {
      "artifact_dir": "package-03-package-cross-storey",
      "attempt_count": 1,
      "candidate_hash": "sha256:03380dd3abd632d83e3b13b61b55031825d41a5d9c15903279a0cbef1a330ec4",
      "classification": "changeset",
      "frozen_component_count": 36,
      "gate_issue_count": 0,
      "package_id": "package-cross-storey",
      "pre_apply_status": "partial_not_formal",
      "response_id": "079413f1-adec-4c43-bfeb-5957c0daa357",
      "revision_id": "revision-03",
      "status": "accepted"
    }
  ],
  "preservation": {
    "changed_ids": [
      "aggregate-stair-1-flight",
      "door-storey-1-south",
      "door-storey-2-south",
      "first-floor-slab",
      "ground-floor-slab",
      "opening-door-storey-1-south",
      "opening-door-storey-2-south",
      "opening-first-floor-slab-stair",
      "opening-window-storey-1-north",
      "opening-window-storey-2-north",
      "rel-fills-door-storey-1-south",
      "rel-fills-door-storey-2-south",
      "rel-fills-window-storey-1-north",
      "rel-fills-window-storey-2-north",
      "rel-voids-door-storey-1-south",
      "rel-voids-door-storey-2-south",
      "rel-voids-first-floor-slab",
      "rel-voids-window-storey-1-north",
      "rel-voids-window-storey-2-north",
      "roof-slab",
      "space-office-1",
      "space-office-2",
      "space-stair-hall",
      "space-stair-landing",
      "stair-1",
      "stair-flight-1",
      "storey-1-wall-east",
      "storey-1-wall-north",
      "storey-1-wall-south",
      "storey-1-wall-west",
      "storey-2-wall-east",
      "storey-2-wall-north",
      "storey-2-wall-south",
      "storey-2-wall-west",
      "window-storey-1-north",
      "window-storey-2-north"
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
      "storey-1",
      "storey-2"
    ],
    "unrelated_component_count": 0,
    "unrelated_component_preservation_rate": 1.0
  },
  "revision": {
    "artifacts": {
      "candidate": "package-03-package-cross-storey/workspace-after.json"
    },
    "candidate_hash": "sha256:03380dd3abd632d83e3b13b61b55031825d41a5d9c15903279a0cbef1a330ec4",
    "component_hashes": {
      "aggregate-building-storeys": "sha256:c9acb3bcf78532f2a86f434403a1edb5edf398228ff2a2d6b713d5f2c4af67cb",
      "aggregate-project-site": "sha256:456b0a2ec791c6c20d7efdda199726d8f9df127fd2739962aceb07dacb1f2567",
      "aggregate-site-building": "sha256:9ccdeec022f78745ceb756d48903226706f909c0db1992457f23fffca5da02d4",
      "aggregate-stair-1-flight": "sha256:115d5b81a92fc9c380a1be96f14e10229ded65f25f136a365c5933eabf5179c0",
      "building-main": "sha256:d2fac45e699944c2dd75aeb376ce156232c45dac25ab318fdc2a4593028a14ad",
      "door-storey-1-south": "sha256:64e3aa7ac385ac42178b2d14966972efaf08d9e006ca8fdeebbc307b94b6ee5c",
      "door-storey-2-south": "sha256:e997529d87551e2d9f3f9133c6f0663126a990f2d48172efdf18ee3223f3ed01",
      "first-floor-slab": "sha256:b9bfeec549e3cc4fd75bbb343e7560db5a16e6fa6fb2b07e928979b381fd1f27",
      "ground-floor-slab": "sha256:7e7032a94318438c340f06f923166306b98a55d26a64158ea03f07c83dd7e2ab",
      "opening-door-storey-1-south": "sha256:966a4024fc2e281418657957404c00155652c4da1d8eb24ddb25f1b772df3c5c",
      "opening-door-storey-2-south": "sha256:11f83baf480fdcc87409a8c90eaef66381be8107102a65296d35501ff534f982",
      "opening-first-floor-slab-stair": "sha256:1102b8e3d9e81cd81de78dd5f55ca300962e00dded727c60fd80720ab81e6224",
      "opening-window-storey-1-north": "sha256:7948e43db5560d7af4c05cdc7571561056132a5d82eaaa7b1faa5705d6ef32cc",
      "opening-window-storey-2-north": "sha256:7b40b85236ff02ce18d86d5a02b6852ac07a264d4eda86624522a8b3fac464ae",
      "project-main": "sha256:9b165163ddbb7d9c4ae8832db8391cf20e41cb9bdd4b1d99f6a3e6cb78a071d1",
      "rel-fills-door-storey-1-south": "sha256:c8e7fdd7ccde503dedf3fd8096413048cffa0a643ee3c7280c2ba46b70637e14",
      "rel-fills-door-storey-2-south": "sha256:da5e29da180424857a751d7b65d1e848e93df7f43b242b5cee1c864db3cf74cd",
      "rel-fills-window-storey-1-north": "sha256:d193ca0821775e43a7fbd7d945b773511e101cd73df99a9d00eadeaa3c236149",
      "rel-fills-window-storey-2-north": "sha256:702f7aff877b0a33bc227222f9505ddbb26cb141d417e42c92a14bf985ca06c3",
      "rel-voids-door-storey-1-south": "sha256:41560d62f89b3f979d31093cbdd84093175219cd0a15ba08aa6b9d15d7fa683a",
      "rel-voids-door-storey-2-south": "sha256:9ed5f7589acfe6d04b76a2c1b61b7ccf259fcef7273ba1b2664e20d7e44e9ae4",
      "rel-voids-first-floor-slab": "sha256:fa561bbec2199d3da19034002d502fb32c9bf06ad389453458c6cd32b65a3a91",
      "rel-voids-window-storey-1-north": "sha256:f1df604787ae9ed8f8d6ffec0e981f3475095f7d8ea9851c6fdff2b3c38f0ebd",
      "rel-voids-window-storey-2-north": "sha256:966acaa52036dc05b9fa2449eff13e37023955fa0754b6bb2b2255d5d4f34064",
      "roof-slab": "sha256:bf1704869547766d9322c010f26a0453bd4a6cb5575e0d3ec00fbd67bac71532",
      "site-main": "sha256:d5dfa3ad348be9625c631e2a45e4f77a67a485791c961139b0c18d37314ff3e5",
      "space-office-1": "sha256:bd8db1a48492bfbe0150f9bf7cdfee191b10a641113849aeef0fd9e68b305f02",
      "space-office-2": "sha256:ef7ac8d0dd0470806641f5cb08025933dc094d61551c9fcbd91065409c04a68d",
      "space-stair-hall": "sha256:70c96deb0c6f9840ebd2014706ec350486faa348645f03d4e624dd076b975deb",
      "space-stair-landing": "sha256:f357004692c055dc7fe72276f6b66e65600c350ebc51b6da09188318f183967d",
      "stair-1": "sha256:75d78b38868fe870f5863c4d61ebe47f7af7621083dcc64d61025a21e178631e",
      "stair-flight-1": "sha256:2b0d74971dbd00960ee668b526f767ffe4ea10a82b284763fad4945d0fd3482a",
      "storey-1": "sha256:99610a8921148fed2654c8a0ceafe7504b69fc54d56ddd6fc49173e89848fee5",
      "storey-1-wall-east": "sha256:2ec5336a8311879a7f323d334a80b61fa2db40d6c570b95630ee09a8c33e5693",
      "storey-1-wall-north": "sha256:247678c848469b305260cd6a3708e65329cb5b855bbba242a5f9961abddd3947",
      "storey-1-wall-south": "sha256:fbb1886a93289195820aead1b021dfcc7fbae109a0da77e557ae99928e322fb4",
      "storey-1-wall-west": "sha256:5829dd68fc8ee85a5658908f68c1edb44fe75ac730eff48784293cfb15dcc4bb",
      "storey-2": "sha256:69d2476948b7d971a1898bcc95d5e6fe70727c47007f3b354fae3f6692111c40",
      "storey-2-wall-east": "sha256:cce064e94a617af9ff411d2be4aad9788aa9970ab065d0a0d26b366f7ef3b87f",
      "storey-2-wall-north": "sha256:f52ff0300b98e91eebba54132c0ac67fbaeccbed677df552d5cb58dd7f926c81",
      "storey-2-wall-south": "sha256:c85e7e1d51b9adb6fbe17f5854262fa72ffc1ed4649bb2ca5ee191541c9891e4",
      "storey-2-wall-west": "sha256:819d1ca95a32f2e3765e9c4b4b0db4fb9b0076c21ea0bf7cb6469f15cd6e759c",
      "window-storey-1-north": "sha256:f1f3dcb16daab80652f8ec758d878833e16e03c638fabdf8f3b9a116c67e1068",
      "window-storey-2-north": "sha256:85bef3719d5b82c358cf663a1043611d75d080cdcd4206f483b1d74c6f3bd049"
    },
    "expected_facts_hash": "sha256:7f0c68e025ea61fb2fde45a1a0eb165c578a210b34ec8a2e39a5ce18238ed0ec",
    "parent_revision_id": "revision-02",
    "revision_id": "revision-03",
    "schema_version": "text2ifc/bim-json-revision/1.0",
    "sequence": 3,
    "source_route": "staged_composition"
  },
  "scopes": [],
  "source_issue_ids": [
    "issue-package-cross-storey",
    "issue-package-storey-1",
    "issue-package-storey-2"
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

- [runs/d9fda4e730f9971d/session-export.json](runs/d9fda4e730f9971d/session-export.json)

## Session DB Evidence

### Events

```json
[
  {
    "created_at": "2026-07-12T14:56:42+00:00",
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
    "created_at": "2026-07-12T15:00:54+00:00",
    "event_index": 1,
    "event_type": "generator_completed",
    "payload": {
      "case_id": "d9fda4e730f9971d",
      "classification": "formal",
      "contract_valid": true,
      "evidence_class": "provider-backed-staged",
      "output_dir": "dataset\\processed\\agent-demo\\phase6.5-live-two-storey-diagnostic-21\\runs\\d9fda4e730f9971d\\generator",
      "response_id": "079413f1-adec-4c43-bfeb-5957c0daa357",
      "stage": "generate",
      "status": "formal",
      "strict_output_contract_valid": true,
      "valid": true
    }
  },
  {
    "created_at": "2026-07-12T15:00:54+00:00",
    "event_index": 2,
    "event_type": "semantic_coverage_completed",
    "payload": {
      "blocking_fact_count": 0,
      "capability_profile_hash": "sha256:1a9b5d81e65c07e3b578782744596bd9a56eb1ecf9702c94dbde5fd91681bbb5",
      "capability_profile_id": "text2ifc/semantic-capabilities/ifc2x3-bim-json-2.0/1.0",
      "case_id": "d9fda4e730f9971d",
      "coverage": {
        "blocking_facts": [],
        "candidate_entity_count": 31,
        "capability_profile_hash": "sha256:1a9b5d81e65c07e3b578782744596bd9a56eb1ecf9702c94dbde5fd91681bbb5",
        "capability_profile_id": "text2ifc/semantic-capabilities/ifc2x3-bim-json-2.0/1.0",
        "case_id": "d9fda4e730f9971d",
        "custom_property_policy": {
          "counts_as_semantic_support": false,
          "state": "preserved_text_only"
        },
        "facts": [
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/floor_slab_thickness_mm",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 150
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/outline/x_max",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 8000
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/outline/x_min",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 0
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/outline/y_max",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 6000
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/outline/y_min",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 0
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/roof_slab_thickness_mm",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 150
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/storey_count",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 2
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/building/wall_thickness_mm",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 200
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/floor_slabs",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": [
              {
                "id": "ground-floor-slab",
                "opening": null,
                "storey": "storey-1",
                "thickness_mm": 150,
                "top_elevation_mm": 0
              },
              {
                "id": "first-floor-slab",
                "opening": {
                  "bounds": {
                    "x_max": 8000,
                    "x_min": 6000,
                    "y_max": 6000,
                    "y_min": 1000
                  }
                },
                "storey": "storey-2",
                "thickness_mm": 150,
                "top_elevation_mm": 3150
              }
            ]
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/roof_slab/bottom_elevation_mm",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 6150
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/roof_slab/id",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": "roof-slab"
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/roof_slab/thickness_mm",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": 150
          },
          {
            "coverage_state": "represented",
            "path": "/known_facts/stairs",
            "reason": "Fact is inside the current supported semantic profile.",
            "value": [
              {
                "bounds": {
                  "x_max": 7500,
                  "x_min": 6500,
                  "y_max": 5000,
                  "y_min": 1500
                },
                "end_elevation_mm": 3150,
                "from_storey": "storey-1",
                "id": "stair-1",
                "run_direction": "+Y",
                "start_elevation_mm": 150,
                "to_storey": "storey-2",
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
                "doors": [
                  {
                    "alignment": "horizontal_center",
                    "height_mm": 2100,
                    "host_wall": "storey-1-wall-south",
                    "id": "door-storey-1-south",
                    "sill_height_mm": 0,
                    "width_mm": 900
                  }
                ],
                "elevation_mm": 0,
                "id": "storey-1",
                "name": "首层",
                "net_height_mm": 3000,
                "spaces": [
                  {
                    "bounds": {
                      "x_max": 6000,
                      "x_min": 0,
                      "y_max": 6000,
                      "y_min": 0
                    },
                    "id": "space-office-1",
                    "name": "办公室"
                  },
                  {
                    "bounds": {
                      "x_max": 8000,
                      "x_min": 6000,
                      "y_max": 6000,
                      "y_min": 0
                    },
                    "id": "space-stair-hall",
                    "name": "楼梯间"
                  }
                ],
                "walls": [
                  {
                    "id": "storey-1-wall-south",
                    "side": "south",
                    "thickness_mm": 200
                  },
                  {
                    "id": "storey-1-wall-north",
                    "side": "north",
                    "thickness_mm": 200
                  },
                  {
                    "id": "storey-1-wall-east",
                    "side": "east",
                    "thickness_mm": 200
                  },
                  {
                    "id": "storey-1-wall-west",
                    "side": "west",
                    "thickness_mm": 200
                  }
                ],
                "windows": [
                  {
                    "alignment": "horizontal_center",
                    "height_mm": 1000,
                    "host_wall": "storey-1-wall-north",
                    "id": "window-storey-1-north",
                    "sill_height_mm": 900,
                    "width_mm": 1200
                  }
                ]
              },
              {
                "doors": [
                  {
                    "alignment": "horizontal_center",
                    "height_mm": 2100,
                    "host_wall": "storey-2-wall-south",
                    "id": "door-storey-2-south",
                    "sill_height_mm": 0,
                    "width_mm": 900
                  }
                ],
                "elevation_mm": 3150,
                "id": "storey-2",
                "name": "二层",
                "net_height_mm": 3000,
                "spaces": [
                  {
                    "bounds": {
                      "x_max": 6000,
                      "x_min": 0,
                      "y_max": 6000,
                      "y_min": 0
                    },
                    "id": "space-office-2",
                    "name": "办公室"
                  },
                  {
                    "bounds": {
                      "x_max": 8000,
                      "x_min": 6000,
                      "y_max": 1000,
                      "y_min": 0
                    },
                    "id": "space-stair-landing",
                    "name": "楼梯平台"
                  }
                ],
                "walls": [
                  {
                    "id": "storey-2-wall-south",
                    "side": "south",
                    "thickness_mm": 200
                  },
                  {
                    "id": "storey-2-wall-north",
                    "side": "north",
                    "thickness_mm": 200
                  },
                  {
                    "id": "storey-2-wall-east",
                    "side": "east",
                    "thickness_mm": 200
                  },
                  {
                    "id": "storey-2-wall-west",
                    "side": "west",
                    "thickness_mm": 200
                  }
                ],
                "windows": [
                  {
                    "alignment": "horizontal_center",
                    "height_mm": 1000,
                    "host_wall": "storey-2-wall-north",
                    "id": "window-storey-2-north",
                    "sill_height_mm": 900,
                    "width_mm": 1200
                  }
                ]
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
    "created_at": "2026-07-12T15:00:54+00:00",
    "event_index": 3,
    "event_type": "repair_completed",
    "payload": {
      "case_id": "d9fda4e730f9971d",
      "evidence_class": "live-derived-no-call",
      "output_dir": "dataset/processed/agent-demo/phase6.5-live-two-storey-diagnostic-21/runs/d9fda4e730f9971d/repair",
      "provider_call_count": 0,
      "repair_attempts": [],
      "route": "no_repair_needed",
      "source_generator_response_id": "079413f1-adec-4c43-bfeb-5957c0daa357",
      "stage": "repair",
      "valid": true
    }
  },
  {
    "created_at": "2026-07-12T15:00:55+00:00",
    "event_index": 4,
    "event_type": "candidate_gates_completed",
    "payload": {
      "case_id": "d9fda4e730f9971d",
      "compile_reopen_success": true,
      "deterministic_gates_passed": true,
      "gate_summary": {
        "artifact_hashes": {
          "dynamic-gates.json": "028e025df4ab44cf2cc7c5cfc6bdb0cf5bd59abd060de18ca11ea44fab10fe9e",
          "expected-facts.json": "7f0c68e025ea61fb2fde45a1a0eb165c578a210b34ec8a2e39a5ce18238ed0ec",
          "generator/candidate.json": "03380dd3abd632d83e3b13b61b55031825d41a5d9c15903279a0cbef1a330ec4",
          "generator/validation.json": "6be6595f4f77090199203073905e3755e4015ff1a83b3412d64571cd872b4c41",
          "geometry-feedback.json": "498b01952d4749c457b5e209d9882c2b9a76ef6b16ba51be683ba44a39af72a0",
          "ifc-verification.json": "a2ad80151ac1c71fff97622e2069774e7f3991f4fd5e1aad0a92210a42cc8a62",
          "repair/route.json": "2d41407cb9d38c14a5d1478f0a2ea7e27612d6ef8e9ba2508349c3cfc8dcf91c",
          "semantic-coverage.json": "f31466552b29cdcf78ccf65223797e082a7723fa43d9554662d0b195a0da2ff6"
        },
        "candidate_hash": "03380dd3abd632d83e3b13b61b55031825d41a5d9c15903279a0cbef1a330ec4",
        "candidate_path": "generator/candidate.json",
        "case_id": "d9fda4e730f9971d",
        "evidence": {
          "compile_reopen": {
            "ifc_issues": [],
            "input_issues": [],
            "output_path": "dataset\\processed\\agent-demo\\phase6.5-live-two-storey-diagnostic-21\\runs\\d9fda4e730f9971d\\output.ifc",
            "success": true
          },
          "geometry": {
            "expectation_source": "design_brief_expected_facts",
            "issues": [],
            "metrics": {
              "case_id": "d9fda4e730f9971d",
              "floor_openings": {
                "opening-first-floor-slab-stair": {
                  "bbox": {
                    "x": [
                      6.0,
                      8.0
                    ],
                    "y": [
                      1.0,
                      6.0
                    ],
                    "z": [
                      3.0,
                      3.15
                    ]
                  },
                  "ifc_class": "IfcOpeningElement"
                }
              },
              "roof": {
                "roof-slab": {
                  "bbox": {
                    "x": [
                      0.0,
                      8.0
                    ],
                    "y": [
                      0.0,
                      6.0
                    ],
                    "z": [
                      6.15,
                      6.300000000000001
                    ]
                  },
                  "ifc_class": "IfcSlab"
                }
              },
              "slabs": {
                "first-floor-slab": {
                  "bbox": {
                    "x": [
                      0.0,
                      8.0
                    ],
                    "y": [
                      0.0,
                      6.0
                    ],
                    "z": [
                      3.0,
                      3.15
                    ]
                  },
                  "ifc_class": "IfcSlab"
                },
                "ground-floor-slab": {
                  "bbox": {
                    "x": [
                      0.0,
                      8.0
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
              "stairs": {
                "stair-1": {
                  "bbox": {
                    "x": [
                      6.5,
                      7.5
                    ],
                    "y": [
                      1.5,
                      5.0
                    ],
                    "z": [
                      0.15,
                      3.15
                    ]
                  },
                  "flight_ids": [
                    "stair-flight-1"
                  ],
                  "has_stepped_profile": true
                }
              },
              "wall_set_convention": "primary",
              "walls": {}
            },
            "success": true
          },
          "repair_history": {
            "case_id": "d9fda4e730f9971d",
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
            "source_generator_dir": "dataset/processed/agent-demo/phase6.5-live-two-storey-diagnostic-21/runs/d9fda4e730f9971d/generator",
            "source_generator_response_id": "079413f1-adec-4c43-bfeb-5957c0daa357",
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
            "candidate_entity_count": 31,
            "capability_profile_hash": "sha256:1a9b5d81e65c07e3b578782744596bd9a56eb1ecf9702c94dbde5fd91681bbb5",
            "capability_profile_id": "text2ifc/semantic-capabilities/ifc2x3-bim-json-2.0/1.0",
            "case_id": "d9fda4e730f9971d",
            "custom_property_policy": {
              "counts_as_semantic_support": false,
              "state": "preserved_text_only"
            },
            "facts": [
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/floor_slab_thickness_mm",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 150
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/outline/x_max",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 8000
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/outline/x_min",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 0
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/outline/y_max",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 6000
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/outline/y_min",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 0
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/roof_slab_thickness_mm",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 150
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/storey_count",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 2
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/building/wall_thickness_mm",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 200
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/floor_slabs",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": [
                  {
                    "id": "ground-floor-slab",
                    "opening": null,
                    "storey": "storey-1",
                    "thickness_mm": 150,
                    "top_elevation_mm": 0
                  },
                  {
                    "id": "first-floor-slab",
                    "opening": {
                      "bounds": {
                        "x_max": 8000,
                        "x_min": 6000,
                        "y_max": 6000,
                        "y_min": 1000
                      }
                    },
                    "storey": "storey-2",
                    "thickness_mm": 150,
                    "top_elevation_mm": 3150
                  }
                ]
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/roof_slab/bottom_elevation_mm",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 6150
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/roof_slab/id",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": "roof-slab"
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/roof_slab/thickness_mm",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": 150
              },
              {
                "coverage_state": "represented",
                "path": "/known_facts/stairs",
                "reason": "Fact is inside the current supported semantic profile.",
                "value": [
                  {
                    "bounds": {
                      "x_max": 7500,
                      "x_min": 6500,
                      "y_max": 5000,
                      "y_min": 1500
                    },
                    "end_elevation_mm": 3150,
                    "from_storey": "storey-1",
                    "id": "stair-1",
                    "run_direction": "+Y",
                    "start_elevation_mm": 150,
                    "to_storey": "storey-2",
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
                    "doors": [
                      {
                        "alignment": "horizontal_center",
                        "height_mm": 2100,
                        "host_wall": "storey-1-wall-south",
                        "id": "door-storey-1-south",
                        "sill_height_mm": 0,
                        "width_mm": 900
                      }
                    ],
                    "elevation_mm": 0,
                    "id": "storey-1",
                    "name": "首层",
                    "net_height_mm": 3000,
                    "spaces": [
                      {
                        "bounds": {
                          "x_max": 6000,
                          "x_min": 0,
                          "y_max": 6000,
                          "y_min": 0
                        },
                        "id": "space-office-1",
                        "name": "办公室"
                      },
                      {
                        "bounds": {
                          "x_max": 8000,
                          "x_min": 6000,
                          "y_max": 6000,
                          "y_min": 0
                        },
                        "id": "space-stair-hall",
                        "name": "楼梯间"
                      }
                    ],
                    "walls": [
                      {
                        "id": "storey-1-wall-south",
                        "side": "south",
                        "thickness_mm": 200
                      },
                      {
                        "id": "storey-1-wall-north",
                        "side": "north",
                        "thickness_mm": 200
                      },
                      {
                        "id": "storey-1-wall-east",
                        "side": "east",
                        "thickness_mm": 200
                      },
                      {
                        "id": "storey-1-wall-west",
                        "side": "west",
                        "thickness_mm": 200
                      }
                    ],
                    "windows": [
                      {
                        "alignment": "horizontal_center",
                        "height_mm": 1000,
                        "host_wall": "storey-1-wall-north",
                        "id": "window-storey-1-north",
                        "sill_height_mm": 900,
                        "width_mm": 1200
                      }
                    ]
                  },
                  {
                    "doors": [
                      {
                        "alignment": "horizontal_center",
                        "height_mm": 2100,
                        "host_wall": "storey-2-wall-south",
                        "id": "door-storey-2-south",
                        "sill_height_mm": 0,
                        "width_mm": 900
                      }
                    ],
                    "elevation_mm": 3150,
                    "id": "storey-2",
                    "name": "二层",
                    "net_height_mm": 3000,
                    "spaces": [
                      {
                        "bounds": {
                          "x_max": 6000,
                          "x_min": 0,
                          "y_max": 6000,
                          "y_min": 0
                        },
                        "id": "space-office-2",
                        "name": "办公室"
                      },
                      {
                        "bounds": {
                          "x_max": 8000,
                          "x_min": 6000,
                          "y_max": 1000,
                          "y_min": 0
                        },
                        "id": "space-stair-landing",
                        "name": "楼梯平台"
                      }
                    ],
                    "walls": [
                      {
                        "id": "storey-2-wall-south",
                        "side": "south",
                        "thickness_mm": 200
                      },
                      {
                        "id": "storey-2-wall-north",
                        "side": "north",
                        "thickness_mm": 200
                      },
                      {
                        "id": "storey-2-wall-east",
                        "side": "east",
                        "thickness_mm": 200
                      },
                      {
                        "id": "storey-2-wall-west",
                        "side": "west",
                        "thickness_mm": 200
                      }
                    ],
                    "windows": [
                      {
                        "alignment": "horizontal_center",
                        "height_mm": 1000,
                        "host_wall": "storey-2-wall-north",
                        "id": "window-storey-2-north",
                        "sill_height_mm": 900,
                        "width_mm": 1200
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
        "expected_facts_hash": "7f0c68e025ea61fb2fde45a1a0eb165c578a210b34ec8a2e39a5ce18238ed0ec",
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
                "candidate_id": "door-storey-1-south",
                "collection": "doors",
                "expected_id": "door-storey-1-south",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "door-storey-2-south",
                "collection": "doors",
                "expected_id": "door-storey-2-south",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "space-office-1",
                "collection": "spaces",
                "expected_id": "space-office-1",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "space-stair-hall",
                "collection": "spaces",
                "expected_id": "space-stair-hall",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "space-office-2",
                "collection": "spaces",
                "expected_id": "space-office-2",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "space-stair-landing",
                "collection": "spaces",
                "expected_id": "space-stair-landing",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "window-storey-1-north",
                "collection": "windows",
                "expected_id": "window-storey-1-north",
                "match_basis": "exact_brief_id"
              },
              {
                "candidate_id": "window-storey-2-north",
                "collection": "windows",
                "expected_id": "window-storey-2-north",
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
          "case_id": "d9fda4e730f9971d",
          "floor_openings": {
            "opening-first-floor-slab-stair": {
              "bbox": {
                "x": [
                  6.0,
                  8.0
                ],
                "y": [
                  1.0,
                  6.0
                ],
                "z": [
                  3.0,
                  3.15
                ]
              },
              "ifc_class": "IfcOpeningElement"
            }
          },
          "roof": {
            "roof-slab": {
              "bbox": {
                "x": [
                  0.0,
                  8.0
                ],
                "y": [
                  0.0,
                  6.0
                ],
                "z": [
                  6.15,
                  6.300000000000001
                ]
              },
              "ifc_class": "IfcSlab"
            }
          },
          "slabs": {
            "first-floor-slab": {
              "bbox": {
                "x": [
                  0.0,
                  8.0
                ],
                "y": [
                  0.0,
                  6.0
                ],
                "z": [
                  3.0,
                  3.15
                ]
              },
              "ifc_class": "IfcSlab"
            },
            "ground-floor-slab": {
              "bbox": {
                "x": [
                  0.0,
                  8.0
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
          "stairs": {
            "stair-1": {
              "bbox": {
                "x": [
                  6.5,
                  7.5
                ],
                "y": [
                  1.5,
                  5.0
                ],
                "z": [
                  0.15,
                  3.15
                ]
              },
              "flight_ids": [
                "stair-flight-1"
              ],
              "has_stepped_profile": true
            }
          },
          "wall_set_convention": "primary",
          "walls": {}
        },
        "success": true
      },
      "geometry_success": true,
      "ifc_path": "dataset\\processed\\agent-demo\\phase6.5-live-two-storey-diagnostic-21\\runs\\d9fda4e730f9971d\\output.ifc",
      "ifc_verification": {
        "ifc_issues": [],
        "input_issues": [],
        "output_path": "dataset\\processed\\agent-demo\\phase6.5-live-two-storey-diagnostic-21\\runs\\d9fda4e730f9971d\\output.ifc",
        "success": true
      },
      "output_dir": "dataset\\processed\\agent-demo\\phase6.5-live-two-storey-diagnostic-21\\runs\\d9fda4e730f9971d",
      "semantic_geometry_expectation": {
        "case_id": "d9fda4e730f9971d",
        "floor_openings": {
          "opening-first-floor-slab-stair": {
            "bbox": {
              "x": [
                6.0,
                8.0
              ],
              "y": [
                1.0,
                6.0
              ],
              "z": [
                3.0,
                3.15
              ]
            },
            "host_slab_id": "first-floor-slab",
            "source_fact_refs": [
              "/known_facts/floor_slabs/1/openings/0"
            ]
          }
        },
        "roof": {
          "roof-slab": {
            "bbox": {
              "x": [
                0.0,
                8.0
              ],
              "y": [
                0.0,
                6.0
              ],
              "z": [
                6.15,
                6.3
              ]
            },
            "datum": "roof_bottom",
            "source_fact_refs": [
              "/known_facts/roof_slab"
            ]
          }
        },
        "schema_version": "text2ifc/design-geometry-expectation/1.0",
        "slabs": {
          "first-floor-slab": {
            "bbox": {
              "x": [
                0.0,
                8.0
              ],
              "y": [
                0.0,
                6.0
              ],
              "z": [
                3.0,
                3.15
              ]
            },
            "datum": "slab_top",
            "must_touch_walls": [],
            "source_fact_refs": [
              "/known_facts/floor_slabs/1"
            ]
          },
          "ground-floor-slab": {
            "bbox": {
              "x": [
                0.0,
                8.0
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
        "stairs": {
          "stair-1": {
            "bbox": {
              "x": [
                6.5,
                7.5
              ],
              "y": [
                1.5,
                5.0
              ],
              "z": [
                0.15,
                3.15
              ]
            },
            "flight_ids": [
              "stair-flight-1"
            ],
            "require_steps": true,
            "source_fact_refs": [
              "/known_facts/stairs/0"
            ]
          }
        },
        "tolerance": 0.05,
        "units": "METRE",
        "unresolved": [],
        "walls": {}
      },
      "stage": "candidate-gates",
      "valid": true
    }
  },
  {
    "created_at": "2026-07-12T15:01:02+00:00",
    "event_index": 5,
    "event_type": "audit_completed",
    "payload": {
      "case_id": "d9fda4e730f9971d",
      "evidence_class": "live",
      "output_dir": "dataset/processed/agent-demo/phase6.5-live-two-storey-diagnostic-21/runs/d9fda4e730f9971d",
      "report_path": "dataset/processed/agent-demo/phase6.5-live-two-storey-diagnostic-21/runs/d9fda4e730f9971d/report.md",
      "response_id": "7aab01cf-ef1c-4753-b196-de07633c7d07",
      "route_decision": "accept",
      "route_owner_stage": "none",
      "stage": "audit-report",
      "status": "accepted",
      "valid": true
    }
  },
  {
    "created_at": "2026-07-12T15:01:04+00:00",
    "event_index": 6,
    "event_type": "final_acceptance_completed",
    "payload": {
      "case_id": "d9fda4e730f9971d",
      "compile_reopen_success": true,
      "geometry_success": true,
      "ifc_path": "dataset\\processed\\agent-demo\\phase6.5-live-two-storey-diagnostic-21\\runs\\d9fda4e730f9971d\\output.ifc",
      "output_dir": "dataset\\processed\\agent-demo\\phase6.5-live-two-storey-diagnostic-21\\runs\\d9fda4e730f9971d",
      "report_path": "dataset\\processed\\agent-demo\\phase6.5-live-two-storey-diagnostic-21\\runs\\d9fda4e730f9971d\\report.md",
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
    "created_at": "2026-07-12T14:57:57+00:00",
    "kind": "design_brief",
    "path": "runs/d9fda4e730f9971d/design-brief.json"
  },
  {
    "created_at": "2026-07-12T14:57:57+00:00",
    "kind": "session_export",
    "path": "runs/d9fda4e730f9971d/session-export.json"
  },
  {
    "created_at": "2026-07-12T14:57:57+00:00",
    "kind": "expected_facts",
    "path": "runs/d9fda4e730f9971d/expected-facts.json"
  },
  {
    "created_at": "2026-07-12T15:00:54+00:00",
    "kind": "candidate",
    "path": "runs/d9fda4e730f9971d/candidate.json"
  },
  {
    "created_at": "2026-07-12T15:00:54+00:00",
    "kind": "candidate_revision",
    "path": "runs/d9fda4e730f9971d/candidate-revision.json"
  },
  {
    "created_at": "2026-07-12T15:00:54+00:00",
    "kind": "component_preservation",
    "path": "runs/d9fda4e730f9971d/component-preservation.json"
  },
  {
    "created_at": "2026-07-12T15:00:54+00:00",
    "kind": "semantic_coverage",
    "path": "runs/d9fda4e730f9971d/semantic-coverage.json"
  },
  {
    "created_at": "2026-07-12T15:01:04+00:00",
    "kind": "issues",
    "path": "runs/d9fda4e730f9971d/issues.json"
  },
  {
    "created_at": "2026-07-12T15:01:04+00:00",
    "kind": "route_decision",
    "path": "runs/d9fda4e730f9971d/route-decision.json"
  },
  {
    "created_at": "2026-07-12T15:01:04+00:00",
    "kind": "feedback_rounds",
    "path": "runs/d9fda4e730f9971d/feedback-rounds.json"
  },
  {
    "created_at": "2026-07-12T15:01:04+00:00",
    "kind": "ifc",
    "path": "runs/d9fda4e730f9971d/output.ifc"
  },
  {
    "created_at": "2026-07-12T15:01:04+00:00",
    "kind": "report",
    "path": "runs/d9fda4e730f9971d/report.md"
  },
  {
    "created_at": "2026-07-12T15:01:04+00:00",
    "kind": "session_export",
    "path": "runs/d9fda4e730f9971d/session-export.json"
  }
]
```
