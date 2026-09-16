"""Production imports stay independent of the private benchmark entry point."""

import os
from pathlib import Path
import subprocess
import sys


def test_public_orchestrator_does_not_load_private_benchmark() -> None:
    root = Path(__file__).resolve().parents[2]
    environment = dict(os.environ, PYTHONPATH=os.pathsep.join(sys.path))
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import text2ifc_ifc_repair.orchestrator; "
            "assert 'text2ifc_ifc_repair.benchmark_evaluation' not in sys.modules",
        ],
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr


def test_legacy_evaluation_imports_share_the_production_implementation() -> None:
    from text2ifc_ifc_repair import benchmark_evaluation as legacy
    from text2ifc_ifc_repair import production_evaluation as production

    assert legacy.ProductionEvaluationInputs is production.ProductionEvaluationInputs
    assert legacy.evaluate_production is production.evaluate_production
    assert legacy.BENCHMARK_POLICY_VERSION == production.EVALUATION_POLICY_VERSION
    assert not hasattr(production, "BenchmarkEvaluationInputs")
    assert not hasattr(production, "evaluate_benchmark")
