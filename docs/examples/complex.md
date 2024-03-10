# Example: Multiple Models

In this second example, we use multiple models in a single command:

```python
--8<--
complex.py
--8<--
```

```shell
~ python examples/complex.py --help
Usage: complex.py [OPTIONS]

  A slightly more complex examples with multiple models and various options.

Options:
  --verbose / --no-verbose        Verbose output
  --epochs INTEGER                [required]
  --batch-size INTEGER
  --log-file PATH
  -o, --opt [sgd|adam|adamw|adagrad]
  --opt-learning-rate, --lr FLOAT RANGE
                                  [x>0]
  --opt-decay-steps INTEGER       Attach a description directly in the field
  -l, --loss [cross_entropy|mse|hinge]
  --loss-from-logits / --no-loss-from-logits
  --help                          Show this message and exit.

```

You can notice that:

- `prefix` can be use to have different namespaces for different models
- fields can be excluded with `exclude`
- regular options can be used alongside `pydanclick`
- option names can be controlled with `rename` and `shorten
- docstring parsing can be disabled with `parse_docstring=False`
