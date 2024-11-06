"""
Some custom [`click` parameter types][click.ParamType] for some known `Pydantic` types.
"""

from ipaddress import IPv4Address, IPv4Interface, IPv4Network, IPv6Address, IPv6Interface, IPv6Network
from typing import Any, Dict, Optional, Type, Union

from click import Context, Parameter, ParamType
from click.types import StringParamType
from pydantic import NameEmail, SecretBytes, SecretStr, TypeAdapter, ValidationError
from pydantic.fields import FieldInfo
from pydantic.networks import EmailStr, IPvAnyAddress, IPvAnyInterface, IPvAnyNetwork
from pydantic_core import MultiHostUrl, Url
from typing_extensions import Annotated, TypeAlias

from pydanclick.utils import camel_case_to_snake_case

Annotation: TypeAlias = Union[Annotated[Any, ...], Type[Any]]

TYPES_NAMES: Dict[Annotation, str] = {
    SecretStr: "secret",
    SecretBytes: "secret",
    Url: "url",
    MultiHostUrl: "url",
    EmailStr: "email",
    NameEmail: "email",
    IPvAnyAddress: "ip",
    IPv4Address: "ip",
    IPv6Address: "ip",
    IPvAnyNetwork: "network",
    IPv4Network: "network",
    IPv6Network: "network",
    IPvAnyInterface: "iface",
    IPv4Interface: "iface",
    IPv6Interface: "iface",
}


class PydanticStringParam(StringParamType):
    """Base class for Pydantic custom param types parseable from string"""

    annotation: Annotation
    """The pydantic type used for validation"""

    def __repr__(self) -> str:
        return self.name.upper()

    def convert(self, value: Any, param: Optional[Parameter], ctx: Optional[Context]) -> Any:
        try:
            return TypeAdapter(self.annotation).validate_python(value)
        except ValidationError as e:
            # For strings based types there is always a single error.
            # so we take the first message only to avoid Pydantic boilerplate
            self.fail(str(e.errors()[0]["msg"]), param, ctx)


def pydantic_string_param_type(name: str, annotation: Annotation) -> ParamType:
    new_type: Type[PydanticStringParam] = type(
        f"{name.title()}ParamType", (PydanticStringParam,), {"name": name, "annotation": annotation}
    )
    return new_type()


def get_pydantic_paramtype(field_type: Optional[Type], field: FieldInfo) -> Optional[ParamType]:
    """
    Get a customised ParamType for Pydantic known types
    """
    if not (field_type and field.annotation):
        return None
    annotation: Annotation = field.annotation
    for metadata in field.metadata:
        annotation = Annotated[annotation, metadata]
    if name := TYPES_NAMES.get(field_type):
        return pydantic_string_param_type(name, annotation)
    return None


def register_pydanclick_string_type(new_type: Type, name: Optional[str] = None) -> None:
    """
    Register a custom Pydantic type known to be parseable as a string.

    Args:
        new_type: The type to register.
        name: an optional that will serve as default metavar.
    """
    if not name:
        name = camel_case_to_snake_case(new_type.__name__)
    TYPES_NAMES[new_type] = name
