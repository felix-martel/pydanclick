from pydantic import BaseModel

from pydanclick.model.config import PydanclickConfig, _Config, get_config


def test_get_config_without_parameters_and_config():
    class Foo(BaseModel):
        a: int
        b: str = "123"

    assert get_config(Foo) == _Config(
        exclude=set(),
        rename=None,
        shorten=None,
        parse_docstring=True,
        docstring_style="google",
        prefix=None,
        extra_options=None,
    )


def test_get_config_with_config_and_no_parameters():
    class Foo(BaseModel):
        a: int
        b: str = "123"

        __pydanclick__ = {
            "exclude": ["a"],
            "parse_docstring": False,
        }

    assert get_config(Foo) == _Config(
        exclude={"a"},
        rename=None,
        shorten=None,
        parse_docstring=False,
        docstring_style="google",
        prefix=None,
        extra_options=None,
    )


def test_get_config_with_config_and_parameters():
    class Foo(BaseModel):
        a: int
        b: str = "123"

        __pydanclick__ = {
            "exclude": ["a"],
            "parse_docstring": False,
        }

    assert get_config(Foo, exclude=["b"], extra_options={"a": {"prompt": True}}) == _Config(
        exclude={"b"},
        rename=None,
        shorten=None,
        parse_docstring=False,
        docstring_style="google",
        prefix=None,
        extra_options={"a": {"prompt": True}},
    )
    assert get_config(Foo, parse_docstring=True).parse_docstring is True


def test_get_config_with_validated_config():
    class Foo(BaseModel):
        a: int
        b: str = "123"

        __pydanclick__ = PydanclickConfig(exclude=["a"], parse_docstring=False)

    assert get_config(Foo, exclude=["b"], extra_options={"a": {"prompt": True}}) == _Config(
        exclude={"b"},
        rename=None,
        shorten=None,
        parse_docstring=False,
        docstring_style="google",
        prefix=None,
        extra_options={"a": {"prompt": True}},
    )
