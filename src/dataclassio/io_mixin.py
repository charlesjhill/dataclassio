from dataclasses import dataclass

import typing_extensions as tp

from .functional import make_from_dict, make_to_dict
from .functional.from_dict import _EXTRA_FIELD_ATTR_NAME
from .types import EFS


@dataclass
class IOMixin:
    __slots__ = _EXTRA_FIELD_ATTR_NAME

    def __post_init__(self):
        setattr(self, _EXTRA_FIELD_ATTR_NAME, {})

    @property
    def extra_fields(self):
        """Shallow copy of the extra fields stored in this instance from deserialization."""
        return dict(getattr(self, _EXTRA_FIELD_ATTR_NAME))

    @classmethod
    def from_dict(
        cls: type[tp.Self], dikt: tp.Mapping, extra_field_strategy: EFS = EFS.IGNORE
    ) -> tp.Self:
        """Initialize this class from a dictionary."""

        # Cache based on desired extra field strategy
        meth_name = f"_dict_deserializer_method_ef_{extra_field_strategy.name}"
        method = getattr(cls, meth_name, None)
        if method is None:
            method = make_from_dict(cls, extra_field_strategy=extra_field_strategy)
            setattr(cls, meth_name, method)
        return method(dikt)

    def to_dict(self, skip_defaults: bool = False):
        """Convert this class to a dictionary."""

        # Cache based on if we are skipping defaults.
        cls = self.__class__
        meth_name = f"_dict_serializer_method_skip_{skip_defaults}"
        method = getattr(cls, meth_name, None)
        if method is None:
            method = make_to_dict(cls, skip_defaults=skip_defaults)
            setattr(cls, meth_name, method)
        return method(self)
