from typing import Literal

import click
from pydantic import BaseModel, Field

from pydanclick import from_pydantic


class Foo(BaseModel):
    """Foo.

    Attributes:
        a: first letter
        b: second letter
    """

    a: int = 1
    b: bool = True


class Baz(BaseModel):
    """Baz.

    Attributes:
        c: third letter
    """

    c: Literal["a", "b"] = "a"


class Bar(BaseModel):
    """Bar.

    Attributes:
        a: an argument
        b: another one
        baz: a third one
    """

    a: float = 0.1
    b: str = "b"
    baz: Baz = Field(default_factory=Baz)


class Obj(BaseModel):
    """Obj.

    Attributes:
        foo: foo attribute
        bar: bar attribute
    """

    foo: Foo = Field(default_factory=Foo)
    bar: Bar = Field(default_factory=Bar)


@click.command()
@from_pydantic("obj", Obj, rename={"bar.baz": "baz"})
def cli(obj: Obj):
    click.echo(obj.model_dump_json(indent=2))


if __name__ == "__main__":
    cli()
