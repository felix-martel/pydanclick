from typing import Dict, List

import click
import pytest
from click.testing import CliRunner
from pydantic import BaseModel, ValidationError

from pydanclick import from_pydantic
from tests.base_models import Bar, Baz, Foo, Foos, MultipleFoos, NestedFoos, Obj, OptionalFoos, UnionFoos


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


def test_nested():
    @click.command()
    @from_pydantic("obj", Obj)
    def cli(obj: Obj):
        click.echo(obj.model_dump_json(indent=2))

    runner = CliRunner()
    result = runner.invoke(cli, ["--no-foo-b", "--bar-baz-c", "b", "--bar-a", "0.5"])
    print(result.output)
    assert Obj.model_validate_json(result.output) == Obj(foo=Foo(b=False), bar=Bar(a=0.5, baz=Baz(c="b")))


def test_list_field():
    class Foo(BaseModel):
        a: List[int]
        b: Dict[str, int]

    @click.command()
    @from_pydantic("foo", Foo)
    def cli(foo: Foo):
        assert foo.a == [1, 2, 3]
        assert foo.b == {"a": 1, "b": 2, "c": 3}

    result = CliRunner().invoke(cli, ["--a", "[1, 2, 3]", "--b", '{"a": 1, "b": 2, "c": 3}'])
    assert result.exit_code == 0


def test_from_pydantic_with_invalid_call():
    with pytest.raises(ValueError, match="`model` must be provided"):

        @from_pydantic("foo")
        def cli(foo):
            pass


def test_unpack_list():
    @click.command()
    @from_pydantic(Foos, unpack_list=True)
    def cli(foos: Foos):
        click.echo(foos.model_dump_json(indent=2))

    result = CliRunner().invoke(cli, ["--foos-a", "2"])
    assert Foos.model_validate_json(result.output) == Foos(foos=[Foo(a=2)])

    result = CliRunner().invoke(cli, ["--foos-a", "2", "--no-foos-b"])
    assert Foos.model_validate_json(result.output) == Foos(foos=[Foo(a=2, b=False)])

    result = CliRunner().invoke(cli, ["--foos-a", "2", "--foos-a", "3"])
    assert Foos.model_validate_json(result.output) == Foos(foos=[Foo(a=2), Foo(a=3)])

    with pytest.raises(ValidationError):
        CliRunner().invoke(cli, [], catch_exceptions=False)


def test_unpack_list_with_default_factory():
    @click.command()
    @from_pydantic("foos", OptionalFoos, unpack_list=True)
    def cli(foos: OptionalFoos):
        click.echo(foos.model_dump_json(indent=2))

    result = CliRunner().invoke(cli, [], catch_exceptions=False)
    assert OptionalFoos.model_validate_json(result.output) == OptionalFoos(foos=[])


def test_unpack_list_with_union():
    @click.command()
    @from_pydantic("foos", UnionFoos, unpack_list=True)
    def cli(foos: UnionFoos):
        click.echo(foos.model_dump_json(indent=2))

    result = CliRunner().invoke(cli, args=["--foobazs", '[{"a": 1}, {"c": "a"}]', "--foos-a", "2", "--foos-a", "3"])
    # First field `foobazs` is a list of union of Pydantic models and shouldn't be unpacked, whereas the second field
    # `foos` is a list of Pydantic models and thus should be unpacked
    assert UnionFoos.model_validate_json(result.output) == UnionFoos(
        foobazs=[Foo(a=1), Baz(c="a")], foos=[Foo(a=2), Foo(a=3)]
    )


def test_unpack_list_with_multiple_lists():
    @click.command()
    @from_pydantic("foos", MultipleFoos, unpack_list=True)
    def cli(foos: MultipleFoos):
        click.echo(foos.model_dump_json(indent=2))

    result = CliRunner().invoke(cli, args=["--foos-a", "2", "--foos-a", "3", "--bazs-c", "a", "--bazs-c", "b"])
    assert MultipleFoos.model_validate_json(result.output) == MultipleFoos(
        foos=[Foo(a=2), Foo(a=3)], bazs=[Baz(c="a"), Baz(c="b")]
    )


@pytest.mark.xfail(reason="`model_validate_kwargs()` doesn't support nested fields")
def test_unpack_list_with_nested_list():
    @click.command()
    @from_pydantic("nested", NestedFoos, unpack_list=True)
    def cli(nested: NestedFoos):
        click.echo(nested.model_dump_json(indent=2))

    result = CliRunner().invoke(cli, ["--nested-foos-a", "2", "--no-nested-foos-b", "--nested-foos-a", "3"])
    assert result.exit_code == 0
    assert NestedFoos.model_validate_json(result.output) == NestedFoos(nested=Foos(foos=[Foo(a=2, b=False), Foo(a=3)]))
