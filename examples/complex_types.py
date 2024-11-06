from pathlib import Path
from typing import Literal

import click
from pydantic import BaseModel, Field

from pydanclick import from_pydantic


class RunConfig(BaseModel):
    """Configure how to run your container.

    Attributes:
        image: image name
        mounts: how to mount data on your container, as triples `(mount_type, src, dst)`
        ports: port binding
    """

    image: str
    mounts: list[tuple[Literal["bind", "volume", "tmpfs"], Path, Path]] = Field(default_factory=list)
    ports: dict[int, int] = Field(default_factory=dict)


@click.command()
@from_pydantic("config", RunConfig)
def cli(config: RunConfig):
    """A fake Docker client."""
    # Here, we receive an already validated Pydantic object.
    click.echo(config.model_dump_json(indent=2))


if __name__ == "__main__":
    cli()
