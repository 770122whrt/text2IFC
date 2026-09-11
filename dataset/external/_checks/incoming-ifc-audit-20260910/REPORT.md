# 新增 IFC ZIP 检查结果（2026-09-10）

本报告仅登记检查结果，不是 canonical 准入清单。原 IFC/ZIP 均未修改。

## 汇总

```json
{
  "ifc_occurrences": 80,
  "exact_unique_files": 80,
  "canonical_exact_matches": 0,
  "independent_building_count": null,
  "data_identical_groups": [],
  "high_guid_overlap_pairs": [
    {
      "a": "RVT-006",
      "b": "RVT-007",
      "shared": 117,
      "a_elements": 157,
      "b_elements": 117,
      "smaller_overlap": 1.0,
      "classification": "variant_signal_not_independent_identity_proof"
    },
    {
      "a": "RVT-008",
      "b": "RVT-010",
      "shared": 443,
      "a_elements": 443,
      "b_elements": 445,
      "smaller_overlap": 1.0,
      "classification": "variant_signal_not_independent_identity_proof"
    },
    {
      "a": "RVT-014",
      "b": "RVT-015",
      "shared": 61,
      "a_elements": 104,
      "b_elements": 61,
      "smaller_overlap": 1.0,
      "classification": "variant_signal_not_independent_identity_proof"
    },
    {
      "a": "RVT-014",
      "b": "RVT-016",
      "shared": 30,
      "a_elements": 104,
      "b_elements": 35,
      "smaller_overlap": 0.8571,
      "classification": "variant_signal_not_independent_identity_proof"
    },
    {
      "a": "RVT-015",
      "b": "RVT-016",
      "shared": 30,
      "a_elements": 61,
      "b_elements": 35,
      "smaller_overlap": 0.8571,
      "classification": "variant_signal_not_independent_identity_proof"
    },
    {
      "a": "RVT-016",
      "b": "RVT-017",
      "shared": 35,
      "a_elements": 35,
      "b_elements": 121,
      "smaller_overlap": 1.0,
      "classification": "variant_signal_not_independent_identity_proof"
    },
    {
      "a": "RVT-004",
      "b": "RVT-005",
      "shared": 2815,
      "a_elements": 2818,
      "b_elements": 2815,
      "smaller_overlap": 1.0,
      "classification": "variant_signal_not_independent_identity_proof"
    },
    {
      "a": "RVT-004",
      "b": "RVT-011",
      "shared": 2630,
      "a_elements": 2818,
      "b_elements": 3271,
      "smaller_overlap": 0.9333,
      "classification": "variant_signal_not_independent_identity_proof"
    },
    {
      "a": "RVT-004",
      "b": "RVT-012",
      "shared": 2630,
      "a_elements": 2818,
      "b_elements": 3271,
      "smaller_overlap": 0.9333,
      "classification": "variant_signal_not_independent_identity_proof"
    },
    {
      "a": "RVT-005",
      "b": "RVT-011",
      "shared": 2630,
      "a_elements": 2815,
      "b_elements": 3271,
      "smaller_overlap": 0.9343,
      "classification": "variant_signal_not_independent_identity_proof"
    },
    {
      "a": "RVT-005",
      "b": "RVT-012",
      "shared": 2630,
      "a_elements": 2815,
      "b_elements": 3271,
      "smaller_overlap": 0.9343,
      "classification": "variant_signal_not_independent_identity_proof"
    },
    {
      "a": "RVT-011",
      "b": "RVT-012",
      "shared": 3271,
      "a_elements": 3271,
      "b_elements": 3271,
      "smaller_overlap": 1.0,
      "classification": "variant_signal_not_independent_identity_proof"
    }
  ],
  "groups": {
    "converted_29": {
      "count": 29,
      "reparse_ok": 29,
      "size_body": {
        "small_with_body": 20,
        "oversize_with_body": 4,
        "no_body": 5
      },
      "no_grid_and_axis": 29,
      "schema_checked": 25,
      "schema_errors_found": 25,
      "schema_error_total": 2006,
      "files_duplicate_globalid": 29,
      "files_missing_unit_name": 29,
      "files_missing_header_originating_system": 29,
      "geometry_files_checked": 20,
      "geometry_elements_checked": 436,
      "geometry_failures": 0,
      "roundtrip_passed": 25,
      "basic_candidates": 0,
      "roof_entity_files": 11,
      "roof_slab_files": 7,
      "unvoided_opening_files": 0,
      "door_window_without_fill_files": 7
    },
    "circular_existing": {
      "count": 1,
      "reparse_ok": 1,
      "size_body": {
        "small_with_body": 1
      },
      "no_grid_and_axis": 1,
      "schema_checked": 1,
      "schema_errors_found": 0,
      "schema_error_total": 0,
      "files_duplicate_globalid": 0,
      "files_missing_unit_name": 0,
      "files_missing_header_originating_system": 0,
      "geometry_files_checked": 1,
      "geometry_elements_checked": 24,
      "geometry_failures": 0,
      "roundtrip_passed": 1,
      "basic_candidates": 1,
      "roof_entity_files": 0,
      "roof_slab_files": 0,
      "unvoided_opening_files": 0,
      "door_window_without_fill_files": 0
    },
    "resbim_50": {
      "count": 50,
      "reparse_ok": 50,
      "size_body": {
        "small_with_body": 50
      },
      "no_grid_and_axis": 50,
      "schema_checked": 50,
      "schema_errors_found": 50,
      "schema_error_total": 2501,
      "files_duplicate_globalid": 50,
      "files_missing_unit_name": 50,
      "files_missing_header_originating_system": 50,
      "geometry_files_checked": 50,
      "geometry_elements_checked": 1200,
      "geometry_failures": 0,
      "roundtrip_passed": 50,
      "basic_candidates": 0,
      "roof_entity_files": 0,
      "roof_slab_files": 0,
      "unvoided_opening_files": 0,
      "door_window_without_fill_files": 0
    }
  },
  "reported_missing_dependency_assets": [
    "RVT-025",
    "RVT-026",
    "RVT-028"
  ],
  "reported_unresolved_link_assets": [
    "RVT-008",
    "RVT-022"
  ]
}
```

## 逐文件结果

| 编号 | IFC 文件 | MiB | 主体构件 | 格式错误数 | 几何抽检数/失败数 | 屋顶/屋面板 | 状态 |
|---|---|---:|---:|---:|---:|---:|---|
| RVT-001 | RVT-001__LittleHouse__IFC2X3_NoGrid.ifc | 0.4963 | 20 | 12 | 20/0 | 1/0 | small_with_body |
| RVT-018 | RVT-018__FindColumns-Basic__IFC2X3_NoGrid.ifc | 0.2974 | 24 | 18 | 24/0 | 0/0 | small_with_body |
| RVT-028 | RVT-028__ABG_210902_FormworkStarter__IFC2X3_NoGrid.ifc | 5.9282 | 556 | 383 | 24/0 | 0/0 | small_with_body |
| RVT-029 | RVT-029__ARCH-Documenting-BaseFile__IFC2X3_NoGrid.ifc | 3.0446 | 226 | 7 | 24/0 | 0/0 | small_with_body |
| RVT-019 | RVT-019__DynamoSample_2025__IFC2X3_NoGrid.ifc | 1.9694 | 247 | 102 | 24/0 | 0/0 | small_with_body |
| RVT-021 | RVT-021__unwrapElement__IFC2X3_NoGrid.ifc | 0.0678 | 12 | 15 | 12/0 | 2/2 | small_with_body |
| RVT-024 | RVT-024__linkFile__IFC2X3_NoGrid.ifc | 0.0242 | 2 | 5 | 2/0 | 0/0 | small_with_body |
| RVT-025 | RVT-025__01-08-2026_PROJECT__IFC2X3_NoGrid.ifc | 0.2470 | 57 | 15 | 24/0 | 0/0 | small_with_body |
| RVT-026 | RVT-026__PROJECT-1__IFC2X3_NoGrid.ifc | 0.9613 | 132 | 68 | 24/0 | 0/0 | small_with_body |
| RVT-027 | RVT-027__STEEL_TRUSSES___DETAILING__IFC2X3_NoGrid.ifc | 4.4354 | 423 | 302 | 24/0 | 1/0 | small_with_body |
| RVT-003 | RVT-003__Planning Site solution__IFC2X3_NoGrid.ifc | 0.1298 | 18 | 27 | 18/0 | 0/0 | small_with_body |
| RVT-006 | RVT-006__Create Ceilings Solution__IFC2X3_NoGrid.ifc | 7.5360 | 155 | 147 | 24/0 | 3/1 | small_with_body |
| RVT-007 | RVT-007__Create Ceilings__IFC2X3_NoGrid.ifc | 6.0678 | 115 | 74 | 24/0 | 3/1 | small_with_body |
| RVT-008 | RVT-008__Studio Block Finished__IFC2X3_NoGrid.ifc | 5.0611 | 438 | 84 | 24/0 | 1/0 | small_with_body |
| RVT-009 | RVT-009__Studio Block Structure__IFC2X3_NoGrid.ifc | 0.9071 | 66 | 69 | 24/0 | 0/0 | small_with_body |
| RVT-010 | RVT-010__Studio Block__IFC2X3_NoGrid.ifc | 5.0926 | 440 | 88 | 24/0 | 1/0 | small_with_body |
| RVT-014 | RVT-014__house1__IFC2X3_NoGrid.ifc | 5.2155 | 104 | 188 | 24/0 | 0/0 | small_with_body |
| RVT-015 | RVT-015__house1_nowalls__IFC2X3_NoGrid.ifc | 4.5781 | 61 | 150 | 24/0 | 0/0 | small_with_body |
| RVT-016 | RVT-016__house2_nowalls__IFC2X3_NoGrid.ifc | 4.5186 | 35 | 78 | 24/0 | 0/0 | small_with_body |
| RVT-017 | RVT-017__house2__IFC2X3_NoGrid.ifc | 5.5392 | 121 | 156 | 24/0 | 0/0 | small_with_body |
| RVT-004 | RVT-004__Embed Walls solution__IFC2X3_NoGrid.ifc | 37.9450 | 2788 | 未完成（超限） | 未完成 | 6/3 | oversize_with_body |
| RVT-005 | RVT-005__Embed Walls__IFC2X3_NoGrid.ifc | 37.8857 | 2785 | 未完成（超限） | 未完成 | 6/3 | oversize_with_body |
| RVT-011 | RVT-011__Create View Template solution__IFC2X3_NoGrid.ifc | 67.9031 | 3241 | 未完成（超限） | 未完成 | 6/3 | oversize_with_body |
| RVT-012 | RVT-012__Create View Template__IFC2X3_NoGrid.ifc | 67.9031 | 3241 | 未完成（超限） | 未完成 | 6/3 | oversize_with_body |
| RVT-002 | RVT-002__ModelCreation__IFC2X3_NoGrid.ifc | 0.0081 | 0 | 4 | 0/0 | 0/0 | no_body |
| RVT-020 | RVT-020__Empty-Metric__IFC2X3_NoGrid.ifc | 0.0057 | 0 | 3 | 0/0 | 0/0 | no_body |
| RVT-022 | RVT-022__hostFile__IFC2X3_NoGrid.ifc | 0.0057 | 0 | 3 | 0/0 | 0/0 | no_body |
| RVT-023 | RVT-023__MAGN_8367__IFC2X3_NoGrid.ifc | 0.0067 | 0 | 4 | 0/0 | 0/0 | no_body |
| RVT-013 | RVT-013__CA-L15-01-Use PDF and Images__IFC2X3_NoGrid.ifc | 0.0085 | 0 | 4 | 0/0 | 0/0 | no_body |
| Circular-existing | Circular_example-ifc.ifc | 0.1348 | 84 | 0 | 24/0 | 0/0 | small_with_body |
| ResBIM-23 | 23.ifc | 0.6506 | 43 | 47 | 24/0 | 0/0 | small_with_body |
| ResBIM-5 | 5.ifc | 0.5364 | 36 | 48 | 24/0 | 0/0 | small_with_body |
| ResBIM-44 | 44.ifc | 0.6429 | 44 | 52 | 24/0 | 0/0 | small_with_body |
| ResBIM-28 | 28.ifc | 0.5986 | 37 | 46 | 24/0 | 0/0 | small_with_body |
| ResBIM-26 | 26.ifc | 0.6194 | 41 | 50 | 24/0 | 0/0 | small_with_body |
| ResBIM-11 | 11.ifc | 0.6696 | 46 | 48 | 24/0 | 0/0 | small_with_body |
| ResBIM-15 | 15.ifc | 0.5997 | 39 | 49 | 24/0 | 0/0 | small_with_body |
| ResBIM-16 | 16.ifc | 0.6422 | 50 | 50 | 24/0 | 0/0 | small_with_body |
| ResBIM-17 | 17.ifc | 0.6044 | 42 | 51 | 24/0 | 0/0 | small_with_body |
| ResBIM-30 | 30.ifc | 0.8289 | 61 | 58 | 24/0 | 0/0 | small_with_body |
| ResBIM-24 | 24.ifc | 0.7070 | 44 | 48 | 24/0 | 0/0 | small_with_body |
| ResBIM-7 | 7.ifc | 0.6455 | 47 | 55 | 24/0 | 0/0 | small_with_body |
| ResBIM-21 | 21.ifc | 0.6156 | 41 | 53 | 24/0 | 0/0 | small_with_body |
| ResBIM-22 | 22.ifc | 0.5907 | 48 | 44 | 24/0 | 0/0 | small_with_body |
| ResBIM-49 | 49.ifc | 0.6277 | 45 | 57 | 24/0 | 0/0 | small_with_body |
| ResBIM-8 | 8.ifc | 0.5961 | 38 | 47 | 24/0 | 0/0 | small_with_body |
| ResBIM-14 | 14.ifc | 0.7560 | 54 | 59 | 24/0 | 0/0 | small_with_body |
| ResBIM-46 | 46.ifc | 0.6133 | 38 | 46 | 24/0 | 0/0 | small_with_body |
| ResBIM-0 | 0.ifc | 0.5372 | 31 | 39 | 24/0 | 0/0 | small_with_body |
| ResBIM-18 | 18.ifc | 0.6974 | 50 | 50 | 24/0 | 0/0 | small_with_body |
| ResBIM-31 | 31.ifc | 0.5685 | 42 | 53 | 24/0 | 0/0 | small_with_body |
| ResBIM-20 | 20.ifc | 0.6080 | 42 | 51 | 24/0 | 0/0 | small_with_body |
| ResBIM-42 | 42.ifc | 0.6281 | 49 | 49 | 24/0 | 0/0 | small_with_body |
| ResBIM-29 | 29.ifc | 0.5506 | 35 | 43 | 24/0 | 0/0 | small_with_body |
| ResBIM-35 | 35.ifc | 0.7608 | 67 | 63 | 24/0 | 0/0 | small_with_body |
| ResBIM-3 | 3.ifc | 0.6913 | 52 | 50 | 24/0 | 0/0 | small_with_body |
| ResBIM-12 | 12.ifc | 0.8518 | 67 | 55 | 24/0 | 0/0 | small_with_body |
| ResBIM-41 | 41.ifc | 0.7515 | 52 | 54 | 24/0 | 0/0 | small_with_body |
| ResBIM-48 | 48.ifc | 0.6575 | 45 | 57 | 24/0 | 0/0 | small_with_body |
| ResBIM-1 | 1.ifc | 0.6222 | 42 | 50 | 24/0 | 0/0 | small_with_body |
| ResBIM-39 | 39.ifc | 0.6311 | 40 | 49 | 24/0 | 0/0 | small_with_body |
| ResBIM-47 | 47.ifc | 0.7361 | 47 | 46 | 24/0 | 0/0 | small_with_body |
| ResBIM-45 | 45.ifc | 0.6499 | 45 | 50 | 24/0 | 0/0 | small_with_body |
| ResBIM-9 | 9.ifc | 0.3531 | 26 | 31 | 24/0 | 0/0 | small_with_body |
| ResBIM-13 | 13.ifc | 0.6621 | 50 | 58 | 24/0 | 0/0 | small_with_body |
| ResBIM-27 | 27.ifc | 0.6816 | 49 | 50 | 24/0 | 0/0 | small_with_body |
| ResBIM-34 | 34.ifc | 0.5475 | 35 | 43 | 24/0 | 0/0 | small_with_body |
| ResBIM-32 | 32.ifc | 0.5612 | 43 | 55 | 24/0 | 0/0 | small_with_body |
| ResBIM-19 | 19.ifc | 0.5782 | 40 | 50 | 24/0 | 0/0 | small_with_body |
| ResBIM-4 | 4.ifc | 0.5299 | 33 | 41 | 24/0 | 0/0 | small_with_body |
| ResBIM-38 | 38.ifc | 0.5170 | 35 | 47 | 24/0 | 0/0 | small_with_body |
| ResBIM-37 | 37.ifc | 0.6217 | 39 | 48 | 24/0 | 0/0 | small_with_body |
| ResBIM-36 | 36.ifc | 0.6182 | 39 | 48 | 24/0 | 0/0 | small_with_body |
| ResBIM-6 | 6.ifc | 0.5034 | 41 | 50 | 24/0 | 0/0 | small_with_body |
| ResBIM-43 | 43.ifc | 0.6027 | 49 | 57 | 24/0 | 0/0 | small_with_body |
| ResBIM-33 | 33.ifc | 0.4906 | 28 | 40 | 24/0 | 0/0 | small_with_body |
| ResBIM-2 | 2.ifc | 0.5645 | 40 | 52 | 24/0 | 0/0 | small_with_body |
| ResBIM-40 | 40.ifc | 0.5696 | 42 | 53 | 24/0 | 0/0 | small_with_body |
| ResBIM-10 | 10.ifc | 0.6058 | 42 | 56 | 24/0 | 0/0 | small_with_body |
| ResBIM-25 | 25.ifc | 0.6099 | 41 | 55 | 24/0 | 0/0 | small_with_body |

## 检查边界

全体80个IFC从ZIP内重新用IfcOpenShell解析，未解压落盘。正式属性/基数/逆关系/唯一性校验对76个未超限文件完成；4个超限文件只计基础解析及直接必填字段/GlobalId检查。几何是按构件类别分层的有限抽样，不是全模型几何验收。EXPRESS WHERE规则、碰撞、设计规范、RVT→IFC完整性、逐模型视觉审查和许可终审未完成。

重复GlobalId、缺失必填单位名等已由第二次独立解析直接确认。许可未审查通过前，training_eligible保持false；同一建筑变体不得计作独立建筑。

历史member-000至004为检查器兼容故障证据，已由member-v2结果替代。member-v2-020保留一次90秒超时；整批10至19曾遇180秒命令超时，已保留完成结果并补齐。
