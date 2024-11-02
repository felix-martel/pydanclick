from dataclasses import dataclass, fields, replace
from typing import Any, Dict, Optional, Type, Union, cast

from pydantic import BaseModel, RootModel
from typing_extensions import Self

from pydanclick.types import _ParameterKwargs

_PARAM_KEYS = _ParameterKwargs.__optional_keys__ | _ParameterKwargs.__required_keys__


@dataclass
class ClickOpts:
    """
    Type Annotation metadata for Click and Pydanclic specific options
    """

    default: Any = None
    prompt: Optional[Union[bool, str]] = None
    metavar: Optional[str] = None
    shorten: Optional[str] = None
    exclude: Optional[bool] = None
    rename: Optional[str] = None
    show_default: Optional[bool] = None
    show_envvar: Optional[bool] = None

    def merge(self, other: Self) -> Self:
        attrs = {
            field.name: value for field in fields(self.__class__) if (value := getattr(other, field.name)) is not None
        }
        return replace(self, **attrs)

    def as_extra_options(self) -> _ParameterKwargs:
        return cast(
            _ParameterKwargs, {key: value for key in _PARAM_KEYS if (value := getattr(self, key, None)) is not None}
        )


class ClickOptsSet(RootModel[Dict[str, ClickOpts]]):
    def __getitem__(self, key: str) -> ClickOpts:
        return self.root[key]

    def __setitem__(self, key: str, opts: ClickOpts) -> None:
        self.root[key] = opts

    @classmethod
    def from_model(cls, model: Type[BaseModel]) -> Self:
        opts = cls({})
        for name, info in model.model_fields.items():
            metas = [meta for meta in info.metadata if isinstance(meta, ClickOpts)]
            if not metas:
                continue
            meta = ClickOpts()
            for m in metas:
                meta = meta.merge(m)
            opts[name] = meta
        return opts

    def as_config_dict(
        self,
    ) -> Dict[str, Any]:
        from pydanclick.model.config import PydanclickConfig

        config = PydanclickConfig(
            exclude=[field for field, opts in self.root.items() if opts.exclude] or None,
            rename={field: opts.rename for field, opts in self.root.items() if opts.rename} or None,
            shorten={field: opts.shorten for field, opts in self.root.items() if opts.shorten} or None,
            extra_options={field: extra for field, opts in self.root.items() if (extra := opts.as_extra_options())}
            or None,
        )
        return config.model_dump(exclude_unset=True, exclude_none=True)
