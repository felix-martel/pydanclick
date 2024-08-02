from typing import Dict, List

import click
import pytest
from click.testing import CliRunner
from pydantic import BaseModel

from pydanclick import from_pydantic
from tests.base_models import Bar, Baz, Foo, Obj


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
