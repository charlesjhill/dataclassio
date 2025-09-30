from dataclasses import dataclass

import typing_extensions as tp

from .functional import ExtraFieldStrategy, make_from_dict


@dataclass()
class IOMixin:
    __slots__ = "_extra_fields"

    class Config:
        extra_key_strategy: ExtraFieldStrategy = ExtraFieldStrategy.EXCLUDE

    def __post_init__(self):
        self._extra_fields = {}

    @property
    def extra_fields(self):
        """Shallow copy of the extra fields stored in this instance from deserialization."""
        return dict(self._extra_fields)

    @classmethod
    def from_dict(cls: type[tp.Self], dikt: tp.Mapping) -> tp.Self:
        if not hasattr(cls, "__dict_deserializer_method"):
            cls.__dict_deserializer_method = make_from_dict(
                cls, extra_field_strategy=cls.Config.extra_key_strategy
            )
        return cls.__dict_deserializer_method(cls, dikt)
