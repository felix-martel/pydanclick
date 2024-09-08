"""Validation consists in converting the arguments (passed to the Click command) to a Pydantic model.

Validation involves the following steps:

- collect arguments that corresponds to a Pydantic field
- create a flat representation of the object (with nested field names separated by dots)
- unflatten this representation
- pass the nested representation to the `model_validate` method of the Pydantic model
"""

from itertools import zip_longest
from typing import Any, Dict, Iterable, List, Set, Type

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
    unpacked_names: Set[DottedFieldName],
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

    Returns:
        an instance of `model` with the provided values
    """
    flat_model = _parse_options(qualified_names, kwargs)
    raw_model = _unflatten_dict(flat_model)
    for name in unpacked_names & raw_model.keys():
        raw_model[name] = _pack_dict(raw_model[name])
        # There is no way to distinguish between passing an empty list and not passing anything: here, we assume empty
        # means nothing was passed, and we rely on Pydantic validation to either fail (if argument is mandatory) or
        # provide a default value (if there is one). To pass an empty list explicitly, turn off unpacking and pass '[]'
        if not raw_model[name]:
            del raw_model[name]
    return model.model_validate(raw_model)


def _pack_dict(d: Dict[K, Iterable[V]]) -> List[Dict[K, Any]]:
    unset = object()
    packed_dict = []
    for values in zip_longest(*d.values(), fillvalue=unset):
        packed_dict.append({key: value for key, value in zip(d, values) if value is not unset})
    return packed_dict


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
    aliases: Dict[ArgumentName, DottedFieldName], kwargs: Dict[ArgumentName, V]
) -> Dict[DottedFieldName, V]:
    """Extract keys and values from `kwargs`.

    Args:
        aliases: mapping from argument name to field name
        kwargs: mapping from argument name to their values. Note that `kwargs` will be modified in-place

    Returns:
        mapping from field name to their values
    """
    parsed = {}
    for key in aliases.keys() & kwargs.keys():
        value = kwargs.pop(key)
        if value is not None:
            parsed[aliases[key]] = value
    return parsed
