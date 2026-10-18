"""Experimental request 1.3: one locator and complete surviving shape references."""
from __future__ import annotations

import copy
import itertools
import json
import math
from collections import Counter

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.unit
import numpy as np

from .prompts import NAMES
from .prompts_v2 import prepare_inventory as prepare_v2

PROFILE = 'text2ifc/dataset-request/1.3'
OPERATED_CLASSES = {'IfcDoor', 'IfcWindow', 'IfcBeam', 'IfcColumn'}


def number(value):
    value = round(float(value), 3)
    return '0' if value == 0 else f'{value:.3f}'.rstrip('0').rstrip('.')


def xyz(values):
    return '（' + '，'.join(number(v) for v in values) + '）'


def compass(axis):
    x, y, z = axis
    if abs(z) > math.hypot(x, y):
        return '上' if z > 0 else '下'
    return ('东', '东北', '北', '西北', '西', '西南', '南', '东南')[int(math.floor(math.degrees(math.atan2(y, x)) / 45 + 0.5)) % 8]


def euler(rotation):
    r = np.asarray(rotation)
    pitch = math.asin(float(np.clip(-r[2, 0], -1, 1)))
    if abs(math.cos(pitch)) > 1e-8:
        yaw, roll = math.atan2(r[1, 0], r[0, 0]), math.atan2(r[2, 1], r[2, 2])
    else:
        yaw, roll = math.atan2(-r[0, 1], r[1, 1]), 0.0
    return [math.degrees(v) for v in (yaw, pitch, roll)]


def _mesh_data(entity, *, uncut=False):
    settings = ifcopenshell.geom.settings()
    settings.set('disable-opening-subtractions', uncut)
    shape = ifcopenshell.geom.create_shape(settings, entity)
    return np.asarray(shape.geometry.verts).reshape(-1, 3), np.asarray(shape.geometry.faces).reshape(-1, 3)


def _basic_box(entity, geometry):
    """Require a single rectangular extrusion AND the complete eight-corner mesh."""
    spec = geometry.get('body_spec')
    if not spec or spec.get('method') != 'complete_extrusions' or len(spec['components']) != 1:
        return None
    part = spec['components'][0]
    if part['profile']['kind'] != 'IfcRectangleProfileDef':
        return None
    vertices, faces = _mesh_data(entity)
    low, high = vertices.min(axis=0), vertices.max(axis=0)
    unique = np.unique(np.round(vertices, 8), axis=0)
    corners = np.asarray(list(itertools.product(*zip(low, high))))
    if len(unique) != 8 or len(faces) != 12 or not all(any(np.allclose(c, v, atol=1e-8, rtol=0) for v in unique) for c in corners):
        return None
    area = sum(np.linalg.norm(np.cross(vertices[f[1]] - vertices[f[0]], vertices[f[2]] - vertices[f[0]])) / 2 for f in faces)
    d = high - low
    if not np.all(d > 0) or not np.isclose(area, 2 * (d[0]*d[1] + d[0]*d[2] + d[1]*d[2]), atol=1e-8, rtol=1e-8):
        return None
    return {'method': 'basic_box', 'dimensions_m': d.tolist(), 'negative_face_offset_m': (-low).tolist()}


def prepare_inventory(path, inventory=None):
    """Keep full private bodies; add public selection facts for the new projection."""
    from .engine import _matrix

    inv = prepare_v2(path, inventory)
    inv['properties'] = [p for p in inv['properties'] if p['ifc_class'] in OPERATED_CLASSES]
    model = ifcopenshell.open(str(path))
    unit = ifcopenshell.util.unit.calculate_unit_scale(model)
    frames, meshes, basic, anchors, wall_bounds = {}, {}, {}, {}, {}

    def frame(entity):
        if entity.GlobalId not in frames:
            frames[entity.GlobalId] = _matrix(entity.ObjectPlacement, unit)
        return frames[entity.GlobalId]

    def mesh(entity):
        if entity.GlobalId not in meshes:
            v, f = _mesh_data(entity)
            meshes[entity.GlobalId] = sorted(tuple(sorted(tuple(round(float(x), 6) for x in v[i]) for i in face)) for face in f)
        return meshes[entity.GlobalId]

    def basic_shape(entity, geometry):
        if entity.GlobalId not in basic:
            basic[entity.GlobalId] = _basic_box(entity, geometry)
        return basic[entity.GlobalId]

    indexes = {}
    for cls in ('IfcDoor', 'IfcWindow', 'IfcBeam', 'IfcColumn'):
        entities = model.by_type(cls)
        indexes[cls] = [frame(e)[:3, 3] for e in entities]

    def coordinate_unique(entity):
        cls = entity.is_a()
        if cls not in indexes:
            indexes[cls] = [frame(e)[:3, 3] for e in model.by_type(cls)]
        point = np.round(frame(entity)[:3, 3], 3)
        return bool(sum(np.all(np.abs(p - point) <= 0.000501) for p in indexes[cls]) == 1)

    walls = model.by_type('IfcWall')
    for wall in walls:
        v, _ = _mesh_data(wall, uncut=True)
        wf = frame(wall)
        world = (wf[:3, :3] @ v.T).T + wf[:3, 3]
        wall_bounds[wall.GlobalId] = (np.asarray([v.min(axis=0), v.max(axis=0)]), np.asarray([world.min(axis=0), world.max(axis=0)]))

    from text2ifc_ifc_repair.door_geometry import public_door_installation_anchor
    from text2ifc_ifc_repair.window_geometry import public_window_installation_anchor
    from .geometry_spec import body_spec

    def anchor_usable(entity):
        if entity.GlobalId not in anchors:
            try:
                if entity.is_a('IfcDoor'):
                    public_door_installation_anchor(entity)
                elif entity.is_a('IfcWindow'):
                    public_window_installation_anchor(entity)
                anchors[entity.GlobalId] = True
            except ValueError:
                # Basic bodies can be specified without polygon/representation reuse.
                anchors[entity.GlobalId] = basic_shape(entity, {'body_spec': body_spec(entity, unit)}) is not None
        return anchors[entity.GlobalId]

    for rows in [*inv['targets'].values(), inv['properties']]:
        for target in rows:
            entity = model.by_guid(target['guid'])
            g = target['geometry']
            g['world_unique'] = coordinate_unique(entity)
            g['basic_shape'] = basic_shape(entity, g)
            if target.get('host'):
                host = target['host']
                lowhigh, world = wall_bounds[host['guid']]
                host['locator']['bounds_local_m'] = lowhigh.tolist()
                host['locator']['bounds_world_m'] = world.tolist()
                rounded = np.round(world, 3)
                host['world_unique'] = bool(sum(np.all(np.abs(b[1] - rounded) <= 0.000501) for b in wall_bounds.values()) == 1)
            opening = target.get('opening')
            if opening:
                oe = model.by_guid(opening['guid'])
                opening['geometry']['basic_shape'] = basic_shape(oe, opening['geometry'])
                relative = np.linalg.inv(frame(entity)) @ frame(oe)
            enriched = []
            for peer in g.get('peers', []):
                pe = model.by_guid(peer['guid'])
                peer = {**peer, 'world_unique': coordinate_unique(pe), 'harness_reference_usable': anchor_usable(pe)}
                peer['opening_matches'] = False
                if opening and len(getattr(pe, 'FillsVoids', ())) == 1:
                    po = pe.FillsVoids[0].RelatingOpeningElement
                    peer['opening_guid_private'] = po.GlobalId
                    peer['opening_matches'] = bool(mesh(oe) == mesh(po) and np.allclose(relative, np.linalg.inv(frame(pe)) @ frame(po), atol=1e-8, rtol=0))
                if peer['world_unique']:
                    enriched.append(peer)
            g['peers'] = enriched
    inv['request_profile'] = PROFILE
    return inv


def prepare_recipe(recipe):
    """Admit only a surviving complete reference or a proven basic rectangular body."""
    result = copy.deepcopy(recipe)
    if any(t['ifc_class'] not in OPERATED_CLASSES for t in [*result['deletions'], *result.get('property_changes', [])]):
        raise ValueError('DAMAGE_SCOPE_RESTRICTED_TO_DOOR_WINDOW_BEAM_COLUMN')
    deleted = {t['guid'] for t in result['deletions']}
    deleted.update(t['opening_guid'] for t in result['deletions'] if t.get('opening_guid') and not t.get('preserve_opening', True))
    for target in result['deletions']:
        g = target['geometry']
        needs_opening = bool(target.get('opening') and not target.get('preserve_opening', True))
        candidates = [p for p in g.get('peers', []) if p['guid'] not in deleted and p.get('opening_guid_private') not in deleted and p.get('harness_reference_usable') and p.get('world_unique') and (not needs_opening or p.get('opening_matches') or target['opening']['geometry'].get('basic_shape'))]
        candidates.sort(key=lambda p: (needs_opening and not p.get('opening_matches'), not p.get('name_storey_unique'), float(np.linalg.norm(np.asarray(p['axes_world']) - np.asarray(g['axes_world']))), p['guid']))
        if candidates:
            g['request_shape'] = {'method': 'surviving_instance', 'peer': candidates[0]}
        elif g.get('basic_shape'):
            g['request_shape'] = copy.deepcopy(g['basic_shape'])
        else:
            raise ValueError('NO_SUPPORTED_SHAPE_REFERENCE_OR_BASIC_BOX:' + target['ifc_class'])
        if needs_opening:
            peer = g['request_shape'].get('peer')
            if peer and peer.get('opening_matches'):
                target['opening']['geometry']['request_shape'] = {'method': 'paired_reference', 'peer': peer}
            elif target['opening']['geometry'].get('basic_shape'):
                target['opening']['geometry']['request_shape'] = copy.deepcopy(target['opening']['geometry']['basic_shape'])
            else:
                raise ValueError('NO_SUPPORTED_OPENING_REFERENCE_OR_BASIC_BOX')
    return result


def _membership(target, mode):
    if not target['storey'].get('name_unique'):
        raise ValueError('STOREY_NAME_AMBIGUOUS')
    text = f"归属楼层「{target['storey']['name']}」。"
    host = target.get('host')
    if not host:
        return text
    locator = host['locator']
    if mode == 'host_wall':
        if not host.get('name_storey_unique'):
            raise ValueError('WALL_NAME_AMBIGUOUS')
        axes = locator['axes_world']
        return text + f"宿主墙「{host['name']}」，长度正向大致朝{compass(axes[0])}，厚度正向大致朝{compass(axes[1])}。"
    if not host.get('world_unique'):
        raise ValueError('WALL_BOUNDS_AMBIGUOUS')
    bounds = locator['bounds_world_m']
    return text + f'宿主墙未扣洞口的整体范围为{xyz(bounds[0])}至{xyz(bounds[1])}米。'


def _position(g, target, mode, prefix='放置基点'):
    if mode == 'world':
        return f"{prefix}世界坐标为{xyz(g['origin_world_m'])}米。"
    if not target.get('host') or 'origin_host_m' not in g:
        raise ValueError('NO_WALL_HOST')
    distances = (np.asarray(g['origin_host_m']) - np.asarray(target['host']['locator']['bounds_local_m'][0])) * 1000
    return f'{prefix}距墙长度起端{number(distances[0])}毫米，距墙厚度负向侧{number(distances[1])}毫米，高出墙底{number(distances[2])}毫米。'


def _rotation(g, mode, peer=None, prefix='朝向'):
    r = np.asarray(g['axes_world']).T
    if peer:
        relative = np.asarray(peer['axes_world']) @ r
        if np.allclose(relative, np.eye(3), atol=1e-8, rtol=0):
            return '朝向与参照相同。'
        basis = '参照'
    else:
        relative = np.asarray(g['axes_host']) .T if mode == 'host_wall' else r
        basis = '宿主墙' if mode == 'host_wall' else '项目坐标系'
    yaw, pitch, roll = euler(relative)
    return f'{prefix}相对{basis}，按自身高、厚、宽轴依次旋转{number(yaw)}度、{number(pitch)}度、{number(roll)}度。' if peer else f'{prefix}相对{basis}，按高、厚、宽轴依次旋转{number(yaw)}度、{number(pitch)}度、{number(roll)}度。'


def _box(spec, prefix='形状'):
    return f"{prefix}为单一长方体，沿自身三个轴方向的尺寸为{xyz(np.asarray(spec['dimensions_m']) * 1000)}毫米；基点距对应负向面的距离为{xyz(np.asarray(spec['negative_face_offset_m']) * 1000)}毫米。"


def _shape(target, mode):
    g = target['geometry']
    spec = g['request_shape']
    if spec['method'] == 'basic_box':
        return _box(spec) + _rotation(g, mode)
    peer = spec['peer']
    if mode == 'host_wall':
        if not peer.get('name_storey_unique'):
            raise ValueError('REFERENCE_NAME_AMBIGUOUS')
        locator = f"楼层「{peer['storey_name']}」的现存{peer['ifc_class']}「{peer['name']}」。"
    else:
        locator = f"现存{peer['ifc_class']}世界基点{xyz(peer['origin_world_m'])}米。"
    return '完整形状复制参照：' + locator + _rotation(g, mode, peer)


def _opening(target, mode):
    og = target['opening']['geometry']
    if target.get('preserve_opening', True):
        if mode == 'world':
            point = f"世界基点{xyz(og['origin_world_m'])}米"
        else:
            point = _position(og, target, mode, prefix='')[0:-1]
        return '保留现有洞口：' + point + '；将新构件填入并建立门窗填充关系。'
    spec = og['request_shape']
    if spec['method'] == 'paired_reference':
        return '洞口复制参照构件所填洞口，保持与新构件相同的相对位置和朝向；在宿主墙上建立洞口并建立门窗填充关系。'
    return '洞口规格：' + _position(og, target, mode, prefix='洞口放置基点') + _box(spec, prefix='洞口形状') + _rotation(og, mode, prefix='洞口朝向') + '在宿主墙上建立洞口并建立门窗填充关系。'


def render_prompts(manifest):
    results = {}
    for mode in ('host_wall', 'world'):
        try:
            header = '请按以下要求修复模型。世界坐标用米，尺寸和相对距离用毫米；公开数值最多三位小数。' if mode == 'world' else '请按以下要求修复模型。尺寸和相对距离用毫米；公开数值最多三位小数。'
            rows = [header]
            for i, target in enumerate(manifest.get('deletions', []), 1):
                g = target['geometry']
                row = f"{i}. 补建一{'扇' if target['ifc_class'] in {'IfcDoor', 'IfcWindow'} else '根'}{NAMES[target['ifc_class']]}："
                row += _membership(target, mode) + _position(g, target, mode) + _shape(target, mode)
                if target.get('opening'):
                    row += _opening(target, mode)
                rows.append(row)
            for i, change in enumerate(manifest.get('property_changes', []), 1):
                value = change['before']
                value = '是' if value is True else '否' if value is False else number(value) if isinstance(value, float) else json.dumps(value, ensure_ascii=False)
                rows.append(f"属性更改{i}：现有{change['ifc_class']}，" + _membership(change, mode) + _position(change['geometry'], change, mode) + f"将实例属性「{change['pset_name']}.{change['property_name']}」改为{value}，保留其原属性类型。")
            rows.append('除以上补建、洞口关系及指定实例属性外，其余构件、楼层、尺寸、位置、类型和材料保持原样。')
            results[mode] = '\n'.join(rows) + '\n'
        except (ValueError, KeyError):
            results[mode] = None
    return results
