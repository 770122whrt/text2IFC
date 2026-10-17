"""Additional pairs keep old damages/ledgers and count unused modes only once."""
from __future__ import annotations

from contextlib import nullcontext
import copy
from types import SimpleNamespace

import pytest

from scripts.ifc_repair import dataset_extension as x


def pair(mode="world"):
    return {"case_id": "formal-021-s1-d004-" + mode,
            "source_id": "formal-021", "damage_id": "formal-021-s1-d004",
            "locator_mode": mode,
            "case_path": "sources/formal-021/cases/supplement-r1-damage-004",
            "request_relative_path": "public/request-" + mode + ".txt",
            "model_sha256": "a" * 64, "request_sha256": "b" * 64,
            "primary_target_count": 1, "task_kind": "property"}


def test_old_odd_quota_can_add_the_existing_unselected_host_mode():
    original = [pair()]
    templates = {original[0]["damage_id"]: {
        "world": {"applicable": True, "sha256": "b" * 64},
        "host_wall": {"applicable": True, "sha256": "c" * 64}}}
    before = copy.deepcopy(original)
    extra = x.missing_variants(original, templates)
    assert original == before
    assert len(extra) == 1
    assert extra[0] == {**pair("host_wall"), "request_sha256": "c" * 64}


def test_a_saved_mode_is_never_counted_a_second_time():
    original = [pair(), pair("host_wall")]
    templates = {original[0]["damage_id"]: {
        "world": {"applicable": True, "sha256": "b" * 64},
        "host_wall": {"applicable": True, "sha256": "c" * 64}}}
    assert x.missing_variants(original, templates) == []


def test_inapplicable_host_does_not_become_an_extra_pair():
    templates = {pair()["damage_id"]: {
        "world": {"applicable": True, "sha256": "b" * 64},
        "host_wall": {"applicable": False}}}
    assert x.missing_variants([pair()], templates) == []


def test_existing_extra_five_separates_borrowed_and_new_damage_pairs():
    assert x.plan_targets(25, 1) == {
        "baseline_pairs": 25, "target_added_pairs": 5,
        "borrowed_pairs": 1, "target_new_damage_pairs": 4, "total_target_pairs": 30}


def test_excess_borrowed_capacity_is_truncated_to_the_requested_addition():
    assert x.plan_targets(25, 6)["borrowed_pairs"] == 5
    assert x.plan_targets(25, 6)["target_new_damage_pairs"] == 0


def test_replacement_source_can_target_thirty_without_relabeling_old_zero():
    assert x.plan_targets(0, 0, replacement=True)["target_new_damage_pairs"] == 30
    with pytest.raises(ValueError, match="CAP"):
        x.plan_targets(31, 0)


def test_variant_merge_rejects_duplicate_damage_and_mode():
    with pytest.raises(ValueError, match="DUPLICATE"):
        x.verify_pair_uniqueness([pair(), pair()])
    assert x.verify_pair_uniqueness([pair(), pair("host_wall")]) is True


def test_known_unconfirmed_wall_excludes_deletion_but_keeps_properties():
    target = {"guid": "door-one", "host": {"guid": "wall-one"},
              "opening_guid": "opening-one"}
    inventory = {"targets": {"door": [target], "window": [], "beam": [], "column": []},
                 "properties": [{"guid": "door-one", "pset_name": "Common"}]}
    filtered, exclusions = x.exclude_known_geometry(inventory, [{"host_guid": "wall-one"}])
    assert filtered["targets"]["door"] == []
    assert filtered["properties"] == inventory["properties"]
    assert exclusions[0]["reason"] == "KNOWN_WALL_INTERIOR_AND_CLOSURE_UNCONFIRMED"
    assert inventory["targets"]["door"] == [target]


def test_thirty_quota_wrapper_keeps_the_original_durable_locked_loop(tmp_path, monkeypatch):
    source = tmp_path / "intact.ifc"
    source.write_bytes(b"metadata-only-entry-fixture")
    spec = {"source_id": "formal-041", "input_path": str(source),
            "source_sha256": x.q.sha256(source)}
    calls = []
    monkeypatch.setattr(x.q, "_exclusive_lock", lambda _: nullcontext())
    monkeypatch.setattr(x.resume_engine, "_locked", lambda *args, **kw: calls.append(kw) or "locked")
    assert x.process_mother_up_to_30(spec, tmp_path, tmp_path / "round",
                                   pairs_per_ifc=30) == "locked"
    assert calls[0]["pairs_per_ifc"] == 30
    with pytest.raises(ValueError, match="1_TO_30"):
        x.process_mother_up_to_30(spec, tmp_path, tmp_path / "other", pairs_per_ifc=31)


def test_entry_wrapper_refuses_changed_source_before_any_locked_work(tmp_path, monkeypatch):
    source = tmp_path / "intact.ifc"
    source.write_bytes(b"metadata-only-entry-fixture")
    spec = {"source_id": "formal-041", "input_path": str(source), "source_sha256": "f" * 64}
    monkeypatch.setattr(x.resume_engine, "_locked", lambda *_, **__: pytest.fail("must reject before loop"))
    with pytest.raises(ValueError, match="SOURCE_SIZE_OR_SHA_CHANGED"):
        x.process_mother_up_to_30(spec, tmp_path, tmp_path / "round", pairs_per_ifc=30)


def test_known_wall_filter_accepts_non_hosted_structural_targets():
    inventory = {"targets": {"beam": [{"guid": "beam-one", "host": None}]}, "properties": []}
    filtered, excluded = x.exclude_known_geometry(inventory, [{"host_guid": "wall-one"}])
    assert filtered["targets"]["beam"] == inventory["targets"]["beam"]
    assert excluded == []


def test_round_adapter_restores_all_old_bindings_when_work_raises():
    names = ('_program_bindings', '_configuration', 'iter_raw_recipes', 'iter_prepared_recipes',
             'make_pair_records', '_check_damage', '_candidate_inventory')
    before = {name: getattr(x.q, name) for name in names}
    guard = x.engine.guard_geometry
    with pytest.raises(RuntimeError, match="interrupted"):
        with x.extension_adapter({"replacement": False}, set(), set(), []):
            assert x.q.make_pair_records is not before['make_pair_records']
            raise RuntimeError("interrupted")
    assert all(getattr(x.q, name) is value for name, value in before.items())
    assert x.engine.guard_geometry is guard


def test_changed_parent_checkpoint_blocks_append_before_writing(tmp_path, monkeypatch):
    spec = {"source_id": "formal-041"}
    monkeypatch.setattr(x, "baseline_rows", lambda _: [])
    monkeypatch.setattr(x, "_baseline_binding", lambda *_: {"changed": "c" * 64})
    plan = {"replacement": True, "borrowed_bound_hashes": {}, "target_added_pairs": 30,
            "baseline_binding": {"prior": "p" * 64}}
    monkeypatch.setattr(x, "process_mother_up_to_30", lambda *_, **__: pytest.fail("must reject"))
    with pytest.raises(ValueError, match="EXTENSION_BASELINE_CHANGED"):
        x.extension_mother(tmp_path, spec, repository=tmp_path, plan=plan)
    assert not (tmp_path / "private/extension-r2").exists()


def test_loaded_project_file_must_be_declared_and_hash_bound(tmp_path):
    code = tmp_path / "src/text2ifc_extra/example.py"
    code.parent.mkdir(parents=True)
    code.write_bytes(b"bound-module")
    modules = {"text2ifc_extra.example": SimpleNamespace(__file__=str(code))}
    relative = code.relative_to(tmp_path).as_posix()
    digest = x.q.sha256(code)
    assert x.loaded_programs(tmp_path, {relative: digest}, modules)["text2ifc_extra.example"]["sha256"] == digest
    with pytest.raises(ValueError, match="UNBOUND_ACTUAL_LOADED"):
        x.loaded_programs(tmp_path, {}, modules)
    with pytest.raises(ValueError, match="UNBOUND_ACTUAL_LOADED"):
        x.loaded_programs(tmp_path, {relative: "f" * 64}, modules)
