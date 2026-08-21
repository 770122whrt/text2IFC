"""Extensible local repair workflow for authoritative IFC2X3 models."""

from text2ifc_knowledge.property_search import _prepare_windows_torch_runtime


# The public RepairAPI imports IfcOpenShell before the property vector model.
# On Windows, load the OS MSVC runtime first so IfcOpenShell cannot pin the
# older Anaconda copy that prevents Torch's c10.dll from initializing.
_prepare_windows_torch_runtime()
