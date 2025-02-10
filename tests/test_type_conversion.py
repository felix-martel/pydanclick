from typing import Annotated, Literal, Optional, Union

import click
import pytest
from click import BadParameter
from pydantic import BaseModel, Field

from pydanclick.model.type_conversion import _get_type_from_field
from tests.conftest import error_or_value


def test_get_type_from_field_with_unconstrained_int():
    class Foo(BaseModel):
        a: int

    click_type = _get_type_from_field(Foo.model_fields["a"])
    assert isinstance(click_type, click.types.IntParamType)


def test_get_type_from_field_with_optional_int():
    class Foo(BaseModel):
        a: Optional[int] = None

    click_type = _get_type_from_field(Foo.model_fields["a"])
    assert isinstance(click_type, click.types.IntParamType)


def test_get_type_from_field_with_optional_float():
    class Foo(BaseModel):
        a: Optional[float] = None

    click_type = _get_type_from_field(Foo.model_fields["a"])
    assert isinstance(click_type, click.types.FloatParamType)


def test_get_type_from_field_with_unconstrained_bool():
    class Foo(BaseModel):
        a: bool

    click_type = _get_type_from_field(Foo.model_fields["a"])
    assert isinstance(click_type, click.types.BoolParamType)


def test_get_type_from_field_with_constrained_int():
    class Foo(BaseModel):
        a: Annotated[int, Field(ge=0)]

    click_type = _get_type_from_field(Foo.model_fields["a"])
    assert isinstance(click_type, click.IntRange)
    assert click_type.min == 0
    assert click_type.min_open is False


@pytest.mark.parametrize(
    "annotation, raw_value, expected_outcome",
    [
        (int, 1, 1),
        (int, 1.2, 1),
        (Annotated[int, Field(ge=0)], -2, pytest.raises(BadParameter, match="not in the range x>=0")),
        (Annotated[int, Field(ge=0)], 0, 0),
        (Annotated[int, Field(ge=0)], 10, 10),
        (Annotated[int, Field(ge=0, le=10)], 10, 10),
        (Annotated[int, Field(gt=0, lt=10)], 0, pytest.raises(BadParameter)),
        (Annotated[int, Field(gt=0, lt=10)], 10, pytest.raises(BadParameter)),
        (Annotated[int, Field(gt=0, lt=10)], 5, 5),
        (Annotated[float, Field(ge=0)], -0.5, pytest.raises(BadParameter)),
        (Annotated[float, Field(ge=0)], 0, 0),
        (Annotated[float, Field(ge=0)], 0.5, 0.5),
        (Annotated[float, Field(ge=0, le=1)], 1, 1),
        (Annotated[float, Field(gt=0, lt=1)], 0, pytest.raises(BadParameter)),
        (Annotated[float, Field(gt=0, lt=1)], 1, pytest.raises(BadParameter)),
        (Annotated[float, Field(gt=0, lt=1)], 0.99, 0.99),
        (Literal["a", "b", "c"], "a", "a"),
        (Literal["a", "b", "c"], "c", "c"),
        (Literal["a", "b", "c"], "d", pytest.raises(BadParameter)),
        (bool, False, False),
        (bool, True, True),
        (bool, "yes", True),
        (bool, "1", True),
        (bool, "n", False),
        (bool, "123", pytest.raises(BadParameter)),
        (Annotated[bool, "foo_bar"], "yes", True),
        (Union[float, str], "3.14", 3.14),
        (list[str], "[]", []),
        (list[str], """["1", "2", "3", "4"]""", ["1", "2", "3", "4"]),
    ],
)
def test_get_type_from_field(annotation, raw_value, expected_outcome):
    class Foo(BaseModel):
        bar: annotation

    click_type = _get_type_from_field(Foo.model_fields["bar"])
    context, check_expected = error_or_value(expected_outcome)
    with context:
        converted_value = click_type.convert(raw_value, None, None)
        check_expected(converted_value)
