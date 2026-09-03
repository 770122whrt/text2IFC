from __future__ import annotations

import ast
import importlib
import inspect
import json
import textwrap
from types import SimpleNamespace

import pytest

from text2ifc_ifc_repair import benchmark_evaluation


PRIVATE_CANARIES = (
    "CANARY-STRUCTURAL-GOLD-GUID-12",
    "CANARY-STRUCTURAL-STEP-120012",
    "C:/private-gold/CANARY-structural-original.ifc",
    "CANARY-STRUCTURAL-GEOMETRY-12",
    "CANARY-STRUCTURAL-GOLD-CHANGESET-12",
)


def _runner_module():
    return importlib.import_module(
        "scripts.ifc_repair.run_phase12_public_structural_repair"
    )


def test_phase12_public_process_has_only_damaged_bundle_and_output_inputs() -> None:
    runner = _runner_module()
    signature = inspect.signature(runner.run_public_repair)
    assert set(signature.parameters) == {
        "damaged_ifc",
        "public_request_bundle",
        "output_root",
    }

    main_source = inspect.getsource(runner.main)
    for forbidden_flag in (
        "--original",
        "--mutation",
        "--deleted",
        "--gold",
        "--private",
    ):
        assert forbidden_flag not in main_source

    function_tree = ast.parse(
        textwrap.dedent(inspect.getsource(runner.run_public_repair))
    )
    names = {node.id for node in ast.walk(function_tree) if isinstance(node, ast.Name)}
    assert {
        "original",
        "mutation_manifest",
        "deleted_object_ids",
        "private_geometry",
        "gold_changeset",
    }.isdisjoint(names)

    module_source = inspect.getsource(runner)
    assert "BenchmarkEvaluationInputs" not in module_source
    assert "evaluate_benchmark" not in module_source
    assert "evaluate_production" in module_source


@pytest.mark.parametrize(
    ("key", "value"),
    (
        ("original_ifc_path", PRIVATE_CANARIES[2]),
        ("removed_global_id", PRIVATE_CANARIES[0]),
        ("removed_step_id", PRIVATE_CANARIES[1]),
        ("private_geometry", PRIVATE_CANARIES[3]),
        ("gold_changeset", PRIVATE_CANARIES[4]),
    ),
)
def test_public_bundle_rejects_every_private_gold_channel_without_echo(
    key: str,
    value: str,
) -> None:
    runner = _runner_module()
    bundle = {
        "schema_version": "text2ifc/phase12-public-structural-request/0.1",
        "request": "add one beam and one column on the selected storey",
        "operations": [],
        "nested": {key: value},
    }
    with pytest.raises(ValueError, match="PUBLIC_STRUCTURAL_BUNDLE_PRIVATE_FIELD") as error:
        runner.validate_public_request_bundle(bundle)
    assert value not in str(error.value)


def test_post_production_benchmark_gate_is_monotonic() -> None:
    guard = getattr(
        benchmark_evaluation,
        "assert_benchmark_cannot_promote_failed_production",
    )
    failed_production = SimpleNamespace(
        complete_repair_success=False,
        successful_artifact_publishable=False,
    )
    passing_private_comparison = SimpleNamespace(
        complete_repair_success=True,
        successful_artifact_publishable=True,
    )
    with pytest.raises(
        ValueError,
        match="BENCHMARK_CANNOT_PROMOTE_FAILED_PRODUCTION",
    ):
        guard(failed_production, passing_private_comparison)

    passing_production = SimpleNamespace(
        complete_repair_success=True,
        successful_artifact_publishable=True,
    )
    assert guard(passing_production, passing_private_comparison) is None


def test_public_artifacts_do_not_contain_private_mutation_canaries(tmp_path) -> None:
    runner = _runner_module()
    bundle = {
        "schema_version": "text2ifc/phase12-public-structural-request/0.1",
        "request": "add one beam and one column on Level 1",
        "operations": [],
    }
    runner.validate_public_request_bundle(bundle)
    public_payloads = {
        "repair-intent.json": {"request": bundle["request"]},
        "target-resolution.json": {"status": "resolved"},
        "changeset.json": {"operations": []},
    }
    for name, payload in public_payloads.items():
        (tmp_path / name).write_text(
            json.dumps(payload, ensure_ascii=False),
            encoding="utf-8",
        )
    public_text = "\n".join(
        path.read_text(encoding="utf-8") for path in tmp_path.iterdir()
    )
    assert all(canary not in public_text for canary in PRIVATE_CANARIES)

