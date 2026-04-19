from dataclasses import dataclass

import typing_extensions as tp

from .functional import EFS, make_from_dict


@dataclass()
class IOMixin:
    __slots__ = "_extra_fields"

    def __post_init__(self):
        self._extra_fields = {}

    @property
    def extra_fields(self):
        """Shallow copy of the extra fields stored in this instance from deserialization."""
        return dict(self._extra_fields)

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
