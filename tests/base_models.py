from typing import Literal

from pydantic import BaseModel, Field


class Foo(BaseModel):
    a: int = 1
    b: bool = True


class Baz(BaseModel):
    c: Literal["a", "b"] = "a"


class Bar(BaseModel):
    a: float = 0.1
    b: str = "b"
    baz: Baz = Field(default_factory=Baz)


class Obj(BaseModel):
    foo: Foo = Field(default_factory=Foo)
    bar: Bar = Field(default_factory=Bar)
