import pytest

from pydanclick.model.validation import _pack_dict


@pytest.mark.parametrize(
    "input_value, expected_value",
    [
        # Same length
        ({"a": [1, 2], "b": ["a", "b"]}, [{"a": 1, "b": "a"}, {"a": 2, "b": "b"}]),
        # Different lengths
        ({"a": [1, 2], "b": ["a"]}, [{"a": 1, "b": "a"}, {"a": 2}]),
        # One empty
        ({"a": [1, 2], "b": []}, [{"a": 1}, {"a": 2}]),
    ],
)
def test__pack_dict(input_value, expected_value):
    packed_value = _pack_dict(input_value)
    assert packed_value == expected_value
