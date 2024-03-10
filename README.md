# pydanclick

<!-- these tags are used by `pymarkdownx.snippets` to include some parts of the readme in the Mkdocs documentation -->
<!-- --8<-- [start:overview] -->

![Release](https://img.shields.io/github/v/release/felix-martel/pydanclick)
![Build status](https://img.shields.io/github/actions/workflow/status/felix-martel/pydanclick/main.yml?branch=main)
![codecov](https://codecov.io/gh/felix-martel/pydanclick/branch/main/graph/badge.svg)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pydanclick)
![License](https://img.shields.io/github/license/felix-martel/pydanclick)

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
    # Here, we receive an already validated Pydantic object.
    click.echo(config.model_dump_json(indent=2))
```

```shell
~ python my_app.py --help
Usage: my_app.py [OPTIONS]

Options:
  --early-stopping / --no-early-stopping
  --lr FLOAT RANGE                [x>0]
  --epochs INTEGER                [required]
  --help                          Show this message and exit.
```

<!-- --8<-- [end:overview] -->

- Take a tour of the features below
- Find examples in the `examples/` folder
- Read the **[📚 Documentation](https://felix-martel.github.io/pydanclick/)**

<!-- --8<-- [start:features] -->

## Features

### Use native Click types

The following types are converted to native Click types:

| Pydantic type                            | Converted to         |
| :--------------------------------------- | :------------------- |
| `bool`                                   | `click.BOOL`         |
| `str`                                    | `click.STRING`       |
| `int`                                    | `click.INT`          |
| `float`                                  | `click.FLOAT`        |
| `Annotated[int, Field(lt=..., ge=...)`   | `click.IntRange()`   |
| `Annotated[float, Field(lt=..., ge=...)` | `click.FloatRange()` |
| `pathlib.Path`                           | `click.Path()`       |
| `uuid.UUID`                              | `click.UUID`         |
| `datetime.datetime`, `datetime.date`     | `click.DateTime()`   |
| `Literal`                                | `click.Choice`       |

Complex container types such as lists or dicts are also supported: they must be passed as JSON strings, and will be validated through Pydantic `TypeAdapter.validate_json` method:

```shell
--arg1 '[1, 2, 3]' --arg2 '{"a": bool, "b": false}'
```

In any case, Pydantic validation will run during model instantiation.

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

will give:

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

### Document options

Options added with `pydanclick.from_pydantic` will appear in the command help page.

**From docstrings**: if `griffe` is installed, model docstring will be parsed and the _Attributes_ section will be used to document options automatically (you can use `pip install pydanclick[griffe]` to install it). Use `docstring_tyle` to choose between `google`, `numpy` and `sphinx` coding style. Disable docstring parsing by passing `parse_docstring=False`.

**From field description**: `pydanclick` supports the [`Field(description=...)`](https://docs.pydantic.dev/latest/api/fields/#pydantic.fields.Field) syntax from Pydantic. If specified, it will take precedence over the docstring description.

**Explicitly**: you can always specify a custom help string for a given field by using `extra_options={"my_field": {"help": "my help string"}}` where `my_field` is the name of your field.

Here are these three methods in action:

```python
class Baz(BaseModel):
    """Some demo model.

    Attributes:
        a: this comes from the docstring (requires griffe)
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
  --a INTEGER  this comes from the docstring (requires griffe)
  --b INTEGER  this comes from the field description
  --c INTEGER  this comes from the `extra_options`
  --help       Show this message and exit.
```

### Customize option names

Specify option names with `rename` and short option names with `shorten`:

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

Note that `prefix` won't be prepended to option names passed with `rename` or `shorten`.

### Pass extra parameters

Use `extra_options` to pass extra parameters to `click.option` for a given field.

For example, in the following code, the user will be prompted for the value of `a`:

```python
@click.command()
@from_pydantic("foo", Foo, extra_options={"a": {"prompt": True}})
def cli(foo: Foo):
    pass
```

### Add nested models

Nested Pydantic models are supported, with arbitrary nesting level.
Option names will be built by joining all parent names and the field names itself with dashes.

```python
class Left(BaseModel):
    x: int

class Right(BaseModel):
    x: int

class Root(BaseModel):
    left: Left
    right: Right
    x: int

@click.command()
@from_pydantic("root", Root)
def cli(root: Root):
    pass
```

will give:

```shell
~ python cli.py --help
Usage: cli.py [OPTIONS]

Options:
  --left-x INTEGER   [required]
  --right-x INTEGER  [required]
  --x INTEGER        [required]
  --help             Show this message and exit.
```

To use `rename`, `shorten`, `exclude`, `extra_options` with a nested field, use its _dotted name_, e.g. `left.x` or `right.x`. Note that the alias of a field will apply to all its sub-fields:

```python
@click.command()
@from_pydantic("root", Root, rename={"right": "--the-other-left"})
def cli(root: Root):
    pass
```

will give:

```shell
~ python cli.py --help
Usage: cli.py [OPTIONS]

Options:
  --left-x INTEGER            [required]
  --the-other-left-x INTEGER  [required]
  --x INTEGER                 [required]
  --help                      Show this message and exit.
```

<!-- --8<-- [end:features] -->

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

<!--  --8<-- [start:limitations] -->

## Limitations

`pydanclick` doesn't support (yet!):

- Pydantic v1
- converting fields to arguments, instead of options
- fields annotated with union of Pydantic models can only be used with JSON inputs, instead of properly merging all sub-fields
- custom argument validators

Other missing features:

- Reading model from file
- Specifying all field-specific options directly in the Pydantic model (would allow easier re-use)
- Most Click features should be supported out-of-the-box through the `extra_options` parameter. However, most of them aren't tested
- Click and Pydantic both include validation logic. In particular, Click support custom `ParamType`, validation callbacks and `BadParameter` errors: it's not clear if we want to fully rely on Pydantic or on Click or on a mixture of both
- populating Pydantic fields from existing options or arguments (combined with `exclude`, it will provide a complete escape hatch to bypass Pydantclick when needed)
- attaching Pydanclick arguments directly to the model class, to avoid duplication when re-using a model in multiple commands

<!--  --8<-- [end:limitations] -->

---

Repository initiated with [fpgmaas/cookiecutter-poetry](https://github.com/fpgmaas/cookiecutter-poetry).
