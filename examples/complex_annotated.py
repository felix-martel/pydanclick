from pathlib import Path
from typing import Literal, Optional

import click
from pydantic import BaseModel, Field
from typing_extensions import Annotated

from pydanclick import ClickOpts, from_pydantic


class TrainingConfig(BaseModel):
    """Simple training config.

    Attributes:
    """

    epochs: int
    batch_size: Annotated[int, ClickOpts(default=12)] = 64
    log_file: Optional[Path] = None


class OptimizerConfig(BaseModel):
    optimizer: Annotated[Literal["sgd", "adam", "adamw", "adagrad"], ClickOpts(rename="--opt", shorten="-o")] = "adam"
    learning_rate: Annotated[float, Field(gt=0), ClickOpts(shorten="--lr")] = 1e-2
    decay_steps: Annotated[int, Field(description="Attach a description directly in the field")] = 2_000
    decay_rate: Annotated[float, Field(gt=0, lt=1), ClickOpts(exclude=True)] = 1e-4


class LossConfig(BaseModel):
    """Loss configuration.

    Attributes:
        func: loss function
        from_logits: if True, interpret `y` as logits
    """

    func: Annotated[
        Literal["cross_entropy", "mse", "hinge"], ClickOpts(rename="--loss"), ClickOpts(shorten="-l")
    ] = "cross_entropy"
    from_logits: bool = True


class Config(BaseModel):
    verbose: bool
    training: TrainingConfig
    optimizer: OptimizerConfig
    loss: LossConfig


@click.command()
@click.option("--verbose/--no-verbose", default=False, help="Verbose output")
@from_pydantic(TrainingConfig)
@from_pydantic(OptimizerConfig, prefix="opt")
@from_pydantic(LossConfig, prefix="loss", parse_docstring=False)
def cli(
    verbose: bool,
    training_config: TrainingConfig,
    optimizer_config: OptimizerConfig,
    loss_config: LossConfig,
):
    """A slightly more complex examples with multiple models and various options."""
    config = Config(verbose=verbose, training=training_config, optimizer=optimizer_config, loss=loss_config)
    click.echo(config.model_dump_json(indent=2))


if __name__ == "__main__":
    cli()
