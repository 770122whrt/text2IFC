"""Narrow bridge from an IFC2Text description into the existing text2IFC public path.

This module intentionally knows nothing about a source IFC or source facts.  Its
input contract is text only, which makes the roundtrip truth boundary explicit.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any


def reconstruct_description_with_public_text2ifc(
    description: str,
    *,
    store: Any,
    invoke_design_brief: Callable[..., Any],
    provider_factory: Callable[[], Any],
    clarification_answers: Iterable[str] = (),
    trace_level: str | None = "debug",
    generation_strategy: str = "legacy_full",
    budget_limits: Any = None,
) -> dict[str, Any]:
    """Feed only the design description through the supported text2IFC session APIs.

    The caller remains responsible for Provider admission and budget authorization.
    This function does not create a fallback result when clarification is incomplete
    or a Provider call fails.
    """
    from text2ifc_agent.interactive_cli_flow import (
        run_design_brief_clarification_loop,
        run_ready_session_to_ifc,
    )

    session = store.create_session(original_input=description)
    brief = run_design_brief_clarification_loop(
        store=store,
        session=session.session_id,
        invoke_design_brief=invoke_design_brief,
        user_answers=clarification_answers,
    )
    if brief.status != "ready":
        return {
            "status": brief.status,
            "session_id": brief.session_id,
            "session_hash": brief.session_hash,
            "ifc_path": None,
            "public_path": "design_brief_clarification_loop",
        }
    result = run_ready_session_to_ifc(
        store=store,
        session=brief.session_id,
        provider_factory=provider_factory,
        trace_level=trace_level,
        generation_strategy=generation_strategy,
        budget_limits=budget_limits,
    )
    return {
        "status": result.status,
        "session_id": result.session_id,
        "session_hash": result.session_hash,
        "ifc_path": None if result.ifc_path is None else str(result.ifc_path),
        "report_path": None if result.report_path is None else str(result.report_path),
        "generator_status": result.generator_status,
        "audit_status": result.audit_status,
        "public_path": "run_ready_session_to_ifc",
    }
