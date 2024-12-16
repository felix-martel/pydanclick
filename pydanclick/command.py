"""Utilities to work with Click commands and options."""

from typing import Any, Callable, Optional, TypeVar, Union

import click

T = TypeVar("T")


def add_options(
    __f_or_opts: Union[Callable[..., Any], list[click.Option]], options: Optional[list[click.Option]] = None
) -> Callable[..., Any]:
    """Add options to a Click command.

    Given `options` a list of `click.Option` instances, it can either be used as a decorator:

    ```python
    @click.command()
    @add_options(options)
    def cli(...):
        pass
    ```

    Or called directly on a function:

    ```python
    command = add_options(command, options)
    ```

    Args:
        __f_or_opts: if used as a decorator, list of options to add. Otherwise, a callable or a `click.Command` to add
            the options to
        options: list of options to add (if called directly on a function)

    Returns:
        either a decorator or the callable/command with the new options added
    """
    if callable(__f_or_opts):
        if options is None:
            raise ValueError("No options specified.")
        return _add_options(__f_or_opts, options)

    def wrapper(__f: Callable[..., T]) -> Callable[..., T]:
        return add_options(__f, __f_or_opts)

    return wrapper


def _add_options(f: Callable[..., Any], options: list[click.Option]) -> Callable[..., Any]:
    """Add Click options to a callable or command.

    This is basically a copy of what the `@click.option()` decorator does (i.e. if `f` isn't a `click.Command`, add its
    parameters to a hidden `__click_params__` attribute).

    Args:
        f: callable or `click.Command` instance. It will be modified in-place.
        options: list of options to add to `f`

    Returns:
        the same callable or command, returned for convenience
    """
    ordered_options = reversed(options)
    if isinstance(f, click.Command):
        f.params.extend(ordered_options)
    else:
        if not hasattr(f, "__click_params__"):
            f.__click_params__ = []  # type: ignore[attr-defined]
        f.__click_params__.extend(ordered_options)  # type: ignore[attr-defined]
    return f
