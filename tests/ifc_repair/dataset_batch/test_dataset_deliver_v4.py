"""Seed-rule control fixtures only; these tests do not validate IFC or native geometry."""
import importlib
from pathlib import Path

import pytest

from scripts.ifc_repair import dataset_deliver as old
from scripts.ifc_repair import dataset_pairs as q


def api():
    return importlib.import_module('scripts.ifc_repair.dataset_deliver_v4')


def test_seed_offsets_follow_catalogue_order_not_id_or_eligible_order():
    specs=[{'source_id':'formal-032'},{'source_id':'formal-003'},{'source_id':'formal-014'}]
    assert api().catalogue_seeds(specs,20261010)=={
        'formal-032':20261010,'formal-003':20261011,'formal-014':20261012}


@pytest.mark.parametrize('specs,seed',[([{'source_id':'formal-001'}],True),
    ([{'source_id':'formal-001'},{'source_id':'formal-001'}],10)])
def test_invalid_seed_or_duplicate_catalogue_fails_closed(specs,seed):
    with pytest.raises(ValueError):
        api().catalogue_seeds(specs,seed)


def test_full_checkpoint_config_is_still_checked_and_adapter_restored(monkeypatch,tmp_path):
    module=api();production=tmp_path/'private/production'
    specs=[{'source_id':'formal-032'},{'source_id':'formal-003'}]
    q.write_json(production/'build.json',{'seed':17})
    q.write_json(production/'mother-sources.json',{'sources':specs})
    config={'seed':17,'max_attempts':30,'pairs_per_ifc':25,'profile':'unchanged','code_sha256':{'old':'bound'}}
    observed={**config,'seed':18}
    def strict_mother(root,spec,row,expected,bindings,**kwargs):
        assert spec==specs[1]
        if expected!=observed:
            raise ValueError('CHECKPOINT_CONFIGURATION_CHANGED')
        return expected
    monkeypatch.setattr(old,'_mother',strict_mother)
    with module.corrected_seeds(tmp_path):
        assert old._mother(production,specs[1],{},config,{})==observed
        assert old._mother(tmp_path/'private/supplement-r1',specs[1],{},config,{},supplement=True)==observed
        with pytest.raises(ValueError,match='CHECKPOINT_CONFIGURATION_CHANGED'):
            old._mother(production,specs[1],{},{**config,'max_attempts':29},{})
    assert old._mother is strict_mother
    assert config['seed']==17


def test_frozen_dispatch_rule_and_new_program_binding_are_explicit():
    module=api();module.check_dispatch_rule()
    programs=module.tail_program_bindings()
    assert programs['scripts/ifc_repair/dataset_deliver_v4.py']==q.sha256(Path(module.__file__))
    assert 'scripts/ifc_repair/dataset_property_tail.py' in programs
    assert module.SCHEMA=='text2ifc/dataset-offline-delivery/1.3'


def test_adapter_restores_tail_functions_and_schema_even_on_failure(tmp_path):
    module=api();production=tmp_path/'private/production'
    q.write_json(production/'build.json',{'seed':17})
    q.write_json(production/'mother-sources.json',{'sources':[{'source_id':'formal-003'}]})
    original=(module.tail.program_bindings,module.tail.execution_environment,module.previous.SCHEMA)
    with pytest.raises(RuntimeError,match='controlled failure'):
        with module.delivery_adapter(tmp_path):
            assert module.tail.program_bindings is module.tail_program_bindings
            assert module.previous.SCHEMA==module.SCHEMA
            raise RuntimeError('controlled failure')
    assert (module.tail.program_bindings,module.tail.execution_environment,module.previous.SCHEMA)==original
