"""IFC2Text baseline: deterministic building facts, description and roundtrip comparison."""

from .facts import extract_building_facts
from .description import render_design_description
from .compare import CompareTolerances, compare_ifc_buildings
from .roundtrip import prepare_roundtrip_baseline, finalize_roundtrip_baseline
from .writing import assemble_sectioned_description, build_fact_index
from .llm_pipeline import IFC2TextLLMError, run_ifc_llm_description, run_llm_description

__all__ = [
    "CompareTolerances",
    "IFC2TextLLMError",
    "assemble_sectioned_description",
    "build_fact_index",
    "compare_ifc_buildings",
    "extract_building_facts",
    "finalize_roundtrip_baseline",
    "prepare_roundtrip_baseline",
    "render_design_description",
    "run_ifc_llm_description",
    "run_llm_description",
]
