"""Convert Pydantic fields to Click options."""

from typing import Any, Callable, Optional, TypeVar, Union

import click
from pydantic import PydanticUserError
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

from pydanclick.model.field_collection import _Field
from pydanclick.model.type_conversion import PydanclickDefault, PydanclickDefaultCallable, _get_type_from_field
from pydanclick.types import ArgumentName, DottedFieldName, OptionName, _ParameterKwargs
from pydanclick.utils import kebab_case_to_snake_case, snake_case_to_kebab_case, strip_option_name

T = TypeVar("T")


def convert_fields_to_options(
    fields: list[_Field],
    prefix: Optional[str] = None,
    aliases: Optional[dict[DottedFieldName, OptionName]] = None,
    shorten: Optional[dict[DottedFieldName, OptionName]] = None,
    extra_options: Optional[dict[DottedFieldName, _ParameterKwargs]] = None,
    ignore_unsupported: Optional[bool] = False,
) -> tuple[dict[ArgumentName, DottedFieldName], list[click.Option]]:
    """Convert Pydantic fields to Click options.

    Args:
        fields: fields to convert
        prefix: prefix to add to each option name, if any
        aliases: custom option names for specific fields, as a mapping from dotted field names to option names
        shorten: short option names for specific fields, as a mapping from dotted field names to 1-letter option names
        extra_options: extra options to pass to `click.Option` for specific fields, as a mapping from dotted field names
            to option dictionary
        ignore_unsupported: ignore unsupported model fields instead of raising

    Returns:
        a pair `(qualified_names, options)` where `qualified_names` is a mapping from argument names to dotted field
            names and `options` is a list of `click.Option` objects. When calling a command, Click will use these
            options to parse the command line arguments, and will return a mapping from argument names to values.
    """
    aliases = aliases or {}
    aliases = {dotted_name: OptionName(_convert_to_valid_prefix(alias)) for dotted_name, alias in aliases.items()}
    option_prefix = _convert_to_valid_prefix(prefix) if prefix is not None else ""
    argument_prefix = kebab_case_to_snake_case(strip_option_name(option_prefix)) + "_" if option_prefix else ""
    shorten = shorten or {}
    extra_options = extra_options or {}
    options = []
    qualified_names = {}
    for field in fields:
        argument_name = ArgumentName(argument_prefix + "_".join(field.parents))
        try:
            option = _get_option_from_field(
                argument_name=argument_name,
                option_name=get_option_name(
                    field.dotted_name, aliases=aliases, is_boolean=field.is_boolean_flag, prefix=option_prefix
                ),
                field_info=field.field_info,
                documentation=field.field_info.description or field.documentation,
                short_name=shorten.get(field.dotted_name, None),
                option_kwargs=extra_options.get(field.dotted_name, {}),
                multiple=field.multiple,
            )
            options.append(option)
            qualified_names[argument_name] = field.dotted_name
        except PydanticUserError as e:
            if ignore_unsupported and e.code == "schema-for-unknown-type":
                continue
            raise
    return qualified_names, options


def _get_base_option_name(
    dotted_name: DottedFieldName, aliases: dict[DottedFieldName, OptionName], prefix: str = ""
) -> str:
    parents = dotted_name.split(".")
    for i in range(len(parents) + 1, 0, -1):
        parent = DottedFieldName(".".join(parents[:i]))
        alias = aliases.get(parent)
        if not alias:
            continue
        suffix = snake_case_to_kebab_case("-".join(parents[i:]))
        if suffix:
            if "/" in alias:
                raise ValueError(
                    f"Invalid boolean alias `{alias}` for field `{parent}`: boolean aliases can only be used for "
                    f"boolean fields, however `{parent}` has child field `{suffix}`."
                )
            return alias + "-" + suffix
        return alias
    if prefix:
        return snake_case_to_kebab_case("-".join((prefix, *parents)))
    else:
        return "--" + snake_case_to_kebab_case(dotted_name)


def _convert_to_valid_prefix(name: str) -> str:
    if not name:
        return name
    return "--" + strip_option_name(name)


def get_option_name(
    dotted_name: DottedFieldName,
    *,
    aliases: dict[DottedFieldName, OptionName],
    is_boolean: bool = False,
    prefix: str = "",
) -> OptionName:
    """Get the option name from a dotted field name.

    >>> get_option_name("foo_bar", aliases={})
    '--foo-bar'
    >>> get_option_name("foo", aliases={}, is_boolean=True)
    '--foo/--no-foo'
    >>> get_option_name("foo.bar.baz", aliases={"foo.bar.baz": "--alias"})
    '--alias'
    >>> get_option_name("foo.bar.baz", aliases={"foo.bar": "--alias"})
    '--alias-baz'
    >>> get_option_name("bar", aliases={}, is_boolean=True, prefix="--foo")
    '--foo-bar/--no-foo-bar'

    Args:
        dotted_name: dotted name of the field (i.e. the field name and all its parent names, joined by a dot)
        aliases: mapping from dotted field names to option names, used to override default option names. Aliases must
            use kebab case and start with two dashes.
        is_boolean: whether the field is a boolean flag. Boolean flags have a specific behavior in Click: they have
            two option names, separated with a slash, one for True and one for False (for example, `--shout/--no-shout`)
        prefix: prefix to prepend to the option name. Ignored if an alias was found for `dotted_name` or one of its
            parent. If provided, prefix must use kebab case and start with two dashes.

    Return:
        option name, in kebab case and with two leading dashes
    """
    base_name = _get_base_option_name(dotted_name, aliases=aliases, prefix=prefix)
    if not is_boolean or "/" in base_name:
        return OptionName(base_name)
    else:
        if base_name.startswith("--"):
            base_name = base_name[2:]
        return OptionName(f"--{base_name}/--no-{base_name}")


def _get_option_from_field(
    argument_name: ArgumentName,
    option_name: str,
    field_info: FieldInfo,
    documentation: Optional[str] = None,
    short_name: Optional[str] = None,
    option_kwargs: Optional[_ParameterKwargs] = None,
    multiple: bool = False,
) -> click.Option:
    """Convert a Pydantic field to a Click option.

    Args:
        argument_name: argument name (i.e. name of the variable that will receive the option). Must be a valid Python
            identifier, distinct from all other argument names for the same command
        option_name: name of the option (in kebab-case, starting with two dashes)
        field_info: field to convert
        documentation: help string for the option
        short_name: short name of the option (one dash and one letter)
        option_kwargs: extra options to pass to `click.option`
        multiple: if field can be specified multiple times

    Returns:
        `click.Option` object
    """
    param_decls = [argument_name, option_name]
    if short_name is not None:
        param_decls.append(short_name)
    kwargs: _ParameterKwargs = {
        "type": _get_type_from_field(field_info),
        "default": _get_default_value_from_field(field_info) if not multiple else [],
        "required": field_info.is_required(),
        "help": documentation,
        "multiple": multiple,
    }
    if option_kwargs is not None:
        kwargs.update(option_kwargs)
    return click.Option(param_decls=param_decls, **kwargs)


def _get_default_value_from_field(field: FieldInfo) -> Union[Any, Callable[[], Any], None]:
    """Return the default value of `field`.

    Args:
         field: Pydantic field

    Returns:
        either the default value or the default factory or None if field has no default
    """
    if field.default is not None:
        if field.default is not PydanticUndefined:
            return PydanclickDefault(field.default)
        elif field.default_factory is not None:
            return PydanclickDefaultCallable(field.default_factory)
    return None
