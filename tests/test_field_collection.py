from pydanclick.model.field_collection import _Field, collect_fields
from tests.base_models import Bar, Baz, Foo, Foos, Obj


def test_collect_fields():
    fields = collect_fields(Obj)
    assert fields == [
        _Field(name="a", dotted_name="foo.a", field_info=Foo.model_fields["a"], parents=("foo", "a")),
        _Field(name="b", dotted_name="foo.b", field_info=Foo.model_fields["b"], parents=("foo", "b")),
        _Field(name="a", dotted_name="bar.a", field_info=Bar.model_fields["a"], parents=("bar", "a")),
        _Field(name="b", dotted_name="bar.b", field_info=Bar.model_fields["b"], parents=("bar", "b")),
        _Field(name="c", dotted_name="bar.baz.c", field_info=Baz.model_fields["c"], parents=("bar", "baz", "c")),
    ]


def test_collect_fields_with_exclude():
    fields = collect_fields(Obj, excluded_fields=["foo", "bar.b"])
    assert {field.dotted_name for field in fields} == {"bar.a", "bar.baz.c"}
    # TODO: test docstring parsing


def test_collect_fields_without_unpack_list():
    fields = collect_fields(Foos, unpack_list=False)
    assert fields == [_Field(name="foos", dotted_name="foos", field_info=Foos.model_fields["foos"], parents=("foos",))]


def test_collect_fields_with_unpack_list():
    fields = collect_fields(Foos, unpack_list=True)
    assert fields == [
        _Field(
            name="a",
            dotted_name="foos.a",
            field_info=Foo.model_fields["a"],
            parents=("foos", "a"),
            unpacked_from="foos",
        ),
        _Field(
            name="b",
            dotted_name="foos.b",
            field_info=Foo.model_fields["b"],
            parents=("foos", "b"),
            unpacked_from="foos",
        ),
    ]
