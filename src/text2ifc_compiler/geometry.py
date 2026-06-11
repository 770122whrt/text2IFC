from typing import Any, Mapping


def add_element_geometry(
    ifc_file: Any,
    element: Any,
    element_data: Mapping[str, Any],
    body_context: Any,
    source_index: int,
) -> None:
    del ifc_file, element, element_data, body_context, source_index

