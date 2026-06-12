"""Independent represented-plus-reported accounting."""

from __future__ import annotations


def category(source: int, represented: int) -> dict[str, int]:
    return {
        "source": source,
        "represented": represented,
        "reported": source - represented,
    }


def verify_inventory(inventory: dict[str, dict[str, int]]) -> None:
    for name, record in inventory.items():
        if record["source"] != record["represented"] + record["reported"]:
            raise ValueError(f"unbalanced extraction inventory: {name}")
        if min(record.values()) < 0:
            raise ValueError(f"negative extraction inventory: {name}")
