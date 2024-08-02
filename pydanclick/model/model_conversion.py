"""Convert a Pydantic model to Click options, and provide function to convert Click arguments back to Pydantic."""

import functools
from typing import Callable, Dict, List, Literal, Optional, Sequence, Set, Tuple, Type, TypeVar, cast

import click
from pydantic import BaseModel

from pydanclick.model.field_collection import collect_fields
from pydanclick.model.field_conversion import convert_fields_to_options
from pydanclick.model.validation import model_validate_kwargs
from pydanclick.types import DottedFieldName, OptionName, _ParameterKwargs

T = TypeVar("T")
M = TypeVar("M", bound=BaseModel)


def convert_to_click(
    model: Type[M],
    *,
    exclude: Sequence[str] = (),
    rename: Optional[Dict[str, str]] = None,
    shorten: Optional[Dict[str, str]] = None,
    prefix: Optional[str] = None,
    parse_docstring: bool = True,
    docstring_style: Literal["google", "numpy", "sphinx"] = "google",
    extra_options: Optional[Dict[str, _ParameterKwargs]] = None,
) -> Tuple[List[click.Option], Callable[..., M]]:
    """Extract Click options from a Pydantic model.

    Here's an example on how it can be used:
    ```python
    import click
    from pydanclick.model import convert_to_click
    from pydanclick.command import add_options

    options, validate = convert_to_click(MyModel)

    @click.command()
    @add_options(options)
    def func(**kwargs):
        my_obj = validate(kwargs)
        assert isinstance(my_obj, MyModel)  # True
    ```
    In real life however, you can simply use `pydanclick.from_pydantic()` to avoid the boilerplate.

    Args:
        model: Pydantic model
        exclude: fields to exclude. Use dotted names for nested fields (i.e. parent names and field name, joined by
            a dot). Excluded fields must have a default value: otherwise, model instantiation will fail.
        rename: a mapping from dotted field names to option names, to override the default values
        shorten: a mapping from dotted field names to short option names
        prefix: prefix to add to option names. Can be useful to disambiguate field with the same names from different
            models. Prefix won't be added to aliases or short option names.
        parse_docstring: if True, parse model docstring to extract field documentation
        docstring_style: docstring style of the model. Only used if `parse_docstring=True`
        extra_options: extra options to pass to `click.Option` for specific fields, as a mapping from dotted field names
            to option dictionary

    Returns:
        a pair `(options, validate)` where `options` is the list of Click options extracted from the model, and
            `validate` is a function that can instantiate a model from the list of arguments parsed by Click
    """
    # We're doing a lot of casting here, to convert regular strings provided by the user into specific string types
    # used internally to disambiguate the different names associated with a field (option, argument, dotted...)
    fields = collect_fields(
        obj=model,
        excluded_fields=cast(Set[DottedFieldName], set(exclude)),
        docstring_style=docstring_style,
        parse_docstring=parse_docstring,
    )
    qualified_names, options = convert_fields_to_options(
        fields,
        prefix=prefix,
        aliases=cast(Optional[Dict[DottedFieldName, OptionName]], rename),
        shorten=cast(Optional[Dict[DottedFieldName, OptionName]], shorten),
        extra_options=cast(Dict[DottedFieldName, _ParameterKwargs], extra_options),
    )

    validator = functools.partial(model_validate_kwargs, model=model, qualified_names=qualified_names)
    return options, validator
