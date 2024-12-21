from typing import Literal, Union

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


class Foos(BaseModel):
    foos: list[Foo]


class OptionalFoos(BaseModel):
    foos: list[Foo] = Field(default_factory=list)


class UnionFoos(BaseModel):
    foobazs: list[Union[Foo, Baz]]
    foos: list[Foo]


class MultipleFoos(BaseModel):
    foos: list[Foo]
    bazs: list[Baz]


class NestedFoos(BaseModel):
    nested: Foos
