"""Run one real DeepSeek UAT against the Phase 10.3 damaged vvo fixture."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from text2ifc_agent.openai_compat import load_openai_compatible_config
from text2ifc_ifc_repair.api import RepairAPI
from text2ifc_ifc_repair.mutation import remove_windows_and_openings_batch
from text2ifc_ifc_repair.projection import (
    project_public_batch_repair_spec,
    render_batch_repair_request,
)
from text2ifc_text.splits import atomic_write_text


def _environment(path: Path) -> dict[str, str]:
    environment = dict(os.environ)
    if path.is_file():
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            environment.setdefault(
                key.strip(),
                value.strip().strip('"').strip("'"),
            )
    return environment


def main() -> int:
    offline = (
        ROOT
        / "dataset"
        / "processed"
        / "ifc-repair"
        / "phase10.3-vvo-five-window-offline"
    )
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument(
        "--case-manifest",
        type=Path,
        default=(
            ROOT
            / "dataset"
            / "manifests"
            / "ifc-repair-cases"
            / "vvo-five-window-001.private.json"
        ),
    )
    parser.add_argument("--damaged-ifc", type=Path, default=offline / "fixture" / "damaged.ifc")
    parser.add_argument("--request", type=Path, default=offline / "request.txt")
    parser.add_argument("--prepare-fixture", action="store_true")
    parser.add_argument(
        "--output",
        type=Path,
        default=(
            ROOT
            / "dataset"
            / "processed"
            / "ifc-repair"
            / "phase10.3-vvo-five-window-deepseek-uat"
        ),
    )
    args = parser.parse_args()
    damaged_ifc = args.damaged_ifc
    request_path = args.request
    case = json.loads(args.case_manifest.read_text(encoding="utf-8"))
    if args.prepare_fixture:
        fixture = args.output / "fixture"
        remove_windows_and_openings_batch(
            source_path=ROOT / case["source"]["local_path"],
            output_dir=fixture,
            targets=case["targets"],
            expected_source_sha256=case["source"]["sha256"],
        )
        private_manifest = json.loads(
            (fixture / "mutation_manifest.private.json").read_text(encoding="utf-8")
        )
        public_spec = project_public_batch_repair_spec(
            private_manifest,
            request_id=f"{case['case_id']}-live-001",
        )
        damaged_ifc = fixture / "damaged.ifc"
        request_path = args.output / "request.txt"
        atomic_write_text(request_path, render_batch_repair_request(public_spec))
    if not damaged_ifc.is_file() or not request_path.is_file():
        raise SystemExit("OFFLINE_FIXTURE_REQUIRED")
    environment = _environment(args.env_file)
    config = load_openai_compatible_config(environment)
    if not config["configured"]:
        print(json.dumps(config, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    request = request_path.read_text(encoding="utf-8")
    api = RepairAPI.from_environment(args.output, environment)
    result = api.start(damaged_ifc, request)
    payload = {
        "schema_version": "text2ifc/phase10.3-live-uat-result/0.1",
        "provider": config["provider"],
        "case_id": case["case_id"],
        "status": result.status,
        "run_id": result.run_id,
        "run_directory": result.run_directory,
        "successful_artifact_publishable": result.successful_artifact_publishable,
        "artifacts": dict(result.artifacts),
        "reason_code": result.reason_code,
        "state_version": result.state_version,
    }
    atomic_write_text(
        args.output / "uat-result.json",
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.status == "succeeded" else 1


if __name__ == "__main__":
    raise SystemExit(main())
