"""Offline registry API skeleton for the RED phase."""

from __future__ import annotations


class RegistryDriftError(ValueError):
    pass


class IfcKnowledgeRegistry:
    def entity(self, name):
        return None

    def property_set(self, name):
        return None


def load_ifc2x3_registry(project_root=None):
    return IfcKnowledgeRegistry()


def check_registry_files(project_root=None):
    raise NotImplementedError("registry drift checking is not implemented")
