from typing import Any, Dict, Literal, Optional, Sequence, Set, Type

from pydantic import BaseModel, ConfigDict, Field

from pydanclick.types import DottedFieldName, OptionName, _ParameterKwargs

unset = object()
_PYDANCLICK_OPTION_ATTRIBUTE = "__pydanclick__"


class PydanclickConfig(BaseModel):
    """Configure how to turn a model into Click options.

    When converting a Pydantic model to Click options, Pydanclick will look for an `__pydanclick__` attribute of the
    model, and read custom conversion parameters from it. This attribute can be a `PydanclickConfig` object, or a
    dictionary with the same keys.

    ```python
    class Foo(BaseModel):
        a: int
        b: str
        c: float

        __pydanclick__ = PydanclickConfig(prefix="foo")
    ```

    Attributes:
        exclude: fields to exclude
        rename: fields to rename
        shorten: fields to shorten
        prefix: prefix to prepend to the option names
        parse_docstring: if True, create option help strings from docstring
        docstring_style: docstring style
        extra_options: provide extra options to specific fields
    """

    exclude: Sequence[str] = ()
    rename: Optional[Dict[str, str]] = None
    shorten: Optional[Dict[str, str]] = None
    prefix: Optional[str] = None
    parse_docstring: bool = True
    docstring_style: Literal["google", "numpy", "sphinx"] = "google"
    extra_options: Optional[Dict[str, _ParameterKwargs]] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class _Config(BaseModel):
    exclude: Set[DottedFieldName] = Field(default_factory=set)
    aliases: Optional[Dict[DottedFieldName, OptionName]] = Field(None, alias="rename")
    shorten: Optional[Dict[DottedFieldName, OptionName]] = None
    prefix: Optional[str] = None
    parse_docstring: bool = True
    docstring_style: Literal["google", "numpy", "sphinx"] = "google"
    extra_options: Optional[Dict[DottedFieldName, _ParameterKwargs]] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


def get_config(
    model: Type[BaseModel],
    *,
    exclude: Sequence[str] = (),
    rename: Optional[Dict[str, str]] = None,
    shorten: Optional[Dict[str, str]] = None,
    prefix: Optional[str] = None,
    parse_docstring: Optional[bool] = None,
    docstring_style: Literal["google", "numpy", "sphinx"] = "google",
    extra_options: Optional[Dict[str, _ParameterKwargs]] = None,
) -> _Config:
    """Get conversion config for a given model.

    Config parameters are read from three sources (by decreasing priority):

    - non-default arguments provided to `get_config`
    - `__pydanclick__` attribute of `model`, if any
    - default values

    Args:
        model: Pydantic class to convert
        *args: see `from_pydantic` help

    Returns:
        a validated conversion config
    """
    default_options = getattr(model, _PYDANCLICK_OPTION_ATTRIBUTE, {})
    if isinstance(default_options, PydanclickConfig):
        default_options = default_options.model_dump(exclude_unset=True)
    overriding_options: Dict[str, Any] = {
        key: value
        for key, value in [
            ("rename", rename),
            ("shorten", shorten),
            ("prefix", prefix),
            ("parse_docstring", parse_docstring),
            ("extra_options", extra_options),
        ]
        if value is not None
    }
    if exclude:
        overriding_options["exclude"] = exclude
    if "docstring_style" not in default_options:
        overriding_options["docstring_style"] = docstring_style
    return _Config.model_validate({**default_options, **overriding_options})
