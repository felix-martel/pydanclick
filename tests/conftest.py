from contextlib import nullcontext as does_not_raise
from typing import Iterable

import click
from _pytest.python_api import RaisesContext


def assert_option_equals(actual: click.Option, expected: click.Option) -> None:
    assert actual.__dict__ == expected.__dict__


def assert_options_equals(actuals: Iterable[click.Option], expecteds: Iterable[click.Option]) -> None:
    actuals = sorted(actuals, key=lambda o: o.name)
    expecteds = sorted(expecteds, key=lambda o: o.name)
    assert len(actuals) == len(expecteds), f"Different number of options: {len(actuals)} != {len(expecteds)}"
    for i, (actual, expected) in enumerate(zip(actuals, expecteds)):
        assert (
            actual.__dict__ == expected.__dict__
        ), f"Different option at index {i}: {actual.__dict__} != {expected.__dict__}"


def maybe_raises(outcome):
    return outcome if isinstance(outcome, RaisesContext) else does_not_raise()


def error_or_value(outcome):
    if isinstance(outcome, RaisesContext):
        context = outcome
        assert_is_expected = lambda x: True
        return context, assert_is_expected
    else:

        def assert_is_expected(__x):
            assert __x == outcome

        return does_not_raise(), assert_is_expected
