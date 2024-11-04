"""Analyze a Pydantic model and turn it into Click options."""

from pydanclick.model.known_types import register_pydanclick_string_type
from pydanclick.model.model_conversion import convert_to_click

__all__ = ("convert_to_click", "register_pydanclick_string_type")
