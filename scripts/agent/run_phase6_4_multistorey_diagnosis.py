"""Run Phase 6.4 multistorey route-loop diagnosis cases."""

from __future__ import annotations

import argparse
import io
import json
import shutil
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from scripts.agent.run_phase6_2_cli import load_env_file  # noqa: E402
from scripts.agent import run_text2ifc_chat  # noqa: E402
from text2ifc_agent.multistorey_diagnosis import build_multistorey_diagnosis_summary  # noqa: E402
from text2ifc_agent.session_store import SessionStore  # noqa: E402


DEFAULT_OUTPUT_ROOT = (
    ROOT / "dataset" / "processed" / "agent-demo" / "phase6.4-multistorey-diagnosis"
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--case", choices=sorted(_cases()), action="append")
    args = parser.parse_args(argv)

    load_env_file(args.env_file)
    args.output_root.mkdir(parents=True, exist_ok=True)
    case_ids = args.case or list(_cases())
    for case_id in case_ids:
        _run_case(case_id=case_id, prompt=_cases()[case_id], output_root=args.output_root)
    summary = build_multistorey_diagnosis_summary(args.output_root)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


def _run_case(*, case_id: str, prompt: str, output_root: Path) -> None:
    case_work_root = output_root / "_work" / case_id
    case_work_root.mkdir(parents=True, exist_ok=True)
    transcript = io.StringIO()
    stdout = _TeeStream(transcript, sys.stdout)
    driver = _InputDriver(initial_prompt=prompt)
    exit_code = run_text2ifc_chat.main(
        [
            "--live",
            "--env-file",
            str(ROOT / ".env"),
            "--output-root",
            str(case_work_root),
            "--db",
            str(case_work_root / "sessions.sqlite"),
            "--trace-level",
            "compact",
        ],
        input_func=driver,
        stdout=stdout,
    )
    store = SessionStore.open(case_work_root / "sessions.sqlite", artifact_root=case_work_root)
    try:
        session = store.list_sessions()[-1]
        export = store.session_export_payload(session.session_id)
    finally:
        store.close()
    run_dir = case_work_root / "runs" / session.session_hash
    case_dir = output_root / case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    _write_text(case_dir / "input.txt", prompt)
    _write_text(case_dir / "stdout.txt", transcript.getvalue())
    _write_json(
        case_dir / "diagnosis-run.json",
        {
            "schema_version": "text2ifc/phase6.4-multistorey-diagnosis-run/1.0",
            "case_id": case_id,
            "exit_code": exit_code,
            "session_hash": session.session_hash,
            "session_status": session.status,
            "answer_count": len(driver.answers),
            "answers": driver.answers,
            "source_run_dir": str(run_dir),
        },
    )
    _write_json(case_dir / "session-export.json", export)
    for name in (
        "case-result.json",
        "issues.json",
        "route-decision.json",
        "feedback-rounds.json",
        "report.md",
        "output.ifc",
        "design-brief.json",
        "expected-facts.json",
        "gate-summary.json",
        "geometry-feedback.json",
    ):
        source = run_dir / name
        if source.is_file():
            shutil.copyfile(source, case_dir / name)
    if not (case_dir / "case-result.json").is_file():
        _write_json(
            case_dir / "case-result.json",
            {
                "schema_version": "text2ifc/phase6.4-case-result/1.0",
                "case_id": case_id,
                "final_status": session.status,
                "route": "missing_route_artifact",
                "output_type": "none",
                "blocking_issue_count": 0,
            },
        )
    if not (case_dir / "issues.json").is_file():
        _write_json(
            case_dir / "issues.json",
            {"schema_version": "text2ifc/issues/1.0", "issues": []},
        )
    if not (case_dir / "route-decision.json").is_file():
        _write_json(
            case_dir / "route-decision.json",
            {"schema_version": "text2ifc/route-decision/2.0", "route": "missing_route_artifact", "final_status": session.status},
        )


class _InputDriver:
    def __init__(self, *, initial_prompt: str) -> None:
        self.initial_prompt = initial_prompt
        self.calls = 0
        self.answers: list[str] = []

    def __call__(self, prompt: str) -> str:
        self.calls += 1
        if self.calls == 1:
            return self.initial_prompt
        answer = (
            "请严格依据我已经给出的尺寸、楼层、门窗、楼梯和空间关系处理；"
            "如果仍缺少必要事实，请保持 Draft 并列出缺失项，不要编造。"
        )
        self.answers.append(answer)
        return answer


class _TeeStream:
    def __init__(self, capture: io.StringIO, console: Any) -> None:
        self.capture = capture
        self.console = console

    def write(self, text: str) -> int:
        self.capture.write(text)
        return self.console.write(text)

    def flush(self) -> None:
        self.capture.flush()
        self.console.flush()


def _cases() -> dict[str, str]:
    return {
        "two-storey-residential": _two_storey_prompt(),
        "three-storey-compact": _three_storey_prompt(),
    }


def _legacy_two_storey_prompt() -> str:
    return (
        "创建一个两层小型住宅建筑，单位为毫米。建筑整体为矩形平面，外轮廓尺寸为东西向 10000 mm、南北向 8000 mm，共两层，"
        "每层净高 3000 mm，墙厚 200 mm，楼板厚度 150 mm，首层地板厚度 150 mm。坐标约定为：建筑西南角为原点，X 轴向东，Y 轴向北，Z 轴向上。"
        "首层包含客厅、厨房、卫生间、楼梯间四个空间：客厅位于西南侧，尺寸 6000 mm × 4500 mm；厨房位于东南侧，尺寸 4000 mm × 3500 mm；"
        "卫生间位于东北侧，尺寸 2500 mm × 2500 mm；楼梯间位于西北侧，尺寸 3500 mm × 3500 mm。"
        "首层过道区域用于连接厨房、卫生间和楼梯间，矩形范围为 x=3500..7500 mm、y=3500..8000 mm。"
        "二层包含主卧、次卧、书房、卫生间、走廊五个空间：主卧位于西南侧，尺寸 5000 mm × 4000 mm；次卧位于东南侧，尺寸 4000 mm × 3500 mm；"
        "书房位于东北侧，尺寸 3000 mm × 2500 mm；二层卫生间位于西北侧，尺寸 2500 mm × 2500 mm；二层走廊为矩形，范围为 x=2500..7000 mm、y=3500..5500 mm，连接楼梯口和各房间；二层走廊矩形范围作为控制边界，不再额外施加 1200 mm 宽度约束；二层楼梯平台范围为 x=0..3500 mm、y=4500..5500 mm。"
        "要求生成 IfcBuilding、两个 IfcBuildingStorey、所有 IfcSpace、外墙、内墙、首层地板、二层楼板、屋面板、楼梯、门和窗，并保持空间归属和相邻关系正确。"
        "首层客厅南墙居中设置一樘外门，尺寸 1200 mm × 2200 mm；客厅东墙与厨房之间设置一樘室内门，尺寸 900 mm × 2100 mm；"
        "厨房北墙与卫生间/过道区域之间设置一樘门，尺寸 800 mm × 2100 mm；卫生间西墙设置一樘门，尺寸 750 mm × 2100 mm；楼梯间东墙设置一樘门，尺寸 900 mm × 2100 mm。"
        "二层楼梯上来后进入走廊，走廊分别连接主卧、次卧、书房和卫生间，每个房间门尺寸均为 900 mm × 2100 mm，卫生间门尺寸为 750 mm × 2100 mm。"
        "未单独指定偏移的门窗均居中于宿主墙段；成对窗按门或房间中心线两侧对称布置。"
        "窗户要求如下：客厅南墙设置两扇窗，每扇 1500 mm × 1200 mm，窗台高 900 mm，分布在外门两侧；厨房东墙设置一扇窗，尺寸 1200 mm × 1000 mm，窗台高 1000 mm；"
        "首层卫生间北墙设置一扇小窗，尺寸 800 mm × 600 mm，窗台高 1600 mm；主卧南墙设置两扇窗，每扇 1500 mm × 1200 mm，窗台高 900 mm；"
        "次卧东墙设置一扇窗，尺寸 1400 mm × 1200 mm，窗台高 900 mm；书房北墙设置一扇窗，尺寸 1200 mm × 1000 mm，窗台高 900 mm；"
        "二层卫生间西墙设置一扇小窗，尺寸 800 mm × 600 mm，窗台高 1600 mm。楼梯位于首层楼梯间内，楼梯宽度 1000 mm，从首层 Z=150 mm 起步到二层楼面 Z=3150 mm，"
        "采用直跑或折返楼梯均可，但必须正确连接两层，生成 IfcStair 或等效楼梯构件；二层楼板需要为楼梯预留可通行洞口或明确表达楼梯平台开口关系。所有墙体必须与对应楼层关联，门窗必须嵌入对应墙体并与相邻空间关系一致，"
        "楼板和屋面板应覆盖建筑外轮廓，二层空间位于 Z=3150 mm 以上，屋面板厚度 150 mm，屋面板位于二层顶部 Z=6150 mm 附近。"
    )


def _two_storey_prompt() -> str:
    """Return a geometrically self-consistent control input for live diagnosis."""
    return """创建一个受控的两层住宅测试模型，单位为毫米。建筑外轮廓为 x=0..10000、y=0..8000；西南角为原点，X 向东，Y 向北，Z 向上。首层墙从 Z=0 到 Z=3000；二层墙从 Z=3150 到 Z=6150；墙厚 200，首层地板、二层楼板和屋面板厚度均为 150，屋面板厚度 150 mm，底标高为 Z=6150。每层必须有独立的南、东、北、西四面外墙，二层不得复用首层墙作为宿主。

CONTROL_LAYOUT_V2
以下坐标是精确控制事实，不得改写、补全或用近似位置替代。相同楼层的 IfcSpace 只能在边界接触，不能有正面积重叠。
storey-1.living_room: x=0..4000, y=0..4000
storey-1.kitchen: x=6000..10000, y=0..4000
storey-1.stairwell: x=0..2000, y=4000..8000
storey-1.utility: x=2000..4000, y=4000..8000
storey-1.bathroom: x=6000..10000, y=4000..8000
storey-1.corridor: x=4000..6000, y=0..8000
storey-2.master_bedroom: x=0..4000, y=0..4000
storey-2.bedroom_2: x=6000..10000, y=0..4000
storey-2.stair_landing: x=2000..4000, y=4000..8000
storey-2.study: x=6000..10000, y=4000..8000
storey-2.corridor: x=4000..6000, y=0..8000
stair-opening: x=0..2000, y=4000..8000
首层地板顶面标高为 Z=0，地板实体向下延伸至 Z=-150。
楼梯水平投影长度为 3900 mm，宽度为 1000 mm，平面范围为 x=500..1500、y=4050..7950；楼梯沿 +Y 方向上升，从 Z=150 到 Z=3150。该范围必须保持在 storey-1.stairwell 和 stair-opening 内。

首层和二层都生成上述 IfcSpace。二层楼板在 stair-opening 范围必须生成可通行洞口；该洞口不是 IfcSpace，不能与任何二层空间重叠。生成宽 1000 的直跑 IfcStair：它位于首层 stairwell，连接到二层 stair_landing，并从 Z=150 上升到 Z=3150。

门的宿主和中心如下。每扇门必须位于列出的共享墙段中，宽度沿墙长方向测量。
door-living-corridor: host=storey-1-wall-living-corridor, segment=x=4000,y=0..4000, center=(4000,2000), width=900,height=2100
door-kitchen-corridor: host=storey-1-wall-kitchen-corridor, segment=x=6000,y=0..4000, center=(6000,2000), width=900,height=2100
door-stairwell-utility: host=storey-1-wall-stairwell-utility, segment=x=2000,y=4000..8000, center=(2000,6000), width=900,height=2100
door-utility-corridor: host=storey-1-wall-utility-corridor, segment=x=4000,y=4000..8000, center=(4000,6000), width=900,height=2100
door-bathroom-corridor: host=storey-1-wall-bathroom-corridor, segment=x=6000,y=4000..8000, center=(6000,6000), width=750,height=2100
door-master-corridor: host=storey-2-wall-master-corridor, segment=x=4000,y=0..4000, center=(4000,2000), width=900,height=2100
door-bedroom2-corridor: host=storey-2-wall-bedroom2-corridor, segment=x=6000,y=0..4000, center=(6000,2000), width=900,height=2100
door-landing-corridor: host=storey-2-wall-landing-corridor, segment=x=4000,y=4000..8000, center=(4000,6000), width=900,height=2100
door-study-corridor: host=storey-2-wall-study-corridor, segment=x=6000,y=4000..8000, center=(6000,6000), width=900,height=2100

窗的宿主与全局中心如下：首层客厅南墙 window-living-south 的中心为 (2000,0)，宽 1500、高 1200、窗台高 900；首层厨房东墙 window-kitchen-east 的中心为 (10000,2000)，宽 1200、高 1000、窗台高 1000；首层卫生间北墙 window-bathroom-north 的中心为 (8000,8000)，宽 800、高 600、窗台高 1600。二层主卧南墙 window-master-south 的中心为 (2000,0)，宽 1500、高 1200、窗台高 900；二层次卧东墙 window-bedroom2-east 的中心为 (10000,2000)，宽 1400、高 1200、窗台高 900；二层书房北墙 window-study-north 的中心为 (8000,8000)，宽 1200、高 1000、窗台高 900。

生成 IfcBuilding、两个 IfcBuildingStorey、上述空间、外墙、内墙、楼板、屋面板、IfcStair、门、窗和门窗洞口。所有门窗必须使用本楼层的宿主墙；洞口相对宿主墙使用局部坐标，门窗相对洞口对齐。输出可验证的 BIM JSON 2.0；若任何明确控制事实互相矛盾，返回 Draft 并列出矛盾，不得静默修改坐标。"""


def _three_storey_prompt() -> str:
    return (
        "创建一个三层紧凑办公建筑，单位为毫米。建筑外轮廓为 8000 mm × 6000 mm，三层，每层净高 3000 mm，墙厚 200 mm，楼板厚度 150 mm。"
        "坐标原点在首层西南角，X 向东，Y 向北，Z 向上。每层包含一个开放办公空间和一个楼梯间：办公空间尺寸 6000 mm × 6000 mm，位于西侧；"
        "楼梯间尺寸 2000 mm × 3000 mm，位于东南角。每层都要生成 IfcBuildingStorey 和 IfcSpace。"
        "外墙围合建筑，楼梯间与办公区之间设置内墙和一扇门，门宽 900 mm、高 2100 mm。"
        "首层南墙中部设置入口门，宽 1200 mm、高 2200 mm。每层办公空间北墙设置两扇窗，每扇 1200 mm × 1000 mm，窗台高 900 mm。"
        "生成首层地板、二层楼板、三层楼板和屋面板；屋面板位于三层顶部附近。"
        "楼梯连续连接首层、二层和三层，可使用 IfcStair 或等效楼梯构件，但必须表达三层之间的竖向连接。"
        "所有墙、门、窗、楼板和空间必须归属到正确楼层，并保持空间关系正确。"
    )


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
