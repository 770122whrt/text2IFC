"""Request profile 1.4: explicit public coordinate/rotation conventions.

The sealed 1.3 request body is unchanged. This upgrade receives public text
only; it cannot read a pristine IFC, mutation recipe, identity map or Gold.
It adds no object-specific facts, dimensions, identities or target coordinates.
"""
from __future__ import annotations

PROFILE = 'text2ifc/dataset-request/1.4'
SOURCE_PROFILE = 'text2ifc/dataset-request/1.3'
HEADER = '请按以下要求修复模型。世界坐标用米，尺寸和相对距离用毫米；公开数值最多三位小数。'
HOST_HEADER = '请按以下要求修复模型。尺寸和相对距离用毫米；公开数值最多三位小数。'
PREFIX = (
    '坐标与旋转约定：放置基点指构件 ObjectPlacement 的原点；复制完整形状时保留 Body 与 MappedItem 内部的变换和偏移。\n'
    '世界坐标指沿公开 IFC 的 ObjectPlacement 层级变换得到的项目放置坐标，按模型 LengthUnit 换算为米，沿用模型原点与轴方向，无需地理或地图转换。\n'
    '构件自身宽轴、厚轴、高轴分别指其放置坐标系的局部 X、Y、Z 轴，轴名由放置坐标系确定。\n'
    '旋转采用主动右手旋转，依请求所列顺序逐次绕当前构件自身轴执行；“高、厚、宽”顺序即当前 Z、Y、X 轴，先前旋转会改变后续轴的方向。'
    '复制参照时以参照的放置轴为初始轴；无参照时以请求指定的项目或宿主墙坐标轴为初始轴。\n\n'
)


def _body(text):
    if not isinstance(text, str) or not text.startswith((HEADER, HOST_HEADER)) or PREFIX in text:
        raise ValueError('SOURCE_REQUEST_13_BODY_REQUIRED')
    return text


def upgrade_request(original_text: str) -> str:
    """Deterministically add the public conventions to a supported 1.3 body."""
    return PREFIX + _body(original_text)


def validate_request(upgraded_text: str, original_text: str) -> bool:
    """Reject missing conventions, private/body additions and double upgrades."""
    expected = upgrade_request(original_text)
    if not isinstance(upgraded_text, str) or upgraded_text != expected:
        raise ValueError('REQUEST_14_PREFIX_OR_BOUND_SOURCE_BODY_MISMATCH')
    return True
