"""Opt-in request profile 1.2: wall identity or world coordinates, kept separate."""
from __future__ import annotations

import copy
import json
from collections import Counter

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.unit
import numpy as np

from .geometry_spec import describe_body
from .prompts import NAMES, _xyz

PROFILE = 'text2ifc/dataset-request/1.2'


def prepare_inventory(path, inventory=None):
    """Extract public-resolvable anchors; source and cached inventories stay untouched."""
    from .engine import _matrix, inventory_model

    inv = copy.deepcopy(inventory if inventory and inventory.get('inventory_version', 0) >= 3 else inventory_model(path))
    model = ifcopenshell.open(str(path))
    unit = ifcopenshell.util.unit.calculate_unit_scale(model)
    floor_counts = Counter(x.Name for x in model.by_type('IfcBuildingStorey'))
    walls = model.by_type('IfcWall')
    floor_ids, frames, bounds, index = {}, {}, {}, {}

    def floor_of(entity):
        if entity.id() not in floor_ids:
            floor = ifcopenshell.util.element.get_container(entity, ifc_class='IfcBuildingStorey')
            floor_ids[entity.id()] = floor
        return floor_ids[entity.id()]

    def frame(entity):
        if entity.id() not in frames:
            frames[entity.id()] = _matrix(entity.ObjectPlacement, unit)
        return frames[entity.id()]

    def world_bounds(entity):
        if entity.id() not in bounds:
            settings = ifcopenshell.geom.settings()
            settings.set('use-world-coords', True)
            settings.set('disable-opening-subtractions', True)
            shape = ifcopenshell.geom.create_shape(settings, entity)
            verts = np.asarray(shape.geometry.verts).reshape(-1, 3)
            bounds[entity.id()] = [verts.min(axis=0).tolist(), verts.max(axis=0).tolist()]
        return bounds[entity.id()]

    def counters(cls):
        if cls not in index:
            entities = model.by_type(cls)
            name_counts = Counter((floor_of(e).GlobalId if floor_of(e) else None, e.Name) for e in entities)
            world_counts = Counter(tuple(np.round(frame(e)[:3, :].flatten(), 5)) for e in entities)
            index[cls] = name_counts, world_counts
        return index[cls]

    def peer_info(peer):
        entity = model.by_guid(peer['guid'])
        floor = floor_of(entity)
        names, locations = counters(peer['ifc_class'])
        result = {**peer, 'storey_name': floor.Name if floor else None,
                  'name_storey_unique': bool(entity.Name and floor and floor_counts[floor.Name] == 1 and names[(floor.GlobalId, entity.Name)] == 1),
                  'world_unique': locations[tuple(np.round(frame(entity)[:3, :].flatten(), 5))] == 1}
        if entity.is_a('IfcOpeningElement'):
            fills = list(entity.HasFillings)
            if len(fills) == 1:
                filled = fills[0].RelatedBuildingElement
                ff = frame(filled)
                result['fill_reference'] = peer_info({'guid': filled.GlobalId, 'name': filled.Name, 'ifc_class': filled.is_a(),
                                                      'origin_world_m': ff[:3, 3].tolist(), 'axes_world': ff[:3, :3].T.tolist()})
        return result

    wall_name_counts = Counter((floor_of(w).GlobalId if floor_of(w) else None, w.Name) for w in walls)
    for rows in [*inv['targets'].values(), inv['properties']]:
        for target in rows:
            geometry = target['geometry']
            entity = model.by_guid(target['guid'])
            target['storey']['name_unique'] = floor_counts[target['storey']['name']] == 1
            _, locations = counters(target['ifc_class'])
            geometry['world_unique'] = locations[tuple(np.round(frame(entity)[:3, :].flatten(), 5))] == 1
            host = target.get('host', {})
            if host:
                wall = model.by_guid(host['guid'])
                wf = frame(wall)
                host['name_storey_unique'] = bool(host.get('name') and target['storey']['name_unique'] and wall_name_counts[(target['storey']['guid'], host['name'])] == 1)
                locator = {'origin_world_m': wf[:3, 3].tolist(), 'axes_world': wf[:3, :3].T.tolist(), 'bounds_world_m': world_bounds(wall)}
                similar = [w for w in walls if np.allclose(frame(w), wf, atol=1e-5, rtol=0)]
                host['world_unique'] = sum(np.allclose(world_bounds(w), locator['bounds_world_m'], atol=1e-5, rtol=0) for w in similar) == 1
                host['locator'] = locator
            for item in [geometry, target.get('opening', {}).get('geometry', {}) if target.get('opening') else {}]:
                if item:
                    item['peers'] = [p for p in (peer_info(p) for p in item.get('peers', [])) if p['world_unique']]
    for family, rows in inv['targets'].items():
        inv['targets'][family] = [t for t in rows if t['storey']['name_unique'] and (t['geometry'].get('body_spec') or t['geometry'].get('peers'))]
    inv['properties'] = [t for t in inv['properties'] if t['storey']['name_unique'] and t['geometry']['world_unique']]
    inv['request_profile'] = PROFILE
    return inv


def _world_axes(geometry):
    return '世界X/Y/Z轴分别为' + '、'.join(_xyz(a) for a in geometry['axes_world']) + '。'


def _wall_axes(geometry):
    return '构件自身X/Y/Z轴相对墙自身坐标系的方向分别为' + '、'.join(_xyz(a) for a in geometry['axes_host']) + '。'


def _wall_position(geometry, prefix='放置原点'):
    x, y, z = geometry['origin_host_m']
    return f'{prefix}相对墙自身放置原点，沿墙自身X方向距离{x:.6f}米，Y方向距离{y:.6f}米，Z方向距离{z:.6f}米。'


def _body(spec, mode, deleted):
    if not spec:
        raise ValueError('complete_body_missing')
    if spec.get('method') != 'surviving_instance':
        return describe_body(spec, _xyz)
    peer = spec['peer']
    if peer['guid'] in deleted:
        raise ValueError('shape_reference_deleted')
    if mode == 'world':
        if not peer.get('world_unique'):
            raise ValueError('shape_reference_not_unique_by_coordinates')
        locator = f"模型中仍存在的{peer['ifc_class']}，参考实例世界原点为{_xyz(peer['origin_world_m'])}米，" + _world_axes(peer)
    elif peer.get('name_storey_unique'):
        locator = f"楼层「{peer['storey_name']}」中仍存在的{peer['ifc_class']}「{peer['name']}」。"
    elif peer.get('fill_reference', {}).get('name_storey_unique') and peer['fill_reference']['guid'] not in deleted:
        fill = peer['fill_reference']
        locator = f"楼层「{fill['storey_name']}」中现存{fill['ifc_class']}「{fill['name']}」所填充的洞口。"
    else:
        raise ValueError('shape_reference_not_unique_by_name')
    return '几何形状逐项复制' + locator + '复制其自身局部几何，再按本条指定原点和轴放置。'


def _membership(target, mode):
    if not target['storey'].get('name_unique', False):
        raise ValueError('storey_name_not_unique')
    text = f"归属楼层「{target['storey']['name']}」。"
    host = target.get('host')
    if not host:
        return text
    if mode == 'host_wall':
        if not host.get('name_storey_unique'):
            raise ValueError('wall_name_not_unique_in_storey')
        side = '正' if target['geometry']['origin_host_m'][0] >= 0 else '负'
        return text + f"宿主墙「{host['name']}」，补建或修改位置在该墙自身X轴{side}向一侧。"
    if not host.get('world_unique'):
        raise ValueError('wall_not_unique_by_coordinates')
    locator = host['locator']
    return text + f"宿主墙世界原点为{_xyz(locator['origin_world_m'])}米，" + _world_axes(locator) + f"宿主墙未扣洞口的世界外包范围下角点为{_xyz(locator['bounds_world_m'][0])}米，上角点为{_xyz(locator['bounds_world_m'][1])}米。"


def render_prompts(manifest):
    deleted = {t['guid'] for t in manifest.get('deletions', [])}
    deleted.update(t['opening_guid'] for t in manifest.get('deletions', []) if t.get('opening_guid') and not t.get('preserve_opening', True))
    results = {}
    for mode in ('host_wall', 'world'):
        try:
            rows = ['请按以下要求修复模型。距离和放置坐标单位为米，几何尺寸单位为毫米。' +
                    ('世界坐标采用IFC模型的项目放置坐标系。' if mode == 'world' else '采用各宿主墙已有的自身放置原点及轴方向。')]
            for i, target in enumerate(manifest.get('deletions', []), 1):
                g = target['geometry']
                if mode == 'host_wall' and (not target.get('host') or 'origin_host_m' not in g):
                    raise ValueError('target_without_wall_host')
                row = f"{i}. 补建一{'扇' if target['ifc_class'] in {'IfcDoor', 'IfcWindow'} else '根'}{NAMES[target['ifc_class']]}："
                row += _membership(target, mode)
                row += (f"放置原点的世界坐标为{_xyz(g['origin_world_m'])}米。" + _world_axes(g)) if mode == 'world' else _wall_position(g) + _wall_axes(g)
                row += f"自身坐标的外包范围下角点为{_xyz(np.asarray(g['bounds_local_m'][0]) * 1000)}毫米，上角点为{_xyz(np.asarray(g['bounds_local_m'][1]) * 1000)}毫米。"
                row += _body(g['body_spec'], mode, deleted)
                if target['ifc_class'] in {'IfcDoor', 'IfcWindow'}:
                    og = target['opening']['geometry']
                    row += '洞口规格开始：'
                    row += (f"洞口世界原点为{_xyz(og['origin_world_m'])}米。" + _world_axes(og)) if mode == 'world' else _wall_position(og, '洞口原点') + _wall_axes(og)
                    if target.get('preserve_opening', True):
                        row += '保留现有洞口，将新门窗填入该洞口，建立门窗填充关系。'
                    else:
                        row += _body(og['body_spec'], mode, deleted) + '在上述宿主墙上建立新洞口的void关系，并建立新门窗的门窗填充关系。'
                    row += '洞口规格结束。'
                rows.append(row)
            for i, change in enumerate(manifest.get('property_changes', []), 1):
                g = change['geometry']
                if mode == 'host_wall' and (not change.get('host') or 'origin_host_m' not in g):
                    raise ValueError('property_target_without_wall_host')
                locator = _membership(change, mode)
                locator += (f"放置原点的世界坐标为{_xyz(g['origin_world_m'])}米。" + _world_axes(g)) if mode == 'world' else _wall_position(g) + _wall_axes(g)
                value = '是' if change['before'] is True else '否' if change['before'] is False else json.dumps(change['before'], ensure_ascii=False)
                rows.append(f"属性更改{i}：现有{change['ifc_class']}，" + locator + f"将实例属性「{change['pset_name']}.{change['property_name']}」改为{value}，保留其原属性类型。")
            rows.append('除以上补建、洞口关系及指定实例属性外，其余构件、楼层、尺寸、位置、类型和材料保持原样。')
            results[mode] = '\n'.join(rows) + '\n'
        except (ValueError, KeyError):
            results[mode] = None
    return results
