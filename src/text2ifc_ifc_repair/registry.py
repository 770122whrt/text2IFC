"""Heterogeneous operation capability registry for IFC repair orchestration."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Iterable, Mapping

from jsonschema import Draft202012Validator

from text2ifc_contract.validation import ValidationIssue

if TYPE_CHECKING:
    from .evaluation_models import CheckResult
    from .evaluation_policy import OperationEvaluationPolicy
    from .semantic_facts import SemanticFact


OperationCallable = Callable[..., Any]
CAPABILITY_NAMES = (
    "context_adapter",
    "precondition_checker",
    "applicator",
    "postcondition_checker",
    "comparison_adapter",
)


class OperationRegistryError(ValueError):
    """Stable machine-readable registry failure."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


@dataclass(frozen=True)
class OperationDefinition:
    operation_type: str
    target_ifc_classes: tuple[str, ...]
    parameter_schema: Mapping[str, Any]
    context_adapter: OperationCallable
    precondition_checker: OperationCallable
    applicator: OperationCallable
    postcondition_checker: OperationCallable
    comparison_adapter: OperationCallable
    capability_constraints: Mapping[str, Any]
    prototype_ifc_classes: tuple[str, ...] = ()
    prototype_dimension_paths: Mapping[str, tuple[str, ...]] = field(
        default_factory=dict
    )
    target_schema: Mapping[str, Any] | None = None
    precondition_names: tuple[str, ...] = ()
    postcondition_names: tuple[str, ...] = ()
    evaluation_policy: OperationEvaluationPolicy | None = None
    semantic_manifest_builder: OperationCallable | None = None
    semantic_policy_fact_builder: OperationCallable | None = None

    def __post_init__(self) -> None:
        if not self.operation_type or not self.target_ifc_classes:
            raise OperationRegistryError(
                "INVALID_OPERATION_DEFINITION", self.operation_type or "<empty>"
            )
        if any(not value for value in self.prototype_ifc_classes):
            raise OperationRegistryError(
                "INVALID_PROTOTYPE_IFC_CLASS", self.operation_type
            )
        if any(not key or not path for key, path in self.prototype_dimension_paths.items()):
            raise OperationRegistryError(
                "INVALID_PROTOTYPE_DIMENSION_PATH", self.operation_type
            )
        Draft202012Validator.check_schema(dict(self.parameter_schema))
        if self.target_schema is not None:
            Draft202012Validator.check_schema(dict(self.target_schema))
        for capability_name in CAPABILITY_NAMES:
            if not callable(getattr(self, capability_name)):
                raise OperationRegistryError(
                    "INVALID_OPERATION_CAPABILITY",
                    f"{self.operation_type}.{capability_name}",
                )
        if self.semantic_manifest_builder is not None and not callable(
            self.semantic_manifest_builder
        ):
            raise OperationRegistryError(
                "INVALID_SEMANTIC_MANIFEST_BUILDER", self.operation_type
            )
        if self.semantic_policy_fact_builder is not None and not callable(
            self.semantic_policy_fact_builder
        ):
            raise OperationRegistryError(
                "INVALID_SEMANTIC_POLICY_FACT_BUILDER", self.operation_type
            )


class OperationRegistry:
    """Registry used by common context, audit, apply and compare dispatchers."""

    def __init__(self) -> None:
        self._definitions: dict[str, OperationDefinition] = {}

    @property
    def operation_types(self) -> tuple[str, ...]:
        return tuple(sorted(self._definitions))

    def register(self, definition: OperationDefinition) -> None:
        if definition.operation_type in self._definitions:
            raise OperationRegistryError(
                "DUPLICATE_OPERATION_TYPE", definition.operation_type
            )
        policy = definition.evaluation_policy
        if policy is not None:
            if policy.operation_type != definition.operation_type:
                raise OperationRegistryError(
                    "EVALUATION_POLICY_OPERATION_MISMATCH",
                    f"{policy.operation_type}:{definition.operation_type}",
                )
            if any(
                registered.evaluation_policy is not None
                and registered.evaluation_policy.policy_id == policy.policy_id
                for registered in self._definitions.values()
            ):
                raise OperationRegistryError(
                    "DUPLICATE_EVALUATION_POLICY_ID", policy.policy_id
                )
        self._definitions[definition.operation_type] = definition

    def require(self, operation_type: str) -> OperationDefinition:
        try:
            return self._definitions[operation_type]
        except KeyError as error:
            raise OperationRegistryError(
                "UNKNOWN_OPERATION_TYPE", operation_type
            ) from error

    def require_evaluation_policy(
        self, operation_type: str
    ) -> OperationEvaluationPolicy:
        definition = self.require(operation_type)
        if definition.evaluation_policy is None:
            raise OperationRegistryError(
                "MISSING_EVALUATION_POLICY", operation_type
            )
        return definition.evaluation_policy

    def evaluate_semantics(
        self,
        operation_type: str,
        *,
        expected_facts: Iterable[SemanticFact],
        repaired_facts: Iterable[SemanticFact],
    ) -> tuple[CheckResult, ...]:
        from .semantic_facts import evaluate_operation_semantics

        return evaluate_operation_semantics(
            self.require_evaluation_policy(operation_type),
            expected_facts=expected_facts,
            repaired_facts=repaired_facts,
        )

    def build_semantic_manifest(self, operation_type: str, **kwargs: Any) -> Any:
        definition = self.require(operation_type)
        builder = definition.semantic_manifest_builder
        if builder is None:
            from .semantic_authoring import build_semantic_manifest

            builder = build_semantic_manifest
        return builder(registry=self, **kwargs)

    def build_semantic_policy_facts(
        self, operation_type: str, *, operation: Mapping[str, Any]
    ) -> tuple[Any, ...]:
        builder = self.require(operation_type).semantic_policy_fact_builder
        if builder is None:
            return ()
        return tuple(builder(operation=operation))

    def validate_parameters(
        self,
        operation: Mapping[str, Any],
    ) -> list[ValidationIssue]:
        definition = self.require(str(operation.get("operation_type", "")))
        return _schema_issues(
            value=operation.get("parameters"),
            schema=definition.parameter_schema,
            code="OPERATION_PARAMETER_SCHEMA_ERROR",
            path_prefix="/parameters",
        )

    def prepare_partial_parameters(
        self,
        operation: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Copy partial parameters and add only schema-declared constants.

        Constants such as the Window operation's local-coordinate convention
        are deterministic compiler policy, not project facts authored by the
        Provider.
        """

        definition = self.require(str(operation.get("operation_type", "")))
        raw = operation.get("parameters")
        value = copy.deepcopy(raw if isinstance(raw, Mapping) else {})
        _inject_schema_constants(value, definition.parameter_schema)
        return value

    def validate_partial_parameters(
        self,
        operation: Mapping[str, Any],
    ) -> list[ValidationIssue]:
        """Validate supplied values without treating absent required facts as errors."""

        definition = self.require(str(operation.get("operation_type", "")))
        return _schema_issues(
            value=operation.get("parameters"),
            schema=_without_required(definition.parameter_schema),
            code="OPERATION_PARAMETER_SCHEMA_ERROR",
            path_prefix="/parameters",
        )

    def missing_required_parameters(
        self,
        operation: Mapping[str, Any],
    ) -> tuple[str, ...]:
        """Return stable JSON pointers for executable facts still absent."""

        definition = self.require(str(operation.get("operation_type", "")))
        parameters = operation.get("parameters")
        value = parameters if isinstance(parameters, Mapping) else {}
        return tuple(sorted(_missing_required(value, definition.parameter_schema)))

    def validate_target(
        self,
        operation: Mapping[str, Any],
    ) -> list[ValidationIssue]:
        definition = self.require(str(operation.get("operation_type", "")))
        if definition.target_schema is None:
            return []
        return _schema_issues(
            value=operation.get("target"),
            schema=definition.target_schema,
            code="OPERATION_TARGET_SCHEMA_ERROR",
            path_prefix="/target",
        )

    def dispatch(
        self,
        capability_name: str,
        operation: Mapping[str, Any],
        **kwargs: Any,
    ) -> Any:
        if capability_name not in CAPABILITY_NAMES:
            raise OperationRegistryError(
                "UNKNOWN_OPERATION_CAPABILITY", capability_name
            )
        definition = self.require(str(operation.get("operation_type", "")))
        capability = getattr(definition, capability_name)
        return capability(operation=operation, **kwargs)


def _schema_issues(
    *,
    value: Any,
    schema: Mapping[str, Any],
    code: str,
    path_prefix: str,
) -> list[ValidationIssue]:
    validator = Draft202012Validator(dict(schema))
    issues = [
        ValidationIssue(
            code=code,
            path=_pointer(error.absolute_path, prefix=path_prefix),
            message=error.message,
        )
        for error in validator.iter_errors(value)
    ]
    return sorted(set(issues), key=lambda issue: (issue.path, issue.message))


def _without_required(schema: Mapping[str, Any]) -> dict[str, Any]:
    relaxed: dict[str, Any] = {}
    for key, value in schema.items():
        if key == "required":
            continue
        if isinstance(value, Mapping):
            relaxed[key] = _without_required(value)
        elif isinstance(value, list):
            relaxed[key] = [
                _without_required(item) if isinstance(item, Mapping) else copy.deepcopy(item)
                for item in value
            ]
        else:
            relaxed[key] = copy.deepcopy(value)
    return relaxed


def _inject_schema_constants(value: dict[str, Any], schema: Mapping[str, Any]) -> None:
    properties = schema.get("properties")
    if not isinstance(properties, Mapping):
        return
    for name, raw_child in properties.items():
        if not isinstance(raw_child, Mapping):
            continue
        child = dict(raw_child)
        if name not in value and "const" in child:
            value[str(name)] = copy.deepcopy(child["const"])
            continue
        if child.get("type") != "object":
            continue
        existing = value.get(name)
        nested: dict[str, Any]
        if isinstance(existing, Mapping):
            nested = copy.deepcopy(dict(existing))
        elif existing is None:
            nested = {}
        else:
            continue
        _inject_schema_constants(nested, child)
        if nested:
            value[str(name)] = nested


def _missing_required(
    value: Mapping[str, Any],
    schema: Mapping[str, Any],
    prefix: str = "",
) -> list[str]:
    required = schema.get("required", ())
    properties = schema.get("properties", {})
    if not isinstance(required, (list, tuple)) or not isinstance(properties, Mapping):
        return []
    missing: list[str] = []
    for raw_name in required:
        name = str(raw_name)
        child = properties.get(name, {})
        child_schema = child if isinstance(child, Mapping) else {}
        path = f"{prefix}/{name}"
        present = name in value
        if not present:
            nested = _missing_required({}, child_schema, path)
            missing.extend(nested or [path])
            continue
        child_value = value[name]
        if isinstance(child_value, Mapping):
            missing.extend(_missing_required(child_value, child_schema, path))
    return missing


def _pointer(parts: Any, *, prefix: str) -> str:
    tokens = [str(part).replace("~", "~0").replace("/", "~1") for part in parts]
    return prefix + ("/" + "/".join(tokens) if tokens else "")
