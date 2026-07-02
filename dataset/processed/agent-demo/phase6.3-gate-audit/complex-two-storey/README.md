# Phase 6.3 Complex Two-storey Fixture

This directory freezes the complex residential request that exposed the next
text2IFC reliability gap after Phase 6.2-fix.

The fixture is manual review truth for Wave 0 only. It is not production logic
and must not become a hard-coded two-storey rule. Later Phase 6.3 waves must
generalize these expectations through `expected-facts.json`, dynamic gates,
Gate-Audit evidence, and route decisions.

Key no-false-accept rule:

- An IFC can compile and reopen but still be unacceptable when requested doors,
  windows, opening/fill relationships, containment, slabs, roof, stair, or
  storey ownership are missing.

Primary follow-up risks:

- Missing second-storey door facts.
- Windows present as entities but not embedded through opening/fill relations.
- Elements assigned to the wrong storey.
- Geometry gates applying a simple-room convention to multi-storey layouts.
