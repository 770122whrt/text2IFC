"""A submission seam cannot be substituted by the older budget seam."""
import pytest

from scripts.ifc_repair.repair_comparison import formal_admission as m


SCHEMA = 'repair-comparison-d-submission-native-seams/0.1'


def test_submission_seam_still_requires_current_sources(monkeypatch):
    monkeypatch.setattr(m, 'capture_sources', lambda scope: {'source': 'current'})
    with pytest.raises(ValueError, match='REVISION_NATIVE_BINDING_STALE'):
        m.validate_revision_seams({'schema_version': SCHEMA, 'real_models_called': False,
            'source_bindings': {}, 'images': {}},
            current_bindings={'images': {}}, families={'D', 'admission'})


def test_submission_seam_cannot_admit_a_b_or_c_changes():
    with pytest.raises(ValueError, match='REVISION_D_SUBMISSION_SCOPE_REQUIRED'):
        m.validate_revision_seams({'schema_version': SCHEMA, 'real_models_called': False},
            current_bindings={'images': {}}, families={'D', 'B'})


def test_three_distinct_submission_scenarios_are_required():
    rows = [('bare_json', 'submitted'), ('fenced_with_prose', 'submitted'),
            ('duplicate_declarations', 'runtime_error')]
    m.require_d_submission_scenarios(rows)


@pytest.mark.parametrize('rows', [
    [('bare_json', 'submitted'), ('duplicate_declarations', 'runtime_error')],
    [('bare_json', 'submitted'), ('fenced_with_prose', 'no_output'),
     ('duplicate_declarations', 'runtime_error')],
    [('bare_json', 'submitted'), ('fenced_with_prose', 'submitted'),
     ('duplicate_declarations', 'submitted')],
    [('bare_json', 'submitted'), ('fenced_with_prose', 'submitted'),
     ('duplicate_declarations', 'runtime_error'), ('bare_json', 'submitted')],
])
def test_missing_failed_or_repeated_submission_scenario_is_rejected(rows):
    with pytest.raises(ValueError, match='REVISION_D_SUBMISSION_SCENARIOS_REQUIRED'):
        m.require_d_submission_scenarios(rows)
