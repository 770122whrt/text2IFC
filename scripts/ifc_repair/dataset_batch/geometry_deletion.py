"""Bounded geometry ownership guard; no global library changes or IFC writes.

Usage: with guard_geometry(model, product): existing_remove_product(model, product)
The existing deleter retains responsibility for relationships/properties/types.
"""
from __future__ import annotations

from contextlib import contextmanager

import ifcopenshell.util.element


def _find(model, identifier):
    try:
        return model.by_id(identifier)
    except RuntimeError:
        return None


@contextmanager
def guard_geometry(model, product):
    """Preserve external geometry graphs while removing target-owned geometry.

    All ownership and descendant protection are frozen before any mutation.
    Direct layer links and unreferenced StyledItems are metadata companions,
    not geometry owners. Their shared definitions and non-target members stay.
    Other external inverses, including a StyledItem used by another graph,
    protect the referenced node and its complete forward descendant closure.

    The caller must delete this IfcProduct in an unbatched model. This guard
    detaches only its two forward fields; it does not alter surviving products.
    Cleanup rejects retained exclusive graph nodes instead of leaving a full
    deleted target as orphan geometry that could expose the private answer.
    """
    if not product.is_a("IfcProduct"):
        raise ValueError("GEOMETRY_GUARD_REQUIRES_IFCPRODUCT")
    if model.to_delete is not None:
        raise ValueError("GEOMETRY_GUARD_REQUIRES_UNBATCHED_MODEL")
    product_id = product.id()
    pds = product.Representation
    placement = product.ObjectPlacement
    representation_ids = [r.id() for r in pds.Representations or ()] if pds else []
    pds_id = pds.id() if pds else None
    placement_id = placement.id() if placement else None
    roots = [root for root in (pds, placement) if root is not None]
    graph = {node.id(): node for root in roots for node in model.traverse(root)}
    graph_ids = set(graph)
    protected_seeds, styled_ids, layer_ids = set(), set(), set()

    for identifier, node in graph.items():
        if node.is_a("IfcGeometricRepresentationContext"):
            protected_seeds.add(identifier)
        for inverse in model.get_inverse(node):
            inverse_id = inverse.id()
            if inverse_id == product_id or inverse_id in graph_ids:
                continue
            if inverse.is_a("IfcPresentationLayerAssignment"):
                layer_ids.add(inverse_id)
                # AssignedItems is metadata membership, safely trimmed below.
                continue
            if inverse.is_a("IfcStyledItem"):
                styled_ids.add(inverse_id)
                # A StyledItem can itself be consumed by a material/other graph.
                # Such an external use owns the Item; standalone style metadata
                # can be shallowly removed without deleting style definitions.
                if any(ref.id() not in graph_ids for ref in model.get_inverse(inverse)):
                    protected_seeds.add(identifier)
                continue
            protected_seeds.add(identifier)

    protected_ids = {child.id() for seed in protected_seeds for child in model.traverse(graph[seed])}
    exclusive_ids = graph_ids - protected_ids
    # The source fields are now detached, so remove_product never enters its
    # unsafe unassign/remove_representation or placement deep-delete branches.
    product.Representation = None
    product.ObjectPlacement = None
    try:
        yield {"protected_node_count": len(protected_ids), "exclusive_node_count": len(exclusive_ids)}
    except BaseException:
        remaining_product = _find(model, product_id)
        if remaining_product is not None:
            remaining_product.Representation = _find(model, pds_id) if pds_id else None
            remaining_product.ObjectPlacement = _find(model, placement_id) if placement_id else None
        raise

    remaining_product = _find(model, product_id)
    if remaining_product is not None:
        remaining_product.Representation = _find(model, pds_id) if pds_id else None
        remaining_product.ObjectPlacement = _find(model, placement_id) if placement_id else None
        raise ValueError("GEOMETRY_GUARD_TARGET_NOT_DELETED")

    for identifier in styled_ids:
        styled = _find(model, identifier)
        if styled is not None and styled.Item is not None and styled.Item.id() in exclusive_ids:
            # This item has no external consumer: remove metadata only, keeping
            # SurfaceStyle/PresentationStyleAssignment resources unchanged.
            model.remove(styled)
    for identifier in layer_ids:
        layer = _find(model, identifier)
        if layer is None:
            continue
        before = tuple(layer.AssignedItems)
        after = tuple(item for item in before if item.id() not in exclusive_ids)
        if after == before:
            continue
        if after:
            layer.AssignedItems = after
        else:
            model.remove(layer)

    for identifier in [pds_id, *representation_ids, placement_id]:
        root = _find(model, identifier) if identifier else None
        if root is None or identifier in protected_ids:
            continue
        protected = {node for i in protected_ids if (node := _find(model, i)) is not None}
        ifcopenshell.util.element.remove_deep2(model, root, do_not_delete=protected)

    remaining = sorted(identifier for identifier in exclusive_ids if _find(model, identifier) is not None)
    if remaining:
        raise ValueError("EXCLUSIVE_GEOMETRY_RETAINED:" + ",".join(map(str, remaining[:20])))
