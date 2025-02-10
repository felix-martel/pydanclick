"""Convert Pydantic types to Click types."""

import datetime
import re
import sys
from pathlib import Path
from typing import Any, Literal, Optional, TypedDict, Union, cast, get_args, get_origin
from uuid import UUID

import click
from annotated_types import Ge, Gt, Le, Lt, SupportsGe, SupportsGt, SupportsLe, SupportsLt
from pydantic import TypeAdapter, ValidationError
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

NoneType = type(None)

if sys.version_info >= (3, 10):
    from types import UnionType

    UnionTypes = {Union, UnionType}
else:
    UnionTypes = {Union}


class _RangeDict(TypedDict, total=False):
    """Represent arguments to `click.IntRange` or `click.FloatRange`."""

    max: Union[SupportsLt, SupportsLe]
    min: Union[SupportsGt, SupportsGe]
    max_open: bool
    min_open: bool


class PydanclickParamType(click.ParamType):
    """Wraps a click.ParamType to allow selective overriding of behavior"""

    def __init__(self, actual_type: click.ParamType) -> None:
        self._actual_type = actual_type

    @property
    def actual_type(self) -> click.ParamType:
        return self._actual_type

    def convert(self, value: Any, param: Optional[click.Parameter], ctx: Optional[click.Context]) -> Any:
        if isinstance(value, PydanclickDefault):
            return None
        return self._actual_type.convert(value, param, ctx)

    def __getattr__(self, attr: Any) -> Any:
        return getattr(self._actual_type, attr)


def _get_pydanclick_type(field_type: click.ParamType) -> click.ParamType:
    pydanclick_type: type[PydanclickParamType] = type(
        "PydanclickParamType",
        (
            PydanclickParamType,
            field_type.__class__,
        ),
        {},
    )
    return pydanclick_type(field_type)


class PydanclickDefault:
    """Represents a default value in pydanclick"""

    def __init__(self, default: Any) -> None:
        self._default = default

    def __getattr__(self, attr: Any) -> Any:
        return getattr(self._default, attr)

    def __eq__(self, value: object) -> Any:
        return self._default.__eq__(value)

    def __bool__(self) -> bool:
        return bool(self._default)

    def __repr__(self) -> Any:
        return repr(self._default)


class PydanclickDefaultCallable(PydanclickDefault):
    """Represents a callable default value in pydanclick"""

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self._default.__call__(*args, **kwargs)


def _get_range_from_metadata(metadata: list[Any]) -> _RangeDict:
    """Convert Pydantic numerical constraints to keyword arguments compatible with `IntRange` and `FloatRange`.

    Args:
        metadata: list of Pydantic constraints

    Returns:
        a dictionary
    """
    range_args: _RangeDict = {}
    for constraint in metadata:
        if isinstance(constraint, Le):
            range_args["max"] = constraint.le
            range_args["max_open"] = False
        if isinstance(constraint, Lt):
            range_args["max"] = constraint.lt
            range_args["max_open"] = True
        if isinstance(constraint, Ge):
            range_args["min"] = constraint.ge
            range_args["min_open"] = False
        if isinstance(constraint, Gt):
            range_args["min"] = constraint.gt
            range_args["min_open"] = True
    return range_args


def _get_numerical_type(field: FieldInfo) -> click.ParamType:
    """Convert a numerical field to a Click parameter type.

    Converts Pydantic numerical constraints (e.g. `Field(gt=0)` or `Field(le=10)`) into a Click range type such as
    `IntRange` or `FloatRange`. Unconstrained types result in `click.INT` or `click.FLOAT` types. Decimal types or any
    non-integer numerical type will be treated as a float.

    Args:
        field: field to convert

    Returns:
        either `click.INT`, `click.FLOAT` or an instance of `click.IntRange` or `click.FloatRange`
    """
    range_args = _get_range_from_metadata(field.metadata)
    if field.annotation is int or int in get_args(field.annotation):
        if range_args:
            return click.IntRange(**range_args)  # type: ignore[arg-type]
        return click.INT
    # Non-integer numerical types default to float
    if range_args:
        return click.FloatRange(**range_args)  # type: ignore[arg-type]
    return click.FLOAT


def _get_type_from_field(field: FieldInfo) -> click.ParamType:
    """Get the Click type for a Pydantic field.

    Pydantic and Click both define custom types for validating arguments. This function attempts to map Pydantic field
    types to Click `ParamType` instances, on a best effort basis. Pydantic types may be stricted than their Click
    counterparts: in that case, validation will happen when instantiating the Pydantic model, not when Click parses
    the CLI arguments. When no equivalent is found, Click won't perform any validation and Pydantic will receive raw
    strings.

    Args:
        field: field to convert

    Returns:
        a Click type
    """
    return _get_pydanclick_type(_get_click_type_from_field(field))


def _get_click_type_from_field(field: FieldInfo) -> click.ParamType:
    """Get the Click type for a Pydantic field.

    Pydantic and Click both define custom types for validating arguments. This function attempts to map Pydantic field
    types to Click `ParamType` instances, on a best effort basis. Pydantic types may be stricted than their Click
    counterparts: in that case, validation will happen when instantiating the Pydantic model, not when Click parses
    the CLI arguments. When no equivalent is found, Click won't perform any validation and Pydantic will receive raw
    strings.

    Args:
        field: field to convert

    Returns:
        a Click type
    """
    field_type = field.annotation
    field_args = get_args(field_type)
    field_origin = get_origin(field_type)
    # TODO: handle annotated
    # TODO: handle subclasses

    if (
        field_origin in UnionTypes
        and len(field_args) == 2
        and NoneType in field_args
        and field.default is not PydanticUndefined
    ):
        # Optional types where None is only used as a default value can be safely treated as a
        # non-optional type, since Click doesn't really distinguish between a string with default value None from
        # an actual str
        field_type = next(field_arg for field_arg in field_args if field_arg is not None)
    if field_type is str:
        return click.STRING
    elif field_type in (int, float):
        return _get_numerical_type(field)
    elif field_type is float:
        return click.FLOAT
    elif field_type is bool:
        return click.BOOL
    elif field_type is UUID:
        return click.UUID
    elif field_type is Path:
        return click.Path(path_type=Path)
    elif field_type in (datetime.datetime, datetime.date):
        return click.DateTime()
    elif field_origin is Literal:
        # TODO: allow converting literal to feature switches
        return click.Choice(field_args)
    else:
        return _create_custom_type(field)


def _create_custom_type(field: FieldInfo) -> click.ParamType:
    """Create a custom Click type from a Pydantic field."""
    name = "".join(part.capitalize() for part in re.split(r"\W", str(field.annotation)) if part)
    type_adapter = TypeAdapter(cast(type[Any], field.annotation))

    def convert(self, value, param, ctx):  # type: ignore[no-untyped-def]
        try:
            if isinstance(value, str):
                return type_adapter.validate_json(value)
            else:
                return type_adapter.validate_python(value)
        except ValidationError as e:
            self.fail(str(e), param, ctx)

    custom_type: type[click.ParamType] = type(
        name,
        (click.ParamType,),
        {
            "name": "JSON STRING",
            "convert": convert,
        },
    )
    return custom_type()
