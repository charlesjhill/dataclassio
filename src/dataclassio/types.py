import dataclasses as dcs
import io
import os
from enum import Enum
from functools import total_ordering
from pathlib import Path

import typing_extensions as tp

__all__ = (
    "PathLike",
    "PathOrHandle",
    "ExtraFieldStrategy",
    "EFS",
    "DataclassInstance",
    "NO_DEFAULT",
    "TDataclass",
)


PathLike: tp.TypeAlias = str | bytes | Path | os.PathLike
PathOrHandle: tp.TypeAlias = PathLike | io.IOBase


@total_ordering
class ExtraFieldStrategy(Enum):
    STRICT = "strict"
    IGNORE = "ignore"
    CAPTURE = "capture"

    def __lt__(self, other):
        if not isinstance(other, ExtraFieldStrategy):
            return NotImplemented
        return self.value < other.value


EFS = ExtraFieldStrategy


class DataclassInstance(tp.Protocol):
    __dataclass_fields__: tp.ClassVar[dict[str, dcs.Field]]


TDataclass = tp.TypeVar("TDataclass", bound=DataclassInstance)

NO_DEFAULT = tp.Sentinel("NO_DEFAULT")
