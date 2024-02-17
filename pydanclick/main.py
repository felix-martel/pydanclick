import datetime
import functools
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Sequence,
    Type,
    TypedDict,
    TypeVar,
    Union,
    get_args,
    get_origin,
)
from uuid import UUID

import click
from annotated_types import Ge, Gt, Le, Lt, SupportsGe, SupportsGt, SupportsLe, SupportsLt
from pydantic import BaseModel
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

# Can't use `types.NoneType`, as it was only introduced in Python 3.10
NoneType = type(None)

T = TypeVar("T")


class _ParameterKwargs(TypedDict, total=False):
    """Represent valid parameters for `click.option()`."""

    param_decls: Optional[Sequence[str]]
    show_default: Union[bool, str, None]
    prompt: Union[bool, str]
    confirmation_prompt: Union[bool, str]
    prompt_required: bool
    hide_input: bool
    is_flag: Optional[bool]
    flag_value: Optional[Any]
    multiple: bool
    count: bool
    allow_from_autoenv: bool
    type: Optional[Union[click.ParamType, Any]]
    help: Optional[str]
    hidden: bool
    show_choices: bool
    show_envvar: bool


def from_pydantic(
    __var: str,
    model: Type[BaseModel],
    *,
    exclude: Sequence[str] = (),
    rename: Optional[Dict[str, str]] = None,
    shorten: Optional[Dict[str, str]] = None,
    prefix: str = "",
    parse_docstring: bool = True,
    docstring_style: Literal["google", "numpy", "sphinx"] = "google",
    extra_options: Optional[Dict[str, _ParameterKwargs]] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to add fields from a Pydantic model as options to a Click command.

    Args:
        __var: name of the variable that will receive the Pydantic model in the decorated function
        model: Pydantic model
        exclude: field names that won't be added to the command
        rename: a mapping from field names to command line option names (this will override any prefix). Option names
            must start with two dashes
        shorten: a mapping from field names to short command line option names. Option names must start with one dash
        prefix: a prefix to add to option names (without any dash)
        parse_docstring: if True and `griffe` is installed, parse the docstring of the Pydantic model and pass argument
            documentation to the Click `help` option
        docstring_style: style of the docstring (`google`, `numpy` or `sphinx`). Ignored if `parse_docstring` is False
        extra_options: a mapping from field names to a dictionary of options passed to the `click.option()` function

    Returns:
        a decorator that adds options to a function
    """
    excluded_fields = set(exclude)
    fields = {
        field_name: field for field_name, field in model.model_fields.items() if field_name not in excluded_fields
    }
    renamed_fields = rename if rename is not None else {}
    shortened_fields = shorten if shorten is not None else {}
    extra_options = extra_options if extra_options is not None else {}
    doc = _parse_docstring(model, docstring_style=docstring_style) if parse_docstring else {}

    def wrapper(f: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(f)
        def wrapped(**kwargs: Any) -> Any:
            raw_model = {field: kwargs.pop(field) for field in fields if field in kwargs}
            kwargs[__var] = model.model_validate(raw_model)
            return f(**kwargs)

        # Use `reversed` to preserve order
        for field_name, field in reversed(fields.items()):
            option_name = renamed_fields.get(field_name)
            short_name = shortened_fields.get(field_name)
            wrapped = _get_option_from_field(
                field_name,
                field,
                prefix=prefix,
                documentation=doc,
                option_name=option_name,
                short_name=short_name,
                option_kwargs=extra_options.get(field_name),
            )(wrapped)
        return wrapped

    return wrapper


def _get_option_from_field(
    field_name: str,
    field: FieldInfo,
    prefix: str = "",
    documentation: Optional[Dict[str, str]] = None,
    option_name: Optional[str] = None,
    short_name: Optional[str] = None,
    option_kwargs: Optional[_ParameterKwargs] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Convert a Pydantic field to a Click option function.

    Note that it doesn't return a `click.Option` object, but rather a decorator, as created by `click.option()`.

    Args:
        field_name: Pydantic field name (usually in snake_case)
        field: field to convert
        prefix: prefix to add to the field name
        documentation: help string for the option
        option_name: name of the option (in kebab-case, starting with two dashes). If not provided, option name will be
            `--{prefix}-{field-name}`, where `field-name` is the kebab-case version of `field_name`.
        short_name: short name of the option (one dash and one letter)
        option_kwargs: extra options to pass to `click.option`

    Returns:

    """
    if documentation is None:
        documentation = {}
    param_decls = [field_name]
    if option_name is None:
        option_name = _get_option_name(field_name, is_boolean_flag=field.annotation is bool, prefix=prefix)
    param_decls.append(option_name)
    if short_name is not None:
        param_decls.append(short_name)
    kwargs = {
        "type": _get_type_from_field(field),
        "default": _get_default_value_from_field(field),
        "required": field.is_required(),
        "help": field.description or documentation.get(field_name, ""),
    }
    if option_kwargs is not None:
        kwargs.update(option_kwargs)
    return click.option(*param_decls, cls=click.Option, **kwargs)


def _get_option_name(field_name: str, is_boolean_flag: bool = False, prefix: str = "") -> str:
    """Convert a field name into a CLI option name.

    Args:
        field_name: field name, in snake_case
        is_boolean_flag: whether the field is a boolean flag. If True, this will create two options `--{opt}/--no-{opt}`
            as recommended by Click: https://click.palletsprojects.com/en/8.1.x/options/#boolean-flags
        prefix: an optional prefix to add to the option name (it does not need to start or end with a dash)

    Returns:
        the option name, in kebab-case, with two dashes prepended and an optional prefix
    """
    base_option_name = field_name.replace("_", "-")
    if prefix:
        base_option_name = f"{prefix}-{base_option_name}"
    if is_boolean_flag:
        return f"--{base_option_name}/--no-{base_option_name}"
    return f"--{base_option_name}"


class _RangeDict(TypedDict, total=False):
    """Represent arguments to `click.IntRange` or `click.FloatRange`."""

    max: Union[SupportsLt, SupportsLe]
    min: Union[SupportsGt, SupportsGe]
    max_open: bool
    min_open: bool


def _get_range_from_metadata(metadata: List[Any]) -> _RangeDict:
    """Convert Pydantic numerical constraints to keyword argumetns compatible with `IntRange` and `FloatRange`.

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
    if field.annotation is int:
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
    field_type = field.annotation
    field_args = get_args(field_type)
    field_origin = get_origin(field_type)
    # TODO: handle annotated
    # TODO: handle subclasses
    if field_origin is Union and len(field_args) == 2 and NoneType in field_args and field.default is None:
        # Optional types where None is only used as a default value can be safely treated as a
        # non-optional type, since Click doesn't really distinguish between a strign with default value None from
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
        # TODO: generate custom types: https://click.palletsprojects.com/en/8.1.x/api/#click.ParamType ?
        # Default to None and let Pydantic handle the validation
        custom_type = click.ParamType()
        custom_type.name = str(field.annotation)
        return custom_type


def _get_default_value_from_field(field: FieldInfo) -> Union[Any, Callable[[], Any], None]:
    """Return the default value of `field`.

    Args:
         field: Pydantic field

    Returns:
        either the default value or the default factory or None if field has no default
    """
    if field.default is not PydanticUndefined:
        return field.default
    elif field.default_factory is not None:
        return field.default_factory
    return None


def _parse_docstring(
    model_cls: Type[BaseModel], docstring_style: Literal["google", "numpy", "sphinx"] = "google"
) -> Dict[str, str]:
    """Parse the docstring of a `BaseModel` and returns a mapping from field name to their documentation.

    Requires the optional dependency `griffe`. If it is not installed, return an empty dictionary.

    Args:
        model_cls: base model to parse
        docstring_style: docstring style (see `griffe` documentation for details)

    Returns:
        a mapping from field name to their documentation. Only documented fields will be present
    """
    try:
        from griffe.dataclasses import Docstring
        from griffe.docstrings.dataclasses import DocstringAttribute, DocstringSectionAttributes
    except ImportError:
        return {}
    docstring = Docstring(model_cls.__doc__ or "").parse(docstring_style)
    fields = {}
    for section in docstring:
        if not isinstance(section, DocstringSectionAttributes):
            continue
        for attribute in section.value:
            if not isinstance(attribute, DocstringAttribute):
                continue
            fields[attribute.name] = attribute.description
    return fields
