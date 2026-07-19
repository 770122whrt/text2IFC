import hashlib
import json
from pathlib import Path

from text2ifc_agent.providers import ProviderOutput
from text2ifc_ifc_repair.workflow import (
    run_live_window_repair_case,
    run_offline_window_repair_case,
)


ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    ROOT
    / "dataset"
    / "external"
    / "bim-whale-ifc-samples"
    / "LargeBuilding"
    / "IFC"
    / "LargeBuilding.ifc"
)


def test_fake_provider_e2e_writes_a_complete_publicly_bound_evidence_bundle(
    tmp_path: Path,
) -> None:
    output = tmp_path / "offline-window-001"

    result = run_offline_window_repair_case(
        source_path=SOURCE,
        output_dir=output,
        case_id="large-building-window-repair-001",
        wall_global_id="1F6umJ5H50aeL3A1As_wTm",
        opening_global_id="2cXV28XOjE6f6irhW0CO4t",
        window_global_id="2cXV28XOjE6f6irgi0CO4t",
    )

    assert result["schema_version"] == "text2ifc/ifc-repair-evaluation-public/0.2"
    assert result["complete_repair_success"] is False
    assert result["successful_artifact_publishable"] is False
    assert result["diagnostic_artifact_retained"] is True
    expected = {
        "mutation/damaged.ifc",
        "mutation/mutation_manifest.private.json",
        "repair_request.txt",
        "public-repair-spec.json",
        "public-context.json",
        "provider/raw-response.txt",
        "provider/predicted-changeset.json",
        "audit-report.json",
        "application-report.json",
        "diagnostic/repaired-candidate.ifc",
        "evaluation_report.json",
        "evaluation-public.json",
        "private/evaluation-private.json",
        "report.md",
        "artifact-manifest.json",
    }
    assert expected.issubset(
        {
            path.relative_to(output).as_posix()
            for path in output.rglob("*")
            if path.is_file()
        }
    )
    assert not (output / "repaired.ifc").exists()
    assert not (output / "successful-repaired.ifc").exists()

    renderer_input = (output / "provider" / "renderer-input.json").read_text(
        encoding="utf-8"
    )
    assert "mutation_manifest.private.json" not in renderer_input
    assert "2cXV28XOjE6f6irhW0CO4t" not in renderer_input
    assert "2cXV28XOjE6f6irgi0CO4t" not in renderer_input
    metadata = json.loads(
        (output / "provider" / "provider-metadata.json").read_text(encoding="utf-8")
    )
    assert metadata["provider"] == "deterministic-public-rule"
    assert metadata["evidence_class"] == "offline_fake"

    manifest = json.loads(
        (output / "artifact-manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["private_input_exclusion"]["provider_received_private_artifacts"] is False
    for artifact in manifest["artifacts"]:
        path = output / artifact["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == artifact["sha256"]
    report = (output / "report.md").read_text(encoding="utf-8")
    assert "离线确定性验证" in report
    assert "真实 Provider UAT" in report
    assert "未冒充" in report


class _InvalidLiveProvider:
    def generate_candidate(self, **kwargs) -> ProviderOutput:
        del kwargs
        return ProviderOutput(
            text="{}",
            metadata={"provider": "live-fixture", "evidence_class": "live"},
        )


def test_live_uat_failure_is_preserved_as_failure_evidence(tmp_path: Path) -> None:
    output = tmp_path / "live-invalid"

    result = run_live_window_repair_case(
        provider=_InvalidLiveProvider(),
        source_path=SOURCE,
        output_dir=output,
        case_id="large-building-window-live-invalid",
        wall_global_id="1F6umJ5H50aeL3A1As_wTm",
        opening_global_id="2cXV28XOjE6f6irhW0CO4t",
        window_global_id="2cXV28XOjE6f6irgi0CO4t",
    )

    assert result["complete_repair_success"] is False
    assert result["evidence_class"] == "live_provider_uat"
    assert result["failure_stage"] == "provider"
    assert (output / "provider" / "raw-response.txt").is_file()
    assert (output / "provider" / "diagnostics.json").is_file()
    assert (output / "evaluation_report.json").is_file()
    assert (output / "artifact-manifest.json").is_file()
    assert not (output / "repaired.ifc").exists()
    report = (output / "report.md").read_text(encoding="utf-8")
    assert "完整修复结果：**失败**" in report
