"""The host and worker must use the frozen bundle's method, not today's guess."""
import pytest

from scripts.ifc_repair.repair_comparison.isolated_b import _bundle_scene_version


def write_version(tmp_path, source):
    file = tmp_path / 'src/text2ifc_ifc_repair/scene_grounding.py'
    file.parent.mkdir(parents=True)
    file.write_text(source, encoding='utf-8')


@pytest.mark.parametrize('version', ['0.2', '0.3'])
def test_read_frozen_literal_does_not_import_or_run_bundle(tmp_path, version):
    write_version(tmp_path, f"SCENE_GROUNDING_VERSION = 'text2ifc/ifc-scene-grounding/{version}'\n"
                           "raise RuntimeError('must not execute source')\n")
    assert _bundle_scene_version(tmp_path) == f'text2ifc/ifc-scene-grounding/{version}'


@pytest.mark.parametrize('source', ["", "SCENE_GROUNDING_VERSION = input()",
    "SCENE_GROUNDING_VERSION = 'invalid'", "SCENE_GROUNDING_VERSION = 'text2ifc/ifc-scene-grounding/0.3'\n"*2])
def test_missing_dynamic_or_ambiguous_version_is_rejected(tmp_path, source):
    write_version(tmp_path, source)
    with pytest.raises(ValueError, match='BUNDLE_SCENE_VERSION_INVALID'):
        _bundle_scene_version(tmp_path)
