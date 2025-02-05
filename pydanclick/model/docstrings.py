"""Extract attribute documentation from docstrings."""

from typing import Literal

from pydantic import BaseModel
from typing_extensions import TypeAlias

from pydanclick.types import FieldName

DocstringStyle: TypeAlias = Literal["google", "numpy", "sphinx"]


def parse_attribute_documentation(
    model_cls: type[BaseModel], docstring_style: DocstringStyle = "google"
) -> dict[FieldName, str]:
    """Parse the docstring of a `BaseModel` and returns a mapping from field name to their documentation.

    Requires the optional dependency `griffe`. If it is not installed, returns an empty dictionary.

    Args:
        model_cls: base model to parse
        docstring_style: docstring style (see `griffe` documentation for details)

    Returns:
        a mapping from field name to their documentation. Only documented fields will be present
    """
    try:
        import logging

        from griffe import Docstring, DocstringAttribute, DocstringSectionAttributes

        logging.getLogger(f"griffe.docstrings.{docstring_style}").disabled = True
        logging.getLogger("griffe.agents.nodes").disabled = True
    except ImportError:
        return {}

    class_docs: list[str] = []
    for cls in [model_cls, *model_cls.__bases__]:
        if issubclass(cls, BaseModel) and cls is not BaseModel and cls.__doc__ is not None:
            class_docs.append(cls.__doc__)

    fields = {}
    for doc in reversed(class_docs):
        docstring = Docstring(doc).parse(docstring_style)
        for section in docstring:
            if not isinstance(section, DocstringSectionAttributes):
                continue
            for attribute in section.value:
                if not isinstance(attribute, DocstringAttribute):
                    continue
                fields[FieldName(attribute.name)] = attribute.description

    return fields
