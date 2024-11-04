import json
from operator import attrgetter
from pathlib import Path

import pytest
from click import Command
from click.testing import CliRunner

from examples import (
    complex,
    complex_annotated,
    complex_mixed,
    complex_model_config,
    complex_types,
    reuse_models,
    simple,
)


@pytest.mark.parametrize(
    "args, expected_results",
    [
        (["--epochs", "8"], {"epochs": 8, "lr": 1e-4, "early_stopping": False}),
        (["--epochs", "8", "--lr", "0.1", "--early-stopping"], {"epochs": 8, "lr": 0.1, "early_stopping": True}),
        (["--epochs", "8", "--lr", "0.1", "--no-early-stopping"], {"epochs": 8, "lr": 0.1, "early_stopping": False}),
    ],
)
def test_simple_example(args, expected_results):
    """Ensure the simple examples works."""
    runner = CliRunner()
    result = runner.invoke(simple.cli, args)
    assert result.exit_code == 0
    assert json.loads(result.output) == expected_results


@pytest.mark.parametrize(
    "args, expected_error",
    [
        ([], "Error: Missing option '--epochs'."),
        (["--epochs", "8", "--lr", "0"], "Error: Invalid value for '--lr': 0.0 is not in the range x>0."),
        (["--epochs", "8", "--early-stopping=yes"], "Error: Option '--early-stopping' does not take a value."),
    ],
)
def test_simple_example_with_invalid_args(args, expected_error):
    """Ensure the simple example fails when expected."""
    runner = CliRunner()
    result = runner.invoke(simple.cli, args, catch_exceptions=False)
    assert expected_error in result.output
    assert result.exit_code > 0


@pytest.fixture(
    params=[
        pytest.param(complex, id="complexe"),
        pytest.param(complex_annotated, id="annotated"),
        pytest.param(complex_model_config, id="model-config"),
        pytest.param(complex_mixed, id="mixed"),
    ]
)
def complex_cli(request: pytest.FixtureRequest) -> Command:
    return request.param.cli


@pytest.mark.parametrize(
    "args, attr, expected_result",
    [
        ([], "training.epochs", 4),
        (["--verbose"], "verbose", True),
        (["--epochs", "8"], "training.epochs", 8),
        (["--opt", "sgd"], "optimizer.optimizer", "sgd"),
        (["-o", "sgd"], "optimizer.optimizer", "sgd"),
        (["--opt", "sgd", "--opt-learning-rate", "0.1"], "optimizer.learning_rate", 0.1),
        (["--lr", "0.1"], "optimizer.learning_rate", 0.1),
        (["--loss", "mse"], "loss.func", "mse"),
        (["-l", "hinge"], "loss.func", "hinge"),
        (["--log-file", "foo/bar.log"], "training.log_file", Path("foo/bar.log")),
    ],
)
def test_complex_example(args, attr, expected_result, complex_cli: Command):
    """Ensure the complex error works as expected."""
    runner = CliRunner()
    raw_result = runner.invoke(complex_cli, ["--epochs", "4", *args])
    assert raw_result.exit_code == 0
    result = complex.Config.model_validate_json(raw_result.output)
    assert attrgetter(attr)(result) == expected_result


def test_complex_example_help(complex_cli: Command):
    runner = CliRunner()
    result = runner.invoke(complex_cli, ["--help"])
    # Ensure field description is added to the CLI documentation
    assert "Attach a description directly in the field" in result.output


@pytest.mark.parametrize(
    "args, expected_results",
    [
        ([], {}),
        (["--mounts", "[]"], {}),
        (["--mounts", '[["bind", ".", "."]]'], {"mounts": [["bind", ".", "."]]}),
        (["--ports", '{"80": 80, "8888": 8888}'], {"ports": {"80": 80, "8888": 8888}}),
    ],
)
def test_complex_types_example(args, expected_results):
    """Ensure the 'complex_types' examples works."""
    runner = CliRunner()
    result = runner.invoke(complex_types.cli, ["--image", "foo", *args])
    assert result.exit_code == 0
    assert json.loads(result.output) == {"image": "foo", "mounts": [], "ports": {}, **expected_results}


@pytest.mark.parametrize(
    "args, expected_results",
    [
        (["foo"], {}),
        (["bar"], {}),
        (["foo", "-l", "30"], {"level": 30}),
        (["foo", "--log-level", "30"], {"level": 30}),
        (["bar", "-l", "30"], {"level": 30}),
        (["bar", "--logging-level", "30"], {"level": 30}),
    ],
)
def test_reuse_models_example(args, expected_results):
    """Ensure the 'reuse_models' examples works."""
    runner = CliRunner()
    result = runner.invoke(reuse_models.cli, args)
    assert result.exit_code == 0
    assert json.loads(result.output) == {
        "filename": "app.log",
        "level": 20,
        "record_format": "%(message)s",
        **expected_results,
    }
