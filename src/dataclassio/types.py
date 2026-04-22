import dataclasses as dcs
from enum import Enum, auto

import typing_extensions as tp

__all__ = ("ExtraFieldStrategy", "EFS", "DataclassInstance", "NO_DEFAULT")


class ExtraFieldStrategy(Enum):
    STRICT = auto()
    IGNORE = auto()
    CAPTURE = auto()


EFS = ExtraFieldStrategy


class DataclassInstance(tp.Protocol):
    __dataclass_fields__: tp.ClassVar[dict[str, dcs.Field]]


class _NO_DEFAULT_TYPE:
    pass


# Sentinel for no default value. Use a class for a better repr.
NO_DEFAULT = _NO_DEFAULT_TYPE()
