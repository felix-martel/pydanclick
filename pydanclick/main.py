import functools
from typing import Any, Callable, Dict, Literal, Optional, Sequence, Type, TypeVar

from pydantic import BaseModel

from pydanclick.command import add_options
from pydanclick.model import convert_to_click
from pydanclick.types import _ParameterKwargs

T = TypeVar("T")


def from_pydantic(
    __var: str,
    model: Type[BaseModel],
    *,
    exclude: Sequence[str] = (),
    rename: Optional[Dict[str, str]] = None,
    shorten: Optional[Dict[str, str]] = None,
    prefix: Optional[str] = None,
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
    options, validator = convert_to_click(
        model,
        exclude=exclude,
        rename=rename,
        shorten=shorten,
        prefix=prefix,
        parse_docstring=parse_docstring,
        docstring_style=docstring_style,
        extra_options=extra_options,
    )

    def wrapper(f: Callable[..., T]) -> Callable[..., T]:
        @add_options(options)
        @functools.wraps(f)
        def wrapped(**kwargs: Any) -> T:
            kwargs[__var] = validator(kwargs)
            return f(**kwargs)

        return wrapped  # type: ignore[no-any-return]

    return wrapper
