import typing_extensions as tp

from .functional import make_from_dict

_DICT_DESERIALIZER_NAME = ""


class IOMixin:
    __slots__ = "__extra_fields"

    def __init__(self):
        self.__extra_fields = {}

    @classmethod
    def from_dict(cls: type[tp.Self], dikt: tp.Mapping) -> tp.Self:
        if not hasattr(cls, "__dict_deserializer_method"):
            cls.__dict_deserializer_method = make_from_dict(cls)
        return cls.__dict_deserializer_method(cls, dikt)
