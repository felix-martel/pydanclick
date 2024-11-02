import json
from operator import attrgetter
from pathlib import Path

import pytest
from click.testing import CliRunner

from examples import complex, complex_types, known_types, simple


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
def test_complex_example(args, attr, expected_result):
    """Ensure the complex error works as expected."""
    runner = CliRunner()
    raw_result = runner.invoke(complex.cli, ["--epochs", "4", *args])
    assert raw_result.exit_code == 0
    result = complex.Config.model_validate_json(raw_result.output)
    assert attrgetter(attr)(result) == expected_result


def test_complex_example_help():
    runner = CliRunner()
    result = runner.invoke(complex.cli, ["--help"])
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


def test_complex_types_example_help():
    """Ensure the 'complex_types' examples help works."""
    for o in complex_types.cli.params:
        o.show_default = True
    runner = CliRunner()
    result = runner.invoke(complex_types.cli, ["--help"])
    assert result.exit_code == 0
    assert "--ports JSON STRING   port binding  [default: <class 'dict'>]" in result.output


@pytest.mark.parametrize(
    "args, expected",
    [
        ([], {}),
        (["--secret", "secret"], {"secret": "**********"}),
        (["--url", "https://docs.pydantic.dev"], {"url": "https://docs.pydantic.dev/"}),
        (["--name-email", "john.doe@acme.net"], {"name_email": "john.doe <john.doe@acme.net>"}),
        (["--ip", "::1", "--net", "127.0.0.0/8"], {"ip": "::1", "net": "127.0.0.0/8"}),
    ],
)
def test_known_types_example(args, expected):
    """Ensure the 'known_types' examples works."""
    runner = CliRunner()
    result = runner.invoke(known_types.cli, args)
    assert result.exit_code == 0
    assert json.loads(result.output) == expected


def test_known_types_example_help():
    """Ensure the 'known_types' help show customized metavars."""
    runner = CliRunner()
    result = runner.invoke(known_types.cli, ["--help"])
    assert result.exit_code == 0
    assert "--secret SECRET" in result.output
    assert "--url URL" in result.output
    assert "--ip IP" in result.output
