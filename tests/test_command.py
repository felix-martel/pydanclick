import click
from click.testing import CliRunner

from pydanclick.command import add_options


def test_add_options():
    options = [click.Option(["--foo"]), click.Option(["--bar"])]

    def cli(foo, bar):
        click.echo(f"foo={foo}, bar={bar}")

    cli = click.command()(add_options(cli, options))
    runner = CliRunner()
    result = runner.invoke(cli, ["--foo", "abc", "--bar", "123"])
    assert result.output.strip() == "foo=abc, bar=123"
