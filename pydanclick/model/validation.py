"""Validation consists in converting the arguments (passed to the Click command) to a Pydantic model.

Validation involves the following steps:

- collect arguments that corresponds to a Pydantic field
- create a flat representation of the object (with nested field names separated by dots)
- unflatten this representation
- pass the nested representation to the `model_validate` method of the Pydantic model
"""

from typing import Any, Dict, Type

from pydantic import BaseModel
from typing_extensions import TypeVar

from pydanclick.types import ArgumentName, DottedFieldName

M = TypeVar("M", bound=BaseModel)
V = TypeVar("V")
K = TypeVar("K", bound=str)


def model_validate_kwargs(
    kwargs: Dict[ArgumentName, Any],
    model: Type[M],
    qualified_names: Dict[ArgumentName, DottedFieldName],
    defaults_to_ignore: Dict[str, Any],
) -> M:
    """Instantiate `model` for keyword arguments.

    >>> class Foo(BaseModel):
    ...     a: int
    >>> class Bar(BaseModel):
    ...     b: Foo
    ...     c: str
    >>> model_validate_kwargs({"arg1": 1, "arg2": "c"}, Bar, {"arg1": "b.a", "arg2": "c"})
    Bar(b=Foo(a=1), c='c')

    Args:
        kwargs: mapping from argument name to their values
        model: Pydantic model to instantiate
        qualified_names: a mapping from argument names to corresponding dotted field names
        defaults_to_ignore: mapping from argument name to a default to ignore

    Returns:
        an instance of `model` with the provided values
    """
    flat_model = _parse_options(qualified_names, kwargs, defaults_to_ignore)
    raw_model = _unflatten_dict(flat_model)
    return model.model_validate(raw_model)


def _unflatten_dict(d: Dict[K, V], sep: str = ".") -> Dict[str, Any]:
    """Create a nested dictionary from a flat dictionary.

    >>> _unflatten_dict({"a.b.c": "abc", "a.b.d": "def", "a.e": "ghi", "f": 1})
    {'a': {'b': {'c': 'abc', 'd': 'def'}, 'e': 'ghi'}, 'f': 1}

    Args:
        d: flat mapping with strings as keys
        sep: separator used to separate different levels of nesting in a key
    """
    nested: Dict[str, Any] = {}
    for k, v in d.items():
        if not k:
            raise ValueError("Empty keys are not supported")
        parts = k.split(sep)
        current_dict = nested
        for part in parts[:-1]:
            current_dict = current_dict.setdefault(part, {})
        current_dict[parts[-1]] = v
    return nested


def _parse_options(
    aliases: Dict[ArgumentName, DottedFieldName], kwargs: Dict[ArgumentName, V], defaults_to_ignore: Dict[str, Any]
) -> Dict[DottedFieldName, V]:
    """Extract keys and values from `kwargs`.

    Args:
        aliases: mapping from argument name to field name
        kwargs: mapping from argument name to their values. Note that `kwargs` will be modified in-place
        defaults_to_ignore: mapping from argument name to a default to ignore

    Returns:
        mapping from field name to their values
    """
    parsed = {}
    for key in aliases.keys() & kwargs.keys():
        value = kwargs.pop(key)
        default = defaults_to_ignore.get(key)
        if value is not None and (default is None or default != value):
            parsed[aliases[key]] = value
    return parsed
