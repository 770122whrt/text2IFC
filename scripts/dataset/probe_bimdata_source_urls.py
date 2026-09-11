"""Probe BIMData upstream source URLs without downloading large payloads."""

from __future__ import annotations

import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "dataset/manifests/candidates/bimdata-rd-source-evidence.jsonl"
OUTPUT = ROOT / "dataset/manifests/candidates/bimdata-rd-url-probe.jsonl"
HEADERS = {"User-Agent": "text2ifc-dataset/1.0"}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def classify_response(response: requests.Response, prefix: bytes) -> str:
    content_type = (response.headers.get("content-type") or "").lower()
    final_url = response.url.lower()
    if response.status_code >= 400:
        return "dead_or_unreachable"
    if (
        "application/zip" in content_type
        or "application/octet-stream" in content_type
        or final_url.endswith(".ifc")
        or final_url.endswith(".zip")
    ) and not prefix.lstrip().lower().startswith((b"<!doctype html", b"<html")):
        return "direct_file_or_archive"
    if "text/html" in content_type or prefix.lstrip().lower().startswith((b"<!doctype html", b"<html")):
        return "live_landing_page"
    return "live_other"


def main() -> int:
    evidence = read_jsonl(EVIDENCE)
    urls = sorted({url for row in evidence for url in row.get("source_urls") or [] if url})
    rows: list[dict] = []
    for index, url in enumerate(urls, start=1):
        record = {
            "schema_version": "text2ifc/source-url-probe/1.0",
            "url": url,
            "status": "dead_or_unreachable",
            "http_status": None,
            "final_url": None,
            "content_type": None,
            "content_length": None,
            "error": None,
        }
        try:
            with requests.get(
                url,
                headers=HEADERS,
                timeout=30,
                allow_redirects=True,
                stream=True,
            ) as response:
                prefix = next(response.iter_content(2048), b"")
                record["http_status"] = response.status_code
                record["final_url"] = response.url
                record["content_type"] = response.headers.get("content-type")
                record["content_length"] = response.headers.get("content-length")
                record["status"] = classify_response(response, prefix)
        except Exception as exc:
            record["error"] = f"{type(exc).__name__}: {exc}"
        rows.append(record)
        print(f"{index}/{len(urls)} {record['status']} {url}", flush=True)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    print(json.dumps({"urls": len(rows), "status": counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
