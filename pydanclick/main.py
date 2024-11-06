import functools
from collections.abc import Sequence
from typing import Any, Callable, Literal, Optional, TypeVar, Union

from pydantic import BaseModel

from pydanclick.command import add_options
from pydanclick.model import convert_to_click
from pydanclick.types import _ParameterKwargs
from pydanclick.utils import camel_case_to_snake_case

T = TypeVar("T")


def from_pydantic(
    __var_or_model: Union[str, type[BaseModel]],
    model: Optional[type[BaseModel]] = None,
    *,
    exclude: Sequence[str] = (),
    rename: Optional[dict[str, str]] = None,
    shorten: Optional[dict[str, str]] = None,
    prefix: Optional[str] = None,
    parse_docstring: bool = True,
    docstring_style: Literal["google", "numpy", "sphinx"] = "google",
    extra_options: Optional[dict[str, _ParameterKwargs]] = None,
    ignore_unsupported: Optional[bool] = False,
    unpack_list: bool = False,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to add fields from a Pydantic model as options to a Click command.

    Args:
        __var_or_model: name of the variable that will receive the Pydantic model in the decorated function
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
        ignore_unsupported: ignore unsupported model fields instead of raising
        unpack_list: if True, a list of nested models (e.g. `list[Foo]`) will be yield one command-line option for each
            field in the nested model. Each field can be specified multiple times. This API is experimental.


    Returns:
        a decorator that adds options to a function
    """
    if isinstance(__var_or_model, str):
        if model is None:
            raise ValueError("`model` must be provided")
        variable_name = __var_or_model
    else:
        model = __var_or_model
        variable_name = camel_case_to_snake_case(model.__name__)
    options, validator = convert_to_click(
        model,
        exclude=exclude,
        rename=rename,
        shorten=shorten,
        prefix=prefix,
        parse_docstring=parse_docstring,
        docstring_style=docstring_style,
        extra_options=extra_options,
        ignore_unsupported=ignore_unsupported,
        unpack_list=unpack_list,
    )

    def wrapper(f: Callable[..., T]) -> Callable[..., T]:
        @add_options(options)
        @functools.wraps(f)
        def wrapped(**kwargs: Any) -> T:
            kwargs[variable_name] = validator(kwargs)
            return f(**kwargs)

        return wrapped  # type: ignore[no-any-return]

    return wrapper
