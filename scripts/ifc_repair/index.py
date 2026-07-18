from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from text2ifc_ifc_repair.index_store import IndexStoreError, SQLiteIndexRepository
from text2ifc_ifc_repair.indexer import IndexBuildError, build_ifc_index
from text2ifc_ifc_repair.target_context import TargetContextError, build_target_context
from text2ifc_ifc_repair.target_query import TargetQuery, resolve_target


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build and query a local IFC target index")
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build")
    build.add_argument("source", type=Path)
    build.add_argument("--database", type=Path, required=True)
    query = commands.add_parser("query")
    query.add_argument("database", type=Path)
    query.add_argument("--query", type=Path, required=True)
    query.add_argument("--diagnostic", action="store_true")
    query.add_argument("--max-bytes", type=int, default=12_000)
    arguments = parser.parse_args(argv)
    if arguments.command == "build":
        return _build(arguments.source, arguments.database)
    return _query(arguments.database, arguments.query, arguments.diagnostic, arguments.max_bytes)


def _build(source: Path, database: Path) -> int:
    try:
        metadata = build_ifc_index(source, database)
        with SQLiteIndexRepository.open(database) as repository:
            count = sum(1 for _ in repository.iter_records())
    except (IndexBuildError, IndexStoreError, OSError) as error:
        _print({"status": "error", "code": getattr(error, "code", "INDEX_BUILD_FAILED"), "message": str(error)})
        return 1
    _print({"status": "built", "database": str(database), "record_count": count, "metadata": metadata.__dict__})
    return 0


def _query(database: Path, query_path: Path, diagnostic: bool, max_bytes: int) -> int:
    try:
        payload = json.loads(query_path.read_text(encoding="utf-8"))
        query = TargetQuery.from_dict(payload)
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
        _print({"status": "error", "code": "INVALID_TARGET_QUERY", "message": str(error)})
        return 2
    try:
        with SQLiteIndexRepository.open(database) as repository:
            result = resolve_target(repository, query)
            context = build_target_context(
                repository, query, result, diagnostic=diagnostic, max_bytes=max_bytes
            )
    except (IndexStoreError, TargetContextError, OSError) as error:
        _print({"status": "error", "code": getattr(error, "code", "INDEX_QUERY_FAILED"), "message": str(error)})
        return 1
    _print({"resolution": result.to_dict(), "context": context})
    return 0 if result.status == "resolved" else 3


def _print(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False))


if __name__ == "__main__":
    raise SystemExit(main())
