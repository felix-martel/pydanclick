import os
from typing import Optional

import click
from click.testing import CliRunner
from pydantic_settings import BaseSettings

from pydanclick import from_pydantic


def test_use_env():
    class Foo(BaseSettings):
        a: str = "default"
        b: Optional[int] = None

    @click.command()
    @from_pydantic("foo", Foo, defer_set_default=True)
    def cli(foo: Foo):
        assert foo.a == "new-value"
        assert foo.b == 1

    try:
        os.environ["A"] = "new-value"
        os.environ["B"] = "1"
        result = CliRunner().invoke(cli, [])
        assert result.exit_code == 0
    finally:
        del os.environ["A"]
        del os.environ["B"]


def test_use_cli():
    class Foo(BaseSettings):
        a: str = "default"
        b: Optional[int] = None

    @click.command()
    @from_pydantic("foo", Foo, defer_set_default=True)
    def cli(foo: Foo):
        assert foo.a == "new-value"
        assert foo.b == 3

    result = CliRunner().invoke(cli, ["--a", "new-value", "--b", "3"])
    assert result.exit_code == 0


def test_use_precedence():
    class Foo(BaseSettings):
        a: str = "default"
        b: Optional[int] = None

    @click.command()
    @from_pydantic("foo", Foo, defer_set_default=True)
    def cli(foo: Foo):
        assert foo.a == "new-cli-value"
        assert foo.b == 3

    try:
        os.environ["A"] = "new-env-value"
        os.environ["B"] = "2"
        result = CliRunner().invoke(cli, ["--a", "new-cli-value", "--b", "3"])
        assert result.exit_code == 0
    finally:
        del os.environ["A"]
        del os.environ["B"]


def test_defer_default():
    class Foo(BaseSettings):
        a: str = "default"
        b: Optional[int] = None

    @click.command()
    @from_pydantic("foo", Foo, defer_set_default=True)
    def cli(foo: Foo):
        assert foo.a == "default"
        assert foo.b is None

    result = CliRunner().invoke(cli, [])
    assert result.exit_code == 0


def test_use_env_no_defer():
    class Foo(BaseSettings):
        a: str = "default"
        b: Optional[int] = None

    @click.command()
    @from_pydantic("foo", Foo, defer_set_default=False)
    def cli(foo: Foo):
        assert foo.a == "default"
        assert foo.b == 1

    try:
        os.environ["A"] = "new-value"
        os.environ["B"] = "1"
        result = CliRunner().invoke(cli, [])
        assert result.exit_code == 0
    finally:
        del os.environ["A"]
        del os.environ["B"]


def test_use_cli_no_defer():
    class Foo(BaseSettings):
        a: str = "default"
        b: Optional[int] = None

    @click.command()
    @from_pydantic("foo", Foo, defer_set_default=False)
    def cli(foo: Foo):
        assert foo.a == "new-value"
        assert foo.b == 3

    result = CliRunner().invoke(cli, ["--a", "new-value", "--b", "3"])
    assert result.exit_code == 0


def test_use_precedence_no_defer():
    class Foo(BaseSettings):
        a: str = "default"
        b: Optional[int] = None

    @click.command()
    @from_pydantic("foo", Foo, defer_set_default=False)
    def cli(foo: Foo):
        assert foo.a == "new-cli-value"
        assert foo.b == 3

    try:
        os.environ["A"] = "new-env-value"
        os.environ["B"] = "2"
        result = CliRunner().invoke(cli, ["--a", "new-cli-value", "--b", "3"])
        assert result.exit_code == 0
    finally:
        del os.environ["A"]
        del os.environ["B"]


def test_defer_default_no_defer():
    class Foo(BaseSettings):
        a: str = "default"
        b: Optional[int] = None

    @click.command()
    @from_pydantic("foo", Foo, defer_set_default=False)
    def cli(foo: Foo):
        assert foo.a == "default"
        assert foo.b is None

    result = CliRunner().invoke(cli, [])
    assert result.exit_code == 0
