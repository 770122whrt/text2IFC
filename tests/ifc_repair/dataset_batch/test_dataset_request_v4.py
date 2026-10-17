"""Public-only coordinate glossary: identity-free and independent of Gold."""
import pytest

from scripts.ifc_repair.dataset_request_v4 import PROFILE, PREFIX, upgrade_request, validate_request


BODY = '请按以下要求修复模型。世界坐标用米，尺寸和相对距离用毫米；公开数值最多三位小数。\n1. 补建一根梁：朝向相对参照，按自身高、厚、宽轴依次旋转0度、0度、180度。\n'
HOST_BODY = '请按以下要求修复模型。尺寸和相对距离用毫米；公开数值最多三位小数。\n属性更改1：归属楼层「Level A」。宿主墙「Host wall」，朝东。\n'


def test_host_wall_request_has_the_same_explicit_axis_convention():
    upgraded = upgrade_request(HOST_BODY)
    assert upgraded == PREFIX + HOST_BODY
    assert validate_request(upgraded, HOST_BODY)


def test_upgrade_adds_only_explicit_shared_coordinate_conventions():
    upgraded = upgrade_request(BODY)
    assert PROFILE == 'text2ifc/dataset-request/1.4'
    assert upgraded == PREFIX + BODY
    assert '宽轴、厚轴、高轴分别指' in PREFIX and 'X、Y、Z' in PREFIX
    assert '当前构件自身轴' in PREFIX and '右手' in PREFIX
    assert 'ObjectPlacement' in PREFIX and 'Body' in PREFIX and 'MappedItem' in PREFIX
    assert 'LengthUnit' in PREFIX and '项目放置坐标' in PREFIX
    assert validate_request(upgraded, BODY) is True


@pytest.mark.parametrize('bad', [BODY, '宽、高、厚按长度排序。\n' + BODY,
    PREFIX + BODY.replace('180度', '90度'), PREFIX + PREFIX + BODY])
def test_missing_ambiguous_or_changed_body_is_rejected(bad):
    with pytest.raises(ValueError, match='REQUEST_14'):
        validate_request(bad, BODY)


@pytest.mark.parametrize('bad', ['', 'ordinary prompt', PREFIX + BODY, None])
def test_non_v3_body_or_repeated_upgrade_is_rejected(bad):
    with pytest.raises(ValueError, match='SOURCE_REQUEST'):
        upgrade_request(bad)
