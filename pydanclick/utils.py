import re

_CAMEL_CASE_PATTERN = re.compile(r"(?<!^)(?=[A-Z])")


def camel_case_to_snake_case(name: str) -> str:
    """Convert camel case name to snake case.

    >>> camel_case_to_snake_case('FooBar')
    'foo_bar'

    """
    return _CAMEL_CASE_PATTERN.sub("_", name).lower()


def snake_case_to_kebab_case(name: str) -> str:
    """Convert snake case or dotted name to kebab case.

    >>> snake_case_to_kebab_case('a_b')
    'a-b'

    >>> snake_case_to_kebab_case('a.b')
    'a-b'

    """
    return name.lower().replace("_", "-").replace(".", "-")


def kebab_case_to_snake_case(name: str) -> str:
    """Convert kebab case to snake case.

    >>> kebab_case_to_snake_case('a-b')
    'a_b'

    """
    return name.replace("-", "_")


def strip_option_name(name: str) -> str:
    """Strip leading and trailing dashes from an option name.

    >>> strip_option_name('-a')
    'a'

    >>> strip_option_name('--foo-bar-')
    'foo-bar'

    """
    return re.sub("-+$", "", re.sub("^-+", "", name))
