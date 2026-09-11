"""Discover public GitHub IFC2X3 files below 10 MiB and compare them with local canonical IFCs."""

from __future__ import annotations

import concurrent.futures
import hashlib
import json
import re
import ssl
import urllib.request
from pathlib import Path

import certifi

ROOT = Path(__file__).resolve().parents[2]
LOCAL_MANIFEST = ROOT / "dataset/manifests/ifc-files.jsonl"
OUTPUT = ROOT / ".tmp/dataset-acquisition/ifc2x3-small-github-candidates.jsonl"
REPORT = ROOT / "docs/reports/ifc2x3-small-model-web-search.md"
MAX_BYTES = 10 * 1024 * 1024
USER_AGENT = "text2ifc-dataset-discovery/1.0"
SCHEMA_RE = re.compile(rb"FILE_SCHEMA\s*\(\s*\(\s*['\"]([^'\"]+)", re.I)

REPOSITORIES = (
    "Moult/ifc-test-files",
    "IfcOpenShell/files",
    "ThatOpen/engine_web-ifc",
    "ThatOpen/web-ifc-three",
    "opensourceBIM/IFC-files",
    "opensourceBIM/TestFiles",
    "buildingSMART/Sample-Test-Files",
    "xBimTeam/XbimSamples",
    "xBimTeam/XbimEssentials",
    "AsuniSoft/ifc2x3-SDK",
    "stijngoedertier/georeference-ifc",
    "andyward/XBimDemo",
    "compas-dev/compas_ifc",
    "mac999/infra_physics_sim",
    "GeometryGym/GeometryGymIFCExamples",
)


def request_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"})
    ctx = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(req, timeout=60, context=ctx) as response:
        return json.load(response)


def download(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    ctx = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(req, timeout=120, context=ctx) as response:
        return response.read(MAX_BYTES + 1)


def local_hashes() -> dict[str, str]:
    result: dict[str, str] = {}
    for line in LOCAL_MANIFEST.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            result[str(row["sha256"])] = str(row["local_path"])
    return result


def enumerate_repo(repo: str) -> tuple[dict, list[dict]]:
    meta = request_json(f"https://api.github.com/repos/{repo}")
    branch = str(meta["default_branch"])
    tree = request_json(f"https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1")
    candidates = []
    for item in tree.get("tree", []):
        path = str(item.get("path", ""))
        size = item.get("size")
        if item.get("type") != "blob" or not path.lower().endswith(".ifc"):
            continue
        if not isinstance(size, int) or size >= MAX_BYTES:
            continue
        candidates.append({"path": path, "size_bytes": size, "branch": branch})
    license_info = meta.get("license") or {}
    repo_info = {
        "repo": repo,
        "default_branch": branch,
        "repository_license_spdx": license_info.get("spdx_id"),
        "repository_license_name": license_info.get("name"),
        "html_url": meta.get("html_url"),
    }
    return repo_info, candidates


def inspect_candidate(repo_info: dict, item: dict, known: dict[str, str]) -> dict | None:
    repo = repo_info["repo"]
    branch = item["branch"]
    path = item["path"]
    raw_url = f"https://raw.githubusercontent.com/{repo}/{branch}/{path}"
    try:
        data = download(raw_url)
    except Exception as exc:
        return {
            **repo_info,
            **item,
            "raw_url": raw_url,
            "status": "download_error",
            "error": f"{type(exc).__name__}:{exc}",
        }
    if len(data) > MAX_BYTES:
        return None
    match = SCHEMA_RE.search(data[:1024 * 1024])
    schema = match.group(1).decode("ascii", errors="replace").upper() if match else "UNKNOWN"
    if schema != "IFC2X3":
        return None
    digest = hashlib.sha256(data).hexdigest()
    duplicate = known.get(digest)
    return {
        **repo_info,
        **item,
        "raw_url": raw_url,
        "schema": schema,
        "sha256": digest,
        "size_bytes": len(data),
        "size_mib": round(len(data) / 1024 / 1024, 6),
        "local_exact_duplicate": duplicate,
        "status": "exact_duplicate_local" if duplicate else "new_candidate",
        "admission": "discovery_only",
        "license_note": "Repository license metadata is recorded for discovery only; file/model rights must be reviewed before canonical admission.",
    }


def main() -> int:
    known = local_hashes()
    repo_entries: list[tuple[dict, list[dict]]] = []
    for repo in REPOSITORIES:
        try:
            info, items = enumerate_repo(repo)
            repo_entries.append((info, items))
            print(f"ENUM {repo} under10MiB_ifc={len(items)}", flush=True)
        except Exception as exc:
            print(f"ENUM_ERROR {repo} {type(exc).__name__}:{exc}", flush=True)

    tasks = [(info, item) for info, items in repo_entries for item in items]
    records: list[dict] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
        futures = [executor.submit(inspect_candidate, info, item, known) for info, item in tasks]
        for index, future in enumerate(concurrent.futures.as_completed(futures), start=1):
            result = future.result()
            if result is not None:
                records.append(result)
            if index % 50 == 0:
                print(f"INSPECT {index}/{len(futures)} ifc2x3_or_errors={len(records)}", flush=True)

    records.sort(key=lambda row: (row.get("status", ""), row.get("size_bytes", 0), row["repo"], row["path"].casefold()))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for row in records), encoding="utf-8")

    valid = [row for row in records if row.get("schema") == "IFC2X3"]
    new = [row for row in valid if row.get("status") == "new_candidate"]
    dup = [row for row in valid if row.get("status") == "exact_duplicate_local"]
    lt1 = [row for row in new if row["size_bytes"] < 1024 * 1024]
    lt3 = [row for row in new if row["size_bytes"] < 3 * 1024 * 1024]

    lines = [
        "# IFC2X3 Small Model Web Search",
        "",
        "> Discovery-only scan. Candidates are not canonical dataset members until license/source review and technical admission are complete.",
        "",
        f"- Repositories scanned: **{len(repo_entries)}**",
        f"- IFC2X3 files under 10 MiB found: **{len(valid)}**",
        f"- Exact duplicates of local canonical IFC: **{len(dup)}**",
        f"- New candidates under 10 MiB: **{len(new)}**",
        f"- New candidates under 3 MiB: **{len(lt3)}**",
        f"- New candidates under 1 MiB: **{len(lt1)}**",
        "- Machine-readable candidates: `dataset/manifests/acquisitions/ifc2x3-small-github-candidates.jsonl`",
        "",
        "## New candidates",
        "",
        "| Size (MiB) | Repository | Repository license | Path |",
        "| ---: | --- | --- | --- |",
    ]
    for row in sorted(new, key=lambda r: (r["size_bytes"], r["repo"], r["path"].casefold())):
        lines.append(f"| {row['size_mib']:.3f} | `{row['repo']}` | `{row.get('repository_license_spdx')}` | `{row['path']}` |")
    lines += ["", "## Exact duplicates already local", "", "| Size (MiB) | Repository path | Local canonical path |", "| ---: | --- | --- |"]
    for row in sorted(dup, key=lambda r: (r["size_bytes"], r["repo"], r["path"].casefold())):
        lines.append(f"| {row['size_mib']:.3f} | `{row['repo']}:{row['path']}` | `{row['local_exact_duplicate']}` |")
    lines.append("")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({"repos_scanned": len(repo_entries), "ifc2x3_under10": len(valid), "new_under10": len(new), "new_under3": len(lt3), "new_under1": len(lt1), "duplicates_local": len(dup)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
