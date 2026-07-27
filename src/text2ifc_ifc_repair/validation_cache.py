"""Immutable content-addressed cache for normalized IFC validation evidence."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

import ifcopenshell


CACHE_SCHEMA_VERSION = "text2ifc/ifc-validation-cache/0.1"
CACHE_MODES = frozenset({"off", "read_write", "refresh"})


@dataclass(frozen=True)
class ValidationCacheKey:
    ifc_sha256: str
    ifc_schema: str
    ifcopenshell_version: str
    validation_policy_version: str
    diagnostic_normalization_version: str

    def to_dict(self) -> dict[str, str]:
        return {
            "ifc_sha256": self.ifc_sha256,
            "ifc_schema": self.ifc_schema,
            "ifcopenshell_version": self.ifcopenshell_version,
            "validation_policy_version": self.validation_policy_version,
            "diagnostic_normalization_version": self.diagnostic_normalization_version,
        }

    @property
    def digest(self) -> str:
        return hashlib.sha256(_canonical(self.to_dict())).hexdigest()


class ValidationCache:
    def __init__(self, root: str | Path, *, mode: str = "read_write") -> None:
        if mode not in CACHE_MODES:
            raise ValueError(f"VALIDATION_CACHE_MODE_INVALID:{mode}")
        self.root = Path(root)
        self.mode = mode

    def build_key(
        self,
        ifc_path: str | Path,
        *,
        validation_policy_version: str,
        diagnostic_normalization_version: str,
    ) -> ValidationCacheKey:
        source = Path(ifc_path)
        model = ifcopenshell.open(str(source))
        return ValidationCacheKey(
            ifc_sha256="sha256:" + hashlib.sha256(source.read_bytes()).hexdigest(),
            ifc_schema=str(model.schema).upper(),
            ifcopenshell_version=str(ifcopenshell.version),
            validation_policy_version=validation_policy_version,
            diagnostic_normalization_version=diagnostic_normalization_version,
        )

    def get_or_compute(
        self,
        key: ValidationCacheKey,
        compute: Callable[[], Mapping[str, Any]],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        if self.mode == "off":
            result = _json_copy(compute())
            return result, self._evidence(key, "miss", "cache_off")
        if self.mode != "refresh":
            cached, reason = self.read(key)
            if cached is not None:
                return cached, self._evidence(key, "hit", "validated_entry")
        else:
            reason = "refresh_requested"
        result = _json_copy(compute())
        self.write(key, result)
        return result, self._evidence(key, "miss", reason)

    def read(
        self, key: ValidationCacheKey
    ) -> tuple[dict[str, Any] | None, str]:
        path = self._path(key)
        if not path.is_file():
            return None, "entry_missing"
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None, "corrupt_json"
        if not isinstance(document, dict):
            return None, "invalid_envelope"
        if document.get("schema_version") != CACHE_SCHEMA_VERSION:
            return None, "schema_mismatch"
        if document.get("complete") is not True:
            return None, "partial_write"
        if document.get("key") != key.to_dict():
            return None, "key_mismatch"
        result = document.get("result")
        if not isinstance(result, dict):
            return None, "result_missing"
        expected_hash = "sha256:" + hashlib.sha256(
            _canonical(
                {
                    "schema_version": CACHE_SCHEMA_VERSION,
                    "key": key.to_dict(),
                    "result": result,
                    "complete": True,
                }
            )
        ).hexdigest()
        if document.get("payload_sha256") != expected_hash:
            return None, "payload_hash_mismatch"
        if not _valid_result(result):
            return None, "result_consistency_mismatch"
        return _json_copy(result), "validated_entry"

    def write(self, key: ValidationCacheKey, result: Mapping[str, Any]) -> Path:
        normalized = _json_copy(result)
        if not _valid_result(normalized):
            raise ValueError("VALIDATION_CACHE_RESULT_INVALID")
        self.root.mkdir(parents=True, exist_ok=True)
        base = {
            "schema_version": CACHE_SCHEMA_VERSION,
            "key": key.to_dict(),
            "result": normalized,
            "complete": True,
        }
        document = {
            **base,
            "payload_sha256": "sha256:"
            + hashlib.sha256(_canonical(base)).hexdigest(),
        }
        target = self._path(key)
        handle = tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            prefix=f".{target.name}-",
            suffix=".tmp",
            dir=self.root,
            delete=False,
        )
        temporary = Path(handle.name)
        try:
            json.dump(
                document,
                handle,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
            handle.close()
            os.replace(temporary, target)
        finally:
            if not handle.closed:
                handle.close()
            temporary.unlink(missing_ok=True)
        return target

    def _path(self, key: ValidationCacheKey) -> Path:
        return self.root / f"{key.digest}.json"

    def _evidence(
        self, key: ValidationCacheKey, status: str, reason: str
    ) -> dict[str, Any]:
        return {
            "schema_version": CACHE_SCHEMA_VERSION,
            "mode": self.mode,
            "status": status,
            "reason": reason,
            "key_digest": f"sha256:{key.digest}",
            "key": key.to_dict(),
        }


def _valid_result(result: Mapping[str, Any]) -> bool:
    count = result.get("diagnostic_count")
    signatures = result.get("signature_counts")
    diagnostics = result.get("diagnostics")
    return (
        result.get("schema_version") == "text2ifc/ifc-validation-normalized/0.1"
        and isinstance(count, int)
        and count >= 0
        and isinstance(signatures, dict)
        and all(
            isinstance(key, str)
            and isinstance(value, int)
            and value > 0
            for key, value in signatures.items()
        )
        and sum(signatures.values()) == count
        and isinstance(diagnostics, list)
    )


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _json_copy(value: Any) -> Any:
    return json.loads(_canonical(value))


__all__ = [
    "CACHE_MODES",
    "CACHE_SCHEMA_VERSION",
    "ValidationCache",
    "ValidationCacheKey",
]
