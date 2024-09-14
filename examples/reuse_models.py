import logging

import click
from pydantic import BaseModel

from pydanclick import PydanclickConfig, from_pydantic


class LoggingConfig(BaseModel):
    """Logging configuration.

    Attributes:
        level: logging level
        filename: name of log file
        record_format: logging format
    """

    level: int = logging.INFO
    filename: str = "app.log"
    record_format: str = "%(message)s"

    __pydanclick__ = PydanclickConfig(prefix="log", shorten={"level": "-l"})


@click.group()
def cli():
    pass


@cli.command()
@from_pydantic(LoggingConfig)
def foo(logging_config: LoggingConfig):
    click.echo(logging_config.model_dump_json(indent=2))


@cli.command()
@from_pydantic(LoggingConfig, prefix="logging", parse_docstring=False)
def bar(logging_config: LoggingConfig):
    click.echo(logging_config.model_dump_json(indent=2))


if __name__ == "__main__":
    cli()
