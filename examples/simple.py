import click
from pydantic import BaseModel, Field
from typing_extensions import Annotated

from pydanclick import from_pydantic


class TrainingConfig(BaseModel):
    """Simple training config.

    Attributes:
        epochs: number of epochs
        lr: learning rate
        early_stopping: whether to stop training when validation loss stops decreasing
    """

    epochs: int
    lr: Annotated[float, Field(gt=0)] = 1e-4
    early_stopping: bool = False


@click.command()
@from_pydantic("config", TrainingConfig)
def cli(config: TrainingConfig):
    """A simple example with a few parameters and default behvior."""
    # Here, we receive an already validated Pydantic object.
    click.echo(config.model_dump_json(indent=2))


if __name__ == "__main__":
    cli()
