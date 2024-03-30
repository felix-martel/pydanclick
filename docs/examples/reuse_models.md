# Re-use models across commands

Here, we're using the `LoggingConfig` class in two different subcommands.
To avoid duplicating parameters, we attach a Pydanclick configuration object directly to the class:

```python hl_lines="22"
--8<--
reuse_models.py
--8<--
```

```shell
~ python examples/reuse_models.py foo --help                                                                                                       <aws:tooling>
Usage: reuse_models.py foo [OPTIONS]

Options:
  -l, --log-level INTEGER   logging level
  --log-filename TEXT       name of log file
  --log-record-format TEXT  logging format
  --help                    Show this message and exit.
```

```shell
~ python examples/reuse_models.py bar --help                                                                                                       <aws:tooling>
Usage: reuse_models.py bar [OPTIONS]

Options:
  -l, --logging-level INTEGER
  --logging-filename TEXT
  --logging-record-format TEXT
  --help                        Show this message and exit.
```

Notes:

- using `PydanclickConfig` is not required: a simple dict would work as well
- options defined in `__pydanclick__` can be overridden for a specific command
- all options to `from_pydantic` are supported
