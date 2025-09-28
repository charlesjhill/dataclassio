from dataclasses import MISSING, Field, fields

import typing_extensions as tp


def _get_fields(cls: type):
    try:
        return fields(cls)
    except TypeError:
        pass

    msg = f"Unsupported type: {cls}. Currently, just `dataclasses.dataclass` is supported."
    raise ValueError(msg)


def _has_default(f: Field):
    return (f.default is not MISSING) or (f.default_factory is not MISSING)


_DICT_DESERIALIZER_NAME = "__dict_deserializer_co"


class IOMixin:
    __slots__ = "__extra_fields"

    def __init__(self):
        self.__extra_fields = {}

    @classmethod
    def _build_from_dict_str(cls):
        arg_specs = []
        for f in _get_fields(cls):
            if _has_default(f):
                spec = f"{f.name}=dikt.get('{f.name}')"
            else:
                spec = f"{f.name}=dikt['{f.name}']"
            arg_specs.append(spec)
        return f"""
cls({", ".join(arg_specs)})
""".strip()

    @classmethod
    def from_dict(cls: type[tp.Self], dikt: tp.Mapping) -> tp.Self:
        if not hasattr(cls, _DICT_DESERIALIZER_NAME):
            method_str = cls._build_from_dict_str()
            setattr(
                cls,
                _DICT_DESERIALIZER_NAME,
                compile(method_str, "<dynamic_from_dict>", "eval"),
            )
        return eval(
            getattr(cls, _DICT_DESERIALIZER_NAME), locals={"cls": cls, "dikt": dikt}
        )
