from typing import Any, Optional, TypedDict, Union

import click
from typing_extensions import NewType


class _ParameterKwargs(TypedDict, total=False):
    """Represent valid parameters for `click.option()`."""

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
    required: bool
    default: Any


ArgumentName = NewType("ArgumentName", str)
OptionName = NewType("OptionName", str)
FieldName = NewType("FieldName", str)
DottedFieldName = NewType("DottedFieldName", str)
