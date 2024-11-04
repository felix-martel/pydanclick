from pathlib import Path
from typing import Literal, Optional

import click
from pydantic import BaseModel, Field
from typing_extensions import Annotated

from pydanclick import PydanclickConfig, from_pydantic


class TrainingConfig(BaseModel):
    """Simple training config.

    Attributes:
    """

    epochs: int
    batch_size: int = 64
    log_file: Optional[Path] = None

    __pydanclick__ = PydanclickConfig(extra_options={"batch_size": {"default": 12}})


class OptimizerConfig(BaseModel):
    optimizer: Literal["sgd", "adam", "adamw", "adagrad"] = "adam"
    learning_rate: Annotated[float, Field(gt=0)] = 1e-2
    decay_steps: Annotated[int, Field(description="Attach a description directly in the field")] = 2_000
    decay_rate: Annotated[float, Field(gt=0, lt=1)] = 1e-4

    __pydanclick__ = PydanclickConfig(
        prefix="opt",
        rename={"optimizer": "--opt"},
        shorten={"learning_rate": "--lr", "optimizer": "-o"},
        exclude=["decay_rate"],
    )


class LossConfig(BaseModel):
    """Loss configuration.

    Attributes:
        func: loss function
        from_logits: if True, interpret `y` as logits
    """

    func: Literal["cross_entropy", "mse", "hinge"] = "cross_entropy"
    from_logits: bool = True

    __pydanclick__ = PydanclickConfig(
        prefix="loss",
        rename={"func": "--loss"},
        shorten={"func": "-l"},
        parse_docstring=False,
    )


class Config(BaseModel):
    verbose: bool
    training: TrainingConfig
    optimizer: OptimizerConfig
    loss: LossConfig


@click.command()
@click.option("--verbose/--no-verbose", default=False, help="Verbose output")
@from_pydantic(TrainingConfig)
@from_pydantic(OptimizerConfig)
@from_pydantic(LossConfig)
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
