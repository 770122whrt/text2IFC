# Phase 6.4 Feedback Routing Matrix

- case_count: `8`
- accepted_count: `2`
- blocked_count: `5`
- draft_count: `1`
- false_accept_count: `0`

## Cases

- `simple-accepted-ifc`: final_status=`accepted`, route=`accepted`, report=[report.md](simple-accepted-ifc/report.md)
- `two-room-smoke`: final_status=`accepted`, route=`accepted`, report=[report.md](two-room-smoke/report.md)
- `controlled-two-storey-route`: final_status=`blocked`, route=`regenerate_json`, report=[report.md](controlled-two-storey-route/report.md)
- `clarification-two-storey-route`: final_status=`draft`, route=`ask_user`, report=[report.md](clarification-two-storey-route/report.md)
- `ambiguous-two-storey-route`: final_status=`blocked`, route=`revise_design_brief`, report=[report.md](ambiguous-two-storey-route/report.md)
- `provider-truncation`: final_status=`blocked`, route=`provider_retry`, report=[report.md](provider-truncation/report.md)
- `unsupported-compiler-feature`: final_status=`blocked`, route=`blocked_as_unsupported`, report=[report.md](unsupported-compiler-feature/report.md)
- `three-storey-dynamic-route`: final_status=`blocked`, route=`regenerate_json`, report=[report.md](three-storey-dynamic-route/report.md)
