from ipaddress import IPv4Address, IPv4Interface, IPv4Network, IPv6Address, IPv6Interface, IPv6Network
from typing import List, Literal, Optional, Union

import click
import pytest
from click import BadParameter
from pydantic import BaseModel, Field, SecretBytes, SecretStr
from pydantic.networks import EmailStr, HttpUrl, IPvAnyAddress, IPvAnyInterface, IPvAnyNetwork, NameEmail, PostgresDsn
from typing_extensions import Annotated

from pydanclick.model.type_conversion import _get_type_from_field
from tests.conftest import error_or_value


def test_get_type_from_field_with_unconstrained_int():
    class Foo(BaseModel):
        a: int

    click_type = _get_type_from_field(Foo.model_fields["a"])
    assert isinstance(click_type, click.types.IntParamType)


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
        (List[str], "[]", []),
        (List[str], """["1", "2", "3", "4"]""", ["1", "2", "3", "4"]),
        # Pydantic types
        (SecretStr, "my-secret", SecretStr("my-secret")),
        (SecretBytes, "my-secret", SecretBytes(b"my-secret")),
        (HttpUrl, "https://docs.pydantic.dev/", HttpUrl("https://docs.pydantic.dev/")),
        (
            HttpUrl,
            "irc://docs.pydantic.dev/",
            pytest.raises(BadParameter, match="URL scheme should be 'http' or 'https'"),
        ),
        (
            PostgresDsn,
            "postgres://user:pass@localhost:5432/foobar",
            PostgresDsn("postgres://user:pass@localhost:5432/foobar"),
        ),
        (
            PostgresDsn,
            "redis://user:pass@localhost:5432/foobar",
            pytest.raises(BadParameter, match="URL scheme should be 'postgres'"),
        ),
        (EmailStr, "hello@world.net", "hello@world.net"),
        (EmailStr, "not-an-email", pytest.raises(BadParameter, match="not a valid email")),
        (NameEmail, "Hello World <hello@world.net>", NameEmail("Hello World", "hello@world.net")),
        (NameEmail, "not an email", pytest.raises(BadParameter, match="not a valid email")),
        (IPv4Address, "127.0.0.1", IPv4Address("127.0.0.1")),
        (IPv4Address, "::1", pytest.raises(BadParameter, match="not a valid IPv4 address")),
        (IPv6Address, "::1", IPv6Address("::1")),
        (IPv6Address, "127.0.0.1", pytest.raises(BadParameter, match="not a valid IPv6 address")),
        (IPvAnyAddress, "127.0.0.1", IPv4Address("127.0.0.1")),
        (IPvAnyAddress, "::1", IPv6Address("::1")),
        (IPvAnyAddress, "not-an-ip", pytest.raises(BadParameter, match="not a valid IPv4 or IPv6 address")),
        (IPv4Network, "127.0.0.0/8", IPv4Network("127.0.0.0/8")),
        (IPv4Network, "::1/128", pytest.raises(BadParameter, match="not a valid IPv4 network")),
        (IPv6Network, "::1", IPv6Network("::1/128")),
        (IPv6Network, "127.0.0.0/8", pytest.raises(BadParameter, match="not a valid IPv6 network")),
        (IPvAnyNetwork, "127.0.0.0/8", IPv4Network("127.0.0.0/8")),
        (IPvAnyNetwork, "::1/128", IPv6Network("::1/128")),
        (IPvAnyNetwork, "not-a-network", pytest.raises(BadParameter, match="not a valid IPv4 or IPv6 network")),
        (IPv4Interface, "127.0.0.0/8", IPv4Interface("127.0.0.0/8")),
        (IPv4Interface, "::1/128", pytest.raises(BadParameter, match="not a valid IPv4 interface")),
        (IPv6Interface, "::1", IPv6Interface("::1/128")),
        (IPv6Interface, "127.0.0.0/8", pytest.raises(BadParameter, match="not a valid IPv6 interface")),
        (IPvAnyInterface, "127.0.0.0/8", IPv4Interface("127.0.0.0/8")),
        (IPvAnyInterface, "::1/128", IPv6Interface("::1/128")),
        (IPvAnyInterface, "not-an-interface", pytest.raises(BadParameter, match="not a valid IPv4 or IPv6 interface")),
    ],
)
@pytest.mark.parametrize(
    "optional",
    [
        pytest.param(True, id="optional"),
        pytest.param(False, id="single-type"),
    ],
)
def test_get_type_from_field(annotation, raw_value, expected_outcome, optional):
    class Foo(BaseModel):
        if optional:
            bar: Optional[annotation] = None
        else:
            bar: annotation

    click_type = _get_type_from_field(Foo.model_fields["bar"])
    context, check_expected = error_or_value(expected_outcome)
    with context:
        converted_value = click_type.convert(raw_value, None, None)
        check_expected(converted_value)
