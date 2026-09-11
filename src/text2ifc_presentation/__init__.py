from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Iterable

from ifcopenshell.api.style.add_style import add_style
from ifcopenshell.api.style.add_surface_style import add_surface_style
from ifcopenshell.api.style.assign_item_style import assign_item_style
from ifcopenshell.api.style.assign_material_style import assign_material_style


@dataclass(frozen=True)
class AppearanceSpec:
    name: str
    red: float
    green: float
    blue: float
    transparency: float = 0.0

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("APPEARANCE_NAME_REQUIRED")
        for value in (self.red, self.green, self.blue, self.transparency):
            if not 0.0 <= float(value) <= 1.0:
                raise ValueError("APPEARANCE_COMPONENT_OUT_OF_RANGE")

    def signature(self) -> dict[str, float | str]:
        return {
            "style_name": self.name,
            "red": round(float(self.red), 6),
            "green": round(float(self.green), 6),
            "blue": round(float(self.blue), 6),
            "transparency": round(float(self.transparency), 6),
        }


@dataclass(frozen=True)
class _GenerationProfile:
    name: str
    default_palette: tuple[AppearanceSpec, ...]
    palettes_by_class: dict[str, tuple[AppearanceSpec, ...]]


_DEMO = _GenerationProfile(
    name="demo-colorful-v0.1",
    default_palette=(
        AppearanceSpec("demo-sage", 0.45, 0.64, 0.53),
        AppearanceSpec("demo-terracotta", 0.72, 0.38, 0.28),
        AppearanceSpec("demo-sand", 0.78, 0.67, 0.47),
    ),
    palettes_by_class={
        "IfcWall": (
            AppearanceSpec("demo-wall-sand", 0.78, 0.67, 0.47),
            AppearanceSpec("demo-wall-sage", 0.45, 0.64, 0.53),
            AppearanceSpec("demo-wall-terracotta", 0.72, 0.38, 0.28),
        ),
        "IfcWallStandardCase": (
            AppearanceSpec("demo-wall-sand", 0.78, 0.67, 0.47),
            AppearanceSpec("demo-wall-sage", 0.45, 0.64, 0.53),
            AppearanceSpec("demo-wall-terracotta", 0.72, 0.38, 0.28),
        ),
        "IfcSlab": (AppearanceSpec("demo-slab-stone", 0.63, 0.61, 0.56),),
        "IfcBeam": (
            AppearanceSpec("demo-beam-blue", 0.25, 0.43, 0.68),
            AppearanceSpec("demo-beam-teal", 0.24, 0.55, 0.56),
        ),
        "IfcColumn": (
            AppearanceSpec("demo-column-charcoal", 0.30, 0.34, 0.39),
            AppearanceSpec("demo-column-indigo", 0.34, 0.38, 0.61),
        ),
        "IfcDoor": (
            AppearanceSpec("demo-door-walnut", 0.48, 0.27, 0.15),
            AppearanceSpec("demo-door-ochre", 0.67, 0.45, 0.19),
        ),
        "IfcWindow": (
            AppearanceSpec("demo-glass-blue", 0.48, 0.72, 0.86, transparency=0.45),
            AppearanceSpec("demo-glass-cyan", 0.42, 0.78, 0.80, transparency=0.45),
        ),
        "IfcRoof": (AppearanceSpec("demo-roof-graphite", 0.20, 0.23, 0.27),),
        "IfcStair": (AppearanceSpec("demo-stair-bronze", 0.57, 0.43, 0.28),),
        "IfcStairFlight": (AppearanceSpec("demo-flight-bronze", 0.62, 0.47, 0.31),),
    },
)

_WARM = _GenerationProfile(
    name="warm-residential-v0.1",
    default_palette=(
        AppearanceSpec("warm-cream", 0.82, 0.76, 0.64),
        AppearanceSpec("warm-clay", 0.66, 0.42, 0.29),
        AppearanceSpec("warm-olive", 0.48, 0.52, 0.37),
    ),
    palettes_by_class={
        "IfcWall": (
            AppearanceSpec("warm-wall-cream", 0.84, 0.78, 0.68),
            AppearanceSpec("warm-wall-limestone", 0.76, 0.68, 0.56),
        ),
        "IfcWallStandardCase": (
            AppearanceSpec("warm-wall-cream", 0.84, 0.78, 0.68),
            AppearanceSpec("warm-wall-limestone", 0.76, 0.68, 0.56),
        ),
        "IfcDoor": (AppearanceSpec("warm-door-oak", 0.54, 0.34, 0.20),),
        "IfcWindow": (AppearanceSpec("warm-glass", 0.57, 0.74, 0.80, transparency=0.4),),
        "IfcRoof": (AppearanceSpec("warm-roof", 0.28, 0.22, 0.20),),
        "IfcBeam": (AppearanceSpec("warm-beam", 0.42, 0.36, 0.31),),
        "IfcColumn": (AppearanceSpec("warm-column", 0.49, 0.45, 0.39),),
        "IfcSlab": (AppearanceSpec("warm-slab", 0.68, 0.64, 0.58),),
    },
)

_COOL = _GenerationProfile(
    name="modern-cool-v0.1",
    default_palette=(
        AppearanceSpec("cool-slate", 0.36, 0.43, 0.50),
        AppearanceSpec("cool-blue", 0.36, 0.56, 0.72),
        AppearanceSpec("cool-mist", 0.66, 0.72, 0.76),
    ),
    palettes_by_class={
        "IfcWall": (
            AppearanceSpec("cool-wall-mist", 0.72, 0.76, 0.77),
            AppearanceSpec("cool-wall-bluegrey", 0.56, 0.64, 0.68),
        ),
        "IfcWallStandardCase": (
            AppearanceSpec("cool-wall-mist", 0.72, 0.76, 0.77),
            AppearanceSpec("cool-wall-bluegrey", 0.56, 0.64, 0.68),
        ),
        "IfcDoor": (AppearanceSpec("cool-door-charcoal", 0.24, 0.28, 0.32),),
        "IfcWindow": (AppearanceSpec("cool-glass", 0.46, 0.69, 0.84, transparency=0.5),),
        "IfcRoof": (AppearanceSpec("cool-roof", 0.17, 0.21, 0.25),),
        "IfcBeam": (AppearanceSpec("cool-beam-steel", 0.31, 0.42, 0.52),),
        "IfcColumn": (AppearanceSpec("cool-column-steel", 0.34, 0.39, 0.44),),
        "IfcSlab": (AppearanceSpec("cool-slab-concrete", 0.62, 0.65, 0.66),),
    },
)

_GENERATION_PROFILES = {profile.name: profile for profile in (_DEMO, _WARM, _COOL)}
_GENERATION_STYLE_EXCLUDED_CLASSES = frozenset({"IfcOpeningElement"})


def generation_profile_names() -> tuple[str, ...]:
    return tuple(sorted(_GENERATION_PROFILES))


def select_generation_profile(requested: str, *, seed: str) -> str:
    if requested != "auto":
        if requested not in _GENERATION_PROFILES:
            raise ValueError("GENERATION_APPEARANCE_PROFILE_UNKNOWN")
        return requested
    names = generation_profile_names()
    digest = hashlib.sha256(str(seed).encode("utf-8")).digest()
    return names[int.from_bytes(digest[:8], "big") % len(names)]


def _stable_index(value: str, size: int) -> int:
    digest = hashlib.sha256(value.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % size


def _style_from_spec(model: Any, spec: AppearanceSpec) -> Any:
    style = add_style(model, name=spec.name, ifc_class="IfcSurfaceStyle")
    colour = {
        "Name": None,
        "Red": float(spec.red),
        "Green": float(spec.green),
        "Blue": float(spec.blue),
    }
    if float(spec.transparency) > 0.0:
        add_surface_style(
            model,
            style=style,
            ifc_class="IfcSurfaceStyleRendering",
            attributes={
                "SurfaceColour": colour,
                "Transparency": float(spec.transparency),
                "ReflectanceMethod": "NOTDEFINED",
            },
        )
    else:
        add_surface_style(
            model,
            style=style,
            ifc_class="IfcSurfaceStyleShading",
            attributes={"SurfaceColour": colour},
        )
    return style


def assign_material_appearance(
    model: Any,
    *,
    material: Any,
    context: Any,
    spec: AppearanceSpec,
) -> Any:
    if not material.is_a("IfcMaterial"):
        raise ValueError("APPEARANCE_MATERIAL_REQUIRED")
    style = _style_from_spec(model, spec)
    assign_material_style(model, material=material, style=style, context=context)
    return style


def assign_item_appearance(model: Any, *, item: Any, spec: AppearanceSpec) -> Any:
    style = _style_from_spec(model, spec)
    assign_item_style(model, item=item, style=style)
    return style


def assign_existing_style_to_item(model: Any, *, item: Any, style: Any) -> None:
    if not style.is_a("IfcSurfaceStyle"):
        raise ValueError("APPEARANCE_SURFACE_STYLE_REQUIRED")
    assign_item_style(model, item=item, style=style)


def _unwrap_surface_styles(values: Iterable[Any]) -> tuple[Any, ...]:
    styles: list[Any] = []
    seen: set[int] = set()
    for value in values:
        if value is None:
            continue
        if value.is_a("IfcSurfaceStyle"):
            if value.id() not in seen:
                styles.append(value)
                seen.add(value.id())
            continue
        if value.is_a("IfcPresentationStyleAssignment"):
            for style in _unwrap_surface_styles(value.Styles):
                if style.id() not in seen:
                    styles.append(style)
                    seen.add(style.id())
    return tuple(styles)


def item_surface_styles(item: Any) -> tuple[Any, ...]:
    styled_items = tuple(getattr(item, "StyledByItem", ()) or ())
    values = [style for styled in styled_items for style in styled.Styles]
    return _unwrap_surface_styles(values)


def material_surface_styles(material: Any) -> tuple[Any, ...]:
    values: list[Any] = []
    for definition in tuple(getattr(material, "HasRepresentation", ()) or ()):
        for representation in definition.Representations:
            for item in representation.Items:
                if item.is_a("IfcStyledItem"):
                    values.extend(item.Styles)
    return _unwrap_surface_styles(values)


def _style_signature(style: Any) -> dict[str, float | str] | None:
    if not style.is_a("IfcSurfaceStyle"):
        return None
    rendering = next(
        (item for item in style.Styles if item.is_a("IfcSurfaceStyleRendering")),
        None,
    )
    shading = rendering or next(
        (item for item in style.Styles if item.is_a("IfcSurfaceStyleShading")),
        None,
    )
    if shading is None:
        return None
    colour = shading.SurfaceColour
    transparency = (
        float(rendering.Transparency or 0.0) if rendering is not None else 0.0
    )
    return {
        "style_name": str(style.Name or ""),
        "red": round(float(colour.Red), 6),
        "green": round(float(colour.Green), 6),
        "blue": round(float(colour.Blue), 6),
        "transparency": round(transparency, 6),
    }


def _signatures(styles: Iterable[Any]) -> tuple[dict[str, float | str], ...]:
    values = [signature for style in styles if (signature := _style_signature(style))]
    values.sort(
        key=lambda item: (
            str(item["style_name"]),
            float(item["red"]),
            float(item["green"]),
            float(item["blue"]),
            float(item["transparency"]),
        )
    )
    return tuple(values)


def item_appearance_signatures(item: Any) -> tuple[dict[str, float | str], ...]:
    return _signatures(item_surface_styles(item))


def material_appearance_signatures(material: Any) -> tuple[dict[str, float | str], ...]:
    return _signatures(material_surface_styles(material))


def appearance_fingerprint(entity: Any) -> str:
    if entity.is_a("IfcMaterial"):
        signatures = material_appearance_signatures(entity)
    elif entity.is_a("IfcRepresentationItem"):
        signatures = item_appearance_signatures(entity)
    else:
        raise ValueError("APPEARANCE_FINGERPRINT_ENTITY_UNSUPPORTED")
    payload = json.dumps(signatures, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _materials_from_resource(resource: Any) -> tuple[Any, ...]:
    if resource is None:
        return ()
    if resource.is_a("IfcMaterial"):
        return (resource,)
    if resource.is_a("IfcMaterialLayerSetUsage"):
        return _materials_from_resource(resource.ForLayerSet)
    if resource.is_a("IfcMaterialLayerSet"):
        return tuple(
            layer.Material
            for layer in tuple(resource.MaterialLayers or ())
            if layer.Material is not None
        )
    if resource.is_a("IfcMaterialList"):
        return tuple(resource.Materials or ())
    return ()


def type_surface_styles(type_object: Any) -> tuple[Any, ...]:
    if not type_object.is_a("IfcTypeObject"):
        raise ValueError("APPEARANCE_TYPE_REQUIRED")

    # A style attached directly to the Type representation is the more specific
    # presentation authority and therefore wins over a Type-associated material style.
    direct: list[Any] = []
    for representation_map in tuple(getattr(type_object, "RepresentationMaps", ()) or ()):
        for item in representation_map.MappedRepresentation.Items:
            direct.extend(item_surface_styles(item))
    if direct:
        unique = {style.id(): style for style in direct}
        return tuple(unique[key] for key in sorted(unique))

    material_styles: list[Any] = []
    for relation in tuple(getattr(type_object, "HasAssociations", ()) or ()):
        if not relation.is_a("IfcRelAssociatesMaterial"):
            continue
        for material in _materials_from_resource(relation.RelatingMaterial):
            material_styles.extend(material_surface_styles(material))
    unique = {style.id(): style for style in material_styles}
    return tuple(unique[key] for key in sorted(unique))


def _occurrence_surface_styles(occurrence: Any) -> tuple[Any, ...]:
    direct: list[Any] = []
    representation = getattr(occurrence, "Representation", None)
    if representation is not None:
        for shape in representation.Representations:
            if str(shape.RepresentationIdentifier or "") != "Body":
                continue
            for item in shape.Items:
                direct.extend(item_surface_styles(item))
    if direct:
        unique = {style.id(): style for style in direct}
        return tuple(unique[key] for key in sorted(unique))

    material_styles: list[Any] = []
    for relation in tuple(getattr(occurrence, "HasAssociations", ()) or ()):
        if not relation.is_a("IfcRelAssociatesMaterial"):
            continue
        for material in _materials_from_resource(relation.RelatingMaterial):
            material_styles.extend(material_surface_styles(material))
    unique = {style.id(): style for style in material_styles}
    return tuple(unique[key] for key in sorted(unique))


def _same_type_reference_surface_styles(
    type_object: Any,
    *,
    occurrence: Any,
) -> tuple[Any, ...]:
    styles: list[Any] = []
    for relation in tuple(getattr(type_object, "ObjectTypeOf", ()) or ()):
        if not relation.is_a("IfcRelDefinesByType"):
            continue
        for candidate in relation.RelatedObjects:
            if candidate == occurrence:
                continue
            styles.extend(_occurrence_surface_styles(candidate))
    unique = {style.id(): style for style in styles}
    return tuple(unique[key] for key in sorted(unique))


def _unambiguous_surface_style(styles: tuple[Any, ...], *, ambiguity_code: str) -> Any | None:
    by_signature: dict[str, Any] = {}
    for style in styles:
        signature = _style_signature(style)
        if signature is None:
            continue
        key = json.dumps(signature, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        by_signature.setdefault(key, style)
    if not by_signature:
        return None
    if len(by_signature) > 1:
        raise ValueError(ambiguity_code)
    return next(iter(by_signature.values()))


def _preserved_mapped_type_appearance(type_object: Any, occurrence: Any) -> dict[str, Any] | None:
    """Keep per-item Type styles when the occurrence already maps that exact Body."""
    if type_object is None:
        return None
    maps = tuple(getattr(type_object, "RepresentationMaps", ()) or ())
    representation = getattr(occurrence, "Representation", None)
    if not maps or representation is None:
        return None
    items = tuple(item for shape in representation.Representations
                  if str(shape.RepresentationIdentifier or "") == "Body"
                  for item in shape.Items)
    if not items or any(not item.is_a("IfcMappedItem")
                        or item.MappingSource not in maps
                        or tuple(getattr(item, "StyledByItem", ()) or ()) for item in items):
        return None
    styles = tuple(style for item in items
                   for source_item in item.MappingSource.MappedRepresentation.Items
                   for style in item_surface_styles(source_item))
    if not styles:
        return None
    return {"applied": False, "preserved": True, "source": "type_representation",
            "style_count": len({style.id() for style in styles}), "item_count": len(items)}


def apply_repair_appearance_on_occurrence(
    model: Any,
    *,
    type_object: Any,
    occurrence: Any,
    explicit_appearance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Apply Repair appearance authority: Type > explicit user > reference > none."""

    preserved = _preserved_mapped_type_appearance(type_object, occurrence)
    if preserved is not None:
        return preserved

    type_styles = () if type_object is None else type_surface_styles(type_object)
    style = _unambiguous_surface_style(
        type_styles,
        ambiguity_code="APPEARANCE_TYPE_STYLE_AMBIGUOUS",
    )
    source = "type"
    if style is None and explicit_appearance is not None:
        if str(explicit_appearance.get("intent_kind")) != "surface_color_rgb":
            raise ValueError("APPEARANCE_INTENT_KIND_UNSUPPORTED")
        spec = AppearanceSpec(
            name=(
                "repair-user-rgb-"
                f"{float(explicit_appearance['red']):.6f}-"
                f"{float(explicit_appearance['green']):.6f}-"
                f"{float(explicit_appearance['blue']):.6f}"
            ),
            red=float(explicit_appearance["red"]),
            green=float(explicit_appearance["green"]),
            blue=float(explicit_appearance["blue"]),
        )
        style = _style_from_spec(model, spec)
        source = "explicit_user"
    if style is None and type_object is not None:
        reference_styles = _same_type_reference_surface_styles(
            type_object,
            occurrence=occurrence,
        )
        source = "same_type_reference_occurrence"
        style = _unambiguous_surface_style(
            reference_styles,
            ambiguity_code="APPEARANCE_REFERENCE_STYLE_AMBIGUOUS",
        )
        style_count = len(reference_styles)
    elif style is None:
        style_count = 0
    else:
        style_count = len(type_styles) if source == "type" else 1
    if style is None:
        return {"applied": False, "source": source, "style_count": style_count}

    representation = getattr(occurrence, "Representation", None)
    if representation is None:
        return {"applied": False, "source": source, "style_count": style_count}
    item_count = 0
    for shape in representation.Representations:
        if str(shape.RepresentationIdentifier or "") != "Body":
            continue
        for item in shape.Items:
            assign_existing_style_to_item(model, item=item, style=style)
            item_count += 1
    return {
        "applied": item_count > 0,
        "source": source,
        "style_count": style_count,
        "item_count": item_count,
        "style": _style_signature(style),
    }


def preserve_type_appearance_on_occurrence(
    model: Any,
    *,
    type_object: Any,
    occurrence: Any,
) -> dict[str, Any]:
    styles = type_surface_styles(type_object)
    source = "type"
    style = _unambiguous_surface_style(
        styles,
        ambiguity_code="APPEARANCE_TYPE_STYLE_AMBIGUOUS",
    )
    if style is None:
        styles = _same_type_reference_surface_styles(
            type_object,
            occurrence=occurrence,
        )
        source = "same_type_reference_occurrence"
        style = _unambiguous_surface_style(
            styles,
            ambiguity_code="APPEARANCE_REFERENCE_STYLE_AMBIGUOUS",
        )
    if style is None:
        return {"applied": False, "source": source, "style_count": len(styles)}

    representation = getattr(occurrence, "Representation", None)
    if representation is None:
        return {"applied": False, "source": source, "style_count": len(styles)}
    item_count = 0
    for shape in representation.Representations:
        if str(shape.RepresentationIdentifier or "") != "Body":
            continue
        for item in shape.Items:
            assign_existing_style_to_item(model, item=item, style=style)
            item_count += 1
    return {
        "applied": item_count > 0,
        "source": source,
        "style_count": len(styles),
        "item_count": item_count,
        "style": _style_signature(style),
    }


def apply_generation_profile(
    model: Any,
    *,
    requested_profile: str,
    seed: str,
) -> dict[str, Any]:
    selected = select_generation_profile(requested_profile, seed=seed)
    profile = _GENERATION_PROFILES[selected]
    style_cache: dict[AppearanceSpec, Any] = {}
    styled_products = 0
    styled_items = 0
    for product in model.by_type("IfcProduct"):
        if product.is_a() in _GENERATION_STYLE_EXCLUDED_CLASSES:
            continue
        representation = getattr(product, "Representation", None)
        if representation is None:
            continue
        palette = profile.palettes_by_class.get(product.is_a(), profile.default_palette)
        if not palette:
            continue
        key = f"{selected}|{seed}|{product.is_a()}|{getattr(product, 'GlobalId', '')}"
        spec = palette[_stable_index(key, len(palette))]
        style = style_cache.get(spec)
        if style is None:
            style = _style_from_spec(model, spec)
            style_cache[spec] = style
        item_count = 0
        for shape in representation.Representations:
            if str(shape.RepresentationIdentifier or "") != "Body":
                continue
            for item in shape.Items:
                assign_item_style(model, item=item, style=style)
                item_count += 1
        if item_count:
            styled_products += 1
            styled_items += item_count
    return {
        "profile": selected,
        "seed": str(seed),
        "styled_products": styled_products,
        "styled_items": styled_items,
        "style_count": len(style_cache),
    }


__all__ = [
    "AppearanceSpec",
    "appearance_fingerprint",
    "apply_generation_profile",
    "apply_repair_appearance_on_occurrence",
    "assign_existing_style_to_item",
    "assign_item_appearance",
    "assign_material_appearance",
    "generation_profile_names",
    "item_appearance_signatures",
    "item_surface_styles",
    "material_appearance_signatures",
    "material_surface_styles",
    "preserve_type_appearance_on_occurrence",
    "select_generation_profile",
    "type_surface_styles",
]
