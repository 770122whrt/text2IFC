import json
import math
from typing import Any


def _non_finite_number(value: str) -> ValueError:
    return ValueError(
        f"JSON number {value!r} is not representable as a finite value."
    )


def _parse_float(value: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise _non_finite_number(value)
    return result


def _parse_int(value: str) -> int:
    result = int(value)
    try:
        finite = math.isfinite(result)
    except OverflowError:
        finite = False
    if not finite:
        raise _non_finite_number(value)
    return result


def _reject_constant(value: str) -> None:
    raise _non_finite_number(value)


def loads_strict_json(text: str) -> Any:
    return json.loads(
        text,
        parse_float=_parse_float,
        parse_int=_parse_int,
        parse_constant=_reject_constant,
    )

