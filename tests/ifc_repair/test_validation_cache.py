from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import ifcopenshell

from text2ifc_ifc_repair.ifc_validation import (
    DIAGNOSTIC_NORMALIZATION_VERSION,
    VALIDATION_POLICY_VERSION,
    compare_validation_models,
    normalized_validation_result,
)
from text2ifc_ifc_repair.validation_cache import ValidationCache


def _write_model(path: Path, *, extra_error: bool = False) -> None:
    model = ifcopenshell.file(schema="IFC2X3")
    model.create_entity("IfcCartesianPoint")
    if extra_error:
        model.create_entity("IfcDirection")
    model.write(str(path))


def _key(cache: ValidationCache, path: Path, **overrides):
    return cache.build_key(
        path,
        validation_policy_version=overrides.get(
            "policy", VALIDATION_POLICY_VERSION
        ),
        diagnostic_normalization_version=overrides.get(
            "normalization", DIAGNOSTIC_NORMALIZATION_VERSION
        ),
    )


def _compute(path: Path):
    return normalized_validation_result(ifcopenshell.open(str(path)))


def test_cache_key_contains_five_dimensions_and_recomputes_file_hash(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.ifc"
    _write_model(source)
    cache = ValidationCache(tmp_path / "cache")
    first = _key(cache, source)
    source.write_bytes(source.read_bytes() + b"\n")
    second = _key(cache, source)

    assert set(first.to_dict()) == {
        "ifc_sha256",
        "ifc_schema",
        "ifcopenshell_version",
        "validation_policy_version",
        "diagnostic_normalization_version",
    }
    assert first.ifc_schema == "IFC2X3"
    assert first.ifc_sha256 != second.ifc_sha256
    assert first.digest != second.digest


def test_cache_hit_miss_refresh_and_stale_policy(tmp_path: Path) -> None:
    source = tmp_path / "source.ifc"
    _write_model(source)
    cache = ValidationCache(tmp_path / "cache")
    key = _key(cache, source)
    calls = 0

    def compute():
        nonlocal calls
        calls += 1
        return _compute(source)

    first, first_evidence = cache.get_or_compute(key, compute)
    second, second_evidence = cache.get_or_compute(key, compute)
    stale_key = _key(cache, source, policy="future-policy/9.9")
    _, stale_evidence = cache.get_or_compute(stale_key, compute)
    refresh = ValidationCache(tmp_path / "cache", mode="refresh")
    _, refresh_evidence = refresh.get_or_compute(key, compute)

    assert first == second
    assert calls == 3
    assert first_evidence["status"] == "miss"
    assert second_evidence["status"] == "hit"
    assert stale_evidence["status"] == "miss"
    assert refresh_evidence["reason"] == "refresh_requested"


def test_corrupt_hash_partial_and_key_mismatch_are_cache_misses(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.ifc"
    _write_model(source)
    cache = ValidationCache(tmp_path / "cache")
    key = _key(cache, source)
    result = _compute(source)
    path = cache.write(key, result)

    path.write_text("{broken", encoding="utf-8")
    assert cache.read(key)[1] == "corrupt_json"

    cache.write(key, result)
    document = json.loads(path.read_text(encoding="utf-8"))
    document["complete"] = False
    path.write_text(json.dumps(document), encoding="utf-8")
    assert cache.read(key)[1] == "partial_write"

    cache.write(key, result)
    document = json.loads(path.read_text(encoding="utf-8"))
    document["payload_sha256"] = "sha256:" + "0" * 64
    path.write_text(json.dumps(document), encoding="utf-8")
    assert cache.read(key)[1] == "payload_hash_mismatch"

    cache.write(key, result)
    document = json.loads(path.read_text(encoding="utf-8"))
    document["key"]["ifcopenshell_version"] = "stale"
    path.write_text(json.dumps(document), encoding="utf-8")
    assert cache.read(key)[1] == "key_mismatch"


def test_cached_and_uncached_delta_are_identical(tmp_path: Path) -> None:
    baseline_path = tmp_path / "baseline.ifc"
    candidate_path = tmp_path / "candidate.ifc"
    _write_model(baseline_path)
    _write_model(candidate_path, extra_error=True)
    baseline = ifcopenshell.open(str(baseline_path))
    candidate = ifcopenshell.open(str(candidate_path))
    uncached = compare_validation_models(baseline, candidate)
    cached = compare_validation_models(
        baseline,
        candidate,
        baseline_result=normalized_validation_result(baseline),
        candidate_result=normalized_validation_result(candidate),
    )

    assert cached == uncached


def test_concurrent_atomic_creation_produces_one_valid_entry(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.ifc"
    _write_model(source)
    cache = ValidationCache(tmp_path / "cache")
    key = _key(cache, source)

    def work(_):
        return cache.get_or_compute(key, lambda: _compute(source))[0]

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(work, range(2)))

    assert results[0] == results[1]
    assert cache.read(key)[0] == results[0]
    assert len(list((tmp_path / "cache").glob("*.json"))) == 1
    payload = (tmp_path / "cache" / f"{key.digest}.json").read_text(
        encoding="utf-8"
    )
    for forbidden in (
        "private_original",
        "benchmark_gold",
        "provider",
        "entity_instance",
    ):
        assert forbidden not in payload.casefold()
