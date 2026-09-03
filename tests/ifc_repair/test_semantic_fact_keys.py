from text2ifc_ifc_repair.semantic_facts import semantic_fact_key_token


def test_non_ascii_semantic_fact_names_remain_distinct_and_stable() -> None:
    glass = semantic_fact_key_token("玻璃")
    sash = semantic_fact_key_token("窗扇")

    assert glass != sash
    assert glass.startswith("u-")
    assert sash.startswith("u-")
    assert semantic_fact_key_token("玻璃") == glass
    assert semantic_fact_key_token("Aluminium frame") == "Aluminium-frame"

