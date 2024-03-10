# Nested Example

In this third example, our Pydantic model itself contains Pydantic models. Nested fields can be overridden from the command-line:

```python
--8<--
nested.py
--8<--
```

```shell
~ python examples/nested.py --help                                                                                                                               <aws:tooling>
Usage: nested.py [OPTIONS]

Options:
  --foo-a INTEGER       first letter
  --foo-b / --no-foo-b  second letter
  --bar-a FLOAT         an argument
  --bar-b TEXT          another one
  --baz-c [a|b]         third letter
  --help                Show this message and exit.
```

Some observations:

- you can `rename` any field by using its _dotted name_ (here, `bar.baz`)
- same notation can be used for `exclude`, `shorten`, `extra_options`
- when a field is renamed, all its subfields are renamed, too
