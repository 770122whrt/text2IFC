"""Three frozen public request projections, without private deleted identities."""
from __future__ import annotations

import json
import numpy as np

from .geometry_spec import describe_body


NAMES = {"IfcDoor": "门", "IfcWindow": "窗", "IfcBeam": "梁", "IfcColumn": "柱", "IfcWall": "墙", "IfcWallStandardCase": "墙"}


def _xyz(values):
    return "（" + "，".join(f"{float(v):.6f}".rstrip("0").rstrip(".") if abs(float(v)) >= 0.0000005 else "0" for v in values) + "）"


def _location(target, frame):
    geometry = target["geometry"]
    if frame == "host_wall":
        host = target["host"]
        matrix = np.asarray(geometry["host_frame_world_m"])
        return f"楼层「{target['storey']['name']}」的墙「{host['name']}」上（墙世界基点{_xyz(matrix[:3, 3])}米，世界X/Y/Z轴{_xyz(matrix[:3, 0])}、{_xyz(matrix[:3, 1])}、{_xyz(matrix[:3, 2])}），放置原点相对该墙局部坐标为{_xyz(geometry['origin_host_m'])}米"
    if frame == "storey_local":
        matrix = np.asarray(geometry["storey_frame_world_m"])
        return f"楼层「{target['storey']['name']}」中（楼层世界基点{_xyz(matrix[:3, 3])}米，世界X/Y/Z轴{_xyz(matrix[:3, 0])}、{_xyz(matrix[:3, 1])}、{_xyz(matrix[:3, 2])}），放置原点相对该楼层局部坐标为{_xyz(geometry['origin_storey_m'])}米"
    return f"放置原点的世界坐标为{_xyz(geometry['origin_world_m'])}米"


def _memberships(target):
    frame = np.asarray(target["geometry"]["storey_frame_world_m"])
    row = f"归属楼层「{target['storey']['name']}」（楼层世界基点{_xyz(frame[:3, 3])}米，世界X/Y/Z轴{_xyz(frame[:3, 0])}、{_xyz(frame[:3, 1])}、{_xyz(frame[:3, 2])}）。"
    if target.get("host"):
        frame = np.asarray(target["geometry"]["host_frame_world_m"])
        row += f"宿主墙「{target['host']['name']}」（墙世界基点{_xyz(frame[:3, 3])}米，世界X/Y/Z轴{_xyz(frame[:3, 0])}、{_xyz(frame[:3, 1])}、{_xyz(frame[:3, 2])}）。"
    return row


def _opening(target):
    opening = target.get("opening")
    if not opening or not opening["geometry"].get("body_spec"):
        return None
    geometry = opening["geometry"]
    axes = geometry["axes_world"]
    return f"洞口规格开始：洞口世界原点为{_xyz(geometry['origin_world_m'])}米，洞口世界X/Y/Z轴分别为{_xyz(axes[0])}、{_xyz(axes[1])}、{_xyz(axes[2])}。" + describe_body(geometry["body_spec"], _xyz) + "在上述宿主墙上建立该IfcOpeningElement的void关系，并建立新门窗的门窗填充关系。洞口规格结束。"


def render_prompts(manifest: dict) -> dict:
    results = {}
    deletions = manifest.get("deletions", [])
    properties = manifest.get("property_changes", [])
    targets = [*deletions, *properties]
    for frame in ("host_wall", "world", "storey_local"):
        missing = [target for target in targets if not target.get("geometry") or (frame == "host_wall" and (not target.get("host", {}).get("name") or target["host"].get("name_frame_unique") is False or not target["geometry"].get("origin_host_m"))) or (frame == "storey_local" and (not target.get("storey", {}).get("name") or target["storey"].get("name_frame_unique") is False))]
        if missing:
            results[frame] = None
            continue
        if any(not target["geometry"].get("body_spec") for target in deletions):
            results[frame] = None
            continue
        if any(target["ifc_class"] in {"IfcDoor", "IfcWindow"} and (not target.get("host", {}).get("name") or target["host"].get("name_frame_unique") is False or (not target.get("preserve_opening", True) and _opening(target) is None)) for target in deletions):
            results[frame] = None
            continue
        header = "请按以下要求修复模型。坐标单位为米，尺寸单位为毫米。"
        header += "世界坐标指该IFC模型的放置坐标，不是经纬度。"
        if frame == "storey_local":
            header += "楼层局部坐标采用IFC中该楼层的放置原点和轴方向，不把世界坐标直接当作楼层坐标。"
        elif frame == "host_wall":
            header += "墙局部坐标采用该墙的放置原点和轴方向；墙名称重复时须结合楼层及坐标定位。"
        rows = [header]
        for index, target in enumerate(deletions, 1):
            geometry = target["geometry"]
            row = f"{index}. 补建一{ '扇' if target['ifc_class'] in {'IfcDoor', 'IfcWindow'} else '根'}{NAMES[target['ifc_class']]}：{_location(target, frame)}。"
            row += _memberships(target)
            axes = geometry["axes_world"] if frame == "world" else geometry["axes_host"] if frame == "host_wall" else geometry["axes_storey"]
            row += f"构件自身X、Y、Z轴在上述坐标系中的方向分别为{_xyz(axes[0])}、{_xyz(axes[1])}、{_xyz(axes[2])}。自身坐标的外包范围下角点为{_xyz([v * 1000 for v in geometry['bounds_local_m'][0]])}毫米，上角点为{_xyz([v * 1000 for v in geometry['bounds_local_m'][1]])}毫米。"
            row += describe_body(geometry["body_spec"], _xyz)
            if target["ifc_class"] in {"IfcDoor", "IfcWindow"}:
                if target.get("preserve_opening", True):
                    geometry = target["opening"]["geometry"]
                    row += f"保留现有洞口（其世界原点为{_xyz(geometry['origin_world_m'])}米），将新门窗填入上述宿主墙的该洞口，建立门窗填充关系。"
                else:
                    row += _opening(target)
            if target.get("type_name"):
                row += f"原有类型「{target['type_name']}」如仍存在，请沿用其样式及材料。"
            rows.append(row)
        for change in properties:
            value = "是" if change["before"] is True else "否" if change["before"] is False else json.dumps(change["before"], ensure_ascii=False)
            rows.append(f"将现有{NAMES.get(change['ifc_class'], change['ifc_class'])}「{change.get('name') or '未命名构件'}」（{_location(change, frame)}）的实例属性「{change['pset_name']}.{change['property_name']}」改为{value}，保留其原属性类型。")
        rows.append("除以上补建、洞口关系及指定实例属性外，其余构件、楼层、尺寸、位置、类型和材料保持原样。")
        results[frame] = "\n".join(rows) + "\n"
    return results
