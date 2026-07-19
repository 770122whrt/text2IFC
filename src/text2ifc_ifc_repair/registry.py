"""Heterogeneous operation capability registry for IFC repair orchestration."""

from __future__ import annotations

from dataclasses import dataclass
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
    target_schema: Mapping[str, Any] | None = None
    precondition_names: tuple[str, ...] = ()
    postcondition_names: tuple[str, ...] = ()
    evaluation_policy: OperationEvaluationPolicy | None = None

    def __post_init__(self) -> None:
        if not self.operation_type or not self.target_ifc_classes:
            raise OperationRegistryError(
                "INVALID_OPERATION_DEFINITION", self.operation_type or "<empty>"
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


def _pointer(parts: Any, *, prefix: str) -> str:
    tokens = [str(part).replace("~", "~0").replace("/", "~1") for part in parts]
    return prefix + ("/" + "/".join(tokens) if tokens else "")
