from __future__ import annotations

from text2ifc_ifc_repair.operations.window import window_operation_definition
from text2ifc_ifc_repair.resolution_flow import generated_type_authority
from text2ifc_ifc_repair.run_models import hash_json


def test_generated_type_authority_is_hash_bound_to_compiler_template() -> None:
    authority = generated_type_authority(
        window_operation_definition(),
        operation_id="window-1",
        request_hash="sha256:" + "a" * 64,
        model_fingerprint="sha256:" + "b" * 64,
    )
    expected = hash_json(
        {
            "template_id": authority["template_id"],
            "template_version": authority["template_version"],
            "ifc_class": authority["ifc_class"],
            "formal_attributes": authority["formal_attributes"],
            "template": authority["template"],
        }
    )
    assert authority["template_digest"] == expected
    assert authority["template_id"] == (
        "add_window_with_opening_to_wall.generated-type"
    )
    assert authority["formal_attributes"]["operation_type"] == "NOTDEFINED"
