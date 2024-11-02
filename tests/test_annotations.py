from pydantic import BaseModel
from typing_extensions import Annotated

from pydanclick.model.annotations import ClickOpts, ClickOptsSet


def test_merge_clickopts():
    o1 = ClickOpts(metavar="initial", show_envvar=True)
    o2 = ClickOpts(metavar="updated", show_default=True)

    merged = o1.merge(o2)

    assert merged == ClickOpts(metavar="updated", show_default=True, show_envvar=True)


def test_extract_and_merge_clickopts():
    class MyModel(BaseModel):
        myid: Annotated[int, ClickOpts(exclude=True)]
        string: Annotated[str, ClickOpts(metavar="STR"), ClickOpts(rename="str")]
        another: Annotated[str, ClickOpts(metavar="OTHER", rename="other")]
        integer: int

    opts = ClickOptsSet.from_model(MyModel)

    assert opts == ClickOptsSet(
        {
            "myid": ClickOpts(exclude=True),
            "string": ClickOpts(metavar="STR", rename="str"),
            "another": ClickOpts(metavar="OTHER", rename="other"),
        }
    )
