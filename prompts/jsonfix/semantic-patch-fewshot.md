# Semantic Patch v1 Few-shot Examples

These examples define output shape, not hidden defaults. Replace ids, values,
and provenance only with facts supported by the current request and base
document.

## Example 1: Add a missing wall

```json
{
  "patch_version": "bim-json-patch/1.0",
  "target_schema_version": "bim-json/2.0",
  "target_ifc_schema": "IFC2X3",
  "target_document_id": "simple-room-base",
  "layers": [
    {
      "id": "user-add-west-wall",
      "kind": "user",
      "provenance": {
        "source": "user-repair-request",
        "request_id": "repair-001"
      },
      "operations": [
        {
          "op": "add_entity",
          "target": {
            "collection": "entities",
            "id": "wall-west"
          },
          "value": {
            "id": "wall-west",
            "ifc_class": "IfcWallStandardCase",
            "attributes": {
              "Name": "West wall",
              "ObjectPlacement": {
                "relative_to": "storey-1",
                "origin": [0, 2000, 0],
                "axis": [0, 0, 1],
                "ref_direction": [0, 1, 0]
              },
              "Representation": {
                "kind": "extruded_profile",
                "profile": {
                  "kind": "rectangle",
                  "x": 4000,
                  "y": 200
                },
                "depth": 2800,
                "direction": [0, 0, 1]
              }
            },
            "property_sets": {},
            "provenance": {
              "source": "user-patch",
              "layer_id": "user-add-west-wall"
            }
          }
        }
      ]
    }
  ]
}
```

## Example 2: Set a wall property

```json
{
  "patch_version": "bim-json-patch/1.0",
  "target_schema_version": "bim-json/2.0",
  "target_ifc_schema": "IFC2X3",
  "target_document_id": "simple-room-base",
  "layers": [
    {
      "id": "agent-fire-rating",
      "kind": "agent",
      "provenance": {
        "source": "agent-interpretation",
        "prompt_version": "semantic-patch-v1"
      },
      "operations": [
        {
          "op": "set_property",
          "target": {
            "collection": "entities",
            "id": "wall-north",
            "property_set": "Pset_WallCommon",
            "property": "FireRating"
          },
          "value": "R30"
        }
      ]
    }
  ]
}
```

## Example 3: Record unsupported source geometry

```json
{
  "patch_version": "bim-json-patch/1.0",
  "target_schema_version": "bim-json/2.0",
  "target_ifc_schema": "IFC2X3",
  "target_document_id": "source-extract-base",
  "layers": [
    {
      "id": "validator-geometry-loss",
      "kind": "validator",
      "provenance": {
        "source": "ifc-extraction-validation"
      },
      "operations": [
        {
          "op": "mark_unsupported_loss",
          "target": {
            "collection": "entities",
            "id": "source-wall-17",
            "path": "attributes.Representation"
          },
          "value": {
            "source_ifc_class": "IfcFacetedBrep",
            "reason": "The current Formal profile cannot preserve this geometry exactly.",
            "substitution": "none"
          }
        }
      ]
    }
  ]
}
```
