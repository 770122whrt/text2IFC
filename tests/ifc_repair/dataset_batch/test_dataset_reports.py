"""Report invariants use metadata fixtures; they are not IFC/native evidence."""
import copy

import pytest

from scripts.ifc_repair.dataset_reports import validate_counts


def fixture():
    rows = [{"source_id": f"formal-{n:03d}", "active": n != 28,
             "total_pairs": 30 if n != 28 else 0,
             "distinct_damages": 30 if n != 28 else 0,
             "cap": 30, "missing_pairs": 0, "failed_attempts": 0}
            for n in range(1, 42)]
    return {"schema_version": "text2ifc/dataset-offline-delivery/1.1", "status": "complete",
            "pairs": 1200, "distinct_damages": 1200, "active_source_models": 40,
            "historical_source_models": 41, "source_models": 40,
            "target_pairs": 1200, "pairs_per_ifc": 30, "missing_pairs": 0,
            "quota_complete": True, "per_mother": rows,
            "rounds": [{"pairs": 1200, "distinct_damages": 1200,
                        "attempted_cases": 1200, "failed_attempts": 0}],
            "attempted_cases": 1200, "failed_attempts": 0,
            "damage_families": {"attributes": 1200}, "locator_modes": {"world": 1200},
            "pair_task_kinds": {"property": 1200}, "budget_levels": {"S1": 1200}}


def test_report_rejects_a_different_total_instead_of_claiming_completion():
    data = fixture()
    data["pairs"] = 1199
    with pytest.raises(ValueError, match="REPORT_COUNT_MISMATCH"):
        validate_counts(data)


def test_report_rejects_an_extra_active_source_or_excess_quota():
    data = fixture()
    data["per_mother"][27]["active"] = True
    with pytest.raises(ValueError, match="REPORT_COUNT_MISMATCH"):
        validate_counts(data)
    data = fixture()
    data["per_mother"][0]["total_pairs"] = 31
    with pytest.raises(ValueError, match="REPORT_COUNT_MISMATCH"):
        validate_counts(data)


def test_valid_counts_are_read_only_and_partial_delivery_is_distinguished():
    data = fixture()
    original = copy.deepcopy(data)
    assert validate_counts(data) is True
    assert data == original
    data["per_mother"][0].update(total_pairs=29, distinct_damages=29, missing_pairs=1)
    data.update(pairs=1199, distinct_damages=1199, missing_pairs=1,
                quota_complete=False, attempted_cases=1199)
    data["rounds"][0].update(pairs=1199, distinct_damages=1199, attempted_cases=1199)
    for key in ("damage_families", "locator_modes", "pair_task_kinds", "budget_levels"):
        data[key][next(iter(data[key]))] = 1199
    assert validate_counts(data) is True


@pytest.mark.parametrize('schema', ['text2ifc/dataset-offline-delivery/1.2',
                                  'text2ifc/dataset-offline-delivery/1.3'])
def test_four_round_delivery_requires_the_property_tail_in_the_totals(schema):
    data = fixture()
    data['schema_version'] = schema
    data['rounds'] = [
        {'pairs': count, 'distinct_damages': count,
         'attempted_cases': count, 'failed_attempts': 0}
        for count in (911, 64, 223, 2)
    ]
    assert validate_counts(data) is True
    data['rounds'].pop()
    with pytest.raises(ValueError, match='REPORT_COUNT_MISMATCH'):
        validate_counts(data)
