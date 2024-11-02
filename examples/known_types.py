from typing import Optional

import click
from pydantic import BaseModel, EmailStr, HttpUrl, NameEmail, PostgresDsn, SecretStr
from pydantic.networks import IPvAnyAddress, IPvAnyInterface, IPvAnyNetwork

from pydanclick import from_pydantic


class KnownTypes(BaseModel):
    secret: Optional[SecretStr] = None
    url: Optional[HttpUrl] = None
    postgres_dsn: Optional[PostgresDsn] = None
    email: Optional[EmailStr] = None
    name_email: Optional[NameEmail] = None
    ip: Optional[IPvAnyAddress] = None
    net: Optional[IPvAnyNetwork] = None
    iface: Optional[IPvAnyInterface] = None


@click.command()
@from_pydantic(KnownTypes)
def cli(known_types: KnownTypes):
    """An example showing known Pydantic types support."""
    click.echo(known_types.model_dump_json(indent=2, exclude_none=True))


if __name__ == "__main__":
    cli()
