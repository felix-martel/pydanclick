import pytest
from pydantic import BaseModel

from pydanclick.model.docstrings import parse_attribute_documentation
from pydanclick.types import FieldName

pytest.importorskip("griffe")


class ParentClass(BaseModel):
    """Parent class.

    Attributes:
        a: a from parent
        b: b from parent
    """

    a: str
    b: str


class ChildClass(ParentClass):
    """Child class.

    Attributes:
        b: b from child
        c: c from child
    """

    b: str
    c: str


def test_parse_attribute_documentation():
    attributes = parse_attribute_documentation(ChildClass)
    assert attributes == {
        FieldName("a"): "a from parent",
        FieldName("b"): "b from child",
        FieldName("c"): "c from child",
    }
