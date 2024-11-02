"""
Some custom [`click` parameter types][click.ParamType] for some known `Pydantic` types.
"""

from ipaddress import IPv4Address, IPv4Interface, IPv4Network, IPv6Address, IPv6Interface, IPv6Network
from typing import Annotated, Any, Optional, Type, Union

from click import Context, Parameter, ParamType
from click.types import StringParamType
from pydantic import NameEmail, SecretBytes, SecretStr, TypeAdapter, ValidationError
from pydantic.fields import FieldInfo
from pydantic.networks import EmailStr, IPvAnyAddress, IPvAnyInterface, IPvAnyNetwork
from pydantic_core import MultiHostUrl, Url
from typing_extensions import TypeAlias

Annotation: TypeAlias = Union[Annotated, Type[Any]]


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
    if not field.annotation:
        return
    annotation = Annotated[field.annotation, *field.metadata] if field.metadata else field.annotation
    if field_type in (SecretStr, SecretBytes):
        return pydantic_string_param_type("secret", annotation)
    elif field_type in (Url, MultiHostUrl):
        return pydantic_string_param_type("url", annotation)
    elif field_type in (EmailStr, NameEmail):
        return pydantic_string_param_type("email", annotation)
    elif field_type in (IPvAnyAddress, IPv4Address, IPv6Address):
        return pydantic_string_param_type("ip", annotation)
    elif field_type in (IPvAnyNetwork, IPv4Network, IPv6Network):
        return pydantic_string_param_type("network", annotation)
    elif field_type in (IPvAnyInterface, IPv4Interface, IPv6Interface):
        return pydantic_string_param_type("iface", annotation)
