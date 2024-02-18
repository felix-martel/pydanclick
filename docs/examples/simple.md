# Simple Example

In this first example, we use a single model and default values:

```python
--8<--
simple.py
--8<--
```

```shell
python examples/simple.py --help
Usage: simple.py [OPTIONS]

  A simple example with a few parameters and default behavior.

Options:
  --epochs INTEGER                number of epochs  [required]
  --lr FLOAT RANGE                learning rate  [x>0]
  --early-stopping / --no-early-stopping
                                  whether to stop training when validation
                                  loss stops decreasing
  --help                          Show this message and exit.
```

You can notice that:

- fields without default values are marked as `required`
- contraints are properly recognized by Click
- boolean fields are converted to boolean flags, as recommended by Click
