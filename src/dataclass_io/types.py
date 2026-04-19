import dataclasses as dcs
from enum import Enum, auto

import typing_extensions as tp

__all__ = ("ExtraFieldStrategy", "EFS", "DataclassInstance")


class ExtraFieldStrategy(Enum):
    STRICT = auto()
    IGNORE = auto()
    CAPTURE = auto()


EFS = ExtraFieldStrategy


class DataclassInstance(tp.Protocol):
    __dataclass_fields__: tp.ClassVar[dict[str, dcs.Field]]
