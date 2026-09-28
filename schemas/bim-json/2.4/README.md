# BIM JSON 2.4

2.4 retains the 2.3 JSON structure and adds semantic support for placed,
end-clipped polygon wall hosts. Existing versions keep their original behavior.
The basic filling template remains `text2ifc/basic-filling/1.0`; its defaults and
the meaning of its input depth are unchanged.

Supported layered walls are positive local-Z extrusions. After composing
`Representation.position`, the convex section must have two parallel local-X
faces defining a constant thickness along product-local Y. End bevels and
collinear vertices are supported. Tilted, tapered-long-face and concave layered
sections remain unsupported. Use `IfcWall` for polygon walls; the existing
`IfcWallStandardCase` rectangle restriction remains in place.

Material layer sums are compared to the transformed section thickness, with
0.1 mm tolerance for rounded coordinates. Collinear deviations up to 0.1 mm may
be simplified for semantic inspection only; compilation preserves the authored
profile and placements. Material errors and opening-placement errors are
reported separately.

Basic fillings still require rectangular vertical openings. Opening and filling
frames must align with the wall's product axes, allowing a 180-degree planar
reversal. Representation positions participate in all placement comparisons.
The nominal filling width, height, depth and placement must fit inside the
opening. The opening cutter and the filling's resolved envelope must each have
positive-volume overlap with the uncut wall; pure tangency is insufficient.

Neither cutter nor filling must be wholly contained in the wall footprint.
IFC Boolean openings can cross a clipped wall end, and source window geometry
can do the same. Requiring full host containment would alter such source models.
The compiler retains the original cutter, filling, wall profile and materials;
it does not shift them or replace a polygon wall with a rectangle.

Focused regression: `tests/compiler/test_polygon_wall_hosts_v24.py` includes
independent placed and reversed profiles, invalid sections, material mismatch,
disjoint/tangent cutters, filling containment, and reopened IFC Boolean cut
volume. These tests establish deterministic behavior, not Provider capability.
