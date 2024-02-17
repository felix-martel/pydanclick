from pathlib import Path
from typing import Literal, Optional

import click
from pydantic import BaseModel, Field
from typing_extensions import Annotated

from pydanclick import from_pydantic


class TrainingConfig(BaseModel):
    """Simple training config.

    Attributes:
    """

    epochs: int
    batch_size: int = 64
    log_file: Optional[Path] = None


class OptimizerConfig(BaseModel):
    optimizer: Literal["sgd", "adam", "adamw", "adagrad"] = "adam"
    learning_rate: Annotated[float, Field(gt=0)] = 1e-2
    decay_steps: Annotated[int, Field(description="Attach a description directly in the field")] = 2_000
    decay_rate: Annotated[float, Field(gt=0, lt=1)] = 1e-4


class LossConfig(BaseModel):
    """Loss configuration.

    Attributes:
        func: loss function
        from_logits: if True, interpret `y` as logits
    """

    func: Literal["cross_entropy", "mse", "hinge"] = "cross_entropy"
    from_logits: bool = True


class Config(BaseModel):
    verbose: bool
    training: TrainingConfig
    optimizer: OptimizerConfig
    loss: LossConfig


@click.command()
@click.option("--verbose/--no-verbose", default=False, help="Verbose output")
@from_pydantic("training_config", TrainingConfig, extra_options={"batch_size": {"default": 12}})
@from_pydantic(
    "optimizer_config",
    OptimizerConfig,
    prefix="opt",
    rename={"optimizer": "--opt"},
    shorten={"learning_rate": "--lr", "optimizer": "-o"},
    exclude=["decay_rate"],
)
@from_pydantic(
    "loss_config", LossConfig, prefix="loss", rename={"func": "--loss"}, shorten={"func": "-l"}, parse_docstring=False
)
def cli(
    verbose: bool,
    training_config: TrainingConfig,
    optimizer_config: OptimizerConfig,
    loss_config: LossConfig,
):
    """A simple example with a few parameters and default behvior."""
    config = Config(verbose=verbose, training=training_config, optimizer=optimizer_config, loss=loss_config)
    click.echo(config.model_dump_json(indent=2))


if __name__ == "__main__":
    cli()
