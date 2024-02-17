from contextlib import nullcontext as does_not_raise
from typing import Literal, Union

import click
import pytest
from _pytest.python_api import RaisesContext
from click import BadParameter
from click.testing import CliRunner
from pydantic import BaseModel, Field
from typing_extensions import Annotated

from pydanclick import from_pydantic
from pydanclick.main import _get_type_from_field


class Config(BaseModel):
    a: int = 1
    b: str = "foo"


@click.command()
@from_pydantic("config", Config)
def cli(config: Config):
    print(config.model_dump_json())


def test_cli():
    runner = CliRunner()
    result = runner.invoke(cli, [], catch_exceptions=False)
    assert result.exit_code == 0
    assert Config.model_validate_json(result.output) == Config()


def test_get_type_from_field_with_unconstrained_int():
    class Foo(BaseModel):
        a: int

    click_type = _get_type_from_field(Foo.model_fields["a"])
    assert click_type == click.INT


def test_get_type_from_field_with_constrained_int():
    class Foo(BaseModel):
        a: Annotated[int, Field(ge=0)]

    click_type = _get_type_from_field(Foo.model_fields["a"])
    assert isinstance(click_type, click.IntRange)
    assert click_type.min == 0
    assert click_type.min_open is False


def maybe_raises(outcome):
    return outcome if isinstance(outcome, RaisesContext) else does_not_raise()


def error_or_value(outcome):
    if isinstance(outcome, RaisesContext):
        context = outcome
        assert_is_expected = lambda x: True
        return context, assert_is_expected
    else:

        def assert_is_expected(__x):
            assert __x == outcome

        return does_not_raise(), assert_is_expected


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
        (Union[float, str], "3.14", "3.14"),
        (list[str], None, None),
        (list[str], "[1, 2, 3, 4]", "[1, 2, 3, 4]"),
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
