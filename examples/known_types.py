from typing import Optional

import click
from pydantic import BaseModel, EmailStr, HttpUrl, NameEmail, PostgresDsn, SecretStr
from pydantic.networks import IPvAnyAddress, IPvAnyInterface, IPvAnyNetwork
from pydantic_extra_types.color import Color
from pydantic_extra_types.mac_address import MacAddress

from pydanclick import from_pydantic, register_pydanclick_string_type

register_pydanclick_string_type(Color)
register_pydanclick_string_type(MacAddress, "mac")


class KnownTypes(BaseModel):
    secret: Optional[SecretStr] = None
    url: Optional[HttpUrl] = None
    postgres_dsn: Optional[PostgresDsn] = None
    email: Optional[EmailStr] = None
    name_email: Optional[NameEmail] = None
    ip: Optional[IPvAnyAddress] = None
    net: Optional[IPvAnyNetwork] = None
    iface: Optional[IPvAnyInterface] = None
    color: Optional[Color] = None
    mac: Optional[MacAddress] = None


@click.command()
@from_pydantic(KnownTypes)
def cli(known_types: KnownTypes):
    """An example showing known Pydantic types support."""
    click.echo(known_types.model_dump_json(indent=2, exclude_none=True))


if __name__ == "__main__":
    cli()
