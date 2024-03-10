# Example: Complex Types

Complex container types such as lists or dicts are supported: they must be passed as JSON strings, and will be parsed by Pydantic through the `TypeAdapter.validate_json` method.
Consider the following Pydantic model:

```python
--8<--
complex_types.py
--8<--
```

It can be ran with:

```shell
python examples/complex_types.py \
    --image foo \
    --mounts '[["tmpfs", "/foo/bar", "foo/"], ["bind", ".", "foo/"]]' \
    --ports '{"80":80, "8888":8888}'
```

_Pay attention to single quotes versus double quotes: quotes are required around the JSON strings to prevent shell extension, and JSON strings **must** use double quotes._

Such types as marked as `JSON STRING` in the Click documentation:

```shell
~ python examples/complex_types.py --help                                                                                                                        <aws:tooling>
Usage: complex_types.py [OPTIONS]

  A fake Docker client.

Options:
  --image TEXT          image name  [required]
  --mounts JSON STRING  how to mount data on your container, as triples
                        `(mount_type, src, dst)`
  --ports JSON STRING   port binding
  --help                Show this message and exit.
```

As of now, Pydanclick doesn't provide a mechanism to override this.
