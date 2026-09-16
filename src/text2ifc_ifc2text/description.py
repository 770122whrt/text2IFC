"""Deterministic first IFC2Text design-description baseline."""

from __future__ import annotations

from typing import Any


DESCRIPTION_SCHEMA_VERSION = "text2ifc/ifc2text-description/0.1"


def _m(mm: float | None) -> str:
    return "未知" if mm is None else f"{mm / 1000.0:.3f} m"


def _point(values: list[float] | None) -> str:
    if not values:
        return "未知"
    return f"({values[0] / 1000.0:.3f}, {values[1] / 1000.0:.3f}, {values[2] / 1000.0:.3f}) m"


def _xy(values: list[float] | None) -> str:
    if not values:
        return "未知"
    return f"({values[0] / 1000.0:.3f}, {values[1] / 1000.0:.3f}) m"


def _bounds(bounds: dict[str, list[float]] | None) -> str:
    if not bounds:
        return "几何范围未能可靠读取"
    return (
        f"X={_m(bounds['x'][0])}～{_m(bounds['x'][1])}，"
        f"Y={_m(bounds['y'][0])}～{_m(bounds['y'][1])}，"
        f"Z={_m(bounds['z'][0])}～{_m(bounds['z'][1])}"
    )


def _display_name(item: dict[str, Any]) -> str:
    name = item.get("name") or item.get("long_name")
    return item["label"] if not name else f"{item['label']}（{name}）"


def render_design_description(facts: dict[str, Any]) -> str:
    """Render every measured major fact once in a readable storey-first form.

    The output deliberately excludes source GlobalIds.  Reconstruction therefore
    receives architectural facts and local labels, not source identity shortcuts.
    """
    building = facts["building"]
    lines = [
        "# 建筑设计说明（IFC2Text 基线）",
        "",
        "## 一、整体概况",
        "",
        f"本说明依据 IFC 模型中可读取或可计算的事实生成。建筑共 {building['storey_count']} 层。",
        f"项目名称：{building.get('project_name') or '未提供'}；建筑名称：{building.get('building_name') or '未提供'}。",
        "所有坐标均使用源 IFC 的统一世界坐标系，长度单位为米；未提供真实北向时，不把 X/Y 轴解释为东、西、南、北。",
        "墙体按中心轴起点和终点定位；门窗若存在标准开洞关系，则优先按其宿主墙起点的沿墙距离和墙底标高定位。",
        "",
    ]
    for storey in facts["storeys"]:
        lines.extend(
            [
                f"## 二、楼层 {storey['label']}：{storey.get('name') or '未命名楼层'}",
                "",
                f"本层基准标高为 {_m(storey.get('elevation_mm'))}。读取到 {len(storey['walls'])} 面墙、{len(storey['doors'])} 扇门、{len(storey['windows'])} 扇窗、{len(storey['openings'])} 个开口。",
                "",
            ]
        )
        if storey["spaces"]:
            lines.append("### 房间与空间")
            lines.append("")
            for space in storey["spaces"]:
                wall_text = "、".join(space.get("boundary_walls", [])) or "未提供可靠 IfcRelSpaceBoundary"
                lines.append(
                    f"- {_display_name(space)}：来源为 IfcSpace；{_bounds(space.get('bounds_mm'))}；"
                    f"边界墙记录为 {wall_text}。"
                )
            lines.append("")
        elif storey["derived_spaces"]:
            lines.append("### 几何推导的封闭区域")
            lines.append("")
            lines.append("本层没有可用 IfcSpace。以下仅是由直墙中心轴围合得到的几何区域，不据此猜测卧室、走廊等用途。")
            for region in storey["derived_spaces"]:
                lines.append(
                    f"- {region['label']}：面积约 {region['area_m2']:.3f} m²，几何中心 {_xy(region['centroid_xy_mm'])}；"
                    "用途未知。"
                )
            lines.append("")
        else:
            lines.extend(
                [
                    "### 空间划分",
                    "",
                    "本层没有可靠的 IfcSpace，现有墙体几何也不足以形成可信的封闭区域；因此不补造房间或用途，以下直接给出构件布置。",
                    "",
                ]
            )

        lines.extend(["### 墙体布置", ""])
        for wall in storey["walls"]:
            if wall.get("measurement_status") == "measured":
                spaces = "、".join(wall.get("spaces", []))
                relation = f"；与空间 {spaces} 有边界关系" if spaces else ""
                lines.append(
                    f"- {_display_name(wall)}：中心轴从 {_point(wall.get('axis_start_mm'))} 到 {_point(wall.get('axis_end_mm'))}，"
                    f"长 {_m(wall.get('length_mm'))}、厚 {_m(wall.get('thickness_mm'))}、高 {_m(wall.get('height_mm'))}{relation}。"
                )
            else:
                lines.append(f"- {_display_name(wall)}：精确直墙轴线未能读取；{_bounds(wall.get('bounds_mm'))}。")
        if not storey["walls"]:
            lines.append("- 本层未读取到墙体。")
        lines.append("")

        lines.extend(["### 门窗与开口", ""])
        for category_name, items in (("门", storey["doors"]), ("窗", storey["windows"])):
            for item in items:
                host = item.get("host_wall")
                position = item.get("host_position_mm")
                if host and position:
                    placement = (
                        f"位于宿主墙 {host}，中心距该墙轴线起点 {_m(position.get('center_offset_mm'))}，"
                        f"底部相对墙局部基准高 {_m(position.get('sill_height_mm'))}"
                    )
                else:
                    placement = f"标准宿主定位关系不足；世界坐标几何中心为 {_point(item.get('centroid_mm'))}"
                lines.append(
                    f"- {category_name} {_display_name(item)}：{placement}；"
                    f"名义宽 {_m(item.get('overall_width_mm'))}、高 {_m(item.get('overall_height_mm'))}。"
                )
        unfilled = [opening for opening in storey["openings"] if not opening.get("filling")]
        for opening in unfilled:
            position = opening.get("host_position_mm")
            dimensions = opening.get("dimensions_mm", {})
            if opening.get("host_wall") and position:
                lines.append(
                    f"- 未填充开口 {_display_name(opening)}：位于 {opening['host_wall']}，中心沿墙偏移 {_m(position.get('center_offset_mm'))}，"
                    f"底部高 {_m(position.get('sill_height_mm'))}，宽 {_m(dimensions.get('width'))}、高 {_m(dimensions.get('height'))}。"
                )
            else:
                lines.append(f"- 未填充开口 {_display_name(opening)}：{_bounds(opening.get('bounds_mm'))}。")
        if not storey["doors"] and not storey["windows"] and not unfilled:
            lines.append("- 本层未读取到门、窗或独立开口。")
        lines.append("")

        if storey["stairs"]:
            lines.extend(["### 楼梯与跨层构件", ""])
            for stair in storey["stairs"]:
                spans = "、".join(stair.get("spans_storeys_by_geometry", []))
                span_text = f"；按几何高度覆盖楼层 {spans}" if spans else ""
                lines.append(
                    f"- {_display_name(stair)}：{_bounds(stair.get('bounds_mm'))}{span_text}。"
                    "这里的跨层范围来自几何高度，不把它等同于未提供的语义连接关系。"
                )
            lines.append("")

    unassigned_count = sum(len(items) for items in facts["unassigned"].values())
    lines.extend(["## 三、读取限制与未分配信息", ""])
    lines.append(f"共有 {unassigned_count} 个本阶段关注构件未能可靠归入楼层；另记录 {len(facts['issues'])} 个解析、几何或空间推导问题。")
    if facts["issues"]:
        codes: dict[str, int] = {}
        for issue in facts["issues"]:
            codes[issue["code"]] = codes.get(issue["code"], 0) + 1
        lines.append("问题类型：" + "、".join(f"{code}×{count}" for code, count in sorted(codes.items())) + "。")
    lines.append("这些缺失项不由语言模型补写；重建与比较时继续保留为未验证或不支持项。")
    lines.append("")
    return "\n".join(lines)
