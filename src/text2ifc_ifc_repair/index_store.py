from __future__ import annotations

import json
import os
import sqlite3
import uuid
from pathlib import Path
from typing import Any, Iterator

from .index_models import (
    INDEX_SCHEMA_VERSION,
    AliasFact,
    ElementRecord,
    IndexDiagnostic,
    IndexMetadata,
    PropertyFact,
    RelationshipFact,
)


class IndexStoreError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _json_dump(value: Any) -> str:
    return json.dumps(
        value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
    )


def _json_load(value: str) -> Any:
    return json.loads(value)


class SQLiteIndexRepository:
    def __init__(
        self,
        connection: sqlite3.Connection,
        database: Path,
        metadata: IndexMetadata,
        *,
        build_path: Path | None = None,
    ) -> None:
        self._connection = connection
        self._database = database
        self._build_path = build_path
        self._published = False
        self._closed = False
        self.metadata = metadata

    @classmethod
    def create(
        cls, database: str | Path, metadata: IndexMetadata
    ) -> SQLiteIndexRepository:
        target = Path(database)
        target.parent.mkdir(parents=True, exist_ok=True)
        build_path = target.with_name(f"{target.name}.building-{uuid.uuid4().hex}")
        connection = sqlite3.connect(build_path)
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            cls._create_schema(connection)
            connection.execute(
                """INSERT INTO index_metadata (
                    singleton, index_schema_version, source_ifc_sha256, ifc_schema,
                    extractor_version, source_size_bytes, created_at
                ) VALUES (1, ?, ?, ?, ?, ?, ?)""",
                (
                    metadata.index_schema_version,
                    metadata.source_ifc_sha256,
                    metadata.ifc_schema,
                    metadata.extractor_version,
                    metadata.source_size_bytes,
                    metadata.created_at,
                ),
            )
        except Exception:
            connection.close()
            build_path.unlink(missing_ok=True)
            raise
        return cls(connection, target, metadata, build_path=build_path)

    @classmethod
    def open(
        cls,
        database: str | Path,
        *,
        expected_source_ifc_sha256: str | None = None,
        expected_index_schema_version: str | None = None,
    ) -> SQLiteIndexRepository:
        target = Path(database)
        connection = sqlite3.connect(f"file:{target.as_posix()}?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        try:
            row = connection.execute("SELECT * FROM index_metadata WHERE singleton = 1").fetchone()
            if row is None:
                raise IndexStoreError("INDEX_METADATA_MISSING", "Index metadata is missing")
            metadata = IndexMetadata(
                source_ifc_sha256=row["source_ifc_sha256"],
                ifc_schema=row["ifc_schema"],
                extractor_version=row["extractor_version"],
                source_size_bytes=row["source_size_bytes"],
                created_at=row["created_at"],
                index_schema_version=row["index_schema_version"],
            )
            if (
                expected_source_ifc_sha256 is not None
                and metadata.source_ifc_sha256 != expected_source_ifc_sha256
            ):
                raise IndexStoreError(
                    "INDEX_SOURCE_FINGERPRINT_MISMATCH",
                    "The index was built from a different IFC source",
                )
            expected_version = expected_index_schema_version
            if expected_version is not None and metadata.index_schema_version != expected_version:
                raise IndexStoreError(
                    "INDEX_SCHEMA_VERSION_MISMATCH",
                    "The index schema version does not match the requested version",
                )
        except Exception:
            connection.close()
            raise
        return cls(connection, target, metadata)

    @staticmethod
    def _create_schema(connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE index_metadata (
                singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                index_schema_version TEXT NOT NULL,
                source_ifc_sha256 TEXT NOT NULL,
                ifc_schema TEXT NOT NULL,
                extractor_version TEXT NOT NULL,
                source_size_bytes INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE elements (
                record_id TEXT PRIMARY KEY,
                ifc_global_id TEXT,
                identity_reliable INTEGER NOT NULL CHECK (identity_reliable IN (0, 1)),
                ifc_class TEXT NOT NULL,
                name TEXT,
                long_name TEXT,
                tag TEXT,
                object_type TEXT,
                type_name TEXT,
                type_global_id TEXT,
                storey_name TEXT,
                storey_global_id TEXT,
                geometry_capability TEXT NOT NULL,
                geometry_summary_json TEXT NOT NULL,
                facets_json TEXT NOT NULL,
                provenance_json TEXT NOT NULL
            );
            CREATE UNIQUE INDEX reliable_global_id
                ON elements(ifc_global_id) WHERE identity_reliable = 1;
            CREATE TABLE aliases (
                record_id TEXT NOT NULL REFERENCES elements(record_id) ON DELETE CASCADE,
                ordinal INTEGER NOT NULL,
                normalized_value TEXT NOT NULL,
                original_value TEXT NOT NULL,
                field TEXT NOT NULL,
                provenance TEXT NOT NULL,
                PRIMARY KEY (record_id, ordinal)
            );
            CREATE INDEX alias_lookup ON aliases(normalized_value, record_id);
            CREATE TABLE relationships (
                record_id TEXT NOT NULL REFERENCES elements(record_id) ON DELETE CASCADE,
                ordinal INTEGER NOT NULL,
                kind TEXT NOT NULL,
                target_global_id TEXT NOT NULL,
                provenance TEXT NOT NULL,
                PRIMARY KEY (record_id, ordinal)
            );
            CREATE TABLE properties (
                record_id TEXT NOT NULL REFERENCES elements(record_id) ON DELETE CASCADE,
                ordinal INTEGER NOT NULL,
                set_kind TEXT NOT NULL,
                set_name TEXT NOT NULL,
                property_name TEXT NOT NULL,
                value_json TEXT NOT NULL,
                value_type TEXT,
                unit TEXT,
                inherited INTEGER NOT NULL CHECK (inherited IN (0, 1)),
                provenance TEXT NOT NULL,
                PRIMARY KEY (record_id, ordinal)
            );
            CREATE TABLE diagnostics (
                diagnostic_id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL,
                record_id TEXT,
                ifc_global_id TEXT,
                step_id INTEGER,
                evidence_json TEXT NOT NULL
            );
            """
        )

    def put_record(self, record: ElementRecord) -> None:
        self._require_build()
        try:
            self._connection.execute(
                """INSERT INTO elements VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )""",
                (
                    record.record_id,
                    record.ifc_global_id,
                    int(record.identity_reliable),
                    record.ifc_class,
                    record.name,
                    record.long_name,
                    record.tag,
                    record.object_type,
                    record.type_name,
                    record.type_global_id,
                    record.storey_name,
                    record.storey_global_id,
                    record.geometry_capability,
                    _json_dump(record.geometry_summary),
                    _json_dump(record.facets),
                    _json_dump(record.provenance),
                ),
            )
            self._connection.executemany(
                "INSERT INTO aliases VALUES (?, ?, ?, ?, ?, ?)",
                [
                    (
                        record.record_id,
                        ordinal,
                        fact.normalized_value,
                        fact.original_value,
                        fact.field,
                        fact.provenance,
                    )
                    for ordinal, fact in enumerate(record.aliases)
                ],
            )
            self._connection.executemany(
                "INSERT INTO relationships VALUES (?, ?, ?, ?, ?)",
                [
                    (record.record_id, ordinal, fact.kind, fact.target_global_id, fact.provenance)
                    for ordinal, fact in enumerate(record.relationships)
                ],
            )
            self._connection.executemany(
                "INSERT INTO properties VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        record.record_id,
                        ordinal,
                        fact.set_kind,
                        fact.set_name,
                        fact.property_name,
                        _json_dump(fact.value),
                        fact.value_type,
                        fact.unit,
                        int(fact.inherited),
                        fact.provenance,
                    )
                    for ordinal, fact in enumerate(record.properties)
                ],
            )
        except sqlite3.IntegrityError as exc:
            if "elements.ifc_global_id" in str(exc):
                raise IndexStoreError(
                    "DUPLICATE_RELIABLE_GLOBAL_ID",
                    f"Reliable IFC GlobalId is duplicated: {record.ifc_global_id}",
                ) from exc
            raise

    def put_diagnostic(self, diagnostic: IndexDiagnostic) -> None:
        self._require_build()
        self._connection.execute(
            """INSERT INTO diagnostics (
                code, severity, message, record_id, ifc_global_id, step_id, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                diagnostic.code,
                diagnostic.severity,
                diagnostic.message,
                diagnostic.record_id,
                diagnostic.ifc_global_id,
                diagnostic.step_id,
                _json_dump(diagnostic.evidence),
            ),
        )

    def publish(self) -> None:
        self._require_build()
        assert self._build_path is not None
        result = self._connection.execute("PRAGMA integrity_check").fetchone()
        if result is None or result[0] != "ok":
            raise IndexStoreError("INDEX_INTEGRITY_CHECK_FAILED", str(result))
        self._connection.commit()
        self._connection.close()
        self._closed = True
        os.replace(self._build_path, self._database)
        self._published = True

    def get_by_global_id(self, global_id: str) -> ElementRecord | None:
        row = self._connection.execute(
            "SELECT * FROM elements WHERE ifc_global_id = ? AND identity_reliable = 1",
            (global_id,),
        ).fetchone()
        return None if row is None else self._record_from_row(row)

    def iter_records(self) -> Iterator[ElementRecord]:
        rows = self._connection.execute("SELECT * FROM elements ORDER BY record_id")
        for row in rows:
            yield self._record_from_row(row)

    def find_aliases(self, normalized_value: str) -> list[ElementRecord]:
        rows = self._connection.execute(
            """SELECT DISTINCT e.* FROM elements e
               JOIN aliases a ON a.record_id = e.record_id
               WHERE a.normalized_value = ? AND e.identity_reliable = 1
               ORDER BY e.record_id""",
            (normalized_value,),
        )
        return [self._record_from_row(row) for row in rows]

    def properties_for(self, record_id: str) -> list[PropertyFact]:
        rows = self._connection.execute(
            "SELECT * FROM properties WHERE record_id = ? ORDER BY ordinal", (record_id,)
        )
        return [
            PropertyFact(
                set_kind=row["set_kind"],
                set_name=row["set_name"],
                property_name=row["property_name"],
                value=_json_load(row["value_json"]),
                value_type=row["value_type"],
                unit=row["unit"],
                inherited=bool(row["inherited"]),
                provenance=row["provenance"],
            )
            for row in rows
        ]

    def relationships_from(self, record_id: str) -> list[RelationshipFact]:
        rows = self._connection.execute(
            "SELECT * FROM relationships WHERE record_id = ? ORDER BY ordinal", (record_id,)
        )
        return [
            RelationshipFact(row["kind"], row["target_global_id"], row["provenance"])
            for row in rows
        ]

    def diagnostics(self) -> list[IndexDiagnostic]:
        rows = self._connection.execute("SELECT * FROM diagnostics ORDER BY diagnostic_id")
        return [
            IndexDiagnostic(
                code=row["code"],
                severity=row["severity"],
                message=row["message"],
                record_id=row["record_id"],
                ifc_global_id=row["ifc_global_id"],
                step_id=row["step_id"],
                evidence=_json_load(row["evidence_json"]),
            )
            for row in rows
        ]

    def _record_from_row(self, row: sqlite3.Row) -> ElementRecord:
        record_id = row["record_id"]
        aliases = self._connection.execute(
            "SELECT * FROM aliases WHERE record_id = ? ORDER BY ordinal", (record_id,)
        )
        return ElementRecord(
            record_id=record_id,
            ifc_global_id=row["ifc_global_id"],
            identity_reliable=bool(row["identity_reliable"]),
            ifc_class=row["ifc_class"],
            name=row["name"],
            long_name=row["long_name"],
            tag=row["tag"],
            object_type=row["object_type"],
            type_name=row["type_name"],
            type_global_id=row["type_global_id"],
            storey_name=row["storey_name"],
            storey_global_id=row["storey_global_id"],
            geometry_capability=row["geometry_capability"],
            geometry_summary=_json_load(row["geometry_summary_json"]),
            facets=_json_load(row["facets_json"]),
            provenance=_json_load(row["provenance_json"]),
            aliases=tuple(
                AliasFact(
                    item["normalized_value"],
                    item["original_value"],
                    item["field"],
                    item["provenance"],
                )
                for item in aliases
            ),
            relationships=tuple(self.relationships_from(record_id)),
            properties=tuple(self.properties_for(record_id)),
        )

    def _require_build(self) -> None:
        if self._build_path is None or self._published:
            raise IndexStoreError("INDEX_NOT_WRITABLE", "Repository is not writable")

    def close(self) -> None:
        if not self._closed:
            self._connection.close()
            self._closed = True
        if self._build_path is not None and not self._published:
            self._build_path.unlink(missing_ok=True)

    def __enter__(self) -> SQLiteIndexRepository:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if exc_type is not None and not self._closed:
            self._connection.rollback()
        self.close()


__all__ = [
    "INDEX_SCHEMA_VERSION",
    "IndexStoreError",
    "SQLiteIndexRepository",
]
