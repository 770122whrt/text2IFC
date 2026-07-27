import json
from pathlib import Path

from text2ifc_agent.providers import LiveProviderResult, ProviderOutput
from text2ifc_ifc_repair.operations import create_default_registry
from text2ifc_ifc_repair.provider_stage import generate_repair_changeset


class RecordingProvider:
    def __init__(self, response: dict) -> None:
        self.response = response
        self.calls = []

    def generate_candidate(self, **kwargs) -> ProviderOutput:
        self.calls.append(kwargs)
        return ProviderOutput(
            text=json.dumps(self.response, ensure_ascii=False),
            metadata={"provider": "recording-fake", "response_id": "fake-001"},
        )


class LiveRecordingProvider:
    def __init__(self, response: dict) -> None:
        self.response = response

    def generate_live(self, **kwargs) -> LiveProviderResult:
        output = ProviderOutput(
            text=json.dumps(self.response, ensure_ascii=False),
            metadata={
                "provider": "deepseek-openai-compatible",
                "evidence_class": "live",
                "response_id": "deepseek-ifc-repair-001",
                "model": "deepseek-v4-flash",
                "stop_reason": "stop",
                "usage": {"prompt_tokens": 100, "completion_tokens": 50},
            },
        )
        return LiveProviderResult(
            session_id=kwargs["session_id"],
            evidence_class="live",
            http_status=200,
            request={"model": "deepseek-v4-flash", "messages": ["public prompt"]},
            response={"id": "deepseek-ifc-repair-001", "choices": []},
            events=(
                {"sequence": 0, "event": "chat.completion", "data": {"id": "deepseek-ifc-repair-001"}},
            ),
            output=output,
        )


def test_provider_stage_receives_only_public_artifacts(tmp_path: Path) -> None:
    base_fingerprint = "sha256:" + "a" * 64
    request_hash = "sha256:" + "b" * 64
    repair_request = "在公开候选墙的指定位置新增窗户。\n"
    public_spec = {
        "schema_version": "text2ifc/ifc-repair-spec/0.1",
        "request_id": "request-public-001",
        "requested_operation_type": "add_window_with_opening_to_wall",
        "opening": {},
    }
    public_context = {
        "schema_version": "text2ifc/ifc-repair-context/0.1",
        "base_model_fingerprint": base_fingerprint,
        "candidate_targets": [
            {
                "target_id": "ifc:wall-public",
                "ifc_global_id": "wall-public",
            }
        ],
    }
    response = {
        "schema_version": "text2ifc/ifc-repair-changeset/0.1",
        "changeset_id": "changeset-provider-001",
        "base_model_fingerprint": base_fingerprint,
        "source_request_hash": request_hash,
        "scope": {"target_ids": ["wall-public"], "forbidden_ids": []},
        "evidence_refs": ["spec:/opening", "context:/candidate_targets/0"],
        "preconditions": ["target_exists"],
        "postconditions": ["window_fills_opening"],
        "operations": [
            {
                "operation_id": "operation-provider-window-001",
                "operation_type": "add_window_with_opening_to_wall",
                "target": {"wall_global_id": "wall-public"},
                "parameters": {
                    "position": {
                        "reference": "wall_local_start",
                        "center_offset_mm": 1000.0,
                    },
                    "opening": {
                        "width_mm": 915.0,
                        "height_mm": 1830.0,
                        "sill_height_mm": 305.0,
                    },
                    "window": {"fit_opening": True},
                },
                "evidence_refs": [
                    "spec:/opening",
                    "context:/candidate_targets/0",
                ],
            }
        ],
    }
    provider = RecordingProvider(response)

    result = generate_repair_changeset(
        provider=provider,
        case_id="public-001",
        repair_request=repair_request,
        source_request_hash=request_hash,
        public_spec=public_spec,
        public_context=public_context,
        registry=create_default_registry(),
        output_dir=tmp_path,
    )

    assert result["valid"] is True
    assert result["classification"] == "changeset"
    assert result["changeset"] == response
    assert result["prompt"]["template_id"] == "ifc-repair-changeset.v0.1"
    assert (tmp_path / "predicted-changeset.json").is_file()
    assert (tmp_path / "raw-response.txt").is_file()

    call = provider.calls[0]
    serialized_call = json.dumps(call, ensure_ascii=False, sort_keys=True)
    assert "mutation_manifest.private.json" not in serialized_call
    assert "secret-opening-global-id" not in serialized_call
    assert "secret-window-global-id" not in serialized_call
    assert call["state"] == {"case_id": "public-001", "stage": "ifc_repair_changeset"}
    renderer_input = json.loads(
        (tmp_path / "renderer-input.json").read_text(encoding="utf-8")
    )
    supported = next(
        item
        for item in renderer_input["SUPPORTED_OPERATIONS"]
        if item["operation_type"] == "add_window_with_opening_to_wall"
    )
    assert supported["target_schema"]["required"] == ["wall_global_id"]
    assert "opening_interval_available" in supported["precondition_names"]
    assert "window_fills_opening" in supported["postcondition_names"]


def test_provider_stage_preserves_openai_compatible_live_evidence(
    tmp_path: Path,
) -> None:
    base_fingerprint = "sha256:" + "a" * 64
    request_hash = "sha256:" + "b" * 64
    response = {
        "schema_version": "text2ifc/ifc-repair-changeset/0.1",
        "changeset_id": "changeset-live-001",
        "base_model_fingerprint": base_fingerprint,
        "source_request_hash": request_hash,
        "scope": {"target_ids": ["wall-public"], "forbidden_ids": []},
        "evidence_refs": ["spec:/opening"],
        "preconditions": ["target_exists"],
        "postconditions": ["window_fills_opening"],
        "operations": [
            {
                "operation_id": "operation-live-window-001",
                "operation_type": "add_window_with_opening_to_wall",
                "target": {"wall_global_id": "wall-public"},
                "parameters": {
                    "position": {
                        "reference": "wall_local_start",
                        "center_offset_mm": 1000.0,
                    },
                    "opening": {
                        "width_mm": 915.0,
                        "height_mm": 1830.0,
                        "sill_height_mm": 305.0,
                    },
                    "window": {"fit_opening": True},
                },
                "evidence_refs": ["spec:/opening"],
            }
        ],
    }
    result = generate_repair_changeset(
        provider=LiveRecordingProvider(response),
        case_id="live-public-001",
        repair_request="public repair request\n",
        source_request_hash=request_hash,
        public_spec={
            "requested_operation_type": "add_window_with_opening_to_wall",
            "opening": {},
        },
        public_context={
            "base_model_fingerprint": base_fingerprint,
            "candidate_targets": [{"ifc_global_id": "wall-public"}],
        },
        registry=create_default_registry(),
        output_dir=tmp_path,
    )

    assert result["valid"] is True
    assert (tmp_path / "live-request.json").is_file()
    assert (tmp_path / "live-response.json").is_file()
    assert (tmp_path / "live-events.jsonl").is_file()
    metadata = json.loads(
        (tmp_path / "provider-metadata.json").read_text(encoding="utf-8")
    )
    assert metadata["provider"] == "deepseek-openai-compatible"
    assert metadata["evidence_class"] == "live"


def test_provider_stage_rejects_invalid_target_contract_and_evidence_pointer(
    tmp_path: Path,
) -> None:
    base_fingerprint = "sha256:" + "a" * 64
    request_hash = "sha256:" + "b" * 64
    response = {
        "schema_version": "text2ifc/ifc-repair-changeset/0.1",
        "changeset_id": "changeset-invalid-binding-001",
        "base_model_fingerprint": base_fingerprint,
        "source_request_hash": request_hash,
        "scope": {"target_ids": ["wall-public"], "forbidden_ids": []},
        "evidence_refs": ["spec:/missing"],
        "preconditions": ["made_up_precondition"],
        "postconditions": ["window_fills_opening"],
        "operations": [
            {
                "operation_id": "operation-invalid-binding-001",
                "operation_type": "add_window_with_opening_to_wall",
                "target": {"wrong_global_id": "wall-public"},
                "parameters": {
                    "position": {
                        "reference": "wall_local_start",
                        "center_offset_mm": 1000.0,
                    },
                    "opening": {
                        "width_mm": 915.0,
                        "height_mm": 1830.0,
                        "sill_height_mm": 305.0,
                    },
                    "window": {"fit_opening": True},
                },
                "evidence_refs": ["spec:/missing"],
            }
        ],
    }

    result = generate_repair_changeset(
        provider=RecordingProvider(response),
        case_id="invalid-binding-001",
        repair_request="public repair request\n",
        source_request_hash=request_hash,
        public_spec={"opening": {}},
        public_context={
            "base_model_fingerprint": base_fingerprint,
            "candidate_targets": [{"ifc_global_id": "wall-public"}],
        },
        registry=create_default_registry(),
        output_dir=tmp_path,
    )

    assert result["valid"] is False
    assert {issue["code"] for issue in result["issues"]} == {
        "EVIDENCE_POINTER_NOT_FOUND",
        "OPERATION_TARGET_SCHEMA_ERROR",
        "UNDECLARED_PRECONDITION",
    }
