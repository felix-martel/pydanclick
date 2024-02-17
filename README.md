# pydanclick

[![Release](https://img.shields.io/github/v/release/felix-martel/pydanclick)](https://img.shields.io/github/v/release/felix-martel/pydanclick)
[![Build status](https://img.shields.io/github/actions/workflow/status/felix-martel/pydanclick/main.yml?branch=main)](https://github.com/felix-martel/pydanclick/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/felix-martel/pydanclick/branch/main/graph/badge.svg)](https://codecov.io/gh/felix-martel/pydanclick)
[![Commit activity](https://img.shields.io/github/commit-activity/m/felix-martel/pydanclick)](https://img.shields.io/github/commit-activity/m/felix-martel/pydanclick)
[![License](https://img.shields.io/github/license/felix-martel/pydanclick)](https://img.shields.io/github/license/felix-martel/pydanclick)

Use Pydantic models as Click options.

## Getting started

Install:

```sh
pip install pydanclick
```

Let's assume you have a Pydantic model:

```python
class TrainingConfig(BaseModel):
    epochs: int
    lr: Annotated[float, Field(gt=0)] = 1e-4
    early_stopping: bool = False
```

Add all its fields as options in your Click command:

```python
from pydanclick import from_pydantic

@click.command()
@from_pydantic("config", TrainingConfig)
def cli(config: TrainingConfig):
    """A simple example with a few parameters and default behavior."""
    # Here, we receive an already validated Pydantic object.
    click.echo(config.model_dump_json(indent=2))
```

```shell
~ python my_app.py --help
Usage: my_app.py [OPTIONS]

  A simple example with a few parameters and default behvior.

Options:
  --early-stopping / --no-early-stopping
  --lr FLOAT RANGE                [x>0]
  --epochs INTEGER                [required]
  --help                          Show this message and exit.
```

- Find examples in the `examples/` folder
- See the [API Reference](#api-reference) for the full list of options

## Features

### Use native Click types

The following types are converted to native Click types:

| Pydantic type                                        | Converted to         |
| :--------------------------------------------------- | :------------------- |
| `bool`                                               | `click.BOOL`         |
| `str`                                                | `click.STRING`       |
| `int`                                                | `click.INT`          |
| `float`                                              | `click.FLOAT`        |
| `conint`, `Annotated[int, Field(lt=..., ge=...)`     | `click.IntRange()`   |
| `confloat`, `Annotated[float, Field(lt=..., ge=...)` | `click.FloatRange()` |
| `pathlib.Path`                                       | `click.Path()`       |
| `uuid.UUID`                                          | `click.UUID`         |
| `datetime.datetime`, `datetime.date`                 | `click.DateTime()`   |
| `Literal`                                            | `click.Choice`       |

More complex validators will be handled through Pydantic usual validation logic: once handled by Click, all arguments will be used to initialize Pydantic model.

### Add multiple models

`pydanclick.from_pydantic` can be called several times with different models.

Use the `prefix` parameter to namespace the options from different models:

```python
class Foo(BaseModel):
    a: str = ""
    b: str = ""

class Bar(BaseModel):
    x: int = 0
    y: int = 0

@click.command()
@from_pydantic("foo", Foo, prefix="foo")
@from_pydantic("bar", Bar, prefix="bar")
def cli(foo: Foo, bar: Bar):
    pass
```

will give

```
~ python cli.py
Usage: cli.py [OPTIONS]

Options:
  --foo-a TEXT
  --foo-b TEXT
  --bar-x INTEGER
  --bar-y INTEGER
  --help           Show this message and exit.
```

### Add regular options and arguments

`pydanclick` can be used alongside regular options and arguments:

```python
@click.command()
@click.argument("arg")
@click.option("--option")
@from_pydantic("foo", Foo)
def cli(arg, option, foo: Foo):
    pass
```

will give:

```
~ python cli.py
Usage: cli.py [OPTIONS] ARG

Options:
  --option TEXT
  --a TEXT
  --b TEXT
  --help         Show this message and exit.
```

### Option documentation

Options added with `pydanclick.from_pydantic` will appear in the command help page.

Model docstring is used to document options automatically (requires `griffe`, e.g. `pip install pydanclick[griffe]`). Enabled by default, use `parse_docstring=False` to disable. Use `docstring_tyle` to choose between `google`, `numpy` and `sphinx` coding style.

`pydanclick` also supports the `Field(description=...)` syntax from Pydantic.

To specify custom documentation for a given field, use `extra_options={"my_field": "my help string"}`.

Provided `griffe` is installed, using:

```python
class Baz(BaseModel):
    """Some demo model.

    Attributes:
        a: this comes from the docstring
    """

    a: int = 0
    b: Annotated[int, Field(description="this comes from the field description")] = 0
    c: int = 0


@click.command()
@from_pydantic("baz", Baz, extra_options={"c": {"help": "this comes from the `extra_options`"}})
def cli(baz: Baz):
    pass
```

will give:

```
~ python cli.py --help
Usage: cli.py [OPTIONS]

Options:
  --a INTEGER  this comes from the docstring
  --b INTEGER  this comes from the field description
  --c INTEGER  this comes from the `extra_options`
  --help       Show this message and exit.
```

### Customize option names

Specify option names with `prefix` and short option names with `shorten`:

```python
@click.command()
@from_pydantic("foo", Foo, rename={"a": "--alpha", "b": "--beta"}, shorten={"a": "-A", "b": "-B"})
def cli(foo: Foo):
    pass
```

will give:

```
~ python cli.py --help
Usage: cli.py [OPTIONS]

Options:
  -A, --alpha TEXT
  -B, --beta TEXT
  --help            Show this message and exit.
```

### Pass extra parameters

Use `extra_options` to pass extra parameters to `click.option` for a given field.

## API Reference

**Functions:**

- [**from_pydantic**](#pydanclick.main.from_pydantic) – Decorator to add fields from a Pydantic model as options to a Click command.

### pydanclick.from_pydantic

```python
from_pydantic(__var, model, *, exclude=(), rename=None, shorten=None, prefix='', parse_docstring=True, docstring_style='google', extra_options=None)
```

Decorator to add fields from a Pydantic model as options to a Click command.

**Example:**

```python
@click.command()
@pydanclick.from_pydantic("arg_name", SomePydanticModel)
def my_command(arg_name: SomePydanticModel):
    assert isinstance(arg_name, SomePydanticModel)  # True
```

**Parameters:**

- **\_\_var** (<code>[str](#str)</code>) – name of the variable that will receive the Pydantic model in the decorated function
- **model** (<code>[type](#type)\[[BaseModel](#pydantic.BaseModel)\]</code>) – Pydantic model
- **exclude** (<code>[Sequence](#collections.abc.Sequence)\[[str](#str)\]</code>) – field names that won't be added to the command
- **rename** (<code>[dict](#dict)\[[str](#str), [str](#str)\] | None</code>) – a mapping from field names to command line option names (this will override any prefix). Option names
  must start with two dashes
- **shorten** (<code>[dict](#dict)\[[str](#str), [str](#str)\] | None</code>) – a mapping from field names to short command line option names. Option names must start with one dash
- **prefix** (<code>[str](#str)</code>) – a prefix to add to option names (without any dash)
- **parse_docstring** (<code>[bool](#bool)</code>) – if True and `griffe` is installed, parse the docstring of the Pydantic model and pass argument
  documentation to the Click `help` option
- **docstring_style** (<code>[str](#str)</code>) – style of the docstring (`google`, `numpy` or `sphinx`). Ignored if `parse_docstring` is False
- **extra_options** (<code>[dict](#dict)\[[str](#str), [\_ParameterKwargs](#pydanclick.main._ParameterKwargs)\] | None</code>) – a mapping from field names to a dictionary of options passed to the `click.option()` function

**Returns:**

- <code>[Callable](#collections.abc.Callable)\[\[[Callable](#collections.abc.Callable)\[..., T\]\], [Callable](#collections.abc.Callable)\[..., T\]\]</code> – a decorator that adds options to a function

## Contributing

Install the environment and the pre-commit hooks with

```bash
make install
```

Run tests with:

```shell
pytest
```

## Limitations

`pydanclick` doesn't support (yet!):

- Nested models
- Container types (tuples, lists, dicts) or other complex types
- Converting fields to arguments, instead of options
- Some union types won't work
- Python `<3.11`

Other missing features:

- Reading model from file
- Specifying all field-specific options directly in the Pydantic model (would allow easier re-use)
- Most Click features should be supported out-of-the-box through the `extra_options` parameter. However, most of them aren't tested
- Click and Pydantic both include validation logic. In particular, Click support custom `ParamType`, validation callbacks and `BadParameter` errors: it's not clear if we want to fully rely on Pydantic or on Click or on a mixture of both

---

Repository initiated with [fpgmaas/cookiecutter-poetry](https://github.com/fpgmaas/cookiecutter-poetry).
