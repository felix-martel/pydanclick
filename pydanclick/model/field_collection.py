"""Collect fields from Pydantic models."""

import dataclasses
import re
from typing import Any, Iterable, List, Literal, Optional, Tuple, Type, Union, get_args, get_origin

from pydantic import BaseModel
from pydantic.fields import FieldInfo
from typing_extensions import TypeGuard

from pydanclick.model.docstrings import parse_attribute_documentation
from pydanclick.types import DottedFieldName, FieldName


@dataclasses.dataclass
class _Field:
    """Represent a (possibly nested) field contained in a Pydantic model.

    Attributes:
        name: name of the field (without its parent)
        dotted_name: dotted name of the field (i.e. field name and all its parent names, joined with dots). From a user
            standpoint, this uniquely identifies the field within a nested model.
        field_info: Pydantic `FieldInfo` object representing the field
        documentation: help string for the field, if available
        parents: list of parent names for the field
    """

    name: FieldName
    dotted_name: DottedFieldName
    field_info: FieldInfo
    documentation: Optional[str] = None
    parents: Tuple[FieldName, ...] = ()

    @property
    def is_boolean_flag(self) -> bool:
        """Return True if the field represents boolean values."""
        return self.field_info.annotation is bool


def collect_fields(
    obj: Type[BaseModel],
    excluded_fields: Iterable[DottedFieldName] = frozenset(),
    parse_docstring: bool = True,
    docstring_style: Literal["google", "numpy", "sphinx"] = "google",
) -> List[_Field]:
    """Collect fields (including nested ones) from a Pydantic model.

    Args:
        obj: Pydantic model to collect fields from
        excluded_fields: fields to exclude. To exclude nested fields, use their dotted names, i.e. the field name and
            all its parent names, separated by dots
        parse_docstring: if True, parse the model docstring and extract document for each field
        docstring_style: docstring style of the model. Ignored if `parse_docstring=False`

    Returns:
        a mapping from field dotted names to field objects. Each field object contains the Pydantic `FieldInfo`, as well
            as additional information, such as field parents, name of the argument mapped to the field, documentation
            and so on. See `_Field` for details.
    """
    if excluded_fields:
        excluded_pattern = r"^(" + "|".join(field.replace(".", "[.]") for field in excluded_fields) + r")\b"
    else:
        excluded_pattern = None
    return [
        option
        for option in _collect_fields(obj, docstring_style=docstring_style, parse_docstring=parse_docstring)
        if excluded_pattern is None or not re.search(excluded_pattern, option.dotted_name)
    ]


def _iter_union(field_type: Any) -> List[Type[Any]]:
    """Iterate over the types of a union.

    Args:
        field_type: union type to iterate over. If not a union, return an empty list.

    Returns:
        list of types in the union, if any
    """
    if get_origin(field_type) is Union:
        return list(get_args(field_type))
    return []


def _is_pydantic_model(model: Any) -> TypeGuard[Type[BaseModel]]:
    """Return True if `model` is a Pydantic `BaseModel` class."""
    try:
        return issubclass(model, BaseModel)
    except TypeError:
        return False


def _collect_fields(
    obj: Union[Type[BaseModel], FieldInfo],
    name: FieldName = "",  # type: ignore[assignment]
    parents: Tuple[FieldName, ...] = (),
    documentation: Optional[str] = None,
    parse_docstring: bool = True,
    docstring_style: Literal["google", "numpy", "sphinx"] = "google",
) -> Iterable[_Field]:
    """Recursively iterate over fields from a Pydantic model."""
    if _is_pydantic_model(obj) or _is_pydantic_model(getattr(obj, "annotation", None)):
        model: Type[BaseModel]
        model = obj if _is_pydantic_model(obj) else obj.annotation  # type: ignore[assignment, union-attr]
        docstrings = parse_attribute_documentation(model, docstring_style=docstring_style) if parse_docstring else {}
        for field_name, field in model.model_fields.items():
            field_name = FieldName(field_name)
            documentation = docstrings.get(field_name, None)
            yield from _collect_fields(
                field,
                name=field_name,
                parents=(*parents, field_name),
                documentation=documentation,
                parse_docstring=parse_docstring,
            )
    elif isinstance(obj, FieldInfo):
        if not name:
            raise ValueError(f"Can't automatically infer a name from a field: {obj}")
        for annotation in _iter_union(obj.annotation):
            if _is_pydantic_model(annotation):
                yield from _collect_fields(
                    annotation,
                    name=name,
                    parents=parents,
                    documentation=documentation,
                    parse_docstring=parse_docstring,
                )
        # TODO: exclude base models from the union
        dotted_name = DottedFieldName(".".join(parents))
        yield _Field(
            name=name,
            dotted_name=dotted_name,
            parents=parents,
            field_info=obj,
            documentation=documentation,
        )
    else:
        raise TypeError(f"Can't process {type(obj)}: {obj} is neither a `BaseModel`, nor a `FieldInfo`")
