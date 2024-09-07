import click
import pytest
from pydantic.fields import FieldInfo

from pydanclick.model.field_collection import _Field
from pydanclick.model.field_conversion import convert_fields_to_options, get_option_name
from tests.conftest import assert_options_equals


def test_convert_fields_to_options():
    str_field = FieldInfo(annotation=str, default="")
    bool_field = FieldInfo(annotation=bool, default=True)
    fields = [
        _Field(name="a", dotted_name="foo.a", field_info=str_field, parents=("foo", "a")),
        _Field(name="b", dotted_name="foo.b", field_info=str_field, parents=("foo", "b")),
        _Field(name="a", dotted_name="bar.a", field_info=str_field, parents=("bar", "a")),
        _Field(name="b", dotted_name="bar.b", field_info=bool_field, parents=("bar", "b")),
        _Field(name="c", dotted_name="bar.baz.c", field_info=str_field, parents=("bar", "baz", "c")),
    ]
    _, options = convert_fields_to_options(
        fields,
        aliases={"foo.b": "foob", "bar": "rab"},
        shorten={"bar.baz.c": "-b"},
        extra_options={"bar.b": {"help": "help!"}},
    )
    assert_options_equals(
        options,
        [
            click.Option(["foo_a", "--foo-a"], type=str, default=""),
            click.Option(["foo_b", "--foob"], type=str, default=""),
            click.Option(["bar_a", "--rab-a"], type=str, default=""),
            click.Option(["bar_b", "--rab-b/--no-rab-b"], type=bool, default=True, help="help!"),
            click.Option(["bar_baz_c", "--rab-baz-c", "-b"], type=str, default=""),
        ],
    )


@pytest.mark.parametrize(
    "name, aliases, prefix, is_boolean, expected_result",
    [
        ("foo", {}, "", False, "--foo"),
        ("foo", {}, "", True, "--foo/--no-foo"),
        ("foo", {}, "--pref", False, "--pref-foo"),
        ("foo", {}, "--pref", True, "--pref-foo/--no-pref-foo"),
        ("foo_bar", {}, "", False, "--foo-bar"),
        ("foo_bar", {}, "", True, "--foo-bar/--no-foo-bar"),
        ("foo_bar", {}, "--pref", True, "--pref-foo-bar/--no-pref-foo-bar"),
        ("Foo", {}, "", False, "--foo"),
        ("foo.bar", {"foo": "--oof"}, "", False, "--oof-bar"),
        ("foo.bar", {"foo": "--oof"}, "", True, "--oof-bar/--no-oof-bar"),
        ("foo.bar", {"foo.bar": "--baz"}, "", False, "--baz"),
        ("foo.bar", {"foo.bar": "--on/--off"}, "", False, "--on/--off"),
        ("foo.bar", {"foo": "--oof", "foo.bar": "--baz"}, "", False, "--baz"),
        ("foo.bar", {"foo": "--oof", "foo.bar": "--baz"}, "--pref", False, "--baz"),
        ("foo.baz", {"foo": "--oof", "foo.bar": "--baz"}, "", False, "--oof-baz"),
        ("foo.baz", {"foo": "--oof", "foo.bar": "--baz"}, "--pref", False, "--oof-baz"),
        ("bar", {"foo": "--oof", "foo.bar": "--baz"}, "--pref", False, "--pref-bar"),
    ],
)
def test_get_option_name(name, aliases, prefix, is_boolean, expected_result):
    assert get_option_name(name, aliases=aliases, prefix=prefix, is_boolean=is_boolean) == expected_result


# TODO: ensure prefix is correctly prepended to the argument name
